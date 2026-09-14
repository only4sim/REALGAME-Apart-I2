#!/usr/bin/env python3
"""One-command offline reproduction of saved results; no new inference or sampling."""
import argparse
import datetime
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
COHORT = 'results/codex_subscription_pilot_v8_01'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, help='Fresh output directory; default is a timestamped build/ directory')
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = (args.out or ROOT / 'build' / ('reproduction-' + stamp)).resolve()
    if out.is_relative_to(ROOT / 'results') or out.is_relative_to(ROOT / 'archive'):
        raise SystemExit('Use a fresh build directory, not an evidence directory')
    out.mkdir(parents=True, exist_ok=False)
    commands = [
        ('tests', ['-m', 'unittest', 'discover', '-s', 'tests', '-v']),
        ('repository', ['scripts/verify_repository.py', '--out', str(out / 'repository.json')]),
        ('scripted_records', ['scripts/verify_evidence.py', '--out', str(out / 'scripted_records.json')]),
        ('full_certificates', ['certificates/code/check_certificates.py', 'certificates/data/full_class_certificates.json', '--output', str(out / 'full_certificates.json')]),
        ('restricted_certificates', ['certificates/code/check_certificates.py', 'certificates/data/certificates.json', '--output', str(out / 'restricted_certificates.json')]),
        ('pilot_analysis', ['scripts/analyze_codex_pilot.py', '--input', COHORT + '/runs.jsonl', '--out', str(out / 'pilot_analysis.json')]),
        ('pilot_payloads', ['scripts/audit_frozen_payloads.py', '--cohort', COHORT, '--out', str(out / 'pilot_payloads.json')]),
        ('pilot_usage', ['scripts/summarize_usage.py', '--pilot', COHORT, '--global-ledger', 'results/codex_subscription_v8_global_allowance.jsonl', '--preinference', 'verification/subscription_v8/preinference_metadata_ledger.json', '--out', str(out / 'pilot_usage.json')]),
    ]
    steps = []
    for name, arguments in commands:
        completed = subprocess.run([sys.executable, *arguments], cwd=ROOT, capture_output=True, text=True)
        (out / (name + '.log')).write_text(completed.stdout + completed.stderr)
        steps.append({'step': name, 'command': [sys.executable, *arguments], 'exit_code': completed.returncode})
        (out / 'steps.json').write_text(json.dumps(steps, indent=2) + '\n')
        print(name + ': ' + ('passed' if completed.returncode == 0 else 'FAILED'), flush=True)
        if completed.returncode:
            raise SystemExit('Stopped; inspect ' + str(out / (name + '.log')))
    saved = json.loads((ROOT / COHORT / 'analysis.json').read_text())
    actual = json.loads((out / 'pilot_analysis.json').read_text())
    if actual != saved:
        raise SystemExit('Reanalysis differs from saved results; inspect ' + str(out))
    certificates = [json.loads((out / name).read_text()) for name in ('full_certificates.json', 'restricted_certificates.json')]
    result = {'status': 'passed', 'new_model_calls': 0, 'new_sampling_runs': 0,
              'pilot_analysis_matches_saved': True,
              'certificate_cases': sum(item['case_count'] for item in certificates),
              'rational_constraints': sum(item['checked_constraints'] for item in certificates),
              'output_directory': str(out),
              'note': 'Reanalysis and finite certificate checks are reproduction, not new independent scientific observations.'}
    (out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
