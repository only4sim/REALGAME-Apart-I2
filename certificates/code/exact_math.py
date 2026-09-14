"""Exact rational arithmetic and certified logarithm intervals.

Logarithms use the atanh series after reduction to [1,2). No floating
point logarithm is trusted by the certificate checker.
"""
from __future__ import annotations
from fractions import Fraction as F
from functools import lru_cache


def dot(a,b):
    return sum((u*v for u,v in zip(a,b,strict=True)),F(0))


def mv(A,x):
    return [dot(r,x) for r in A]


@lru_cache(maxsize=None)
def log_bounds(q:F,terms:int=24):
    q=F(q)
    if q<=0: raise ValueError('The logarithm argument must be positive.')
    k=0
    while q>=2: q/=2; k+=1
    while q<1: q*=2; k-=1
    def base(m):
        z=(m-1)/(m+1); zz=z*z; power=z; acc=F(0)
        for t in range(terms):
            acc+=2*power/(2*t+1); power*=zz
        err=2*power/((2*terms+1)*(1-zz))
        return acc,acc+err
    lo,hi=base(q); l2,u2=base(F(2))
    if k>=0: lo,hi=lo+k*l2,hi+k*u2
    else: lo,hi=lo+k*u2,hi+k*l2
    # Outward dyadic rounding controls certificate size, never narrows the interval.
    scale=2**100
    low=(lo.numerator*scale)//lo.denominator
    high=-((-hi.numerator*scale)//hi.denominator)
    return F(low,scale),F(high,scale)


def elog_bounds(p,e):
    lo=hi=F(0)
    for a,b in zip(p,e,strict=True):
        if a:
            l,u=log_bounds(b);lo+=a*l;hi+=a*u
    return lo,hi


def kl_bounds(p,q):
    return elog_bounds(p,[a/b for a,b in zip(p,q,strict=True)])


def jsave(x):
    if isinstance(x,F): return str(x)
    if isinstance(x,dict): return {k:jsave(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [jsave(v) for v in x]
    return x
