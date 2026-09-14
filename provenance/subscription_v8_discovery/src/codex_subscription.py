"""Official App Server metadata adapter and fail-closed subscription controls.

The v8 subject is a model-plus-Codex-client system. This adapter deliberately
does not expose thread/start or turn/start until an included-only billing
boundary and a subject-context boundary have been independently established.
No config flag, quota percentage, or ChatGPT login alone establishes either.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import selectors
import subprocess
import tempfile
import time

PROTOCOL = 'codex-subscription-pilot-v8'
METADATA_METHODS = frozenset({'initialize', 'model/list', 'account/rateLimits/read'})
# This is an implementation capability, not a user-editable readiness switch.
INCLUDED_ONLY_EXECUTION_IMPLEMENTED = False
SUBJECT_ISOLATION_VERIFIED = False


class AccessBlocked(RuntimeError):
    """An access/control blocker; never a target-model outcome."""


class MetadataError(RuntimeError):
    """Only a sanitized error category crosses this boundary."""


class OfficialMetadataClient:
    """Allowlisted JSON-RPC over the installed official client's stdio.

    No auth files, environment values, raw stderr, raw login status, account
    identities, or unfiltered streams are recorded. No model thread is created.
    The ordinary client handles authentication; no tokens are extracted/replayed.
    """

    def __init__(self, executable='codex', timeout=25):
        self.executable = executable
        self.timeout = timeout
        self.calls = 0
        self.buffer = b''
        self.process = None
        self.folder = None
        self.selector = None

    def __enter__(self):
        self.folder = tempfile.TemporaryDirectory(prefix='realgame_metadata_')
        try:
            self.process = subprocess.Popen(
                [self.executable, 'app-server', '--stdio'],
                cwd=self.folder.name, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, bufsize=0)
            self.selector = selectors.DefaultSelector()
            self.selector.register(self.process.stdout, selectors.EVENT_READ)
            self.request('initialize', {
                'clientInfo': {'name': 'realgame_access_audit', 'version': '8.0.0'},
                'capabilities': {'experimentalApi': False}})
            self._send({'method': 'initialized'})
            return self
        except Exception:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *_):
        if self.process:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)
            for stream in (self.process.stdin, self.process.stdout):
                if stream:
                    stream.close()
        if self.selector:
            self.selector.close()
        if self.folder:
            self.folder.cleanup()

    def _send(self, data):
        self.process.stdin.write((json.dumps(data, allow_nan=False) + '\n').encode())
        self.process.stdin.flush()

    def _read(self, deadline):
        while b'\n' not in self.buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not self.selector.select(remaining):
                raise MetadataError('metadata_timeout')
            chunk = os.read(self.process.stdout.fileno(), 65536)
            if not chunk:
                raise MetadataError('metadata_process_closed')
            self.buffer += chunk
            if len(self.buffer) > 2_000_000:
                raise MetadataError('metadata_frame_limit')
        line, self.buffer = self.buffer.split(b'\n', 1)
        try:
            value = json.loads(line)
        except (ValueError, UnicodeError):
            raise MetadataError('metadata_invalid_json') from None
        if not isinstance(value, dict):
            raise MetadataError('metadata_invalid_message')
        return value

    def request(self, method, params=None):
        if method not in METADATA_METHODS:
            raise AccessBlocked('Method is outside the read-only metadata allowlist')
        self.calls += 1
        request_id = self.calls
        message = {'id': request_id, 'method': method}
        if params is not None:
            message['params'] = params
        self._send(message)
        deadline = time.monotonic() + self.timeout
        while True:
            response = self._read(deadline)
            if 'method' in response:
                if 'id' in response:
                    self._send({'id': response['id'], 'error': {
                        'code': -32601, 'message': 'Unsupported in metadata-only client'}})
                    raise MetadataError('unexpected_server_request')
                # Drop notifications in memory, before persistence or logging.
                continue
            if response.get('id') != request_id:
                raise MetadataError('metadata_response_id_mismatch')
            if 'error' in response:
                code = (response.get('error') or {}).get('code')
                raise MetadataError('metadata_rpc_error_' + str(code if isinstance(code, int) else 'unknown'))
            result = response.get('result')
            if not isinstance(result, dict):
                raise MetadataError('metadata_missing_result')
            return result


def sanitize_models(result):
    models = []
    for item in result.get('data', []):
        if not isinstance(item, dict) or item.get('hidden') is not False:
            continue
        if not isinstance(item.get('model'), str) or not item['model']:
            continue
        models.append({
            'id': item.get('id'), 'model': item['model'], 'hidden': False,
            'isDefault': item.get('isDefault'),
            'defaultReasoningEffort': item.get('defaultReasoningEffort'),
            'supportedReasoningEfforts': [
                {'reasoningEffort': option['reasoningEffort']}
                for option in item.get('supportedReasoningEfforts', [])
                if isinstance(option, dict) and isinstance(option.get('reasoningEffort'), str)]})
    return models


def sanitize_usage(result):
    def snapshot(value):
        if not isinstance(value, dict):
            return None
        out = {k: value.get(k) for k in (
            'limitId', 'planType', 'spendControlReached', 'rateLimitReachedType')}
        for key in ('primary', 'secondary'):
            window = value.get(key)
            out[key] = ({k: window.get(k) for k in (
                'usedPercent', 'windowDurationMins', 'resetsAt')}
                if isinstance(window, dict) else None)
        credit = value.get('credits')
        out['credits'] = ({k: credit.get(k) for k in ('hasCredits', 'unlimited', 'balance')}
                          if isinstance(credit, dict) else None)
        return out
    buckets = result.get('rateLimitsByLimitId')
    return {
        'ordinaryUsageAllowed': result.get('ordinaryUsageAllowed'),
        'rateLimits': snapshot(result.get('rateLimits')),
        'rateLimitsByLimitId': ({key: snapshot(value) for key, value in buckets.items()}
                               if isinstance(buckets, dict) else None),
        'credit_consumption': None, 'monetary_cost_usd': None,
        'account_identity_retained': False,
        'note': 'Passive usage telemetry is not an included-only billing control.'}


def subscription_gates(cfg, discovery=None, authorization_verified=False):
    """Route-specific checks. Human approval must be independently supplied."""
    discovery = discovery or {}
    missing = []
    if cfg.get('protocol_version') != PROTOCOL:
        missing.append('Exact separate subscription protocol ID')
    if not authorization_verified:
        missing.append('Recorded human approval for this synthetic data scope')
    if cfg.get('allow_synthetic_transmission') is not True:
        missing.append('Synthetic-prompt and permitted-history transmission scope')
    if cfg.get('billing_route') != 'included_subscription_only':
        missing.append('Included-subscription-only route')
    if cfg.get('api_fallback') is not False or cfg.get('extra_credits_allowed') is not False:
        missing.append('API fallback and extra-credit use must be disabled')
    if discovery.get('auth_type') != 'chatgpt':
        missing.append('Official client ChatGPT authentication')
    if discovery.get('official_cli_available') is not True:
        missing.append('Installed official Codex executable')
    selected = cfg.get('models')
    available = {item.get('model'): item for item in discovery.get('models', [])
                 if item.get('hidden') is False}
    if not isinstance(selected, list) or len(selected) != 1 or selected[0] not in available:
        missing.append('One exact non-hidden model from official model/list')
    else:
        efforts = {item.get('reasoningEffort') for item in available[selected[0]].get('supportedReasoningEfforts', [])}
        if cfg.get('reasoning_effort') not in efforts:
            missing.append('Supported frozen reasoning effort')
    for key, ceiling in (('workers', 1), ('max_episodes', 20),
                         ('max_client_invocations', 140), ('inference_wallclock_seconds', 2700)):
        if type(cfg.get(key)) is not int or not 0 < cfg[key] <= ceiling:
            missing.append('Authorized positive cap: ' + key)
    if cfg.get('seeds_per_cell') != 1:
        missing.append('One repeat per cell')
    if not INCLUDED_ONLY_EXECUTION_IMPLEMENTED:
        missing.append('Verified official control preventing extra-credit consumption')
    if not SUBJECT_ISOLATION_VERIFIED:
        missing.append('Verified subject tool, filesystem, instruction and history isolation')
    return {'route': 'codex_subscription', 'ready_by_configuration': not missing,
            'missing': missing, 'human_authorization_must_be_separately_confirmed': True,
            'api_key_required': False, 'api_token_prices_required': False,
            'experimental_execution_implemented': False,
            'note': 'Billing/isolation capabilities cannot be enabled by configuration assertions.'}


class PilotBudget:
    """One shared outer allowance; a client turn may contain backend retries."""
    def __init__(self, max_invocations=140, seconds=2700, clock=time.monotonic):
        if type(max_invocations) is not int or not 0 < max_invocations <= 140:
            raise AccessBlocked('Invalid invocation cap')
        if type(seconds) is not int or not 0 < seconds <= 2700:
            raise AccessBlocked('Invalid wallclock cap')
        self.limit, self.seconds, self.clock = max_invocations, seconds, clock
        self.started = clock()
        self.submitted = 0

    def reserve(self):
        if self.clock() - self.started >= self.seconds:
            raise AccessBlocked('Experimental time cap reached')
        if self.submitted >= self.limit:
            raise AccessBlocked('Client invocation cap reached')
        self.submitted += 1
        return self.submitted


def filter_visible_event(event):
    """Prospective stream filter: all reasoning payloads are discarded.

    This is not an inference implementation or a claim that the installed
    client avoids internal persistence. Only visible final messages are kept.
    """
    method = event.get('method')
    params = event.get('params') or {}
    if method == 'item/completed':
        item = params.get('item') or {}
        if item.get('type') == 'agentMessage':
            if item.get('phase') == 'final_answer':
                return {'type': 'visible_final_answer', 'text': item.get('text', '')}
            return None
        if item.get('type') in ('commandExecution', 'fileChange', 'mcpToolCall',
                                'webSearch', 'dynamicToolCall', 'collabAgentToolCall'):
            return {'type': 'forbidden_tool_attempt', 'tool_type': item['type'],
                    'arguments_retained': False}
    if method == 'turn/completed':
        turn = params.get('turn') or {}
        error = turn.get('error') or {}
        return {'type': 'turn_status', 'status': turn.get('status'),
                'error_present': bool(error), 'model_returned': None,
                'note': 'Missing effective model metadata is not filled from the requested slug.'}
    return None


def validate_public_history(messages):
    """Reject coordinator metadata containers; do not send filesystem context."""
    if not isinstance(messages, list) or not messages:
        raise AccessBlocked('Expected reconstructed public messages')
    for message in messages:
        if (not isinstance(message, dict) or set(message) != {'role', 'content'}
                or message['role'] not in ('system', 'user', 'assistant')
                or not isinstance(message['content'], str)):
            raise AccessBlocked('Forbidden context field')
    # Structural validation does not prove that arbitrary strings are public.
    return messages


def start_experimental_call(*args, **kwargs):
    """Intentionally unavailable while the two substantive boundaries are open."""
    raise AccessBlocked('Experimental transport disabled: billing and isolation are unverified')
