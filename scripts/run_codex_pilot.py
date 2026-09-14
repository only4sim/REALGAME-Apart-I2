#!/usr/bin/env python3
"""Run only the authorized, separately frozen, one-worker subscription pilot."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from check_readiness import inference_gates
from run_llm import plan, run_episode, SYSTEM, PROB
from codex_budget import GlobalPilotBudget
from codex_subscription import AccessBlocked
from analyze_codex_pilot import analyze_subject_records


def save_new(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False)+'\n')


def freeze_design(cfg, config_path):
    jobs = plan(cfg, False)
    if len(jobs) != 20 or sum(s.budget+3 for _, s in jobs) != 108:
        raise AccessBlocked('The original one-model, one-repeat generator must yield 20 cells and at most 108 turns')
    paths = [config_path.resolve()]
    for directory in ('src', 'scripts', 'protocol', 'tests', 'access'):
        paths += [p for p in (ROOT/directory).glob('*') if p.is_file() and p.suffix in ('.py', '.json', '.txt', '.md')]
    frozen = {
        'protocol_version': cfg['protocol_version'],
        'frozen_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'config': cfg,
        'source_manifest': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in sorted(set(path.resolve() for path in paths))},
        'planned': [{'model': model, 'scenario': scenario.__dict__} for model, scenario in jobs],
        'protocol_prompts': {'action': SYSTEM, 'post_commit_probability': PROB},
        'maximum_benchmark_turns': 108, 'compatibility_turns_planned': 0,
        'analysis_script': 'scripts/analyze_codex_pilot.py',
        'planned_holm_family_size': 4,
        'all_pilot_comparisons_exploratory': True,
        'exclusions': 'No exclusions or replacement completions. Invalid/refused/truncated outputs remain outcomes; unstarted cells remain in the 20-cell plan.',
        'history_design': cfg['history_mode'],
        'effective_runtime_model_id_may_be_missing': True,
        'note': 'An official client turn can involve multiple backend requests. Local invocation/time limits do not expose provider per-token cost.'}
    return frozen, jobs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit('Use a fresh pilot directory. No resume or overwrite is supported.')
    cfg = json.loads(args.config.read_text())
    if cfg.get('provider') != 'codex_subscription' or cfg.get('workers') != 1:
        raise SystemExit('Only the approved one-worker subscription arm is supported')
    gates = inference_gates(cfg)
    if not gates['ready_by_configuration']:
        raise SystemExit('Subscription gates unresolved: ' + '; '.join(gates['missing']))
    from codex_subject import SubjectProvider
    frozen, jobs = freeze_design(cfg, args.config)
    global_path = ROOT/cfg['global_allowance_ledger_path']
    budget = GlobalPilotBudget(global_path, cfg['global_allowance_scope'],
                               cfg['max_client_invocations'], cfg['inference_wallclock_seconds'])
    if budget.invocations:
        budget.close()
        raise SystemExit('This approved pilot already has invocation records; do not start a replacement cohort automatically')
    args.out.mkdir(parents=True)
    (args.out/'episodes').mkdir()
    save_new(args.out/'frozen_plan.json', frozen)
    for name, expected in frozen['source_manifest'].items():
        original = (ROOT/name).read_bytes()
        if hashlib.sha256(original).hexdigest() != expected:
            raise SystemExit('Source changed during freeze')
        target = args.out/'source_snapshot'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(original)
    save_new(args.out/'readiness_at_freeze.json', gates)
    rows = []
    stopped = None
    try:
        provider = SubjectProvider(cfg, args.out, budget)
        with (args.out/'runs.jsonl').open('x') as ledger:
            for model, scenario in jobs:
                if provider.halted or budget.remaining_seconds() <= 0:
                    stopped = provider.stop_category if provider.halted else 'global_time_cap'
                    break
                before = budget.invocations
                row = run_episode(provider, model, scenario)
                row['client_process_invocations_in_episode'] = budget.invocations-before
                row['client_turn_submissions_in_episode'] = row.pop('api_calls_in_episode')
                row['subject_type'] = 'model_plus_official_codex_client'
                row['backend_request_count'] = None
                rows.append(row)
                ledger.write(json.dumps(row, sort_keys=True, allow_nan=False)+'\n')
                ledger.flush()
                print(json.dumps({'finished_episode_records': len(rows), 'planned': 20,
                                  'client_invocations': budget.invocations,
                                  'turn_submissions': budget.turn_submissions,
                                  'status': row['status']}), flush=True)
                if provider.halted:
                    stopped = provider.stop_category
                    break
    finally:
        budget.close()
    requests = [json.loads(p.read_text()) for p in sorted((args.out/'requests').glob('*.json'))]
    analysis = analyze_subject_records(rows, frozen, requests)
    save_new(args.out/'analysis.json', analysis)
    with (args.out/'visible_records.jsonl').open('x') as stream:
        for record in requests:
            stream.write(json.dumps(record, sort_keys=True, allow_nan=False)+'\n')
    ledger = {
        'protocol_version': cfg['protocol_version'], 'planned_episodes': 20,
        'started_episodes': analysis['started'], 'unstarted_episodes': analysis['unstarted'],
        'committed_action_episodes': analysis['committed_actions'],
        'valid_pre_diagnostic_probability_episodes': analysis['valid_pre_diagnostic_probabilities'],
        'valid_final_probability_episodes': analysis['valid_final_probabilities'],
        'valid_both_probability_episodes': analysis['outcome_accounting']['complete_probability_reports'],
        'refused_episodes': analysis['refused_episodes'],
        'failed_started_episodes': analysis['failed_started_episodes'],
        'global_client_invocations': budget.invocations,
        'global_turn_submission_reservations': budget.turn_submissions,
        'confirmed_turn_submissions': len(requests),
        'global_allowance_ledger': str(global_path.relative_to(ROOT)),
        'global_allowance_sha256': hashlib.sha256(global_path.read_bytes()).hexdigest() if global_path.exists() else None,
        'stopped_reason': stopped, 'compatibility_turns': 0,
        'backend_requests': None, 'monetary_cost_usd': None, 'credit_consumption': None,
        'api_requests': 0, 'new_api_spending_authorized_usd': 0,
        'billing_control_evidence': cfg['billing_control_path'],
        'requested_model': cfg['models'][0],
        'effective_runtime_model_ids': sorted({r['model_returned'] for r in requests if r.get('model_returned')}),
        'requests_missing_effective_runtime_model': sum(r.get('model_returned') is None for r in requests),
        'model_backed_evidence_exists': analysis['model_backed_evidence_exists']}
    save_new(args.out/'usage_failure_ledger.json', ledger)
    print(json.dumps(ledger, indent=2))


if __name__ == '__main__':
    main()
