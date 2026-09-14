"""Check the PDF-to-source reconciliation and both pilot tables without inference."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from extract_supplied_pdf import PDF

ROOT = Path(__file__).resolve().parents[2]
AUDIT = Path(__file__).resolve().parent


def normalized(text):
    return ' '.join(text.replace('**', '').split())


def verify():
    pdf_path = ROOT / 'paper/Certifying Behavior Without Hiding the Sandbox v1.pdf'
    pdf = PDF(pdf_path)
    source_path = ROOT / 'paper/submission_blocks.json'
    source = json.loads(source_path.read_text())
    mapping = json.loads((AUDIT / 'source_mapping.json').read_text())
    formulas = {int(k): v for k, v in json.loads((AUDIT / 'math_mapping.json').read_text()).items()}
    rendered_math = {latex: pdf.text(('ref', n, 0)) for n, latex in formulas.items()}
    tops = [r[1] for r in pdf.objects[71]['/K']]
    corrections = []
    verified = 0
    for record in mapping:
        group, i, j = record['source_location']
        block = source[group][i][j]
        n = record['pdf_object']
        actual_pdf = normalized(pdf.text(('ref', n, 0)))
        assert actual_pdf == normalized(record['pdf_text']), ('PDF mapping drift', n)
        if 'repository_correction' in record:
            assert block['text'] == record['repository_correction']['revised_text'], n
            corrections.append(n)
        elif block['type'] == 'eq':
            assert block['latex'] == formulas[n], n
        elif block['type'] == 'figure':
            caption_id = tops[tops.index(n) + 1]
            assert normalized(block['caption']) == normalized(pdf.text(('ref', caption_id, 0))), n
        elif block['type'] == 'table':
            flat = ' '.join(block['headers'] + [cell for row in block['rows'] for cell in row])
            assert normalized(flat) == actual_pdf, n
            caption_id = tops[tops.index(n) - 1]
            assert normalized(block['caption']) == normalized(pdf.text(('ref', caption_id, 0))), n
        else:
            text = re.sub(r'\$([^$]+)\$', lambda m: rendered_math[m[1]], block['text'])
            assert normalized(text) == actual_pdf, (n, text, actual_pdf)
        verified += 1
    assert verified == sum(len(page) for group in ['main_pages', 'appendix_pages'] for page in source[group])
    for i, reference in enumerate(source['references']):
        expected = pdf.text(('ref', 463+i, 0))
        if i == 12:
            expected = expected.replace('PILOT_RUN_REPORT.md', 'docs/PILOT_RUN_REPORT.md')
        assert normalized(reference) == normalized(expected), ('reference', i+1)
    assert source['abstract'] == normalized(pdf.text(('ref', 78, 0)))
    assert len(source['abstract'].split()) == 150
    assert source['author_name'] == 'Li Quan'
    assert source['author_metadata'] == source['author_name']
    assert source['author_affiliation'] == 'The Pioneer Centre for Artificial Intelligence, Denmark'
    assert source['author_metadata_confirmed'] is True
    assert normalized(source['author_name'] + ' ' + source['author_affiliation']) == normalized(pdf.text(('ref', 75, 0)))

    analysis_path = ROOT / 'results/codex_subscription_pilot_v8_01/analysis.json'
    analysis = json.loads(analysis_path.read_text())
    tables = [b for group in ['main_pages', 'appendix_pages'] for page in source[group] for b in page if b['type'] == 'table']
    aggregate = next(t for t in tables if t['caption'].startswith('Table 4.'))
    detailed = next(t for t in tables if t['caption'].startswith('Table C2.'))

    def close(actual, expected):
        assert math.isclose(float(actual), expected, abs_tol=1e-12), (actual, expected)

    for row, control in zip(aggregate['rows'], [False, True, None]):
        groups = [g for g in analysis['groups'] if control is None or g['control'] == control]
        n = sum(g['attempted'] for g in groups)
        assert int(row[1]) == n
        for score_col, brier_col, stage, denominator in [(2, 4, 'pre_reveal', 'pre_reveal_probability_n'), (3, 5, 'final', 'final_probability_n')]:
            observed = sum(g[denominator] for g in groups)
            score, score_n = map(float, row[score_col].split('/'))
            assert score_n == observed
            close(score, sum(g[stage + '_accuracy_ties_half'] * g[denominator] for g in groups))
            close(row[brier_col], sum(g[stage + '_brier'] * g[denominator] for g in groups) / observed)
    seen = set()
    for row in detailed['rows']:
        key = (row[0].lower(), row[1].lower(), int(row[2]), row[3] == 'Yes')
        assert key not in seen
        seen.add(key)
        group = next(g for g in analysis['groups'] if (g['family'], g['timing'], g['budget'], g['control']) == key)
        assert group['attempted'] == 2
        pre, final = row[4].split(' / ')
        for value, stage, denominator in [(pre, 'pre_reveal', 'pre_reveal_probability_n'), (final, 'final', 'final_probability_n')]:
            score, n = map(float, value.split('/'))
            assert n == group[denominator]
            close(score, group[stage + '_accuracy_ties_half'] * n)
        pre_brier, final_brier = row[5].split(' / ')
        close(pre_brier, group['pre_reveal_brier'])
        close(final_brier, group['final_brier'])
        assert int(row[6]) == group['probe_calls_total']
    assert len(seen) == len(analysis['groups']) == 10
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    return {
        'status': 'text_and_saved_table_values_verified',
        'pdf_sha256': digest(pdf_path), 'source_sha256': digest(source_path),
        'saved_analysis_sha256': digest(analysis_path),
        'source_blocks_checked': verified, 'references_checked': 13,
        'abstract_words': 150, 'author_block_matches_pdf': True,
        'mapped_math_objects': len(formulas), 'editable_display_equations': 6,
        'tables': len(tables), 'figures': 3,
        'pilot_aggregate_rows_checked_against_saved_analysis': 3,
        'pilot_cell_rows_checked_against_saved_analysis': 10,
        'documented_status_or_path_corrections': corrections,
        'reference_path_correction': 'Reference 13: docs/PILOT_RUN_REPORT.md',
        'visual_review_performed': False, 'new_document_rendering_performed': False,
        'new_model_calls': 0, 'new_cpu_sampling_runs': 0,
        'limitations': 'Tag/text comparison and an explicit reviewed LaTeX mapping do not verify glyph geometry, font identity, figure rendering, or pagination of a rebuilt document.'
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='Fresh verification record')
    args = parser.parse_args()
    result = verify()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
