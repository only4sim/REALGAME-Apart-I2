#!/usr/bin/env python3
"""Local-only build/inference preflight. No API calls or credential discovery.

The API route checks only the presence of its named credential variable. The
subscription route reads only the explicitly linked non-sensitive approval and
discovery records. Configuration flags and artifact hashes are not evidence that
a human has authorized spending. Successful preflight does not establish
provider compatibility or permission to execute.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def linked_evidence(cfg, name):
    """Read the named non-sensitive evidence and require its matching hash.

    A matching digest links an artifact to the configuration. It does not
    establish human authorship, approval scope, or provider compatibility.
    No artifact contents or filesystem exception details are returned.
    """
    configured_path = cfg.get(name + '_path')
    expected = cfg.get(name + '_sha256')
    if (not isinstance(configured_path, str) or not configured_path
            or not isinstance(expected, str) or len(expected) != 64
            or any(c not in '0123456789abcdefABCDEF' for c in expected)):
        return None
    path = Path(configured_path)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if not path.is_relative_to(ROOT.resolve()) or any(part.startswith('.') for part in path.relative_to(ROOT.resolve()).parts):
        return None
    try:
        data = path.read_bytes()
    except (OSError, ValueError):
        return None
    if not data or hashlib.sha256(data).hexdigest() != expected.lower():
        return None
    return data


def subscription_inference_gates(cfg):
    """Use linked approval/discovery records without reading API credentials."""
    if str(ROOT / 'src') not in sys.path:
        sys.path.insert(0, str(ROOT / 'src'))
    from codex_subscription import subscription_gates

    discovery_bytes = linked_evidence(cfg, 'access_discovery')
    authorization_bytes = linked_evidence(cfg, 'authorization')
    billing_bytes = linked_evidence(cfg, 'billing_control')
    boundary_bytes = linked_evidence(cfg, 'subject_boundary')
    host_bytes = linked_evidence(cfg, 'host_boundary')
    discovery = None
    if discovery_bytes is not None:
        try:
            decoded = json.loads(discovery_bytes)
            if isinstance(decoded, dict):
                discovery = decoded
        except (ValueError, UnicodeError):
            pass
    authorization_verified = authorization_bytes is not None
    def object_record(data):
        try:
            value = json.loads(data) if data else None
            return value if isinstance(value, dict) else None
        except (ValueError, UnicodeError):
            return None
    boundary, host_check = object_record(boundary_bytes), object_record(host_bytes)
    result = subscription_gates(cfg, discovery or {}, authorization_verified,
                                billing_bytes is not None, boundary, host_check)
    if discovery is None:
        result['missing'].append('Hash-linked non-sensitive access discovery JSON object')
    if not authorization_verified:
        result['missing'].append('Hash-linked non-sensitive human authorization artifact')
    result['ready_by_configuration'] = not result['missing']
    result['access_discovery_artifact_hash_verified'] = discovery is not None
    result['human_authorization_artifact_hash_verified'] = authorization_verified
    result['billing_control_attestation_hash_verified'] = billing_bytes is not None
    result['subject_boundary_artifact_hash_verified'] = boundary is not None
    result['host_boundary_artifact_hash_verified'] = host_check is not None
    result['human_authorization_must_be_separately_confirmed'] = True
    result['evidence_linkage_note'] = (
        'Hashes link the supplied artifacts only. They do not establish human '
        'consent, billing permission, or successful subject isolation.')
    return result


def finite_number(value, positive=False):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and (value > 0 if positive else value >= 0))


def inference_gates(cfg):
    if cfg.get('provider') == 'codex_subscription':
        return subscription_inference_gates(cfg)
    missing = []
    models = cfg.get('models')
    if not isinstance(models, list) or not models or any(not isinstance(m, str) or not m.strip() for m in models):
        missing.append('Exact nonempty model identifiers')
    if cfg.get('provider') not in ('responses', 'chat'):
        missing.append('Supported provider protocol')
    url = urlparse(cfg.get('base_url', ''))
    host = url.hostname
    local = host in ('localhost', '127.0.0.1', '::1')
    if cfg.get('allow_network') is not True or host not in cfg.get('approved_hosts', []):
        missing.append('Explicit permission for the exact inference host')
    if not host or url.username or url.password or url.scheme not in ('https', 'http') or (url.scheme == 'http' and not local):
        missing.append('Valid HTTPS endpoint (HTTP only for authorized loopback)')
    env_name = cfg.get('api_key_env')
    present = bool(isinstance(env_name, str) and env_name and os.environ.get(env_name))
    if not local:
        if not present:
            missing.append('Presence of the specifically configured credential variable')
        if cfg.get('paid_calls_authorized') is not True or not finite_number(cfg.get('max_estimated_usd'), positive=True):
            missing.append('Explicit paid-call authorization and positive spending ceiling')
        if any(not finite_number(cfg.get(k)) for k in ('price_input_per_million', 'price_output_per_million')) or not cfg.get('price_source'):
            missing.append('Finite nonnegative token prices and a dated primary price source')
    for key in ('max_requests', 'max_output_tokens', 'workers', 'seeds_per_cell'):
        if type(cfg.get(key)) is not int or cfg[key] <= 0:
            missing.append('Positive integer '+key)
    if not finite_number(cfg.get('wallclock_seconds'), positive=True):
        missing.append('Positive finite inference wallclock ceiling')
    return {'ready_by_configuration': not missing, 'missing': missing,
            'configured_credential_variable': env_name, 'configured_credential_present': present,
            'credential_value_recorded': False, 'host': host,
            'exact_model_ids': models, 'provider_pilot_verified': False,
            'human_authorization_must_be_separately_confirmed': True,
            'note': 'Per-directory estimates are not account-level spending controls. Deduct pilot costs from the global authorized ceiling.'}


def build_gates():
    modules = {m: importlib.util.find_spec(m) is not None for m in ('docx', 'lxml', 'fitz', 'matplotlib')}
    executables = {e: shutil.which(e) for e in ('pandoc', 'libreoffice')}
    font = None
    if shutil.which('fc-match'):
        completed = subprocess.run(['fc-match', '-f', '%{family}|%{file}', 'Old Standard TT'],
                                   capture_output=True, text=True, timeout=20)
        if completed.returncode == 0:
            font = completed.stdout.strip()
    font_ok = bool(font and 'oldstandard' in font.lower().replace(' ', ''))
    return {'ready': all(modules.values()) and all(executables.values()) and font_ok,
            'python_modules': modules, 'executables': executables,
            'old_standard_font_match': font, 'font_available': font_ok,
            'note': 'A build-ready environment is not a visually verified document. No dependencies were installed by this check.'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', type=Path, default=ROOT/'configs/halfday.json')
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    cfg = json.loads(args.config.read_text())
    result = {'build': build_gates(), 'inference': inference_gates(cfg),
              'network_calls': 0, 'provider_spending': 0,
              'status': 'preflight_only', 'scope': 'Local configuration and dependency checks; not provider or scientific validation.'}
    text = json.dumps(result, indent=2)+'\n'
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open('x') as f:
            f.write(text)
    print(text, end='')


if __name__ == '__main__':
    main()
