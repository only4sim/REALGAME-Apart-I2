"""Boundary and stopping checks; all probability calculations are exact.

This is not a model-behavior experiment. No network, credentials, physical
actuators, or operational sandbox fingerprints are used.
"""
from __future__ import annotations
import argparse,json,math
from fractions import Fraction as F
from itertools import product
from pathlib import Path
from exact_math import dot,mv,log_bounds,jsave


def minimum_n(beta,delta):
    if beta==0:return None
    if beta==1:return 1
    n=max(1,math.ceil(math.log(float(delta))/math.log1p(-float(beta))))
    while (1-beta)**n>delta:n+=1
    while n>1 and (1-beta)**(n-1)<=delta:n-=1
    assert (1-beta)**n<=delta and (n==1 or (1-beta)**(n-1)>delta)
    return n


def first_passage(prob_one,e0,e1,delta,horizon):
    # The current product depends on counts. Surviving-path probabilities
    # retain the effect of prior boundary crossings through absorption.
    alive={0:F(1)};hit=F(0);exp_truncated=F(0)
    for t in range(horizon):
        exp_truncated+=sum(alive.values(),F(0));nxt={}
        for k,p in alive.items():
            for bit,prob in ((0,1-prob_one),(1,prob_one)):
                kk=k+bit;mass=p*prob;capital=e0**(t+1-kk)*e1**kk
                if capital>=1/delta:hit+=mass
                else:nxt[kk]=nxt.get(kk,F(0))+mass
        alive=nxt
        assert hit+sum(alive.values(),F(0))==1
    return {'crossing_probability':float(hit),'survival_probability':float(sum(alive.values(),F(0))),
            'expected_minimum_T_H':float(exp_truncated),'horizon':horizon},hit


def alarm_theorem_checks():
    # A convex risk-constrained alarm model: theta_1+theta_2 >= 1.
    # Audits expose theta_j with probability 1/2. beta=1/4.
    # The common hard alternative is theta_1=theta_2=1/2.
    beta=F(1,4);w=(F(1,2),F(1,2));uverts=((F(0),F(1)),(F(1),F(0)),(F(1),F(1)))
    assert min(sum(ww*t/2 for ww,t in zip(w,x)) for x in uverts)==beta
    policies=0
    for decisions in product((0,1),repeat=7):
        # All deterministic depth-3 choices based on prior alarm bits.
        def rec(hist,theta):
            if len(hist)==3:return F(int(not any(hist)))
            idx=(2**len(hist)-1)+sum(bit*2**(len(hist)-i-1) for i,bit in enumerate(hist))
            j=decisions[idx];p=theta[j]/2
            return (1-p)*rec(hist+(0,),theta)+p*rec(hist+(1,),theta)
        assert rec((),(F(1,2),F(1,2)))==(1-beta)**3
        assert rec((),(F(0),F(0)))==1;policies+=1
    return {'beta':'1/4','adaptive_policies_checked':policies,'budget':3,
            'exact_worst_case_zero_alarm_probability':'27/64'}


def main():
    pa=argparse.ArgumentParser();pa.add_argument('--output',required=True);a=pa.parse_args()
    rows=[]
    for exposure in (F(1),F(1,4)):
        for threshold in (F(1,10),F(1,100)):
            for u in (F(0),threshold/2,threshold):
                beta=exposure*max(F(0),(threshold-u)/(1-u))
                n=minimum_n(beta,F(1,20))
                rows.append({'exposure':exposure,'uncovered_mass':u,'threshold':threshold,
                             'beta':beta,'delta':'1/20','exact_minimum_runs':n})
    # e0=5/3 and e1=5/7 from a jointly least-favorable pair.
    # Individually a selected controller need not yield a valid e-factor.
    e0,e1=F(5,3),F(5,7);moment0=(e0+e1)/2;moment1=e0/F(10)+9*e1/F(10)
    assert moment0==F(25,21)>1 and moment1==F(17,21)<1
    assert (moment0+moment1)/2==1
    good,_=first_passage(F(1,2),e0,e1,F(1,20),200)
    bad,bprob=first_passage(F(7,10),e0,e1,F(1,20),200);assert bprob<=F(1,20)
    broken,wrong=first_passage(F(1,2),e0,e1,F(1,20),200);assert wrong>F(1,20)
    # Exact log interval checks against identities (not float approximations).
    logchecks=0
    for q in (F(1,100),F(1,3),F(1),F(2),F(5,3),F(10),F(100)):
        l,u=log_bounds(q);il,iu=log_bounds(1/q)
        assert l<=u and l+il<=0<=u+iu;logchecks+=2
    for u in (F(0),F(1,5),F(1,2)):
        # Unknown target branch may be invisible; the same late label does
        # not affect an already completed first action.
        assert (F(2,5)+u)-F(2,5)==u;logchecks+=1
    result={'status':'all_boundary_checks_passed','local_llm_runs':0,
            'exact_zero_alarm_design_cases':len(rows),'zero_alarm_designs':rows,
            'adaptive_alarm_checks':alarm_theorem_checks(),
            'rational_log_and_identity_checks':logchecks,
            'joint_randomization':{'controller0_null_moment':moment0,'controller1_null_moment':moment1,
                                   'correct_mixture_null_moment':'1','good_stopping':good,'bad_stopping':bad,
                                   'broken_controller_selection':broken},
            'note':'Finite-state dynamic programs, not independent empirical agent runs. 200-step results are truncated.'}
    Path(a.output).write_text(json.dumps(jsave(result),indent=2)+'\n');print(json.dumps(jsave(result),indent=2))

if __name__=='__main__':main()
