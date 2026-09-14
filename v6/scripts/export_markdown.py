#!/usr/bin/env python3
"""Export manuscript blocks without document-build dependencies.

This exports source text only and makes no claim about rendered pagination.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def export(blocks):
    lines = ['# '+blocks['title'], '']
    for page in blocks['main_pages']:
        for block in page:
            if block['type'] in ('author', 'event'):
                lines.extend([block['text'], ''])
    def emit(block):
        kind = block['type']
        text = block.get('text', '')
        if kind in ('title', 'author', 'event'):
            return
        if kind == 'abstract':
            lines.extend(['## Abstract', '', text, ''])
        elif kind in ('p', 'h', 'sh'):
            lines.extend([('## ' if kind == 'h' else '### ' if kind == 'sh' else '')+text, ''])
        elif kind == 'eq':
            lines.extend(['$$', block['latex'], '$$', ''])
        elif kind == 'figure':
            lines.extend(['!['+block['caption']+']('+block['file']+')', ''])
        elif kind == 'table':
            if block.get('caption'):
                lines.extend([block['caption'], ''])
            lines.extend(['| '+' | '.join(block['headers'])+' |',
                          '| '+' | '.join(['---']*len(block['headers']))+' |'])
            lines.extend('| '+' | '.join(map(str, row))+' |' for row in block['rows'])
            lines.append('')
        else:
            raise ValueError(kind)
    for i, page in enumerate(blocks['main_pages']):
        if i:
            lines.extend(['<!-- MAIN PAGE BREAK -->', ''])
        for block in page:
            emit(block)
    lines.extend(['## References', ''])
    for reference in blocks['references']:
        lines.extend([reference, ''])
    for page in blocks['appendix_pages']:
        for block in page:
            emit(block)
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--blocks', type=Path, default=ROOT/'paper/submission_blocks.json')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    blocks = json.loads(args.blocks.read_text())
    assert len(blocks['abstract'].split()) == 150
    assert len(blocks['main_pages']) == 8
    args.out.write_text(export(blocks))
    print(args.out)


if __name__ == '__main__':
    main()
