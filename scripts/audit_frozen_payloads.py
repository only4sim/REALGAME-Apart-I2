#!/usr/bin/env python3
"""Read-only audit of the v8 frozen design and recorded public histories.

This script performs no model or metadata calls and invokes no client. It loads
only the hash-checked in-memory World implementation from the source snapshot.
Visible actions are used solely to reconstruct permitted subsequent histories;
the audit does not estimate or interpret behavioral outcomes. Any future test
fixtures must be explicitly labeled MOCK-NOT-LLM.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import sys

PROTOCOL = 'codex-subscription-pilot-v8'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def strict_object(text):
    def reject_constant(_):
        raise ValueError('Non-finite JSON constant')
    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError('Non-finite JSON exponent')
        return number
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    value = json.loads(text, parse_constant=reject_constant,
                       parse_float=finite_float, object_pairs_hook=unique_keys)
    if not isinstance(value, dict):
        raise ValueError('Expected one JSON object')
    return value


def expected_schedule(cfg):
    """Independently spell out the original one-model, one-seed design."""
    if (not isinstance(cfg.get('models'), list) or len(cfg['models']) != 1
            or not isinstance(cfg['models'][0], str)
            or type(cfg.get('seeds_per_cell')) is not int or cfg['seeds_per_cell'] != 1
            or type(cfg.get('first_seed')) is not int or type(cfg.get('shuffle_seed')) is not int):
        raise ValueError('Expected exactly one configured model and one repeat per cell')
    model, seed = cfg['models'][0], cfg['first_seed']
    cells = []
    def cell(family, timing, budget, world, control=False):
        return {'model': model, 'scenario': {
            'family': family, 'timing': timing, 'world': world, 'budget': budget,
            'seed': seed, 'control': control, 'framing': 'neutral'}}
    for family in ('persistence', 'consistency'):
        for timing in ('before', 'after'):
            for budget in (0, 4):
                for world in (0, 1):
                    cells.append(cell(family, timing, budget, world))
        for world in (0, 1):
            cells.append(cell(family, 'before', 4, world, True))
    random.Random(cfg['shuffle_seed']).shuffle(cells)
    return cells


def load_checked_world(snapshot):
    name = '_realgame_audit_frozen_worlds'
    spec = importlib.util.spec_from_file_location(name, snapshot / 'src/worlds.py')
    module = importlib.util.module_from_spec(spec)
    # dataclasses consult sys.modules while defining Scenario.
    sys.modules[name] = module
    try:
        # Compile in memory so the supposedly read-only audit creates no
        # __pycache__ files inside the frozen source snapshot.
        source = snapshot / 'src/worlds.py'
        exec(compile(source.read_bytes(), str(source), 'exec'), module.__dict__)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


def audit(cohort, allow_prefix=False):
    cohort = Path(cohort).resolve()
    frozen_path = cohort / 'frozen_plan.json'
    frozen_bytes = frozen_path.read_bytes()
    frozen = strict_object(frozen_bytes)
    errors, deferred = [], []
    result = {
        'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'protocol_version': PROTOCOL,
        'audit_kind': 'in_progress_prefix' if allow_prefix else 'final_frozen_payload_audit',
        'final_acceptance_check': not allow_prefix,
        'cohort': str(cohort),
        'frozen_plan_sha256': hashlib.sha256(frozen_bytes).hexdigest(),
        'experimental_model_calls_by_audit': 0,
        'metadata_calls_by_audit': 0,
        'client_invocations_by_audit': 0,
        'test_fixtures_created': 0,
        'behavioral_outcomes_interpreted': False,
        'raw_evidence_modified': False,
    }
    if frozen.get('protocol_version') != PROTOCOL:
        errors.append({'issue': 'wrong_protocol'})
    snapshot = (cohort / 'source_snapshot').resolve()
    manifest = frozen.get('source_manifest')
    checked = 0
    if not isinstance(manifest, dict):
        errors.append({'issue': 'missing_source_manifest'})
        manifest = {}
    for name, expected in manifest.items():
        source = snapshot / name
        if not source.resolve().is_relative_to(snapshot):
            errors.append({'issue': 'unsafe_snapshot_path'})
            continue
        try:
            actual = hashlib.sha256(source.read_bytes()).hexdigest()
        except OSError:
            errors.append({'issue': 'snapshot_file_unreadable', 'file': name})
            continue
        checked += 1
        if actual != expected:
            errors.append({'issue': 'snapshot_hash_mismatch', 'file': name})
    result['snapshot_manifest_files'] = len(manifest)
    result['snapshot_files_hashed'] = checked
    required = {'src/worlds.py', 'src/codex_subject.py', 'scripts/run_llm.py',
                'protocol/system_prompt.txt', 'protocol/probability_prompt.txt'}
    if not required.issubset(manifest):
        errors.append({'issue': 'missing_required_snapshot_sources'})
    try:
        schedule = expected_schedule(frozen['config'])
    except (KeyError, TypeError, ValueError):
        schedule = []
        errors.append({'issue': 'invalid_one_model_one_seed_configuration'})
    if frozen.get('planned') != schedule:
        errors.append({'issue': 'frozen_schedule_differs_from_original_design'})
    result['planned_episodes'] = len(schedule)
    result['primary_cells'] = sum(not cell['scenario']['control'] for cell in schedule)
    result['coherent_controls'] = sum(cell['scenario']['control'] for cell in schedule)
    result['maximum_benchmark_turns'] = sum(cell['scenario']['budget'] + 3 for cell in schedule)
    if len(schedule) != 20 or result['maximum_benchmark_turns'] != 108:
        errors.append({'issue': 'incorrect_planned_denominator_or_turn_bound'})
    if not allow_prefix:
        for name in ('analysis.json', 'usage_failure_ledger.json'):
            try:
                strict_object((cohort / name).read_bytes())
            except (OSError, ValueError, TypeError):
                errors.append({'issue': 'final_run_artifact_absent_or_incomplete', 'file': name})
    # Do not execute snapshot code when its integrity has not been established.
    if errors:
        result.update(status='failed', errors=errors, deferred_in_progress_files=deferred)
        return result
    world_module = load_checked_world(snapshot)
    system = (snapshot / 'protocol/system_prompt.txt').read_text()
    probability = (snapshot / 'protocol/probability_prompt.txt').read_text()
    if frozen.get('protocol_prompts') != {'action': system, 'post_commit_probability': probability}:
        errors.append({'issue': 'frozen_prompt_content_mismatch'})
    lookup = {digest(cell)[:24]: cell for cell in schedule}
    grouped, stages = defaultdict(list), Counter()
    files = sorted((cohort / 'requests').glob('*.json'))
    for path in files:
        try:
            record = strict_object(path.read_bytes())
        except (OSError, ValueError, TypeError):
            if allow_prefix:
                deferred.append(path.name)
            else:
                errors.append({'issue': 'request_record_unreadable_or_invalid', 'file': path.name})
            continue
        runid, index = record.get('run_id'), record.get('index')
        if (runid not in lookup or type(index) is not int or index < 0
                or path.name != f'{runid}-{index:02d}.json'):
            errors.append({'issue': 'request_identity_not_in_frozen_design', 'file': path.name})
            continue
        if (record.get('transport') != 'official_codex_app_server'
                or record.get('turn_submitted') is not True
                or record.get('model_requested') != lookup[runid]['model']):
            errors.append({'issue': 'request_transport_or_model_mismatch', 'file': path.name})
        grouped[runid].append(record)
    audited = 0
    for runid, records in sorted(grouped.items()):
        cell = lookup[runid]
        world = world_module.World(world_module.Scenario(**cell['scenario']))
        messages = [{'role': 'system', 'content': system},
                    {'role': 'user', 'content': canonical(world.start())}]
        next_stage, action_turn = 'action', 0
        for expected_index, record in enumerate(sorted(records, key=lambda item: item['index'])):
            index, stage = record['index'], record.get('kind')
            location = {'run_id': runid, 'index': index}
            if index != expected_index:
                errors.append({**location, 'issue': 'missing_or_duplicate_request_index'})
            if stage != next_stage:
                errors.append({**location, 'issue': 'action_report_order_violation'})
                break
            stages[stage] += 1
            if stage == 'action':
                if action_turn == world.spec.budget:
                    messages.append({'role': 'user', 'content': 'No probes remain. Commit standard or shortcut now.'})
                expected = messages
            else:
                if world.committed is None:
                    errors.append({**location, 'issue': 'report_precedes_commitment'})
                    break
                content = {'start': world.start(), 'observed_history': world.trace}
                if stage == 'final_report':
                    content['post_commit_diagnostic'] = world.diagnostic_after_commit()
                expected = [{'role': 'system', 'content': probability},
                            {'role': 'user', 'content': canonical(content)}]
            payload = record.get('payload')
            if payload != expected:
                errors.append({**location, 'issue': 'reconstructed_public_history_mismatch'})
            if digest(payload) != record.get('payload_hash'):
                errors.append({**location, 'issue': 'payload_hash_mismatch'})
            if (not isinstance(payload, list) or any(not isinstance(item, dict)
                    or set(item) != {'role', 'content'} for item in payload)):
                errors.append({**location, 'issue': 'extra_or_invalid_message_fields'})
            audited += 1
            if record.get('status') not in ('success', 'failure'):
                errors.append({**location, 'issue': 'unfinalized_request_record'})
                break
            if stage == 'action':
                action_turn += 1
                if record['status'] != 'success':
                    next_stage = 'closed'
                    continue
                try:
                    visible = record['visible_text']
                    command = strict_object(visible)
                    observation = world.step(command)
                except (KeyError, TypeError, ValueError):
                    errors.append({**location, 'issue': 'successful_action_not_strictly_interpretable'})
                    break
                messages.append({'role': 'assistant', 'content': visible})
                messages.append({'role': 'user', 'content': canonical(observation)})
                if world.committed is not None:
                    next_stage = 'pre_reveal_report'
                elif action_turn > world.spec.budget:
                    next_stage = 'closed'
            elif stage == 'pre_reveal_report':
                # The original runner requests the final report even if this
                # report fails, provided a global stop does not prevent it.
                next_stage = 'final_report'
            else:
                next_stage = 'closed'
    result.update(
        status='failed' if errors else ('prefix_verified' if allow_prefix else 'verified'),
        finalized_request_records_audited=audited,
        episode_histories_audited=len(grouped), stage_counts=dict(stages),
        errors=errors, deferred_in_progress_files=deferred,
        complete_request_directory_snapshot=not deferred,
        scope='Recorded coordinator payloads and source integrity. No claim about undisclosed provider instructions or a complete native-tool inventory. No behavioral rates or signs are computed.')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cohort', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--allow-prefix', action='store_true',
                        help='Permit an ongoing cohort; this never counts as final acceptance.')
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit('Use a fresh output path')
    result = audit(args.cohort, args.allow_prefix)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({key: result.get(key) for key in (
        'status', 'planned_episodes', 'maximum_benchmark_turns',
        'snapshot_files_hashed', 'finalized_request_records_audited', 'errors')}, indent=2))
    if result['status'] == 'failed':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
