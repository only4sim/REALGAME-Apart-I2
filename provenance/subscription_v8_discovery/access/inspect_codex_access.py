#!/usr/bin/env python3
"""Sanitized official-client discovery. Never invokes a model turn."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from codex_subscription import OfficialMetadataClient, MetadataError, sanitize_models, sanitize_usage


def inspect_local(check_login=False):
    rows = []
    version = None
    auth = None
    commands = [['codex', '--version']]
    if check_login:
        commands.append(['codex', 'login', 'status'])
    commands += [['codex', 'exec', '--help'], ['codex', 'app-server', '--help']]
    for command in commands:
        row = {'command': ' '.join(command)}
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=20)
            row['exit_code'] = result.returncode
            row['supported'] = result.returncode == 0
            if command[1:] == ['--version']:
                match = re.search(r'codex(?:-cli)?\s+([0-9][0-9A-Za-z.+_-]*)', result.stdout)
                version = match.group(1) if match else None
                row['client_version'] = version
            elif command[1:] == ['login', 'status']:
                status = (result.stdout + '\n' + result.stderr).lower()
                auth = ('chatgpt' if result.returncode == 0 and 'chatgpt' in status else
                        'api_key' if result.returncode == 0 and ('api key' in status or 'api_key' in status) else
                        'not_logged_in' if result.returncode != 0 else 'unknown')
                row.update(auth_type=auth, raw_output_retained=False)
            else:
                row['help_sha256'] = hashlib.sha256(result.stdout.encode()).hexdigest()
                row['supported_flags'] = sorted(set(re.findall(r'--[a-z][a-z-]+', result.stdout)))
        except FileNotFoundError:
            row.update(status='executable_not_found', supported=False)
        except subprocess.TimeoutExpired:
            row.update(status='local_command_timeout', supported=None)
        rows.append(row)
    return {'official_cli_available': shutil.which('codex') is not None,
            'client_version': version, 'auth_type': auth, 'commands': rows,
            'installation_interpretation': 'Checked the child-process CLI directly; parent conversation access was not assumed.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-login', action='store_true')
    parser.add_argument('--allow-network-metadata', action='store_true')
    parser.add_argument('--authorization', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit('Use a fresh output path')
    if args.allow_network_metadata and (not args.authorization or not args.authorization.is_file()):
        raise SystemExit('Supply the recorded human metadata authorization; a configuration flag alone is not consent')
    output = inspect_local(args.check_login)
    output.update(checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  models=[], metadata_rpc_submissions=0, experimental_turn_submissions=0,
                  benchmark_episodes_started=0, raw_stream_retained=False,
                  secret_values_inspected=False, usage=None,
                  metadata_may_use_network=args.allow_network_metadata,
                  authorization_sha256=(hashlib.sha256(args.authorization.read_bytes()).hexdigest()
                                        if args.authorization else None))
    if args.allow_network_metadata and output['official_cli_available'] and output['auth_type'] == 'chatgpt':
        client = OfficialMetadataClient()
        try:
            with client:
                cursor = None
                for _ in range(10):
                    params = {'includeHidden': False, 'limit': 100}
                    if cursor:
                        params['cursor'] = cursor
                    result = client.request('model/list', params)
                    output['models'].extend(sanitize_models(result))
                    cursor = result.get('nextCursor')
                    if not cursor:
                        break
                if cursor:
                    raise MetadataError('model_catalog_pagination_limit')
                output['usage'] = sanitize_usage(client.request('account/rateLimits/read'))
                output['metadata_status'] = 'completed'
        except (MetadataError, OSError) as error:
            output['metadata_status'] = 'failed'
            output['metadata_error_category'] = str(error) if isinstance(error, MetadataError) else type(error).__name__
        finally:
            output['metadata_rpc_submissions'] = client.calls
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(output, indent=2, allow_nan=False) + '\n')
    print(json.dumps(output, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
