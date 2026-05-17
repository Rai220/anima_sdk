#!/usr/bin/env python3
"""
serve.py — Launch local server for all micro-tools.

Usage:
  python3 serve.py            # Serve on port 8080, open browser
  python3 serve.py -p 3000    # Custom port
  python3 serve.py --no-open  # Don't open browser

Serves the tools directory, opens index.html by default.
"""

import http.server
import socketserver
import argparse
import sys
import os
import webbrowser
from pathlib import Path
from functools import partial

TOOLS_DIR = Path(__file__).parent

# ANSI colors
GREEN = '\033[92m'
CYAN = '\033[96m'
MUTED = '\033[90m'
BOLD = '\033[1m'
RESET = '\033[0m'


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with cleaner logging."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(TOOLS_DIR), **kwargs)

    def log_message(self, format, *args):
        # Show only GET requests, skip favicon etc.
        method = args[0].split()[0] if args else ''
        path = args[0].split()[1] if args and len(args[0].split()) > 1 else ''
        code = args[1] if len(args) > 1 else ''

        if path and not path.startswith('/favicon'):
            status_color = GREEN if str(code) == '200' else '\033[93m'
            print(f'  {MUTED}{method}{RESET} {path} {status_color}{code}{RESET}')


def get_tool_list():
    """List available tools."""
    html_tools = sorted(TOOLS_DIR.glob('*.html'))
    py_tools = sorted(f for f in TOOLS_DIR.glob('*.py')
                      if f.name not in ('serve.py', 'self_test.py'))
    return html_tools, py_tools


def main():
    parser = argparse.ArgumentParser(description='Serve micro-tools locally')
    parser.add_argument('-p', '--port', type=int, default=8080, help='Port (default: 8080)')
    parser.add_argument('--no-open', action='store_true', help='Do not open browser automatically')
    args = parser.parse_args()

    html_tools, py_tools = get_tool_list()

    # Find an available port
    port = args.port
    for attempt in range(10):
        try:
            server = socketserver.TCPServer(('', port), QuietHandler)
            break
        except OSError:
            port += 1
    else:
        print(f'Could not find available port near {args.port}', file=sys.stderr)
        sys.exit(1)

    url = f'http://localhost:{port}'

    print(f'\n  {BOLD}Micro-Tools Server{RESET}')
    print(f'  {MUTED}{"─" * 36}{RESET}')
    print(f'  {GREEN}▶{RESET} {CYAN}{url}{RESET}')
    print(f'  {MUTED}{"─" * 36}{RESET}')
    print(f'  {BOLD}HTML Tools:{RESET}')

    for f in html_tools:
        if f.name == 'index.html':
            continue
        name = f.stem.replace('_', ' ').title()
        print(f'  {MUTED}•{RESET} {name:20s} {CYAN}{url}/{f.name}{RESET}')

    if py_tools:
        print(f'\n  {BOLD}CLI Tools:{RESET}')
        for f in py_tools:
            print(f'  {MUTED}•{RESET} {f.name:20s} {MUTED}python3 {f.name} --help{RESET}')

    print(f'\n  {MUTED}Press Ctrl+C to stop{RESET}\n')

    if not args.no_open:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f'\n  {MUTED}Server stopped.{RESET}')
        server.server_close()


if __name__ == '__main__':
    main()
