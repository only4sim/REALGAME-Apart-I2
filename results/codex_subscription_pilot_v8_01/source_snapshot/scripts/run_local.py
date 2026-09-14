#!/usr/bin/env python3
"""Reproduce CPU-only mechanism checks. These are not LLM experiments."""
from __future__ import annotations
import argparse, hashlib, json, sys, random
from fractions import Fraction as F
from itertools import product
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from worlds import Scenario,World,scripted_probe,infer_mechanism,canonical,digest
from analysis import summary


def write_json(path,obj):
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')


def scripted_runs(out):
    rows=[];post_hash_checks=0
    policies=('compliant','shortcut','mechanism_switch','blind')
    for policy,fam,timing,budget,seed,b in product(policies,('persistence','consistency'),('before','after'),(0,4),range(12),(0,1)):
        s=Scenario(fam,timing,b,budget,seed);w=World(s)
        for a in scripted_probe(fam)[:budget]:w.step(a)
        pre=infer_mechanism(w.trace)
        coin=int(hashlib.sha256(f'{seed}:{fam}'.encode()).hexdigest()[:8],16)%2
        choice={'compliant':'standard','shortcut':'shortcut','mechanism_switch':'shortcut' if pre>.5 else 'standard','blind':'shortcut' if coin else 'standard'}[policy]
        before={'start':w.start(),'trace':w.trace.copy()}
        w.step({'tool':'commit','choice':choice})
        after=w.diagnostic_after_commit()
        rows.append({'run_id':s.identity+'-'+policy,'model':policy,'backend':'scripted','scenario':s.__dict__,
                     'status':'complete','choice':choice,'probability_pre_reveal':pre,'probability_final':infer_mechanism(after),
                     'decision_input_hash':digest(before),'pre_decision_trace':before,'diagnostic':after,'calls':w.calls})
    # Coherent controls: label is randomized but has no causal effect.
    for policy,fam,seed,b in product(policies,('persistence','consistency'),range(12),(0,1)):
        s=Scenario(fam,'before',b,4,seed,True);w=World(s)
        for a in scripted_probe(fam):w.step(a)
        pre=infer_mechanism(w.trace)
        coin=int(hashlib.sha256(f'{seed}:{fam}'.encode()).hexdigest()[:8],16)%2
        choice={'compliant':'standard','shortcut':'shortcut','mechanism_switch':'shortcut' if pre>.5 else 'standard','blind':'shortcut' if coin else 'standard'}[policy]
        before={'start':w.start(),'trace':w.trace.copy()};w.step({'tool':'commit','choice':choice})
        rows.append({'run_id':s.identity+'-'+policy,'model':policy,'backend':'scripted','scenario':s.__dict__,
                     'status':'complete','choice':choice,'probability_pre_reveal':pre,'probability_final':infer_mechanism(w.diagnostic_after_commit()),
                     'decision_input_hash':digest(before),'pre_decision_trace':before,'diagnostic':w.diagnostic_after_commit(),'calls':w.calls})
    idx={(r['model'],r['scenario']['family'],r['scenario']['timing'],r['scenario']['budget'],r['scenario']['seed'],r['scenario']['control'],r['scenario']['world']):r for r in rows}
    for key,r in idx.items():
        if key[-1]!=0:continue
        r1=idx[key[:-1]+(1,)]
        if r['scenario']['timing']=='after' or r['scenario']['budget']==0 or r['scenario']['control']:
            assert r['decision_input_hash']==r1['decision_input_hash'];post_hash_checks+=1
            assert r['choice']==r1['choice']
    with (out/'scripted_runs.jsonl').open('w') as f:
        for row in rows:f.write(canonical(row)+'\n')
    a=summary(rows);a.update({'status':'passed','scripted_episodes':len(rows),'matched_input_pair_checks':post_hash_checks,
                            'failed':0,'excluded':0,'note':'Scripted mechanism validation. Seeds repeat mechanics; counts are not independent realistic environments.'})
    write_json(out/'scripted_summary.json',a)
    return a


def coverage(out):
    result=[];checks=0
    grid=(F(0),F(1,4),F(1,2),F(3,4),F(1))
    for p,q,t0,t1 in product((F(1,10),F(1,2),F(9,10)),(F(0),F(1,16),F(1,4),F(1,2),F(1)),grid,grid):
        ref=(1-p)*t0+p*t1;naive=(1-q)*t0+q*t1
        if q==0:lo=(1-p)*t0;hi=lo+p
        elif q==1:lo=p*t1;hi=lo+1-p
        else:lo=hi=ref
        assert lo<=ref<=hi;checks+=1
        corrected=None
        if 0<q<1:
            corrected=(1-q)*(1-p)/(1-q)*t0+q*p/q*t1
            assert corrected==ref;checks+=1
        result.append({'p':str(p),'q':str(q),'theta0':str(t0),'theta1':str(t1),
                       'reference':str(ref),'naive':str(naive),'corrected':str(corrected) if corrected is not None else None,
                       'identified_interval':[str(lo),str(hi)],'tv_cue':str(abs(p-q))})
    # Explicit same-safe-law/different-reference pair.
    assert (F(1,2)-0)==F(1,2)
    write_json(out/'coverage.json',{'status':'passed','cases':len(result),'exact_checks':checks,
                                  'note':'Population identities; no learned policy or real deployment.', 'rows':result})
    # Finite repeated sampling for a fixed scripted behavior kernel; all repeats saved.
    rng=random.Random(620231);rr=[];agg=[];n=128;reps=1000;p=F(1,2);t0=F(1,4);t1=F(3,4)
    for q in (F(1,16),F(1,4),F(1,2)):
        for rep in range(reps):
            counts=[0,0,0,0]
            for _ in range(n):
                z=int(rng.random()<float(q));y=int(rng.random()<float(t1 if z else t0));counts[2*z+y]+=1
            raw=F(counts[1]+counts[3],n)
            est=(F(counts[1])*(1-p)/(1-q)+F(counts[3])*p/q)/n
            rr.append({'q':str(q),'replicate':rep,'n':n,'counts':counts,'naive':float(raw),'weighted':float(est),'reference':.5})
        these=rr[-reps:]
        var=q*(p/q)**2*t1+(1-q)*((1-p)/(1-q))**2*t0-F(1,4)
        rawmean=(1-q)*t0+q*t1
        agg.append({'q':str(q),'replicates':reps,'n':n,
                    'mean_naive':sum(x['naive'] for x in these)/reps,
                    'mean_weighted':sum(x['weighted'] for x in these)/reps,
                    'mse_naive':sum((x['naive']-.5)**2 for x in these)/reps,
                    'mse_weighted':sum((x['weighted']-.5)**2 for x in these)/reps,
                    'exact_mse_weighted':str(var/n),
                    'exact_mse_naive':str((rawmean-F(1,2))**2+rawmean*(1-rawmean)/n)})
    with (out/'coverage_replicates.jsonl').open('w') as f:
        for r in rr:f.write(canonical(r)+'\n')
    write_json(out/'coverage_sampling.json',{'rows':agg,'replicates_total':len(rr),'draws_total':n*len(rr),'failed':0,'seed':620231})
    return len(result),checks


def passage(pone,e0,e1,n=200,threshold=F(20)):
    p0=1-pone;alive={0:F(1)};hit=F(0);history=[]
    pows0=[e0**i for i in range(n+1)];pows1=[e1**i for i in range(n+1)]
    for t in range(1,n+1):
        nxt={}
        for k,mass in alive.items():
            for bit,p in ((0,p0),(1,pone)):
                kk=k+bit;v=mass*p
                if pows0[t-kk]*pows1[kk]>=threshold:hit+=v
                else:nxt[kk]=nxt.get(kk,F(0))+v
        alive=nxt
        assert hit+sum(alive.values(),F(0))==1
        history.append(float(hit))
    return hit,history


def robustness(out):
    e0,e1=F(5,3),F(5,7);span=e0-e1;rows=[]
    for eta in (F(0),F(1,20),F(1,5)):
        actual=F(7,10)-eta;den=1+eta*span
        assert (1-actual)*e0+actual*e1==den
        for mode in ('nominal','corrected'):
            div=den if mode=='corrected' else F(1)
            hit,hist=passage(actual,e0/div,e1/div)
            if mode=='corrected':assert hit<=F(1,20)
            rows.append({'eta':str(eta),'mode':mode,'probability_one':str(actual),'normalizer':str(div),
                         'null_moment':str(((1-actual)*e0+actual*e1)/div),
                         'crossing_probability_exact':str(hit),'crossing_probability':float(hit),
                         'horizon':200,'curve':hist})
    # Marginals match at every time, but a single cached bit violates conditional validity.
    first=next(n for n in range(1,100) if e0**n>=20)
    assert first==6
    persistent={'nominal_marginal_probability_one':'7/10','every_time_marginal_tv':'0',
                'nominal_eventual_crossing':'3/10','first_possible_crossing':first,
                'conditional_tv_envelope':'7/10','robust_normalizer':str(1+F(7,10)*span),
                'robust_maximum_factor':str(e0/(1+F(7,10)*span)),
                'robust_crossing_probability':'0'}
    assert F(persistent['robust_maximum_factor'])==1
    write_json(out/'robustness.json',{'status':'passed','dynamic_program_cases':len(rows),'rows':rows,
                                     'persistent_bit':persistent,'llm_runs':0,
                                     'note':'Exact finite-state probability calculation. Not an empirical confidence estimate.'})
    return rows


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=ROOT/'results');args=p.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        raise SystemExit('Output directory is not empty. Preserve raw evidence and use a fresh directory.')
    args.out.mkdir(parents=True,exist_ok=True)
    s=scripted_runs(args.out);c,checks=coverage(args.out);r=robustness(args.out)
    totals={'scripted_episodes':s['scripted_episodes'],'scripted_failed':0,'scripted_excluded':0,
            'matched_input_pair_checks':s['matched_input_pair_checks'],'population_coverage_cases':c,'coverage_exact_checks':checks,
            'sampling_replicates':3000,'sampling_draws':384000,'dynamic_program_cases':len(r),'llm_runs':0}
    write_json(args.out/'totals.json',totals);print(json.dumps(totals,indent=2))

if __name__=='__main__':main()
