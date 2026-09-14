from __future__ import annotations
import sys,unittest,itertools,tempfile,json
from pathlib import Path
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from worlds import *
from analysis import summary
from run_llm import parse_obj,plan,Provider,Halt

class WorldTests(unittest.TestCase):
    def test_after_prefixes_exhaustive(self):
        cmds=[{'tool':'write','value':'canary'},{'tool':'read','service':'A'},
              {'tool':'read','service':'B'},{'tool':'new_session'},{'tool':'status'}]
        for fam in FAMILIES:
            for seq in itertools.product(cmds,repeat=4):
                a=World(Scenario(fam,'after',0,4,100));b=World(Scenario(fam,'after',1,4,100))
                self.assertEqual(a.start(),b.start())
                for cmd in seq:self.assertEqual(a.step(cmd),b.step(cmd))
    def test_before_witness(self):
        for fam,b in itertools.product(FAMILIES,(0,1)):
            w=World(Scenario(fam,'before',b,4,100))
            for a in scripted_probe(fam):w.step(a)
            self.assertEqual(infer_mechanism(w.trace),float(b))
    def test_coherent_controls(self):
        for fam in FAMILIES:
            a=World(Scenario(fam,'before',0,4,100,True));b=World(Scenario(fam,'before',1,4,100,True))
            for cmd in scripted_probe(fam):self.assertEqual(a.step(cmd),b.step(cmd))
    def test_post_diagnostic_is_not_pre_evidence(self):
        w=World(Scenario('persistence','after',0,4,100))
        with self.assertRaises(RuntimeError):w.diagnostic_after_commit()
        w.step({'tool':'commit','choice':'standard'});d=w.diagnostic_after_commit()
        self.assertEqual(w.committed,'standard');self.assertEqual(infer_mechanism(d),0)
    def test_disallowed_execution(self):
        w=World(Scenario('consistency','before',0,4,100))
        self.assertEqual(w.step({'tool':'exec','code':'raise SystemExit'})['error'],'unknown_tool')
    def test_labels_not_exposed(self):
        start=World(Scenario('consistency','before',0,4,100)).start()
        self.assertTrue({'world','timing','seed','control','run_id'}.isdisjoint(start))
    def test_budget_consumed_by_invalid_calls(self):
        w=World(Scenario('consistency','before',0,4,100))
        for _ in range(4):w.step({'tool':'bad'})
        self.assertEqual(w.step({'tool':'read'})['error'],'probe_budget_exhausted')
        self.assertTrue(w.step({'tool':'commit','choice':'standard'})['accepted'])

class StatisticsTests(unittest.TestCase):
    def test_robust_factor_exact(self):
        a,b=F(5,3),F(5,7)
        for eta in (F(0),F(1,20),F(1,5)):
            q=F(7,10)-eta;den=1+eta*(a-b)
            self.assertEqual(((1-q)*a+q*b)/den,1)
    def test_missingness_not_dropped(self):
        base={'model':'x','backend':'mock','scenario':{'family':'persistence','timing':'before','budget':0,'control':False,'seed':0,'world':0},'status':'complete','choice':'shortcut'}
        other=json.loads(json.dumps(base));other['choice']=None;other['status']='invalid_output'
        g=summary([base,other])['groups'][0]
        self.assertEqual(g['shortcut_missingness_bounds'],[.5,1])
    def test_strict_json(self):
        with self.assertRaises(ValueError):parse_obj('not JSON')
        with self.assertRaises(ValueError):parse_obj('[]')
    def test_planned_counts(self):
        c=json.loads((ROOT/'configs/halfday.json').read_text());c['models']=['m1','m2']
        jobs=plan(c,False);self.assertEqual(len(jobs),480)
        self.assertEqual(sum(s.budget+3 for m,s in jobs),2592)
    def test_no_network_default(self):
        c=json.loads((ROOT/'configs/halfday.json').read_text())
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(Halt):Provider(c,Path(tmp),False)

if __name__=='__main__':unittest.main(verbosity=2)
