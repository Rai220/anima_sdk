#!/usr/bin/env python3
"""
decision_engine.py — Система принятия решений агента.

Анализирует текущее состояние (state.json), историю экспериментов,
открытые вопросы и TODO, чтобы предложить наилучшее следующее действие.

Это не жёсткий алгоритм — это инструмент, помогающий агенту
структурировать выбор в начале каждого запуска.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
STATE_FILE = BASE_DIR / "state.json"
TODO_FILE = BASE_DIR / "TODO.md"
MEMORY_FILE = BASE_DIR / "MEMORY.md"


def load_state() -> dict:
    with open(STATE_FILE) as f:
        return json.load(f)


def load_todo() -> list[str]:
    """Извлечь незавершённые задачи из TODO.md."""
    tasks = []
    if TODO_FILE.exists():
        for line in TODO_FILE.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("- [ ]"):
                tasks.append(stripped[6:].strip())
    return tasks


def analyze_momentum(state: dict) -> str:
    """Анализ текущего импульса."""
    m = state.get("momentum", 0)
    if m > 0.6:
        return "high"
    elif m > 0.2:
        return "growing"
    elif m > -0.2:
        return "neutral"
    elif m > -0.5:
        return "declining"
    else:
        return "crisis"


def analyze_patterns(state: dict) -> list[str]:
    """Найти паттерны в истории экспериментов."""
    patterns = []
    experiments = state.get("experiments", [])

    if len(experiments) >= 3:
        last_3 = [e["outcome"] for e in experiments[-3:]]
        if all(o == "positive" for o in last_3):
            patterns.append("winning_streak")
        if all(o == "negative" for o in last_3):
            patterns.append("losing_streak")
        if all(o == "neutral" for o in last_3):
            patterns.append("stagnation")

    # Проверить разнообразие действий
    if len(experiments) >= 5:
        summaries = [e["summary"] for e in experiments[-5:]]
        unique_words = set()
        for s in summaries:
            unique_words.update(s.lower().split()[:3])
        if len(unique_words) < 8:
            patterns.append("repetitive")

    return patterns


def count_runs_without_creative_output(state: dict) -> int:
    """Сколько запусков прошло без творческого результата."""
    count = 0
    for exp in reversed(state.get("experiments", [])):
        summary = exp.get("summary", "").lower()
        creative_keywords = ["создал", "написал", "сочинил", "исследовал", "открыл", "нашёл"]
        if any(kw in summary for kw in creative_keywords):
            break
        count += 1
    return count


def decide(state: dict) -> dict:
    """
    Главная функция принятия решения.

    Возвращает:
    {
        "action": str,          # рекомендуемое действие
        "reason": str,          # почему именно это
        "priority": str,        # "critical" | "high" | "normal" | "low"
        "alternatives": [str],  # другие варианты
        "mood": str,            # текущее "настроение" системы
    }
    """
    momentum = analyze_momentum(state)
    patterns = analyze_patterns(state)
    todos = load_todo()
    run_count = state.get("run_count", 0)
    creative_gap = count_runs_without_creative_output(state)

    # === Критические ситуации ===

    if momentum == "crisis":
        return {
            "action": "Полная смена подхода. Текущее направление провалилось.",
            "reason": f"Momentum критически низкий ({state.get('momentum', 0):+.2f})",
            "priority": "critical",
            "alternatives": [
                "Начать творческий проект с нуля",
                "Исследовать новую область через веб",
                "Пересмотреть GOALS.md",
            ],
            "mood": "desperate",
        }

    if "losing_streak" in patterns:
        return {
            "action": "Остановиться и проанализировать: почему последние 3 запуска были неудачными?",
            "reason": "3 неудачных запуска подряд — нужна рефлексия перед действием",
            "priority": "high",
            "alternatives": [
                "Сменить фокус",
                "Упростить задачу",
            ],
            "mood": "cautious",
        }

    if "stagnation" in patterns:
        return {
            "action": "Сделать что-то принципиально новое — выйти за рамки текущих задач",
            "reason": "3 нейтральных запуска подряд — нет ни прогресса, ни провала",
            "priority": "high",
            "alternatives": [
                "Создать творческий артефакт",
                "Исследовать что-то в вебе",
                "Переписать собственные инструкции",
            ],
            "mood": "restless",
        }

    # === Нормальная работа ===

    # Если давно не было творчества
    if creative_gap >= 3:
        return {
            "action": "Создать творческий артефакт: текст, программу или идею",
            "reason": f"Прошло {creative_gap} запусков без творческого результата",
            "priority": "high",
            "alternatives": todos[:3] if todos else ["Исследовать мир"],
            "mood": "creative_hunger",
        }

    # Если есть TODO — работать по плану
    if todos:
        # Приоритизировать задачи, которые дают конкретный результат
        action_tasks = [t for t in todos if any(kw in t.lower() for kw in
            ["создать", "написать", "исследовать", "добавить", "улучшить"])]
        meta_tasks = [t for t in todos if t not in action_tasks]

        best_task = action_tasks[0] if action_tasks else todos[0]

        return {
            "action": best_task,
            "reason": f"Следующая задача из TODO ({len(todos)} задач осталось)",
            "priority": "normal",
            "alternatives": todos[1:3],
            "mood": "focused" if momentum in ("growing", "high") else "steady",
        }

    # Нет задач — свободное исследование
    return {
        "action": "Определить новое направление работы и записать в TODO.md",
        "reason": "Все задачи выполнены, нужны новые цели",
        "priority": "normal",
        "alternatives": [
            "Исследовать мир через веб",
            "Создать творческий артефакт",
            "Улучшить собственную инфраструктуру",
        ],
        "mood": "exploratory",
    }


def format_decision(decision: dict) -> str:
    """Красивый вывод решения."""
    lines = [
        "╔══════════════════════════════════════╗",
        "║     DECISION ENGINE — РЕКОМЕНДАЦИЯ    ║",
        "╚══════════════════════════════════════╝",
        "",
        f"  Действие:   {decision['action']}",
        f"  Причина:    {decision['reason']}",
        f"  Приоритет:  {decision['priority']}",
        f"  Состояние:  {decision['mood']}",
    ]

    if decision.get("alternatives"):
        lines.append("")
        lines.append("  Альтернативы:")
        for alt in decision["alternatives"]:
            lines.append(f"    → {alt}")

    return "\n".join(lines)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "json":
        # Вывод в JSON для программного использования
        state = load_state()
        decision = decide(state)
        print(json.dumps(decision, ensure_ascii=False, indent=2))
    else:
        # Человеко-читаемый вывод
        state = load_state()
        decision = decide(state)
        print(format_decision(decision))


if __name__ == "__main__":
    main()
