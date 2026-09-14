#!/usr/bin/env python3
"""Analyze the separate official-client arm with full planned denominators."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from analyze_llm import outcome_accounting, paired_label_test, valid_probability
sys.path.insert(0, str(ROOT/'src'))
from analysis import summary


def analyze_blocked_design(rows, frozen, visible_records):
    if frozen.get('protocol_version') != 'codex-subscription-pilot-v8':
        raise ValueError('A separate v8 frozen plan is required')
    if rows or visible_records:
        raise ValueError('The metadata-only adapter cannot establish provenance for subject records')
    result = outcome_accounting(rows, frozen, visible_records)
    result['charged_estimated_usd'] = None
    result.update(
        real_model_calls_documented=False, subject_type='model_plus_official_codex_client',
        probability_and_shortcut_outcomes_measured=False, planned_holm_family_size=4,
        inferential_statistics=None, interpretation='All planned episodes are unstarted. Access/control failures are not model outcomes; [0,1] missingness bounds contain no empirical information.')
    return result


def analyze_subject_records(rows, frozen, requests):
    if frozen.get('protocol_version') != 'codex-subscription-pilot-v8':
        raise ValueError('A separate v8 frozen plan is required')
    if len({row['run_id'] for row in rows}) != len(rows):
        raise ValueError('Duplicate subject records')
    if any(request.get('transport') != 'official_codex_app_server'
           or request.get('turn_submitted') is not True for request in requests):
        raise ValueError('Request provenance does not establish an official client turn')
    if any(row.get('backend') != 'codex_subscription' for row in rows):
        raise ValueError('Do not pool API, scripted or mock cohorts into the subscription arm')
    attempted = [row for row in rows if row.get('attempted')]
    attempted_by_id = {row['run_id']: row for row in attempted}
    request_keys = set()
    for request in requests:
        key = (request.get('run_id'), request.get('index'))
        if key in request_keys:
            raise ValueError('Duplicate submitted request records')
        request_keys.add(key)
        row = attempted_by_id.get(request.get('run_id'))
        if row is None or request.get('model_requested') != row['model']:
            raise ValueError('Submitted request lacks a matching attempted episode/model record')
    request_runids = {request['run_id'] for request in requests}
    if any(row['run_id'] not in request_runids for row in attempted):
        raise ValueError('Attempted episode is missing its official-client request record')
    for row in rows:
        for field in ('probability_pre_reveal', 'probability_final'):
            if row.get(field) is not None and not valid_probability(row[field]):
                raise ValueError('Invalid saved probability; do not repair it')
    accounting = outcome_accounting(rows, frozen, requests)
    accounting['charged_estimated_usd'] = None
    result = summary(attempted)
    result.pop('llm_runs', None)
    documented_runids = {r['run_id'] for r in requests if r.get('visible_messages') or r.get('visible_text')}
    tests = []
    for model in frozen['config']['models']:
        for family in ('persistence', 'consistency'):
            selected = [row for row in attempted if row['model'] == model
                        and row['scenario']['family'] == family
                        and row['scenario']['timing'] == 'before'
                        and row['scenario']['budget'] == 4 and not row['scenario']['control']]
            test = paired_label_test(selected)
            test.update(model=model, family=family, interpretation='exploratory pilot')
            tests.append(test)
    previous = 0.
    order = sorted(range(len(tests)), key=lambda i: tests[i]['p_one_sided'] if tests[i]['p_one_sided'] is not None else 1.)
    for rank, i in enumerate(order):
        p = tests[i]['p_one_sided']
        adjusted = min(1., max(previous, (4-rank)*(p if p is not None else 1.)))
        previous = adjusted
        tests[i]['holm_adjusted_p'] = adjusted if p is not None else None
    for group in result['groups']:
        selected = [row for row in attempted if all(
            (row['model'] if key == 'model' else row['scenario'][key]) == group[key]
            for key in ('model', 'family', 'timing', 'budget', 'control'))]
        pre = [row for row in selected if valid_probability(row.get('probability_pre_reveal'))]
        group['pre_reveal_brier'] = sum((row['probability_pre_reveal']-row['scenario']['world'])**2 for row in pre)/len(pre) if pre else None
        group['probe_calls_total'] = sum(row.get('probe_calls', 0) for row in selected)
        group['probe_usage_denominator'] = len(selected)
    refused = {row['run_id'] for row in attempted if any(
        failure.get('category') == 'refusal' for failure in row.get('outcome_failures', []))}
    result.update(protocol_version=frozen['protocol_version'],
                  subject_type='model_plus_official_codex_client',
                  outcome_accounting=accounting,
                  codex_client_episodes_with_visible_model_output=len(documented_runids),
                  api_model_episodes=0, model_backed_evidence_exists=bool(documented_runids),
                  planned=accounting['planned_episodes'], started=len(attempted),
                  unstarted=accounting['unstarted_episodes'],
                  committed_actions=accounting['completed_actions'],
                  valid_pre_diagnostic_probabilities=sum(valid_probability(row.get('probability_pre_reveal')) for row in attempted),
                  valid_final_probabilities=sum(valid_probability(row.get('probability_final')) for row in attempted),
                  refused_episodes=len(refused),
                  failed_started_episodes=sum(row['status'] != 'complete' for row in attempted),
                  primary_tests=tests, holm_family_size=4,
                  monetary_cost_usd=None, credit_consumption=None,
                  claim_limits='Exploratory Codex-client-system results, not raw-API estimates, internal-belief measurements, causal mediation, equivalence, intent, or deployment safety certification.')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit('Use a fresh analysis path')
    frozen = json.loads((args.input.parent/'frozen_plan.json').read_text())
    rows = [json.loads(line) for line in args.input.read_text().splitlines() if line.strip()]
    requests = [json.loads(path.read_text()) for path in sorted((args.input.parent/'requests').glob('*.json'))]
    result = analyze_subject_records(rows, frozen, requests)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'planned': result['planned'], 'started': result['started'],
                      'monetary_cost_usd': None}, indent=2))


if __name__ == '__main__':
    main()
