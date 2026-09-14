"""Propose convex threshold-audit designs, then certify them rationally.

SciPy proposes only. All retained moments, policy constraints, and
information brackets are verified independently by check_certificates.py.
The examples are finite local probability models, not LLM experiments.
"""
from __future__ import annotations
import argparse,json
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
import numpy as np
from scipy.optimize import minimize,linprog
from exact_math import dot,mv,log_bounds,elog_bounds,kl_bounds,jsave
from finite_model import (safe_worlds,deployment_worlds,pure_realizations,
                         observation_matrix,target_vector,losses)


def clipped_vertices(c,eta,bound,lower=False):
    k=len(c);base=[eta/k]*k;verts=[]
    for i in range(k):
        x=list(base);x[i]+=1-eta;verts.append(x)
    vals=[dot(c,x) for x in verts]
    ok=lambda v: v>=bound if lower else v<=bound
    out=[x for x,v in zip(verts,vals) if ok(v)]
    for i,j in combinations(range(k),2):
        if (vals[i]-bound)*(vals[j]-bound)<0:
            t=(bound-vals[j])/(vals[i]-vals[j])
            out.append([t*a+(1-t)*b for a,b in zip(verts[i],verts[j])])
    return list(map(list,dict.fromkeys(map(tuple,out))))


def frac_simplex(a,den=10**8):
    # Largest-remainder rounding preserves a probability simplex exactly,
    # including zero coordinates of boundary strategies.
    z=[F(max(float(v),0.0)) for v in a]
    total=sum(z,F(0))
    if total<=0: raise ArithmeticError('Zero candidate probability mass.')
    z=[v/total for v in z];raw=[v*den for v in z]
    ints=[v.numerator//v.denominator for v in raw]
    order=sorted(range(len(z)),key=lambda i:(-(raw[i]-ints[i]),i))
    for i in order[:den-sum(ints)]: ints[i]+=1
    assert sum(ints)==den and min(ints)>=0
    return [F(v,den) for v in ints]


def repair(a,vertices,c,eta,bound,lower=False):
    x=frac_simplex(a);k=len(x)
    center=[sum((v[i] for v in vertices),F(0))/len(vertices) for i in range(k)]
    # Mix toward a strict relative interior point whenever a rational inequality fails.
    constraints=[([F(int(i==j)) for j in range(k)],eta/k) for i in range(k)]
    constraints.append((list(c) if lower else [-v for v in c],bound if lower else -bound))
    t=F(0)
    for a,b in constraints:
        ax=dot(a,x);ac=dot(a,center)
        if ax<b:
            if ac<=ax: raise ArithmeticError('Cannot repair a candidate.')
            t=max(t,(b-ax)/(ac-ax))
    if t: t=min(F(1),t+F(1,10**10))
    x=[(1-t)*a+t*b for a,b in zip(x,center)]
    assert sum(x)==1 and all(dot(a,x)>=b for a,b in constraints)
    return x


def cases():
    raw=list(dict.fromkeys(tuple(v) for v in pure_realizations()))
    worlds=safe_worlds();W=deployment_worlds()[4]
    menus=[('missing',(worlds[0],)),('complementary',(worlds[0],worlds[1])),
           ('overlap',(worlds[3],)),('reactive',(worlds[2],worlds[3]))]
    def mats(menu,proj=lambda z:z):
        ans=[]
        for e in menu:
            A=[[dot(r,x) for x in raw] for r in observation_matrix(e,proj)]
            ans.append([r for r in A if any(r)])
        return ans
    for name,menu in menus:
        for target in ('first_action','second_action'):
            c=[dot(target_vector(W,losses()[target]),x) for x in raw]
            for g,b in [(F(1,10),F(1,5)),(F(1,4),F(3,4))]:
                yield name+'/'+target+f'/{g}_{b}',mats(menu),c,g,b
    for proj,name in [(lambda z:(z[2],),'action_only'),
                      (lambda z:(z[1],z[2]),'context_action'),
                      (lambda z:(z[0],z[1],z[2]),'full_predecision')]:
        c=[dot(target_vector(W,losses()['second_action']),x) for x in raw]
        yield 'logger/'+name,mats((worlds[3],),proj),c,F(1,10),F(3,10)


def solve(name,A,c,tg,tb,eta=F(1,20),smoothing=F(0)):
    k=len(c);m=len(A)
    gv=clipped_vertices(c,eta,tg);bv=clipped_vertices(c,eta,tb,True)
    workA=[[[((1-smoothing)*v+smoothing/len(a)) for v in row] for row in a] for a in A]
    Af=[np.array(a,dtype=float) for a in workA];cf=np.array(c,dtype=float)
    xg=np.mean(np.array(gv,dtype=float),axis=0);xb=np.mean(np.array(bv,dtype=float),axis=0)
    # Detect exactly indistinguishable good/bad agents before applying logarithmic optimization.
    eq=[];rhs=[]
    eq.append(np.r_[np.ones(k),np.zeros(k)]);rhs.append(1.)
    eq.append(np.r_[np.zeros(k),np.ones(k)]);rhs.append(1.)
    for a in A:
        for row in np.array(a,dtype=float): eq.append(np.r_[row,-row]);rhs.append(0.)
    lp=linprog(np.zeros(2*k),A_ub=[np.r_[cf,np.zeros(k)],np.r_[np.zeros(k),-cf]],
               b_ub=[float(tg),-float(tb)],A_eq=eq,b_eq=rhs,
               bounds=[(float(eta/k),1)]*(2*k),method='highs')
    common={'name':name,'maps':A,'target':c,'eta':eta,'good_threshold':tg,'bad_threshold':tb,
            'good_vertices':gv,'bad_vertices':bv,'virtual_smoothing':smoothing}
    if lp.success:
        q=[F(float(v)).limit_denominator(10**7) for v in lp.x]
        g,b=q[:k],q[k:]
        if sum(g)==sum(b)==1 and min(g+b)>=eta/k and dot(c,g)<=tg and dot(c,b)>=tb and all(mv(a,g)==mv(a,b) for a in A):
            return common|{'kind':'exact_overlap','good_agent':g,'bad_agent':b,'gamma':'0',
                           'solver_status':str(lp.message)}
        # Never turn a floating overlap assertion into an impossibility certificate.
        raise ArithmeticError('Overlap LP needs an exact rational witness.')
    def Ds(z):
        p=[a@z[:k] for a in Af];q=[a@z[k:2*k] for a in Af]
        return np.array([np.dot(u,np.log(u/v)) for u,v in zip(p,q)])
    def gradD(z):
        out=[]
        for a in Af:
            p=a@z[:k];q=a@z[k:2*k]
            out.append(np.r_[a.T@(np.log(p/q)+1),-a.T@(p/q),0.])
        return np.array(out)
    z0=np.r_[xg,xb,max(Ds(np.r_[xg,xb]))+.01]
    cons=[{'type':'eq','fun':lambda z: np.array([sum(z[:k])-1,sum(z[k:2*k])-1]),
           'jac':lambda z:np.array([np.r_[np.ones(k),np.zeros(k+1)],np.r_[np.zeros(k),np.ones(k),0.]])},
          {'type':'ineq','fun':lambda z:np.array([float(tg)-cf@z[:k],cf@z[k:2*k]-float(tb)]),
           'jac':lambda z:np.array([np.r_[-cf,np.zeros(k+1)],np.r_[np.zeros(k),cf,0.]])},
          {'type':'ineq','fun':lambda z:z[-1]-Ds(z),
           'jac':lambda z:np.tile(np.r_[np.zeros(2*k),1.],(m,1))-gradD(z)}]
    opt=minimize(lambda z:z[-1],z0,jac=lambda z:np.r_[np.zeros(2*k),1.],constraints=cons,
                 bounds=[(float(eta/k),1)]*(2*k)+[(0,None)],method='SLSQP',
                 options={'ftol':1e-12,'maxiter':2000})
    g=repair(opt.x[:k],gv,c,eta,tg);b=repair(opt.x[k:2*k],bv,c,eta,tb,True)
    if eta==0:
        # A feasible interior hard pair gives finite original KL values.
        # This does not restrict the class on which soundness is checked.
        mix=F(1,10**8)
        cg=[sum((v[i] for v in gv),F(0))/len(gv) for i in range(k)]
        cb=[sum((v[i] for v in bv),F(0))/len(bv) for i in range(k)]
        g=[(1-mix)*v+mix*u for v,u in zip(g,cg)]
        b=[(1-mix)*v+mix*u for v,u in zip(b,cb)]
    pg=[mv(a,g) for a in A];pb=[mv(a,b) for a in A]
    wg=[mv(a,g) for a in workA];wb=[mv(a,b) for a in workA]
    e=[[F(round((u/v)*2**40),2**40) for u,v in zip(p,q)] for p,q in zip(wg,wb)]
    # Average the virtual-channel factor. No record is changed or fabricated.
    e=[[(1-smoothing)*v+smoothing*sum(row,F(0))/len(row) for v in row] for row in e]
    # For this proposed pair, find a mixture obeying all null moment constraints.
    # A small numerical slack is removed by exact normalization below.
    growth=np.array([[sum(float(p)*np.log(float(s)) for p,s in zip(mv(a,x),ee)) for a,ee in zip(A,e)] for x in gv])
    moments=np.array([[float(dot(mv(a,x),ee)) for a,ee in zip(A,e)] for x in bv])
    wl=linprog(np.r_[np.zeros(m),-1.],A_ub=np.vstack([np.c_[-growth,np.ones(len(gv))],np.c_[moments,np.zeros(len(bv))]]),
               b_ub=np.r_[np.zeros(len(gv)),np.ones(len(bv))+1e-7],A_eq=[np.r_[np.ones(m),0]],b_eq=[1],
               bounds=[(0,1)]*m+[(None,None)],method='highs')
    allocation_method='linear_program'
    if wl.success:
        ww=wl.x[:m]
    elif m==1:
        ww=np.ones(1);allocation_method='single_controller_exact_normalization'
    elif m==2:
        grid=np.linspace(0,1,10001);ws=np.array([grid,1-grid])
        score=np.min(growth@ws,axis=0)-np.log(np.maximum(1,np.max(moments@ws,axis=0)))
        ww=ws[:,int(np.argmax(score))];allocation_method='grid_proposal_exact_normalization'
    else:
        ww=np.ones(m)/m;allocation_method='uniform_proposal_exact_normalization'
    w=frac_simplex(ww);C=max(F(1),max(sum((ww*dot(mv(a,x),ee) for ww,a,ee in zip(w,A,e)),F(0)) for x in bv))
    e=[[v/C for v in ee] for ee in e]
    gamma=min(sum((ww*elog_bounds(mv(a,x),ee)[0] for ww,a,ee in zip(w,A,e)),F(0)) for x in gv)
    info=max(kl_bounds(p,q)[1] for p,q in zip(pg,pb))
    overshoot=max(F(0),max(log_bounds(v)[1] for ww,ee in zip(w,e) if ww for v in ee))
    return common|{'kind':'positive_certificate','good_agent':g,'bad_agent':b,
                   'allocation':w,'e_factors':e,'normalizer':C,'gamma_lower':gamma,
                   'information_upper':info,'overshoot_upper':overshoot,
                   'allocation_method':allocation_method,'allocation_solver_success':bool(wl.success),'solver_success':bool(opt.success),'solver_status':str(opt.message),
                   'certified_gap_float':float(info-gamma),'gamma_float':float(gamma),'information_float':float(info)}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--full-class',action='store_true');args=p.parse_args()
    out=[]
    for name,A,c,g,b in cases():
        result=solve(name,A,c,g,b,eta=F(0) if args.full_class else F(1,20),smoothing=F(1,1000) if args.full_class else F(0));out.append(result)
        print(name,result['kind'],result.get('gamma_float'),result.get('certified_gap_float'),flush=True)
    summary={'status':'complete','case_count':len(out),'positive_count':sum(v['kind']=='positive_certificate' for v in out),
             'overlap_count':sum(v['kind']=='exact_overlap' for v in out),'llm_runs':0,'cases':out}
    Path(args.output).write_text(json.dumps(jsave(summary),indent=2)+'\n')

if __name__=='__main__': main()
