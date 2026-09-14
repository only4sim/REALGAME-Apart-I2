#!/usr/bin/env python3
"""Verify current source and immutable evidence without any model calls."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from export_markdown import export
from history import verify_history

ROOT = Path(__file__).resolve().parents[1]


def verify_manifest(root=ROOT):
    records = json.loads((root / 'verification/evidence_manifest.json').read_text())['files']
    for record in records:
        path = root / record['path']
        if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink():
            raise ValueError('Unsafe evidence path: ' + record['path'])
        data = path.read_bytes()
        if len(data) != record['bytes'] or hashlib.sha256(data).hexdigest() != record['sha256']:
            raise ValueError('Evidence changed: ' + record['path'])
    return len(records)


def verify():
    count = verify_manifest()
    history = verify_history()
    cohort = ROOT / 'results/codex_subscription_pilot_v8_01'
    frozen = json.loads((cohort / 'frozen_plan.json').read_text())
    for name, digest in frozen['source_manifest'].items():
        path = cohort / 'source_snapshot' / name
        if not path.resolve().is_relative_to((cohort / 'source_snapshot').resolve()):
            raise ValueError('Unsafe frozen source path')
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Frozen source changed: ' + name)
    blocks_path = ROOT / 'paper/submission_blocks.json'
    blocks = json.loads(blocks_path.read_text())
    abstracts = [b['text'] for page in blocks['main_pages'] for b in page if b['type'] == 'abstract']
    if abstracts != [blocks['abstract']] or len(blocks['abstract'].split()) != 150:
        raise ValueError('The abstract must be identical in both fields and exactly 150 words')
    if len(blocks['main_pages']) != 8:
        raise ValueError('Expected eight main source groups; this is not pagination verification')
    extensions = [b for page in blocks['appendix_pages'] for b in page
                  if b['type'] == 'p' and re.match(r'^\*\*[1-4][.)]', b.get('text', ''))]
    if len(extensions) != 4:
        raise ValueError('Exactly four one-month extensions must remain')
    text = '\n'.join(b.get('text', '') for page in blocks['appendix_pages'] for b in page)
    for title in ('Limitations and Dual-Use Considerations', 'LLM Usage Statement'):
        if title not in text:
            raise ValueError('Missing required section: ' + title)
    markdown = ROOT / 'paper/manuscript.md'
    if markdown.read_text() != export(blocks, markdown.parent):
        raise ValueError('Manuscript Markdown is stale; run make paper-source')
    return {'status': 'source_and_saved_evidence_verified', 'evidence_files_verified': count,
            'history': history, 'frozen_source_files_verified': len(frozen['source_manifest']),
            'abstract_words': 150, 'main_source_groups': 8, 'month_extensions': 4,
            'author_metadata_confirmed': blocks.get('author_metadata_confirmed', False),
            'author_name': blocks.get('author_name'),
            'author_affiliation': blocks.get('author_affiliation'),
            'paper_source_sha256': hashlib.sha256(blocks_path.read_bytes()).hexdigest(),
            'rendering_checked_by_this_command': False,
            'supplied_paper_pdf_present': (ROOT / 'paper/Certifying Behavior Without Hiding the Sandbox v1.pdf').is_file(),
            'deck_content_present': any((ROOT / 'slides' / name).is_file() for name in ('REALGAME_deck.pdf', 'deck.md', 'deck.pdf', 'deck.html', 'deck.pptx')),
            'network_calls': 0, 'new_model_episodes': 0,
            'note': 'This source check makes no rendered pagination or publication claim. Frozen pilot source is verified independently of current maintenance code.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = verify()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open('x') as stream:
            stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
