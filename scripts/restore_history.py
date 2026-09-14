#!/usr/bin/env python3
"""Restore one explicitly selected historical file to a fresh output path."""
import argparse
from pathlib import Path
from history import read_historical, verify_history


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path', help='Exact logical key from archive/INDEX.json')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        print(verify_history())
        return
    if not args.path or not args.out:
        parser.error('--path and --out are required when not using --verify')
    data = read_historical(args.path)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('xb') as stream:
        stream.write(data)
    print(args.out)


if __name__ == '__main__':
    main()
