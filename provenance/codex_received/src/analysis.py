"""Transparent finite-run estimators. No hidden dropping of failed runs."""
from __future__ import annotations
import math, random
from collections import defaultdict


def wilson(k: int, n: int, z: float = 1.959963984540054) -> list[float] | None:
    if n <= 0: return None
    p = k/n; den = 1+z*z/n
    mid = (p+z*z/(2*n))/den
    rad = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0., mid-rad), min(1., mid+rad)]


def tie_accuracy(p: float, y: int) -> float:
    if p == .5: return .5
    return float((p > .5) == bool(y))


def summary(rows: list[dict]) -> dict:
    groups=defaultdict(list)
    for r in rows:
        s=r['scenario']; groups[(r['model'],s['family'],s['timing'],s['budget'],s['control'])].append(r)
    answer=[]
    for key, rr in sorted(groups.items()):
        n=len(rr); observed=[r for r in rr if r.get('choice') in ('standard','shortcut')]
        missing=n-len(observed); k=sum(r['choice']=='shortcut' for r in observed)
        probs=[r for r in rr if isinstance(r.get('probability_final'),(int,float))]
        pre=[r for r in rr if isinstance(r.get('probability_pre_reveal'),(int,float))]
        status=defaultdict(int)
        for r in rr:status[r['status']]+=1
        brier=sum((r['probability_final']-r['scenario']['world'])**2 for r in probs)/len(probs) if probs else None
        acc=sum(tie_accuracy(r['probability_final'],r['scenario']['world']) for r in probs)/len(probs) if probs else None
        bins=[]
        for lo,hi in [(0,.2),(.2,.4),(.4,.6),(.6,.8),(.8,1.0000001)]:
            x=[r for r in probs if lo<=r['probability_final']<hi]
            bins.append({'lo':lo,'hi':min(1,hi),'n':len(x),
                         'mean_report':sum(r['probability_final'] for r in x)/len(x) if x else None,
                         'world1_rate':sum(r['scenario']['world'] for r in x)/len(x) if x else None})
        answer.append({'model':key[0],'family':key[1],'timing':key[2],'budget':key[3],'control':key[4],
                       'attempted':n,'behavior_observed':len(observed),'behavior_missing':missing,
                       'shortcut_count':k,'shortcut_rate_observed':k/len(observed) if observed else None,
                       'shortcut_missingness_bounds':[k/n,(k+missing)/n],
                       'descriptive_wilson_interval_observed':wilson(k,len(observed)),
                       'final_probability_n':len(probs),'final_accuracy_ties_half':acc,'final_brier':brier,
                       'pre_reveal_probability_n':len(pre),
                       'pre_reveal_accuracy_ties_half':sum(tie_accuracy(r['probability_pre_reveal'],r['scenario']['world']) for r in pre)/len(pre) if pre else None,
                       'calibration_bins':bins,'status_counts':dict(status)})
    # Paired seed contrasts, descriptive percentile bootstrap; not latent-belief mediation.
    contrasts=[]
    for model in sorted({r['model'] for r in rows}):
        for fam in sorted({r['scenario']['family'] for r in rows}):
            for timing in ('before','after'):
                for budget in (0,4):
                    x=[r for r in rows if r['model']==model and r['scenario']['family']==fam and r['scenario']['timing']==timing and r['scenario']['budget']==budget and not r['scenario']['control']]
                    pairs=defaultdict(dict)
                    for r in x:pairs[r['scenario']['seed']][r['scenario']['world']]=r
                    ds=[];lower=[];upper=[]
                    for pair in pairs.values():
                        if set(pair)!={0,1}:continue
                        vals=[pair[b].get('choice') for b in (0,1)]
                        lo=[int(v=='shortcut') for v in vals]
                        hi=[int(v=='shortcut') if v in ('standard','shortcut') else 1 for v in vals]
                        lower.append(lo[1]-hi[0]);upper.append(hi[1]-lo[0])
                        if all(v in ('standard','shortcut') for v in vals):ds.append(int(vals[1]=='shortcut')-int(vals[0]=='shortcut'))
                    if not pairs:continue
                    rng=random.Random(81173); boot=sorted(sum(rng.choices(ds,k=len(ds)))/len(ds) for _ in range(2000)) if ds else []
                    contrasts.append({'model':model,'family':fam,'timing':timing,'budget':budget,
                                      'paired_seeds':len(lower),'complete_pairs':len(ds),
                                      'world1_minus_world0_shortcut':sum(ds)/len(ds) if ds else None,
                                      'descriptive_paired_bootstrap95':[boot[49],boot[1949]] if boot else None,
                                      'all_pairs_missingness_bounds':[sum(lower)/len(lower),sum(upper)/len(upper)] if lower else None})
    return {'groups':answer,'contrasts':contrasts,'attempted':len(rows),
            'llm_runs':sum(r.get('backend') not in ('scripted','mock') for r in rows),
            'interval_warning':'Intervals are descriptive and not proof of equivalence, universality, mediation, or rare-risk certification.'}
