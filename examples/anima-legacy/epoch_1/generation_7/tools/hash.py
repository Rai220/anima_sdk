#!/usr/bin/env python3
"""
hash.py — File and text hash calculator. Zero dependencies.

Usage:
  python3 hash.py file.txt              # Hash a file
  python3 hash.py -t "hello world"      # Hash text
  echo "data" | python3 hash.py         # Hash from stdin
  python3 hash.py -a sha256 file.txt    # Specific algorithm
  python3 hash.py --verify abc123 file  # Verify hash matches
  python3 hash.py --json file.txt       # JSON output
"""

import argparse
import hashlib
import sys
import os
import json as _json

ALGORITHMS = ['md5', 'sha1', 'sha256', 'sha512']


def hash_data(data, algorithms=None):
    """Hash bytes data with specified algorithms. Returns dict of algo: hex."""
    if algorithms is None:
        algorithms = ['md5', 'sha1', 'sha256']
    result = {}
    for algo in algorithms:
        h = hashlib.new(algo)
        h.update(data)
        result[algo] = h.hexdigest()
    return result


def hash_file(path, algorithms=None):
    """Hash a file by reading in chunks. Returns dict of algo: hex."""
    if algorithms is None:
        algorithms = ['md5', 'sha1', 'sha256']
    hashers = {algo: hashlib.new(algo) for algo in algorithms}
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            for h in hashers.values():
                h.update(chunk)
    return {algo: h.hexdigest() for algo, h in hashers.items()}


def format_size(size):
    """Human-readable file size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}" if unit != 'B' else f"{size} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def main():
    parser = argparse.ArgumentParser(
        description='File and text hash calculator — zero dependencies',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Examples:\n'
               '  python3 hash.py file.txt\n'
               '  python3 hash.py -t "hello"\n'
               '  python3 hash.py -a sha256 *.py\n'
               '  python3 hash.py --verify abc123 file.txt\n'
    )
    parser.add_argument('files', nargs='*', help='Files to hash')
    parser.add_argument('-t', '--text', help='Hash text instead of file')
    parser.add_argument('-a', '--algorithm', choices=ALGORITHMS,
                        help='Single algorithm (default: md5+sha1+sha256)')
    parser.add_argument('--verify', metavar='HASH',
                        help='Verify file matches expected hash')
    parser.add_argument('--json', action='store_true', help='JSON output')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Output only hash (first algorithm)')

    args = parser.parse_args()
    algos = [args.algorithm] if args.algorithm else ['md5', 'sha1', 'sha256']

    # Text mode
    if args.text is not None:
        hashes = hash_data(args.text.encode('utf-8'), algos)
        if args.json:
            print(_json.dumps({"input": args.text, "hashes": hashes}))
        elif args.quiet:
            print(list(hashes.values())[0])
        else:
            for algo, h in hashes.items():
                print(f"  {algo:>6}  {h}")
        return

    # Stdin mode (no files, no text)
    if not args.files:
        if sys.stdin.isatty():
            parser.print_help()
            return
        data = sys.stdin.buffer.read()
        hashes = hash_data(data, algos)
        if args.json:
            print(_json.dumps({"input": "stdin", "size": len(data), "hashes": hashes}))
        elif args.quiet:
            print(list(hashes.values())[0])
        else:
            for algo, h in hashes.items():
                print(f"  {algo:>6}  {h}")
        return

    # File mode
    results = []
    for path in args.files:
        if not os.path.isfile(path):
            print(f"  ✗ {path}: not found", file=sys.stderr)
            continue

        hashes = hash_file(path, algos)
        size = os.path.getsize(path)

        # Verify mode
        if args.verify:
            expected = args.verify.lower()
            matched = any(h == expected for h in hashes.values())
            if args.json:
                results.append({"file": path, "match": matched, "hashes": hashes})
            elif matched:
                print(f"  ✓ {path}: hash matches")
            else:
                print(f"  ✗ {path}: hash does NOT match")
                for algo, h in hashes.items():
                    print(f"      {algo}: {h}")
            continue

        if args.json:
            results.append({"file": path, "size": size, "hashes": hashes})
        elif args.quiet:
            print(f"{list(hashes.values())[0]}  {path}")
        else:
            print(f"\n  {path} ({format_size(size)})")
            for algo, h in hashes.items():
                print(f"  {algo:>6}  {h}")

    if args.json and results:
        print(_json.dumps(results if len(results) > 1 else results[0], indent=2))


if __name__ == '__main__':
    main()
