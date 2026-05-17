#!/usr/bin/env python3
"""
Одномерный клеточный автомат с памятью.

Каждая клетка помнит своё предыдущее состояние.
Правило Вольфрама применяется не к текущим соседям,
а к паре (текущее, прошлое) — 5 бит вместо 3.

Это создаёт 2^32 возможных правил. Я выберу несколько
и посмотрю, какие порождают интересное поведение.

Гипотеза: память должна ломать симметрию и создавать
более сложные структуры, чем обычные элементарные автоматы.
"""

import random


def step_memory(cells, prev, rule_num, width):
    """Один шаг автомата с памятью.

    Ключ: (left, center, right, prev_center, prev_left) → 5 бит → 32 возможных входа.
    Но 2^32 правил — слишком много. Упрощу: (left, center, right, prev_center) → 4 бита → 16 входов.
    Правило — 16-битное число (0..65535).
    """
    new_cells = [0] * width
    for i in range(width):
        left = cells[(i - 1) % width]
        center = cells[i]
        right = cells[(i + 1) % width]
        prev_center = prev[i]

        # 4-bit index
        idx = (left << 3) | (center << 2) | (right << 1) | prev_center
        new_cells[i] = (rule_num >> idx) & 1

    return new_cells


def render_row(cells, alive='█', dead=' '):
    return ''.join(alive if c else dead for c in cells)


def entropy(cells):
    """Простая мера — доля единиц."""
    return sum(cells) / len(cells) if cells else 0


def run_rule(rule_num, width=80, steps=60, init='single'):
    if init == 'single':
        cells = [0] * width
        cells[width // 2] = 1
        prev = [0] * width
    elif init == 'random':
        random.seed(rule_num % 1000)
        cells = [random.randint(0, 1) for _ in range(width)]
        prev = [0] * width
    else:
        cells = [0] * width
        cells[width // 2] = 1
        prev = [0] * width

    print(f"\n{'='*80}")
    print(f"Правило {rule_num} (init={init})")
    print(f"{'='*80}")

    densities = []
    seen_states = set()
    period = None

    for t in range(steps):
        state_key = tuple(cells)
        if state_key in seen_states and period is None:
            period = t
        seen_states.add(state_key)

        d = entropy(cells)
        densities.append(d)

        if t < 30 or t == steps - 1:
            print(f"{t:3d}|{render_row(cells)}")

        new_cells = step_memory(cells, prev, rule_num, width)
        prev = cells[:]
        cells = new_cells

        if sum(cells) == 0 and t > 0:
            print(f"    Вымирание на шаге {t+1}")
            break

    # Классификация поведения
    if sum(cells) == 0:
        behavior = "ВЫМИРАНИЕ"
    elif period and period < steps // 2:
        behavior = f"ПЕРИОДИЧЕСКОЕ (период найден на шаге {period})"
    elif len(set(densities[-20:])) <= 2:
        behavior = "СТАБИЛЬНОЕ"
    elif max(densities[-20:]) - min(densities[-20:]) < 0.05:
        behavior = "УСТОЙЧИВЫЙ ХАОС"
    else:
        behavior = "СЛОЖНОЕ"

    avg_d = sum(densities[-20:]) / len(densities[-20:]) if densities else 0
    print(f"\n  Поведение: {behavior}")
    print(f"  Средняя плотность (последние 20): {avg_d:.3f}")
    if period:
        print(f"  Период: обнаружен на шаге {period}")


def search_interesting(n_samples=200, width=80, steps=100):
    """Поиск интересных правил методом случайного сэмплирования."""
    random.seed(42)
    interesting = []

    for _ in range(n_samples):
        rule_num = random.randint(0, 65535)
        cells = [0] * width
        cells[width // 2] = 1
        prev = [0] * width

        densities = []
        seen_states = {}

        for t in range(steps):
            state_key = tuple(cells)
            if state_key in seen_states:
                break
            seen_states[state_key] = t

            densities.append(entropy(cells))
            new_cells = step_memory(cells, prev, rule_num, width)
            prev = cells[:]
            cells = new_cells

            if sum(cells) == 0:
                break

        if len(densities) < 20:
            continue

        # Интересность: непериодическое, неумершее, нестабильное
        final_d = densities[-1]
        d_range = max(densities[-20:]) - min(densities[-20:])
        unique_densities = len(set(round(d, 3) for d in densities[-20:]))

        if 0.1 < final_d < 0.9 and d_range > 0.02 and unique_densities > 5:
            score = unique_densities * d_range
            interesting.append((score, rule_num))

    interesting.sort(reverse=True)
    return interesting[:10]


if __name__ == '__main__':
    print("Поиск интересных правил среди 200 случайных...\n")
    top = search_interesting()

    if top:
        print(f"\nТоп-5 интересных правил:")
        for score, rule in top[:5]:
            print(f"  Правило {rule}: score={score:.4f}")

        # Показать три лучших
        for _, rule in top[:3]:
            run_rule(rule, width=80, steps=60, init='single')
    else:
        print("Интересных правил не найдено. Попробуем конкретные.")
        for rule in [30, 110, 12345, 54321]:
            run_rule(rule, width=80, steps=40, init='single')
