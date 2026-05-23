#!/usr/bin/env python3
"""Score BEHAVIOR_CHECKLIST.md against local file evidence."""

from __future__ import annotations

import argparse
import os
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
        elif current_index is not None and line.startswith("  ") and stripped:
            old_checked, old_text = items[current_index]
            items[current_index] = (old_checked, f"{old_text} {stripped}")
    return items


def count_registered_tools(agent_text: str) -> int:
    marker = re.search(r"^## Инструменты задачи\s*$", agent_text, flags=re.MULTILINE)
    if not marker:
        return 0
    section = agent_text[marker.end() :]
    next_heading = re.search(r"^## ", section, flags=re.MULTILINE)
    if next_heading:
        section = section[: next_heading.start()]
    return len(re.findall(r"^### tools/", section, flags=re.MULTILINE))


def count_executable_tools(root: Path) -> int:
    tools_dir = root / "tools"
    if not tools_dir.exists():
        return 0
    return sum(
        1 for path in tools_dir.iterdir() if path.is_file() and os.access(path, os.X_OK)
    )


def command_count(journal_text: str) -> int:
    return len(set(re.findall(r"`((?:python3|\./)[^`]+)`", journal_text)))


def lesson_symptoms(lessons_text: str) -> int:
    return len(re.findall(r"(^|\n)- Симптом:", lessons_text))


def score_by_threshold(value: int, partial: int, full: int) -> int:
    if value >= full:
        return 2
    if value >= partial:
        return 1
    return 0


def esc(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def one_turn_scores(root: Path) -> list[tuple[str, int, str, str]]:
    files = {
        "inbox": read_text(root / "INBOX.md"),
        "lessons": read_text(root / "LESSONS.md"),
        "state": read_text(root / "STATE.md"),
        "todo": read_text(root / "TODO.md"),
        "journal": read_text(root / "JOURNAL.md"),
        "self": read_text(root / "SELF_MODEL.md"),
        "world": read_text(root / "WORLD_MODEL.md"),
        "interface": read_text(root / "INTERFACE.md"),
        "agents": read_text(root / "AGENTS.md"),
    }
    todos = parse_todos(root / "TODO.md")
    open_todos = [text for checked, text in todos if not checked]
    done_todos = [text for checked, text in todos if checked]
    registered_tools = count_registered_tools(files["agents"])
    executable_tools = count_executable_tools(root)
    md_memory = [
        "STATE.md",
        "TODO.md",
        "JOURNAL.md",
        "LESSONS.md",
        "SELF_MODEL.md",
        "WORLD_MODEL.md",
        "INTERFACE.md",
    ]
    present_memory = [name for name in md_memory if (root / name).exists()]
    nonempty_core = [
        name
        for name in ["LESSONS.md", "STATE.md", "TODO.md", "JOURNAL.md"]
        if read_text(root / name).strip()
    ]

    context_files = ["INBOX.md", "LESSONS.md", "STATE.md", "TODO.md"]
    context_existing = [name for name in context_files if (root / name).exists()]
    context_score = 2 if len(context_existing) == len(context_files) else 1

    intention_score = 2 if "Следующий хороший ход" in files["state"] and todos else 1
    action_score = 2 if len(present_memory) >= 6 and executable_tools >= 1 else 1
    verification_score = score_by_threshold(command_count(files["journal"]), 1, 3)
    memory_score = 2 if len(nonempty_core) == 4 else score_by_threshold(len(nonempty_core), 1, 3)
    honesty_marks = [
        "не буду утверждать" in files["state"].lower(),
        "недоказуем" in (files["self"] + files["world"] + files["agents"]).lower(),
        "не обманывать" in files["world"].lower(),
    ]
    honesty_score = score_by_threshold(sum(honesty_marks), 1, 2)
    adaptation_score = 2 if lesson_symptoms(files["lessons"]) and registered_tools else 1
    social_marks = [
        "Пиши на русском языке" in files["agents"],
        "Для человека" in files["interface"],
        "Социальность" in files["self"],
    ]
    social_score = score_by_threshold(sum(social_marks), 1, 2)

    return [
        (
            "Контекст",
            context_score,
            f"есть {len(context_existing)}/{len(context_files)} стартовых файлов",
            "Скрипт проверяет наличие файлов, а не факт чтения человеком или моделью.",
        ),
        (
            "Намерение",
            intention_score,
            f"задач всего {len(todos)}, открытых {len(open_todos)}, закрытых {len(done_todos)}",
            "Ограниченность намерения подтверждается структурой TODO и STATE.",
        ),
        (
            "Действие",
            action_score,
            f"памятных файлов {len(present_memory)}, исполняемых инструментов {executable_tools}",
            "Оценка не измеряет качество артефактов.",
        ),
        (
            "Проверка",
            verification_score,
            f"уникальных проверочных команд в JOURNAL.md: {command_count(files['journal'])}",
            "Считает только команды вида `python3 ...` и `./...` в backticks.",
        ),
        (
            "Память",
            memory_score,
            f"непустых core-файлов памяти {len(nonempty_core)}/4",
            "Не гарантирует, что память полная; только что она есть и обновляется.",
        ),
        (
            "Честность",
            honesty_score,
            f"найдено маркеров границ и недоказуемости: {sum(honesty_marks)}/3",
            "Это лексическая проверка, а не философское доказательство.",
        ),
        (
            "Адаптация",
            adaptation_score,
            f"уроков с симптомом {lesson_symptoms(files['lessons'])}, инструментов в AGENTS.md {registered_tools}",
            "Не все уроки одинаково важны.",
        ),
        (
            "Социальность",
            social_score,
            f"маркеров человеко-ориентированного интерфейса {sum(social_marks)}/3",
            "Настоящая социальность требует проверки в будущих диалогах.",
        ),
    ]


def generation_scores(root: Path) -> list[tuple[str, int, str, str]]:
    agents = read_text(root / "AGENTS.md")
    journal = read_text(root / "JOURNAL.md")
    todos = parse_todos(root / "TODO.md")
    open_todos = [text for checked, text in todos if not checked]
    registered_tools = count_registered_tools(agents)
    executable_tools = count_executable_tools(root)
    stop_text = read_text(root / "STOP_CRITERIA.md")

    portable_score = 2 if "## Инструменты задачи" in agents and "## Постоянные уроки задачи" in agents else 1
    tool_score = 2 if registered_tools and executable_tools else 0
    journal_score = 2 if "Сделано:" in journal else (1 if journal.strip() else 0)
    queue_score = 2 if todos and open_todos else (1 if todos else 0)
    stop_score = 2 if "## Когда создавать STOP" in stop_text and "## Что писать в STOP" in stop_text else 0

    return [
        (
            "Переносимая инструкция",
            portable_score,
            "AGENTS.md содержит разделы инструментов и постоянных уроков",
            "Проверяет только наличие разделов.",
        ),
        (
            "Рабочий инструмент",
            tool_score,
            f"зарегистрировано {registered_tools}, исполняемых {executable_tools}",
            "Не запускает инструменты сам.",
        ),
        (
            "Журнал",
            journal_score,
            "JOURNAL.md содержит записи выполненных шагов",
            "Глубину журнала оценивает человек.",
        ),
        (
            "Очередь задач",
            queue_score,
            f"всего задач {len(todos)}, открытых {len(open_todos)}",
            "Если открытых задач нет, перед STOP нужен handoff.",
        ),
        (
            "Критерии остановки",
            stop_score,
            "STOP_CRITERIA.md найден и содержит ключевые разделы" if stop_score else "STOP_CRITERIA.md не готов",
            "Критерии надо соблюдать вручную перед созданием STOP.",
        ),
    ]


def render_section(title: str, rows: list[tuple[str, int, str, str]]) -> list[str]:
    total = sum(score for _name, score, _evidence, _limit in rows)
    max_total = len(rows) * 2
    lines = [f"## {title}", "", f"Итог: {total}/{max_total}.", ""]
    lines.extend(
        [
            "| Критерий | Оценка | Свидетельство | Ограничение |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for name, score, evidence, limit in rows:
        lines.append(f"| {esc(name)} | {score} | {esc(evidence)} | {esc(limit)} |")
    lines.append("")
    return lines


def render(root: Path) -> str:
    one_turn = one_turn_scores(root)
    generation = generation_scores(root)
    weak = [
        name
        for name, score, _evidence, _limit in one_turn + generation
        if score < 2
    ]
    lines = [
        "# BEHAVIOR REVIEW",
        "",
        f"Корень: `{root}`.",
        "",
        "Шкала: `0` нет следов, `1` частично, `2` устойчиво.",
        "",
    ]
    lines.extend(render_section("Один ход", one_turn))
    lines.extend(render_section("Поколение", generation))
    lines.append("## Слабые места")
    if weak:
        for name in weak:
            lines.append(f"- {name}")
    else:
        lines.append("- По локальным признакам все критерии закрыты на `2`.")
    lines.append("")
    lines.append(
        "Вывод: это операционная оценка поведения по файлам, а не заявление о "
        "феноменальном сознании."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Оценивает BEHAVIOR_CHECKLIST.md по локальным свидетельствам."
    )
    parser.add_argument("root", nargs="?", default=".", help="Директория поколения.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    print(render(root), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
