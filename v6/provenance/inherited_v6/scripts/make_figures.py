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
print('Wrote two separate figures from saved results.')
