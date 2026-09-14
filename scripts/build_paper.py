#!/usr/bin/env python3
"""Build the current paper locally; stop before build if its toolchain is absent."""
from pathlib import Path
import subprocess
import sys
from check_readiness import build_gates

ROOT = Path(__file__).resolve().parents[1]


def main():
    gates = build_gates()
    if not gates['ready']:
        missing = [name for name, present in gates['python_modules'].items() if not present]
        missing += [name for name, path in gates['executables'].items() if not path]
        if not gates['font_available']:
            missing.append('Old Standard font')
        raise SystemExit('Paper build unavailable: ' + ', '.join(missing)
                         + '. See docs/REPRODUCING.md. Current source is unrendered; no old PDF is substituted.')
    commands = [
        ['scripts/make_figures.py'],
        ['scripts/build_report.py'],
        ['scripts/render_report.py', '--images', 'build/paper/pages'],
        ['scripts/verify_report.py'],
    ]
    for command in commands:
        subprocess.run([sys.executable, *command], cwd=ROOT, check=True)
    print('Built build/paper/manuscript.docx and .pdf. Inspect every image in build/paper/pages before release.')


if __name__ == '__main__':
    main()
