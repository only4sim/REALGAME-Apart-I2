#!/usr/bin/env python3
"""Package an explicit release allowlist and verify every archived byte."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ('configs', 'figures', 'legacy_v5', 'paper', 'protocol', 'provenance',
               'results', 'scripts', 'src', 'template', 'tests', 'verification')
ROOT_FILES = ('AGENTS.md', 'START_HERE.md', 'CODEX_PROMPT.md', 'README.md', 'BLOCKERS.md',
              'EXECUTION_REPORT.md', 'DEVIATIONS.md', 'claim_ledger.json', 'requirements.txt',
              'submission_report.pdf', 'submission_report.docx', 'submission_report.md', 'submission_revision.md',
              'NEXT_CODEX_PROMPT.md', 'SOURCE_AUDIT.md', 'REVIEW_AND_NEXT_STEPS.md')
SIDECARS = {'verification/release_archive_check.json', 'verification/release_sha256.txt'}
FONT_EXTENSIONS = {'.ttf', '.otf', '.woff', '.woff2', '.pfb', '.pfa', '.odttf'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--zip', type=Path, default=ROOT / 'REALGAME_Apart_release_2026-09-14.zip')
    parser.add_argument('--working', action='store_true', help='Package an explicitly blocked working state; never label it final.')
    args = parser.parse_args()
    final = json.loads((ROOT / 'verification/final_checks.json').read_text())
    if args.working:
        assert 'working' in args.zip.name.lower(), 'Blocked artifacts require a working ZIP filename'
    else:
        assert final['status'] == 'passed' and final['current_execution_verified'] is True
        assert final['main_pages'] == 8 and final['abstract_words'] == 150
        assert final['visual_review']['all_pages_inspected'] is True
    files = [ROOT / name for name in ROOT_FILES]
    for name in DIRECTORIES:
        for path in (ROOT / name).rglob('*'):
            if not path.is_file() or path.is_symlink():
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in SIDECARS or '__pycache__' in path.parts or path.suffix in ('.pyc', '.tmp'):
                continue
            assert not any(part.startswith('.') for part in path.relative_to(ROOT).parts), rel
            assert path.suffix.lower() not in FONT_EXTENSIONS, 'Standalone font file prohibited: ' + rel
            assert path.suffix.lower() not in ('.pem', '.key'), 'Credential file prohibited: ' + rel
            files.append(path)
    files = sorted(set(files))
    for path in files:
        assert path.is_file(), str(path)
    manifest = {'algorithm': 'sha256', 'release_status': final['status'],
                'note': 'Covers every ZIP member except MANIFEST.json. The archive and its post-build verification/checksum sidecars are excluded to avoid circular hashes. Standalone font files, caches, environment files, and build dependencies are excluded. Fonts embedded by PDF rendering are part of the document.',
                'files': [{'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size,
                           'sha256': sha(p.read_bytes())} for p in files]}
    manifest_path = ROOT / 'MANIFEST.json'
    manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
    members = files + [manifest_path]
    with zipfile.ZipFile(args.zip, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in members:
            archive.write(path, path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(args.zip) as archive:
        assert archive.testzip() is None
        expected = {p.relative_to(ROOT).as_posix() for p in members}
        assert set(archive.namelist()) == expected
        assert len(archive.namelist()) == len(expected)
        for row in manifest['files']:
            data = archive.read(row['path'])
            assert len(data) == row['bytes'] and sha(data) == row['sha256'], row['path']
        assert archive.read('MANIFEST.json') == manifest_path.read_bytes()
    result = {'status': 'passed', 'release_status': final['status'], 'archive': args.zip.name, 'sha256': sha(args.zip.read_bytes()),
              'archive_bytes': args.zip.stat().st_size, 'members': len(members),
              'manifested_files_verified': len(files), 'crc_check_passed': True,
              'all_member_hashes_match': True, 'standalone_fonts_bundled': False,
              'build_dependencies_bundled': False,
              'note': 'This sidecar is produced after the ZIP and is intentionally outside its own manifest.'}
    (ROOT / 'verification/release_archive_check.json').write_text(json.dumps(result, indent=2)+'\n')
    (ROOT / 'verification/release_sha256.txt').write_text(result['sha256']+'  '+args.zip.name+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
