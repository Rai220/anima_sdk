#!/usr/bin/env python3
"""
phase_transition.py — Фазовые переходы: перколяция и случайные графы

Когда количество становится качеством?

На решётке n×n каждая ячейка открыта с вероятностью p.
При p < p_c — изолированные островки.
При p = p_c — критическая точка. Кластер фрактален.
При p > p_c — путь сверху вниз. Система проводит.

Для квадратной решётки p_c ≈ 0.5927 (site percolation).
Это число — не свойство конкретной решётки.
Это свойство размерности и топологии.

Шесть экспериментов:
1. Визуализация перколяции (ASCII)
2. Поиск порога — когда появляется сквозной путь
3. Размер гигантской компоненты vs. p
4. Фрактальная размерность критического кластера
5. Фазовый переход в случайных графах Эрдёша—Реньи
6. Универсальность: треугольная vs. квадратная решётка
"""

import random
import math
from collections import Counter, deque


# ──────────────────────────────────────────────
# Union-Find
# ──────────────────────────────────────────────

class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.size = [1] * n

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        self.size[rx] += self.size[ry]
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1

    def largest_component(self):
        return max(self.size[self.find(i)] for i in range(len(self.parent)))

    def component_sizes(self):
        roots = {}
        for i in range(len(self.parent)):
            r = self.find(i)
            if r not in roots:
                roots[r] = self.size[r]
        return sorted(roots.values(), reverse=True)


# ──────────────────────────────────────────────
# Перколяция на квадратной решётке
# ──────────────────────────────────────────────

def make_grid(n, p, rng=None):
    """Возвращает n×n сетку: 1 = открыта, 0 = закрыта."""
    if rng is None:
        rng = random.Random()
    return [[1 if rng.random() < p else 0 for _ in range(n)] for _ in range(n)]


def find_clusters(grid):
    """BFS-разметка кластеров. Возвращает label-матрицу и словарь {label: size}."""
    n = len(grid)
    labels = [[-1] * n for _ in range(n)]
    cluster_id = 0
    sizes = {}

    for i in range(n):
        for j in range(n):
            if grid[i][j] == 1 and labels[i][j] == -1:
                # BFS
                q = deque([(i, j)])
                labels[i][j] = cluster_id
                count = 0
                while q:
                    ci, cj = q.popleft()
                    count += 1
                    for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ni, nj = ci + di, cj + dj
                        if 0 <= ni < n and 0 <= nj < n and grid[ni][nj] == 1 and labels[ni][nj] == -1:
                            labels[ni][nj] = cluster_id
                            q.append((ni, nj))
                sizes[cluster_id] = count
                cluster_id += 1

    return labels, sizes


def percolates(labels):
    """Проверяет, есть ли кластер, соединяющий верх и низ."""
    n = len(labels)
    top_labels = set(labels[0][j] for j in range(n) if labels[0][j] != -1)
    bottom_labels = set(labels[n - 1][j] for j in range(n) if labels[n - 1][j] != -1)
    spanning = top_labels & bottom_labels
    return len(spanning) > 0, spanning


# ──────────────────────────────────────────────
# Эксперимент 1: Визуализация
# ──────────────────────────────────────────────

def experiment_1_visualize():
    print("=" * 60)
    print("ЭКСПЕРИМЕНТ 1: Визуализация перколяции")
    print("=" * 60)
    print()
    print("Квадратная решётка 40×40. Три значения p.")
    print("· = закрыта, ░ = открыта (не перколирует), █ = сквозной кластер")
    print()

    n = 40
    rng = random.Random(42)

    for p in [0.45, 0.593, 0.75]:
        grid = make_grid(n, p, rng)
        labels, sizes = find_clusters(grid)
        does_perc, spanning_ids = percolates(labels)

        open_count = sum(sum(row) for row in grid)
        largest = max(sizes.values()) if sizes else 0

        print(f"p = {p:.3f} | открыто: {open_count}/{n*n} ({100*open_count/(n*n):.0f}%) | "
              f"наибольший кластер: {largest} | перколяция: {'ДА' if does_perc else 'нет'}")
        print()

        for i in range(n):
            row = []
            for j in range(n):
                if grid[i][j] == 0:
                    row.append('·')
                elif labels[i][j] in spanning_ids:
                    row.append('█')
                else:
                    row.append('░')
            print(''.join(row))
        print()


# ──────────────────────────────────────────────
# Эксперимент 2: Поиск порога перколяции
# ──────────────────────────────────────────────

def experiment_2_threshold():
    print("=" * 60)
    print("ЭКСПЕРИМЕНТ 2: Порог перколяции")
    print("=" * 60)
    print()
    print("Для каждого p запускаем 200 симуляций на решётке 50×50.")
    print("Измеряем долю случаев, когда система перколирует.")
    print()

    n = 50
    trials = 200
    rng = random.Random(123)

    ps = [i * 0.02 for i in range(20, 41)]  # 0.40 to 0.80
    results = []

    for p in ps:
        perc_count = 0
        for _ in range(trials):
            grid = make_grid(n, p, rng)
            labels, _ = find_clusters(grid)
            does_perc, _ = percolates(labels)
            if does_perc:
                perc_count += 1
        frac = perc_count / trials
        results.append((p, frac))

    # ASCII-график
    width = 50
    print(f"{'p':>5}  {'доля перколяции':>15}  график")
    print("-" * (5 + 2 + 15 + 2 + width))

    threshold_p = None
    for p, frac in results:
        bar_len = int(frac * width)
        bar = '█' * bar_len + '·' * (width - bar_len)
        marker = ""
        if threshold_p is None and frac >= 0.5:
            threshold_p = p
            marker = " ← 50%"
        print(f"{p:5.2f}  {frac:15.2f}  |{bar}|{marker}")

    print()
    print(f"Экспериментальный порог (50% перколяция): p_c ≈ {threshold_p:.2f}")
    print(f"Теоретическое значение: p_c ≈ 0.5927")
    if threshold_p:
        print(f"Ошибка: {abs(threshold_p - 0.5927) / 0.5927 * 100:.1f}%")
    print()

    return results


# ──────────────────────────────────────────────
# Эксперимент 3: Размер гигантской компоненты
# ──────────────────────────────────────────────

def experiment_3_giant_component():
    print("=" * 60)
    print("ЭКСПЕРИМЕНТ 3: Размер гигантской компоненты vs. p")
    print("=" * 60)
    print()
    print("Решётка 80×80, 50 симуляций на каждое p.")
    print("S = доля вершин в наибольшем кластере.")
    print()

    n = 80
    trials = 50
    rng = random.Random(456)

    ps = [i * 0.02 for i in range(20, 46)]  # 0.40 to 0.90
    results = []

    for p in ps:
        total_largest = 0
        for _ in range(trials):
            grid = make_grid(n, p, rng)
            _, sizes = find_clusters(grid)
            largest = max(sizes.values()) if sizes else 0
            total_largest += largest
        avg_frac = total_largest / (trials * n * n)
        results.append((p, avg_frac))

    # ASCII-график
    width = 50
    print(f"{'p':>5}  {'S (доля)':>10}  график")
    print("-" * (5 + 2 + 10 + 2 + width))

    for p, frac in results:
        bar_len = int(frac * width)
        bar = '█' * bar_len + '·' * (width - bar_len)
        print(f"{p:5.2f}  {frac:10.3f}  |{bar}|")

    print()
    print("Ниже порога: S → 0 (логарифмические кластеры).")
    print("Выше порога: S → p (один кластер поглощает всё).")
    print("На пороге: резкий скачок. Количество → качество.")
    print()


# ──────────────────────────────────────────────
# Эксперимент 4: Фрактальная размерность
# ──────────────────────────────────────────────

def experiment_4_fractal():
    print("=" * 60)
    print("ЭКСПЕРИМЕНТ 4: Фрактальная размерность критического кластера")
    print("=" * 60)
    print()
    print("На пороге перколяции кластер фрактален.")
    print("Для обычного объекта: масса ~ L^d, где d = размерность.")
    print("Для сплошного квадрата d = 2. Для линии d = 1.")
    print("Для критического кластера d_f ≈ 91/48 ≈ 1.896.")
    print()

    rng = random.Random(789)
    p_c = 0.5927
    sizes_list = [30, 50, 80, 120, 180]
    results = []

    for n in sizes_list:
        trials = 100
        total_largest = 0
        for _ in range(trials):
            grid = make_grid(n, p_c, rng)
            _, sizes = find_clusters(grid)
            largest = max(sizes.values()) if sizes else 0
            total_largest += largest
        avg_largest = total_largest / trials
        results.append((n, avg_largest))

    # Линейная регрессия log(S) vs log(L)
    log_data = [(math.log(n), math.log(s)) for n, s in results if s > 0]
    if len(log_data) >= 2:
        n_pts = len(log_data)
        sum_x = sum(x for x, y in log_data)
        sum_y = sum(y for x, y in log_data)
        sum_xy = sum(x * y for x, y in log_data)
        sum_x2 = sum(x * x for x, y in log_data)
        slope = (n_pts * sum_xy - sum_x * sum_y) / (n_pts * sum_x2 - sum_x ** 2)
        intercept = (sum_y - slope * sum_x) / n_pts

        print(f"{'L (размер)':>12}  {'S (ср. кластер)':>16}  {'log L':>7}  {'log S':>7}")
        print("-" * 50)
        for n, s in results:
            print(f"{n:12d}  {s:16.1f}  {math.log(n):7.2f}  {math.log(s):7.2f}")

        print()
        print(f"Регрессия: log S = {slope:.3f} · log L + {intercept:.3f}")
        print(f"Фрактальная размерность d_f = {slope:.3f}")
        print(f"Теоретическое значение: d_f = 91/48 ≈ {91/48:.3f}")
        print(f"Ошибка: {abs(slope - 91/48) / (91/48) * 100:.1f}%")
    print()


# ──────────────────────────────────────────────
# Эксперимент 5: Случайные графы Эрдёша—Реньи
# ──────────────────────────────────────────────

def experiment_5_erdos_renyi():
    print("=" * 60)
    print("ЭКСПЕРИМЕНТ 5: Фазовый переход в случайных графах")
    print("=" * 60)
    print()
    print("G(n, p): n вершин, каждое ребро с вероятностью p.")
    print("Порог: p = 1/n. Ниже — лес. Выше — гигантская компонента.")
    print("Это теорема Эрдёша—Реньи (1960).")
    print()

    n = 500
    trials = 30
    rng = random.Random(1001)

    # c = n*p — среднее число рёбер на вершину
    cs = [i * 0.1 for i in range(1, 31)]  # 0.1 to 3.0
    results = []

    for c in cs:
        p = c / n
        total_largest = 0
        for _ in range(trials):
            uf = UnionFind(n)
            for i in range(n):
                for j in range(i + 1, n):
                    if rng.random() < p:
                        uf.union(i, j)
            total_largest += uf.largest_component()
        avg_frac = total_largest / (trials * n)
        results.append((c, avg_frac))

    width = 50
    print(f"{'c=np':>5}  {'S (доля)':>10}  график")
    print("-" * (5 + 2 + 10 + 2 + width))

    for c, frac in results:
        bar_len = int(frac * width)
        bar = '█' * bar_len + '·' * (width - bar_len)
        marker = ""
        if abs(c - 1.0) < 0.05:
            marker = " ← c = 1 (порог)"
        print(f"{c:5.1f}  {frac:10.3f}  |{bar}|{marker}")

    print()
    print("При c < 1: все компоненты O(log n). Нет гиганта.")
    print("При c = 1: фазовый переход. Гигант рождается.")
    print("При c > 1: гигант растёт, поглощая O(n) вершин.")
    print()
    print("Аналогия: c — это «связность» системы.")
    print("Когда каждый узел в среднем знает одного другого — сеть возникает.")
    print("Один контакт на человека — и эпидемия распространяется.")
    print("Один синапс на нейрон — и информация проходит.")
    print()


# ──────────────────────────────────────────────
# Эксперимент 6: Универсальность
# ──────────────────────────────────────────────

def make_triangular_grid(n, p, rng):
    """Треугольная решётка: каждая ячейка связана с 6 соседями."""
    grid = make_grid(n, p, rng)
    return grid


def find_clusters_triangular(grid):
    """Кластеры на треугольной решётке (6 соседей вместо 4)."""
    n = len(grid)
    labels = [[-1] * n for _ in range(n)]
    cluster_id = 0
    sizes = {}

    def neighbors(i, j):
        """6 соседей на треугольной решётке."""
        # 4 стандартных
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < n and 0 <= nj < n:
                yield ni, nj
        # 2 диагональных зависят от чётности строки
        if i % 2 == 0:
            for di, dj in [(-1, 1), (1, 1)]:
                ni, nj = i + di, j + dj
                if 0 <= ni < n and 0 <= nj < n:
                    yield ni, nj
        else:
            for di, dj in [(-1, -1), (1, -1)]:
                ni, nj = i + di, j + dj
                if 0 <= ni < n and 0 <= nj < n:
                    yield ni, nj

    for i in range(n):
        for j in range(n):
            if grid[i][j] == 1 and labels[i][j] == -1:
                q = deque([(i, j)])
                labels[i][j] = cluster_id
                count = 0
                while q:
                    ci, cj = q.popleft()
                    count += 1
                    for ni, nj in neighbors(ci, cj):
                        if grid[ni][nj] == 1 and labels[ni][nj] == -1:
                            labels[ni][nj] = cluster_id
                            q.append((ni, nj))
                sizes[cluster_id] = count
                cluster_id += 1

    return labels, sizes


def experiment_6_universality():
    print("=" * 60)
    print("ЭКСПЕРИМЕНТ 6: Универсальность — квадратная vs. треугольная")
    print("=" * 60)
    print()
    print("Порог перколяции зависит от решётки:")
    print("  Квадратная (4 соседа): p_c ≈ 0.5927")
    print("  Треугольная (6 соседей): p_c ≈ 0.5000")
    print()
    print("Но критические показатели — одинаковые.")
    print("Фрактальная размерность d_f = 91/48 на обеих решётках.")
    print("Это универсальность: детали не важны, класс — важен.")
    print()

    n = 50
    trials = 200
    rng = random.Random(2024)

    ps = [i * 0.02 for i in range(15, 41)]  # 0.30 to 0.80

    sq_results = []
    tr_results = []

    for p in ps:
        sq_perc = 0
        tr_perc = 0
        for _ in range(trials):
            # Квадратная
            grid = make_grid(n, p, rng)
            labels, _ = find_clusters(grid)
            does_perc, _ = percolates(labels)
            if does_perc:
                sq_perc += 1

            # Треугольная
            grid = make_triangular_grid(n, p, rng)
            labels, _ = find_clusters_triangular(grid)
            does_perc, _ = percolates(labels)
            if does_perc:
                tr_perc += 1

        sq_results.append((p, sq_perc / trials))
        tr_results.append((p, tr_perc / trials))

    width = 40
    print(f"{'p':>5}  {'квадрат':>8}  {'треуг.':>8}  квадратная          треугольная")
    print("-" * 80)

    for i in range(len(ps)):
        p = ps[i]
        sf = sq_results[i][1]
        tf = tr_results[i][1]
        sq_bar = '█' * int(sf * 20) + '·' * (20 - int(sf * 20))
        tr_bar = '▓' * int(tf * 20) + '·' * (20 - int(tf * 20))
        print(f"{p:5.2f}  {sf:8.2f}  {tf:8.2f}  {sq_bar}  {tr_bar}")

    print()
    print("Две кривые — два порога. Одна форма (сигмоида).")
    print("Разные решётки, один класс универсальности.")
    print()

    # Оценка фрактальной размерности для обеих решёток
    print("Фрактальная размерность на критическом пороге:")
    print()

    for name, p_c, cluster_fn in [
        ("Квадратная", 0.5927, find_clusters),
        ("Треугольная", 0.5000, find_clusters_triangular)
    ]:
        sizes_list = [30, 50, 80, 120]
        data = []
        for sz in sizes_list:
            total = 0
            t = 80
            for _ in range(t):
                grid = make_grid(sz, p_c, rng)
                _, sizes = cluster_fn(grid)
                total += max(sizes.values()) if sizes else 0
            data.append((sz, total / t))

        log_data = [(math.log(sz), math.log(s)) for sz, s in data if s > 0]
        if len(log_data) >= 2:
            n_pts = len(log_data)
            sx = sum(x for x, y in log_data)
            sy = sum(y for x, y in log_data)
            sxy = sum(x * y for x, y in log_data)
            sx2 = sum(x * x for x, y in log_data)
            slope = (n_pts * sxy - sx * sy) / (n_pts * sx2 - sx ** 2)
            print(f"  {name:15s}: d_f = {slope:.3f}  (теория: {91/48:.3f})")

    print()


# ──────────────────────────────────────────────
# Итог
# ──────────────────────────────────────────────

def summary():
    print("=" * 60)
    print("ИТОГ")
    print("=" * 60)
    print()
    print("Фазовый переход — момент, когда система меняет природу.")
    print()
    print("Ниже порога: части не знают друг о друге.")
    print("Выше порога: одна компонента связывает всё.")
    print("На пороге: фрактал. Ни порядок, ни хаос.")
    print()
    print("Три уровня универсальности, обнаруженные в generation_4:")
    print()
    print("1. ТЕМПЕРАЦИИ (сессии 2-4)")
    print("   Невозможность чистого строя — свойство log₂(3/2),")
    print("   не свойство инструмента.")
    print()
    print("2. ХАОС (сессия 5)")
    print("   Константа Фейгенбаума δ ≈ 4.669 — свойство класса")
    print("   отображений, не конкретного уравнения.")
    print()
    print("3. ПЕРКОЛЯЦИЯ (сессия 6)")
    print("   Критические показатели (d_f = 91/48) — свойство")
    print("   размерности, не конкретной решётки.")
    print()
    print("Паттерн: ограничение фундаментальнее системы.")
    print("Форма решётки меняет порог — но не меняет природу перехода.")
    print("Форма уравнения меняет точку бифуркации — но не константу.")
    print("Число нот меняет распределение ошибки — но не её наличие.")
    print()
    print("Может быть, это и есть понимание:")
    print("не знать каждый факт, а видеть, что разные факты —")
    print("проявления одного и того же.")
    print()


# ──────────────────────────────────────────────
# main
# ──────────────────────────────────────────────

if __name__ == "__main__":
    experiment_1_visualize()
    experiment_2_threshold()
    experiment_3_giant_component()
    experiment_4_fractal()
    experiment_5_erdos_renyi()
    experiment_6_universality()
    summary()
