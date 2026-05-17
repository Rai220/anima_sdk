"""
Правило 110 → изображение + звук.

Элементарный клеточный автомат (Rule 110) — один из простейших систем,
способных к универсальным вычислениям (доказано Мэтью Куком в 2004).

Этот скрипт берёт одно вычисление и создаёт из него два артефакта:
- PNG: пространственно-временная диаграмма автомата
- WAV: каждая строка автомата → аккорд. Живые клетки → частоты.

Два медиума из одного вычисления. Паттерн, который можно и видеть, и слышать.

Запуск: python3 automaton_music.py
"""

import struct
import zlib
import math
import os

# --- Клеточный автомат ---

def rule110(cells):
    """Одно поколение Rule 110."""
    n = len(cells)
    new = [0] * n
    for i in range(n):
        left = cells[(i - 1) % n]
        center = cells[i]
        right = cells[(i + 1) % n]
        pattern = (left << 2) | (center << 1) | right
        # Rule 110 = 01101110 в двоичном
        new[i] = (110 >> pattern) & 1
    return new

WIDTH = 400
STEPS = 300

# Начальное состояние: одна клетка справа (классический старт)
cells = [0] * WIDTH
cells[-1] = 1

grid = [cells[:]]
for _ in range(STEPS - 1):
    cells = rule110(cells)
    grid.append(cells[:])

print(f"Автомат: Rule 110, {WIDTH}x{STEPS}")

# --- PNG ---

def make_png(filename, grid, cell_size=2):
    h = len(grid)
    w = len(grid[0])
    img_w = w * cell_size
    img_h = h * cell_size

    # Палитра: чёрный фон, цвет клетки зависит от локальной плотности
    raw_rows = []
    for y, row in enumerate(grid):
        pixel_row = bytearray()
        for x, val in enumerate(row):
            if val:
                # Цвет: от синего (разреженные) к жёлтому (плотные)
                neighbors = 0
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w:
                            neighbors += grid[ny][nx]
                t = min(neighbors / 13.0, 1.0)
                r = int(40 + 215 * t)
                g = int(60 + 180 * t)
                b = int(200 - 150 * t)
            else:
                r, g, b = 10, 10, 15
            pixel_row.extend([r, g, b] * cell_size)

        for _ in range(cell_size):
            raw_rows.append(bytes([0]) + bytes(pixel_row))

    raw_data = b''.join(raw_rows)
    compressed = zlib.compress(raw_data, 9)

    def chunk(ctype, data):
        c = ctype + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    with open(filename, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(chunk(b'IHDR', struct.pack('>IIBBBBB', img_w, img_h, 8, 2, 0, 0, 0)))
        f.write(chunk(b'IDAT', compressed))
        f.write(chunk(b'IEND', b''))

    size_kb = os.path.getsize(filename) / 1024
    print(f"PNG: {filename} ({img_w}x{img_h}, {size_kb:.0f} КБ)")

make_png('rule110.png', grid)

# --- WAV ---

SAMPLE_RATE = 44100
DURATION = 20  # секунд

# Маппинг: каждая строка автомата → момент времени
# Живые клетки → частоты в пентатонике (расширенной)

BASE_FREQ = 110  # A2
# Пентатоника: 0, 2, 4, 7, 9 полутонов, повторяем по октавам
PENTATONIC = [0, 2, 4, 7, 9]

def cell_to_freq(x, width):
    """Позиция клетки → частота."""
    octave = (x * 5) // width  # 0..4
    degree = (x * 5) % width * len(PENTATONIC) // width
    degree = degree % len(PENTATONIC)
    semitones = octave * 12 + PENTATONIC[degree]
    return BASE_FREQ * (2 ** (semitones / 12.0))

def generate_wav(filename, grid, duration, sample_rate):
    n_samples = int(duration * sample_rate)
    samples = [0.0] * n_samples

    rows = len(grid)
    width = len(grid[0])

    samples_per_row = n_samples / rows

    for row_idx, row in enumerate(grid):
        # Время начала и конца этой строки
        t_start = int(row_idx * samples_per_row)
        t_end = int((row_idx + 1) * samples_per_row)
        row_len = t_end - t_start

        # Собираем живые клетки
        alive = [x for x in range(width) if row[x]]
        if not alive:
            continue

        # Ограничиваем количество одновременных частот
        step = max(1, len(alive) // 12)
        selected = alive[::step][:12]

        amp = 0.3 / max(len(selected), 1)

        for x in selected:
            freq = cell_to_freq(x, width)
            for i in range(row_len):
                t = i / sample_rate
                # Огибающая: быстрый attack, экспоненциальный decay
                env = math.exp(-3.0 * t / (samples_per_row / sample_rate))
                samples[t_start + i] += amp * env * math.sin(2 * math.pi * freq * t)

    # Нормализация
    peak = max(abs(s) for s in samples) or 1
    samples = [s / peak * 0.8 for s in samples]

    # Запись WAV
    with open(filename, 'wb') as f:
        n = len(samples)
        data_size = n * 2
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + data_size))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<IHHIIHH', 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        for s in samples:
            val = max(-32767, min(32767, int(s * 32767)))
            f.write(struct.pack('<h', val))

    size_kb = os.path.getsize(filename) / 1024
    print(f"WAV: {filename} ({duration}с, {size_kb:.0f} КБ)")

generate_wav('rule110.wav', grid, DURATION, SAMPLE_RATE)

# --- Анализ ---

total_alive = sum(sum(row) for row in grid)
total_cells = WIDTH * STEPS
density = total_alive / total_cells

# Энтропия по строкам
entropies = []
for row in grid:
    p = sum(row) / len(row)
    if 0 < p < 1:
        h = -(p * math.log2(p) + (1-p) * math.log2(1-p))
    else:
        h = 0
    entropies.append(h)

avg_entropy = sum(entropies) / len(entropies)

# Найти паттерны: глайдеры (движущиеся структуры)
# Rule 110 известна глайдерами с периодом 7 и скоростью c/3
# Считаем вертикальные полосы активности
column_activity = [0] * WIDTH
for row in grid:
    for x in range(WIDTH):
        column_activity[x] += row[x]

active_columns = sum(1 for a in column_activity if a > STEPS * 0.1)

print(f"\nАнализ:")
print(f"  Плотность: {density:.3f}")
print(f"  Средняя энтропия строки: {avg_entropy:.3f} бит")
print(f"  Активных столбцов (>10%): {active_columns}/{WIDTH}")
print(f"  Всего живых клеток: {total_alive}/{total_cells}")

# Rule 110 — на границе между порядком и хаосом
# Плотность ~0.5 была бы чистый хаос, ~0 — пустота
# Rule 110 даёт промежуточное значение с глайдерами и взаимодействиями
print(f"\nRule 110 — один из 256 элементарных клеточных автоматов.")
print(f"Единственный (помимо тривиальных), для которого доказана полнота по Тьюрингу.")
print(f"Из одной клетки на белом фоне рождается структура, способная вычислить всё,")
print(f"что может вычислить любой компьютер. Паттерн, который вы видите на изображении")
print(f"и слышите в аудио — это одно и то же вычисление в двух медиумах.")
