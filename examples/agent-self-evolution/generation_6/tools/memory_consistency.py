#!/usr/bin/env python3
"""Check simple consistency contracts between local memory files."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys


CORE_FILES = ["STATE.md", "TODO.md", "JOURNAL.md", "DECISIONS.md", "AGENTS.md"]
MEMORY_FILES = [
    "STATE.md",
    "TODO.md",
    "JOURNAL.md",
    "DECISIONS.md",
    "LESSONS.md",
    "INTERFACE.md",
    "SELF_MODEL.md",
    "WORLD_MODEL.md",
    "STOP_CRITERIA.md",
]
STOP_WORDS = {
    "следующий",
    "следующая",
    "следующее",
    "ход",
    "задача",
    "пункт",
    "нужно",
    "надо",
    "если",
    "или",
    "для",
    "что",
    "как",
    "после",
    "перед",
}


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


def code_spans(text: str) -> list[str]:
    return [span.strip() for span in re.findall(r"`([^`]+)`", text) if span.strip()]


def words(text: str) -> set[str]:
    found = set(re.findall(r"[A-Za-zА-Яа-я0-9_./-]{4,}", text.lower()))
    return {word for word in found if word not in STOP_WORDS}


def short(value: str, limit: int = 110) -> str:
    collapsed = " ".join(value.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3] + "..."


def count_registered_tools(agent_text: str) -> set[str]:
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


def mentioned_tools(root: Path) -> set[str]:
    mentions: set[str] = set()
    for name in MEMORY_FILES:
        text = read_text(root / name)
        mentions.update(re.findall(r"\btools/[A-Za-z0-9_.-]+(?:\.py|\.sh)\b", text))
    return mentions


def todo_has_journal_trace(todo: str, journal_text: str) -> bool:
    journal_lower = journal_text.lower()
    spans = [
        span
        for span in code_spans(todo)
        if len(span) >= 4 and span not in {"TODO.md", "STATE.md", "JOURNAL.md"}
    ]
    if spans and any(span.lower() in journal_lower for span in spans):
        return True

    todo_words = words(re.sub(r"`[^`]+`", " ", todo))
    if not todo_words:
        return True
    overlap = todo_words & words(journal_text)
    required = min(3, max(1, len(todo_words) // 3))
    return len(overlap) >= required


def state_matches_next_todo(state_text: str, first_open: str | None) -> bool:
    state_hint = first_section_paragraph(state_text, "## Следующий хороший ход")
    if not first_open:
        return not state_hint or "нет открытых" in state_hint.lower()
    if not state_hint:
        return False

    state_words = words(state_hint)
    todo_words = words(first_open)
    if not todo_words:
        return True
    overlap = state_words & todo_words
    return len(overlap) >= min(4, max(2, len(todo_words) // 3))


def parse_decisions(text: str) -> list[tuple[str, str, str]]:
    headings = list(
        re.finditer(r"^### (D\d+):\s*(.+?)\s*$", text, flags=re.MULTILINE)
    )
    decisions: list[tuple[str, str, str]] = []
    for index, match in enumerate(headings):
        start = match.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        decisions.append((match.group(1), match.group(2), text[start:end]))
    return decisions


def check(root: Path) -> tuple[list[str], list[str], list[str]]:
    ok: list[str] = []
    warnings: list[str] = []
    issues: list[str] = []

    missing = [name for name in CORE_FILES if not (root / name).exists()]
    if missing:
        issues.append("missing core files: " + ", ".join(missing))
    else:
        ok.append("core files present")

    state_text = read_text(root / "STATE.md")
    journal_text = read_text(root / "JOURNAL.md")
    agents_text = read_text(root / "AGENTS.md")
    decision_text = read_text(root / "DECISIONS.md")
    todos = parse_todos(root / "TODO.md")
    done = [text for checked, text in todos if checked]
    open_items = [text for checked, text in todos if not checked]

    if state_matches_next_todo(state_text, open_items[0] if open_items else None):
        ok.append("STATE.md next step matches first open TODO item")
    else:
        issues.append("STATE.md next step does not match first open TODO item")

    untraced = [todo for todo in done if not todo_has_journal_trace(todo, journal_text)]
    if untraced:
        for todo in untraced:
            issues.append(f"closed TODO has no journal trace: {short(todo)}")
    else:
        ok.append(f"closed TODO items have journal traces: {len(done)}")

    registered = count_registered_tools(agents_text)
    executable = executable_tools(root)
    mentioned = mentioned_tools(root)
    tool_files = {
        f"tools/{path.name}"
        for path in (root / "tools").iterdir()
        if (root / "tools").exists() and path.is_file()
    }

    missing_registered = sorted(registered - tool_files)
    unregistered_executable = sorted(executable - registered)
    unregistered_mentions = sorted(mentioned - registered)
    non_executable_registered = sorted(registered - executable)

    if missing_registered:
        issues.append("registered tool files missing: " + ", ".join(missing_registered))
    if unregistered_executable:
        issues.append("executable tools not registered: " + ", ".join(unregistered_executable))
    if unregistered_mentions:
        issues.append("mentioned tools not registered: " + ", ".join(unregistered_mentions))
    if non_executable_registered:
        issues.append("registered tools not executable: " + ", ".join(non_executable_registered))
    if not (
        missing_registered
        or unregistered_executable
        or unregistered_mentions
        or non_executable_registered
    ):
        ok.append(f"tool mentions, registrations and executables agree: {len(registered)}")

    decisions = parse_decisions(decision_text)
    ids = [decision_id for decision_id, _title, _body in decisions]
    duplicate_ids = sorted({decision_id for decision_id in ids if ids.count(decision_id) > 1})
    incomplete = [
        decision_id
        for decision_id, _title, body in decisions
        if "Решение:" not in body or "Причина:" not in body
    ]
    if duplicate_ids:
        issues.append("duplicate decision ids: " + ", ".join(duplicate_ids))
    if incomplete:
        issues.append("decisions without Решение/Причина: " + ", ".join(incomplete))
    if decisions and not duplicate_ids and not incomplete:
        ok.append(f"decision records are structured and unique: {len(decisions)}")
    if not decisions:
        warnings.append("no decisions found in DECISIONS.md")

    if not open_items:
        warnings.append("TODO.md has no open item; handoff should explain next generation")

    return ok, warnings, issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Проверяет простую согласованность локальной памяти поколения."
    )
    parser.add_argument("root", nargs="?", default=".", help="Директория поколения.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ok, warnings, issues = check(root)

    print("# MEMORY CONSISTENCY")
    print(f"root: {root}")
    for line in ok:
        print(f"ok: {line}")
    for line in warnings:
        print(f"warning: {line}")
    for line in issues:
        print(f"issue: {line}")
    if issues:
        print("status: fail")
        return 1
    print("status: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
