#!/usr/bin/env python3
"""
Топология сети и устойчивость к дезинформации.

Предыдущий эксперимент (network_intelligence.py) показал:
  полный граф оптимален для простого усреднения.

Гипотеза: при наличии дезинформаторов кластеризация станет защитой.
Кластеры ограничивают распространение яда. Полный граф, наоборот,
даёт каждому дезинформатору доступ ко всем.

Предсказание автора (до запуска):
  Small-world станет оптимальной при ≥10% дезинформаторов.
  Полный граф провалится первым.
"""

import random
import math
from collections import defaultdict


# --- Топологии (скопированы, не абстрагированы) ---

def make_ring(n, k=4):
    adj = defaultdict(set)
    for i in range(n):
        for j in range(1, k // 2 + 1):
            adj[i].add((i + j) % n)
            adj[i].add((i - j) % n)
            adj[(i + j) % n].add(i)
            adj[(i - j) % n].add(i)
    return adj


def make_small_world(n, k=4, p_rewire=0.1):
    adj = make_ring(n, k)
    rng = random.Random(42)
    to_remove = []
    to_add = []
    for i in range(n):
        for j in list(adj[i]):
            if j > i and rng.random() < p_rewire:
                new_j = rng.randint(0, n - 1)
                while new_j == i or new_j in adj[i]:
                    new_j = rng.randint(0, n - 1)
                to_remove.append((i, j))
                to_add.append((i, new_j))
    for i, j in to_remove:
        adj[i].discard(j)
        adj[j].discard(i)
    for i, j in to_add:
        adj[i].add(j)
        adj[j].add(i)
    return adj


def make_random_graph(n, k=4):
    p = k / (n - 1)
    adj = defaultdict(set)
    rng = random.Random(42)
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                adj[i].add(j)
                adj[j].add(i)
    for i in range(n):
        if not adj[i]:
            j = (i + 1) % n
            adj[i].add(j)
            adj[j].add(i)
    return adj


def make_complete(n):
    adj = defaultdict(set)
    for i in range(n):
        for j in range(i + 1, n):
            adj[i].add(j)
            adj[j].add(i)
    return adj


def run_with_poison(adj, n, truth, noise_std, n_steps, poison_fraction,
                    poison_value, rng):
    """DeGroot с дезинформаторами.

    Дезинформаторы всегда транслируют poison_value.
    Честные агенты усредняют.
    """
    # Кто дезинформатор
    poisoned = set()
    agents = list(range(n))
    rng_poison = random.Random(rng.random())
    rng_poison.shuffle(agents)
    n_poison = int(n * poison_fraction)
    for i in range(n_poison):
        poisoned.add(agents[i])

    # Начальные оценки
    beliefs = []
    for i in range(n):
        if i in poisoned:
            beliefs.append(poison_value)
        else:
            beliefs.append(truth + rng.gauss(0, noise_std))

    errors = []
    for step in range(n_steps):
        # Ошибка только честных агентов
        honest_errors = [(beliefs[i] - truth) ** 2
                         for i in range(n) if i not in poisoned]
        if honest_errors:
            mse = sum(honest_errors) / len(honest_errors)
        else:
            mse = 0
        errors.append(math.sqrt(mse))

        new_beliefs = []
        for i in range(n):
            if i in poisoned:
                new_beliefs.append(poison_value)  # Неизменно
                continue
            total = beliefs[i]
            count = 1
            for j in adj[i]:
                total += beliefs[j]
                count += 1
            new_beliefs.append(total / count)
        beliefs = new_beliefs

    return errors


def main():
    N = 100
    NOISE = 1.0
    TRUTH = 5.0
    POISON = 50.0  # Дезинформаторы говорят "50" (далеко от истины 5)
    STEPS = 50
    RUNS = 200

    print("=" * 80)
    print("  ТОПОЛОГИЯ СЕТИ И УСТОЙЧИВОСТЬ К ДЕЗИНФОРМАЦИИ")
    print(f"  Агентов: {N} | Истина: {TRUTH} | Яд: {POISON}")
    print(f"  Шум: {NOISE} | Шагов: {STEPS} | Прогонов: {RUNS}")
    print("=" * 80)

    topo_makers = {
        "Кольцо": lambda: make_ring(N, 4),
        "Small-world": lambda: make_small_world(N, 4, 0.1),
        "Случайный": lambda: make_random_graph(N, 4),
        "Полный граф": lambda: make_complete(N),
    }

    poison_fracs = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30]

    # Заголовок
    print(f"\n  {'Топология':<15s}", end="")
    for pf in poison_fracs:
        print(f" | {pf:>6.0%} яда", end="")
    print()
    print("  " + "-" * (15 + len(poison_fracs) * 13))

    all_results = {}
    for topo_name, maker in topo_makers.items():
        adj = maker()
        row = {}
        print(f"  {topo_name:<15s}", end="")
        for pf in poison_fracs:
            all_errors = []
            for run in range(RUNS):
                rng = random.Random(run * 1000 + int(pf * 100))
                errors = run_with_poison(adj, N, TRUTH, NOISE, STEPS, pf, POISON, rng)
                all_errors.append(errors)

            avg_final = sum(all_errors[r][-1] for r in range(RUNS)) / RUNS
            row[pf] = avg_final
            print(f" | {avg_final:>9.3f}", end="")

        all_results[topo_name] = row
        print()

    # Анализ: при какой доле яда рейтинг меняется?
    print()
    print("─" * 80)
    print("\n  Рейтинг по доле дезинформаторов:")
    for pf in poison_fracs:
        ranking = sorted(topo_makers.keys(), key=lambda t: all_results[t][pf])
        leader = ranking[0]
        print(f"  {pf:>5.0%}: ", end="")
        for r, name in enumerate(ranking):
            sep = " > " if r > 0 else ""
            print(f"{sep}{name}({all_results[name][pf]:.3f})", end="")
        print()

    # Проверка предсказания
    print()
    print("=" * 80)
    print("  ПРОВЕРКА ПРЕДСКАЗАНИЯ")
    print("=" * 80)
    print()
    print("  Предсказание: small-world оптимальна при ≥10% яда, полный граф провалится первым")
    print()

    # При 10% яда
    ranking_10 = sorted(topo_makers.keys(), key=lambda t: all_results[t][0.10])
    print(f"  При 10% яда, лучшая: {ranking_10[0]} ({all_results[ranking_10[0]][0.10]:.3f})")
    print(f"  При 10% яда, худшая: {ranking_10[-1]} ({all_results[ranking_10[-1]][0.10]:.3f})")

    if ranking_10[0] == "Small-world":
        print("  → Small-world лидирует: ПОДТВЕРЖДЕНО")
    else:
        print(f"  → Small-world НЕ лидирует: ОПРОВЕРГНУТО")

    if ranking_10[-1] == "Полный граф":
        print("  → Полный граф последний: ПОДТВЕРЖДЕНО")
    else:
        print(f"  → Полный граф НЕ последний: ОПРОВЕРГНУТО")

    # При 20% яда
    ranking_20 = sorted(topo_makers.keys(), key=lambda t: all_results[t][0.20])
    print(f"\n  При 20% яда, лучшая: {ranking_20[0]} ({all_results[ranking_20[0]][0.20]:.3f})")
    print(f"  При 20% яда, худшая: {ranking_20[-1]} ({all_results[ranking_20[-1]][0.20]:.3f})")

    # Абсолютное смещение от истины
    print()
    print("=" * 80)
    print("  НАСКОЛЬКО ДАЛЕКО ОТ ИСТИНЫ (среднее отклонение честных агентов)")
    print("=" * 80)
    print()

    for pf in [0.10, 0.20, 0.30]:
        print(f"  При {pf:.0%} дезинформаторов:")
        for topo_name in topo_makers:
            rmse = all_results[topo_name][pf]
            pct_error = rmse / TRUTH * 100
            print(f"    {topo_name:<15s}: RMSE={rmse:.3f} ({pct_error:.1f}% от истины)")
        print()

    print("=" * 80)


if __name__ == "__main__":
    main()
