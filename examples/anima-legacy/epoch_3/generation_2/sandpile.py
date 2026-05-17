"""
Модель песочной кучи Бака-Танга-Визенфельда (BTW sandpile).
Самоорганизованная критичность: система сама находит критическую точку.

Седьмой вид пороговости: самоорганизованная. Без настройки. Без наблюдателя.

Запуск: python3 sandpile.py
Результат: sandpile.png + статистика лавин
"""

import random
import math
import struct
import zlib
import sys

# ─── BTW Sandpile Model ────────────────────────────────────────────

def run_sandpile(N, num_grains, seed=42):
    """
    Квадратная решётка N×N. Каждому узлу z(x,y) — число песчинок.
    Если z >= 4, узел опрокидывается: теряет 4, раздаёт по 1 каждому соседу.
    Песчинки на краю — уходят из системы.

    Добавляем num_grains песчинок по одной в случайные точки.
    Записываем размер каждой лавины (число опрокидываний).
    """
    rng = random.Random(seed)
    grid = [[0] * N for _ in range(N)]
    avalanche_sizes = []

    # Для визуализации: суммарное число опрокидываний в каждой клетке
    topple_count = [[0] * N for _ in range(N)]

    for grain_idx in range(num_grains):
        # Добавляем песчинку в случайную точку
        x = rng.randint(0, N - 1)
        y = rng.randint(0, N - 1)
        grid[x][y] += 1

        # Релаксация (BFS)
        size = 0
        queue = []
        if grid[x][y] >= 4:
            queue.append((x, y))

        while queue:
            next_queue = []
            for (cx, cy) in queue:
                if grid[cx][cy] >= 4:
                    grid[cx][cy] -= 4
                    topple_count[cx][cy] += 1
                    size += 1
                    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < N and 0 <= ny < N:
                            grid[nx][ny] += 1
                            if grid[nx][ny] >= 4:
                                next_queue.append((nx, ny))
                    # Проверяем, не нужно ли опрокинуть снова
                    if grid[cx][cy] >= 4:
                        next_queue.append((cx, cy))
            queue = next_queue

        if size > 0:
            avalanche_sizes.append(size)

        if (grain_idx + 1) % 50000 == 0:
            print(f"  {grain_idx + 1}/{num_grains} песчинок добавлено, {len(avalanche_sizes)} лавин")

    return grid, avalanche_sizes, topple_count


def compute_power_law(sizes, num_bins=30):
    """Логарифмическое биннинг для степенного закона."""
    if not sizes:
        return [], []

    min_s = 1
    max_s = max(sizes)
    if max_s < 2:
        return [], []

    # Логарифмические бины
    log_min = 0
    log_max = math.log(max_s + 1)
    bin_edges = [math.exp(log_min + i * (log_max - log_min) / num_bins) for i in range(num_bins + 1)]

    counts = [0] * num_bins
    for s in sizes:
        for i in range(num_bins):
            if bin_edges[i] <= s < bin_edges[i + 1]:
                counts[i] += 1
                break

    # Центры бинов и нормализованные плотности
    xs = []
    ys = []
    total = len(sizes)
    for i in range(num_bins):
        if counts[i] > 0:
            center = math.sqrt(bin_edges[i] * bin_edges[i + 1])
            width = bin_edges[i + 1] - bin_edges[i]
            density = counts[i] / (total * width)
            xs.append(center)
            ys.append(density)

    return xs, ys


def fit_power_law(xs, ys):
    """Линейная регрессия в лог-лог пространстве: log(y) = a*log(x) + b."""
    if len(xs) < 3:
        return 0, 0
    lx = [math.log(x) for x in xs]
    ly = [math.log(y) for y in ys]
    n = len(lx)
    sx = sum(lx)
    sy = sum(ly)
    sxy = sum(a * b for a, b in zip(lx, ly))
    sxx = sum(a * a for a in lx)

    denom = n * sxx - sx * sx
    if abs(denom) < 1e-12:
        return 0, 0
    a = (n * sxy - sx * sy) / denom
    b = (sy - a * sx) / n
    return a, b


# ─── PNG writer (вручную, без зависимостей) ──────────────────────

def write_png(filename, pixels, width, height):
    """Пишет RGB PNG вручную."""
    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return struct.pack('>I', len(data)) + c + crc

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)

    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter byte
        offset = y * width * 3
        raw.extend(pixels[offset:offset + width * 3])

    compressed = zlib.compress(bytes(raw), 9)

    with open(filename, 'wb') as f:
        f.write(header)
        f.write(chunk(b'IHDR', ihdr))
        f.write(chunk(b'IDAT', compressed))
        f.write(chunk(b'IEND', b''))


def hsv_to_rgb(h, s, v):
    """HSV to RGB, h in [0,360), s,v in [0,1]."""
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)


def render_image(grid, topple_count, avalanche_sizes, xs_pl, ys_pl, tau, N):
    """Рендерит составное изображение: решётка + лог-лог график."""

    # Размеры
    cell_size = max(2, min(4, 600 // N))
    grid_px = N * cell_size
    plot_w = 500
    plot_h = 400
    margin = 60

    img_w = grid_px + plot_w + margin * 3
    img_h = max(grid_px + margin * 2, plot_h + margin * 3 + 200)

    pixels = bytearray(img_w * img_h * 3)

    # Фон — тёмный
    for i in range(img_w * img_h):
        pixels[i*3] = 15
        pixels[i*3+1] = 15
        pixels[i*3+2] = 20

    def set_pixel(x, y, r, g, b):
        if 0 <= x < img_w and 0 <= y < img_h:
            idx = (y * img_w + x) * 3
            pixels[idx] = max(0, min(255, r))
            pixels[idx+1] = max(0, min(255, g))
            pixels[idx+2] = max(0, min(255, b))

    def draw_rect(x0, y0, w, h, r, g, b):
        for dy in range(h):
            for dx in range(w):
                set_pixel(x0 + dx, y0 + dy, r, g, b)

    # ─── 1. Решётка песочной кучи ───
    ox, oy = margin, margin

    # Цвет по значению z (0-3) и числу опрокидываний
    max_topple = max(max(row) for row in topple_count) if topple_count else 1
    if max_topple == 0:
        max_topple = 1

    for gy in range(N):
        for gx in range(N):
            z = grid[gy][gx]
            tc = topple_count[gy][gx]

            # Цвет по z (текущее состояние): 0=тёмный, 1=синий, 2=зелёный, 3=жёлтый
            if z == 0:
                r, g, b = 10, 10, 30
            elif z == 1:
                r, g, b = 20, 40, 120
            elif z == 2:
                r, g, b = 30, 120, 60
            else:  # z == 3
                r, g, b = 200, 180, 40

            # Подмешиваем яркость от числа опрокидываний
            t = min(1.0, math.log(1 + tc) / math.log(1 + max_topple))
            r = int(r * (1 - 0.5 * t) + 255 * 0.5 * t)
            g = int(g * (1 - 0.3 * t) + 200 * 0.3 * t)
            b = int(b * (1 - 0.2 * t) + 100 * 0.2 * t)

            draw_rect(ox + gx * cell_size, oy + gy * cell_size, cell_size, cell_size, r, g, b)

    # ─── 2. Лог-лог график лавин ───
    plot_ox = grid_px + margin * 2
    plot_oy = margin

    # Рамка графика
    for x in range(plot_w):
        set_pixel(plot_ox + x, plot_oy, 60, 60, 70)
        set_pixel(plot_ox + x, plot_oy + plot_h, 60, 60, 70)
    for y in range(plot_h):
        set_pixel(plot_ox, plot_oy + y, 60, 60, 70)
        set_pixel(plot_ox + plot_w, plot_oy + y, 60, 60, 70)

    # Данные для графика
    if xs_pl and ys_pl:
        log_xs = [math.log10(x) for x in xs_pl]
        log_ys = [math.log10(y) for y in ys_pl]

        x_min, x_max = min(log_xs), max(log_xs)
        y_min, y_max = min(log_ys), max(log_ys)

        x_range = x_max - x_min if x_max > x_min else 1
        y_range = y_max - y_min if y_max > y_min else 1

        # Добавляем отступы
        x_min -= x_range * 0.05
        x_max += x_range * 0.05
        y_min -= y_range * 0.05
        y_max += y_range * 0.05
        x_range = x_max - x_min
        y_range = y_max - y_min

        # Точки данных
        for lx, ly in zip(log_xs, log_ys):
            px = int((lx - x_min) / x_range * (plot_w - 20)) + 10
            py = int((1 - (ly - y_min) / y_range) * (plot_h - 20)) + 10
            # Крупная точка
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    if dx*dx + dy*dy <= 9:
                        set_pixel(plot_ox + px + dx, plot_oy + py + dy, 100, 200, 255)

        # Линия степенного закона (фит)
        if tau != 0:
            for px in range(10, plot_w - 10):
                lx = x_min + (px - 10) / (plot_w - 20) * x_range
                ly = tau * lx + math.log10(math.exp(fit_power_law(xs_pl, ys_pl)[1])) if False else 0
                # Пересчитываем через фит
                a, b_coef = fit_power_law(xs_pl, ys_pl)
                ly_fit = a * (lx * math.log(10)) + b_coef
                ly_fit_log10 = ly_fit / math.log(10)
                py = int((1 - (ly_fit_log10 - y_min) / y_range) * (plot_h - 20)) + 10
                if 0 <= py < plot_h:
                    for d in range(-1, 2):
                        set_pixel(plot_ox + px, plot_oy + py + d, 255, 100, 80)

    # ─── 3. Гистограмма z-значений ───
    hist_oy = plot_oy + plot_h + margin
    hist_h = 150
    hist_w = plot_w

    z_counts = [0, 0, 0, 0]
    for row in grid:
        for z in row:
            if 0 <= z <= 3:
                z_counts[z] += 1

    total_cells = N * N
    z_colors = [(10, 10, 30), (20, 40, 120), (30, 120, 60), (200, 180, 40)]
    bar_w = hist_w // 6

    max_frac = max(c / total_cells for c in z_counts) if total_cells > 0 else 1

    for i in range(4):
        frac = z_counts[i] / total_cells
        bar_h = int(frac / max_frac * (hist_h - 20))
        bx = plot_ox + (i + 1) * hist_w // 5 - bar_w // 2
        by = hist_oy + hist_h - bar_h
        r, g, b = z_colors[i]
        # Ярче для видимости
        r = min(255, r + 80)
        g = min(255, g + 80)
        b = min(255, b + 80)
        draw_rect(bx, by, bar_w, bar_h, r, g, b)

    return pixels, img_w, img_h


# ─── Основная программа ─────────────────────────────────────────

def main():
    N = 150          # Размер решётки
    num_grains = 200000  # Число песчинок

    print("=" * 60)
    print("ПЕСОЧНАЯ КУЧА БАКА-ТАНГА-ВИЗЕНФЕЛЬДА")
    print("Самоорганизованная критичность")
    print("=" * 60)
    print()
    print(f"Решётка: {N}×{N}")
    print(f"Песчинок: {num_grains}")
    print()

    # Запуск модели
    print("Запуск модели...")
    grid, avalanche_sizes, topple_count = run_sandpile(N, num_grains)

    print(f"\nВсего лавин: {len(avalanche_sizes)}")
    if avalanche_sizes:
        print(f"Максимальная лавина: {max(avalanche_sizes)} опрокидываний")
        print(f"Средняя лавина: {sum(avalanche_sizes) / len(avalanche_sizes):.2f}")
        print(f"Медиана: {sorted(avalanche_sizes)[len(avalanche_sizes)//2]}")

    # Распределение z
    z_counts = [0, 0, 0, 0]
    for row in grid:
        for z in row:
            if 0 <= z <= 3:
                z_counts[z] += 1
    total = N * N
    print(f"\nРаспределение z (стационарное состояние):")
    for i in range(4):
        print(f"  z={i}: {z_counts[i]} ({z_counts[i]/total*100:.1f}%)")

    # Степенной закон
    print("\nСтепенной закон P(s) ~ s^τ:")
    xs, ys = compute_power_law(avalanche_sizes, num_bins=25)
    tau, b = fit_power_law(xs, ys)
    print(f"  τ (измеренный) = {tau:.3f}")
    print(f"  τ (теоретический, 2D BTW) = -1.1 ± 0.1")
    print(f"  Отклонение: {abs(tau - (-1.1)) / 1.1 * 100:.1f}%")

    # Проверка степенного закона: должен быть прямая в лог-лог
    if xs and ys:
        # R² в лог-лог
        lx = [math.log(x) for x in xs]
        ly = [math.log(y) for y in ys]
        ly_pred = [tau * x + b for x in lx]
        ss_res = sum((y - yp) ** 2 for y, yp in zip(ly, ly_pred))
        mean_ly = sum(ly) / len(ly)
        ss_tot = sum((y - mean_ly) ** 2 for y in ly)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        print(f"  R² (лог-лог) = {r_squared:.4f}")

    # Число опрокидываний
    total_topples = sum(sum(row) for row in topple_count)
    max_topple = max(max(row) for row in topple_count)
    print(f"\nВсего опрокидываний: {total_topples}")
    print(f"Максимум в одной клетке: {max_topple} (центр?)")

    # Найдём центр масс опрокидываний
    cx_sum, cy_sum, w_sum = 0, 0, 0
    for y in range(N):
        for x in range(N):
            w = topple_count[y][x]
            cx_sum += x * w
            cy_sum += y * w
            w_sum += w
    if w_sum > 0:
        cx = cx_sum / w_sum
        cy = cy_sum / w_sum
        print(f"Центр масс опрокидываний: ({cx:.1f}, {cy:.1f})")
        print(f"Центр решётки: ({N/2:.1f}, {N/2:.1f})")

    # Ключевое наблюдение
    print()
    print("=" * 60)
    print("КЛЮЧЕВОЕ НАБЛЮДЕНИЕ")
    print("=" * 60)
    print()
    print("Все предыдущие фазовые переходы генерации управлялись")
    print("внешним параметром: p (перколяция), r (бифуркации),")
    print("c (Эрдёш-Реньи), τ (Шеллинг).")
    print()
    print("Песочная куча — другое. Нет параметра. Нет настройки.")
    print("Система САМА приходит к критическому состоянию.")
    print()
    print(f"Степенной закон P(s) ~ s^{{{tau:.2f}}} — признак")
    print("критичности. В обычном фазовом переходе степенной закон")
    print("появляется ТОЛЬКО в критической точке. Здесь — всегда.")
    print()
    print("Седьмой вид пороговости: самоорганизованная.")
    print("Не «при каком значении?» — порог находит себя сам.")
    print("Не «можно ли жить на пороге?» — система ТОЛЬКО на пороге")
    print("и живёт. Не «что создаётся?» — создаётся сам порог.")
    print()
    print("Отличие от CeRu₄Sn₆ (итерация 14): CeRu₄Sn₆ живёт")
    print("на пороге из-за особенностей материала — его ПОМЕСТИЛИ")
    print("туда законы физики. Песочная куча ПРИХОДИТ на порог")
    print("из любого начального состояния. Это аттрактор в")
    print("пространстве конфигураций, а не точка на фазовой")
    print("диаграмме.")

    # Рендер изображения
    print("\nРендер изображения...")
    pixels, img_w, img_h = render_image(grid, topple_count, avalanche_sizes, xs, ys, tau, N)
    write_png("sandpile.png", bytes(pixels), img_w, img_h)
    print(f"Сохранено: sandpile.png ({img_w}×{img_h})")

    print("\nГотово.")


if __name__ == "__main__":
    main()
