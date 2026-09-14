#!/usr/bin/env python3
"""Register an existing local Old Standard installation. Never download fonts.

This writes only a dedicated user fontconfig file after --apply is supplied.
Font binaries are not copied into the research artifact or distributed.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import subprocess
from xml.sax.saxutils import escape


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--font-dir', type=Path, default=Path('/usr/share/texlive/texmf-dist/fonts/opentype/public/oldstandard'))
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()
    folder = args.font_dir.resolve()
    if not folder.is_dir() or not any(folder.glob('OldStandard*')):
        raise SystemExit('An existing local Old Standard installation was not found. Supply a licensed local installation; this script never downloads files.')
    if not shutil.which('fc-cache') or not shutil.which('fc-match'):
        raise SystemExit('fontconfig is unavailable. Install required build tools only under explicit local authorization.')
    target = Path.home()/'.config/fontconfig/conf.d/99-realgame-oldstandard.conf'
    xml = ('<?xml version="1.0"?>\n<!DOCTYPE fontconfig SYSTEM "fonts.dtd">\n<fontconfig>\n'
           '  <dir>'+escape(str(folder))+'</dir>\n'
           '  <alias><family>Old Standard TT</family><prefer><family>Old Standard</family></prefer></alias>\n</fontconfig>\n')
    if not args.apply:
        print('Existing font directory: '+str(folder))
        print('Run with --apply to write only '+str(target))
        return
    if target.exists() and target.read_text() != xml:
        raise SystemExit('Dedicated fontconfig file differs; review it manually instead of overwriting.')
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_text(xml)
    subprocess.run(['fc-cache', '-f'], check=True, timeout=120)
    subprocess.run(['fc-match', 'Old Standard TT'], check=True, timeout=20)
    print('Registered local font; no font binary was copied or bundled.')


if __name__ == '__main__':
    main()
