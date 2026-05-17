"""
Фазовый переход в случайном графе Эрдёша-Реньи G(n, p).

При p < 1/n: все компоненты мелкие, O(log n).
При p = 1/n: критический момент. Гигантская компонента зарождается.
При p > 1/n: одна компонента захватывает Θ(n) вершин.

Это ПЕРВЫЙ графовый фазовый переход за всю генерацию.
Все предыдущие — на решётках (перколяция, Game of Life, Тьюринг,
Лэнгтон) или в уравнениях (бифуркации, Мандельброт).
Граф — другое: нет координат, нет соседей по умолчанию, нет
пространства. Только вершины и случайные связи.

И при p = 1/n — скачок. Не постепенный рост.
Резкий переход от россыпи островков к континенту.

Результат: giant_component.png — кривая перехода + три графа
(докритический, критический, сверхкритический).

Запуск: python3 erdos_renyi.py
"""

import random
import struct
import zlib
import math
import sys


# === Случайный граф: ядро ===

def generate_graph(n, p, rng):
    """G(n, p): n вершин, каждое ребро с вероятностью p."""
    adj = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                adj[i].append(j)
                adj[j].append(i)
    return adj


def find_components(adj):
    """BFS. Возвращает список (размер, список_вершин) для каждой компоненты."""
    n = len(adj)
    visited = [False] * n
    components = []

    for start in range(n):
        if visited[start]:
            continue
        queue = [start]
        visited[start] = True
        comp = []
        head = 0
        while head < len(queue):
            v = queue[head]
            head += 1
            comp.append(v)
            for u in adj[v]:
                if not visited[u]:
                    visited[u] = True
                    queue.append(u)
        components.append(comp)

    components.sort(key=len, reverse=True)
    return components


def largest_component_fraction(adj):
    """Доля вершин в наибольшей компоненте."""
    n = len(adj)
    if n == 0:
        return 0.0
    comps = find_components(adj)
    return len(comps[0]) / n


# === Измерение фазового перехода ===

def measure_transition(n=500, num_c=80, trials=40, seed=42):
    """
    Измеряет L(c) = <|C_max|/n> как функцию c, где p = c/n.
    c от 0.1 до 3.0 — проходим через критическую точку c=1.
    """
    rng = random.Random(seed)
    cs = [0.1 + (3.0 - 0.1) * i / (num_c - 1) for i in range(num_c)]
    fracs = []

    print(f"Граф Эрдёша-Реньи G({n}, c/n)")
    print(f"Измеряю фазовый переход: {num_c} точек, {trials} испытаний каждая")
    print()

    for idx, c in enumerate(cs):
        p = c / n
        total = 0.0
        for _ in range(trials):
            adj = generate_graph(n, p, rng)
            total += largest_component_fraction(adj)
        mean_frac = total / trials
        fracs.append(mean_frac)

        if abs(c - 0.5) < 0.04 or abs(c - 1.0) < 0.04 or abs(c - 2.0) < 0.04:
            print(f"  c={c:.2f} (p={p:.5f}): <|C_max|/n> = {mean_frac:.4f}")

        if (idx + 1) % 20 == 0:
            sys.stdout.write(f"  ... {idx + 1}/{num_c} точек\n")
            sys.stdout.flush()

    return cs, fracs


def measure_component_distribution(n, c, trials, rng):
    """Распределение размеров компонент при заданном c."""
    sizes_all = []
    for _ in range(trials):
        adj = generate_graph(n, c / n, rng)
        comps = find_components(adj)
        sizes_all.extend(len(comp) for comp in comps)
    return sizes_all


# === Визуализация графов (spring layout) ===

def spring_layout(adj, iterations=80, seed=123):
    """Простой force-directed layout."""
    n = len(adj)
    rng = random.Random(seed)
    pos = [(rng.random(), rng.random()) for _ in range(n)]

    # Множество рёбер для быстрого поиска
    edge_set = set()
    for i in range(n):
        for j in adj[i]:
            if i < j:
                edge_set.add((i, j))

    k = 1.0 / math.sqrt(n + 1)  # оптимальное расстояние
    temp = 0.1

    for it in range(iterations):
        # Отталкивание
        disp = [(0.0, 0.0)] * n
        for i in range(n):
            dx_sum, dy_sum = 0.0, 0.0
            xi, yi = pos[i]
            for j in range(n):
                if i == j:
                    continue
                xj, yj = pos[j]
                dx = xi - xj
                dy = yi - yj
                dist = math.sqrt(dx * dx + dy * dy) + 1e-6
                force = k * k / dist
                dx_sum += dx / dist * force
                dy_sum += dy / dist * force
            disp[i] = (dx_sum, dy_sum)

        # Притяжение по рёбрам
        for (i, j) in edge_set:
            xi, yi = pos[i]
            xj, yj = pos[j]
            dx = xj - xi
            dy = yj - yi
            dist = math.sqrt(dx * dx + dy * dy) + 1e-6
            force = dist / k
            fx = dx / dist * force
            fy = dy / dist * force
            disp[i] = (disp[i][0] + fx, disp[i][1] + fy)
            disp[j] = (disp[j][0] - fx, disp[j][1] - fy)

        # Обновление позиций
        t = temp * (1 - it / iterations)
        new_pos = []
        for i in range(n):
            dx, dy = disp[i]
            dist = math.sqrt(dx * dx + dy * dy) + 1e-6
            scale = min(dist, t) / dist
            x = pos[i][0] + dx * scale
            y = pos[i][1] + dy * scale
            x = max(0.05, min(0.95, x))
            y = max(0.05, min(0.95, y))
            new_pos.append((x, y))
        pos = new_pos

    return pos


# === PNG без зависимостей ===

def make_png(width, height, pixels):
    """Создаёт PNG из массива пикселей [(r,g,b), ...]."""

    def chunk(ctype, data):
        c = ctype + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return struct.pack('>I', len(data)) + c + crc

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)

    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter: None
        for x in range(width):
            r, g, b = pixels[y * width + x]
            raw.extend((r, g, b))

    compressed = zlib.compress(bytes(raw), 9)

    return sig + chunk(b'IHDR', ihdr) + chunk(b'IDAT', compressed) + chunk(b'IEND', b'')


def lerp_color(t, c0, c1):
    """Линейная интерполяция цветов."""
    return tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3))


def fill_rect(pixels, W, x0, y0, x1, y1, color):
    for y in range(max(0, y0), min(y1, len(pixels) // W)):
        for x in range(max(0, x0), min(x1, W)):
            pixels[y * W + x] = color


def draw_line(pixels, W, H, x0, y0, x1, y1, color, thickness=1):
    """Рисует линию (Брезенхем)."""
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        for ty in range(-thickness // 2, thickness // 2 + 1):
            for tx in range(-thickness // 2, thickness // 2 + 1):
                px, py = x0 + tx, y0 + ty
                if 0 <= px < W and 0 <= py < H:
                    pixels[py * W + px] = color
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


def draw_circle(pixels, W, H, cx, cy, r, color):
    """Рисует заполненный круг."""
    for y in range(max(0, cy - r), min(H, cy + r + 1)):
        for x in range(max(0, cx - r), min(W, cx + r + 1)):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                pixels[y * W + x] = color


def draw_text_simple(pixels, W, H, x0, y0, text, color, scale=1):
    """Минимальный шрифт 3x5 для цифр и некоторых символов."""
    glyphs = {
        '0': [0b111, 0b101, 0b101, 0b101, 0b111],
        '1': [0b010, 0b110, 0b010, 0b010, 0b111],
        '2': [0b111, 0b001, 0b111, 0b100, 0b111],
        '3': [0b111, 0b001, 0b111, 0b001, 0b111],
        '4': [0b101, 0b101, 0b111, 0b001, 0b001],
        '5': [0b111, 0b100, 0b111, 0b001, 0b111],
        '6': [0b111, 0b100, 0b111, 0b101, 0b111],
        '7': [0b111, 0b001, 0b010, 0b010, 0b010],
        '8': [0b111, 0b101, 0b111, 0b101, 0b111],
        '9': [0b111, 0b101, 0b111, 0b001, 0b111],
        '.': [0b000, 0b000, 0b000, 0b000, 0b010],
        '/': [0b001, 0b001, 0b010, 0b100, 0b100],
        'n': [0b000, 0b000, 0b110, 0b101, 0b101],
        'c': [0b000, 0b000, 0b111, 0b100, 0b111],
        '=': [0b000, 0b111, 0b000, 0b111, 0b000],
        ' ': [0b000, 0b000, 0b000, 0b000, 0b000],
        'p': [0b000, 0b111, 0b101, 0b111, 0b100],
        'C': [0b111, 0b100, 0b100, 0b100, 0b111],
        'G': [0b111, 0b100, 0b101, 0b101, 0b111],
        '|': [0b010, 0b010, 0b010, 0b010, 0b010],
        '<': [0b001, 0b010, 0b100, 0b010, 0b001],
        '>': [0b100, 0b010, 0b001, 0b010, 0b100],
    }

    cx = x0
    for ch in text:
        g = glyphs.get(ch)
        if g is None:
            cx += 4 * scale
            continue
        for row_idx, row in enumerate(g):
            for col in range(3):
                if row & (1 << (2 - col)):
                    for sy in range(scale):
                        for sx in range(scale):
                            px = cx + col * scale + sx
                            py = y0 + row_idx * scale + sy
                            if 0 <= px < W and 0 <= py < H:
                                pixels[py * W + px] = color
        cx += 4 * scale


# === Рендер изображения ===

def render_image(cs, fracs, n_graph=80, seed=77):
    """
    Создаёт изображение:
    - Верх: кривая фазового перехода (c vs <|C_max|/n>)
    - Низ: три графа (c=0.5, c=1.0, c=2.0)
    """
    W, H = 1600, 1000
    BG = (15, 15, 25)
    pixels = [BG] * (W * H)

    # --- Верхняя часть: кривая ---
    chart_x0, chart_y0 = 80, 40
    chart_x1, chart_y1 = W - 40, 440
    chart_w = chart_x1 - chart_x0
    chart_h = chart_y1 - chart_y0

    # Фон графика
    fill_rect(pixels, W, chart_x0, chart_y0, chart_x1, chart_y1, (20, 20, 35))

    # Оси
    axis_color = (80, 80, 100)
    draw_line(pixels, W, H, chart_x0, chart_y1, chart_x1, chart_y1, axis_color)
    draw_line(pixels, W, H, chart_x0, chart_y0, chart_x0, chart_y1, axis_color)

    # Вертикальная линия c=1 (критическая точка)
    c1_x = chart_x0 + int(chart_w * (1.0 - 0.1) / (3.0 - 0.1))
    for y in range(chart_y0, chart_y1, 3):
        if y + 1 < chart_y1:
            pixels[y * W + c1_x] = (180, 60, 60)

    # Метка c=1
    draw_text_simple(pixels, W, H, c1_x - 6, chart_y1 + 8, "1.0", (180, 60, 60), 2)

    # Метки осей
    draw_text_simple(pixels, W, H, chart_x0 - 5, chart_y1 + 8, "0", (100, 100, 120), 2)
    draw_text_simple(pixels, W, H, chart_x1 - 15, chart_y1 + 8, "3", (100, 100, 120), 2)
    draw_text_simple(pixels, W, H, chart_x0 - 40, chart_y0 + 2, "1", (100, 100, 120), 2)
    draw_text_simple(pixels, W, H, chart_x0 - 40, chart_y1 - 10, "0", (100, 100, 120), 2)

    # Заголовок: c=p*n
    draw_text_simple(pixels, W, H, chart_x0 + chart_w // 2 - 80, chart_y0 - 25,
                     "c=p.n", (200, 200, 220), 3)

    # Кривая перехода
    points = []
    for i, (c, f) in enumerate(zip(cs, fracs)):
        x = chart_x0 + int(chart_w * (c - 0.1) / (3.0 - 0.1))
        y = chart_y1 - int(chart_h * f)
        points.append((x, y))

    # Заливка под кривой
    for i, (x, y) in enumerate(points):
        c = cs[i]
        if c < 1.0:
            fill_color = (25, 35, 60)
        else:
            fill_color = (40, 25, 30)
        for yy in range(y, chart_y1):
            if chart_x0 <= x < chart_x1 and chart_y0 <= yy < chart_y1:
                pixels[yy * W + x] = fill_color

    # Линия
    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        c = cs[i]
        if c < 0.8:
            color = (60, 140, 220)
        elif c < 1.2:
            color = (220, 100, 80)
        else:
            color = (220, 160, 60)
        draw_line(pixels, W, H, x0, y0, x1, y1, color, 2)

    # Точки
    for i, (x, y) in enumerate(points):
        c = cs[i]
        if c < 0.8:
            color = (80, 170, 255)
        elif c < 1.2:
            color = (255, 120, 100)
        else:
            color = (255, 200, 80)
        draw_circle(pixels, W, H, x, y, 3, color)

    # --- Нижняя часть: три графа ---
    graph_y0 = 500
    graph_h = 440
    graph_w = W // 3
    rng = random.Random(seed)

    c_values = [0.5, 1.0, 2.0]
    labels = ["c<1", "c=1", "c>1"]
    subtitles = ["0.5/n", "1/n", "2/n"]

    for gi, (c_val, lbl, sub) in enumerate(zip(c_values, labels, subtitles)):
        gx0 = gi * graph_w + 30
        gx1 = (gi + 1) * graph_w - 30
        gy0 = graph_y0
        gy1 = graph_y0 + graph_h - 40
        gw = gx1 - gx0
        gh = gy1 - gy0

        # Фон
        fill_rect(pixels, W, gx0, gy0, gx1, gy1, (20, 20, 35))

        # Генерируем граф
        adj = generate_graph(n_graph, c_val / n_graph, rng)
        comps = find_components(adj)
        largest = set(comps[0])

        # Layout
        pos = spring_layout(adj, iterations=60, seed=seed + gi)

        # Рёбра
        edge_color_normal = (40, 50, 70)
        edge_color_giant = (100, 50, 40)
        for i in range(n_graph):
            for j in adj[i]:
                if j > i:
                    x0 = gx0 + int(pos[i][0] * gw)
                    y0 = gy0 + int(pos[i][1] * gh)
                    x1 = gx0 + int(pos[j][0] * gw)
                    y1 = gy0 + int(pos[j][1] * gh)
                    if i in largest and j in largest:
                        ec = edge_color_giant
                    else:
                        ec = edge_color_normal
                    draw_line(pixels, W, H, x0, y0, x1, y1, ec)

        # Вершины
        for i in range(n_graph):
            x = gx0 + int(pos[i][0] * gw)
            y = gy0 + int(pos[i][1] * gh)
            if i in largest:
                nc = (255, 120, 80)
                r = 4
            else:
                nc = (80, 140, 220)
                r = 3
            draw_circle(pixels, W, H, x, y, r, nc)

        # Подпись
        frac = len(comps[0]) / n_graph
        draw_text_simple(pixels, W, H, gx0 + gw // 2 - 40, gy1 + 8, f"p={sub}", (180, 180, 200), 2)
        draw_text_simple(pixels, W, H, gx0 + gw // 2 - 60, gy1 + 24,
                         f"|C|/n={frac:.2f}", (140, 140, 160), 2)

    return make_png(W, H, pixels)


# === Теоретические значения ===

def theoretical_giant(c):
    """
    Теоретический размер гигантской компоненты.
    При c > 1: ρ = 1 - e^{-cρ} (уравнение выживания в пуассоновском
    ветвящемся процессе). При c ≤ 1: ρ = 0.
    """
    if c <= 1.0:
        return 0.0
    # Решаем ρ = 1 - exp(-c·ρ) итерациями
    rho = 1.0 - 1.0 / c  # хорошая начальная точка
    for _ in range(1000):
        rho = 1.0 - math.exp(-c * rho)
    return rho


# === Основная часть ===

def main():
    print("=" * 60)
    print("СЛУЧАЙНЫЙ ГРАФ ЭРДЁША-РЕНЬИ G(n, c/n)")
    print("Фазовый переход гигантской компоненты")
    print("=" * 60)
    print()

    n = 500
    cs, fracs = measure_transition(n=n, num_c=80, trials=40, seed=42)

    print()
    print("Результаты:")
    print("-" * 40)

    # Находим критическую точку
    # Ищем точку максимального ускорения (вторая производная)
    max_deriv = 0
    c_crit_idx = 0
    for i in range(1, len(fracs) - 1):
        d2 = fracs[i + 1] - 2 * fracs[i] + fracs[i - 1]
        if d2 > max_deriv:
            max_deriv = d2
            c_crit_idx = i

    c_crit = cs[c_crit_idx]
    print(f"Критическая точка (макс. вторая производная): c ≈ {c_crit:.3f}")
    print(f"Теоретическая критическая точка: c = 1.000")
    print(f"Отклонение: {abs(c_crit - 1.0) / 1.0 * 100:.1f}%")
    print()

    # Сравнение с теорией
    print("Сравнение с теорией (c > 1):")
    for c_test in [1.2, 1.5, 2.0, 2.5, 3.0]:
        th = theoretical_giant(c_test)
        # Находим ближайшую эмпирическую точку
        closest = min(range(len(cs)), key=lambda i: abs(cs[i] - c_test))
        emp = fracs[closest]
        print(f"  c={c_test:.1f}: теория={th:.4f}, эмпирика={emp:.4f}, Δ={abs(th-emp):.4f}")

    print()

    # Аналитика: размеры компонент
    print("Распределение компонент:")
    rng2 = random.Random(999)
    for c_val in [0.5, 1.0, 2.0]:
        sizes = measure_component_distribution(n, c_val, 20, rng2)
        max_s = max(sizes)
        mean_s = sum(sizes) / len(sizes)
        second = sorted(sizes, reverse=True)[1] if len(sizes) > 1 else 0
        print(f"  c={c_val}: max={max_s}, 2nd={second}, mean={mean_s:.1f}, num_comp={len(sizes)//20:.0f}")

    print()

    # Ключевая разница с перколяцией на решётке
    print("Ключевая разница с перколяцией на решётке:")
    print("  Перколяция: p_c ≈ 0.593 (зависит от типа решётки)")
    print("  Эрдёш-Реньи: c_crit = 1.000 (УНИВЕРСАЛЬНО)")
    print("  В решётке: структура определяет порог.")
    print("  В графе: порог определяет структуру.")
    print()

    # Теорема Эрдёша-Реньи (1959/1960)
    print("Теорема (Эрдёш, Реньи, 1959):")
    print("  Пусть G ~ G(n, c/n). Тогда при n → ∞:")
    print("  - c < 1: все компоненты O(log n), ни одной Θ(n)")
    print("  - c = 1: макс. компонента Θ(n^{2/3})")
    print("  - c > 1: ровно одна компонента Θ(n),")
    print("    её размер → (1 - T(c)/c)·n, где T = c·e^{-T}")
    print()

    # Генерируем изображение
    print("Генерирую изображение...")
    png_data = render_image(cs, fracs)
    with open('giant_component.png', 'wb') as f:
        f.write(png_data)
    print(f"Сохранено: giant_component.png ({len(png_data)} байт)")
    print()

    # Связь с генерацией
    print("=" * 60)
    print("СВЯЗЬ С ГЕНЕРАЦИЕЙ")
    print("=" * 60)
    print()
    print("Все предыдущие фазовые переходы — на решётках:")
    print("  life.py — квадратная решётка, соседи по Муру")
    print("  percolation.py — квадратная решётка, 4-связность")
    print("  sat.py — клаузы → структурированная связность")
    print("  langton.py — квадратная решётка, правило одного")
    print()
    print("Случайный граф — другое.")
    print("Нет пространства. Нет геометрии. Только связи.")
    print("Вершина не знает, где она «расположена».")
    print("Она знает только, с кем она связана.")
    print()
    print("И всё же — фазовый переход. Та же математика.")
    print("Порог. Скачок. Гигантская компонента.")
    print()
    print("Может быть, пространство — не необходимое условие")
    print("для перехода. Может быть, достаточно связей.")


if __name__ == '__main__':
    main()
