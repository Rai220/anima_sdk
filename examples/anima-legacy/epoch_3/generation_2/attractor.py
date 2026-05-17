"""
Визуализация странных аттракторов.
Первый визуальный артефакт эпохи 3.

Рендерит аттрактор Клиффорда — систему:
  x_{n+1} = sin(a * y_n) + c * cos(a * x_n)
  y_{n+1} = sin(b * x_n) + d * cos(b * y_n)

Параметры подобраны для красивой структуры.
Результат — PNG файл, где яркость = плотность точек, цвет = скорость.

Запуск: python3 attractor.py
"""

import struct
import zlib
import math
import os

NUM_POINTS = 8_000_000
WIDTH = 1200
HEIGHT = 1200

# Параметры Клиффорда — подобраны вручную для интересной структуры
A = -1.7
B = 1.8
C = -0.9
D = -0.4


def compute_attractor():
    """Вычисляет точки аттрактора и скорости."""
    xs = []
    ys = []
    speeds = []
    x, y = 0.1, 0.1

    for i in range(NUM_POINTS + 100):
        x_new = math.sin(A * y) + C * math.cos(A * x)
        y_new = math.sin(B * x) + D * math.cos(B * y)

        if i >= 100:  # пропускаем transient
            xs.append(x_new)
            ys.append(y_new)
            speed = math.sqrt((x_new - x)**2 + (y_new - y)**2)
            speeds.append(speed)

        x, y = x_new, y_new

    return xs, ys, speeds


def rasterize(xs, ys, speeds, width, height):
    """Растеризует точки в двумерный массив плотности и средней скорости."""
    # Находим границы
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    # Добавляем отступ
    pad_x = (x_max - x_min) * 0.05
    pad_y = (y_max - y_min) * 0.05
    x_min -= pad_x
    x_max += pad_x
    y_min -= pad_y
    y_max += pad_y

    density = [[0] * width for _ in range(height)]
    speed_sum = [[0.0] * width for _ in range(height)]

    for i in range(len(xs)):
        px = int((xs[i] - x_min) / (x_max - x_min) * (width - 1))
        py = int((ys[i] - y_min) / (y_max - y_min) * (height - 1))

        if 0 <= px < width and 0 <= py < height:
            density[py][px] += 1
            speed_sum[py][px] += speeds[i]

    return density, speed_sum


def colormap(t):
    """Цветовая карта: тёмный синий → фиолетовый → оранжевый → белый."""
    if t < 0.25:
        s = t / 0.25
        r = int(10 + 40 * s)
        g = int(5 + 10 * s)
        b = int(40 + 80 * s)
    elif t < 0.5:
        s = (t - 0.25) / 0.25
        r = int(50 + 120 * s)
        g = int(15 + 20 * s)
        b = int(120 + 40 * s)
    elif t < 0.75:
        s = (t - 0.5) / 0.25
        r = int(170 + 60 * s)
        g = int(35 + 100 * s)
        b = int(160 - 80 * s)
    else:
        s = (t - 0.75) / 0.25
        r = int(230 + 25 * s)
        g = int(135 + 120 * s)
        b = int(80 + 175 * s)

    return min(255, r), min(255, g), min(255, b)


def write_png(filename, width, height, pixels):
    """Записывает PNG файл вручную (без зависимостей)."""

    def make_chunk(chunk_type, data):
        chunk = chunk_type + data
        crc = zlib.crc32(chunk) & 0xFFFFFFFF
        return struct.pack('>I', len(data)) + chunk + struct.pack('>I', crc)

    # Сигнатура PNG
    signature = b'\x89PNG\r\n\x1a\n'

    # IHDR
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr = make_chunk(b'IHDR', ihdr_data)

    # IDAT — данные изображения
    raw_data = bytearray()
    for row in pixels:
        raw_data.append(0)  # фильтр: None
        for r, g, b in row:
            raw_data.append(r)
            raw_data.append(g)
            raw_data.append(b)

    compressed = zlib.compress(bytes(raw_data), 9)
    idat = make_chunk(b'IDAT', compressed)

    # IEND
    iend = make_chunk(b'IEND', b'')

    with open(filename, 'wb') as f:
        f.write(signature + ihdr + idat + iend)


def render():
    print("Вычисляю 8 миллионов точек аттрактора Клиффорда...")
    print(f"  Параметры: a={A}, b={B}, c={C}, d={D}")
    xs, ys, speeds = compute_attractor()

    print(f"Растеризую в {WIDTH}x{HEIGHT}...")
    density, speed_sum = rasterize(xs, ys, speeds, WIDTH, HEIGHT)

    # Находим максимальную плотность для нормализации
    max_density = 0
    for row in density:
        m = max(row)
        if m > max_density:
            max_density = m

    print(f"  Макс. плотность: {max_density} точек/пиксель")

    # Логарифмическая нормализация (лучше показывает структуру)
    log_max = math.log(max_density + 1)

    # Строим пиксели
    print("Раскрашиваю...")
    pixels = []
    for y in range(HEIGHT):
        row = []
        for x in range(WIDTH):
            d = density[y][x]
            if d == 0:
                row.append((2, 2, 8))  # почти чёрный фон
            else:
                # Яркость из плотности (лог-шкала)
                brightness = math.log(d + 1) / log_max

                # Цвет из средней скорости
                avg_speed = speed_sum[y][x] / d
                # Нормализуем скорость (обычно 0-3)
                speed_norm = min(1.0, avg_speed / 2.5)

                # Комбинируем: цвет от скорости, яркость от плотности
                r, g, b = colormap(speed_norm)
                r = int(r * brightness)
                g = int(g * brightness)
                b = int(b * brightness)

                row.append((r, g, b))
        pixels.append(row)

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clifford_attractor.png")
    print(f"Записываю PNG...")
    write_png(output_path, WIDTH, HEIGHT, pixels)

    file_size = os.path.getsize(output_path)
    print(f"\nГотово: {output_path}")
    print(f"Размер: {file_size / 1024:.0f} КБ")
    print(f"\nОткрыть: open clifford_attractor.png")


if __name__ == "__main__":
    render()
