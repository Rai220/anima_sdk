#!/usr/bin/env python3
"""Classify active human feedback from INBOX.md."""

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


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text()


def strip_html_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def active_lines(text: str) -> list[str]:
    body = strip_html_comments(text)
    lines: list[str] = []
    for raw in body.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if stripped in {"---", "..."}:
            continue
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()
        lines.append(stripped)
    return lines


def classify(line: str) -> tuple[str, str]:
    lower = line.lower()
    for label, prefixes in LABELS:
        for prefix in prefixes:
            if lower.startswith(prefix):
                return label, line[len(prefix) :].strip()
    return "general", line


def parse_inbox(path: Path) -> dict[str, list[str]]:
    items: dict[str, list[str]] = {label: [] for label, _prefixes in LABELS}
    items["general"] = []
    for line in active_lines(read_text(path)):
        label, text = classify(line)
        items[label].append(text or line)
    return items


def render(root: Path) -> str:
    path = root / "INBOX.md"
    items = parse_inbox(path)
    total = sum(len(values) for values in items.values())
    lines = [f"root: {root}", f"inbox_path: {path}"]

    if not path.exists():
        lines.append("status: missing")
        return "\n".join(lines) + "\n"

    lines.append(f"status: {'active' if total else 'empty'}")
    lines.append(f"active_items: {total}")
    for label in ["urgent", "do_not", "focus", "feedback", "question", "general"]:
        values = items[label]
        lines.append(f"{label}: {len(values)}")
        for value in values:
            lines.append(f"  - {value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Классифицирует активные строки INBOX.md, игнорируя HTML-комментарии."
    )
    parser.add_argument("root", nargs="?", default=".", help="Директория поколения.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    print(render(root), end="")
    return 1 if not (root / "INBOX.md").exists() else 0


if __name__ == "__main__":
    sys.exit(main())
