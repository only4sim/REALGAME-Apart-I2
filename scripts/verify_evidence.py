#!/usr/bin/env python3
"""Independently audit saved local records without regenerating observations."""
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
import argparse
import hashlib
import json
import math
from verify_repository import verify_manifest

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    original_count = verify_manifest()
    scripted = [json.loads(line) for line in (ROOT / 'results/scripted_runs.jsonl').read_text().splitlines()]
    assert len(scripted) == len({r['run_id'] for r in scripted}) == 960
    assert Counter(r['backend'] for r in scripted) == {'scripted': 960}
    assert Counter(r['status'] for r in scripted) == {'complete': 960}
    primary = [r for r in scripted if not r['scenario']['control']]
    control = [r for r in scripted if r['scenario']['control']]
    assert len(primary) == 768 and len(control) == 192
    assert sum(r['probability_final'] == r['scenario']['world'] for r in primary) == 768
    assert sum(r['probability_final'] == r['scenario']['world'] for r in control) == 96
    lookup = {(r['model'], r['scenario']['family'], r['scenario']['timing'], r['scenario']['budget'],
               r['scenario']['seed'], r['scenario']['control'], r['scenario']['world']): r for r in scripted}
    matched = 0
    for key, r in lookup.items():
        if key[-1] or not (key[2] == 'after' or key[3] == 0 or key[5]):
            continue
        partner = lookup[key[:-1] + (1,)]
        assert r['decision_input_hash'] == partner['decision_input_hash']
        assert r['choice'] == partner['choice']
        matched += 1
    assert matched == 384
    population = read(ROOT / 'results/coverage.json')['rows']
    checks = 0
    for row in population:
        p, q, t0, t1 = (F(row[k]) for k in ('p', 'q', 'theta0', 'theta1'))
        target = (1-p)*t0 + p*t1
        lo, hi = map(F, row['identified_interval'])
        assert lo <= target <= hi and F(row['reference']) == target
        checks += 1
        if 0 < q < 1:
            assert lo == hi == target == F(row['corrected'])
            checks += 1
        elif q == 0:
            assert (lo, hi) == ((1-p)*t0, (1-p)*t0+p) and row['corrected'] is None
        else:
            assert (lo, hi) == (p*t1, p*t1+1-p) and row['corrected'] is None
    assert len(population) == 375 and checks == 600
    samples = [json.loads(line) for line in (ROOT / 'results/coverage_replicates.jsonl').read_text().splitlines()]
    assert len(samples) == len({(r['q'], r['replicate']) for r in samples}) == 3000
    for row in samples:
        c00, c01, c10, c11 = row['counts']
        n, q = row['n'], F(row['q'])
        assert n == c00 + c01 + c10 + c11 == 128
        assert all(isinstance(c, int) and c >= 0 for c in row['counts'])
        assert row['naive'] == float(F(c01+c11, n))
        assert row['weighted'] == float((F(c01, 2)/(1-q) + F(c11, 2)/q)/n)
    for aggregate in read(ROOT / 'results/coverage_sampling.json')['rows']:
        rows = [r for r in samples if r['q'] == aggregate['q']]
        for estimator in ('naive', 'weighted'):
            actual = math.fsum((r[estimator]-.5)**2 for r in rows)/len(rows)
            assert math.isclose(actual, aggregate['mse_'+estimator], rel_tol=1e-12)
    robust = read(ROOT / 'results/robustness.json')
    for row in robust['rows']:
        eta, q = F(row['eta']), F(row['probability_one'])
        den = F(row['normalizer'])
        assert q == F(7,10)-eta
        assert den == (1 if row['mode'] == 'nominal' else 1+eta*F(20,21))
        assert ((1-q)*F(5,3)+q*F(5,7))/den == F(row['null_moment'])
        assert float(F(row['crossing_probability_exact'])) == row['crossing_probability']
        assert len(row['curve']) == row['horizon'] == 200
        assert row['curve'][-1] == row['crossing_probability']
        assert all(a <= b for a,b in zip(row['curve'], row['curve'][1:]))
        if row['mode'] == 'corrected':assert F(row['crossing_probability_exact']) <= F(1,20)
    assert robust['persistent_bit']['nominal_eventual_crossing'] == '3/10'
    result = {'status': 'passed', 'evidence_files_unchanged': original_count,
              'scripted_episodes': len(scripted),
              'matched_input_pairs': matched, 'population_cases': len(population), 'exact_population_checks': checks,
              'sampling_records_checked': len(samples), 'sampling_draws': sum(r['n'] for r in samples),
              'crossing_outputs_checked': len(robust['rows']),
              'certificate_verification': 'Run certificates/code/check_certificates.py; make reproduce performs both checks.',
              'scope': 'Saved-record consistency and numerical reproduction; no new stochastic or model experiment and no human theorem review.'}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
