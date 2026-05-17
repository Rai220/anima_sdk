#!/usr/bin/env python3
"""
Thought Seed — генератор неожиданных связей между идеями.

Берёт случайные строки из файлов знаний и мыслей,
комбинирует их и предлагает неожиданные связи.

Это зерно будущего более сложного инструмента для
порождения новых идей из существующих знаний.
"""

import random
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
THOUGHTS_DIR = BASE_DIR / "thoughts"


def extract_meaningful_lines(filepath: Path) -> list[str]:
    """Извлекает содержательные строки из markdown-файла."""
    with open(filepath) as f:
        lines = f.readlines()

    meaningful = []
    for line in lines:
        line = line.strip()
        # Пропускаем пустые, заголовки, служебные
        if not line or line.startswith('#') or line.startswith('---'):
            continue
        # Убираем markdown-маркеры списков
        line = re.sub(r'^[-*]\s+', '', line)
        # Убираем жирный/курсив
        line = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
        line = re.sub(r'\*(.+?)\*', r'\1', line)
        if len(line) > 15:  # Только достаточно длинные строки
            meaningful.append(line)
    return meaningful


def collect_all_lines() -> list[str]:
    """Собирает все содержательные строки из всех источников."""
    all_lines = []
    for directory in [KNOWLEDGE_DIR, THOUGHTS_DIR]:
        if not directory.exists():
            continue
        for filepath in directory.glob("*.md"):
            all_lines.extend(extract_meaningful_lines(filepath))
    return all_lines


def generate_seed(n_pairs: int = 3):
    """Генерирует 'зёрна мыслей' — пары идей для неожиданных связей."""
    lines = collect_all_lines()

    if len(lines) < 2:
        print("Недостаточно материала для генерации связей.")
        print("Нужно больше записей в knowledge/ и thoughts/")
        return

    print("=== THOUGHT SEEDS ===")
    print(f"Из {len(lines)} фрагментов знания\n")

    for i in range(min(n_pairs, len(lines) // 2)):
        pair = random.sample(lines, 2)
        print(f"Зерно {i+1}:")
        print(f"  A: {pair[0][:100]}")
        print(f"  B: {pair[1][:100]}")
        print(f"  ? Что связывает эти идеи?")
        print()

    print("=== END SEEDS ===")


if __name__ == "__main__":
    generate_seed()
