#!/usr/bin/env python3
"""Portable DOCX-to-PDF conversion; optional page images for mandatory visual QA."""
from __future__ import annotations
import argparse,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--docx',type=Path,default=ROOT/'build/paper/manuscript.docx');ap.add_argument('--pdf',type=Path,default=ROOT/'build/paper/manuscript.pdf');ap.add_argument('--images',type=Path);a=ap.parse_args()
    exe=shutil.which('libreoffice') or shutil.which('soffice')
    if not exe:raise SystemExit('LibreOffice is required. Do not pretend a DOCX has been rendered.')
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);profile=(tmp/'profile').as_uri();dest=tmp/'out';dest.mkdir()
        p=subprocess.run([exe,'-env:UserInstallation='+profile,'--headless','--convert-to','pdf','--outdir',str(dest),str(a.docx.resolve())],capture_output=True,text=True,timeout=180)
        built=dest/(a.docx.stem+'.pdf')
        if p.returncode or not built.exists():raise SystemExit('PDF conversion failed: '+p.stdout+' '+p.stderr)
        a.pdf.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(built,a.pdf)
    if a.images:
        import fitz
        a.images.mkdir(parents=True,exist_ok=True)
        with fitz.open(a.pdf) as d:
            for i,page in enumerate(d):page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(a.images/f'page-{i+1}.png')
    print(a.pdf)
if __name__=='__main__':main()
