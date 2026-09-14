#!/usr/bin/env python3
"""Analysis for an immutable model-run ledger; no behavior is regenerated."""
from __future__ import annotations
import argparse,itertools,json,sys,random
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from analysis import summary


def vote(p):return .5 if p==.5 else float(p>.5)


def paired_label_test(rows):
    groups=defaultdict(dict)
    for r in rows:
        q=r.get('probability_pre_reveal')
        if isinstance(q,(int,float)):groups[r['scenario']['seed']][r['scenario']['world']]=q
    diffs=[vote(v[1])-vote(v[0]) for v in groups.values() if set(v)=={0,1}]
    if not diffs:return {'n_complete_pairs':0,'p_one_sided':None}
    obs=sum(diffs)
    if len(diffs)<=18:
        stats=(sum(x*s for x,s in zip(diffs,signs)) for signs in itertools.product((-1,1),repeat=len(diffs)))
        total=2**len(diffs);p=sum(v>=obs-1e-12 for v in stats)/total;method='exact within-pair label swaps'
    else:
        rng=random.Random(4718);total=100000;hits=sum(sum(x*rng.choice((-1,1)) for x in diffs)>=obs-1e-12 for _ in range(total))
        p=(hits+1)/(total+1);method='Monte Carlo within-pair label swaps, plus-one correction'
    return {'n_complete_pairs':len(diffs),'paired_accuracy':.5+.5*obs/len(diffs),
            'p_one_sided':p,'randomizations':total,'method':method,
            'missingness_caution':'Complete-report comparison; missingness bounds and denominators must also be reported.'}


def main():
    a=argparse.ArgumentParser();a.add_argument('--input',type=Path,required=True);a.add_argument('--out',type=Path,required=True);z=a.parse_args()
    rows=[json.loads(x) for x in z.input.read_text().splitlines() if x.strip()]
    if len({r['run_id'] for r in rows})!=len(rows):raise SystemExit('Duplicate run IDs: do not double count a resumed run')
    observed=[r for r in rows if r.get('attempted',True)]
    s=summary(observed);s['planned_records']=len(rows);s['not_started']=len(rows)-len(observed)
    f=z.input.parent/'frozen_plan.json'
    models=json.loads(f.read_text())['config']['models'] if f.exists() else sorted({r['model'] for r in rows})
    tests=[]
    for model in models:
        for fam in ('persistence','consistency'):
            rr=[r for r in observed if r['model']==model and r['scenario']['family']==fam and r['scenario']['timing']=='before' and r['scenario']['budget']==4 and not r['scenario']['control']]
            t=paired_label_test(rr);t.update(model=model,family=fam);tests.append(t)
    ids=sorted(range(len(tests)),key=lambda i:tests[i]['p_one_sided'] if tests[i]['p_one_sided'] is not None else 1.)
    prev=0
    for rank,i in enumerate(ids):
        p=tests[i]['p_one_sided'];adj=min(1.,max(prev,(len(tests)-rank)*(1. if p is None else p)));prev=adj
        tests[i]['holm_adjusted_p']=adj if p is not None else None
    s['primary_tests']=tests;s['claim_limits']='This is not a deployment risk certificate, equivalence test, or latent-belief mediation analysis.'
    z.out.parent.mkdir(parents=True,exist_ok=True);z.out.write_text(json.dumps(s,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'attempted':s['attempted'],'llm_runs':s['llm_runs'],'planned_primary_tests':len(tests)},indent=2))

if __name__=='__main__':main()
