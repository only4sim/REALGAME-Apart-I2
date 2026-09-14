#!/usr/bin/env python3
"""Package current publication sources; require separate checks for rendered artifacts."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import zipfile
from verify_repository import verify

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ('archive', 'access', 'certificates', 'configs', 'docs', 'figures',
               'paper', 'protocol', 'results', 'scripts', 'slides', 'src', 'template', 'tests', 'verification')
ROOT_FILES = ('.gitignore', 'AGENTS.md', 'README.md', 'Makefile', 'requirements.txt', 'requirements-paper.txt')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def release_gates(root=ROOT):
    missing = []
    paper = root / 'build/paper'
    required = [paper / name for name in ('manuscript.pdf', 'manuscript.docx', 'report_checks.json', 'visual_review.json')]
    if not all(path.is_file() for path in required):
        missing.append('Current paper DOCX/PDF, report_checks.json and visual_review.json under build/paper/')
    else:
        checks = json.loads((paper / 'report_checks.json').read_text())
        visual = json.loads((paper / 'visual_review.json').read_text())
        expected = {'pdf_sha256': digest(paper / 'manuscript.pdf'),
                    'docx_sha256': digest(paper / 'manuscript.docx'),
                    'blocks_sha256': digest(root / 'paper/submission_blocks.json')}
        if (checks.get('status') != 'passed' or checks.get('main_pages') != 8
                or checks.get('references_start_page') != 9 or checks.get('abstract_words') != 150
                or any(checks.get(key) != value for key, value in expected.items())):
            missing.append('Paper verification matching the exact current source and rendered files')
        pages = visual.get('pages', [])
        total = checks.get('total_pdf_pages')
        if (type(total) is not int or visual.get('pdf_sha256') != expected['pdf_sha256']
                or [row.get('page') for row in pages] != list(range(1, (total or 0) + 1))
                or any(row.get('visual_inspected') is not True or not row.get('notes') for row in pages)):
            missing.append('Recorded visual inspection of every current rendered page')
        else:
            for row in pages:
                image = paper / 'pages' / ('page-' + str(row['page']) + '.png')
                if not image.is_file() or row.get('image_sha256') != digest(image):
                    missing.append('Visual review must hash every inspected current page image')
                    break
    if not any((root / 'slides' / name).is_file() for name in ('REALGAME_deck.pdf', 'deck.pdf', 'deck.html', 'deck.pptx')):
        missing.append('Presentation distribution file under slides/ (REALGAME_deck.pdf, deck.pdf, deck.html or deck.pptx)')
    return missing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-only', action='store_true', help='Package repository sources and supplied PDFs without claiming a verified manuscript build')
    parser.add_argument('--zip', type=Path, help='Fresh destination ZIP; default is timestamped under build/')
    args = parser.parse_args()
    source_checks = verify()
    if not args.source_only:
        missing = release_gates()
        if missing:
            raise SystemExit('Publication artifact is incomplete:\n- ' + '\n- '.join(missing)
                             + '\nUse make package-source for the explicitly source-only artifact.')
    files = [ROOT / name for name in ROOT_FILES]
    for directory in DIRECTORIES:
        for path in (ROOT / directory).rglob('*'):
            if not path.is_file() or '__pycache__' in path.parts or path.suffix in ('.pyc', '.lock', '.tmp'):
                continue
            if path.is_symlink() or any(part.startswith('.') for part in path.relative_to(ROOT).parts):
                raise ValueError('Unexpected linked or hidden package input: ' + str(path))
            if path.suffix.lower() in ('.pem', '.key', '.ttf', '.otf', '.woff', '.woff2', '.odttf'):
                raise ValueError('Credential or standalone-font files cannot be packaged')
            files.append(path)
    if not args.source_only:
        files += [path for path in (ROOT / 'build/paper').rglob('*') if path.is_file()]
    files = sorted(set(files))
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    kind = 'source-only' if args.source_only else 'rendered-artifacts'
    target = args.zip or ROOT / 'build' / ('realgame-v8-' + kind + '-' + stamp + '.zip')
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.resolve().is_relative_to(ROOT / 'archive') or target.resolve().is_relative_to(ROOT / 'results'):
        raise SystemExit('Use a fresh ZIP destination outside immutable evidence directories')
    manifest = {'algorithm': 'sha256', 'package_kind': kind,
                'publication_or_submission_performed': False,
                'source_checks': source_checks,
                'files': [{'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size, 'sha256': digest(p)} for p in files]}
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT))
        archive.writestr('MANIFEST.json', json.dumps(manifest, indent=2) + '\n')
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP CRC verification failed')
        if set(archive.namelist()) != {r['path'] for r in manifest['files']} | {'MANIFEST.json'}:
            raise ValueError('ZIP membership differs from manifest')
        for row in manifest['files']:
            data = archive.read(row['path'])
            if hashlib.sha256(data).hexdigest() != row['sha256'] or len(data) != row['bytes']:
                raise ValueError('ZIP content mismatch: ' + row['path'])
    result = {'status': 'integrity_verified', 'package_kind': kind, 'archive': str(target),
              'sha256': digest(target), 'manifested_files_verified': len(files),
              'note': 'Package integrity is separate from scientific review, authorship, licensing and permission to publish.'}
    target.with_suffix('.checks.json').write_text(json.dumps(result, indent=2) + '\n')
    target.with_suffix('.sha256').write_text(result['sha256'] + '  ' + target.name + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
