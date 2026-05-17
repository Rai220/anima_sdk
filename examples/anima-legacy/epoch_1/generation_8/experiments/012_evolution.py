#!/usr/bin/env python3
"""
Эволюция правил клеточных автоматов через конкуренцию.

Два правила (16-битных, автомат с памятью) конкурируют:
- Поле делится пополам: левая часть — правило A, правая — правило B.
- Граница подвижна: каждая клетка применяет правило того "племени",
  к которому принадлежит.
- Если клетка рождается, она наследует племя большинства своих соседей.
- После N шагов побеждает племя с большей территорией.
- Победитель мутирует (переключает 1-2 бита) → следующий бой.

Вопрос: что эволюция отберёт? Агрессию? Стабильность? Сложность?
"""

import random
from collections import Counter


def step_battle(cells, prev, tribes, rule_a, rule_b, width):
    """Один шаг с двумя конкурирующими правилами."""
    new_cells = [0] * width
    new_tribes = tribes[:]

    for i in range(width):
        left = cells[(i - 1) % width]
        center = cells[i]
        right = cells[(i + 1) % width]
        prev_center = prev[i]

        idx = (left << 3) | (center << 2) | (right << 1) | prev_center
        rule = rule_a if tribes[i] == 'A' else rule_b
        new_cells[i] = (rule >> idx) & 1

    # Определение племени для каждой клетки
    # Живые клетки сохраняют племя
    # При "рождении" (0→1) — наследуют от соседей
    for i in range(width):
        if new_cells[i] == 1 and cells[i] == 0:
            # Рождение — смотрим на соседей
            neighbors = []
            for di in [-1, 0, 1]:
                ni = (i + di) % width
                if cells[ni] == 1:
                    neighbors.append(tribes[ni])
            if neighbors:
                a_count = neighbors.count('A')
                b_count = neighbors.count('B')
                new_tribes[i] = 'A' if a_count >= b_count else 'B'
        elif new_cells[i] == 1:
            new_tribes[i] = tribes[i]  # Сохраняем
        # Мёртвые клетки — племя не имеет значения, но сохраняем для следующего хода

    return new_cells, new_tribes


def fight(rule_a, rule_b, width=100, steps=80):
    """Один бой. Возвращает ('A', score_a, score_b) или ('B', ...)."""
    cells = [0] * width
    tribes = ['A'] * (width // 2) + ['B'] * (width // 2)

    # Начальное состояние: несколько живых клеток с каждой стороны
    random.seed(rule_a * 1000 + rule_b)
    for i in range(width):
        if random.random() < 0.3:
            cells[i] = 1

    prev = [0] * width

    for t in range(steps):
        new_cells, new_tribes = step_battle(cells, prev, tribes, rule_a, rule_b, width)
        prev = cells[:]
        cells = new_cells
        tribes = new_tribes

    # Подсчёт
    a_alive = sum(1 for i in range(width) if cells[i] == 1 and tribes[i] == 'A')
    b_alive = sum(1 for i in range(width) if cells[i] == 1 and tribes[i] == 'B')

    winner = 'A' if a_alive >= b_alive else 'B'
    return winner, a_alive, b_alive


def mutate(rule, n_bits=1):
    """Мутация: переключить n_bits случайных бит."""
    for _ in range(n_bits):
        bit = random.randint(0, 15)
        rule ^= (1 << bit)
    return rule


def tournament(population, width=100, steps=80):
    """Турнир: каждый с каждым (или случайные пары)."""
    scores = Counter()
    n = len(population)

    # Случайные пары — быстрее, чем каждый с каждым
    n_fights = n * 3
    for _ in range(n_fights):
        i, j = random.sample(range(n), 2)
        winner, a_score, b_score = fight(population[i], population[j], width, steps)
        if winner == 'A':
            scores[i] += 1
        else:
            scores[j] += 1

    return scores


def evolve(pop_size=20, generations=50, width=100, steps=80):
    """Основной эволюционный цикл."""
    random.seed(42)

    # Начальная популяция — случайные правила
    population = [random.randint(0, 65535) for _ in range(pop_size)]

    print(f"=== Эволюция правил автоматов ===")
    print(f"Популяция: {pop_size}, поколений: {generations}")
    print(f"Поле: {width}, шагов в бою: {steps}\n")

    history = []

    for gen in range(generations):
        scores = tournament(population, width, steps)

        # Ранжирование
        ranked = sorted(range(pop_size), key=lambda i: scores[i], reverse=True)
        best_idx = ranked[0]
        best_rule = population[best_idx]
        best_score = scores[best_idx]

        # Статистика
        avg_score = sum(scores.values()) / pop_size if pop_size > 0 else 0
        unique_rules = len(set(population))

        history.append({
            'gen': gen,
            'best_rule': best_rule,
            'best_score': best_score,
            'avg_score': avg_score,
            'unique': unique_rules,
            'population': population[:],
        })

        if gen % 10 == 0 or gen == generations - 1:
            top3 = [population[ranked[i]] for i in range(min(3, pop_size))]
            top3_str = ', '.join(f'{r}({scores[ranked[i]]})' for i, r in enumerate(top3))
            print(f"Gen {gen:3d}: лучший={best_rule:5d} "
                  f"(wins={best_score}), уник={unique_rules:2d}, "
                  f"топ-3: {top3_str}")

        # Селекция + мутация
        # Верхняя половина выживает
        survivors = [population[ranked[i]] for i in range(pop_size // 2)]

        # Нижняя половина заменяется мутантами верхней
        children = []
        for _ in range(pop_size - len(survivors)):
            parent = random.choice(survivors)
            child = mutate(parent, n_bits=random.choice([1, 1, 1, 2]))
            children.append(child)

        population = survivors + children
        random.shuffle(population)

    # Финальный анализ
    print(f"\n{'='*60}")
    print(f"РЕЗУЛЬТАТЫ ЭВОЛЮЦИИ")
    print(f"{'='*60}")

    # Самые успешные правила за всю историю
    all_winners = Counter()
    for h in history:
        all_winners[h['best_rule']] += 1

    print(f"\nЧаще всего побеждали:")
    for rule, count in all_winners.most_common(10):
        # Анализ битов правила
        bits = f"{rule:016b}"
        bit0 = (rule >> 0) & 1  # creatio ex nihilo
        bit15 = (rule >> 15) & 1  # устойчивость полноты
        print(f"  Правило {rule:5d} (0b{bits}): {count} поколений в топе, "
              f"bit0={bit0}, bit15={bit15}")

    # Анализ: какие биты чаще включены у победителей?
    print(f"\nБитовый профиль финальной популяции:")
    final_pop = history[-1]['population']
    for bit in range(16):
        count = sum(1 for r in final_pop if (r >> bit) & 1)
        pct = count / len(final_pop) * 100
        left = (bit >> 3) & 1
        center = (bit >> 2) & 1
        right = (bit >> 1) & 1
        prev = bit & 1
        bar = '█' * int(pct / 5)
        print(f"  бит {bit:2d} ({left},{center},{right},p={prev}): "
              f"{pct:5.1f}% {bar}")

    # Конвергенция?
    print(f"\nРазнообразие популяции по поколениям:")
    for h in history[::5]:
        u = h['unique']
        bar = '█' * u
        print(f"  Gen {h['gen']:3d}: {u:2d} уникальных {bar}")

    # Генеалогия: как менялся лучший?
    print(f"\nЛиния лучших правил:")
    prev_best = None
    for h in history:
        if h['best_rule'] != prev_best:
            print(f"  Gen {h['gen']:3d}: {h['best_rule']:5d} "
                  f"(0b{h['best_rule']:016b})")
            prev_best = h['best_rule']


if __name__ == '__main__':
    evolve()
