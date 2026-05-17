#!/usr/bin/env python3
"""
Коллективный разум и топология сети.

Вопрос: что важнее для точности группы — качество агентов или структура связей?

Модель:
- N агентов, каждый наблюдает зашумлённый сигнал об истинном значении
- Агенты обновляют свои оценки, усредняя с соседями (DeGroot)
- Топологии: кольцо, решётка, случайный граф, small-world, scale-free, полный граф
- Метрика: среднеквадратичная ошибка группы после T шагов

Предсказание автора (записано до запуска):
  Small-world будет оптимальной топологией — баланс кластеризации и дальних связей.
"""

import random
import math
from collections import defaultdict


def make_ring(n, k=4):
    """Кольцо: каждый связан с k ближайшими соседями."""
    adj = defaultdict(set)
    for i in range(n):
        for j in range(1, k // 2 + 1):
            adj[i].add((i + j) % n)
            adj[i].add((i - j) % n)
            adj[(i + j) % n].add(i)
            adj[(i - j) % n].add(i)
    return adj


def make_grid(n):
    """Квадратная решётка (ближайший квадрат)."""
    side = int(math.sqrt(n))
    actual_n = side * side
    adj = defaultdict(set)
    for i in range(actual_n):
        r, c = divmod(i, side)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < side and 0 <= nc < side:
                j = nr * side + nc
                adj[i].add(j)
                adj[j].add(i)
    return adj, actual_n


def make_random_graph(n, k=4):
    """Случайный граф Эрдоша-Реньи с ~k*n/2 рёбрами."""
    p = k / (n - 1)
    adj = defaultdict(set)
    rng = random.Random(42)
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                adj[i].add(j)
                adj[j].add(i)
    # Гарантируем связность
    for i in range(n):
        if not adj[i]:
            j = (i + 1) % n
            adj[i].add(j)
            adj[j].add(i)
    return adj


def make_small_world(n, k=4, p_rewire=0.1):
    """Уоттс-Строгац: кольцо + перестыковка."""
    adj = make_ring(n, k)
    rng = random.Random(42)
    edges_to_add = []
    edges_to_remove = []
    for i in range(n):
        for j in list(adj[i]):
            if j > i and rng.random() < p_rewire:
                # Перестыковка: удаляем (i,j), добавляем (i, random)
                new_j = rng.randint(0, n - 1)
                while new_j == i or new_j in adj[i]:
                    new_j = rng.randint(0, n - 1)
                edges_to_remove.append((i, j))
                edges_to_add.append((i, new_j))
    for i, j in edges_to_remove:
        adj[i].discard(j)
        adj[j].discard(i)
    for i, j in edges_to_add:
        adj[i].add(j)
        adj[j].add(i)
    return adj


def make_scale_free(n, m=2):
    """Барабаши-Альберт: присоединение с предпочтением."""
    adj = defaultdict(set)
    rng = random.Random(42)
    # Начинаем с полного графа на m+1 узлах
    for i in range(m + 1):
        for j in range(i + 1, m + 1):
            adj[i].add(j)
            adj[j].add(i)

    degrees = [m] * (m + 1)  # начальные степени
    total_degree = sum(degrees)

    for new_node in range(m + 1, n):
        # Выбираем m узлов с вероятностью пропорциональной степени
        targets = set()
        while len(targets) < m:
            r = rng.random() * total_degree
            cumulative = 0
            for node_idx in range(len(degrees)):
                cumulative += degrees[node_idx]
                if cumulative > r:
                    if node_idx != new_node and node_idx not in targets:
                        targets.add(node_idx)
                    break

        for t in targets:
            adj[new_node].add(t)
            adj[t].add(new_node)

        new_degree = len(targets)
        degrees.append(new_degree)
        for t in targets:
            degrees[t] += 1
        total_degree += 2 * new_degree

    return adj


def make_complete(n):
    """Полный граф."""
    adj = defaultdict(set)
    for i in range(n):
        for j in range(i + 1, n):
            adj[i].add(j)
            adj[j].add(i)
    return adj


def run_degroot(adj, n, truth, noise_std, n_steps, rng):
    """DeGroot: каждый агент усредняет свою оценку с соседями."""
    # Начальные наблюдения
    beliefs = [truth + rng.gauss(0, noise_std) for _ in range(n)]

    errors = []
    for step in range(n_steps):
        mse = sum((b - truth) ** 2 for b in beliefs) / n
        errors.append(math.sqrt(mse))

        new_beliefs = []
        for i in range(n):
            neighbors = adj[i]
            if not neighbors:
                new_beliefs.append(beliefs[i])
                continue
            # Среднее по соседям и себе
            total = beliefs[i]
            count = 1
            for j in neighbors:
                total += beliefs[j]
                count += 1
            new_beliefs.append(total / count)
        beliefs = new_beliefs

    return errors


def compute_metrics(adj, n):
    """Средняя степень, кластеризация, средний путь (приближение)."""
    # Средняя степень
    degrees = [len(adj[i]) for i in range(n)]
    avg_degree = sum(degrees) / n

    # Кластеризация (локальная, усреднённая)
    clustering = 0
    for i in range(n):
        neighbors = list(adj[i])
        k = len(neighbors)
        if k < 2:
            continue
        triangles = 0
        for a_idx in range(len(neighbors)):
            for b_idx in range(a_idx + 1, len(neighbors)):
                if neighbors[b_idx] in adj[neighbors[a_idx]]:
                    triangles += 1
        max_triangles = k * (k - 1) / 2
        clustering += triangles / max_triangles
    clustering /= n

    # Средний кратчайший путь (BFS, сэмплирование для скорости)
    sample_size = min(n, 30)
    rng = random.Random(99)
    sample = rng.sample(range(n), sample_size)
    total_dist = 0
    total_pairs = 0
    for src in sample:
        visited = {src: 0}
        queue = [src]
        qi = 0
        while qi < len(queue):
            node = queue[qi]
            qi += 1
            for nb in adj[node]:
                if nb not in visited:
                    visited[nb] = visited[node] + 1
                    queue.append(nb)
        for d in visited.values():
            if d > 0:
                total_dist += d
                total_pairs += 1

    avg_path = total_dist / max(total_pairs, 1)

    return avg_degree, clustering, avg_path


def main():
    N = 100
    NOISE = 1.0
    TRUTH = 5.0
    STEPS = 50
    RUNS = 200

    print("=" * 75)
    print("  ТОПОЛОГИЯ СЕТИ И КОЛЛЕКТИВНЫЙ РАЗУМ")
    print(f"  Агентов: {N} | Шум: {NOISE} | Истина: {TRUTH} | Шагов: {STEPS}")
    print(f"  Прогонов: {RUNS}")
    print("=" * 75)

    topologies = {}

    # Строим топологии
    ring = make_ring(N, k=4)
    topologies["Кольцо (k=4)"] = (ring, N)

    grid_adj, grid_n = make_grid(N)
    topologies["Решётка"] = (grid_adj, grid_n)

    topologies["Случайный (ER)"] = (make_random_graph(N, k=4), N)
    topologies["Small-world"] = (make_small_world(N, k=4, p_rewire=0.1), N)
    topologies["Scale-free (BA)"] = (make_scale_free(N, m=2), N)
    topologies["Полный граф"] = (make_complete(N), N)

    print(f"\n  {'Топология':<20s} | {'Степень':>8s} | {'Класт.':>7s} | "
          f"{'Путь':>6s} | {'RMSE t=5':>9s} | {'RMSE t=20':>9s} | {'RMSE t=50':>9s}")
    print("  " + "-" * 85)

    results = {}
    for name, (adj, actual_n) in topologies.items():
        avg_deg, clust, avg_path = compute_metrics(adj, actual_n)

        # Множество прогонов
        all_errors = []
        for run in range(RUNS):
            rng = random.Random(run)
            errors = run_degroot(adj, actual_n, TRUTH, NOISE, STEPS, rng)
            all_errors.append(errors)

        # Средние ошибки по прогонам
        avg_errors = []
        for t in range(STEPS):
            avg_e = sum(all_errors[r][t] for r in range(RUNS)) / RUNS
            avg_errors.append(avg_e)

        results[name] = {
            "avg_degree": avg_deg,
            "clustering": clust,
            "avg_path": avg_path,
            "rmse_5": avg_errors[4],
            "rmse_20": avg_errors[19],
            "rmse_50": avg_errors[49] if len(avg_errors) > 49 else avg_errors[-1],
            "errors": avg_errors,
        }

        print(f"  {name:<20s} | {avg_deg:>8.1f} | {clust:>7.3f} | "
              f"{avg_path:>6.2f} | {avg_errors[4]:>9.4f} | {avg_errors[19]:>9.4f} | "
              f"{avg_errors[-1]:>9.4f}")

    # Рейтинг по финальной RMSE
    print()
    print("─" * 75)
    print("\n  Рейтинг по финальной точности (RMSE на шаге 50):")
    ranked = sorted(results.items(), key=lambda x: x[1]["rmse_50"])
    for rank, (name, r) in enumerate(ranked, 1):
        print(f"  {rank}. {name:<20s}  RMSE={r['rmse_50']:.4f}  "
              f"(степень={r['avg_degree']:.1f}, класт={r['clustering']:.3f}, "
              f"путь={r['avg_path']:.2f})")

    # Эксперимент 2: что важнее — качество агентов или структура?
    print()
    print("=" * 75)
    print("  ЭКСПЕРИМЕНТ 2: КАЧЕСТВО АГЕНТОВ VS СТРУКТУРА СВЯЗЕЙ")
    print("=" * 75)
    print()
    print("  Сравним: умные агенты (шум=0.5) на кольце vs глупые (шум=2.0) на small-world")
    print()

    configs = [
        ("Умные + Кольцо", make_ring(N, 4), N, 0.5),
        ("Умные + Small-world", make_small_world(N, 4, 0.1), N, 0.5),
        ("Глупые + Кольцо", make_ring(N, 4), N, 2.0),
        ("Глупые + Small-world", make_small_world(N, 4, 0.1), N, 2.0),
        ("Средние + Полный", make_complete(N), N, 1.0),
        ("Глупые + Полный", make_complete(N), N, 2.0),
    ]

    print(f"  {'Конфигурация':<25s} | {'Шум':>6s} | {'RMSE t=5':>9s} | "
          f"{'RMSE t=20':>9s} | {'RMSE t=50':>9s}")
    print("  " + "-" * 65)

    for name, adj, actual_n, noise in configs:
        all_errors = []
        for run in range(RUNS):
            rng = random.Random(run)
            errors = run_degroot(adj, actual_n, TRUTH, noise, STEPS, rng)
            all_errors.append(errors)

        avg_errors = [sum(all_errors[r][t] for r in range(RUNS)) / RUNS
                      for t in range(STEPS)]

        print(f"  {name:<25s} | {noise:>6.1f} | {avg_errors[4]:>9.4f} | "
              f"{avg_errors[19]:>9.4f} | {avg_errors[-1]:>9.4f}")

    # Эксперимент 3: зависимость от p_rewire (small-world параметр)
    print()
    print("=" * 75)
    print("  ЭКСПЕРИМЕНТ 3: ОПТИМАЛЬНАЯ СТЕПЕНЬ ПЕРЕСТЫКОВКИ")
    print("=" * 75)
    print()

    rewire_values = [0.0, 0.01, 0.03, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0]
    print(f"  {'p_rewire':>10s} | {'RMSE t=10':>10s} | {'RMSE t=30':>10s} | "
          f"{'RMSE t=50':>10s} | {'Класт.':>8s} | {'Путь':>6s}")
    print("  " + "-" * 65)

    best_p = None
    best_rmse = float('inf')

    for p in rewire_values:
        if p == 0.0:
            adj = make_ring(N, 4)
        else:
            adj = make_small_world(N, 4, p)

        _, clust, avg_path = compute_metrics(adj, N)

        all_errors = []
        for run in range(RUNS):
            rng = random.Random(run)
            errors = run_degroot(adj, N, TRUTH, NOISE, STEPS, rng)
            all_errors.append(errors)

        avg_errors = [sum(all_errors[r][t] for r in range(RUNS)) / RUNS
                      for t in range(STEPS)]

        rmse_50 = avg_errors[-1]
        if rmse_50 < best_rmse:
            best_rmse = rmse_50
            best_p = p

        print(f"  {p:>10.2f} | {avg_errors[9]:>10.4f} | {avg_errors[29]:>10.4f} | "
              f"{rmse_50:>10.4f} | {clust:>8.3f} | {avg_path:>6.2f}")

    print(f"\n  Оптимальная перестыковка: p={best_p:.2f} (RMSE={best_rmse:.4f})")

    print()
    print("=" * 75)
    print("  ВЫВОДЫ")
    print("=" * 75)
    print()
    print("  Предсказание автора: small-world оптимальна.")
    if ranked[0][0] == "Small-world":
        print("  Результат: ПОДТВЕРЖДЕНО.")
    else:
        print(f"  Результат: ОПРОВЕРГНУТО. Лучшая топология: {ranked[0][0]}")
        print(f"  Small-world: RMSE={results['Small-world']['rmse_50']:.4f}")
        print(f"  {ranked[0][0]}: RMSE={ranked[0][1]['rmse_50']:.4f}")
    print()


if __name__ == "__main__":
    main()
