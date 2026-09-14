#!/usr/bin/env python3
"""Check report pagination, source constraints, and numerical release counts.

This is a text/structure gate, not a substitute for inspection of every page.
"""
from __future__ import annotations
import argparse,hashlib,json,re,zipfile
from pathlib import Path
import fitz
from docx import Document
ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pdf',type=Path,default=ROOT/'submission_report.pdf');ap.add_argument('--out',type=Path,default=ROOT/'verification/report_checks.json');a=ap.parse_args()
    blocks=json.loads((ROOT/'paper/submission_blocks.json').read_text());assert len(blocks['main_pages'])==8
    assert len(blocks['abstract'].split())==150
    with fitz.open(a.pdf) as d:
        texts=[p.get_text() for p in d]
        refs=[i+1 for i,t in enumerate(texts) if 'References' in [s.strip() for s in t.splitlines()]]
        assert refs==[9],f'References must start on page 9, found {refs}'
        assert all(len(t.split())>150 for t in texts[:8]),'Sparse or padding main-text page'
        alltext='\n'.join(texts)
        for title in ('1. Introduction','2. Related Work','3. Methods','4. Results','5. Discussion and Limitations','6. Conclusion','Code and Data','Limitations and Dual-Use Considerations','LLM Usage Statement'):assert title in alltext,title
        assert '¿' not in alltext and '$$' not in alltext,'Possible equation conversion failure'
        sizes=[list(p.rect) for p in d]
    doc=Document(ROOT/'submission_report.docx');template=Document(ROOT/'template/apart_original.docx')
    for field in ('page_width','page_height','top_margin','bottom_margin','left_margin','right_margin'):
        assert getattr(doc.sections[0],field)==getattr(template.sections[0],field),field
    ext=[b for p in blocks['appendix_pages'] for b in p if b['type']=='p' and re.match(r'^\*\*[1-4][.)]',b.get('text',''))]
    # Alternate plain numbering is accepted, but exactly four extension items are required.
    if not ext:ext=[b for p in blocks['appendix_pages'] for b in p if b['type']=='p' and re.match(r'^[1-4][.)]',b.get('text',''))]
    assert len(ext)==4,f'Expected four numbered extensions, found {len(ext)}'
    totals=json.loads((ROOT/'results/totals.json').read_text())
    for k,v in {'scripted_episodes':960,'population_coverage_cases':375,'coverage_exact_checks':600,'sampling_replicates':3000,'sampling_draws':384000,'dynamic_program_cases':6,'llm_runs':0}.items():
        # Freeze-file audit for the current shipped report; after real runs, update this explicit ledger check.
        assert totals[k]==v,(k,totals[k],v)
    report={'status':'passed','main_pages':8,'references_start_page':9,'total_pdf_pages':len(texts),'abstract_words':150,'main_page_word_counts':[len(t.split()) for t in texts[:8]],'page_rectangles':sizes,'source_docx':'submission_report.docx','template_geometry_preserved':True,'numbered_month_extensions':4,'visual_inspection_required':True,'human_submission_gates':['affiliation','artifact location','theorem and source review','authorship approval','venue eligibility'],'pdf_sha256':hashlib.sha256(a.pdf.read_bytes()).hexdigest()}
    a.out.parent.mkdir(exist_ok=True,parents=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
