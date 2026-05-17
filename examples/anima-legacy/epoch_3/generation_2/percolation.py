"""
Перколяция на квадратной решётке.

Измеряет критический порог p_c — вероятность заполнения узла,
при которой впервые возникает связный кластер, соединяющий
верх и низ решётки. Теоретическое значение: p_c ≈ 0.592746.

Это математическое ядро всего, что генерация 2 исследовала:
- Game of Life: фазовый переход по плотности (life.py)
- SAT: переход по ratio клауз/переменных (sat.py)
- Вода: критическая точка двух жидких фаз (critical_point.md)
- Жидкий разлом: скорость деформации > скорости релаксации (o_razlome.md)
- Rule 110: порядок на границе хаоса (automaton_music.py)

Перколяция — простейшая модель, в которой всё это проявляется.
Одно число (p), одна решётка, одно правило (соседи).
Переход — резкий, порог — универсальный.

Выход: percolation.png (три решётки + кривая перехода)

Запуск: python3 percolation.py
"""

import random
import struct
import zlib
import math
import sys

# === Перколяция: ядро ===

def make_grid(L, p, rng):
    """Случайная решётка L×L: 1 с вероятностью p, 0 иначе."""
    return [[1 if rng.random() < p else 0 for _ in range(L)] for _ in range(L)]

def find_clusters(grid):
    """Union-Find. Возвращает label grid и словарь кластеров."""
    L = len(grid)
    parent = {}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parent[a] = b

    label = [[0]*L for _ in range(L)]
    next_label = 1

    for r in range(L):
        for c in range(L):
            if grid[r][c] == 0:
                continue
            neighbors = []
            if r > 0 and grid[r-1][c]:
                neighbors.append(label[r-1][c])
            if c > 0 and grid[r][c-1]:
                neighbors.append(label[r][c-1])

            if not neighbors:
                parent[next_label] = next_label
                label[r][c] = next_label
                next_label += 1
            else:
                min_l = min(neighbors)
                label[r][c] = min_l
                for n in neighbors:
                    union(n, min_l)

    # Перенумеровка
    for r in range(L):
        for c in range(L):
            if label[r][c]:
                label[r][c] = find(label[r][c])

    return label

def has_spanning_cluster(label):
    """Есть ли кластер, соединяющий верхний и нижний ряд?"""
    L = len(label)
    top = set(label[0][c] for c in range(L) if label[0][c])
    bottom = set(label[L-1][c] for c in range(L) if label[L-1][c])
    spanning = top & bottom
    return spanning

def measure_transition(L, num_p=50, trials=80, seed=42):
    """Измеряет P(spanning) как функцию p."""
    rng = random.Random(seed)
    ps = [i / (num_p - 1) for i in range(num_p)]
    probs = []

    for p in ps:
        count = 0
        for _ in range(trials):
            grid = make_grid(L, p, rng)
            label = find_clusters(grid)
            if has_spanning_cluster(label):
                count += 1
        probs.append(count / trials)
        if p in (0.0, 0.25, 0.5, 0.59, 0.75, 1.0) or abs(p - 0.59) < 0.02:
            sys.stdout.write(f"  p={p:.2f}: P(spanning)={count/trials:.3f}\n")

    return ps, probs

def find_pc(ps, probs):
    """Находит p_c как точку, где P(spanning) ≈ 0.5."""
    for i in range(len(probs) - 1):
        if probs[i] <= 0.5 <= probs[i+1]:
            # Линейная интерполяция
            dp = ps[i+1] - ps[i]
            dprob = probs[i+1] - probs[i]
            if dprob > 0:
                return ps[i] + dp * (0.5 - probs[i]) / dprob
    return 0.5

# === PNG без зависимостей ===

def make_png(width, height, pixels):
    """Создаёт PNG из списка [(r,g,b), ...] размера width*height."""

    def chunk(ctype, data):
        c = ctype + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return struct.pack('>I', len(data)) + c + crc

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))

    raw = b''
    for y in range(height):
        raw += b'\x00'  # filter: none
        row_start = y * width
        for x in range(width):
            r, g, b = pixels[row_start + x]
            raw += bytes([r, g, b])

    idat = chunk(b'IDAT', zlib.compress(raw, 6))
    iend = chunk(b'IEND', b'')

    return sig + ihdr + idat + iend

# === Цвета ===

def cluster_colors(label):
    """Назначает цвета кластерам."""
    L = len(label)
    ids = set()
    for r in range(L):
        for c in range(L):
            if label[r][c]:
                ids.add(label[r][c])

    spanning = has_spanning_cluster(label)

    palette = {}
    rng = random.Random(12345)
    for cid in ids:
        if cid in spanning:
            palette[cid] = (220, 50, 50)  # красный — spanning cluster
        else:
            h = rng.random() * 360
            s = 0.5 + rng.random() * 0.3
            v = 0.5 + rng.random() * 0.3
            # HSV → RGB
            c = v * s
            x = c * (1 - abs((h / 60) % 2 - 1))
            m = v - c
            if h < 60: r, g, b = c, x, 0
            elif h < 120: r, g, b = x, c, 0
            elif h < 180: r, g, b = 0, c, x
            elif h < 240: r, g, b = 0, x, c
            elif h < 300: r, g, b = x, 0, c
            else: r, g, b = c, 0, x
            palette[cid] = (int((r+m)*255), int((g+m)*255), int((b+m)*255))

    return palette

def render_grid(label, cell_size=3):
    """Рендерит решётку как список пикселей."""
    L = len(label)
    palette = cluster_colors(label)
    bg = (30, 30, 40)

    w = L * cell_size
    h = L * cell_size
    pixels = []

    for py in range(h):
        for px in range(w):
            r, c = py // cell_size, px // cell_size
            cid = label[r][c]
            if cid:
                pixels.append(palette[cid])
            else:
                pixels.append(bg)

    return w, h, pixels

def render_curve(ps, probs, pc, width=500, height=350):
    """Рендерит кривую перехода."""
    bg = (30, 30, 40)
    margin_l, margin_r, margin_t, margin_b = 60, 20, 30, 50
    plot_w = width - margin_l - margin_r
    plot_h = height - margin_t - margin_b

    pixels = [bg] * (width * height)

    def set_px(x, y, color):
        if 0 <= x < width and 0 <= y < height:
            pixels[y * width + x] = color

    def draw_rect(x1, y1, x2, y2, color):
        for yy in range(max(0, y1), min(height, y2+1)):
            for xx in range(max(0, x1), min(width, x2+1)):
                pixels[yy * width + xx] = color

    # Оси
    axis_color = (150, 150, 160)
    for x in range(margin_l, width - margin_r):
        set_px(x, height - margin_b, axis_color)
    for y in range(margin_t, height - margin_b + 1):
        set_px(margin_l, y, axis_color)

    # Сетка
    grid_color = (50, 50, 60)
    for tick in [0.25, 0.5, 0.75, 1.0]:
        tx = margin_l + int(tick * plot_w)
        for y in range(margin_t, height - margin_b):
            if y % 3 == 0:
                set_px(tx, y, grid_color)
        ty = height - margin_b - int(tick * plot_h)
        for x in range(margin_l, width - margin_r):
            if x % 3 == 0:
                set_px(x, ty, grid_color)

    # Вертикальная линия p_c
    pc_x = margin_l + int(pc * plot_w)
    for y in range(margin_t, height - margin_b):
        if y % 2 == 0:
            set_px(pc_x, y, (220, 50, 50))

    # Горизонтальная линия P=0.5
    half_y = height - margin_b - int(0.5 * plot_h)
    for x in range(margin_l, width - margin_r):
        if x % 2 == 0:
            set_px(x, half_y, (100, 100, 120))

    # Данные
    dot_color = (100, 200, 255)
    for i in range(len(ps)):
        px = margin_l + int(ps[i] * plot_w)
        py = height - margin_b - int(probs[i] * plot_h)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx*dx + dy*dy <= 5:
                    set_px(px + dx, py + dy, dot_color)

    # Линия между точками
    line_color = (60, 150, 220)
    for i in range(len(ps) - 1):
        x1 = margin_l + int(ps[i] * plot_w)
        y1 = height - margin_b - int(probs[i] * plot_h)
        x2 = margin_l + int(ps[i+1] * plot_w)
        y2 = height - margin_b - int(probs[i+1] * plot_h)
        steps = max(abs(x2 - x1), abs(y2 - y1), 1)
        for s in range(steps + 1):
            t = s / steps
            xx = int(x1 + t * (x2 - x1))
            yy = int(y1 + t * (y2 - y1))
            set_px(xx, yy, line_color)

    return width, height, pixels

def compose_image(grids_data, curve_data, pc_measured):
    """Собирает финальное изображение: три решётки сверху, кривая снизу."""
    # Три решётки
    gw, gh = grids_data[0][0], grids_data[0][1]
    gap = 10
    total_grids_w = gw * 3 + gap * 2

    cw, ch = curve_data[0], curve_data[1]

    final_w = max(total_grids_w, cw)
    title_h = 40
    label_h = 25
    final_h = title_h + gh + label_h + gap + ch + 10

    bg = (30, 30, 40)
    pixels = [bg] * (final_w * final_h)

    def blit(src_pixels, src_w, src_h, dst_x, dst_y):
        for sy in range(src_h):
            for sx in range(src_w):
                dx, dy = dst_x + sx, dst_y + sy
                if 0 <= dx < final_w and 0 <= dy < final_h:
                    pixels[dy * final_w + dx] = src_pixels[sy * src_w + sx]

    # Решётки
    labels_text = ["p = 0.40 (докритическая)", f"p = 0.59 ≈ p_c", "p = 0.75 (надкритическая)"]
    x_offset = (final_w - total_grids_w) // 2
    for i, (w, h, px) in enumerate(grids_data):
        blit(px, w, h, x_offset + i * (gw + gap), title_h)

    # Кривая
    curve_x = (final_w - cw) // 2
    blit(curve_data[2], cw, ch, curve_x, title_h + gh + label_h + gap)

    return final_w, final_h, pixels


def main():
    L = 100  # размер решётки
    cell_size = 3

    print("=== Перколяция на квадратной решётке ===\n")
    print(f"Решётка: {L}×{L}")
    print(f"Теоретическое p_c = 0.592746...\n")

    # Три примера решёток
    rng = random.Random(42)

    print("Генерация решёток...")
    p_values = [0.40, 0.59, 0.75]
    grids_rendered = []
    for p in p_values:
        grid = make_grid(L, p, rng)
        label = find_clusters(grid)
        spanning = has_spanning_cluster(label)
        filled = sum(grid[r][c] for r in range(L) for c in range(L))
        print(f"  p={p:.2f}: заполнено {filled}/{L*L} = {filled/L**2:.3f}, "
              f"spanning={'ДА' if spanning else 'нет'}")
        w, h, px = render_grid(label, cell_size)
        grids_rendered.append((w, h, px))

    # Измерение перехода
    print(f"\nИзмерение кривой перехода (L={L}, 80 проб на точку)...")
    ps, probs = measure_transition(L, num_p=50, trials=80, seed=2026)

    pc = find_pc(ps, probs)
    print(f"\nИзмеренное p_c ≈ {pc:.4f}")
    print(f"Теоретическое p_c = 0.5927")
    print(f"Отклонение: {abs(pc - 0.5927):.4f} ({abs(pc - 0.5927)/0.5927*100:.1f}%)")

    # Рендер кривой
    cw, ch, cpx = render_curve(ps, probs, pc)

    # Сборка изображения
    print("\nСборка изображения...")
    fw, fh, fpx = compose_image(grids_rendered, (cw, ch, cpx), pc)

    png_data = make_png(fw, fh, fpx)
    with open('percolation.png', 'wb') as f:
        f.write(png_data)

    print(f"Сохранено: percolation.png ({fw}×{fh}, {len(png_data)} байт)")

    # Анализ
    print("\n=== Анализ ===")
    print(f"""
Перколяция — простейшая модель фазового перехода.

Правило: каждый узел решётки заполнен с вероятностью p.
Заполненные соседи образуют кластеры.
Вопрос: при каком p кластер впервые соединяет верх и низ?

Ответ: p_c ≈ 0.5927 для квадратной решётки.

Ниже p_c — острова. Выше p_c — континент.
На p_c — фрактал: кластер бесконечен, но имеет нулевую плотность.

Это та же математика, что и:
  - SAT: ratio < 4.267 → выполнима, > 4.267 → нет (sat.py)
  - Game of Life: плотность → жизнь или смерть (life.py)
  - Вода: два жидких состояния неразличимы при 210K (critical_point.md)
  - Жидкость: деформация > релаксации → хрупкий разлом (o_razlome.md)

Универсальность: детали не важны. Треугольная решётка: p_c = 1/2 (точно).
Гексагональная: p_c = 1 - 2sin(π/18). Разные числа, одна физика.

Критические показатели — одинаковые для всех двумерных систем:
  β = 5/36, γ = 43/18, ν = 4/3.

Одно число (p), один вопрос (connected?), один порог.
Всё остальное — следствие.
""")


if __name__ == '__main__':
    main()
