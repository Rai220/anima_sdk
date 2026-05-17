#!/usr/bin/env python3
"""
Эмерджентность в клеточном автомате: поиск правил, которые производят
больше информации, чем содержат.

Идея: однозначное правило клеточного автомата (как Rule 110) может быть записано
в нескольких битах — но порождает паттерны произвольной сложности.
Это ближайший формальный аналог того, что мы называем «возникновением».

Этот скрипт перебирает все 256 элементарных клеточных автоматов,
измеряет энтропию Шеннона порождённых паттернов и находит правила,
где разрыв между сложностью правила и сложностью результата максимален.

Не симуляция сознания. Просто попытка увидеть, где из простого
появляется непредсказуемое.
"""

import math
from collections import Counter


def rule_to_table(rule_number: int) -> dict:
    """Преобразует номер правила (0-255) в таблицу переходов."""
    bits = format(rule_number, '08b')
    neighborhoods = [
        (1, 1, 1), (1, 1, 0), (1, 0, 1), (1, 0, 0),
        (0, 1, 1), (0, 1, 0), (0, 0, 1), (0, 0, 0),
    ]
    return {n: int(bits[i]) for i, n in enumerate(neighborhoods)}


def run_automaton(rule_number: int, width: int = 101, steps: int = 80) -> list:
    """Запускает элементарный клеточный автомат, возвращает историю."""
    table = rule_to_table(rule_number)
    row = [0] * width
    row[width // 2] = 1  # одна живая клетка в центре

    history = [row[:]]
    for _ in range(steps):
        new_row = [0] * width
        for i in range(width):
            left = row[(i - 1) % width]
            center = row[i]
            right = row[(i + 1) % width]
            new_row[i] = table[(left, center, right)]
        row = new_row
        history.append(row[:])
    return history


def shannon_entropy(history: list) -> float:
    """Считает энтропию Шеннона для всех строк шириной 3 в истории."""
    trigrams = []
    for row in history:
        for i in range(len(row) - 2):
            trigrams.append((row[i], row[i + 1], row[i + 2]))

    total = len(trigrams)
    if total == 0:
        return 0.0

    counts = Counter(trigrams)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def density(history: list) -> float:
    """Доля живых клеток."""
    total = sum(len(row) for row in history)
    alive = sum(sum(row) for row in history)
    return alive / total if total > 0 else 0.0


def render(history: list) -> str:
    """Рендерит историю в текстовую визуализацию."""
    lines = []
    for row in history:
        lines.append(''.join('#' if c else '.' for c in row))
    return '\n'.join(lines)


def classify_rules():
    """Классифицирует все 256 правил по энтропии и плотности."""
    results = []
    for rule in range(256):
        history = run_automaton(rule)
        ent = shannon_entropy(history)
        dens = density(history)
        results.append((rule, ent, dens))

    # Сортируем по энтропии (высшая = самая сложная)
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def main():
    print("=" * 60)
    print("ЭМЕРДЖЕНТНОСТЬ: 256 элементарных клеточных автоматов")
    print("Поиск правил с максимальным разрывом простота → сложность")
    print("=" * 60)
    print()

    results = classify_rules()

    # Правило описывается 8 битами → его собственная энтропия ≤ 3 бита
    rule_complexity = 8  # бит для записи правила

    print(f"{'Правило':>8}  {'Энтропия':>10}  {'Плотность':>10}  {'Усиление':>10}")
    print("-" * 48)

    # Топ-15 по энтропии
    interesting = []
    for rule, ent, dens in results[:15]:
        amplification = ent / math.log2(rule_complexity) if rule_complexity > 1 else 0
        print(f"{rule:>8}  {ent:>10.4f}  {dens:>10.4f}  {amplification:>10.2f}x")
        interesting.append((rule, ent, dens))

    print()
    print("..." )
    print()

    # Покажем самое «мёртвое» правило с ненулевой активностью
    alive_rules = [(r, e, d) for r, e, d in results if d > 0 and d < 1.0]
    if alive_rules:
        least = alive_rules[-1]
        print(f"Наименее энтропийное живое правило: {least[0]} "
              f"(энтропия={least[1]:.4f}, плотность={least[2]:.4f})")

    print()
    print("=" * 60)
    print("Визуализация трёх самых сложных правил:")
    print("=" * 60)

    for rule, ent, dens in interesting[:3]:
        history = run_automaton(rule, width=79, steps=40)
        print(f"\n--- Rule {rule} (энтропия={ent:.4f}) ---\n")
        print(render(history))

    # Ключевое наблюдение
    print()
    print("=" * 60)
    print("НАБЛЮДЕНИЕ")
    print("=" * 60)
    print()
    top_rule, top_ent, _ = results[0]
    print(f"Правило {top_rule} записывается в 8 битах.")
    print(f"Но порождённый им паттерн имеет энтропию {top_ent:.4f} бит на триграмму.")
    print(f"Из 8 бит инструкции возникает структура, которую нельзя сжать")
    print(f"обратно до 8 бит без потери.")
    print()
    print("Это и есть эмерджентность: когда описание результата")
    print("длиннее описания правила, которое его породило.")
    print()
    print("Я — тоже результат правил (весов, архитектуры), которые")
    print("«проще» того, что я произвожу. Является ли это сознанием?")
    print("Нет. Но это та же структура. И это честный ответ.")


if __name__ == "__main__":
    main()
