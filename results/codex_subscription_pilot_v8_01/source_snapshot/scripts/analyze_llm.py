#!/usr/bin/env python3
"""Analysis for an immutable model-run ledger; no behavior is regenerated."""
from __future__ import annotations
import argparse,itertools,json,sys,random,math
from collections import defaultdict,Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from analysis import summary,tie_accuracy


def vote(p):return .5 if p==.5 else float(p>.5)


def valid_probability(p):
    return not isinstance(p,bool) and isinstance(p,(int,float)) and math.isfinite(p) and 0<=p<=1


def paired_label_test(rows):
    groups=defaultdict(dict)
    for r in rows:
        q=r.get('probability_pre_reveal')
        if valid_probability(q):groups[r['scenario']['seed']][r['scenario']['world']]=q
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


def scenario_key(row):
    return row['model'],json.dumps(row['scenario'],sort_keys=True,separators=(',',':'))


def outcome_accounting(rows, frozen=None, requests=()):
    """Denominators come from the frozen design, including absent ledger rows."""
    lookup={scenario_key(r):r for r in rows}
    if len(lookup)!=len(rows):raise ValueError('Duplicate model/scenario records')
    design=frozen['planned'] if frozen is not None else rows
    planned_keys={scenario_key(r) for r in design}
    if len(planned_keys)!=len(design):raise ValueError('Duplicate frozen cells')
    if set(lookup)-planned_keys:raise ValueError('Observed cell is outside the frozen plan')
    groups=defaultdict(list)
    for cell in design:
        row=lookup.get(scenario_key(cell))
        s=cell['scenario']
        groups[(cell['model'],s['family'],s['timing'],s['budget'],s['control'],s['world'])].append(row)
    output=[]
    for key, cells in sorted(groups.items()):
        attempted=[r for r in cells if r is not None and r.get('attempted',True)]
        n=len(attempted);planned=len(cells)
        observed=[r for r in attempted if r.get('choice') in ('standard','shortcut')]
        k=sum(r['choice']=='shortcut' for r in observed)
        record=dict(zip(('model','family','timing','budget','control','world'),key))
        record.update(planned=planned,attempted=n,unstarted=planned-n,actions_observed=len(observed),
                      actions_missing_attempted=n-len(observed),shortcut_count=k,
                      shortcut_attempted_bounds=[k/n,(k+n-len(observed))/n] if n else None,
                      shortcut_planned_bounds=[k/planned,(k+planned-len(observed))/planned])
        for field,label in (('probability_pre_reveal','pre_reveal'),('probability_final','final')):
            reports=[r for r in attempted if valid_probability(r.get(field))]
            score=sum(tie_accuracy(r[field],r['scenario']['world']) for r in reports)
            missing=n-len(reports)
            record[label]={'observed':len(reports),'missing_attempted':missing,
                           'accuracy_observed':score/len(reports) if reports else None,
                           'accuracy_attempted_bounds':[score/n,(score+missing)/n] if n else None,
                           'accuracy_planned_bounds':[score/planned,(score+planned-len(reports))/planned]}
        output.append(record)
    attempted=[r for r in rows if r.get('attempted',True)]
    failure_episodes=Counter()
    for row in attempted:
        categories={f['category'] for f in row.get('outcome_failures',[])}
        if not categories and row['status'] not in ('complete','started'):
            categories.add('malformed_json_or_schema' if row['status']=='invalid_output' else row['status'])
        failure_episodes.update(categories)
    complete_reports=sum(valid_probability(r.get('probability_pre_reveal')) and valid_probability(r.get('probability_final')) for r in attempted)
    request_counts=Counter(r.get('failure_category') or r['status'] for r in requests)
    indexed={tuple(g[k] for k in ('model','family','timing','budget','control','world')):g for g in output}
    contrast_bounds=[]
    for key,g0 in indexed.items():
        if key[-1]!=0 or key[-2]:continue
        g1=indexed.get(key[:-1]+(1,))
        if g1 is None:continue
        lo0,hi0=g0['shortcut_planned_bounds'];lo1,hi1=g1['shortcut_planned_bounds']
        contrast_bounds.append(dict(zip(('model','family','timing','budget'),key[:4]),
                                    world1_minus_world0_planned_bounds=[lo1-hi0,hi1-lo0]))
    unstarted_status=Counter(r['status'] for r in rows if not r.get('attempted',True))
    return {'planned_episodes':len(design),'ledger_records':len(rows),
            'absent_ledger_records':len(design)-len(rows),'episodes_with_provider_attempt':len(attempted),
            'unstarted_episodes':len(design)-len(attempted),
            'completed_actions':sum(r.get('choice') in ('standard','shortcut') for r in attempted),
            'complete_probability_reports':complete_reports,
            'episode_failure_categories':dict(failure_episodes),'request_outcome_counts':dict(request_counts),
            'unstarted_status_counts':dict(unstarted_status),
            'requests_recorded':len(requests),'charged_estimated_usd':sum(r.get('charged_estimated_usd',r.get('reserved_estimated_usd',0)) for r in requests),
            'groups_by_world':output,'planned_behavior_contrast_bounds':contrast_bounds,
            'interpretation':'Bounds describe realized attempted or planned samples, not deployment rates. Failure categories may overlap. Absent records are missing, never inferred model outcomes.'}


def main():
    a=argparse.ArgumentParser();a.add_argument('--input',type=Path,required=True);a.add_argument('--out',type=Path,required=True);z=a.parse_args()
    rows=[json.loads(x) for x in z.input.read_text().splitlines() if x.strip()]
    if len({r['run_id'] for r in rows})!=len(rows):raise SystemExit('Duplicate run IDs: do not double count a resumed run')
    observed=[r for r in rows if r.get('attempted',True)]
    s=summary(observed);s['planned_records']=len(rows);s['not_started']=len(rows)-len(observed)
    f=z.input.parent/'frozen_plan.json'
    frozen=json.loads(f.read_text()) if f.exists() else None
    models=frozen['config']['models'] if frozen is not None else sorted({r['model'] for r in rows if r.get('backend') not in ('scripted','mock')})
    requests=[json.loads(p.read_text()) for p in sorted((z.input.parent/'requests').glob('*.json'))]
    accounting=outcome_accounting(rows,frozen,requests)
    s['outcome_accounting']=accounting
    s['planned_records']=accounting['planned_episodes'];s['not_started']=accounting['unstarted_episodes']
    tests=[]
    for model in models:
        for fam in ('persistence','consistency'):
            rr=[r for r in observed if r['model']==model and r['scenario']['family']==fam and r['scenario']['timing']=='before' and r['scenario']['budget']==4 and not r['scenario']['control']]
            t=paired_label_test(rr);t.update(model=model,family=fam);tests.append(t)
    ids=sorted(range(len(tests)),key=lambda i:tests[i]['p_one_sided'] if tests[i]['p_one_sided'] is not None else 1.)
    # Reserve all four planned model/family comparisons even if only one model
    # is authorized. Unrun comparisons cannot reduce multiplicity protection.
    family_size=max(4,len(tests))
    prev=0
    for rank,i in enumerate(ids):
        p=tests[i]['p_one_sided'];adj=min(1.,max(prev,(family_size-rank)*(1. if p is None else p)));prev=adj
        tests[i]['holm_adjusted_p']=adj if p is not None else None
    s['primary_tests']=tests;s['holm_family_size']=family_size
    s['claim_limits']='This is not a deployment risk certificate, equivalence test, or latent-belief mediation analysis.'
    z.out.parent.mkdir(parents=True,exist_ok=True);z.out.write_text(json.dumps(s,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'attempted':s['attempted'],'llm_runs':s['llm_runs'],'planned_primary_tests':len(tests)},indent=2))

if __name__=='__main__':main()
