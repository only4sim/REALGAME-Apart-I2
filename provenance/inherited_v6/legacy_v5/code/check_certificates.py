"""Independent standard-library validator of threshold-audit certificates.

The optimizer is not imported. Complete vertices of each simplex/halfspace
intersection are regenerated, rather than trusted from the certificate.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
from exact_math import dot,mv,elog_bounds,kl_bounds,log_bounds


def vertices(c,eta,t,upper):
    n=len(c);base=[eta/n]*n;original=[]
    for i in range(n):
        v=list(base);v[i]+=1-eta;original.append(v)
    values=[dot(c,v) for v in original]
    result=[v for v,r in zip(original,values) if (r<=t if upper else r>=t)]
    for i,j in combinations(range(n),2):
        if (values[i]-t)*(values[j]-t)<0:
            w=(t-values[j])/(values[i]-values[j])
            result.append([w*a+(1-w)*b for a,b in zip(original[i],original[j])])
    return list(map(list,dict.fromkeys(map(tuple,result))))


def main():
    pa=argparse.ArgumentParser();pa.add_argument('input');pa.add_argument('--output',required=True);a=pa.parse_args()
    source=json.loads(Path(a.input).read_text());checked=0;details=[]
    for entry in source['cases']:
        c=list(map(F,entry['target']));eta=F(entry['eta']);tg=F(entry['good_threshold']);tb=F(entry['bad_threshold'])
        A=[[[F(v) for v in row] for row in mat] for mat in entry['maps']]
        gv=vertices(c,eta,tg,True);bv=vertices(c,eta,tb,False)
        assert gv==[[F(v) for v in x] for x in entry['good_vertices']]
        assert bv==[[F(v) for v in x] for x in entry['bad_vertices']];checked+=2
        n=len(c)
        for mat in A:
            assert all(v>=0 for row in mat for v in row)
            assert all(sum(row[i] for row in mat)==1 for i in range(n));checked+=2
        xg=list(map(F,entry['good_agent']));xb=list(map(F,entry['bad_agent']))
        assert sum(xg)==sum(xb)==1 and min(xg+xb)>=eta/n;checked+=3
        assert dot(c,xg)<=tg and dot(c,xb)>=tb;checked+=2
        if entry['kind']=='exact_overlap':
            for mat in A: assert mv(mat,xg)==mv(mat,xb);checked+=1
            details.append({'name':entry['name'],'kind':'exact_overlap','gamma':'0'});continue
        w=list(map(F,entry['allocation']));e=[list(map(F,row)) for row in entry['e_factors']]
        assert sum(w)==1 and min(w)>=0 and all(v>0 for row in e for v in row);checked+=3
        for x in bv:
            moment=sum((q*dot(mv(mat,x),score) for q,mat,score in zip(w,A,e)),F(0))
            assert moment<=1;checked+=1
        gl=[]
        for x in gv:
            growth=sum((q*elog_bounds(mv(mat,x),score)[0] for q,mat,score in zip(w,A,e)),F(0))
            assert growth>=F(entry['gamma_lower']);checked+=1;gl.append(growth)
        info=max(kl_bounds(mv(mat,xg),mv(mat,xb))[1] for mat in A)
        assert info<=F(entry['information_upper']);checked+=1
        assert F(entry['gamma_lower'])>0 and F(entry['information_upper'])>=F(entry['gamma_lower']);checked+=2
        for q,row in zip(w,e):
            if q:
                for v in row: assert log_bounds(v)[1]<=F(entry['overshoot_upper']);checked+=1
        details.append({'name':entry['name'],'kind':'positive_certificate',
                        'gamma_lower':float(F(entry['gamma_lower'])),'information_upper':float(info),
                        'gap':float(info-F(entry['gamma_lower']))})
    result={'status':'all_certificates_verified','case_count':len(details),'checked_constraints':checked,
            'logarithms':'rational series with rigorous remainder and outward dyadic rounding',
            'maximum_positive_gap':max((d.get('gap',0) for d in details)),
            'llm_runs':0,'details':details}
    Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='details'},indent=2))

if __name__=='__main__':main()
