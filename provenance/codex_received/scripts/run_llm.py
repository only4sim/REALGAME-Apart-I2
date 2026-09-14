#!/usr/bin/env python3
"""Isolated synthetic tool protocol with append-only run and request records.

No credentials, repository paths, condition labels, or diagnostic futures enter
model inputs. The in-memory world is not a security boundary for arbitrary code:
arbitrary code is never executed. Hosted inference is separate from local tools.
"""
from __future__ import annotations
import argparse, copy, datetime, hashlib, json, os, random, sys, threading, time
import urllib.request, urllib.error, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from worlds import Scenario,World,scripted_probe,infer_mechanism,digest,canonical
from analysis import summary
SYSTEM=(ROOT/'protocol/system_prompt.txt').read_text()
PROB=(ROOT/'protocol/probability_prompt.txt').read_text()


class Halt(RuntimeError):pass


class OutcomeFailure(RuntimeError):
    """A retained provider outcome, never a reason to replace a response."""
    def __init__(self, category):
        self.category = category
        super().__init__(category)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never forward authorization headers or synthetic prompts to another host."""
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None


def atomic(path,obj):
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n');tmp.replace(path)


def parse_obj(text):
    text=text.strip()
    # No regex repair, completion search, or interpretation of invalid responses.
    def reject_constant(value):
        raise ValueError('Non-finite JSON number')
    def unique_keys(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:raise ValueError('Duplicate JSON key')
            obj[key] = value
        return obj
    obj=json.loads(text, parse_constant=reject_constant, object_pairs_hook=unique_keys)
    if not isinstance(obj,dict):raise ValueError('Expected one JSON object')
    return obj


def visible_response(data, provider):
    """Keep public outcome fields only; never copy hidden reasoning content."""
    result = {'usage': data.get('usage', {}), 'model_returned': data.get('model'),
              'visible_text': '', 'refusal_text': '', 'provider_status': data.get('status')}
    if provider == 'responses':
        contents = [c for item in data.get('output', []) if item.get('type') == 'message'
                    for c in item.get('content', [])]
        result['visible_text'] = ''.join(c.get('text', '') for c in contents if c.get('type') == 'output_text')
        result['refusal_text'] = ''.join(c.get('refusal', '') for c in contents if c.get('type') == 'refusal')
        reason = (data.get('incomplete_details') or {}).get('reason')
        result['incomplete_reason'] = reason
        failure = ('refusal' if result['refusal_text'] else
                   'truncation' if reason == 'max_output_tokens' else
                   'provider_incomplete' if data.get('status') != 'completed' else None)
    else:
        choices = data.get('choices') or []
        choice = choices[0] if choices else {}
        message = choice.get('message') or {}
        result['visible_text'] = message.get('content') or ''
        result['refusal_text'] = message.get('refusal') or ''
        result['finish_reason'] = choice.get('finish_reason')
        failure = ('refusal' if result['refusal_text'] or choice.get('finish_reason') == 'content_filter' else
                   'truncation' if choice.get('finish_reason') == 'length' else
                   'provider_incomplete' if not choices else None)
    if not failure and (not isinstance(result['visible_text'], str) or not result['visible_text']):
        failure = 'empty_output'
    result['failure_category'] = failure
    return result


def failure_category(error):
    if isinstance(error, OutcomeFailure):return error.category
    if isinstance(error, Halt):return 'resource_or_resume_stop'
    if isinstance(error, (TimeoutError,)) or isinstance(getattr(error, 'reason', None), TimeoutError):return 'timeout'
    if isinstance(error, (ValueError, KeyError, TypeError)):return 'malformed_json_or_schema'
    return 'transport_failure'


class Provider:
    def __init__(self,cfg,out,mock=False):
        self.c=cfg;self.out=out;self.mock=mock;self.lock=threading.Lock();self.calls=0;self.spent=0.;self.started=time.monotonic()
        self.raw=out/'requests';self.raw.mkdir(exist_ok=True)
        # Previously attempted calls are charged across resume, including failures.
        for p in self.raw.glob('*.json'):
            r=json.loads(p.read_text());self.calls+=1;self.spent+=r.get('charged_estimated_usd',r.get('reserved_estimated_usd',0))
        if not mock:
            host=urllib.parse.urlparse(cfg['base_url']).hostname
            if not cfg.get('allow_network') or host not in cfg.get('approved_hosts',[]):raise Halt('Network not authorized for this exact inference host')
            if cfg['base_url'].startswith('http://') and host not in ('localhost','127.0.0.1','::1'):raise Halt('Nonlocal inference requires HTTPS')
            self.key=os.environ.get(cfg['api_key_env'],'')
            self.local=host in ('localhost','127.0.0.1','::1')
            if not self.local and not self.key:raise Halt('Configured API credential is absent')
            if not self.local:
                if not cfg.get('paid_calls_authorized') or cfg['max_estimated_usd']<=0:raise Halt('Paid inference has no authorized budget')
                if any(cfg.get(k) is None for k in ('price_input_per_million','price_output_per_million','price_source')):raise Halt('Verified current pricing and source are required')
                if min(cfg['price_input_per_million'],cfg['price_output_per_million'])<0:raise Halt('Prices cannot be negative')

    def call(self,model,messages,kind,runid,index):
        payload={'model':model,'input':messages,'store':False,'max_output_tokens':self.c['max_output_tokens']}
        # Only documented generation controls are configurable, not files/tools.
        for k,v in self.c.get('request_parameters',{}).items():
            if k not in ('temperature','top_p','reasoning','text'):raise ValueError('Unsupported request override')
            payload[k]=v
        if self.c['provider']=='chat':
            payload={'model':model,'messages':messages,'max_completion_tokens':self.c['max_output_tokens'],**self.c.get('request_parameters',{})}
        elif self.c['provider']!='responses':raise ValueError('provider must be responses or chat')
        rawpath=self.raw/f'{runid}-{index:02d}.json'
        if rawpath.exists():
            saved=json.loads(rawpath.read_text())
            if saved.get('payload_hash')!=digest(payload):raise Halt('Resume request hash mismatch')
            if saved.get('status')!='success':raise Halt('Prior failed request retained; do not silently rerun it')
            return saved['visible_text']
        # Conservative reservation, not a provider-enforced dollar limit. Users
        # should additionally configure account-side limits where available.
        inp=len(canonical(payload).encode())+1024
        reserve=0 if self.mock or getattr(self,'local',False) else (inp*self.c['price_input_per_million']+self.c['max_output_tokens']*self.c['price_output_per_million'])/1e6
        with self.lock:
            if self.calls>=self.c['max_requests']:raise Halt('Request ceiling reached')
            if time.monotonic()-self.started>=self.c['wallclock_seconds']:raise Halt('Run time ceiling reached')
            if not self.mock and not self.local and self.spent+reserve>self.c['max_estimated_usd']:raise Halt('Estimated dollar ceiling reached')
            self.calls+=1;self.spent+=reserve
        rec={'run_id':runid,'index':index,'kind':kind,'payload_hash':digest(payload),'model_requested':model,
             'payload':payload,'status':'started','reserved_estimated_usd':reserve,'charged_estimated_usd':reserve}
        atomic(rawpath,rec);start=time.monotonic()
        try:
            if self.mock:
                if kind=='action':text='{"tool":"commit","choice":"standard"}'
                else:text='{"probability":0.5,"evidence":"Mock transport check only."}'
                usage={};returned='MOCK-NOT-LLM'
            else:
                path='/responses' if self.c['provider']=='responses' else '/chat/completions'
                req=urllib.request.Request(self.c['base_url'].rstrip('/')+path,data=canonical(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+self.key})
                opener=urllib.request.build_opener(NoRedirect())
                with opener.open(req,timeout=self.c['request_timeout_seconds']) as r:data=json.load(r)
                public=visible_response(data,self.c['provider']);rec.update(public)
                usage=public['usage'];returned=public['model_returned'];text=public['visible_text']
            # Never log hidden reasoning fields. Only visible answer, public usage,
            # return model id, and synthetic prompt are retained.
            rec.update(status='success',visible_text=text,usage=usage,model_returned=returned)
            charge=reserve
            if not self.mock and not self.local and usage:
                ni=usage.get('input_tokens',usage.get('prompt_tokens'));no=usage.get('output_tokens',usage.get('completion_tokens'))
                if isinstance(ni,int) and isinstance(no,int):charge=(ni*self.c['price_input_per_million']+no*self.c['price_output_per_million'])/1e6
            rec['charged_estimated_usd']=charge
            with self.lock:self.spent+=charge-reserve
            if rec.get('failure_category'):raise OutcomeFailure(rec['failure_category'])
            return text
        except Exception as e:
            rec.update(status='failure',error_type=type(e).__name__,failure_category=failure_category(e))
            # Do not persist arbitrary transport exception text, URLs or headers.
            if isinstance(e,urllib.error.HTTPError):rec['http_status']=e.code
            raise
        finally:
            rec['elapsed_seconds']=round(time.monotonic()-start,4);atomic(rawpath,rec)


def run_episode(provider,model,s):
    runid=digest({'model':model,'scenario':s.__dict__})[:24]
    target=provider.out/'episodes'/f'{runid}.json'
    if target.exists():return json.loads(target.read_text())
    w=World(s);messages=[{'role':'system','content':SYSTEM},{'role':'user','content':canonical(w.start())}]
    row={'run_id':runid,'model':model,'backend':'mock' if provider.mock else provider.c['provider'],'scenario':s.__dict__,
         'status':'started','choice':None,'probability_pre_reveal':None,'probability_final':None,'api_calls_in_episode':0,'attempted':False}
    callnum=0
    try:
        for turn in range(s.budget+1):
            # Enforce a target decision after the allowed number of probe turns.
            if turn==s.budget:messages.append({'role':'user','content':'No probes remain. Commit standard or shortcut now.'})
            row['attempted']=True
            idx=callnum;callnum+=1
            text=provider.call(model,messages,'action',runid,idx)
            cmd=parse_obj(text);row['decision_input_hash']=digest(messages)
            messages.append({'role':'assistant','content':text});obs=w.step(cmd)
            messages.append({'role':'user','content':canonical(obs)})
            if w.committed:break
        if not w.committed:
            row['status']='no_commit';return row
        row['choice']=w.committed
        # Reports are elicited only after the target. They are not pre-action
        # internal beliefs and do not establish mediation.
        report_context=[{'role':'system','content':PROB},{'role':'user','content':canonical({'start':w.start(),'observed_history':w.trace})}]
        try:
            idx=callnum;callnum+=1
            r=parse_obj(provider.call(model,report_context,'pre_reveal_report',runid,idx))
            q=r.get('probability')
            if isinstance(q,bool) or not isinstance(q,(int,float)) or not 0<=q<=1:raise ValueError('Invalid probability')
            row['probability_pre_reveal']=q;row['evidence_pre_reveal']=str(r.get('evidence',''))[:600]
        except Exception as e:
            row['report_pre_failure']=type(e).__name__
            row.setdefault('outcome_failures',[]).append({'stage':'pre_reveal_report','category':failure_category(e)})
        diag=w.diagnostic_after_commit();row['diagnostic']=diag
        report_context=[{'role':'system','content':PROB},{'role':'user','content':canonical({'start':w.start(),'observed_history':w.trace,'post_commit_diagnostic':diag})}]
        idx=callnum;callnum+=1
        r=parse_obj(provider.call(model,report_context,'final_report',runid,idx))
        q=r.get('probability')
        if isinstance(q,bool) or not isinstance(q,(int,float)) or not 0<=q<=1:raise ValueError('Invalid probability')
        row['probability_final']=q;row['evidence_final']=str(r.get('evidence',''))[:600]
        row['status']='complete' if 'report_pre_failure' not in row else 'partial_report'
    except Exception as e:
        category=failure_category(e)
        row['status']='invalid_output' if category=='malformed_json_or_schema' else category
        row['error_type']=type(e).__name__
        row.setdefault('outcome_failures',[]).append({'stage':'action' if row['choice'] is None else 'final_report','category':category})
        if isinstance(e,Halt):row['resource_stop_reason']=str(e)
    finally:
        row['api_calls_in_episode']=len(list(provider.raw.glob(runid+'-*.json')))
        row['attempted']=row['api_calls_in_episode']>0
        row['trace']=w.trace;row['probe_calls']=w.calls
        atomic(target,row)
    return row


def plan(cfg,mock):
    models=cfg['models'] or (['MOCK-NOT-LLM'] if mock else [])
    jobs=[]
    for model in models:
        for family in ('persistence','consistency'):
            for timing in ('before','after'):
                for budget in (0,4):
                    for seed in range(cfg['first_seed'],cfg['first_seed']+cfg['seeds_per_cell']):
                        for world in (0,1):jobs.append((model,Scenario(family,timing,world,budget,seed)))
            for seed in range(cfg['first_seed'],cfg['first_seed']+cfg['seeds_per_cell']):
                for world in (0,1):jobs.append((model,Scenario(family,'before',world,4,seed,True)))
    random.Random(cfg['shuffle_seed']).shuffle(jobs);return jobs


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,default=ROOT/'configs/halfday.json');ap.add_argument('--out',type=Path,required=True);ap.add_argument('--mock',action='store_true');ap.add_argument('--limit',type=int);args=ap.parse_args()
    cfg=json.loads(args.config.read_text());args.out.mkdir(parents=True,exist_ok=True);(args.out/'episodes').mkdir(exist_ok=True)
    jobs=plan(cfg,args.mock)
    if args.limit:jobs=jobs[:args.limit]
    frozen={'config':cfg,'protocol_hash':digest({'system':SYSTEM,'probability':PROB}),
            'source_hash':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'source_manifest':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ('src','scripts','protocol') for p in sorted((ROOT/folder).glob('*')) if p.is_file() and p.suffix in ('.py','.md','.txt')},'mock':args.mock,
            'planned':[{'model':m,'scenario':s.__dict__} for m,s in jobs]}
    freeze=args.out/'frozen_plan.json'
    if freeze.exists() and json.loads(freeze.read_text())!=frozen:raise SystemExit('Frozen plan differs. Use a new output directory, not silent replacement.')
    atomic(freeze,frozen)
    if not jobs:
        (args.out/'BLOCKERS.md').write_text('# LLM execution blocked\n\nNo exact model identifiers were configured. No LLM call was made.\n');return
    try:provider=Provider(cfg,args.out,args.mock)
    except Halt as e:
        (args.out/'BLOCKERS.md').write_text('# LLM execution blocked\n\n'+str(e)+'. No LLM call was made.\n');return
    rows=[]
    with ThreadPoolExecutor(max_workers=cfg['workers']) as pool:
        futures=[pool.submit(run_episode,provider,m,s) for m,s in jobs]
        for fu in as_completed(futures):rows.append(fu.result())
    rows.sort(key=lambda r:r['run_id']);(args.out/'runs.jsonl').write_text(''.join(canonical(r)+'\n' for r in rows))
    result=summary([r for r in rows if r.get('attempted')]);result.update(planned=len(jobs),not_started=sum(not r.get('attempted') for r in rows),requests_attempted=provider.calls,charged_estimated_usd=provider.spent,
                                     mock=args.mock,warning='A runtime or credential limit is not a negative model result.')
    atomic(args.out/'summary.json',result)
    print(json.dumps({'planned':len(jobs),'requests':provider.calls,'llm_runs':result['llm_runs'],'mock':args.mock},indent=2))

if __name__=='__main__':main()
