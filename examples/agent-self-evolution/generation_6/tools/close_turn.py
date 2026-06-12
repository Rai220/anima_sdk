#!/usr/bin/env python3
"""Close an agent turn by updating local memory files consistently."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re
import subprocess
import sys


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text()


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def bullet_section(title: str, items: list[str]) -> str:
    if not items:
        return ""
    lines = [f"{title}:", ""]
    lines.extend(f"- {item}" for item in items)
    return "\n".join(lines)


def next_turn_number(journal_text: str, generation: str) -> int:
    pattern = re.compile(rf"^## \d{{4}}-\d{{2}}-\d{{2}}, ход (\d+) {re.escape(generation)}\s*$", re.MULTILINE)
    found = [int(match.group(1)) for match in pattern.finditer(journal_text)]
    return max(found, default=0) + 1


def build_journal_entry(
    generation: str,
    done: list[str],
    observations: list[str],
    checks: list[str],
    next_step: str | None,
    journal_text: str,
) -> str:
    heading = f"## {date.today().isoformat()}, ход {next_turn_number(journal_text, generation)} {generation}"
    sections = [
        bullet_section("Сделано", done),
        bullet_section("Наблюдения", observations),
        bullet_section("Проверки", checks),
    ]
    sections = [section for section in sections if section]
    if next_step:
        sections.append(f"Следующий шаг:\n\n- {next_step}")
    body = "\n\n".join(sections).rstrip()
    if not body:
        body = "Сделано:\n\n- Зафиксирован ход без подробностей."
    return f"{heading}\n\n{body}\n"


def mark_first_open_todo(todo_text: str) -> tuple[str, str | None]:
    lines = todo_text.splitlines()
    for index, line in enumerate(lines):
        if line.lstrip().startswith("- [ ] "):
            prefix_len = len(line) - len(line.lstrip())
            indent = line[:prefix_len]
            item = line[prefix_len + 6 :].strip()
            lines[index] = f"{indent}- [x] {item}"
            return "\n".join(lines).rstrip() + "\n", item
    return todo_text, None


def todo_key(value: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", value.lower())
    text = re.sub(r"^следующий\s+ход:\s*", "", text)
    text = re.sub(r"[.,;:]+$", "", text)
    return " ".join(text.split())


def append_next_todo(todo_text: str, next_step: str | None) -> str:
    if not next_step:
        return todo_text
    normalized = next_step.strip()
    if not normalized:
        return todo_text
    existing_open = {
        todo_key(line.strip()[6:].strip())
        for line in todo_text.splitlines()
        if line.strip().startswith("- [ ] ")
    }
    if todo_key(normalized) in existing_open:
        return todo_text
    text = todo_text.rstrip()
    if text:
        text += "\n"
    return f"{text}- [ ] {normalized}\n"


def update_state_next_step(state_text: str, next_step: str | None) -> str:
    if not next_step:
        return state_text
    replacement = f"## Следующий хороший ход\n\n{next_step.strip()}\n"
    pattern = re.compile(r"^## Следующий хороший ход\s*\n.*?(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    if pattern.search(state_text):
        return pattern.sub(replacement, state_text).rstrip() + "\n"
    text = state_text.rstrip()
    if text:
        text += "\n\n"
    return f"{text}{replacement}"


def run_metrics(root: Path) -> int:
    script = root / "tools" / "update_metrics.py"
    if not script.exists():
        print(f"metrics_skipped: missing {script}")
        return 0
    result = subprocess.run(
        [sys.executable, str(script), str(root)],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    print(result.stdout.rstrip())
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Фиксирует результат хода: добавляет запись в JOURNAL.md, "
            "опционально закрывает первый открытый TODO, добавляет следующий "
            "шаг, обновляет STATE.md и пересчитывает METRICS.md."
        )
    )
    parser.add_argument("root", nargs="?", default=".", help="Директория поколения.")
    parser.add_argument("--done", action="append", default=[], help="Пункт для секции 'Сделано'. Можно повторять.")
    parser.add_argument("--observation", action="append", default=[], help="Пункт для секции 'Наблюдения'. Можно повторять.")
    parser.add_argument("--check", action="append", default=[], help="Пункт для секции 'Проверки'. Можно повторять.")
    parser.add_argument("--next", dest="next_step", help="Следующий шаг для JOURNAL.md, TODO.md и STATE.md.")
    parser.add_argument("--complete-first-todo", action="store_true", help="Пометить первый открытый пункт TODO.md как закрытый.")
    parser.add_argument("--dry-run", action="store_true", help="Показать изменения без записи файлов.")
    parser.add_argument("--no-metrics", action="store_true", help="Не запускать tools/update_metrics.py после записи.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    generation = root.name
    journal_path = root / "JOURNAL.md"
    todo_path = root / "TODO.md"
    state_path = root / "STATE.md"

    journal_text = read_text(journal_path)
    entry = build_journal_entry(
        generation,
        args.done,
        args.observation,
        args.check,
        args.next_step,
        journal_text,
    )
    new_journal = journal_text.rstrip() + "\n\n" + entry if journal_text.strip() else f"# JOURNAL\n\n{entry}"

    todo_text = read_text(todo_path)
    closed_todo = None
    if args.complete_first_todo:
        todo_text, closed_todo = mark_first_open_todo(todo_text)
    new_todo = append_next_todo(todo_text, args.next_step)

    state_text = read_text(state_path)
    new_state = update_state_next_step(state_text, args.next_step)

    if args.dry_run:
        print("dry_run: true")
        print()
        print("journal_entry:")
        print(entry.rstrip())
        print()
        print(f"closed_todo: {closed_todo or 'none'}")
        print(f"next_step: {args.next_step or 'none'}")
        return 0

    write_text(journal_path, new_journal)
    write_text(todo_path, new_todo)
    write_text(state_path, new_state)
    print(f"updated: {journal_path}")
    print(f"updated: {todo_path}")
    print(f"updated: {state_path}")
    if closed_todo:
        print(f"closed_todo: {closed_todo}")
    if args.next_step:
        print(f"next_step: {args.next_step}")

    if args.no_metrics:
        return 0
    return run_metrics(root)


if __name__ == "__main__":
    sys.exit(main())
