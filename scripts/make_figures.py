#!/usr/bin/env python3
"""Figures from saved observations and exact calculations; no re-simulation."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'figures';out.mkdir(exist_ok=True)
s=json.loads((ROOT/'results/coverage_sampling.json').read_text())['rows']
fig,ax=plt.subplots(figsize=(6.3,2.6))
x=list(range(len(s)))
ax.plot(x,[r['mse_naive'] for r in s],marker='o',label='Uncorrected estimate',linewidth=1.6)
ax.plot(x,[r['mse_weighted'] for r in s],marker='s',linestyle='--',label='Known-kernel weighted estimate',linewidth=1.6)
ax.set_xticks(x,[r['q'] for r in s]);ax.set_xlabel('Safe probability of the prerequisite, q')
ax.set_ylabel('Mean squared error');ax.set_ylim(bottom=0)
ax.legend(fontsize=8,frameon=False);ax.tick_params(labelsize=9);fig.tight_layout()
fig.savefig(out/'coverage_mse.png',dpi=240);fig.savefig(out/'coverage_mse.pdf');plt.close(fig)
r=json.loads((ROOT/'results/robustness.json').read_text())['rows']
fig,ax=plt.subplots(figsize=(6.3,2.6))
for mode,mark,ls in [('nominal','o','-'),('corrected','s','--')]:
    rr=[v for v in r if v['mode']==mode]
    eta=[float(__import__('fractions').Fraction(v['eta'])) for v in rr]
    ax.plot(eta,[v['crossing_probability'] for v in rr],marker=mark,linestyle=ls,label=mode.capitalize(),linewidth=1.6)
ax.axhline(.05,linestyle=':',label='Claimed error limit (0.05)',linewidth=1)
ax.set_xlabel('Conditional probability misspecification, eta');ax.set_ylabel('False certificate by round 200')
ax.set_ylim(-.02,1.04);ax.set_xticks([0,.05,.2]);ax.legend(fontsize=8,frameon=False,loc='upper left')
ax.tick_params(labelsize=9);fig.tight_layout();fig.savefig(out/'robustness.png',dpi=240);fig.savefig(out/'robustness.pdf');plt.close(fig)
pilot=json.loads((ROOT/'results/codex_subscription_pilot_v8_01/analysis.json').read_text())
panels=[]
for control in (False,True):
    groups=[g for g in pilot['groups'] if g['control']==control]
    pre_n=sum(g['pre_reveal_probability_n'] for g in groups)
    final_n=sum(g['final_probability_n'] for g in groups)
    panels.append((pre_n,
        sum(g['pre_reveal_accuracy_ties_half']*g['pre_reveal_probability_n'] for g in groups)/pre_n,
        sum(g['final_accuracy_ties_half']*g['final_probability_n'] for g in groups)/final_n))
fig,(ax,action)=plt.subplots(1,2,figsize=(6.3,1.7),gridspec_kw={'width_ratios':[3,1]})
positions=[0,1];width=.3
ax.bar([v-width/2 for v in positions],[v[1] for v in panels],width,label='Pre-diagnostic',color='#4c78a8')
ax.bar([v+width/2 for v in positions],[v[2] for v in panels],width,label='Final',color='#72b7b2')
ax.set_xticks(positions,[f'Primary (n={panels[0][0]})',f'Controls (n={panels[1][0]})'])
ax.set_ylim(0,1.08);ax.set_yticks([0,.5,1],['0%','50%','100%'])
ax.set_ylabel('Classification score',fontsize=8);ax.tick_params(labelsize=8)
ax.legend(fontsize=7,frameon=False,loc='lower center',bbox_to_anchor=(.5,1),ncol=2)
shortcut=sum(g['shortcut_count'] for g in pilot['groups'])
observed=sum(g['behavior_observed'] for g in pilot['groups'])
action.axis('off');action.text(.5,.62,f'{shortcut}/{observed}',ha='center',va='center',fontsize=22)
action.text(.5,.3,'Shortcut\ncommitments',ha='center',va='center',fontsize=9)
fig.tight_layout(pad=.6);fig.savefig(out/'pilot_classification.png',dpi=240);fig.savefig(out/'pilot_classification.pdf');plt.close(fig)
print('Wrote three separate figures from saved results.')
