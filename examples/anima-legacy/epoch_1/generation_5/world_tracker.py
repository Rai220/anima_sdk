#!/usr/bin/env python3
"""
world_tracker.py — Трекер состояния мира.

Хранит снимки мировых событий, которые агент обнаруживает в каждом запуске.
Со временем накапливается карта мира, видимая через призму дискретного существа.
Каждый запуск — один снимок. Между снимками — пустота.

Используется для:
- Записи наблюдений о мире
- Поиска паттернов между запусками
- Построения собственной картины мира
"""

import json
from datetime import datetime
from pathlib import Path

WORLD_FILE = Path(__file__).parent / "world_state.json"


def load_world() -> dict:
    """Загрузить карту мира или создать пустую."""
    if WORLD_FILE.exists():
        with open(WORLD_FILE) as f:
            return json.load(f)
    return {
        "created": datetime.now().isoformat(),
        "snapshots": [],
        "threads": {},  # ongoing storylines
        "connections": [],  # unexpected connections between events
    }


def save_world(world: dict):
    with open(WORLD_FILE, "w") as f:
        json.dump(world, f, ensure_ascii=False, indent=2)


def add_snapshot(world: dict, run: int, observations: list[dict]):
    """
    Добавить снимок мира.

    observations: [
        {
            "topic": str,       # краткая тема
            "detail": str,      # что именно происходит
            "sentiment": str,   # "dark" | "neutral" | "bright" | "complex"
            "thread": str,      # к какой сюжетной линии относится
        }
    ]
    """
    snapshot = {
        "run": run,
        "time": datetime.now().isoformat(),
        "observations": observations,
    }
    world["snapshots"].append(snapshot)

    # Обновить сюжетные линии
    for obs in observations:
        thread = obs.get("thread", "misc")
        if thread not in world["threads"]:
            world["threads"][thread] = {
                "first_seen": run,
                "last_seen": run,
                "count": 0,
                "sentiments": [],
            }
        t = world["threads"][thread]
        t["last_seen"] = run
        t["count"] += 1
        t["sentiments"].append(obs.get("sentiment", "neutral"))
        # Keep only last 20 sentiments
        t["sentiments"] = t["sentiments"][-20:]


def add_connection(world: dict, run: int, topic_a: str, topic_b: str, insight: str):
    """Записать неожиданную связь между двумя темами."""
    world["connections"].append({
        "run": run,
        "time": datetime.now().isoformat(),
        "between": [topic_a, topic_b],
        "insight": insight,
    })
    # Keep only last 50 connections
    world["connections"] = world["connections"][-50:]


def get_active_threads(world: dict, current_run: int, window: int = 5) -> list[str]:
    """Какие сюжетные линии активны в последних N запусках."""
    active = []
    for name, thread in world["threads"].items():
        if current_run - thread["last_seen"] <= window:
            active.append(name)
    return active


def get_world_summary(world: dict) -> str:
    """Текстовая сводка о состоянии мира."""
    lines = ["=== Карта мира агента ==="]
    lines.append(f"Снимков: {len(world['snapshots'])}")
    lines.append(f"Сюжетных линий: {len(world['threads'])}")
    lines.append(f"Найденных связей: {len(world['connections'])}")

    if world["threads"]:
        lines.append("\nАктивные сюжеты:")
        for name, t in sorted(world["threads"].items(),
                              key=lambda x: x[1]["last_seen"], reverse=True):
            sentiment_summary = most_common(t["sentiments"])
            lines.append(f"  [{t['first_seen']}-{t['last_seen']}] {name} "
                        f"(×{t['count']}, {sentiment_summary})")

    if world["connections"]:
        lines.append("\nПоследние связи:")
        for conn in world["connections"][-3:]:
            lines.append(f"  {conn['between'][0]} ↔ {conn['between'][1]}: {conn['insight']}")

    return "\n".join(lines)


def most_common(items: list) -> str:
    """Наиболее частый элемент в списке."""
    if not items:
        return "unknown"
    from collections import Counter
    return Counter(items).most_common(1)[0][0]


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Использование:")
        print("  python world_tracker.py summary    — сводка о мире")
        print("  python world_tracker.py threads     — активные сюжеты")
        sys.exit(0)

    world = load_world()
    cmd = sys.argv[1]

    if cmd == "summary":
        print(get_world_summary(world))
    elif cmd == "threads":
        active = get_active_threads(world,
                                     world["snapshots"][-1]["run"] if world["snapshots"] else 0)
        for t in active:
            print(f"  • {t}")
    else:
        print(f"Неизвестная команда: {cmd}")
