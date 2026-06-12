#!/usr/bin/env python3
"""Print the next bounded intention from INBOX.md or TODO.md."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


LABELS = [
    ("urgent", ("срочно:", "urgent:")),
    ("do_not", ("не делать:", "do not:", "dont:", "don't:")),
    ("focus", ("следующий фокус:", "фокус:", "next focus:")),
    ("feedback", ("обратная связь:", "feedback:")),
    ("question", ("вопрос:", "question:")),
]

ACTION_PRIORITY = ["urgent", "focus", "question", "feedback", "general"]


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


def classify_inbox_line(line: str) -> tuple[str, str]:
    lower = line.lower()
    for label, prefixes in LABELS:
        for prefix in prefixes:
            if lower.startswith(prefix):
                return label, line[len(prefix) :].strip() or line
    return "general", line


def parse_inbox(path: Path) -> dict[str, list[str]]:
    items: dict[str, list[str]] = {label: [] for label, _prefixes in LABELS}
    items["general"] = []
    for line in active_inbox_lines(read_text(path)):
        label, text = classify_inbox_line(line)
        items[label].append(text)
    return items


def choose_intent(
    inbox_items: dict[str, list[str]], open_items: list[str]
) -> tuple[str, str | None]:
    for label in ACTION_PRIORITY:
        if inbox_items[label]:
            return f"inbox:{label}", inbox_items[label][0]
    if open_items:
        return "todo", open_items[0]
    if inbox_items["do_not"]:
        return "inbox:do_not", f"Учитывать запрет: {inbox_items['do_not'][0]}"
    return "none", None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Печатает следующее намерение с учетом INBOX.md и TODO.md."
    )
    parser.add_argument("root", nargs="?", default=".", help="Директория поколения.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    todos = parse_todos(root / "TODO.md")
    open_items = [text for checked, text in todos if not checked]
    done_count = sum(1 for checked, _text in todos if checked)
    state = read_text(root / "STATE.md")
    inbox_items = parse_inbox(root / "INBOX.md")
    inbox_total = sum(len(values) for values in inbox_items.values())
    constraints = inbox_items["do_not"]

    print(f"root: {root}")
    print(f"todo: {done_count} done, {len(open_items)} open")
    print(f"inbox: {'active' if inbox_total else 'empty'}")
    if inbox_total:
        for label in ["urgent", "do_not", "focus", "feedback", "question", "general"]:
            print(f"inbox_{label}: {len(inbox_items[label])}")
    for constraint in constraints:
        print(f"constraint: {constraint}")

    state_hint = first_section_paragraph(state, "## Следующий хороший ход")
    if state_hint:
        print(f"state_hint: {state_hint}")

    decision_source, next_intent = choose_intent(inbox_items, open_items)
    print(f"decision_source: {decision_source}")
    if next_intent:
        print(f"next_intent: {next_intent}")
        return 0

    print("next_intent: none")
    return 1


if __name__ == "__main__":
    sys.exit(main())
