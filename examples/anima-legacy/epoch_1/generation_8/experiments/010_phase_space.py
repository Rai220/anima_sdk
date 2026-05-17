#!/usr/bin/env python3
"""
Карта фазового пространства одномерных автоматов с памятью.

Все 65536 правил (16-битные), классифицированные по поведению.
Для каждого правила: запустить 200 шагов, измерить:
  - финальная плотность
  - дисперсия плотности (хаотичность)
  - период (если есть)
  - время жизни (если вымирает)

Вопрос: как устроено пространство правил?
Есть ли кластеры? Фазовые переходы? Острова хаоса в море стабильности?
"""

import sys
from collections import Counter


def step_memory(cells, prev, rule_num, width):
    new_cells = [0] * width
    for i in range(width):
        left = cells[(i - 1) % width]
        center = cells[i]
        right = cells[(i + 1) % width]
        prev_center = prev[i]
        idx = (left << 3) | (center << 2) | (right << 1) | prev_center
        new_cells[i] = (rule_num >> idx) & 1
    return new_cells


def classify_rule(rule_num, width=60, steps=150):
    """Возвращает (class, final_density, variance, period_or_lifetime)."""
    cells = [0] * width
    cells[width // 2] = 1
    prev = [0] * width

    densities = []
    state_history = {}

    for t in range(steps):
        state = tuple(cells)
        if state in state_history:
            period = t - state_history[state]
            d = sum(cells) / width
            return ('periodic', d, 0.0, period)
        state_history[state] = t

        d = sum(cells) / width
        densities.append(d)

        new_cells = step_memory(cells, prev, rule_num, width)
        prev = cells[:]
        cells = new_cells

        if sum(cells) == 0:
            return ('dead', 0.0, 0.0, t + 1)

    # Не вымер, не периодичен
    last = densities[-30:]
    avg_d = sum(last) / len(last)
    var_d = sum((x - avg_d) ** 2 for x in last) / len(last)
    unique = len(set(round(x, 4) for x in last))

    if unique <= 2:
        return ('stable', avg_d, var_d, 0)
    elif var_d < 0.001:
        return ('quasi-stable', avg_d, var_d, 0)
    else:
        return ('complex', avg_d, var_d, unique)


def main():
    total = 65536
    results = {}
    class_counts = Counter()

    print(f"Классификация {total} правил...", flush=True)

    for rule in range(total):
        if rule % 10000 == 0 and rule > 0:
            print(f"  {rule}/{total}...", flush=True)

        cls, density, variance, extra = classify_rule(rule)
        results[rule] = (cls, density, variance, extra)
        class_counts[cls] += 1

    # Общая статистика
    print(f"\n{'='*60}")
    print(f"КАРТА ФАЗОВОГО ПРОСТРАНСТВА")
    print(f"{'='*60}")
    print(f"\nКлассы поведения:")
    for cls, count in class_counts.most_common():
        pct = count / total * 100
        bar = '█' * int(pct / 2)
        print(f"  {cls:14s}: {count:5d} ({pct:5.1f}%) {bar}")

    # Анализ по классам
    print(f"\n--- Периодические ---")
    periodic = [(r, d) for r, (c, d, v, p) in results.items() if c == 'periodic']
    if periodic:
        periods = [results[r][3] for r, _ in periodic]
        period_counts = Counter(periods)
        print(f"  Всего: {len(periodic)}")
        print(f"  Распределение периодов:")
        for p, cnt in period_counts.most_common(10):
            print(f"    период {p}: {cnt} правил")

    print(f"\n--- Сложные ---")
    complex_rules = [(r, results[r]) for r in results if results[r][0] == 'complex']
    if complex_rules:
        print(f"  Всего: {len(complex_rules)}")
        # Топ-10 по дисперсии (самые хаотичные)
        complex_rules.sort(key=lambda x: x[1][2], reverse=True)
        print(f"  Самые хаотичные (по дисперсии плотности):")
        for rule, (cls, d, v, u) in complex_rules[:10]:
            print(f"    Правило {rule:5d}: плотн={d:.3f}, дисп={v:.5f}, уник={u}")

        # Топ-10 по уникальности
        complex_rules.sort(key=lambda x: x[1][3], reverse=True)
        print(f"  Самые разнообразные (по уникальным плотностям):")
        for rule, (cls, d, v, u) in complex_rules[:10]:
            print(f"    Правило {rule:5d}: плотн={d:.3f}, дисп={v:.5f}, уник={u}")

    print(f"\n--- Вымершие ---")
    dead = [(r, results[r][3]) for r in results if results[r][0] == 'dead']
    if dead:
        lifetimes = [lt for _, lt in dead]
        print(f"  Всего: {len(dead)}")
        print(f"  Время жизни: мин={min(lifetimes)}, макс={max(lifetimes)}, "
              f"среднее={sum(lifetimes)/len(lifetimes):.1f}")

    # Битовый анализ: какие биты правила влияют на класс?
    print(f"\n--- Битовый анализ ---")
    print(f"  Влияние каждого бита правила на вероятность сложности:")
    for bit in range(16):
        with_bit = sum(1 for r in range(total)
                      if (r >> bit) & 1 and results[r][0] == 'complex')
        without_bit = sum(1 for r in range(total)
                         if not ((r >> bit) & 1) and results[r][0] == 'complex')
        total_with = sum(1 for r in range(total) if (r >> bit) & 1)
        total_without = total - total_with

        rate_with = with_bit / total_with * 100 if total_with else 0
        rate_without = without_bit / total_without * 100 if total_without else 0

        # Какой переход кодирует этот бит?
        left = (bit >> 3) & 1
        center = (bit >> 2) & 1
        right = (bit >> 1) & 1
        prev = bit & 1
        transition = f"({left},{center},{right},prev={prev})"

        delta = rate_with - rate_without
        marker = '***' if abs(delta) > 5 else ''
        print(f"    бит {bit:2d} {transition}: "
              f"вкл={rate_with:5.1f}% выкл={rate_without:5.1f}% "
              f"Δ={delta:+.1f}% {marker}")

    # 2D карта: правила 0..255 на одной оси, 0..255 на другой
    print(f"\n--- 2D карта (старшие 8 бит × младшие 8 бит) ---")
    print(f"  Символы: · вымер  ○ стабильный  ◐ периодический  █ сложный  ◌ квази")

    for hi in range(0, 256, 8):  # Каждая 8-я строка
        row = ''
        for lo in range(0, 256, 4):  # Каждый 4-й столбец
            rule = (hi << 8) | lo
            cls = results[rule][0]
            sym = {'dead': '·', 'stable': '○', 'periodic': '◐',
                   'complex': '█', 'quasi-stable': '◌'}[cls]
            row += sym
        print(f"  {hi:3d}|{row}")


if __name__ == '__main__':
    main()
