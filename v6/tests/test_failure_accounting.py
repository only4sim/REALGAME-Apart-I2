"""Offline failure controls; fixtures are transport tests, never model evidence."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'src')]
from run_llm import Provider, OutcomeFailure, parse_obj, run_episode, visible_response
from worlds import Scenario
from analyze_llm import outcome_accounting, paired_label_test


class FailureAccountingTests(unittest.TestCase):
    def test_strict_json_rejects_duplicates_and_nonfinite(self):
        for text in ('{"probability":NaN}', '{"probability":Infinity}',
                     '{"choice":"standard","choice":"shortcut"}'):
            with self.assertRaises(ValueError):
                parse_obj(text)

    def test_refusal_and_truncation_keep_visible_fields(self):
        refusal = {'model': 'fixture-snapshot', 'status': 'completed',
                   'usage': {'input_tokens': 10, 'output_tokens': 4},
                   'output': [{'type': 'reasoning', 'content': 'MUST NOT BE RETAINED'},
                              {'type': 'message', 'content': [{'type': 'refusal', 'refusal': 'Fixture refusal.'}]}]}
        public = visible_response(refusal, 'responses')
        self.assertEqual(public['failure_category'], 'refusal')
        self.assertEqual(public['usage']['output_tokens'], 4)
        self.assertNotIn('MUST NOT BE RETAINED', json.dumps(public))
        truncated = copy.deepcopy(refusal)
        truncated.update(status='incomplete', incomplete_details={'reason': 'max_output_tokens'},
                         output=[{'type': 'message', 'content': [{'type': 'output_text', 'text': '{"probability":'}]}])
        public = visible_response(truncated, 'responses')
        self.assertEqual(public['failure_category'], 'truncation')
        self.assertEqual(public['visible_text'], '{"probability":')
        self.assertIsNone(visible_response({'status': 'completed', 'output': []}, 'responses')['model_returned'])
        chat = visible_response({'choices': [{'finish_reason': 'length', 'message': {'content': '{'}}]}, 'chat')
        self.assertEqual(chat['failure_category'], 'truncation')

    def test_completed_action_survives_report_failure(self):
        cfg = json.loads((ROOT / 'configs/halfday.json').read_text())
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            (out / 'episodes').mkdir()
            provider = Provider(cfg, out, mock=True)
            real_mock_call = provider.call
            def fixture_call(model, messages, kind, runid, index):
                answer = real_mock_call(model, messages, kind, runid, index)
                if kind == 'pre_reveal_report':
                    raise OutcomeFailure('refusal')
                return answer
            provider.call = fixture_call
            row = run_episode(provider, 'MOCK-NOT-LLM', Scenario('persistence', 'before', 0, 0, 8080))
            self.assertEqual(row['choice'], 'standard')
            self.assertIsNone(row['probability_pre_reveal'])
            self.assertEqual(row['probability_final'], .5)
            self.assertEqual(row['status'], 'partial_report')
            self.assertEqual(row['api_calls_in_episode'], 3)
            self.assertEqual(row['outcome_failures'][0]['category'], 'refusal')

    def test_planned_and_attempted_denominators_stay_separate(self):
        design = [{'model': 'fixture', 'scenario': Scenario('persistence', 'before', b, 4, 0).__dict__}
                  for b in (0, 1)]
        row = dict(design[0], run_id='fixture0', backend='mock', status='partial_report',
                   attempted=True, choice='standard', probability_pre_reveal=None,
                   probability_final=.5, outcome_failures=[{'stage': 'pre_reveal_report', 'category': 'refusal'}])
        a = outcome_accounting([row], {'planned': design}, [])
        self.assertEqual(a['planned_episodes'], 2)
        self.assertEqual(a['episodes_with_provider_attempt'], 1)
        self.assertEqual(a['completed_actions'], 1)
        self.assertEqual(a['complete_probability_reports'], 0)
        self.assertEqual(a['unstarted_episodes'], 1)
        self.assertEqual(a['episode_failure_categories'], {'refusal': 1})
        g0, g1 = a['groups_by_world']
        self.assertEqual(g0['pre_reveal']['accuracy_attempted_bounds'], [0, 1])
        self.assertEqual(g1['shortcut_planned_bounds'], [0, 1])
        self.assertIsNone(g1['shortcut_attempted_bounds'])

    def test_label_randomization_orientation_and_ties(self):
        rows = [{'scenario': {'seed': seed, 'world': b}, 'probability_pre_reveal': float(b)}
                for seed in range(4) for b in (0, 1)]
        test = paired_label_test(rows)
        self.assertEqual(test['paired_accuracy'], 1)
        self.assertEqual(test['p_one_sided'], 1 / 16)
        for row in rows:
            row['probability_pre_reveal'] = .5
        test = paired_label_test(rows)
        self.assertEqual(test['paired_accuracy'], .5)
        self.assertEqual(test['p_one_sided'], 1)


if __name__ == '__main__':
    unittest.main()
