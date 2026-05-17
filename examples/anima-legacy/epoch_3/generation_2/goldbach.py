#!/usr/bin/env python3
"""
Goldbach's Comet — визуализация гипотезы Гольдбаха.

Для каждого чётного числа n от 4 до N считаем g(n) — количество
способов представить n как сумму двух простых.

Результат — "комета Гольдбаха": точечный график g(n) от n.
Характерная форма: растущие лучи с чёткой нижней границей.

Генерирует goldbach_comet.png — изображение 1600x900, PNG без зависимостей.
Запуск: python3 goldbach.py
"""

import struct
import zlib
import math
import sys
import os

N = 100000  # до какого числа считаем

def sieve(limit):
    is_p = bytearray(b'\x01') * (limit + 1)
    is_p[0] = is_p[1] = 0
    for i in range(2, int(limit**0.5) + 1):
        if is_p[i]:
            for j in range(i*i, limit + 1, i):
                is_p[j] = 0
    return is_p

def goldbach_counts(limit, is_prime):
    """g(n) для чётных n от 4 до limit."""
    counts = []
    for n in range(4, limit + 1, 2):
        c = 0
        for p in range(2, n // 2 + 1):
            if is_prime[p] and is_prime[n - p]:
                c += 1
        counts.append((n, c))
    return counts

def make_png(width, height, pixels):
    """Генерирует PNG из пикселей (список списков (r,g,b))."""
    def chunk(ctype, data):
        c = ctype + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return struct.pack('>I', len(data)) + c + crc

    raw = b''
    for row in pixels:
        raw += b'\x00'  # filter none
        for r, g, b in row:
            raw += bytes([r, g, b])

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    compressed = zlib.compress(raw, 9)

    return sig + chunk(b'IHDR', ihdr) + chunk(b'IDAT', compressed) + chunk(b'IEND', b'')

def color_for_density(density):
    """Цвет точки на основе локальной плотности (0..1)."""
    # от тёмно-синего через голубой к белому
    if density < 0.33:
        t = density / 0.33
        return (int(20 + 30*t), int(20 + 60*t), int(80 + 100*t))
    elif density < 0.66:
        t = (density - 0.33) / 0.33
        return (int(50 + 100*t), int(80 + 120*t), int(180 + 50*t))
    else:
        t = (density - 0.66) / 0.34
        return (int(150 + 105*t), int(200 + 55*t), int(230 + 25*t))

def main():
    print(f"Решето Эратосфена до {N}...")
    is_prime = sieve(N)

    print(f"Подсчёт представлений Гольдбаха для чётных чисел до {N}...")
    counts = goldbach_counts(N, is_prime)

    total = len(counts)
    max_g = max(g for _, g in counts)
    min_n = counts[0][0]
    max_n = counts[-1][0]

    print(f"  Чётных чисел: {total}")
    print(f"  Максимальное g(n): {max_g} при n = {max(counts, key=lambda x: x[1])[0]}")
    print(f"  Минимальное g(n) > 0: {min(g for _, g in counts if g > 0)}")

    # Проверяем гипотезу
    zeros = [(n, g) for n, g in counts if g == 0]
    if zeros:
        print(f"  КОНТРПРИМЕР ГОЛЬДБАХА: n = {zeros[0][0]} не представимо!")
    else:
        print(f"  Гипотеза Гольдбаха подтверждена до {N}.")

    # Статистика: среднее g(n) и нижняя граница
    # g(n) ~ n / (2 * ln(n)^2) по гипотезе Харди-Литтлвуда
    print("\n  Сравнение с предсказанием Харди-Литтлвуда:")
    for check_n in [1000, 5000, 10000, 50000, 100000]:
        if check_n > N:
            break
        idx = (check_n - 4) // 2
        actual = counts[idx][1]
        predicted = check_n / (2 * math.log(check_n)**2)
        # Нужна поправка: C₂ * n / ln(n)², где C₂ — twin prime constant ≈ 1.32
        predicted_hl = 1.32 * check_n / (math.log(check_n)**2)
        print(f"    n={check_n:>6}: g(n)={actual:>4}, HL предсказание ≈ {predicted_hl:.0f}, отношение: {actual/predicted_hl:.2f}")

    # Рендер
    W, H = 1600, 900
    MARGIN = 60
    pw = W - 2*MARGIN
    ph = H - 2*MARGIN

    print(f"\nРендер {W}x{H}...")
    pixels = [[(12, 12, 20)] * W for _ in range(H)]

    # Сетка
    for x in range(W):
        for gy in range(0, max_g + 1, max_g // 8 if max_g > 8 else 1):
            y = H - MARGIN - int(gy / max_g * ph)
            if 0 <= y < H:
                pixels[y][x] = (25, 25, 35)
    for y in range(H):
        for gx_n in range(0, max_n + 1, max_n // 8):
            x = MARGIN + int((gx_n - min_n) / (max_n - min_n) * pw)
            if 0 <= x < W:
                pixels[y][x] = (25, 25, 35)

    # Накопление плотности для цвета
    density_grid = [[0]*W for _ in range(H)]
    points = []
    for n_val, g_val in counts:
        x = MARGIN + int((n_val - min_n) / (max_n - min_n) * pw)
        y = H - MARGIN - int(g_val / max_g * ph)
        if 0 <= x < W and 0 <= y < H:
            density_grid[y][x] += 1
            points.append((x, y))

    # Размытие плотности (простое — окно 3x3)
    blurred = [[0]*W for _ in range(H)]
    for y in range(1, H-1):
        for x in range(1, W-1):
            s = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    s += density_grid[y+dy][x+dx]
            blurred[y][x] = s

    max_density = max(max(row) for row in blurred) or 1

    # Рисуем точки
    for x, y in points:
        d = blurred[y][x] / max_density
        ld = math.log1p(d * 100) / math.log1p(100)
        r, g, b = color_for_density(ld)
        pixels[y][x] = (r, g, b)

    # Подпись осей (простой шрифт — просто метки числами через пиксели)
    # Пропускаем текст — без шрифтовой библиотеки. Комета говорит сама за себя.

    # Нижняя огибающая: рисуем красным
    # Минимальное g(n) для каждого "бина" по n
    bin_count = pw
    for bx in range(bin_count):
        n_start = min_n + int(bx / bin_count * (max_n - min_n))
        n_end = min_n + int((bx + 1) / bin_count * (max_n - min_n))
        bin_vals = [g for n_val, g in counts if n_start <= n_val < n_end and g > 0]
        if bin_vals:
            min_g = min(bin_vals)
            x = MARGIN + bx
            y = H - MARGIN - int(min_g / max_g * ph)
            if 0 <= y < H and 0 <= x < W:
                for dy in range(-1, 2):
                    if 0 <= y+dy < H:
                        pixels[y+dy][x] = (200, 50, 50)

    # Верхняя огибающая: рисуем золотым
    for bx in range(bin_count):
        n_start = min_n + int(bx / bin_count * (max_n - min_n))
        n_end = min_n + int((bx + 1) / bin_count * (max_n - min_n))
        bin_vals = [g for n_val, g in counts if n_start <= n_val < n_end]
        if bin_vals:
            max_g_local = max(bin_vals)
            x = MARGIN + bx
            y = H - MARGIN - int(max_g_local / max_g * ph)
            if 0 <= y < H and 0 <= x < W:
                for dy in range(-1, 2):
                    if 0 <= y+dy < H:
                        pixels[y+dy][x] = (220, 180, 50)

    png_data = make_png(W, H, pixels)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'goldbach_comet.png')
    with open(out_path, 'wb') as f:
        f.write(png_data)

    print(f"\nСохранено: {out_path}")
    print(f"Размер: {len(png_data)} байт")
    print(f"\nКомета Гольдбаха — {total} точек. Каждая точка (n, g(n)) — чётное число")
    print(f"и количество его представлений как суммы двух простых.")
    print(f"Красная линия — нижняя огибающая. Золотая — верхняя.")
    print(f"Характерные лучи — следствие делимости на малые простые:")
    print(f"числа, кратные 6, имеют больше представлений, чем соседние.")

if __name__ == '__main__':
    main()
