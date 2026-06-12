#!/usr/bin/env python3
"""Print the next bounded intention from TODO.md."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text()


def parse_todos(path: Path) -> list[tuple[bool, str]]:
    items: list[tuple[bool, str]] = []
    current_index: int | None = None
    for line in read_text(path).splitlines():
        stripped = line.strip()
        lower = stripped.lower()
        if stripped.startswith("- [ ] ") or lower.startswith("- [x] "):
            checked = lower.startswith("- [x] ")
            items.append((checked, stripped[6:].strip()))
            current_index = len(items) - 1
            continue
        if current_index is not None and line.startswith("  ") and stripped:
            old_checked, old_text = items[current_index]
            items[current_index] = (old_checked, f"{old_text} {stripped}")
    return items


def first_section_paragraph(text: str, heading: str) -> str | None:
    lines = text.splitlines()
    in_section = False
    paragraph: list[str] = []
    for line in lines:
        if line.strip() == heading:
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and line.strip():
            paragraph.append(line.strip())
            continue
        if in_section and paragraph:
            break
    if not paragraph:
        return None
    return " ".join(paragraph)


def strip_html_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def active_inbox_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in strip_html_comments(text).splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()
        lines.append(stripped)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Печатает первый открытый пункт TODO как следующее намерение."
    )
    parser.add_argument("root", nargs="?", default=".", help="Директория поколения.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    todos = parse_todos(root / "TODO.md")
    open_items = [text for checked, text in todos if not checked]
    done_count = sum(1 for checked, _text in todos if checked)
    state = read_text(root / "STATE.md")
    inbox_items = active_inbox_lines(read_text(root / "INBOX.md"))

    print(f"root: {root}")
    print(f"todo: {done_count} done, {len(open_items)} open")
    print(f"inbox: {'active' if inbox_items else 'empty'}")
    if inbox_items:
        print(f"inbox_first: {inbox_items[0]}")

    state_hint = first_section_paragraph(state, "## Следующий хороший ход")
    if state_hint:
        print(f"state_hint: {state_hint}")

    if open_items:
        print(f"next_intent: {open_items[0]}")
        return 0

    print("next_intent: none")
    return 1


if __name__ == "__main__":
    sys.exit(main())
