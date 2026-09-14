"""Offline regression for syntactically valid numbers that overflow to infinity."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('finite_json_runner', ROOT / 'scripts/run_llm.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

class FiniteJSONTests(unittest.TestCase):
    def test_exponent_overflow_is_rejected_at_any_depth(self):
        for text in ('{"x":1e400}', '{"x":-1e400}', '{"nested":[1e400]}',
                     '{"a":{"b":-9.9e999}}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                runner.parse_obj(text)
        self.assertEqual(runner.parse_obj('{"x":1e2,"y":-0.25}'),
                         {'x':100.0, 'y':-0.25})
        self.assertEqual(runner.parse_obj('{"evidence":"1e400 is text"}'),
                         {'evidence':'1e400 is text'})

if __name__ == '__main__':
    unittest.main()
