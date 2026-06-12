#!/usr/bin/env python3
"""Build a one-screen human brief for the current agent turn."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

import intent_card
import next_intent


CORE_FILES = [
    "INBOX.md",
    "STATE.md",
    "TODO.md",
    "LESSONS.md",
    "JOURNAL.md",
    "DECISIONS.md",
    "SELF_MODEL.md",
    "WORLD_MODEL.md",
    "INTERFACE.md",
]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text()


def compact(text: str, limit: int = 220) -> str:
    value = " ".join(text.split())
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def parse_identity(state_text: str, root: Path) -> str:
    match = re.search(r"^Имя рабочей сущности:\s*(.+?)\.\s*$", state_text, re.MULTILINE)
    if match:
        return match.group(1)
    return root.name


def todo_counts(todos: list[tuple[bool, str]]) -> tuple[int, int]:
    done = sum(1 for checked, _text in todos if checked)
    open_count = sum(1 for checked, _text in todos if not checked)
    return done, open_count


def last_journal_heading(journal_text: str) -> str:
    headings = re.findall(r"^##\s+(.+?)\s*$", journal_text, flags=re.MULTILINE)
    return headings[-1] if headings else "none"


def metrics_value(metrics_text: str, metric_name: str) -> str:
    pattern = re.compile(rf"^\|\s*{re.escape(metric_name)}\s*\|.*?\|\s*(.*?)\s*\|\s*$", re.MULTILINE)
    match = pattern.search(metrics_text)
    return match.group(1) if match else "unknown"


def active_inbox_summary(inbox_items: dict[str, list[str]]) -> str:
    ordered = ["urgent", "do_not", "focus", "feedback", "question", "general"]
    active = [item for key in ordered for item in inbox_items[key]]
    if not active:
        return "empty"
    return compact(active[0])


def build_brief(root: Path) -> tuple[str, bool]:
    state = read_text(root / "STATE.md")
    journal = read_text(root / "JOURNAL.md")
    metrics = read_text(root / "METRICS.md")
    todos = next_intent.parse_todos(root / "TODO.md")
    open_items = [text for checked, text in todos if not checked]
    inbox_items = next_intent.parse_inbox(root / "INBOX.md")
    source, intent = next_intent.choose_intent(inbox_items, open_items)
    done_count, open_count = todo_counts(todos)
    missing = [name for name in CORE_FILES if not (root / name).exists()]

    lines = [
        "# TURN BRIEF",
        "",
        f"root: {root}",
        f"identity: {parse_identity(state, root)}",
        f"memory: {'ok' if not missing else 'missing ' + ', '.join(missing)}",
        f"inbox: {active_inbox_summary(inbox_items)}",
        f"todo: {done_count} done, {open_count} open",
        f"last_journal: {last_journal_heading(journal)}",
        f"tools: {metrics_value(metrics, 'Исполняемые инструменты')} executable, "
        f"{metrics_value(metrics, 'Зарегистрированные инструменты')} registered",
        "",
        "## Current Turn",
        "",
        f"source: {source}",
        f"intent: {intent or 'none'}",
        "boundary: делать один ограниченный шаг и фиксировать его в памяти.",
        "boundary: не делать git commit/push без явной необходимости.",
        "boundary: не создавать STOP, пока не выполнены STOP_CRITERIA.md.",
    ]
    for item in inbox_items["do_not"]:
        lines.append(f"boundary: учитывать запрет из INBOX.md: {item}")
    lines.extend(
        [
            f"expected_result: {intent_card.expected_result(intent)}",
            "",
            "## Verification",
            "",
        ]
    )
    lines.extend(f"- {hint}" for hint in intent_card.verification_hints(intent))
    lines.extend(
        [
            "",
            "## Handoff",
            "",
            "- В конце хода обновить `JOURNAL.md`, `TODO.md`, `STATE.md` и `METRICS.md`.",
            "- Если создан или изменён инструмент, обновить его запись в `AGENTS.md`.",
        ]
    )
    ok = bool(intent) and not missing
    lines.append(f"status: {'ok' if ok else 'attention'}")
    return "\n".join(lines) + "\n", ok


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Печатает короткий человекочитаемый briefing текущего хода. "
            "С --write также обновляет TURN_BRIEF.md."
        )
    )
    parser.add_argument("root", nargs="?", default=".", help="Директория поколения.")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Записать briefing в TURN_BRIEF.md рядом с памятью поколения.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    brief, ok = build_brief(root)
    if args.write:
        output = root / "TURN_BRIEF.md"
        output.write_text(brief, encoding="utf-8")
        print(f"updated: {output}")
    else:
        print(brief, end="")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
