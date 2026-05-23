#!/usr/bin/env python3
"""Print a compact handoff report for the next run or generation."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text()


def checkbox_items(path: Path, checked: bool) -> list[str]:
    if not path.exists():
        return []

    items: list[tuple[bool, str]] = []
    current_index: int | None = None
    for line in read_text(path).splitlines():
        stripped = line.strip()
        lower = stripped.lower()
        if stripped.startswith("- [ ] ") or lower.startswith("- [x] "):
            is_checked = lower.startswith("- [x] ")
            items.append((is_checked, stripped[6:].strip()))
            current_index = len(items) - 1
        elif current_index is not None and line.startswith("  ") and stripped:
            old_checked, old_text = items[current_index]
            items[current_index] = (old_checked, f"{old_text} {stripped}")

    return [text for is_checked, text in items if is_checked == checked]


def latest_section(path: Path) -> list[str]:
    if not path.exists():
        return []

    lines = read_text(path).splitlines()
    sections: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if current:
                sections.append(current)
            current = [line]
        elif current:
            current.append(line)
    if current:
        sections.append(current)
    if not sections:
        return []
    return [line for line in sections[-1] if line.strip()]


def count_lesson_symptoms(path: Path) -> int:
    if not path.exists():
        return 0
    return len(re.findall(r"(^|\n)- Симптом:", read_text(path)))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Печатает краткий handoff-отчёт по текущей генерации."
    )
    parser.add_argument("root", nargs="?", default=".", help="Директория поколения.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    todo = root / "TODO.md"
    lessons = root / "LESSONS.md"
    journal = root / "JOURNAL.md"

    done = checkbox_items(todo, checked=True)
    open_items = checkbox_items(todo, checked=False)
    latest_journal = latest_section(journal)

    print("# HANDOFF")
    print()
    print(f"root: {root}")
    print(f"done_tasks: {len(done)}")
    print(f"open_tasks: {len(open_items)}")
    print(f"lesson_symptoms: {count_lesson_symptoms(lessons)}")
    print()
    print("## Next")
    if open_items:
        print(f"- {open_items[0]}")
    else:
        print("- Нет открытых пунктов в TODO.md.")
    print()
    print("## Open TODO")
    if open_items:
        for item in open_items:
            print(f"- {item}")
    else:
        print("- Нет.")
    print()
    print("## Latest Journal")
    if latest_journal:
        for line in latest_journal[:30]:
            print(line)
    else:
        print("- JOURNAL.md пуст или отсутствует.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
