"""Offline maintenance checks; all temporary fixtures are MOCK-NOT-LLM."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from history import read_historical, verify_history
from package_release import release_gates
from verify_repository import verify_manifest


class RepositoryWorkflowTests(unittest.TestCase):
    def test_evidence_edit_is_detected(self):
        with tempfile.TemporaryDirectory(prefix='MOCK-NOT-LLM-') as folder:
            root = Path(folder)
            (root / 'verification').mkdir()
            data = b'MOCK-NOT-LLM original evidence'
            (root / 'record.txt').write_bytes(data)
            (root / 'verification/evidence_manifest.json').write_text(json.dumps({'files': [
                {'path': 'record.txt', 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}]}))
            self.assertEqual(verify_manifest(root), 1)
            (root / 'record.txt').write_bytes(b'MOCK-NOT-LLM changed evidence')
            with self.assertRaisesRegex(ValueError, 'Evidence changed'):
                verify_manifest(root)

    def test_history_restores_exact_bytes_and_rejects_divergent_index(self):
        with tempfile.TemporaryDirectory(prefix='MOCK-NOT-LLM-') as folder:
            root = Path(folder)
            (root / 'archive').mkdir()
            data = b'MOCK-NOT-LLM historical record'
            digest = hashlib.sha256(data).hexdigest()
            index = json.dumps({'baseline_commit': 'MOCK-NOT-LLM', 'files': {
                'old/record.txt': {'sha256': digest, 'bytes': len(data)}}}).encode()
            (root / 'archive/INDEX.json').write_bytes(index)
            with zipfile.ZipFile(root / 'archive/history.zip', 'w') as archive:
                archive.writestr('INDEX.json', index)
                archive.writestr('objects/' + digest, data)
            self.assertEqual(read_historical('old/record.txt', root), data)
            self.assertEqual(verify_history(root)['unique_objects_verified'], 1)
            (root / 'archive/INDEX.json').write_bytes(index + b' ')
            with self.assertRaisesRegex(ValueError, 'index'):
                verify_history(root)

    def test_complete_release_requires_current_rendering_and_deck(self):
        with tempfile.TemporaryDirectory(prefix='MOCK-NOT-LLM-') as folder:
            missing = release_gates(Path(folder))
            self.assertEqual(len(missing), 2)
            self.assertIn('paper', missing[0])
            self.assertIn('deck', missing[1])
            root = Path(folder)
            (root / 'slides').mkdir()
            (root / 'slides/REALGAME_deck.pdf').write_bytes(b'MOCK-NOT-LLM deck presence fixture')
            (root / 'paper').mkdir()
            (root / 'paper/Certifying Behavior Without Hiding the Sandbox v1.pdf').write_bytes(
                b'MOCK-NOT-LLM supplied paper presence fixture')
            remaining = release_gates(root)
            self.assertEqual(len(remaining), 1)
            self.assertIn('paper', remaining[0])


if __name__ == '__main__':
    unittest.main()
