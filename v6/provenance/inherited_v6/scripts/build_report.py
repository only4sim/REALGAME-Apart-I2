#!/usr/bin/env python3
"""Populate the supplied native Word template; equations remain editable OMML.

The original template's page size, margins, named styles, and serif design are
retained. Unused author placeholders are replaced with a single author block.
No font binaries are copied into the output or distribution.
"""
from __future__ import annotations
import argparse,copy,json,re,subprocess,tempfile,zipfile
from functools import lru_cache
from pathlib import Path
from lxml import etree
from docx import Document
from docx.shared import Pt,Inches,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parents[1]


def rich(p,text,size=None):
    for part in re.split(r'(\*\*.*?\*\*|\$[^$]+\$)',text):
        if not part:continue
        if part.startswith('$') and part.endswith('$'):
            for m in equation_xml(part[1:-1]):p._p.append(copy.deepcopy(m))
            continue
        bold=part.startswith('**') and part.endswith('**')
        r=p.add_run(part[2:-2] if bold else part);r.font.name='Old Standard TT'
        if bold:r.bold=True
        if size:r.font.size=Pt(size)
    return p


def no_split(row):
    e=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(e)


def border(p,top=None,bottom=None):
    b=OxmlElement('w:pBdr')
    for name,val in [('top',top),('bottom',bottom)]:
        if val:
            e=OxmlElement('w:'+name);e.set(qn('w:val'),'single');e.set(qn('w:sz'),str(val));e.set(qn('w:space'),'8');e.set(qn('w:color'),'000000');b.append(e)
    p._p.get_or_add_pPr().append(b)


@lru_cache(maxsize=256)
def equation_xml(latex):
    with tempfile.TemporaryDirectory() as td:
        a=Path(td)/'eq.md';o=Path(td)/'eq.docx';a.write_text('$$\n'+latex+'\n$$\n')
        subprocess.run(['pandoc',str(a),'-o',str(o)],check=True,capture_output=True)
        with zipfile.ZipFile(o) as z:root=etree.fromstring(z.read('word/document.xml'))
        ns={'m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
        found=root.findall('.//m:oMath',ns)
        if not found:raise RuntimeError('Equation conversion produced no editable math: '+latex)
        # LibreOffice can misrender a stretchy closing square bracket as a
        # parenthesis. Use literal editable math runs for square delimiters.
        for rootmath in found:
            for delim in list(rootmath.findall('.//m:d',ns)):
                pr=delim.find('m:dPr',ns)
                begin=pr.find('m:begChr',ns) if pr is not None else None
                end=pr.find('m:endChr',ns) if pr is not None else None
                attr='{'+ns['m']+'}val'
                if begin is not None and end is not None and begin.get(attr)=='[' and end.get(attr)==']':
                    parent=delim.getparent();at=parent.index(delim);items=[]
                    for char in ('[',):
                        rr=etree.Element('{'+ns['m']+'}r');tt=etree.SubElement(rr,'{'+ns['m']+'}t');tt.text=char;items.append(rr)
                    for expr in delim.findall('m:e',ns):items.extend(copy.deepcopy(ch) for ch in expr)
                    rr=etree.Element('{'+ns['m']+'}r');tt=etree.SubElement(rr,'{'+ns['m']+'}t');tt.text=']';items.append(rr)
                    parent.remove(delim)
                    for offset,item in enumerate(items):parent.insert(at+offset,item)
        return [copy.deepcopy(x) for x in found]


def build(blocks_path,out):
    x=json.loads(blocks_path.read_text());d=Document(ROOT/'template/apart_original.docx')
    body=d._element.body
    for e in list(body):
        if e.tag!=qn('w:sectPr'):body.remove(e)
    # The source template already specifies letter paper and one-inch margins.
    normal=d.styles['Normal'];normal.font.name='Old Standard TT';normal.font.size=Pt(11)
    normal.paragraph_format.line_spacing=1.15;normal.paragraph_format.space_after=Pt(5)
    normal.paragraph_format.space_before=Pt(0)
    for name,sz in [('Heading 2',14),('Heading 3',12)]:
        st=d.styles[name];st.font.name='Old Standard TT';st.font.size=Pt(sz);st.font.bold=True;st.font.color.rgb=RGBColor(0,0,0)
        st.paragraph_format.space_before=Pt(9);st.paragraph_format.space_after=Pt(5);st.paragraph_format.keep_with_next=True
    section=d.sections[0]
    for p in section.header.paragraphs:p.clear()
    for p in section.footer.paragraphs:p.clear()
    f=section.footer.paragraphs[0];f.alignment=WD_ALIGN_PARAGRAPH.CENTER
    fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');f._p.append(fld)
    d.core_properties.title=x['title'];d.core_properties.author='Li Quan'
    d.core_properties.subject='AI Incident Response Sprint: target-specific safe behavioral evidence'
    d.core_properties.comments='AI-assisted collaboration draft; human authorship and affiliation verification required.'
    md=['# '+x['title'],'']
    md+=['Li Quan','Affiliation to be confirmed','With Apart Research','AI Incident Response Sprint, September 2026','']
    equation_count=0
    def emit(b,break_before=False):
        nonlocal equation_count
        typ=b['type'];txt=b.get('text','')
        if typ in ('p','h','sh','title','author','event','abstract'):
            if typ=='h':p=d.add_paragraph(style='Heading 2')
            elif typ=='sh':p=d.add_paragraph(style='Heading 3')
            else:p=d.add_paragraph()
            p.paragraph_format.page_break_before=break_before
            if typ=='title':
                p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_before=Pt(8);p.paragraph_format.space_after=Pt(12)
                border(p,top=24,bottom=6);rich(p,txt,20);p.runs[0].bold=True
            elif typ in ('author','event'):
                p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.line_spacing=1.;p.paragraph_format.space_after=Pt(6)
                rich(p,txt,11 if typ=='author' else 10)
            elif typ=='abstract':
                p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(4);rich(p,'**Abstract**',13)
                p=d.add_paragraph();p.paragraph_format.line_spacing=1.12;p.paragraph_format.left_indent=Inches(.22);p.paragraph_format.right_indent=Inches(.22)
                p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY;rich(p,txt,10.5)
                md.extend(['## Abstract','',txt,''])
            else:
                if typ=='p':p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
                rich(p,txt)
                md.extend([('## ' if typ=='h' else '### ' if typ=='sh' else '')+txt,''])
            return
        if typ=='eq':
            p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before=Pt(4);p.paragraph_format.space_after=Pt(7)
            for m in equation_xml(b['latex']):p._p.append(copy.deepcopy(m))
            equation_count+=1;md.extend(['$$',b['latex'],'$$','']);return
        if typ=='table':
            if b.get('caption'):
                cp=d.add_paragraph();cp.paragraph_format.line_spacing=1.05;cp.paragraph_format.space_after=Pt(3);cp.paragraph_format.keep_with_next=True
                rich(cp,b['caption'],9.5);md.extend([b['caption'],''])
            t=d.add_table(rows=1,cols=len(b['headers']));t.autofit=False
            widths=b.get('widths') or [6.25/len(b['headers'])]*len(b['headers'])
            for j,w in enumerate(widths):t.columns[j].width=Inches(w)
            for j,lab in enumerate(b['headers']):t.rows[0].cells[j].text=lab
            for row in b['rows']:
                cells=t.add_row().cells
                for j,val in enumerate(row):cells[j].text=str(val)
            for i,row in enumerate(t.rows):
                no_split(row)
                for j,cell in enumerate(row.cells):
                    cell.width=Inches(widths[j])
                    tcpr=cell._tc.get_or_add_tcPr();bd=OxmlElement('w:tcBorders')
                    for nm in ('top','bottom'):
                        if i==0 or (i==len(t.rows)-1 and nm=='bottom'):
                            el=OxmlElement('w:'+nm);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'000000');bd.append(el)
                    tcpr.append(bd)
                    for p in cell.paragraphs:
                        p.paragraph_format.line_spacing=1.05;p.paragraph_format.space_after=Pt(3);p.paragraph_format.space_before=Pt(3)
                        for r in p.runs:r.font.name='Old Standard TT';r.font.size=Pt(9.5);r.bold=(i==0)
            sp=d.add_paragraph();sp.paragraph_format.space_after=Pt(2);sp.paragraph_format.line_spacing=Pt(1);sp.add_run().font.size=Pt(1)
            md.extend(['| '+' | '.join(b['headers'])+' |','| '+' | '.join(['---']*len(b['headers']))+' |'])
            md.extend('| '+' | '.join(row)+' |' for row in b['rows']);md.append('');return
        if typ=='figure':
            p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(2);p.paragraph_format.keep_with_next=True
            p.add_run().add_picture(str(ROOT/b['file']),width=Inches(6.1))
            cap=d.add_paragraph();cap.paragraph_format.line_spacing=1.05;cap.paragraph_format.space_after=Pt(6)
            rich(cap,b['caption'],9.5)
            md.extend(['!['+b['caption']+']('+b['file']+')','']);return
        raise ValueError(typ)
    for i,page in enumerate(x['main_pages']):
        if i:md.extend(['<!-- MAIN PAGE BREAK -->',''])
        for j,b in enumerate(page):emit(b,break_before=(i>0 and j==0))
    emit(H:={'type':'h','text':'References'},True)
    for text in x['references']:
        p=d.add_paragraph();p.paragraph_format.space_after=Pt(6);p.paragraph_format.line_spacing=1.08;rich(p,text,9.5);md.extend([text,''])
    for page in x['appendix_pages']:
        for j,b in enumerate(page):emit(b,break_before=j==0)
    out.parent.mkdir(exist_ok=True,parents=True);d.save(out)
    (ROOT/'submission_report.md').write_text('\n'.join(md))
    print(json.dumps({'docx':str(out),'abstract_words':len(x['abstract'].split()),'planned_main_pages':len(x['main_pages']),'editable_equations':equation_count},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--blocks',type=Path,default=ROOT/'paper/submission_blocks.json');p.add_argument('--out',type=Path,default=ROOT/'submission_report.docx');a=p.parse_args();build(a.blocks,a.out)
