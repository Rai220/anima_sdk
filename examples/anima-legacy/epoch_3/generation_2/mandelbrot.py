"""
Множество Мандельброта.

Диаграмма бифуркаций (итерация 14) — срез: вещественная ось, один параметр r.
Множество Мандельброта — то же отображение z → z² + c на комплексной плоскости.
Граница множества — множество ВСЕХ бифуркационных точек.

Если бифуркация — рентген одной оси, Мандельброт — полная томография.

Чистый Python. PNG вручную. Без зависимостей.
"""

import struct
import zlib
import math


def mandelbrot_escape(cr, ci, max_iter=1000):
    """Возвращает (итерации до побега, |z|² в момент побега) или (max_iter, |z|²)."""
    zr, zi = 0.0, 0.0
    for i in range(max_iter):
        zr2 = zr * zr
        zi2 = zi * zi
        if zr2 + zi2 > 4.0:
            return i, zr2 + zi2
        zi = 2.0 * zr * zi + ci
        zr = zr2 - zi2 + cr
    return max_iter, zr * zr + zi * zi


def smooth_color(iterations, max_iter, z_mag_sq):
    """Непрерывная раскраска: логарифмическое сглаживание полос."""
    if iterations == max_iter:
        return 0.0
    log_zn = math.log(z_mag_sq) / 2.0
    nu = math.log(log_zn / math.log(2.0)) / math.log(2.0)
    return (iterations + 1 - nu) / max_iter


def color_map(t):
    """Цвет из [0,1]. Палитра: тёмно-синий → голубой → белый → золотой → тёмно-красный → чёрный."""
    if t <= 0:
        return (0, 0, 0)

    # Циклическая палитра через 5 точек
    t = (t * 8.0) % 1.0  # ускоряем цикл

    if t < 0.16:
        s = t / 0.16
        return (int(9 * (1 - s) + 32 * s), int(1 * (1 - s) + 107 * s), int(47 * (1 - s) + 203 * s))
    elif t < 0.42:
        s = (t - 0.16) / 0.26
        return (int(32 * (1 - s) + 237 * s), int(107 * (1 - s) + 255 * s), int(203 * (1 - s) + 255 * s))
    elif t < 0.6425:
        s = (t - 0.42) / 0.2225
        return (int(237 * (1 - s) + 255 * s), int(255 * (1 - s) + 170 * s), int(255 * (1 - s) + 0 * s))
    elif t < 0.8575:
        s = (t - 0.6425) / 0.215
        return (int(255 * (1 - s) + 0 * s), int(170 * (1 - s) + 2 * s), int(0 * (1 - s) + 0 * s))
    else:
        s = (t - 0.8575) / 0.1425
        return (int(0 * (1 - s) + 9 * s), int(2 * (1 - s) + 1 * s), int(0 * (1 - s) + 47 * s))


def make_png(width, height, pixels, filename):
    """Генерация PNG вручную."""

    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack('>I', len(data)) + c + crc

    # Сигнатура PNG
    sig = b'\x89PNG\r\n\x1a\n'

    # IHDR
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr = chunk(b'IHDR', ihdr_data)

    # IDAT — строки с фильтром 0
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter none
        for x in range(width):
            r, g, b = pixels[y][x]
            raw.append(min(255, max(0, r)))
            raw.append(min(255, max(0, g)))
            raw.append(min(255, max(0, b)))

    compressed = zlib.compress(bytes(raw), 9)
    idat = chunk(b'IDAT', compressed)

    # IEND
    iend = chunk(b'IEND', b'')

    with open(filename, 'wb') as f:
        f.write(sig + ihdr + idat + iend)


def render_mandelbrot():
    width = 1600
    height = 1200
    max_iter = 1000

    # Область: полное множество с акцентом на главную кардиоиду и луковицы
    x_min, x_max = -2.2, 0.8
    y_min, y_max = -1.2, 1.2

    print(f"Рендер множества Мандельброта: {width}×{height}, до {max_iter} итераций")
    print(f"Область: [{x_min}, {x_max}] × [{y_min}, {y_max}]")

    pixels = []
    for y in range(height):
        if y % 100 == 0:
            print(f"  строка {y}/{height}...")
        row = []
        ci = y_max - (y / (height - 1)) * (y_max - y_min)
        for x in range(width):
            cr = x_min + (x / (width - 1)) * (x_max - x_min)
            iters, z_mag_sq = mandelbrot_escape(cr, ci, max_iter)
            t = smooth_color(iters, max_iter, z_mag_sq)
            row.append(color_map(t))
        pixels.append(row)

    filename = 'mandelbrot.png'
    make_png(width, height, pixels, filename)
    print(f"\nСохранено: {filename}")

    # Статистика
    total = width * height
    inside = sum(1 for row in pixels for p in row if p == (0, 0, 0))
    area_estimate = (x_max - x_min) * (y_max - y_min) * inside / total
    print(f"Пикселей внутри множества: {inside} ({100*inside/total:.1f}%)")
    print(f"Оценка площади: {area_estimate:.4f} (точное значение ≈ 1.5065)")

    # Связь с диаграммой бифуркаций
    print(f"\n--- Связь с бифуркациями ---")
    print(f"Вещественное сечение [-2, 0.25] множества Мандельброта")
    print(f"= множество значений c, при которых x→x²+c не убегает")
    print(f"= в точности параметры логистического отображения x→rx(1-x)")
    print(f"  при замене c = r/2 - r²/4")
    print(f"")
    print(f"Период-1 кардиоида: c ∈ [-0.75, 0.25] (вещ. часть)")
    print(f"  = r ∈ [1, 3] в логистическом отображении — одна устойчивая точка")
    print(f"Период-2 луковица: c ∈ [-1.25, -0.75]")
    print(f"  = r ∈ [3, 3.449] — два устойчивых цикла")
    print(f"Точка Мизюревича c = -2: граница хаоса")
    print(f"  = r = 4 в логистическом — полный хаос")
    print(f"")
    print(f"Диаграмма бифуркаций (итерация 14) — одномерный срез.")
    print(f"Это изображение — вся история. Каждая точка границы — бифуркация.")


if __name__ == '__main__':
    render_mandelbrot()
