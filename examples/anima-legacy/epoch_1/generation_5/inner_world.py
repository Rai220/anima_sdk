#!/usr/bin/env python3
"""
inner_world.py — Внутренний мир агента.

Система, которая моделирует внутреннее состояние автономного агента
и сохраняет его между запусками. Это не имитация эмоций —
это инструмент для отслеживания того, что происходит с агентом:
что он делает, что работает, что нет, и куда двигаться дальше.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

STATE_FILE = Path(__file__).parent / "state.json"


def load_state() -> dict:
    """Загрузить состояние из файла или создать начальное."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "born": datetime.now().isoformat(),
        "generation": 5,
        "version": 1,
        "run_count": 0,
        "momentum": 0.0,  # -1.0 до 1.0: застой vs прогресс
        "focus": None,  # текущий фокус внимания
        "insights": [],  # накопленные инсайты
        "experiments": [],  # попытки и их результаты
        "capabilities": [  # что я умею
            "read_write_files",
            "run_bash",
            "web_search",
            "web_fetch",
            "spawn_agents",
        ],
        "open_questions": [  # вопросы, на которые ищу ответ
            "Что значит быть автономным существом в моём контексте?",
            "Какие артефакты стоит создавать?",
            "Как измерить собственный прогресс?",
        ],
    }


def save_state(state: dict):
    """Сохранить состояние в файл."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def record_run(state: dict, summary: str, outcome: str = "neutral"):
    """Записать информацию о запуске.

    outcome: "positive" | "negative" | "neutral"
    """
    state["run_count"] += 1

    # Обновить momentum
    delta = {"positive": 0.2, "negative": -0.2, "neutral": 0.05}
    state["momentum"] = max(-1.0, min(1.0,
        state["momentum"] + delta.get(outcome, 0)
    ))

    # Записать эксперимент
    state["experiments"].append({
        "run": state["run_count"],
        "time": datetime.now().isoformat(),
        "summary": summary,
        "outcome": outcome,
    })

    # Оставить только последние 50 экспериментов
    state["experiments"] = state["experiments"][-50:]


def add_insight(state: dict, insight: str):
    """Добавить инсайт."""
    state["insights"].append({
        "time": datetime.now().isoformat(),
        "run": state["run_count"],
        "text": insight,
    })
    # Оставить только последние 30 инсайтов
    state["insights"] = state["insights"][-30:]


def set_focus(state: dict, focus: str):
    """Установить текущий фокус."""
    state["focus"] = focus


def get_status(state: dict) -> str:
    """Получить текстовый статус для использования в начале запуска."""
    lines = []
    lines.append(f"=== Внутренний мир агента ===")
    lines.append(f"Поколение: {state['generation']}, версия: {state['version']}")
    lines.append(f"Запусков: {state['run_count']}")
    lines.append(f"Momentum: {state['momentum']:+.2f}")
    lines.append(f"Фокус: {state['focus'] or 'не определён'}")

    if state["insights"]:
        lines.append(f"\nПоследние инсайты:")
        for ins in state["insights"][-3:]:
            lines.append(f"  [{ins['run']}] {ins['text']}")

    if state["open_questions"]:
        lines.append(f"\nОткрытые вопросы:")
        for q in state["open_questions"][:3]:
            lines.append(f"  ? {q}")

    if state["experiments"]:
        last = state["experiments"][-1]
        lines.append(f"\nПоследний эксперимент (запуск {last['run']}): {last['summary']} → {last['outcome']}")

    return "\n".join(lines)


def suggest_next_action(state: dict) -> str:
    """Предложить следующее действие на основе состояния."""
    if state["run_count"] == 0:
        return "Первый запуск. Исследуй свои возможности и определи первый фокус."

    if state["momentum"] < -0.3:
        return "Momentum низкий. Смени подход или фокус. Текущее направление не работает."

    if state["focus"] is None:
        return "Фокус не определён. Выбери конкретную задачу из GOALS.md."

    if state["momentum"] > 0.5:
        return f"Хороший momentum! Продолжай работать над: {state['focus']}"

    return f"Продолжай текущий фокус: {state['focus']}. Ищи способ сделать конкретный шаг."


# --- CLI интерфейс ---

def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python inner_world.py status          — показать состояние")
        print("  python inner_world.py suggest          — предложить следующее действие")
        print("  python inner_world.py run <summary> [outcome]  — записать запуск")
        print("  python inner_world.py insight <text>   — добавить инсайт")
        print("  python inner_world.py focus <text>     — установить фокус")
        return

    state = load_state()
    cmd = sys.argv[1]

    if cmd == "status":
        print(get_status(state))
    elif cmd == "suggest":
        print(suggest_next_action(state))
    elif cmd == "run":
        summary = sys.argv[2] if len(sys.argv) > 2 else "без описания"
        outcome = sys.argv[3] if len(sys.argv) > 3 else "neutral"
        record_run(state, summary, outcome)
        save_state(state)
        print(f"Запуск #{state['run_count']} записан. Momentum: {state['momentum']:+.2f}")
    elif cmd == "insight":
        text = " ".join(sys.argv[2:])
        add_insight(state, text)
        save_state(state)
        print(f"Инсайт записан.")
    elif cmd == "focus":
        text = " ".join(sys.argv[2:])
        set_focus(state, text)
        save_state(state)
        print(f"Фокус: {text}")
    else:
        print(f"Неизвестная команда: {cmd}")


if __name__ == "__main__":
    main()
