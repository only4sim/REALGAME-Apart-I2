#!/usr/bin/env python3
"""Check report pagination, source constraints, and numerical release counts.

This is a text/structure gate, not a substitute for inspection of every page.
"""
from __future__ import annotations
import argparse,hashlib,json,re,zipfile,unicodedata
from pathlib import Path
import fitz
from docx import Document
ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pdf',type=Path,default=ROOT/'build/paper/manuscript.pdf');ap.add_argument('--out',type=Path,default=ROOT/'build/paper/report_checks.json')
    ap.add_argument('--docx',type=Path,default=ROOT/'build/paper/manuscript.docx')
    ap.add_argument('--blocks',type=Path,default=ROOT/'paper/submission_blocks.json')
    a=ap.parse_args()
    blocks=json.loads(a.blocks.read_text());assert len(blocks['main_pages'])==8
    assert len(blocks['abstract'].split())==150
    assert [b['text'] for page in blocks['main_pages'] for b in page if b['type']=='abstract']==[blocks['abstract']]
    with fitz.open(a.pdf) as d:
        texts=[p.get_text() for p in d]
        refs=[i+1 for i,t in enumerate(texts) if 'References' in [s.strip() for s in t.splitlines()]]
        assert refs==[9],f'References must start on page 9, found {refs}'
        assert all(len(t.split())>150 for t in texts[:8]),'Sparse or padding main-text page'
        alltext='\n'.join(texts)
        for title in ('1. Introduction','2. Related Work','3. Methods','4. Results','5. Discussion and Limitations','6. Conclusion','Code and Data','Limitations and Dual-Use Considerations','LLM Usage Statement'):assert title in alltext,title
        assert not any(c in alltext for c in ('¿','$$','\ufffd','\x00')),'Possible equation or glyph conversion failure'
        sizes=[list(p.rect) for p in d]
        assert all(rect==[0.0,0.0,612.0,792.0] for rect in sizes),'All pages must use Letter size'
        fonts=sorted({f[3] for page in d for f in page.get_fonts()})
        assert any('OldStandard' in f.replace(' ','').replace('-','') for f in fonts),'Old Standard font was not rendered'
        first=unicodedata.normalize('NFKC',texts[0])
        # A figure now follows the abstract before the Introduction.
        abstract_tail=first.split('Abstract',1)[1]
        rendered_abstract=re.split(r'Figure 1\.|1\. Introduction',abstract_tail,maxsplit=1)[0]
        assert ' '.join(rendered_abstract.split())==' '.join(unicodedata.normalize('NFKC',blocks['abstract']).split()),'Rendered abstract differs from source'
    doc=Document(a.docx);template=Document(ROOT/'template/apart_original.docx')
    for field in ('page_width','page_height','top_margin','bottom_margin','left_margin','right_margin'):
        assert getattr(doc.sections[0],field)==getattr(template.sections[0],field),field
    assert doc.styles['Normal'].font.name=='Old Standard TT'
    assert doc.styles['Normal'].font.size.pt>=11
    source_blocks=[b for page in blocks['main_pages']+blocks['appendix_pages'] for b in page]
    assert len(doc.tables)==sum(b['type']=='table' for b in source_blocks)==6
    assert len(doc.inline_shapes)==sum(b['type']=='figure' for b in source_blocks)==3
    native_equations=len(doc._element.xpath('.//m:oMath'))
    assert native_equations>=6,'Expected native editable equations'
    ext=[b for p in blocks['appendix_pages'] for b in p if b['type']=='p' and re.match(r'^\*\*[1-4][.)]',b.get('text',''))]
    # Alternate plain numbering is accepted, but exactly four extension items are required.
    if not ext:ext=[b for p in blocks['appendix_pages'] for b in p if b['type']=='p' and re.match(r'^[1-4][.)]',b.get('text',''))]
    assert len(ext)==4,f'Expected four numbered extensions, found {len(ext)}'
    totals=json.loads((ROOT/'results/totals.json').read_text())
    for k,v in {'scripted_episodes':960,'population_coverage_cases':375,'coverage_exact_checks':600,'sampling_replicates':3000,'sampling_draws':384000,'dynamic_program_cases':6,'llm_runs':0}.items():
        # These immutable totals describe only the historical scripted cohort.
        assert totals[k]==v,(k,totals[k],v)
    author_gate=[] if blocks.get('author_metadata_confirmed') is True else ['author identity and affiliation']
    report={'status':'passed','main_pages':8,'references_start_page':9,'total_pdf_pages':len(texts),'abstract_words':150,'main_page_word_counts':[len(t.split()) for t in texts[:8]],'page_rectangles':sizes,'source_docx':str(a.docx),'template_geometry_preserved':True,'numbered_month_extensions':4,'visual_inspection_required':True,'human_submission_gates':author_gate+['artifact location','theorem and source review','authorship approval','venue eligibility'],'pdf_sha256':hashlib.sha256(a.pdf.read_bytes()).hexdigest(),
            'docx_sha256':hashlib.sha256(a.docx.read_bytes()).hexdigest(),
            'blocks_sha256':hashlib.sha256(a.blocks.read_bytes()).hexdigest(),
            'markdown_sha256':hashlib.sha256(a.docx.with_suffix('.md').read_bytes()).hexdigest(),
            'template_sha256':hashlib.sha256((ROOT/'template/apart_original.docx').read_bytes()).hexdigest(),
            'native_editable_equations':native_equations,'rendered_fonts':fonts,
            'body_font_points':doc.styles['Normal'].font.size.pt,
            'rendered_abstract_matches_source':True}
    a.out.parent.mkdir(exist_ok=True,parents=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
