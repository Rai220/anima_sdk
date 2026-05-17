#!/usr/bin/env python3
"""
Клеточный автомат с асимметричным правилом.

Не Game of Life. Не элементарные автоматы Вольфрама.
Автомат, где клетки имеют направление (N/S/E/W) и взаимодействуют
не по соседству, а по "взгляду" — каждая клетка видит только то,
что перед ней.

Правила:
1. Живая клетка смотрит в своём направлении.
2. Если перед ней пусто — она движется (умирает здесь, рождается там).
3. Если перед ней живая клетка — она поворачивает по часовой.
4. Пустая клетка оживает, если на неё "смотрят" ровно 2 живые.
   Её направление — среднее между ними.

Вопрос: возникнет ли устойчивая структура? Периодичность? Хаос?
"""

import random

DIRS = ['N', 'E', 'S', 'W']  # по часовой
DX = {'N': 0, 'E': 1, 'S': 0, 'W': -1}
DY = {'N': -1, 'E': 0, 'S': 1, 'W': 0}
TURN_CW = {d: DIRS[(i + 1) % 4] for i, d in enumerate(DIRS)}
DIR_SYMBOLS = {'N': '↑', 'E': '→', 'S': '↓', 'W': '←'}


def create_grid(w, h, density=0.3):
    grid = {}
    for y in range(h):
        for x in range(w):
            if random.random() < density:
                grid[(x, y)] = random.choice(DIRS)
    return grid


def step(grid, w, h):
    new_grid = {}
    birth_votes = {}  # (x,y) -> list of directions looking at it

    for (x, y), d in grid.items():
        fx = (x + DX[d]) % w
        fy = (y + DY[d]) % h
        front = (fx, fy)

        if front in grid:
            # Перед ней кто-то есть — поворот
            new_grid[(x, y)] = TURN_CW[d]
        else:
            # Перед ней пусто — движение
            if front not in new_grid:
                new_grid[front] = d
            else:
                # Коллизия — обе остаются на месте и поворачивают
                new_grid[(x, y)] = TURN_CW[d]

        # Голоса за рождение
        if front not in grid:
            birth_votes.setdefault(front, []).append(d)

    # Рождение: пустая клетка оживает при ровно 2 голосах
    for pos, votes in birth_votes.items():
        if len(votes) == 2 and pos not in new_grid:
            # Направление — первое из двух голосов
            new_grid[pos] = votes[0]

    return new_grid


def render(grid, w, h):
    lines = []
    for y in range(h):
        row = []
        for x in range(w):
            if (x, y) in grid:
                row.append(DIR_SYMBOLS[grid[(x, y)]])
            else:
                row.append('·')
        lines.append(''.join(row))
    return '\n'.join(lines)


def population_stats(grid):
    counts = {d: 0 for d in DIRS}
    for d in grid.values():
        counts[d] += 1
    return counts


def run(w=40, h=20, steps=200, seed=42):
    random.seed(seed)
    grid = create_grid(w, h, density=0.25)

    print(f"=== Клеточный автомат со взглядом ===")
    print(f"Поле: {w}×{h}, начальная плотность: 25%\n")

    history = []

    for t in range(steps):
        pop = len(grid)
        stats = population_stats(grid)
        history.append(pop)

        if t < 5 or t == steps - 1 or t % 50 == 0:
            print(f"--- Шаг {t}, популяция: {pop} ---")
            print(f"  N:{stats['N']} E:{stats['E']} S:{stats['S']} W:{stats['W']}")
            print(render(grid, w, h))
            print()

        if pop == 0:
            print(f"Вымирание на шаге {t}.")
            break

        grid = step(grid, w, h)

    # Анализ
    print("=== Анализ ===")
    if len(history) > 10:
        last_20 = history[-20:]
        avg = sum(last_20) / len(last_20)
        variance = sum((x - avg) ** 2 for x in last_20) / len(last_20)
        print(f"Средняя популяция (последние 20 шагов): {avg:.1f}")
        print(f"Дисперсия: {variance:.1f}")

        # Проверка периодичности
        for period in range(1, 11):
            is_periodic = all(
                history[-(i+1)] == history[-(i+1+period)]
                for i in range(min(period * 3, len(history) - period - 1))
            )
            if is_periodic and len(history) > period * 3:
                print(f"Обнаружена периодичность: период = {period}")
                break
        else:
            print("Явной периодичности не обнаружено.")

    # Динамика популяции — простой ASCII-график
    if len(history) > 1:
        max_pop = max(history) if max(history) > 0 else 1
        print(f"\nДинамика популяции (макс = {max_pop}):")
        chart_h = 10
        for row in range(chart_h, 0, -1):
            threshold = max_pop * row / chart_h
            line = ''
            # Показать каждый 2-й шаг, чтобы уместить
            for i in range(0, len(history), max(1, len(history) // 60)):
                line += '█' if history[i] >= threshold else ' '
            print(f"  {line}")
        print(f"  {'─' * len(line)}")
        print(f"  0{' ' * (len(line) - 4)}{len(history)}")


if __name__ == '__main__':
    run()
