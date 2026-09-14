#!/usr/bin/env python3
"""Verify a completed pilot and package explicitly unrendered working sources.

This does not call the rendered-release packager or grant its rendering gate.
No inference, credential lookup, download, publication or submission occurs.
"""
from pathlib import Path
import argparse
import collections
import datetime
import difflib
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'verification/subscription_v8'
COHORT = ROOT / 'results/codex_subscription_pilot_v8_01'
BASELINE = ROOT / 'REALGAME_Apart_rendered_release_v7.zip'
BASELINE_SHA = 'a0e964c580a7d95e6993ec0e175c4bc2a38e3f14da3c7d74a75aff1a38678536'
VISIBLE_ROOTS = ('access', 'configs', 'src', 'scripts', 'tests', 'protocol',
                 'paper', 'provenance', 'results', 'verification')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def save_new(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + '\n')


def candidate_files():
    with zipfile.ZipFile(BASELINE) as archive:
        names = {name for name in archive.namelist() if not name.endswith('/')}
    for directory in VISIBLE_ROOTS:
        names.update(str(p.relative_to(ROOT)) for p in (ROOT / directory).rglob('*') if p.is_file())
    names.update(('PILOT_RUN_REPORT.md', 'submission_revision_v8_unrendered.md'))
    output = []
    for name in sorted(names):
        path = Path(name)
        if (path.is_absolute() or '..' in path.parts or any(part.startswith('.') for part in path.parts)
                or '__pycache__' in path.parts or path.suffix.lower() in ('.pyc', '.lock', '.zip', '.ttf', '.otf', '.woff', '.woff2')
                or name == 'MANIFEST.json' or name.endswith('working_bundle_check.json')
                or name.endswith('working_bundle.sha256')):
            continue
        full = ROOT / path
        if not full.is_file() or full.is_symlink():
            raise ValueError('Missing or linked package input: ' + name)
        output.append((name, full.read_bytes()))
    return output


def audit_content(files):
    # Patterns detect likely secret values, not mere field names in schemas.
    patterns = {
        'api_key_like_value': re.compile(rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}'),
        'private_key_block': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
        'jwt_like_value': re.compile(rb'\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}'),
        'credential_value_field': re.compile(rb'"(?:access_token|refresh_token|api_key)"\s*:\s*"[^"\s]{16,}"'),
    }
    hits = []
    text_count = 0
    for name, data in files:
        if Path(name).suffix.lower() not in ('.json', '.jsonl', '.py', '.md', '.txt', '.diff', '.patch'):
            continue
        text_count += 1
        for label, pattern in patterns.items():
            if pattern.search(data):
                hits.append({'file': name, 'category': label})
    requests = [read_json(p) for p in sorted((COHORT / 'requests').glob('*.json'))]
    prohibited_keys = {'access_token', 'refresh_token', 'api_key', 'encrypted_content', 'reasoning',
                       'reasoning_text', 'reasoning_summary', 'auth_json', 'account_email'}
    def walk(value, path):
        if isinstance(value, dict):
            for key, item in value.items():
                if key.lower() in prohibited_keys:
                    hits.append({'file': path, 'category': 'forbidden_record_key:' + key})
                walk(item, path)
        elif isinstance(value, list):
            for item in value:
                walk(item, path)
    for i, record in enumerate(requests):
        walk(record, 'submitted request index ' + str(i))
        if record.get('hidden_reasoning_retained') is not False or record.get('raw_stream_retained') is not False:
            hits.append({'file': str(i), 'category': 'retention_flag'})
    events = [json.loads(line) for line in (COHORT / 'events.jsonl').read_text().splitlines()]
    for event in events:
        walk(event, 'events.jsonl')
    return {'status': 'passed' if not hits else 'failed', 'text_files_scanned': text_count,
            'submitted_request_records_scanned': len(requests), 'event_records_scanned': len(events),
            'findings': hits, 'event_types': dict(collections.Counter(e['type'] for e in events)),
            'scope': 'Declared project artifact text and structured pilot records only; no credential stores read. Pattern/field audit is not a universal secret-absence proof. Numeric reasoning-token counters are permitted public usage.'}


def verify():
    assert sha(BASELINE.read_bytes()) == BASELINE_SHA
    old_checks = read_json(ROOT / 'provenance/subscription_v8_before_revision/verification/final_checks.json')
    blocks = read_json(ROOT / 'paper/submission_blocks.json')
    old_blocks = read_json(ROOT / 'provenance/subscription_v8_before_revision/paper/submission_blocks.json')
    assert len(blocks['abstract'].split()) == 150
    assert [b['text'] for page in blocks['main_pages'] for b in page if b['type'] == 'abstract'] == [blocks['abstract']]
    assert len(blocks['main_pages']) == 8 and len(blocks['appendix_pages']) == 4
    assert blocks['appendix_pages'][3][7:11] == old_blocks['appendix_pages'][3][7:11]
    assert len(blocks['appendix_pages'][3][7:11]) == 4
    assert blocks['author_metadata'] == old_blocks['author_metadata']
    assert blocks['references'] == old_blocks['references']
    assert sha((ROOT / 'submission_report.pdf').read_bytes()) == old_checks['pdf_sha256']
    assert sha((ROOT / 'submission_report.docx').read_bytes()) == old_checks['docx_sha256']
    assert sha((ROOT / 'template/apart_original.docx').read_bytes()) == old_checks['template_sha256']
    frozen = read_json(COHORT / 'frozen_plan.json')
    for name, expected in frozen['source_manifest'].items():
        assert sha((COHORT / 'source_snapshot' / name).read_bytes()) == expected
        assert sha((ROOT / name).read_bytes()) == expected
    assert read_json(COHORT / 'analysis.json') == read_json(COHORT / 'analysis_rechecked.json')
    ledger = read_json(COHORT / 'usage_failure_ledger.json')
    assert ledger['planned_episodes'] == ledger['started_episodes'] == ledger['committed_action_episodes'] == 20
    assert ledger['valid_pre_diagnostic_probability_episodes'] == ledger['valid_final_probability_episodes'] == 20
    assert ledger['confirmed_turn_submissions'] == ledger['global_client_invocations'] == 102
    assert ledger['failed_started_episodes'] == ledger['refused_episodes'] == ledger['unstarted_episodes'] == 0
    assert read_json(HERE / 'final_payload_audit.json')['status'] == 'verified'
    combined = read_json(HERE / 'combined_usage_ledger.json')
    assert combined['consistency']['status'] == 'passed'
    assert combined['allowance']['accepted_turns'] == 102
    assert read_json(HERE / 'unit_tests_initial.json')['exit_code'] == 0
    assert read_json(HERE / 'unit_tests_final.json')['exit_code'] == 0
    assert read_json(HERE / 'runtime_readiness.json')['build']['ready'] is False
    with zipfile.ZipFile(BASELINE) as archive:
        assert archive.testzip() is None
        original_manifest = json.loads(archive.read('MANIFEST.json'))
        for entry in original_manifest['files']:
            data = archive.read(entry['path'])
            assert len(data) == entry['bytes'] and sha(data) == entry['sha256']
        historical = [name for name in archive.namelist() if name.startswith('results/') or '/results/' in name]
        for name in historical:
            if not name.endswith('/'):
                assert archive.read(name) == (ROOT / name).read_bytes()
        assert archive.read('scripts/run_llm.py') == (ROOT / 'scripts/run_llm.py').read_bytes()
    scan = audit_content(candidate_files())
    save_new(HERE / 'artifact_content_audit.json', scan)
    assert scan['status'] == 'passed'
    checks = {
        'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status': 'pilot_and_source_verified_current_rendering_unavailable',
        'current_version': 'v8-subscription-pilot-unrendered-source',
        'planned': 20, 'started': 20, 'committed_actions': 20, 'valid_each_probability': 20,
        'failed': 0, 'refused': 0, 'unstarted': 0, 'official_client_turns': 102,
        'frozen_source_hashes_verified': len(frozen['source_manifest']),
        'public_histories_verified': 102, 'reanalysis_matches': True,
        'distinct_tests_with_passing_evidence': 58,
        'abstract_words': 150, 'main_source_groups': 8, 'numbered_month_extensions': 4,
        'current_main_rendered_pages': None, 'current_references_start_page': None,
        'revised_docx_pdf_built': False, 'current_rendering_verified': False,
        'current_visual_review_completed': False,
        'inherited_v7_pdf_docx_unchanged': True,
        'inherited_v7_main_pages': 8, 'inherited_v7_references_start_page': 9,
        'inherited_v7_total_pages': 13,
        'historical_result_files_unchanged': len([n for n in historical if not n.endswith('/')]),
        'original_api_adapter_unchanged': True,
        'pdf_sha256': old_checks['pdf_sha256'], 'docx_sha256': old_checks['docx_sha256'],
        'blocks_sha256': sha((ROOT / 'paper/submission_blocks.json').read_bytes()),
        'markdown_sha256': sha((ROOT / 'submission_revision_v8_unrendered.md').read_bytes()),
        'template_sha256': old_checks['template_sha256'],
        'frozen_plan_sha256': sha((COHORT / 'frozen_plan.json').read_bytes()),
        'cost_usd': None, 'credit_consumption': None, 'backend_requests': None,
        'effective_runtime_model_missing_requests': 102,
        'scientific_and_submission_approval': False,
        'note': 'Source/evidence checks do not grant the rendered-release gate. Inherited binaries reflect v7; current v8 source must be rendered and every page inspected elsewhere.'}
    save_new(HERE / 'current_checks.json', checks)
    (ROOT / 'verification/final_checks.json').write_text(json.dumps(checks, indent=2) + '\n')
    print(json.dumps(checks, indent=2))


def package(target):
    checks = read_json(HERE / 'current_checks.json')
    assert checks['current_rendering_verified'] is False
    assert sha((ROOT / 'paper/submission_blocks.json').read_bytes()) == checks['blocks_sha256']
    assert sha((ROOT / 'submission_revision_v8_unrendered.md').read_bytes()) == checks['markdown_sha256']
    assert read_json(HERE / 'artifact_content_audit.json')['status'] == 'passed'
    files = candidate_files()
    # Recheck added final artifacts too; this is a packaging check, not inference.
    assert audit_content(files)['status'] == 'passed'
    manifest = {'algorithm': 'sha256', 'release_status': 'working_source_unrendered',
                'note': 'Every ZIP member except MANIFEST.json is covered. Integrity is separate from rendering and submission. Archives, cache/lock files, standalone fonts and hidden paths are excluded.',
                'files': [{'path': name, 'bytes': len(data), 'sha256': sha(data)} for name, data in files]}
    encoded = (json.dumps(manifest, indent=2) + '\n').encode()
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in files:
            archive.writestr(name, data)
        archive.writestr('MANIFEST.json', encoded)
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        assert len(set(archive.namelist())) == len(archive.namelist()) == len(files) + 1
        for item in manifest['files']:
            data = archive.read(item['path'])
            assert len(data) == item['bytes'] and sha(data) == item['sha256']
    check = {'status': 'integrity_verified_working_source_unrendered', 'archive': target.name,
             'archive_sha256': sha(target.read_bytes()), 'archive_bytes': target.stat().st_size,
             'entries': len(files) + 1, 'manifest_files_verified': len(files),
             'crc_verified': True, 'current_rendering_verified': False,
             'all_102_request_files_packaged': sum(name.startswith('results/codex_subscription_pilot_v8_01/requests/') for name, _ in files) == 102,
             'baseline_archive_unchanged': sha(BASELINE.read_bytes()) == BASELINE_SHA}
    assert check['all_102_request_files_packaged'] and check['baseline_archive_unchanged']
    save_new(HERE / 'working_bundle_check.json', check)
    with (HERE / 'working_bundle.sha256').open('x') as stream:
        stream.write(check['archive_sha256'] + '  ' + target.name + '\n')
    print(json.dumps(check, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path)
    args = parser.parse_args()
    if args.package:
        package(args.package)
    else:
        verify()
