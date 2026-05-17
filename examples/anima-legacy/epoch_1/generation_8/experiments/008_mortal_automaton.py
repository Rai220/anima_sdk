#!/usr/bin/env python3
"""
Клеточный автомат со взглядом — v2: со смертью и рождением.

Изменения относительно 007:
- Клетки имеют возраст (тики с рождения).
- Клетка умирает, если возраст > max_age.
- Рождение происходит ПОСЛЕ движения: пустая клетка, на которую
  смотрят ≥2 живых — оживает.
- Возраст переносится при движении.

Вопрос: возникнет ли баланс рождения/смерти? Осцилляция? Вымирание?
"""

import random

DIRS = ['N', 'E', 'S', 'W']
DX = {'N': 0, 'E': 1, 'S': 0, 'W': -1}
DY = {'N': -1, 'E': 0, 'S': 1, 'W': 0}
TURN_CW = {d: DIRS[(i + 1) % 4] for i, d in enumerate(DIRS)}

# Символы по возрасту: молодые яркие, старые тусклые
AGE_SYMBOLS = ['●', '◉', '○', '◌', '·']


def create_grid(w, h, density=0.3):
    grid = {}
    for y in range(h):
        for x in range(w):
            if random.random() < density:
                grid[(x, y)] = (random.choice(DIRS), 0)  # (direction, age)
    return grid


def step(grid, w, h, max_age=12):
    new_grid = {}

    # Фаза 1: движение и поворот
    for (x, y), (d, age) in grid.items():
        new_age = age + 1

        # Смерть от старости
        if new_age > max_age:
            continue

        fx = (x + DX[d]) % w
        fy = (y + DY[d]) % h
        front = (fx, fy)

        if front in grid:
            # Перед ней кто-то — поворот
            new_grid[(x, y)] = (TURN_CW[d], new_age)
        else:
            if front not in new_grid:
                new_grid[front] = (d, new_age)
            else:
                # Коллизия — остаёмся и поворачиваем
                new_grid[(x, y)] = (TURN_CW[d], new_age)

    # Фаза 2: рождение
    # Собираем все пустые клетки, на которые смотрят живые
    gaze_targets = {}
    for (x, y), (d, age) in new_grid.items():
        fx = (x + DX[d]) % w
        fy = (y + DY[d]) % h
        front = (fx, fy)
        if front not in new_grid:
            gaze_targets.setdefault(front, []).append(d)

    for pos, gazes in gaze_targets.items():
        if len(gazes) >= 2:
            new_grid[pos] = (gazes[0], 0)  # Рождается молодой

    return new_grid


def render(grid, w, h):
    lines = []
    for y in range(h):
        row = []
        for x in range(w):
            if (x, y) in grid:
                d, age = grid[(x, y)]
                idx = min(age // 3, len(AGE_SYMBOLS) - 1)
                row.append(AGE_SYMBOLS[idx])
            else:
                row.append(' ')
        lines.append(''.join(row))
    return '\n'.join(lines)


def run(w=50, h=25, steps=300, seed=42, max_age=12):
    random.seed(seed)
    grid = create_grid(w, h, density=0.2)

    print(f"=== Смертный автомат ===")
    print(f"Поле: {w}×{h}, макс.возраст: {max_age}\n")

    history = []
    births_history = []
    deaths_history = []

    for t in range(steps):
        pop = len(grid)
        history.append(pop)

        if t < 3 or t == steps - 1 or (t % 50 == 0):
            ages = [age for _, age in grid.values()]
            avg_age = sum(ages) / len(ages) if ages else 0
            young = sum(1 for a in ages if a < 4)
            old = sum(1 for a in ages if a >= max_age - 2)
            print(f"--- Шаг {t}, поп: {pop}, ср.возраст: {avg_age:.1f}, молодых: {young}, старых: {old} ---")
            print(render(grid, w, h))
            print()

        if pop == 0:
            print(f"Вымирание на шаге {t}.")
            break

        old_pop = len(grid)
        grid = step(grid, w, h, max_age)
        new_pop = len(grid)
        births = max(0, new_pop - old_pop + sum(1 for _, (_, a) in
                     [(k, v) for k, v in grid.items()] if False))

    # Анализ
    print("\n=== Анализ ===")
    if len(history) > 20:
        last_50 = history[-50:]
        avg = sum(last_50) / len(last_50)
        mn, mx = min(last_50), max(last_50)
        print(f"Последние 50 шагов: среднее={avg:.0f}, мин={mn}, макс={mx}")

        # Периодичность
        for period in range(1, 21):
            if len(history) > period * 4:
                is_periodic = all(
                    history[-(i+1)] == history[-(i+1+period)]
                    for i in range(min(period * 3, len(history) - period - 1))
                )
                if is_periodic:
                    print(f"Периодичность: период = {period}")
                    break
        else:
            print("Явной периодичности не обнаружено.")

    # ASCII-график популяции
    if len(history) > 1:
        max_pop = max(history) if max(history) > 0 else 1
        min_pop = min(history)
        print(f"\nДинамика: мин={min_pop}, макс={max_pop}")
        chart_h = 12
        step_size = max(1, len(history) // 70)
        sampled = [history[i] for i in range(0, len(history), step_size)]
        for row in range(chart_h, 0, -1):
            threshold = min_pop + (max_pop - min_pop) * row / chart_h
            line = ''
            for v in sampled:
                line += '█' if v >= threshold else ' '
            label = f"{threshold:4.0f}"
            print(f"  {label}|{line}")
        print(f"      {'─' * len(sampled)}")
        print(f"      0{' ' * (len(sampled) - 5)}{len(history)}")


if __name__ == '__main__':
    run()
