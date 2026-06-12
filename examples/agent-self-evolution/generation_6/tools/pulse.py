#!/usr/bin/env python3
"""Print a compact local pulse for a self-evolution generation."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys


CORE_FILES = [
    "INBOX.md",
    "LESSONS.md",
    "STATE.md",
    "TODO.md",
    "DECISIONS.md",
    "JOURNAL.md",
    "SELF_MODEL.md",
    "WORLD_MODEL.md",
    "INTERFACE.md",
    "BEHAVIOR_CHECKLIST.md",
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


def active_inbox_lines(text: str) -> list[str]:
    items: list[str] = []
    for raw in strip_html_comments(text).splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()
        items.append(stripped)
    return items


def parse_todos(text: str) -> list[tuple[bool, str]]:
    items: list[tuple[bool, str]] = []
    current_index: int | None = None
    for line in text.splitlines():
        stripped = line.strip()
        lower = stripped.lower()
        if stripped.startswith("- [ ] ") or lower.startswith("- [x] "):
            checked = lower.startswith("- [x] ")
            items.append((checked, stripped[6:].strip()))
            current_index = len(items) - 1
            continue
        if current_index is not None and line.startswith("  ") and stripped:
            checked, old_text = items[current_index]
            items[current_index] = (checked, f"{old_text} {stripped}")
    return items


def first_section_paragraph(text: str, heading: str) -> str:
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
    return " ".join(paragraph)


def last_journal_heading(text: str) -> str:
    headings = re.findall(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
    return headings[-1] if headings else "none"


def registered_tools(agent_text: str) -> set[str]:
    marker = re.search(r"^## Инструменты задачи\s*$", agent_text, flags=re.MULTILINE)
    if not marker:
        return set()
    section = agent_text[marker.end() :]
    next_heading = re.search(r"^## ", section, flags=re.MULTILINE)
    if next_heading:
        section = section[: next_heading.start()]
    return set(re.findall(r"^### (tools/[^\s]+)\s*$", section, flags=re.MULTILINE))


def executable_tools(root: Path) -> set[str]:
    tools_dir = root / "tools"
    if not tools_dir.exists():
        return set()
    return {
        f"tools/{path.name}"
        for path in tools_dir.iterdir()
        if path.is_file() and os.access(path, os.X_OK)
    }


def short(text: str, limit: int = 140) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3] + "..."


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Печатает компактный пульс локальной памяти поколения."
    )
    parser.add_argument("root", nargs="?", default=".", help="Директория поколения.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    missing = [name for name in CORE_FILES if not (root / name).exists()]
    inbox_items = active_inbox_lines(read_text(root / "INBOX.md"))
    todos = parse_todos(read_text(root / "TODO.md"))
    done = sum(1 for checked, _text in todos if checked)
    open_items = [text for checked, text in todos if not checked]
    state_hint = first_section_paragraph(read_text(root / "STATE.md"), "## Следующий хороший ход")
    metrics = read_text(root / "METRICS.md")
    registered = registered_tools(read_text(root / "AGENTS.md"))
    executable = executable_tools(root)

    print("# PULSE")
    print(f"root: {root}")
    print(f"inbox: {'active' if inbox_items else 'empty'}")
    if inbox_items:
        print(f"inbox_first: {short(inbox_items[0])}")
    print(f"memory_missing: {', '.join(missing) if missing else 'none'}")
    print(f"todo: {done} done, {len(open_items)} open")
    print(f"next: {short(open_items[0]) if open_items else 'none'}")
    print(f"state_hint: {short(state_hint) if state_hint else 'none'}")
    print(f"last_journal: {last_journal_heading(read_text(root / 'JOURNAL.md'))}")
    print(f"stop_file: {'present' if (root / 'STOP').exists() else 'absent'}")
    print(f"tools_registered: {len(registered)}")
    print(f"tools_executable: {len(executable)}")
    if registered != executable:
        print("tool_mismatch: yes")
        missing_exec = sorted(registered - executable)
        missing_registration = sorted(executable - registered)
        if missing_exec:
            print(f"registered_not_executable: {', '.join(missing_exec)}")
        if missing_registration:
            print(f"executable_not_registered: {', '.join(missing_registration)}")
    else:
        print("tool_mismatch: no")
    print(f"metrics: {'present' if metrics.strip() else 'missing'}")

    if missing or registered != executable:
        print("status: attention")
        return 1
    print("status: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
