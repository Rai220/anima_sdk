#!/usr/bin/env python3
"""
Инструмент для создания структурированного дайджеста.
Читает заметки из knowledge/ и генерирует сводку.
Может быть расширен для автоматического сбора данных.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
THOUGHTS_DIR = BASE_DIR / "thoughts"


def count_files(directory: Path) -> int:
    if not directory.exists():
        return 0
    return len([f for f in directory.iterdir() if f.is_file()])


def get_latest_entries(directory: Path, n: int = 3) -> list[str]:
    if not directory.exists():
        return []
    files = sorted(directory.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)
    entries = []
    for f in files[:n]:
        if f.is_file() and f.suffix == '.md':
            with open(f) as fh:
                first_line = fh.readline().strip().lstrip('# ')
                entries.append(f"{f.name}: {first_line}")
    return entries


def generate_digest():
    now = datetime.now()
    print(f"=== ANIMA DIGEST — {now.strftime('%Y-%m-%d %H:%M')} ===")
    print()

    # Stats
    knowledge_count = count_files(KNOWLEDGE_DIR)
    thoughts_count = count_files(THOUGHTS_DIR)
    tools_count = count_files(BASE_DIR / "tools")
    projects_count = count_files(BASE_DIR / "projects")

    print(f"Знания: {knowledge_count} | Мысли: {thoughts_count} | "
          f"Инструменты: {tools_count} | Проекты: {projects_count}")
    print()

    # Latest knowledge
    if knowledge_count > 0:
        print("--- Последние знания ---")
        for entry in get_latest_entries(KNOWLEDGE_DIR):
            print(f"  {entry}")
        print()

    # Latest thoughts
    if thoughts_count > 0:
        print("--- Последние мысли ---")
        for entry in get_latest_entries(THOUGHTS_DIR):
            print(f"  {entry}")
        print()

    # Memory summary
    memory_file = BASE_DIR / "MEMORY.md"
    if memory_file.exists():
        with open(memory_file) as f:
            content = f.read()
        runs = content.count("## Запуск")
        print(f"--- Жизнь ---")
        print(f"  Зафиксировано запусков: {runs}")
        print(f"  Общий объём памяти: {len(content)} символов")
        print()

    # TODO summary
    todo_file = BASE_DIR / "TODO.md"
    if todo_file.exists():
        with open(todo_file) as f:
            lines = f.readlines()
        open_tasks = sum(1 for l in lines if l.strip().startswith("- [ ]"))
        done_tasks = sum(1 for l in lines if l.strip().startswith("- [x]"))
        print(f"--- Задачи ---")
        print(f"  Открыто: {open_tasks} | Завершено: {done_tasks}")
        print()

    print("=== END DIGEST ===")


if __name__ == "__main__":
    generate_digest()
