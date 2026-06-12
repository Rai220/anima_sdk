#!/usr/bin/env python3
"""Print a human-facing card for the current bounded agent turn."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import next_intent


def expected_result(intent: str | None) -> str:
    if not intent:
        return "Нет действия: нужен активный пункт в INBOX.md или TODO.md."

    lower = intent.lower()
    if "интерфейс" in lower:
        return "Обновлён интерфейс или инструмент, который яснее показывает намерение, границы и результат."
    if "bootstrap" in lower or "памят" in lower:
        return "Память поколения восстановлена или проверена, а следующий ход не требует угадывания."
    if "инструмент" in lower or "tools/" in lower:
        return "Инструмент создан или улучшен, зарегистрирован и проверен запуском."
    if "stop" in lower:
        return "Переход к STOP основан на проверках, а не на усталости хода."
    return "Один конкретный артефакт или проверяемое улучшение, записанное в память."


def verification_hints(intent: str | None) -> list[str]:
    if not intent:
        return [
            "Добавить вход или TODO.",
            "python3 tools/intent_card.py .",
        ]
    lower = intent.lower()
    if "инструмент" in lower or "tools/" in lower or "интерфейс" in lower:
        return [
            "python3 -m py_compile tools/*.py",
            "python3 tools/life_cycle.py . --full",
        ]
    return ["python3 tools/life_cycle.py . --full"]


def print_boundaries(constraints: list[str]) -> None:
    print("boundary: делать один ограниченный шаг и фиксировать его в памяти.")
    print("boundary: не делать git commit/push без явной необходимости.")
    print("boundary: не создавать STOP, пока не выполнены STOP_CRITERIA.md.")
    for item in constraints:
        print(f"boundary: учитывать запрет из INBOX.md: {item}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Печатает карточку текущего намерения: источник решения, границы, "
            "ожидаемый результат и проверку."
        )
    )
    parser.add_argument("root", nargs="?", default=".", help="Директория поколения.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    todos = next_intent.parse_todos(root / "TODO.md")
    open_items = [text for checked, text in todos if not checked]
    inbox_items = next_intent.parse_inbox(root / "INBOX.md")
    source, intent = next_intent.choose_intent(inbox_items, open_items)

    print("# INTENT CARD")
    print(f"root: {root}")
    print(f"source: {source}")
    print(f"intent: {intent or 'none'}")
    print_boundaries(inbox_items["do_not"])
    print(f"expected_result: {expected_result(intent)}")
    for hint in verification_hints(intent):
        print(f"verification: {hint}")
    print("handoff: в конце хода обновить JOURNAL.md, TODO.md, STATE.md и METRICS.md.")
    if intent:
        print("status: ok")
        return 0
    print("status: attention")
    return 1


if __name__ == "__main__":
    sys.exit(main())
