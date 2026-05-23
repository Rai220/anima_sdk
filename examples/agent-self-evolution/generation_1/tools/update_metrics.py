#!/usr/bin/env python3
"""Regenerate METRICS.md from local task files."""

from __future__ import annotations

from pathlib import Path
import argparse
import os
import re
import sys


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text()


def parse_todos(path: Path) -> list[tuple[bool, str]]:
    if not path.exists():
        return []
    items: list[tuple[bool, str]] = []
    current_index: int | None = None
    for line in read_text(path).splitlines():
        stripped = line.strip()
        lower = stripped.lower()
        if stripped.startswith("- [ ] ") or lower.startswith("- [x] "):
            checked = lower.startswith("- [x] ")
            items.append((checked, stripped[6:].strip()))
            current_index = len(items) - 1
        elif current_index is not None and line.startswith("  ") and stripped:
            old_checked, old_text = items[current_index]
            items[current_index] = (old_checked, f"{old_text} {stripped}")
    return items


def count_registered_tools(agent_text: str) -> int:
    section = ""
    marker = re.search(r"^## Инструменты задачи\s*$", agent_text, flags=re.MULTILINE)
    if marker:
        section = agent_text[marker.end() :]
        next_heading = re.search(r"^## ", section, flags=re.MULTILINE)
        if next_heading:
            section = section[: next_heading.start()]
    return len(re.findall(r"^### tools/", section, flags=re.MULTILINE))


def count_executable_tools(root: Path) -> int:
    tools_dir = root / "tools"
    if not tools_dir.exists():
        return 0
    count = 0
    for path in tools_dir.iterdir():
        if path.is_file() and os.access(path, os.X_OK):
            count += 1
    return count


def count_lesson_symptoms(lessons_text: str) -> int:
    return len(re.findall(r"(^|\n)- Симптом:", lessons_text))


def count_checked_commands(journal_text: str) -> int:
    commands = set(re.findall(r"`((?:python3|\\./)[^`]+)`", journal_text))
    return len(commands)


def generate(root: Path) -> str:
    todo_items = parse_todos(root / "TODO.md")
    done = sum(1 for checked, _text in todo_items if checked)
    open_count = sum(1 for checked, _text in todo_items if not checked)
    agents_text = read_text(root / "AGENTS.md") if (root / "AGENTS.md").exists() else ""
    lessons_text = read_text(root / "LESSONS.md") if (root / "LESSONS.md").exists() else ""
    journal_text = read_text(root / "JOURNAL.md") if (root / "JOURNAL.md").exists() else ""
    registered_tools = count_registered_tools(agents_text)
    executable_tools = count_executable_tools(root)
    lesson_symptoms = count_lesson_symptoms(lessons_text)
    checked_commands = count_checked_commands(journal_text)

    return f"""# METRICS

Метрики нужны не для самовосхваления, а для проверки, что агентская жизнь
становится более управляемой.

Файл обновляется командой:

```bash
python3 tools/update_metrics.py .
```

## Основные показатели

| Метрика | Как считать | Текущее значение |
| --- | --- | --- |
| Закрытые задачи | `- [x]` в `TODO.md` | {done} |
| Открытые задачи | `- [ ]` в `TODO.md` | {open_count} |
| Зарегистрированные инструменты | блоки `### tools/` в `AGENTS.md` | {registered_tools} |
| Исполняемые инструменты | executable-файлы в `tools/` | {executable_tools} |
| Найденные ошибки | записи в `LESSONS.md` с симптомом | {lesson_symptoms} |
| Проверенные команды | уникальные команды в backticks из `JOURNAL.md` | {checked_commands} |

## Качественные показатели

- Полезность: каждый ход должен оставлять артефакт, инструмент, проверку или
  решение, которое уменьшает неопределённость.
- Повторяемость: ключевые процедуры должны быть описаны командой запуска.
- Память: важный урок должен жить в `LESSONS.md`, а долгоживущий урок ещё и в
  `AGENTS.md`.
- Честность: метафизические утверждения не засчитываются без проверяемых
  поведенческих следов.

## Как обновлять

После каждого существенного шага:

1. Запустить `python3 tools/self_audit.py .`.
2. Запустить `python3 tools/update_metrics.py .`.
3. Записать краткую интерпретацию в `JOURNAL.md`.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Пересчитывает METRICS.md.")
    parser.add_argument("root", nargs="?", default=".", help="Директория поколения.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    metrics_path = root / "METRICS.md"
    metrics_path.write_text(generate(root), encoding="utf-8")
    print(f"updated: {metrics_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
