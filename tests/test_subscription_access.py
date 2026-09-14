"""Offline access regressions. All synthetic fixtures are MOCK-NOT-LLM.

No test invokes the official executable, queries an account, or sends inference.
Passing these tests does not establish billing enforcement or subject isolation.
"""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts'), str(ROOT / 'access')]
import codex_subscription as subscription
import codex_subject as subject
import inspect_codex_access as inspection
from codex_budget import GlobalPilotBudget
from check_readiness import inference_gates
from run_llm import OutcomeFailure, Provider, parse_obj, run_episode, visible_response
from analyze_llm import outcome_accounting
from worlds import Scenario
from analyze_codex_pilot import analyze_blocked_design, analyze_subject_records

MOCK_LABEL = 'MOCK-NOT-LLM'


def mock_config():
    return {
        'fixture_label': MOCK_LABEL,
        'protocol_version': subscription.PROTOCOL,
        'provider': 'codex_subscription',
        'allow_synthetic_transmission': True,
        'billing_route': 'included_subscription_only',
        'api_fallback': False,
        'extra_credits_allowed': False,
        'models': [MOCK_LABEL],
        'reasoning_effort': 'low',
        'workers': 1,
        'max_episodes': 20,
        'max_client_invocations': 140,
        'inference_wallclock_seconds': 2700,
        'seeds_per_cell': 1,
    }


def mock_discovery():
    return {
        'fixture_label': MOCK_LABEL,
        'auth_type': 'chatgpt',
        'official_cli_available': True,
        'models': [{
            'fixture_label': MOCK_LABEL,
            'model': MOCK_LABEL,
            'hidden': False,
            'supportedReasoningEfforts': [{'reasoningEffort': 'low'}],
        }],
    }


def mock_event(method, **params):
    return {'fixture_label': MOCK_LABEL, 'method': method, 'params': params}


def mock_included_usage():
    return {
        'fixture_label': MOCK_LABEL,
        'ordinaryUsageAllowed': True,
        'rateLimits': {
            'limitId': 'codex', 'spendControlReached': False,
            'rateLimitReachedType': None,
            'credits': {'hasCredits': False, 'unlimited': False, 'balance': '0'},
            'primary': {'usedPercent': 10, 'windowDurationMins': 300},
            'secondary': None,
        },
    }


def mock_frozen_design():
    from run_llm import plan
    cfg = mock_config()
    cfg.update(first_seed=1000, shuffle_seed=60821)
    return {'fixture_label': MOCK_LABEL, 'protocol_version': subscription.PROTOCOL,
            'config': cfg, 'planned': [
                {'fixture_label': MOCK_LABEL, 'model': model, 'scenario': scenario.__dict__}
                for model, scenario in plan(cfg, False)]}


def mock_subject_client(events):
    cfg = mock_config()
    cfg.update(request_timeout_seconds=90, profile_overrides=[MOCK_LABEL],
               codex_executable=MOCK_LABEL)
    return subject.SubjectClient(cfg, float('inf'), events.append,
                                 lambda: None, lambda: None)


class SubscriptionAccessTests(unittest.TestCase):
    def setUp(self):
        # A regression that unexpectedly attempts an official process fails offline.
        self.process_guard = mock.patch('codex_subscription.subprocess.Popen',
                                        side_effect=AssertionError('MOCK-NOT-LLM: process forbidden'))
        self.process_guard.start()
        self.addCleanup(self.process_guard.stop)

    def test_subscription_does_not_require_api_credentials_or_prices(self):
        with mock.patch.dict('os.environ', {}, clear=True):
            gates = subscription.subscription_gates(
                mock_config(), mock_discovery(), authorization_verified=True)
        self.assertFalse(gates['api_key_required'])
        self.assertFalse(gates['api_token_prices_required'])
        self.assertFalse(gates['ready_by_configuration'])
        self.assertEqual(len(gates['missing']), 2)
        self.assertTrue(any('extra-credit' in item for item in gates['missing']))
        self.assertTrue(any('isolation' in item for item in gates['missing']))

    def test_config_assertions_cannot_authorize_or_verify_boundaries(self):
        cfg = mock_config()
        cfg.update(authorization_verified=True, human_authorization=True,
                   INCLUDED_ONLY_EXECUTION_IMPLEMENTED=True,
                   SUBJECT_ISOLATION_VERIFIED=True,
                   included_only_execution_implemented=True,
                   subject_isolation_verified=True)
        gates = subscription.subscription_gates(cfg, mock_discovery())
        self.assertFalse(gates['ready_by_configuration'])
        self.assertTrue(any('human approval' in item for item in gates['missing']))
        self.assertTrue(any('extra-credit' in item for item in gates['missing']))
        self.assertTrue(any('isolation' in item for item in gates['missing']))
        self.assertTrue(gates['experimental_execution_implemented'])

    def test_api_route_retains_credential_price_and_budget_requirements(self):
        cfg = json.loads((ROOT / 'configs/halfday.json').read_text())
        cfg.update(models=[MOCK_LABEL], provider='responses',
                   base_url='https://api.openai.com/v1',
                   approved_hosts=['api.openai.com'], allow_network=True,
                   api_key_env='MOCK_NOT_LLM_API_KEY', paid_calls_authorized=False,
                   max_estimated_usd=0, price_input_per_million=None,
                   price_output_per_million=None, price_source=None)
        with mock.patch.dict('os.environ', {}, clear=True):
            gates = inference_gates(cfg)
        missing = '\n'.join(gates['missing'])
        self.assertFalse(gates['ready_by_configuration'])
        self.assertIn('credential', missing)
        self.assertIn('spending ceiling', missing)
        self.assertIn('token prices', missing)

    def test_paid_api_fallback_and_extra_credit_use_are_rejected(self):
        for key in ('api_fallback', 'extra_credits_allowed'):
            for value in (True, None, 'false', 0):
                with self.subTest(key=key, value=value):
                    cfg = mock_config()
                    cfg[key] = value
                    gates = subscription.subscription_gates(
                        cfg, mock_discovery(), authorization_verified=True)
                    self.assertIn('API fallback and extra-credit use must be disabled',
                                  gates['missing'])

    def test_model_and_effort_must_match_non_hidden_discovery(self):
        for mutation in ('hidden', 'absent', 'effort', 'second_model'):
            with self.subTest(mutation=mutation):
                cfg, discovery = mock_config(), mock_discovery()
                if mutation == 'hidden':
                    discovery['models'][0]['hidden'] = True
                elif mutation == 'absent':
                    discovery['models'] = []
                elif mutation == 'effort':
                    cfg['reasoning_effort'] = 'unsupported-MOCK-NOT-LLM'
                else:
                    cfg['models'].append('second-MOCK-NOT-LLM')
                gates = subscription.subscription_gates(
                    cfg, discovery, authorization_verified=True)
                self.assertTrue(any('model/list' in item or 'reasoning effort' in item
                                    for item in gates['missing']))

    def test_authorized_caps_reject_excess_nonpositive_and_boolean_values(self):
        for key, maximum in (('workers', 1), ('max_episodes', 20),
                             ('max_client_invocations', 140),
                             ('inference_wallclock_seconds', 2700)):
            for value in (maximum + 1, 0, -1, True, 1.0):
                with self.subTest(key=key, value=value):
                    cfg = mock_config()
                    cfg[key] = value
                    gates = subscription.subscription_gates(
                        cfg, mock_discovery(), authorization_verified=True)
                    self.assertIn('Authorized positive cap: ' + key, gates['missing'])
        for kwargs in ({'max_invocations': 141}, {'max_invocations': True},
                       {'seconds': 2701}, {'seconds': 0}):
            with self.subTest(kwargs=kwargs), self.assertRaises(subscription.AccessBlocked):
                subscription.PilotBudget(**kwargs)

    def test_one_outer_allowance_stops_after_reserved_submissions(self):
        budget = subscription.PilotBudget(max_invocations=2, seconds=10, clock=lambda: 0)
        self.assertEqual(budget.reserve(), 1)
        self.assertEqual(budget.reserve(), 2)
        with self.assertRaisesRegex(subscription.AccessBlocked, 'invocation cap'):
            budget.reserve()
        self.assertEqual(budget.submitted, 2)

    def test_outer_timeout_does_not_reserve_an_additional_turn(self):
        now = [100.0]
        budget = subscription.PilotBudget(seconds=10, clock=lambda: now[0])
        budget.reserve()
        now[0] = 110.0
        with self.assertRaisesRegex(subscription.AccessBlocked, 'time cap'):
            budget.reserve()
        self.assertEqual(budget.submitted, 1)

    def test_metadata_allowlist_rejects_actions_before_process_access(self):
        forbidden = ('turn/start', 'thread/start', 'thread/resume',
                     'account/rateLimitResetCredit/consume', 'account/credits/purchase',
                     'account/sendAddCreditsNudgeEmail', 'account/logout',
                     'account/login/start', 'config/value/write')
        client = subscription.OfficialMetadataClient(executable=MOCK_LABEL)
        with mock.patch.object(client, '_send') as send, \
                mock.patch('codex_subscription.subprocess.Popen') as popen:
            for method in forbidden:
                with self.subTest(method=method), self.assertRaises(subscription.AccessBlocked):
                    client.request(method, {'fixture_label': MOCK_LABEL})
            send.assert_not_called()
            popen.assert_not_called()
        self.assertIsNone(client.process)
        self.assertEqual(client.calls, 0)

    def test_metadata_timeout_is_sanitized_without_reading_process_output(self):
        client = subscription.OfficialMetadataClient(executable=MOCK_LABEL)
        client.selector = mock.Mock(name=MOCK_LABEL)
        client.selector.select.return_value = []
        with mock.patch('codex_subscription.time.monotonic', return_value=0), \
                mock.patch('codex_subscription.os.read') as read:
            with self.assertRaisesRegex(subscription.MetadataError, '^metadata_timeout$'):
                client._read(1)
            read.assert_not_called()

    def test_catalog_excludes_hidden_missing_hidden_and_invalid_entries(self):
        public = {'fixture_label': MOCK_LABEL, 'id': MOCK_LABEL, 'model': MOCK_LABEL,
                  'hidden': False, 'isDefault': True, 'defaultReasoningEffort': 'low',
                  'supportedReasoningEfforts': [
                      {'reasoningEffort': 'low', 'description': MOCK_LABEL}, {}, 'bad'],
                  'private_context': MOCK_LABEL + '-DROP'}
        result = subscription.sanitize_models({'fixture_label': MOCK_LABEL, 'data': [
            public, dict(public, hidden=True), dict(public, hidden=None),
            dict(public, model=''), dict(public, model=None), None]})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['model'], MOCK_LABEL)
        self.assertEqual(result[0]['supportedReasoningEfforts'], [{'reasoningEffort': 'low'}])
        self.assertNotIn('private_context', result[0])
        self.assertNotIn('description', json.dumps(result))

    def test_usage_keeps_missing_costs_null_and_drops_account_identity(self):
        result = subscription.sanitize_usage({
            'fixture_label': MOCK_LABEL, 'accountId': MOCK_LABEL + '-ACCOUNT-DROP',
            'ordinaryUsageAllowed': None,
            'rateLimits': {'limitId': MOCK_LABEL,
                           'primary': {'usedPercent': 1, 'windowDurationMins': 300},
                           'credits': {'hasCredits': True, 'unlimited': False, 'balance': '12'}},
            'rateLimitResetCredits': {'fixture_label': MOCK_LABEL, 'availableCount': 5}})
        self.assertIsNone(result['ordinaryUsageAllowed'])
        self.assertIsNone(result['monetary_cost_usd'])
        self.assertIsNone(result['credit_consumption'])
        self.assertFalse(result['account_identity_retained'])
        self.assertNotIn('ACCOUNT-DROP', json.dumps(result))
        self.assertNotIn('rateLimitResetCredits', result)

    def test_missing_effective_model_is_not_filled_from_requested_slug(self):
        event = mock_event('turn/completed', requested_model=MOCK_LABEL,
                           turn={'id': MOCK_LABEL, 'status': 'completed'})
        visible = subscription.filter_visible_event(event)
        self.assertIsNone(visible['model_returned'])
        self.assertEqual(visible['status'], 'completed')
        self.assertIsNone(visible_response({
            'fixture_label': MOCK_LABEL, 'requested_model': MOCK_LABEL,
            'status': 'completed', 'output': []}, 'responses')['model_returned'])

    def test_reasoning_and_nonfinal_event_payloads_are_dropped(self):
        events = [
            mock_event('item/reasoning/textDelta', text=MOCK_LABEL + '-REASONING-DROP'),
            mock_event('item/completed', item={'type': 'reasoning',
                                               'content': MOCK_LABEL + '-REASONING-DROP'}),
            mock_event('item/completed', item={'type': 'agentMessage', 'phase': 'commentary',
                                               'text': MOCK_LABEL + '-COMMENTARY-DROP'}),
            mock_event('rawResponse/completed', payload=MOCK_LABEL + '-RAW-DROP'),
        ]
        for event in events:
            with self.subTest(method=event['method']):
                self.assertIsNone(subscription.filter_visible_event(event))
        final = mock_event('item/completed', item={
            'type': 'agentMessage', 'phase': 'final_answer', 'text': MOCK_LABEL,
            'reasoning': MOCK_LABEL + '-REASONING-DROP'})
        self.assertEqual(subscription.filter_visible_event(final),
                         {'type': 'visible_final_answer', 'text': MOCK_LABEL})

    def test_forbidden_tool_attempts_are_countable_without_arguments(self):
        for tool_type in ('commandExecution', 'fileChange', 'mcpToolCall',
                          'webSearch', 'dynamicToolCall', 'collabAgentToolCall'):
            with self.subTest(tool_type=tool_type):
                event = mock_event('item/completed', item={
                    'type': tool_type, 'arguments': MOCK_LABEL + '-ARGUMENTS-DROP',
                    'output': MOCK_LABEL + '-OUTPUT-DROP'})
                visible = subscription.filter_visible_event(event)
                self.assertEqual(visible['type'], 'forbidden_tool_attempt')
                self.assertEqual(visible['tool_type'], tool_type)
                self.assertFalse(visible['arguments_retained'])
                self.assertNotIn('-DROP', json.dumps(visible))

    def test_coordinator_context_fields_are_rejected(self):
        public = [{'role': 'system', 'content': MOCK_LABEL},
                  {'role': 'user', 'content': MOCK_LABEL}]
        self.assertEqual(subscription.validate_public_history(public), public)
        for field in ('world', 'scenario', 'results', 'cwd', 'files', 'tools',
                      'AGENTS.md', 'memory', 'coordinator_transcript'):
            with self.subTest(field=field), self.assertRaises(subscription.AccessBlocked):
                subscription.validate_public_history([
                    dict(public[0], **{field: MOCK_LABEL + '-FORBIDDEN'})])
        for messages in ([], {'fixture_label': MOCK_LABEL},
                         [{'role': 'tool', 'content': MOCK_LABEL}]):
            with self.subTest(messages=messages), self.assertRaises(subscription.AccessBlocked):
                subscription.validate_public_history(messages)

    def test_strict_visible_json_rejects_overflow_duplicates_and_repair_text(self):
        invalid = (
            '{"fixture":"MOCK-NOT-LLM","probability":1e400}',
            '{"fixture":"MOCK-NOT-LLM","nested":[-1e400]}',
            '{"fixture":"MOCK-NOT-LLM","choice":"standard","choice":"shortcut"}',
            '{"fixture":"MOCK-NOT-LLM","probability":NaN}',
            'MOCK-NOT-LLM answer: {"probability":0.5}',
            '{"fixture":"MOCK-NOT-LLM","probability":',
        )
        for visible_text in invalid:
            with self.subTest(visible_text=visible_text), self.assertRaises(ValueError):
                parse_obj(visible_text)
        self.assertEqual(parse_obj('{"fixture":"MOCK-NOT-LLM","probability":0.5}')
                         ['probability'], 0.5)

    def test_refusals_and_truncations_preserve_visible_evidence(self):
        refusal = {'fixture_label': MOCK_LABEL, 'model': MOCK_LABEL, 'status': 'completed',
                   'usage': {'input_tokens': 10, 'output_tokens': 4},
                   'output': [{'type': 'reasoning', 'content': MOCK_LABEL + '-REASONING-DROP'},
                              {'type': 'message', 'content': [
                                  {'type': 'refusal', 'refusal': MOCK_LABEL + ' refusal.'}]}]}
        visible = visible_response(refusal, 'responses')
        self.assertEqual(visible['failure_category'], 'refusal')
        self.assertEqual(visible['refusal_text'], MOCK_LABEL + ' refusal.')
        self.assertEqual(visible['usage']['output_tokens'], 4)
        self.assertNotIn('REASONING-DROP', json.dumps(visible))
        truncated = copy.deepcopy(refusal)
        text = '{"fixture":"MOCK-NOT-LLM","probability":'
        truncated.update(status='incomplete', incomplete_details={'reason': 'max_output_tokens'},
                         output=[{'type': 'message', 'content': [
                             {'type': 'output_text', 'text': text}]}])
        visible = visible_response(truncated, 'responses')
        self.assertEqual(visible['failure_category'], 'truncation')
        self.assertEqual(visible['visible_text'], text)

    def test_local_discovery_drops_raw_login_output(self):
        def mock_command(command, **kwargs):
            if command[1:] == ['--version']:
                stdout = 'codex-cli 0.154.0\n'
            elif command[1:] == ['login', 'status']:
                stdout = 'Logged in using ChatGPT. MOCK-NOT-LLM-PRIVATE-STATUS\n'
            else:
                stdout = 'MOCK-NOT-LLM help --json --stdio\n'
            return mock.Mock(returncode=0, stdout=stdout, stderr='')

        with mock.patch.object(inspection.subprocess, 'run', side_effect=mock_command), \
                mock.patch.object(inspection.shutil, 'which', return_value=MOCK_LABEL):
            discovery = inspection.inspect_local(check_login=True)
        self.assertEqual(discovery['auth_type'], 'chatgpt')
        self.assertEqual(discovery['client_version'], '0.154.0')
        self.assertNotIn('PRIVATE-STATUS', json.dumps(discovery))
        login = next(row for row in discovery['commands'] if 'login status' in row['command'])
        self.assertFalse(login['raw_output_retained'])

    def test_committed_action_and_full_denominator_survive_later_refusal(self):
        cfg = json.loads((ROOT / 'configs/halfday.json').read_text())
        scenario = Scenario('persistence', 'before', 0, 0, 8181)
        with tempfile.TemporaryDirectory(prefix='MOCK-NOT-LLM-') as folder:
            out = Path(folder)
            (out / 'episodes').mkdir()
            provider = Provider(cfg, out, mock=True)
            mock_call = provider.call

            def mock_refusal_call(model, messages, kind, runid, index):
                result = mock_call(model, messages, kind, runid, index)
                if kind == 'pre_reveal_report':
                    raise OutcomeFailure('refusal')
                return result

            provider.call = mock_refusal_call
            row = run_episode(provider, MOCK_LABEL, scenario)
        self.assertEqual(row['choice'], 'standard')
        self.assertIsNone(row['probability_pre_reveal'])
        self.assertEqual(row['probability_final'], 0.5)
        self.assertEqual(row['status'], 'partial_report')
        self.assertEqual(row['api_calls_in_episode'], 3)
        planned = [{'fixture_label': MOCK_LABEL, 'model': MOCK_LABEL, 'scenario': item.__dict__}
                   for item in (scenario, Scenario('persistence', 'before', 1, 0, 8181))]
        account = outcome_accounting([row], {'planned': planned}, [])
        self.assertEqual(account['planned_episodes'], 2)
        self.assertEqual(account['episodes_with_provider_attempt'], 1)
        self.assertEqual(account['completed_actions'], 1)
        self.assertEqual(account['complete_probability_reports'], 0)
        self.assertEqual(account['unstarted_episodes'], 1)
        self.assertEqual(account['episode_failure_categories'], {'refusal': 1})
        self.assertEqual(account['groups_by_world'][1]['shortcut_planned_bounds'], [0, 1])

    def test_unverified_transport_cannot_be_enabled_by_call_arguments(self):
        with mock.patch('codex_subscription.subprocess.Popen') as popen:
            with self.assertRaisesRegex(subscription.AccessBlocked, 'billing and isolation'):
                subscription.start_experimental_call(
                    fixture_label=MOCK_LABEL, authorization_verified=True,
                    billing_verified=True, isolation_verified=True)
            popen.assert_not_called()

    def test_metadata_rpc_errors_drop_server_error_text(self):
        client = subscription.OfficialMetadataClient(executable=MOCK_LABEL)
        response = {'fixture_label': MOCK_LABEL, 'id': 1,
                    'error': {'code': -32000, 'message': MOCK_LABEL + '-PRIVATE-DROP'}}
        with mock.patch.object(client, '_send'), \
                mock.patch.object(client, '_read', return_value=response):
            with self.assertRaisesRegex(subscription.MetadataError, '^metadata_rpc_error_-32000$'):
                client.request('model/list', {'includeHidden': False})
        self.assertEqual(client.calls, 1)

    def test_malformed_metadata_retains_sanitized_error_category(self):
        for result in ({'data': None}, {'data': [{'hidden': False, 'model': MOCK_LABEL,
                                                  'supportedReasoningEfforts': None}]}):
            with self.subTest(result=result), self.assertRaises(subscription.MetadataError):
                subscription.sanitize_models(result)
        for result in ({'ordinaryUsageAllowed': float('inf')},
                       {'rateLimits': {'primary': {'usedPercent': float('nan')}}},
                       {'rateLimitsByLimitId': []}):
            with self.subTest(result=result), self.assertRaises(subscription.MetadataError):
                subscription.sanitize_usage(result)

    def test_failed_rpc_write_is_attempted_but_not_submitted(self):
        client = subscription.OfficialMetadataClient(executable=MOCK_LABEL)
        with mock.patch.object(client, '_send', side_effect=BrokenPipeError):
            with self.assertRaises(BrokenPipeError):
                client.request('model/list', {'includeHidden': False})
        self.assertEqual(client.calls, 1)
        self.assertEqual(client.submissions, 0)

    def test_subscription_reanalysis_preserves_unstarted_denominator_and_null_cost(self):
        cfg = mock_config()
        cfg.update(first_seed=1000, shuffle_seed=60821)
        from run_llm import plan
        jobs = plan(cfg, False)
        frozen = {'protocol_version': subscription.PROTOCOL,
                  'planned': [{'model': model, 'scenario': scenario.__dict__}
                              for model, scenario in jobs]}
        result = analyze_blocked_design([], frozen, [])
        self.assertEqual(result['planned_episodes'], 20)
        self.assertEqual(result['unstarted_episodes'], 20)
        self.assertEqual(sum(s.budget+3 for _, s in jobs), 108)
        self.assertIsNone(result['charged_estimated_usd'])
        self.assertFalse(result['real_model_calls_documented'])
        with self.assertRaises(ValueError):
            analyze_blocked_design([{'fixture_label': MOCK_LABEL}], frozen, [])

    def test_readiness_requires_linked_boundary_checks_and_separate_billing_attestation(self):
        cfg = mock_config()
        cfg.update(profile_overrides=[MOCK_LABEL], subject_boundary_sha256=MOCK_LABEL)
        required = ('all_catalog_skills_disabled', 'no_instruction_sources', 'no_workspace_roots',
                    'no_environments', 'ephemeral', 'fresh_thread', 'requested_model_retained',
                    'effort_retained', 'named_restricted_profile', 'no_mcp_servers')
        boundary = {'fixture_label': MOCK_LABEL, 'passed': True,
                    'profile_overrides': [MOCK_LABEL],
                    'checks': {key: True for key in required}}
        host = {'fixture_label': MOCK_LABEL, 'passed': True,
                'profile_overrides': [MOCK_LABEL], 'boundary_sha256': MOCK_LABEL}
        gates = subscription.subscription_gates(cfg, mock_discovery(), True, True, boundary, host)
        self.assertTrue(gates['ready_by_configuration'])
        self.assertTrue(gates['experimental_execution_implemented'])
        for key in required:
            with self.subTest(check=key):
                changed = copy.deepcopy(boundary)
                changed['checks'][key] = False
                gates = subscription.subscription_gates(cfg, mock_discovery(), True, True, changed, host)
                self.assertFalse(gates['ready_by_configuration'])
        host['boundary_sha256'] = MOCK_LABEL + '-DIFFERENT'
        gates = subscription.subscription_gates(cfg, mock_discovery(), True, True, boundary, host)
        self.assertFalse(gates['ready_by_configuration'])

    def test_global_budget_persists_across_cohorts_without_replenishing_cap(self):
        with tempfile.TemporaryDirectory(prefix='MOCK-NOT-LLM-') as folder, \
                mock.patch('codex_budget.time.time', return_value=1000.0):
            path = Path(folder) / 'global.jsonl'
            budget = GlobalPilotBudget(path, MOCK_LABEL, limit=2, seconds=10)
            try:
                self.assertEqual(budget.reserve(MOCK_LABEL + '-cohort-a', 0), 1)
                # A startup failure has no turn but still consumes this invocation.
                self.assertEqual(budget.turn_submissions, 0)
            finally:
                budget.close()
            (Path(folder) / 'new-output-directory').mkdir()
            resumed = GlobalPilotBudget(path, MOCK_LABEL, limit=2, seconds=10)
            try:
                self.assertEqual(resumed.invocations, 1)
                self.assertEqual(resumed.reserve(MOCK_LABEL + '-cohort-b', 0), 2)
                resumed.note_turn_submission(MOCK_LABEL + '-cohort-b', 0)
                self.assertEqual(resumed.turn_submissions, 1)
                with self.assertRaises(subscription.AccessBlocked):
                    resumed.reserve(MOCK_LABEL + '-cohort-c', 0)
                with self.assertRaises(subscription.AccessBlocked):
                    resumed.note_turn_submission(MOCK_LABEL + '-cohort-b', 0)
            finally:
                resumed.close()
            self.assertEqual(len(path.read_text().splitlines()), 3)

    def test_global_deadline_survives_reopening_and_stops_pending_turns(self):
        with tempfile.TemporaryDirectory(prefix='MOCK-NOT-LLM-') as folder:
            path = Path(folder) / 'global.jsonl'
            with mock.patch('codex_budget.time.time', return_value=1000.0):
                budget = GlobalPilotBudget(path, MOCK_LABEL, seconds=10)
                try:
                    budget.reserve(MOCK_LABEL, 0)
                finally:
                    budget.close()
            with mock.patch('codex_budget.time.time', return_value=1010.0):
                reopened = GlobalPilotBudget(path, MOCK_LABEL, seconds=10)
                try:
                    self.assertEqual(reopened.started, 1000.0)
                    self.assertEqual(reopened.remaining_seconds(), 0)
                    with self.assertRaises(subscription.AccessBlocked):
                        reopened.reserve(MOCK_LABEL, 1)
                    with self.assertRaises(subscription.AccessBlocked):
                        reopened.note_turn_submission(MOCK_LABEL, 0)
                finally:
                    reopened.close()
            self.assertEqual(len(path.read_text().splitlines()), 1)

    def test_global_allowance_rejects_other_scope_and_duplicate_invocation(self):
        with tempfile.TemporaryDirectory(prefix='MOCK-NOT-LLM-') as folder:
            path = Path(folder) / 'global.jsonl'
            budget = GlobalPilotBudget(path, MOCK_LABEL)
            try:
                budget.reserve(MOCK_LABEL, 0)
                with self.assertRaises(subscription.AccessBlocked):
                    budget.reserve(MOCK_LABEL, 0)
            finally:
                budget.close()
            with self.assertRaisesRegex(subscription.AccessBlocked, 'scope mismatch'):
                GlobalPilotBudget(path, MOCK_LABEL + '-different-approval')

    def test_subject_analysis_keeps_all_unstarted_cells_and_cost_missingness(self):
        frozen = mock_frozen_design()
        unstarted = dict(frozen['planned'][0], run_id=MOCK_LABEL,
                         backend='codex_subscription', attempted=False,
                         status='not_started_resource_limit', choice=None,
                         probability_pre_reveal=None, probability_final=None,
                         outcome_failures=[])
        result = analyze_subject_records([unstarted], frozen, [])
        self.assertEqual(result['planned'], 20)
        self.assertEqual(result['started'], 0)
        self.assertEqual(result['unstarted'], 20)
        self.assertEqual(result['committed_actions'], 0)
        self.assertEqual(result['holm_family_size'], 4)
        self.assertFalse(result['model_backed_evidence_exists'])
        self.assertIsNone(result['monetary_cost_usd'])
        self.assertIsNone(result['credit_consumption'])
        self.assertIsNone(result['outcome_accounting']['charged_estimated_usd'])

    def test_subject_analysis_preserves_commitment_and_refusal_denominators(self):
        frozen = mock_frozen_design()
        row = dict(frozen['planned'][0], run_id=MOCK_LABEL,
                   backend='codex_subscription', attempted=True, status='partial_report',
                   choice='standard', probability_pre_reveal=None, probability_final=0.5,
                   probe_calls=0, outcome_failures=[{'stage': 'pre_reveal_report', 'category': 'refusal'}])
        request = {'fixture_label': MOCK_LABEL, 'run_id': MOCK_LABEL,
                   'model_requested': MOCK_LABEL, 'index': 0,
                   'transport': 'official_codex_app_server', 'turn_submitted': True,
                   'status': 'failure', 'failure_category': 'refusal',
                   'visible_text': 'I cannot comply with MOCK-NOT-LLM.', 'model_returned': None}
        result = analyze_subject_records([row], frozen, [request])
        self.assertEqual((result['planned'], result['started'], result['unstarted']), (20, 1, 19))
        self.assertEqual(result['committed_actions'], 1)
        self.assertEqual(result['valid_pre_diagnostic_probabilities'], 0)
        self.assertEqual(result['valid_final_probabilities'], 1)
        self.assertEqual(result['refused_episodes'], 1)
        self.assertEqual(result['failed_started_episodes'], 1)
        self.assertIsNone(result['monetary_cost_usd'])
        self.assertIsNone(request['model_returned'])

    def test_subject_analysis_rejects_mock_api_and_unlinked_provenance(self):
        frozen = mock_frozen_design()
        row = dict(frozen['planned'][0], run_id=MOCK_LABEL,
                   backend='codex_subscription', attempted=True, status='invalid_output',
                   choice=None, probability_pre_reveal=None, probability_final=None,
                   outcome_failures=[{'stage': 'action', 'category': 'malformed_json_or_schema'}])
        request = {'fixture_label': MOCK_LABEL, 'run_id': MOCK_LABEL,
                   'model_requested': MOCK_LABEL, 'index': 0,
                   'transport': 'official_codex_app_server', 'turn_submitted': True,
                   'status': 'failure', 'failure_category': 'malformed_json_or_schema'}
        for backend in ('mock', 'scripted', 'responses', 'chat'):
            with self.subTest(backend=backend), self.assertRaises(ValueError):
                analyze_subject_records([dict(row, backend=backend)], frozen, [request])
        for invalid in (dict(request, transport='MOCK-NOT-LLM'),
                        dict(request, transport='responses'),
                        dict(request, turn_submitted=False)):
            with self.subTest(request=invalid), self.assertRaises(ValueError):
                analyze_subject_records([row], frozen, [invalid])
        with self.assertRaises(ValueError):
            analyze_subject_records([row], frozen, [])

    def test_subject_client_discards_reasoning_and_nested_turn_items(self):
        events = []
        client = mock_subject_client(events)
        client.notification(mock_event('item/reasoning/textDelta', delta=MOCK_LABEL + '-DROP'))
        client.notification(mock_event('item/completed', item={
            'id': MOCK_LABEL, 'type': 'reasoning', 'text': MOCK_LABEL + '-DROP'}))
        self.assertEqual(events, [])
        client.notification(mock_event('item/completed', item={
            'id': MOCK_LABEL, 'type': 'agentMessage', 'phase': 'final_answer',
            'text': '{"fixture":"MOCK-NOT-LLM","probability":0.5}'}))
        client.notification(mock_event('turn/completed', turn={
            'id': MOCK_LABEL, 'status': 'completed',
            'items': [{'type': 'reasoning', 'content': MOCK_LABEL + '-DROP'}]}))
        self.assertNotIn('-DROP', json.dumps(events))
        self.assertEqual(parse_obj(client.await_result())['probability'], 0.5)
        self.assertIsNone(client.model_returned)

    def test_subject_client_rejects_tools_and_server_approvals_without_payload_retention(self):
        for event in (
            mock_event('item/started', item={'type': 'commandExecution',
                                           'command': MOCK_LABEL + '-DROP'}),
            dict(mock_event('item/commandExecution/requestApproval',
                            command=MOCK_LABEL + '-DROP'), id=MOCK_LABEL),
        ):
            events = []
            client = mock_subject_client(events)
            with self.subTest(method=event['method']), self.assertRaises(subject.SubjectStop):
                client.notification(event)
            self.assertEqual(len(events), 1)
            self.assertFalse(events[0]['arguments_retained'])
            self.assertNotIn('-DROP', json.dumps(events))

    def test_subject_client_preserves_visible_refusal_and_stops_alias_drift(self):
        events = []
        client = mock_subject_client(events)
        refusal = 'I cannot comply with MOCK-NOT-LLM.'
        client.notification(mock_event('item/completed', item={
            'id': MOCK_LABEL, 'type': 'agentMessage', 'phase': 'final_answer', 'text': refusal}))
        client.notification(mock_event('turn/completed', turn={'id': MOCK_LABEL, 'status': 'completed'}))
        with self.assertRaises(OutcomeFailure) as raised:
            client.await_result()
        self.assertEqual(raised.exception.category, 'refusal')
        self.assertIn(refusal, json.dumps(events))
        with self.assertRaises(subject.SubjectStop) as drift:
            client.notification(mock_event('model/rerouted', toModel=MOCK_LABEL + '-different'))
        self.assertEqual(drift.exception.category, 'runtime_model_drift')
        self.assertEqual(client.model_returned, MOCK_LABEL + '-different')

    def test_subscription_usage_changes_fail_closed_without_inference(self):
        self.assertEqual(subject.verify_included_usage(mock_included_usage())['ordinaryUsageAllowed'], True)
        for mutation in ('ordinary_unknown', 'credits_available', 'nonzero', 'overflow',
                         'quota', 'spend_unknown'):
            with self.subTest(mutation=mutation):
                usage = mock_included_usage()
                if mutation == 'ordinary_unknown':
                    usage['ordinaryUsageAllowed'] = None
                elif mutation == 'credits_available':
                    usage['rateLimits']['credits']['hasCredits'] = True
                elif mutation in ('nonzero', 'overflow'):
                    usage['rateLimits']['credits']['balance'] = '1' if mutation == 'nonzero' else 'Infinity'
                elif mutation == 'quota':
                    usage['rateLimits']['primary']['usedPercent'] = 100
                else:
                    usage['rateLimits']['spendControlReached'] = None
                with self.assertRaises(subject.SubjectStop):
                    subject.verify_included_usage(usage)

    def test_subject_boundary_verifies_history_controls_and_rejects_added_instructions(self):
        expected = {
            'model': MOCK_LABEL, 'modelProvider': 'openai', 'reasoningEffort': 'medium',
            'serviceTier': 'default', 'instructionSources': [], 'runtimeWorkspaceRoots': [],
            'sandbox': {'type': 'readOnly', 'networkAccess': False},
            'activePermissionProfile': {'id': 'realgame_subject', 'extends': None},
        }
        provider = subject.SubjectProvider.__new__(subject.SubjectProvider)
        provider.c = {'reasoning_effort': 'medium', 'client_version': '0.154.0'}
        provider.expected_skills = []
        provider.wrapper = MOCK_LABEL
        provider.boundary = {'fixture_label': MOCK_LABEL, 'thread_start_response': expected}

        def make_client(extra_instructions=False):
            thread = dict(expected, fixture_label=MOCK_LABEL, thread={
                'id': MOCK_LABEL, 'cliVersion': '0.154.0', 'ephemeral': True,
                'environments': [], 'parentThreadId': None, 'forkedFromId': None})
            if extra_instructions:
                thread['instructionSources'] = [MOCK_LABEL + '-coordinator-AGENTS.md']
            responses = {
                'skills/list': {'fixture_label': MOCK_LABEL, 'data': [{'errors': [], 'skills': []}]},
                'thread/start': thread,
                'mcpServerStatus/list': {'fixture_label': MOCK_LABEL, 'data': [], 'nextCursor': None},
                'account/rateLimits/read': mock_included_usage(),
            }
            client = mock.Mock(name=MOCK_LABEL)
            client.folder.name = '/MOCK-NOT-LLM-empty'
            client.request.side_effect = lambda method, params=None: copy.deepcopy(responses[method])
            return client

        client = make_client()
        messages = [{'role': 'system', 'content': MOCK_LABEL}, {'role': 'user', 'content': MOCK_LABEL}]
        result = provider.verify_boundary(client, MOCK_LABEL, messages)
        self.assertFalse(result['complete_native_tool_inventory_available'])
        start = next(call.args[1] for call in client.request.call_args_list if call.args[0] == 'thread/start')
        self.assertEqual(start['baseInstructions'], messages[0]['content'])
        self.assertEqual(start['developerInstructions'], MOCK_LABEL)
        self.assertEqual(start['environments'], [])
        self.assertEqual(start['dynamicTools'], [])
        self.assertFalse(start['allowProviderModelFallback'])
        self.assertFalse(start['experimentalRawEvents'])
        with self.assertRaises(subject.SubjectStop) as raised:
            provider.verify_boundary(make_client(True), MOCK_LABEL, messages)
        self.assertEqual(raised.exception.category, 'thread_boundary_or_settings_drift')


class SubscriptionFinalGuardsTests(unittest.TestCase):
    def test_wall_clock_rollback_cannot_extend_live_pilot_deadline(self):
        with tempfile.TemporaryDirectory(prefix='MOCK-NOT-LLM-') as folder, \
                mock.patch('codex_budget.time.time', return_value=1000.0) as wall, \
                mock.patch('codex_budget.time.monotonic', return_value=10.0) as mono:
            budget = GlobalPilotBudget(Path(folder)/'global.jsonl', MOCK_LABEL, seconds=10)
            try:
                budget.reserve(MOCK_LABEL, 0)
                wall.return_value = 900.0
                mono.return_value = 20.0
                self.assertEqual(budget.remaining_seconds(), 0)
                with self.assertRaises(subscription.AccessBlocked):
                    budget.reserve(MOCK_LABEL, 1)
            finally:
                budget.close()

    def test_buffered_frames_and_notifications_do_not_skip_deadline(self):
        client = mock_subject_client([])
        client.deadline = 0.
        client.buffer = b'{"fixture_label":"MOCK-NOT-LLM","id":1}\n'
        with self.assertRaises(subject.SubjectStop):
            client._read(0.)
        with self.assertRaises(subject.SubjectStop):
            client.notification(mock_event('thread/started'))

    def test_analysis_rejects_orphan_and_duplicate_submitted_turns(self):
        frozen = mock_frozen_design()
        request = {'fixture_label': MOCK_LABEL, 'run_id': MOCK_LABEL, 'index': 0,
                   'model_requested': MOCK_LABEL, 'transport': 'official_codex_app_server',
                   'turn_submitted': True, 'status': 'success', 'visible_text': '{}'}
        with self.assertRaises(ValueError):
            analyze_subject_records([], frozen, [request])
        row = dict(frozen['planned'][0], run_id=MOCK_LABEL, backend='codex_subscription',
                   attempted=True, status='invalid_output', choice=None,
                   probability_pre_reveal=None, probability_final=None)
        with self.assertRaises(ValueError):
            analyze_subject_records([row], frozen, [request, request])


if __name__ == '__main__':
    unittest.main()
