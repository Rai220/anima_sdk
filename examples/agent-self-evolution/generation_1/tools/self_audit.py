#!/usr/bin/env python3
"""Check the local self-evolution memory surface."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REQUIRED_FILES = [
    "MAIN_GOAL.md",
    "AGENTS.md",
    "INBOX.md",
    "STATE.md",
    "SELF_MODEL.md",
    "WORLD_MODEL.md",
    "INTERFACE.md",
    "TODO.md",
    "DECISIONS.md",
    "LESSONS.md",
    "JOURNAL.md",
    "BEHAVIOR_CHECKLIST.md",
]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text()


def parse_todos(todo_path: Path) -> list[tuple[bool, str]]:
    if not todo_path.exists():
        return []

    todos: list[tuple[bool, str]] = []
    current_index: int | None = None

    for line in read_text(todo_path).splitlines():
        stripped = line.strip()
        lower = stripped.lower()

        if stripped.startswith("- [ ] ") or lower.startswith("- [x] "):
            checked = lower.startswith("- [x] ")
            todos.append((checked, stripped[6:].strip()))
            current_index = len(todos) - 1
            continue

        if current_index is not None and line.startswith("  ") and stripped:
            checked, text = todos[current_index]
            todos[current_index] = (checked, f"{text} {stripped}")

    return todos


def first_open_todo(todo_path: Path) -> str | None:
    for checked, text in parse_todos(todo_path):
        if not checked:
            return text
    return None


def checkbox_counts(todo_path: Path) -> tuple[int, int]:
    open_count = 0
    done_count = 0
    for checked, _text in parse_todos(todo_path):
        if checked:
            done_count += 1
        else:
            open_count += 1
    return open_count, done_count


def nonempty_status(path: Path) -> str:
    if not path.exists():
        return "missing"
    if path.stat().st_size == 0:
        return "empty"
    return "nonempty"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Проверяет базовую память и показывает следующий открытый шаг."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Директория поколения, по умолчанию текущая.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    missing = [name for name in REQUIRED_FILES if not (root / name).exists()]
    open_count, done_count = checkbox_counts(root / "TODO.md")
    next_todo = first_open_todo(root / "TODO.md")

    print(f"root: {root}")
    print(f"inbox: {nonempty_status(root / 'INBOX.md')}")
    print(f"lessons: {nonempty_status(root / 'LESSONS.md')}")
    print(f"todo: {done_count} done, {open_count} open")

    if missing:
        print("missing:")
        for name in missing:
            print(f"  - {name}")
    else:
        print("missing: none")

    if next_todo:
        print(f"next: {next_todo}")
    else:
        print("next: no open TODO item")

    if missing:
        print("status: fail")
        return 1
    print("status: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
