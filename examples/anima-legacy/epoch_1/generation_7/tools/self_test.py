#!/usr/bin/env python3
"""
self_test.py — Validates all micro-tools in the toolkit.

Checks:
  - HTML files parse without errors
  - Python scripts import and run --help without errors
  - index.html links match actual files
  - No broken internal references

Usage:
  python3 self_test.py          # Run all checks
  python3 self_test.py -v       # Verbose output
"""

import os
import sys
import subprocess
import re
from html.parser import HTMLParser
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'
CHECK = '✓'
CROSS = '✗'
WARN = '!'

verbose = '-v' in sys.argv or '--verbose' in sys.argv
passed = 0
failed = 0
warnings = 0


def log_pass(msg):
    global passed
    passed += 1
    print(f'  {GREEN}{CHECK}{RESET} {msg}')


def log_fail(msg):
    global failed
    failed += 1
    print(f'  {RED}{CROSS}{RESET} {msg}')


def log_warn(msg):
    global warnings
    warnings += 1
    print(f'  {YELLOW}{WARN}{RESET} {msg}')


def log_info(msg):
    if verbose:
        print(f'    {msg}')


# --- Checks ---

class HTMLValidator(HTMLParser):
    VOID = {'br', 'hr', 'img', 'input', 'meta', 'link', 'area', 'base',
            'col', 'embed', 'source', 'track', 'wbr'}

    def __init__(self):
        super().__init__()
        self.errors = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            self.errors.append(f'Mismatched closing tag: </{tag}>')


def check_html_files():
    print('\n📄 HTML Files')
    html_files = sorted(TOOLS_DIR.glob('*.html'))

    if not html_files:
        log_fail('No HTML files found')
        return

    for f in html_files:
        content = f.read_text(encoding='utf-8')
        validator = HTMLValidator()
        try:
            validator.feed(content)
            if validator.errors:
                log_fail(f'{f.name}: {validator.errors[0]}')
            elif validator.stack:
                log_fail(f'{f.name}: Unclosed tags: {validator.stack}')
            else:
                size_kb = len(content) / 1024
                log_pass(f'{f.name} ({size_kb:.1f} KB)')
                log_info(f'Tags OK, no parsing errors')
        except Exception as e:
            log_fail(f'{f.name}: Parse error: {e}')

        # Check for basic structure
        if '<!DOCTYPE html>' not in content[:50]:
            log_warn(f'{f.name}: Missing DOCTYPE')
        if '<title>' not in content:
            log_warn(f'{f.name}: Missing <title>')


def check_js_syntax():
    """Check JavaScript syntax in HTML files using Node.js."""
    # Only run if node is available
    try:
        result = subprocess.run(['node', '--version'],
            capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return  # Skip silently if no node
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return

    print('\n📜 JavaScript Syntax')
    html_files = sorted(TOOLS_DIR.glob('*.html'))
    html_files = [f for f in html_files if f.name != 'index.html']

    for f in html_files:
        content = f.read_text(encoding='utf-8')
        # Extract all <script> blocks
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
        if not scripts:
            continue

        combined = '\n'.join(scripts)
        tmp = TOOLS_DIR / f'_test_{f.stem}.js'
        try:
            tmp.write_text(combined, encoding='utf-8')
            result = subprocess.run(
                ['node', '--check', str(tmp)],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                log_pass(f'{f.name}: JS syntax OK')
            else:
                err = result.stderr.strip().split('\n')[0]
                log_fail(f'{f.name}: JS error: {err}')
        except Exception as e:
            log_fail(f'{f.name}: JS check failed: {e}')
        finally:
            if tmp.exists():
                tmp.unlink()


def check_python_files():
    print('\n🐍 Python Files')
    py_files = sorted(TOOLS_DIR.glob('*.py'))
    py_files = [f for f in py_files if f.name != 'self_test.py']

    if not py_files:
        log_warn('No Python tool files found')
        return

    for f in py_files:
        # Syntax check
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', str(f)],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                log_pass(f'{f.name}: Syntax OK')
            else:
                log_fail(f'{f.name}: Syntax error: {result.stderr.strip()}')
                continue
        except subprocess.TimeoutExpired:
            log_fail(f'{f.name}: Compilation timeout')
            continue

        # Help check (should not crash)
        try:
            result = subprocess.run(
                [sys.executable, str(f), '--help'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                log_pass(f'{f.name}: --help OK')
                log_info(result.stdout.split('\n')[0] if result.stdout else '(no output)')
            else:
                log_warn(f'{f.name}: --help returned code {result.returncode}')
        except subprocess.TimeoutExpired:
            log_fail(f'{f.name}: --help timeout')


def check_index_links():
    print('\n🔗 Index Links')
    index_path = TOOLS_DIR / 'index.html'

    if not index_path.exists():
        log_fail('index.html not found')
        return

    content = index_path.read_text(encoding='utf-8')
    hrefs = re.findall(r'href="([^"]+\.html)"', content)

    if not hrefs:
        log_fail('No tool links found in index.html')
        return

    actual_files = {f.name for f in TOOLS_DIR.glob('*.html') if f.name != 'index.html'}

    # Check all links resolve
    for href in hrefs:
        target = TOOLS_DIR / href
        if target.exists():
            log_pass(f'Link OK: {href}')
        else:
            log_fail(f'Broken link: {href}')

    # Check all tools are linked
    linked = set(hrefs)
    unlinked = actual_files - linked
    for f in sorted(unlinked):
        log_warn(f'Not in index: {f}')

    log_info(f'{len(hrefs)} links, {len(actual_files)} HTML tools')


def check_file_sizes():
    print('\n📊 File Sizes')
    all_files = sorted(TOOLS_DIR.glob('*'))
    all_files = [f for f in all_files if f.is_file() and not f.name.startswith('.')]

    total = 0
    for f in all_files:
        size = f.stat().st_size
        total += size
        if verbose:
            log_info(f'{f.name}: {size / 1024:.1f} KB')

    log_pass(f'Total: {total / 1024:.1f} KB across {len(all_files)} files')

    # Check for unreasonably large files
    for f in all_files:
        if f.stat().st_size > 100_000:
            log_warn(f'{f.name} is large ({f.stat().st_size / 1024:.0f} KB)')


def check_no_external_deps():
    print('\n📦 Dependencies')
    py_files = sorted(TOOLS_DIR.glob('*.py'))
    py_files = [f for f in py_files if f.name != 'self_test.py']

    stdlib = getattr(sys, 'stdlib_module_names', set()) | {
        'html.parser',  # submodule not in stdlib_module_names
    }

    for f in py_files:
        content = f.read_text(encoding='utf-8')
        imports = re.findall(r'^(?:import|from)\s+(\w+)', content, re.MULTILINE)
        external = [i for i in imports if i not in stdlib and not i.startswith('_')]
        if external:
            log_warn(f'{f.name}: Possible external deps: {external}')
        else:
            log_pass(f'{f.name}: Zero external dependencies')


def run_tool(tool_name, args, check, label, stdin=None, env=None):
    """Run a CLI tool and check output. Returns result or None on failure."""
    try:
        cmd = [sys.executable, str(TOOLS_DIR / tool_name)] + args
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10,
            input=stdin, env=env
        )
        ok, msg = check(result)
        if ok:
            log_pass(f'{tool_name}: {label}' + (f' ({msg})' if msg else ''))
        else:
            log_fail(f'{tool_name}: {label} — {msg}')
        return result
    except Exception as e:
        log_fail(f'{tool_name}: {label} — {e}')
        return None


def check_functional():
    """Functional tests — verify tools produce correct output."""
    print('\n🧪 Functional Tests')

    # password.py tests
    run_tool('password.py', ['-n', '20', '-q'],
        lambda r: (len(r.stdout.strip()) == 20, f'{len(r.stdout.strip())} chars'),
        '20-char password generated')

    run_tool('password.py', ['-w', '5', '-q'],
        lambda r: (len(r.stdout.strip().split('-')) == 5, None),
        '5-word passphrase OK')

    run_tool('password.py', ['--pin', '6', '-q'],
        lambda r: (len(r.stdout.strip()) == 6 and r.stdout.strip().isdigit(), None),
        '6-digit PIN OK')

    run_tool('password.py', ['-c', '3', '-q'],
        lambda r: (len([l for l in r.stdout.strip().split('\n') if l.strip()]) == 3, None),
        'Batch of 3 OK')

    run_tool('password.py', ['--check', 'Test123!', '-q'],
        lambda r: (r.stdout.strip().isdigit() and int(r.stdout.strip()) > 0, None),
        'Check mode returns entropy')

    run_tool('password.py', ['--json'],
        lambda r: ('"password"' in r.stdout and '"entropy"' in r.stdout, None),
        'JSON output valid')

    # hash.py tests
    run_tool('hash.py', ['-t', 'hello', '-q'],
        lambda r: (r.stdout.strip() == '5d41402abc4b2a76b9719d911017c592', None),
        'Text hash MD5 correct')

    run_tool('hash.py', ['-t', 'hello', '--json'],
        lambda r: ('"sha256"' in r.stdout and '"md5"' in r.stdout, None),
        'JSON output valid')

    # qr.py tests
    run_tool('qr.py', ['TEST'],
        lambda r: ('█' in r.stdout and len(r.stdout) > 50, f'{len(r.stdout)} chars'),
        'Terminal QR rendered')

    # qr.py: SVG output (needs file cleanup)
    try:
        svg_path = TOOLS_DIR / '_test_qr.svg'
        subprocess.run(
            [sys.executable, str(TOOLS_DIR / 'qr.py'), '-o', str(svg_path), 'HELLO'],
            capture_output=True, text=True, timeout=10
        )
        if svg_path.exists():
            content = svg_path.read_text()
            if '<svg' in content and 'viewBox' in content:
                log_pass('qr.py: SVG output valid')
            else:
                log_fail('qr.py: SVG missing required elements')
            svg_path.unlink()
        else:
            log_fail('qr.py: SVG file not created')
    except Exception as e:
        log_fail(f'qr.py SVG: {e}')

    run_tool('qr.py', [],
        lambda r: ('█' in r.stdout, None),
        'Stdin pipe OK', stdin='PIPE_TEST')

    # password.py: wordlist integrity
    try:
        sys.path.insert(0, str(TOOLS_DIR))
        import importlib
        pw_mod = importlib.import_module('password')
        importlib.reload(pw_mod)
        wl = pw_mod.WORDLIST
        if len(wl) == 1024:
            log_pass('password.py: Wordlist is exactly 1024 words')
        else:
            log_fail(f'password.py: Wordlist has {len(wl)} words, expected 1024')
        if len(set(wl)) == len(wl):
            log_pass('password.py: No duplicate words')
        else:
            log_fail('password.py: Duplicate words found')
    except Exception as e:
        log_fail(f'password.py wordlist: {e}')

    # run_tracker.py: isolated tests using temp log file
    test_log = str(TOOLS_DIR / '_test_run_log.json')
    test_env = os.environ.copy()
    test_env['RUN_TRACKER_LOG'] = test_log
    try:
        # Setup: log 4 identical entries silently
        for i in range(4):
            subprocess.run(
                [sys.executable, str(TOOLS_DIR / 'run_tracker.py'),
                 'log', f'Test action {i+1}', '-t', 'test,html'],
                capture_output=True, text=True, timeout=10, env=test_env
            )

        run_tool('run_tracker.py', ['drift'],
            lambda r: ('ДРЕЙФ' in r.stdout, None),
            'Drift detection works', env=test_env)

        run_tool('run_tracker.py', ['stats'],
            lambda r: ('test' in r.stdout and '4' in r.stdout, None),
            'Stats output correct', env=test_env)

        run_tool('run_tracker.py', ['suggest'],
            lambda r: ('Рекомендуемые' in r.stdout, None),
            'Suggest output correct', env=test_env)

        run_tool('run_tracker.py', ['status'],
            lambda r: ('Статус проекта' in r.stdout and 'дрейф' in r.stdout.lower(), None),
            'Status output correct', env=test_env)

        run_tool('run_tracker.py', ['log', '', '-t', 'test'],
            lambda r: (r.returncode != 0, None),
            'Empty summary rejected', env=test_env)
    finally:
        if os.path.exists(test_log):
            os.remove(test_log)

    # serve.py: starts and serves index.html
    try:
        import urllib.request
        import time
        import random
        port = 18700 + random.randint(50, 99)
        proc = subprocess.Popen(
            [sys.executable, str(TOOLS_DIR / 'serve.py'), '-p', str(port), '--no-open'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        connected = False
        for attempt in range(4):
            time.sleep(0.5 + attempt * 0.5)
            try:
                resp = urllib.request.urlopen(f'http://localhost:{port}/', timeout=3)
                if resp.status == 200 and b'Micro Tools' in resp.read():
                    log_pass('serve.py: Starts and serves index.html')
                    connected = True
                    break
            except Exception:
                continue
        if not connected:
            log_fail('serve.py: Cannot connect after retries')
        proc.terminate()
        proc.wait(timeout=5)
    except Exception as e:
        log_fail(f'serve.py functional: {e}')


# --- Main ---

def main():
    print('🔧 Micro-Tools Self-Test')
    print(f'   Directory: {TOOLS_DIR}')

    check_html_files()
    check_js_syntax()
    check_python_files()
    check_index_links()
    check_no_external_deps()
    check_functional()
    check_file_sizes()

    print(f'\n{"=" * 40}')
    print(f'  {GREEN}{passed} passed{RESET}', end='')
    if failed:
        print(f'  {RED}{failed} failed{RESET}', end='')
    if warnings:
        print(f'  {YELLOW}{warnings} warnings{RESET}', end='')
    print()

    # Cache results for run_tracker check
    import json, datetime as _dt
    cache = {"passed": passed, "failed": failed, "warnings": warnings,
             "timestamp": _dt.datetime.now().isoformat(timespec='seconds')}
    try:
        cache_path = TOOLS_DIR / '.last_test_results.json'
        cache_path.write_text(json.dumps(cache), encoding='utf-8')
    except Exception:
        pass

    if failed:
        print(f'\n  {RED}FAIL{RESET}')
        sys.exit(1)
    else:
        print(f'\n  {GREEN}ALL CHECKS PASSED{RESET}')


if __name__ == '__main__':
    main()
