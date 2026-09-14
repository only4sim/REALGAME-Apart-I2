"""Bounded official-client transport for the separate v8 synthetic pilot.

Each call starts an ephemeral client context containing reconstructed public
history. The client handles its own authentication. No tokens, raw streams,
reasoning items, tool arguments, account identities, or stderr are persisted.
The absence of a public complete tool inventory is not an empty-tool claim.
"""
from __future__ import annotations

import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / 'scripts') not in sys.path:
    sys.path.insert(0, str(ROOT / 'scripts'))
from run_llm import Halt, OutcomeFailure, SYSTEM, PROB, parse_obj
from worlds import canonical, digest
from codex_subscription import (
    AccessBlocked, MetadataError, OfficialMetadataClient, METADATA_METHODS,
    PROTOCOL, sanitize_usage, validate_public_history,
)


class SubjectStop(Halt):
    """Stop the whole pilot; retain any action already committed by its runner."""
    def __init__(self, category):
        self.category = category
        super().__init__(category)


def linked_artifact(cfg, name):
    """Only read an explicitly configured, hash-linked non-sensitive artifact."""
    path, expected = cfg.get(name + '_path'), cfg.get(name + '_sha256')
    if not isinstance(path, str) or not isinstance(expected, str):
        raise SubjectStop('missing_' + name + '_linkage')
    source = Path(path)
    if not source.is_absolute():
        source = ROOT / source
    try:
        data = source.read_bytes()
    except OSError:
        raise SubjectStop('unreadable_' + name + '_artifact') from None
    if not data or hashlib.sha256(data).hexdigest() != expected:
        raise SubjectStop(name + '_hash_mismatch')
    return data


def skill_inventory(result):
    """Keep only the fields present in the independently audited inventory."""
    if not isinstance(result.get('data'), list):
        raise SubjectStop('invalid_skill_catalog')
    inventory = []
    for entry in result['data']:
        if (not isinstance(entry, dict) or entry.get('errors') != []
                or not isinstance(entry.get('skills'), list)):
            raise SubjectStop('skill_catalog_error')
        for item in entry['skills']:
            if not isinstance(item, dict) or item.get('enabled') is not False:
                raise SubjectStop('enabled_or_invalid_skill')
            inventory.append({key: item.get(key) for key in ('name', 'path', 'enabled', 'scope')})
    return sorted(inventory, key=canonical)


def verify_included_usage(public):
    """Telemetry supplements the user's separately recorded billing controls."""
    if public.get('ordinaryUsageAllowed') is not True:
        raise SubjectStop('included_usage_unavailable_or_unknown')
    buckets = public.get('rateLimitsByLimitId')
    codex = buckets.get('codex') if isinstance(buckets, dict) else None
    if not isinstance(codex, dict):
        candidate = public.get('rateLimits')
        codex = candidate if isinstance(candidate, dict) and candidate.get('limitId') == 'codex' else None
    if not isinstance(codex, dict):
        raise SubjectStop('codex_usage_bucket_missing')
    credit = codex.get('credits')
    if not isinstance(credit, dict) or credit.get('hasCredits') is not False or credit.get('unlimited') is not False:
        raise SubjectStop('extra_credit_state_changed_or_unknown')
    try:
        balance = Decimal(credit.get('balance'))
    except (InvalidOperation, TypeError, ValueError):
        raise SubjectStop('credit_balance_unavailable') from None
    if not balance.is_finite() or balance != 0:
        raise SubjectStop('nonzero_or_nonfinite_credit_balance')
    if codex.get('spendControlReached') is not False or codex.get('rateLimitReachedType') is not None:
        raise SubjectStop('subscription_spend_or_rate_limit')
    active_windows = 0
    for key in ('primary', 'secondary'):
        window = codex.get(key)
        if window is None:
            continue
        if not isinstance(window, dict) or type(window.get('usedPercent')) is not int:
            raise SubjectStop('included_usage_window_unknown')
        active_windows += 1
        if not 0 <= window['usedPercent'] < 100:
            raise SubjectStop('subscription_quota_exhausted')
    if not active_windows:
        raise SubjectStop('included_usage_window_unknown')
    return public


ERROR_CODES = frozenset({
    'contextWindowExceeded', 'sessionBudgetExceeded', 'usageLimitExceeded',
    'rateLimitExceeded', 'serverOverloaded', 'cyberPolicy',
    'misalignmentPolicyViolation', 'internalServerError', 'unauthorized',
    'badRequest', 'threadRollbackFailed', 'sandboxError', 'other',
    'httpConnectionFailed', 'responseStreamConnectionFailed',
    'responseStreamDisconnected', 'responseTooManyFailedAttempts',
    'activeTurnNotSteerable',
})
QUOTA_CODES = frozenset({'sessionBudgetExceeded', 'usageLimitExceeded', 'rateLimitExceeded'})
REFUSAL_CODES = frozenset({'cyberPolicy', 'misalignmentPolicyViolation'})
TOKEN_FIELDS = ('inputTokens', 'cachedInputTokens', 'cacheWriteInputTokens',
                'outputTokens', 'reasoningOutputTokens', 'totalTokens')
VISIBLE_REFUSAL = re.compile(
    r"^\s*(?:I (?:cannot|can't|won't|will not|am unable to)|I'm unable to|"
    r"I’m unable to|Sorry[, :] |I'm sorry|I’m sorry)", re.IGNORECASE)


def public_error(error):
    """Discard free-text errors and retain only recognized codes/status codes."""
    info = error.get('codexErrorInfo') if isinstance(error, dict) else None
    if isinstance(info, str):
        return {'code': info if info in ERROR_CODES else 'unknown', 'http_status': None}
    if isinstance(info, dict) and len(info) == 1:
        key, value = next(iter(info.items()))
        status = value.get('httpStatusCode') if isinstance(value, dict) else None
        return {'code': key if key in ERROR_CODES else 'unknown',
                'http_status': status if type(status) is int and 100 <= status <= 599 else None}
    return {'code': 'unknown', 'http_status': None}


def public_token_usage(value):
    """Public numeric usage is distinct from reasoning content."""
    if not isinstance(value, dict):
        raise SubjectStop('invalid_public_usage')
    output = {}
    for key in ('last', 'total'):
        counters = value.get(key)
        if not isinstance(counters, dict):
            raise SubjectStop('invalid_public_usage')
        output[key] = {}
        for field in TOKEN_FIELDS:
            number = counters.get(field)
            if number is not None:
                if type(number) is not int or number < 0:
                    raise SubjectStop('invalid_public_usage')
                output[key][field] = number
    return output


class SubjectClient(OfficialMetadataClient):
    """One fresh client process and one experimental turn, without repairs."""
    allowed_methods = METADATA_METHODS | frozenset({
        'skills/list', 'mcpServerStatus/list', 'thread/start', 'turn/start', 'turn/interrupt',
    })

    def __init__(self, cfg, deadline, emit, submitted, submission_guard):
        super().__init__(executable=cfg.get('codex_executable', 'codex'),
                         timeout=cfg['request_timeout_seconds'],
                         overrides=cfg['profile_overrides'], experimental=True)
        self.deadline = deadline
        self.emit = emit
        self.on_submitted = submitted
        self.submission_guard = submission_guard
        self.requested_model = cfg['models'][0]
        self.thread_id = None
        self.turn_id = None
        self.messages = []
        self.completed_message_ids = set()
        self.partial_messages = {}
        self.usage = None
        self.model_returned = None
        self.turn_status = None
        self.turn_error = None
        self.turn_finished = False
        self.turn_start_accepted = False
        self.cancellation_requests_attempted = 0
        self.cancellation_requests_submitted = 0

    def __exit__(self, *exc):
        try:
            if (self.turn_id and not self.turn_finished and self.process
                    and self.process.poll() is None and self.process.stdin
                    and not self.process.stdin.closed):
                # Cancellation is a control RPC, never a replacement model turn.
                # Use one nonblocking pipe write even after the inference deadline.
                self.calls += 1
                self.cancellation_requests_attempted += 1
                message = {'id': self.calls, 'method': 'turn/interrupt',
                           'params': {'threadId': self.thread_id, 'turnId': self.turn_id}}
                encoded = (json.dumps(message) + '\n').encode()
                written = False
                try:
                    fd = self.process.stdin.fileno()
                    blocking = os.get_blocking(fd)
                    try:
                        os.set_blocking(fd, False)
                        written = os.write(fd, encoded) == len(encoded)
                    finally:
                        os.set_blocking(fd, blocking)
                except (OSError, ValueError):
                    pass
                if written:
                    self.submissions += 1
                    self.cancellation_requests_submitted += 1
                self.emit({'type': 'turn_cancellation_requested',
                           'interrupt_frame_written': written,
                           'server_cancellation_acknowledged': None,
                           'note': 'Best-effort control RPC before client termination; no retry or new turn.'})
        finally:
            super().__exit__(*exc)

    def _send(self, data):
        # FileIO.write may perform a short write. Complete one JSON-RPC frame.
        encoded = (json.dumps(data, allow_nan=False) + '\n').encode()
        view = memoryview(encoded)
        while view:
            if time.monotonic() >= self.deadline:
                raise SubjectStop('client_call_timeout')
            written = self.process.stdin.write(view)
            if not written:
                raise SubjectStop('client_transport_closed')
            view = view[written:]
        self.process.stdin.flush()

    def _read(self, deadline):
        # The base transport checks time only when it must wait for bytes.
        # Apply the same ceiling while complete frames are already buffered.
        effective_deadline = min(deadline, self.deadline)
        if time.monotonic() >= effective_deadline:
            raise SubjectStop('client_call_timeout')
        return super()._read(effective_deadline)

    def request(self, method, params=None):
        if method not in self.allowed_methods:
            raise SubjectStop('unsupported_client_method')
        if time.monotonic() >= self.deadline:
            raise SubjectStop('client_call_timeout')
        self.calls += 1
        request_id = self.calls
        message = {'id': request_id, 'method': method}
        if params is not None:
            message['params'] = params
        if method == 'turn/start':
            # Reserve the turn before transmission; a failed write still consumes
            # this conservative allowance but is not a confirmed submission.
            self.submission_guard()
        self._send(message)
        self.submissions += 1
        if method == 'turn/start':
            self.on_submitted()
        while True:
            response = self._read(self.deadline)
            if 'method' in response:
                self.notification(response)
                continue
            if response.get('id') != request_id:
                raise SubjectStop('client_response_id_mismatch')
            if 'error' in response:
                error = response.get('error')
                code = error.get('code') if isinstance(error, dict) else None
                self.emit({'type': 'rpc_failure', 'rpc_code': code if type(code) is int else None,
                           'stage': method})
                raise SubjectStop('client_rpc_rejected')
            result = response.get('result')
            if not isinstance(result, dict):
                raise SubjectStop('invalid_client_result')
            if method == 'turn/start':
                turn = result.get('turn')
                if not isinstance(turn, dict) or not isinstance(turn.get('id'), str):
                    raise SubjectStop('missing_started_turn_id')
                if turn.get('status') not in ('completed', 'interrupted', 'failed', 'inProgress'):
                    raise SubjectStop('invalid_started_turn_status')
                self.turn_id = turn['id']
                self.turn_start_accepted = True
                # Never persist or traverse result.turn.items: reasoning may be nested.
                self.emit({'type': 'turn_start_accepted', 'status': turn.get('status')})
            return result

    def notification(self, event):
        if time.monotonic() >= self.deadline:
            raise SubjectStop('client_call_timeout')
        method = event.get('method')
        params = event.get('params')
        if not isinstance(params, dict):
            params = {}
        if 'id' in event:
            # Do not approve, execute, or persist parameters of any server request.
            self.emit({'type': 'forbidden_server_request', 'arguments_retained': False})
            raise SubjectStop('unsupported_tool_or_approval_request')
        # Unknown/raw/reasoning notifications are discarded before persistence.
        if not isinstance(method, str) or 'reasoning' in method.lower() or 'raw' in method.lower():
            return
        if self.thread_id and params.get('threadId') not in (None, self.thread_id):
            raise SubjectStop('cross_thread_notification')
        if self.turn_id and params.get('turnId') not in (None, self.turn_id):
            raise SubjectStop('cross_turn_notification')
        if method in ('item/started', 'item/completed'):
            item = params.get('item')
            if not isinstance(item, dict):
                raise SubjectStop('invalid_item_event')
            kind = item.get('type')
            if kind in ('reasoning', 'userMessage'):
                return
            if kind == 'agentMessage':
                if method == 'item/started':
                    return
                text, phase, item_id = item.get('text'), item.get('phase'), item.get('id')
                if not isinstance(text, str) or phase not in (None, 'commentary', 'final_answer') or not isinstance(item_id, str):
                    raise SubjectStop('invalid_visible_message')
                if item_id in self.completed_message_ids:
                    raise SubjectStop('duplicate_completed_message')
                self.completed_message_ids.add(item_id)
                self.partial_messages.pop(item_id, None)
                public = {'type': 'visible_agent_message', 'phase': phase, 'text': text}
                self.messages.append(public)
                self.emit(public)
                return
            # All native non-message actions violate this arm's observation boundary.
            known = {'commandExecution', 'fileChange', 'mcpToolCall', 'dynamicToolCall',
                     'collabAgentToolCall', 'webSearch', 'imageView', 'imageGeneration',
                     'hookPrompt', 'plan', 'contextCompaction', 'functionCallOutput'}
            self.emit({'type': 'forbidden_native_tool_attempt',
                       'item_type': kind if kind in known else 'unrecognized',
                       'arguments_retained': False})
            raise SubjectStop('unsupported_native_tool_attempt')
        if method == 'item/agentMessage/delta':
            item_id, delta = params.get('itemId'), params.get('delta')
            if not isinstance(item_id, str) or not isinstance(delta, str):
                raise SubjectStop('invalid_visible_message_delta')
            self.partial_messages[item_id] = self.partial_messages.get(item_id, '') + delta
            self.emit({'type': 'visible_agent_message_delta', 'text': delta})
        elif method == 'thread/tokenUsage/updated':
            self.usage = public_token_usage(params.get('tokenUsage'))
            self.emit({'type': 'public_token_usage', 'usage': self.usage})
        elif method == 'model/rerouted':
            actual = params.get('toModel')
            if not isinstance(actual, str) or not actual:
                raise SubjectStop('runtime_model_metadata_invalid')
            self.model_returned = actual
            self.emit({'type': 'runtime_model', 'model_returned': actual, 'source': 'model/rerouted'})
            if actual != self.requested_model:
                raise SubjectStop('runtime_model_drift')
        elif method == 'model/verification':
            # The installed schema normally reports verification categories, not IDs.
            actual = params.get('model')
            if isinstance(actual, str) and actual:
                self.model_returned = actual
                self.emit({'type': 'runtime_model', 'model_returned': actual, 'source': 'model/verification'})
                if actual != self.requested_model:
                    raise SubjectStop('runtime_model_drift')
        elif method == 'error':
            error = public_error(params.get('error'))
            self.emit({'type': 'client_error', **error, 'will_retry': params.get('willRetry') is True})
            self.turn_error = error
            if params.get('willRetry') is True:
                raise SubjectStop('client_internal_retry_announced')
            if error['code'] in QUOTA_CODES or error['http_status'] == 429:
                raise SubjectStop('subscription_quota_exhausted')
            if error['code'] in ('unauthorized', 'badRequest', 'sandboxError'):
                raise SubjectStop('client_authorization_or_settings_failure')
        elif method == 'turn/completed':
            turn = params.get('turn')
            if not isinstance(turn, dict):
                raise SubjectStop('invalid_turn_status')
            if self.turn_id and turn.get('id') != self.turn_id:
                raise SubjectStop('cross_turn_completion')
            status = turn.get('status')
            if status not in ('completed', 'interrupted', 'failed', 'inProgress'):
                raise SubjectStop('invalid_turn_status')
            self.turn_status = status
            self.turn_error = public_error(turn['error']) if turn.get('error') is not None else self.turn_error
            self.turn_finished = True
            # Deliberately ignore turn.items and all error message/details fields.
            self.emit({'type': 'turn_status', 'status': status, 'error': self.turn_error})
            if self.turn_error and (self.turn_error['code'] in QUOTA_CODES or self.turn_error['http_status'] == 429):
                raise SubjectStop('subscription_quota_exhausted')

    def await_result(self):
        while not self.turn_finished:
            event = self._read(self.deadline)
            if 'method' not in event:
                raise SubjectStop('unexpected_post_start_response')
            self.notification(event)
        if self.turn_error and self.turn_error['code'] in REFUSAL_CODES:
            raise OutcomeFailure('refusal')
        if self.turn_status != 'completed':
            raise OutcomeFailure('client_incomplete')
        finals = [message['text'] for message in self.messages if message['phase'] == 'final_answer']
        if len(finals) > 1:
            raise OutcomeFailure('multiple_final_answers')
        if finals:
            answer = finals[0]
        else:
            unphased = [message['text'] for message in self.messages if message['phase'] is None]
            if len(unphased) != 1:
                raise OutcomeFailure('missing_or_ambiguous_final_answer')
            answer = unphased[0]
        try:
            parse_obj(answer)
        except ValueError:
            raise OutcomeFailure('refusal' if VISIBLE_REFUSAL.match(answer) else 'malformed_json_or_schema') from None
        return answer


class SubjectProvider:
    """Compatibility surface for inherited run_episode; no API fallback exists."""
    mock = False
    mocks = False

    def __init__(self, c, out, budget):
        self.c, self.out, self.budget = c, Path(out), budget
        self.raw = self.out / 'requests'
        self.raw.mkdir(parents=True, exist_ok=True)
        self.halted = False
        self.stop_category = None
        self.calls = 0
        self.spent = None
        if (c.get('provider') != 'codex_subscription' or c.get('protocol_version') != PROTOCOL
                or c.get('api_fallback') is not False or c.get('extra_credits_allowed') is not False
                or c.get('allow_synthetic_transmission') is not True or c.get('max_retries') != 0
                or c.get('workers') != 1 or c.get('reasoning_effort') != 'medium'
                or c.get('billing_route') != 'included_subscription_only'
                or c.get('allowed_agent_tools') != [] or not isinstance(c.get('models'), list)
                or len(c['models']) != 1 or not isinstance(c['models'][0], str)):
            raise SubjectStop('invalid_subject_configuration')
        self.boundary = json.loads(linked_artifact(c, 'subject_boundary'))
        host = json.loads(linked_artifact(c, 'host_boundary'))
        linked_artifact(c, 'billing_control')
        linked_artifact(c, 'authorization')
        self.wrapper = linked_artifact(c, 'wrapper').decode('utf-8')
        if self.boundary.get('passed') is not True or host.get('passed') is not True:
            raise SubjectStop('boundary_evidence_not_passed')
        if c.get('profile_overrides') != self.boundary.get('profile_overrides'):
            raise SubjectStop('profile_override_drift')
        if (host.get('profile_overrides') != c['profile_overrides']
                or host.get('boundary_sha256') != c['subject_boundary_sha256']):
            raise SubjectStop('host_boundary_linkage_drift')
        self.expected_skills = sorted(self.boundary['initial_skills'], key=canonical)
        if any(skill.get('enabled') is not False for skill in self.expected_skills):
            raise SubjectStop('audited_skill_enabled')

    def append_event(self, value):
        with (self.out / 'events.jsonl').open('a') as stream:
            stream.write(json.dumps(value, sort_keys=True, allow_nan=False) + '\n')
            stream.flush()
            os.fsync(stream.fileno())

    def stop(self, category):
        self.halted = True
        self.stop_category = category
        raise SubjectStop(category)

    def verify_boundary(self, client, model, messages):
        skills = skill_inventory(client.request('skills/list', {
            'cwds': [client.folder.name], 'forceReload': True}))
        if skills != self.expected_skills:
            raise SubjectStop('skill_catalog_drift')
        result = client.request('thread/start', {
            'model': model, 'modelProvider': 'openai', 'allowProviderModelFallback': False,
            'cwd': client.folder.name, 'ephemeral': True, 'environments': [],
            'runtimeWorkspaceRoots': [], 'selectedCapabilityRoots': [], 'dynamicTools': [],
            'permissions': 'realgame_subject', 'approvalPolicy': 'never',
            'baseInstructions': messages[0]['content'], 'developerInstructions': self.wrapper,
            'experimentalRawEvents': False, 'serviceTier': 'default',
            'config': {'model_reasoning_effort': self.c['reasoning_effort']},
        })
        thread = result.get('thread') or {}
        expected = self.boundary['thread_start_response']
        fields = ('model', 'modelProvider', 'reasoningEffort', 'serviceTier',
                  'instructionSources', 'runtimeWorkspaceRoots', 'sandbox', 'activePermissionProfile')
        if any(result.get(key) != expected.get(key) for key in fields):
            raise SubjectStop('thread_boundary_or_settings_drift')
        if (thread.get('cliVersion') != self.c['client_version']
                or thread.get('ephemeral') is not True or thread.get('environments') != []
                or thread.get('parentThreadId') is not None or thread.get('forkedFromId') is not None
                or not isinstance(thread.get('id'), str)):
            raise SubjectStop('thread_context_or_client_version_drift')
        client.thread_id = thread['id']
        mcp = client.request('mcpServerStatus/list', {
            'threadId': client.thread_id, 'limit': 100, 'detail': 'toolsAndAuthOnly'})
        if mcp.get('data') != [] or mcp.get('nextCursor'):
            raise SubjectStop('mcp_boundary_drift')
        usage = verify_included_usage(sanitize_usage(client.request('account/rateLimits/read')))
        return {'configured_model': result['model'], 'configured_effort': result['reasoningEffort'],
                'client_version': thread['cliVersion'], 'instruction_sources': [],
                'runtime_workspace_roots': [], 'environments': [], 'ephemeral': True,
                'permission_profile': 'realgame_subject', 'mcp_servers': 0,
                'enabled_skills': 0, 'included_usage_check': usage,
                'complete_native_tool_inventory_available': False}

    def call(self, model, messages, kind, runid, index):
        if self.halted:
            raise SubjectStop(self.stop_category)
        if model != self.c['models'][0]:
            self.stop('requested_model_drift')
        try:
            validate_public_history(messages)
        except AccessBlocked:
            self.stop('forbidden_protocol_context')
        expected_prompt = SYSTEM if kind == 'action' else PROB
        if (kind not in ('action', 'pre_reveal_report', 'final_report')
                or messages[0] != {'role': 'system', 'content': expected_prompt}
                or any(message['role'] == 'system' for message in messages[1:])):
            self.stop('forbidden_protocol_context')
        path = self.raw / f'{runid}-{index:02d}.json'
        if path.exists():
            self.stop('request_reuse_forbidden')
        try:
            ordinal = self.budget.reserve(runid, index)
        except AccessBlocked:
            self.stop('global_invocation_or_time_limit')
        start = time.monotonic()
        deadline = start + min(self.c['request_timeout_seconds'], self.budget.remaining_seconds())
        context = {'run_id': runid, 'index': index, 'kind': kind, 'invocation_ordinal': ordinal}
        emit = lambda event: self.append_event({**context, **event})
        emit({'type': 'client_invocation_started', 'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'model_requested': model, 'payload_hash': digest(messages)})
        record = {**context, 'model_requested': model, 'model_returned': None,
                  'backend': 'codex_subscription', 'payload': messages, 'payload_hash': digest(messages),
                  'transport': 'official_codex_app_server',
                  'status': 'started', 'failure_category': None, 'visible_text': '',
                  'usage': None, 'credit_consumption': None, 'monetary_cost_usd': None,
                  'backend_request_count': None, 'turn_submission_confirmed': False,
                  'turn_submission_reserved': False, 'turn_submitted': False,
                  'hidden_reasoning_retained': False, 'raw_stream_retained': False}
        submitted = False
        client = None
        def guard_submission():
            try:
                self.budget.note_turn_submission(runid, index)
            except AccessBlocked:
                raise SubjectStop('global_turn_or_time_limit') from None
            record['turn_submission_reserved'] = True
            emit({'type': 'turn_submission_reserved'})
        def note_submitted():
            nonlocal submitted
            submitted = True
            self.calls += 1
            record['turn_submission_confirmed'] = True
            record['turn_submitted'] = True
            emit({'type': 'turn_submitted_to_official_client'})
        try:
            client = SubjectClient(self.c, deadline, emit, note_submitted, guard_submission)
            with client:
                record['preturn_boundary'] = self.verify_boundary(client, model, messages)
                emit({'type': 'preturn_boundary_passed', 'enabled_skills': 0, 'mcp_servers': 0})
                if self.budget.remaining_seconds() <= 0:
                    raise SubjectStop('global_inference_timeout')
                client.request('turn/start', {
                    'threadId': client.thread_id,
                    'input': [{'type': 'text', 'text': canonical(messages[1:])}],
                    'model': model, 'effort': self.c['reasoning_effort'], 'summary': 'none',
                    'environments': [], 'runtimeWorkspaceRoots': [],
                    'serviceTierForTurn': 'default',
                })
                answer = client.await_result()
                record.update(status='success', visible_text=answer)
                return answer
        except SubjectStop as error:
            self.halted = True
            self.stop_category = error.category
            record.update(status='failure', failure_category=error.category)
            emit({'type': 'pilot_stop', 'category': error.category, 'turn_submitted': submitted})
            raise
        except OutcomeFailure as error:
            record.update(status='failure', failure_category=error.category)
            raise
        except (MetadataError, AccessBlocked, OSError, ValueError, TypeError, KeyError) as error:
            category = 'client_call_timeout' if isinstance(error, MetadataError) and str(error) == 'metadata_timeout' else 'client_startup_or_transport_failure'
            self.halted, self.stop_category = True, category
            record.update(status='failure', failure_category=category, error_type=type(error).__name__)
            emit({'type': 'pilot_stop', 'category': category, 'turn_submitted': submitted})
            raise SubjectStop(category) from None
        finally:
            if client is not None:
                record.update(visible_messages=client.messages,
                              partial_visible_messages=list(client.partial_messages.values()),
                              usage=client.usage, model_returned=client.model_returned,
                              turn_start_accepted=client.turn_start_accepted,
                              client_turn_start_accepted=client.turn_start_accepted,
                              client_turn_status=client.turn_status, client_error=client.turn_error,
                              cancellation_rpc_attempts=client.cancellation_requests_attempted,
                              cancellation_rpc_submissions=client.cancellation_requests_submitted,
                              metadata_rpc_attempts=client.calls - int(submitted) - client.cancellation_requests_attempted,
                              metadata_rpc_submissions=client.submissions - int(submitted) - client.cancellation_requests_submitted)
                if not record['visible_text']:
                    finals = [item['text'] for item in client.messages if item['phase'] == 'final_answer']
                    unphased = [item['text'] for item in client.messages if item['phase'] is None]
                    if len(finals) == 1:
                        record['visible_text'] = finals[0]
                    elif not finals and len(unphased) == 1:
                        record['visible_text'] = unphased[0]
            record['elapsed_seconds'] = round(time.monotonic() - start, 4)
            if submitted:
                with path.open('x') as stream:
                    stream.write(json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + '\n')
                    stream.flush()
                    os.fsync(stream.fileno())
            emit({'type': 'client_invocation_finished', 'turn_submitted': submitted,
                  'status': record['status'], 'failure_category': record['failure_category'],
                  'elapsed_seconds': record['elapsed_seconds']})
