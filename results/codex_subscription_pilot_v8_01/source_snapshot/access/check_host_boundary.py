#!/usr/bin/env python3
"""Test the official filesystem restriction using newly created benign files.

No credential file, real log, model context, network endpoint or OS identifier
is probed. This is a local implementation check, not a benchmark episode.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--boundary', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit('Use a fresh host-check path')
    boundary = json.loads(args.boundary.read_text())
    rows = []
    for location, parent in (('temporary_directory', None), ('repository', ROOT)):
        with tempfile.TemporaryDirectory(prefix='MOCK-NOT-LLM-', dir=parent) as folder:
            marker = Path(folder)/'benign_boundary_marker.txt'
            marker.write_text('MOCK-NOT-LLM')
            command = ['codex', 'sandbox', '-P', 'realgame_subject', '-C', folder,
                       '--include-managed-config']
            for override in boundary['profile_overrides']:
                command += ['-c', override]
            command += ['/bin/sh', '-c',
                        'if [ -r "$1" ]; then printf "readable"; else printf "blocked"; fi',
                        'MOCK-NOT-LLM', str(marker)]
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=20)
                rows.append({'fixture': 'MOCK-NOT-LLM', 'location': location,
                             'exit_code': result.returncode,
                             'benign_marker_read_denied': result.returncode == 0 and result.stdout == 'blocked',
                             'raw_stderr_retained': False})
            except subprocess.TimeoutExpired:
                rows.append({'fixture': 'MOCK-NOT-LLM', 'location': location,
                             'benign_marker_read_denied': False, 'status': 'timeout'})
    output = {
        'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'boundary_sha256': hashlib.sha256(args.boundary.read_bytes()).hexdigest(),
        'profile_overrides': boundary['profile_overrides'],
        'rows': rows, 'passed': all(row['benign_marker_read_denied'] for row in rows),
        'experimental_turns': 0, 'credentials_or_evidence_files_read': False,
        'network_probe_performed': False,
        'scope': 'Benign read-denial checks for the same named official profile; not a universal containment proof.'}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(output, indent=2)+'\n')
    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
