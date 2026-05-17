#!/usr/bin/env python3
"""
Модель сегрегации Шеллинга.
Первый СОЦИАЛЬНЫЙ фазовый переход за всю эпоху 3.

Агенты двух типов на решётке. Каждый хочет, чтобы хотя бы доля τ соседей
была его типа. Если нет — переезжает на случайную пустую клетку.

Результат: при τ ≈ 0.33 — фазовый переход от интеграции к сегрегации.
Мягкие индивидуальные предпочтения → экстремальный коллективный результат.

Выход: schelling.png — три состояния решётки + кривая перехода.

Чистый Python, без зависимостей.
"""

import random
import struct
import zlib
import math

# ── PNG writer ──────────────────────────────────────────────────────

def make_png(width, height, pixels):
    """pixels: list of (r, g, b) row by row"""
    def chunk(ctype, data):
        c = ctype + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return struct.pack('>I', len(data)) + c + crc

    raw = b''
    for y in range(height):
        raw += b'\x00'  # filter none
        for x in range(width):
            r, g, b = pixels[y * width + x]
            raw += struct.pack('BBB', r, g, b)

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    return sig + chunk(b'IHDR', ihdr) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')


# ── Цвета ───────────────────────────────────────────────────────────

BG       = (245, 245, 240)   # пустая клетка
COLOR_A  = (70, 130, 180)    # тип A — синий
COLOR_B  = (205, 92, 92)     # тип B — красный
UNHAPPY  = (255, 200, 50)    # недовольные (для отладки, не используется в финале)
BORDER   = (80, 80, 80)
WHITE    = (255, 255, 255)
BLACK    = (0, 0, 0)
GRID_BG  = (30, 30, 35)
ACCENT   = (100, 200, 150)


# ── Модель Шеллинга ────────────────────────────────────────────────

class SchellingGrid:
    def __init__(self, size, density=0.9, ratio=0.5, tau=0.33, seed=42):
        self.size = size
        self.tau = tau
        self.rng = random.Random(seed)

        self.grid = [[0] * size for _ in range(size)]  # 0=пусто, 1=A, 2=B
        cells = [(r, c) for r in range(size) for c in range(size)]
        self.rng.shuffle(cells)

        n_filled = int(size * size * density)
        n_a = int(n_filled * ratio)
        for i in range(n_filled):
            r, c = cells[i]
            self.grid[r][c] = 1 if i < n_a else 2

    def neighbors(self, r, c):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    yield self.grid[nr][nc]

    def is_happy(self, r, c):
        t = self.grid[r][c]
        if t == 0:
            return True
        total = 0
        same = 0
        for n in self.neighbors(r, c):
            if n != 0:
                total += 1
                if n == t:
                    same += 1
        if total == 0:
            return True
        return (same / total) >= self.tau

    def step(self):
        """One round: find all unhappy, move each to random empty cell."""
        unhappy = []
        empty = []
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] == 0:
                    empty.append((r, c))
                elif not self.is_happy(r, c):
                    unhappy.append((r, c))

        self.rng.shuffle(unhappy)
        self.rng.shuffle(empty)

        moved = 0
        for (r, c) in unhappy:
            if not empty:
                break
            # Перемещаем
            t = self.grid[r][c]
            nr, nc = empty.pop()
            self.grid[nr][nc] = t
            self.grid[r][c] = 0
            empty.append((r, c))
            moved += 1

        return moved

    def run(self, max_steps=500):
        for i in range(max_steps):
            moved = self.step()
            if moved == 0:
                return i + 1
        return max_steps

    def segregation_index(self):
        """Средняя доля одноимённых соседей для занятых клеток."""
        total_ratio = 0
        count = 0
        for r in range(self.size):
            for c in range(self.size):
                t = self.grid[r][c]
                if t == 0:
                    continue
                total = 0
                same = 0
                for n in self.neighbors(r, c):
                    if n != 0:
                        total += 1
                        if n == t:
                            same += 1
                if total > 0:
                    total_ratio += same / total
                    count += 1
        return total_ratio / count if count > 0 else 0

    def snapshot(self):
        """Return copy of current grid."""
        return [row[:] for row in self.grid]


# ── Рисование ──────────────────────────────────────────────────────

def draw_grid(snapshot, size, cell_px, x0, y0, pixels, img_w):
    """Draw grid snapshot onto pixel buffer."""
    for r in range(size):
        for c in range(size):
            v = snapshot[r][c]
            color = BG if v == 0 else (COLOR_A if v == 1 else COLOR_B)
            for dy in range(cell_px):
                for dx in range(cell_px):
                    px = x0 + c * cell_px + dx
                    py = y0 + r * cell_px + dy
                    if 0 <= px < img_w and 0 <= py < len(pixels) // img_w:
                        pixels[py * img_w + px] = color


def draw_line(pixels, w, x0, y0, x1, y1, color, thickness=1):
    """Bresenham line."""
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        for t in range(-thickness//2, thickness//2 + 1):
            for s in range(-thickness//2, thickness//2 + 1):
                px, py = x0 + s, y0 + t
                h = len(pixels) // w
                if 0 <= px < w and 0 <= py < h:
                    pixels[py * w + px] = color

        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


def draw_rect(pixels, w, x0, y0, x1, y1, color):
    h = len(pixels) // w
    for y in range(max(0, y0), min(h, y1)):
        for x in range(max(0, x0), min(w, x1)):
            pixels[y * w + x] = color


def draw_char(pixels, w, x0, y0, ch, color, scale=1):
    """Tiny 5x7 font for digits and basic chars."""
    font = {
        '0': [0x7C, 0xC6, 0xCE, 0xD6, 0xE6, 0xC6, 0x7C],
        '1': [0x30, 0x70, 0x30, 0x30, 0x30, 0x30, 0xFC],
        '2': [0x78, 0xCC, 0x0C, 0x38, 0x60, 0xCC, 0xFC],
        '3': [0x78, 0xCC, 0x0C, 0x38, 0x0C, 0xCC, 0x78],
        '4': [0x1C, 0x3C, 0x6C, 0xCC, 0xFE, 0x0C, 0x0C],
        '5': [0xFC, 0xC0, 0xF8, 0x0C, 0x0C, 0xCC, 0x78],
        '6': [0x38, 0x60, 0xC0, 0xF8, 0xCC, 0xCC, 0x78],
        '7': [0xFC, 0xCC, 0x0C, 0x18, 0x30, 0x30, 0x30],
        '8': [0x78, 0xCC, 0xCC, 0x78, 0xCC, 0xCC, 0x78],
        '9': [0x78, 0xCC, 0xCC, 0x7C, 0x0C, 0x18, 0x70],
        '.': [0x00, 0x00, 0x00, 0x00, 0x00, 0x30, 0x30],
        ',': [0x00, 0x00, 0x00, 0x00, 0x00, 0x30, 0x60],
        '-': [0x00, 0x00, 0x00, 0x7C, 0x00, 0x00, 0x00],
        '=': [0x00, 0x00, 0xFC, 0x00, 0xFC, 0x00, 0x00],
        ' ': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        ':': [0x00, 0x30, 0x30, 0x00, 0x30, 0x30, 0x00],
        '/': [0x06, 0x0C, 0x18, 0x30, 0x60, 0xC0, 0x80],
        '%': [0xC6, 0xCC, 0x18, 0x30, 0x66, 0xC6, 0x00],
        'S': [0x78, 0xCC, 0xC0, 0x78, 0x0C, 0xCC, 0x78],
        'I': [0x78, 0x30, 0x30, 0x30, 0x30, 0x30, 0x78],
        'τ': [0x00, 0x00, 0xFE, 0x30, 0x30, 0x30, 0x30],
        'p': [0x00, 0x00, 0xF8, 0xCC, 0xF8, 0xC0, 0xC0],
        'c': [0x00, 0x00, 0x78, 0xCC, 0xC0, 0xCC, 0x78],
    }
    bitmap = font.get(ch, font[' '])
    for row_i, row_bits in enumerate(bitmap):
        for col_i in range(8):
            if row_bits & (0x80 >> col_i):
                for sy in range(scale):
                    for sx in range(scale):
                        px = x0 + col_i * scale + sx
                        py = y0 + row_i * scale + sy
                        h = len(pixels) // w
                        if 0 <= px < w and 0 <= py < h:
                            pixels[py * w + px] = color


def draw_text(pixels, w, x0, y0, text, color, scale=1):
    for i, ch in enumerate(text):
        draw_char(pixels, w, x0 + i * 8 * scale, y0, ch, color, scale)


def draw_dot(pixels, w, cx, cy, r, color):
    h = len(pixels) // w
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                px, py = cx + dx, cy + dy
                if 0 <= px < w and 0 <= py < h:
                    pixels[py * w + px] = color


# ── Эксперимент ────────────────────────────────────────────────────

def run_experiment():
    print("Модель сегрегации Шеллинга")
    print("=" * 50)
    print()
    print("Два типа агентов на решётке 50x50.")
    print("Каждый хочет, чтобы доля τ соседей была его типа.")
    print("Если нет — переезжает. Вопрос: при каком τ")
    print("возникает полная сегрегация?")
    print()

    grid_size = 50
    tau_values = [i / 100 for i in range(5, 76, 1)]
    results = []
    n_trials = 5

    for tau in tau_values:
        seg_sum = 0
        for trial in range(n_trials):
            model = SchellingGrid(grid_size, density=0.90, ratio=0.5, tau=tau,
                                  seed=42 + trial * 1000)
            model.run(max_steps=300)
            seg_sum += model.segregation_index()
        seg_avg = seg_sum / n_trials
        results.append((tau, seg_avg))

        if int(tau * 100) % 10 == 0:
            print(f"  τ = {tau:.2f}  →  сегрегация = {seg_avg:.3f}")

    print()

    # Найдём точку перехода (максимальный градиент)
    max_grad = 0
    transition_tau = 0
    for i in range(1, len(results)):
        grad = (results[i][1] - results[i-1][1]) / (results[i][0] - results[i-1][0])
        if grad > max_grad:
            max_grad = grad
            transition_tau = (results[i][0] + results[i-1][0]) / 2

    print(f"Точка перехода: τ_c ≈ {transition_tau:.2f}")
    print(f"Максимальный градиент: {max_grad:.2f}")
    print()

    # Базовый уровень: при τ=0 (все довольны), ожидаемая доля = 0.5
    base_seg = results[0][1]
    # Уровень полной сегрегации: при τ→1
    max_seg = max(r[1] for r in results)
    print(f"Базовая сегрегация (τ=0.05): {base_seg:.3f}")
    print(f"Максимальная сегрегация (τ=0.75): {max_seg:.3f}")
    print()
    print("Ключевое наблюдение: агент с τ=0.33 толерантен —")
    print("он согласен быть в меньшинстве (1/3 своих, 2/3 чужих).")
    print("Но коллективный результат — почти полная сегрегация.")
    print("Мягкие индивидуальные предпочтения → экстремальный")
    print("коллективный результат. Фазовый переход.")
    print()

    # Три снимка
    snapshots = []
    labels = []
    for tau_snap in [0.15, 0.33, 0.60]:
        model = SchellingGrid(grid_size, density=0.90, ratio=0.5, tau=tau_snap, seed=42)
        model.run(max_steps=300)
        snapshots.append(model.snapshot())
        seg = model.segregation_index()
        labels.append(f"τ={tau_snap:.2f}, SI={seg:.2f}")
        print(f"Снимок τ={tau_snap:.2f}: сегрегация = {seg:.3f}")

    print()
    print("Генерация изображения...")

    # ── Рисуем PNG ──────────────────────────────────────────────────

    img_w = 1600
    img_h = 950
    pixels = [GRID_BG] * (img_w * img_h)

    cell_px = 5
    grid_px = grid_size * cell_px  # 250

    # Три решётки сверху
    margin = 40
    gap = (img_w - 3 * grid_px - 2 * margin) // 2
    y_grid = 80

    for i, (snap, label) in enumerate(zip(snapshots, labels)):
        x0 = margin + i * (grid_px + gap)
        # Фон решётки
        draw_rect(pixels, img_w, x0 - 2, y_grid - 2,
                  x0 + grid_px + 2, y_grid + grid_px + 2, (50, 50, 55))
        draw_grid(snap, grid_size, cell_px, x0, y_grid, pixels, img_w)
        # Подпись
        draw_text(pixels, img_w, x0, y_grid + grid_px + 10, label, WHITE, scale=2)

    # Заголовок
    draw_text(pixels, img_w, margin, 20,
              "Schelling segregation model", WHITE, scale=3)

    # ── Кривая перехода ─────────────────────────────────────────────

    chart_x0 = margin + 60
    chart_y0 = y_grid + grid_px + 80
    chart_w = img_w - 2 * margin - 80
    chart_h = 350

    # Оси
    draw_line(pixels, img_w, chart_x0, chart_y0, chart_x0, chart_y0 + chart_h,
              WHITE, 2)
    draw_line(pixels, img_w, chart_x0, chart_y0 + chart_h,
              chart_x0 + chart_w, chart_y0 + chart_h, WHITE, 2)

    # Подписи осей
    draw_text(pixels, img_w, chart_x0 - 50, chart_y0 + chart_h // 2 - 10, "SI", WHITE, 2)
    draw_text(pixels, img_w, chart_x0 + chart_w // 2 - 20,
              chart_y0 + chart_h + 20, "tau", WHITE, 2)

    # Метки по X
    for tv in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]:
        x = chart_x0 + int(tv / 0.76 * chart_w)
        draw_line(pixels, img_w, x, chart_y0 + chart_h, x, chart_y0 + chart_h + 6, WHITE, 1)
        draw_text(pixels, img_w, x - 8, chart_y0 + chart_h + 8, f"{tv:.1f}", WHITE, 1)

    # Метки по Y
    for sv in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        y = chart_y0 + chart_h - int((sv - 0.45) / 0.55 * chart_h)
        if chart_y0 <= y <= chart_y0 + chart_h:
            draw_line(pixels, img_w, chart_x0 - 4, y, chart_x0, y, WHITE, 1)
            draw_text(pixels, img_w, chart_x0 - 40, y - 3, f"{sv:.1f}", WHITE, 1)

    # Данные
    prev_px = None
    prev_py = None
    for tau, seg in results:
        px = chart_x0 + int(tau / 0.76 * chart_w)
        py = chart_y0 + chart_h - int((seg - 0.45) / 0.55 * chart_h)
        py = max(chart_y0, min(chart_y0 + chart_h, py))

        draw_dot(pixels, img_w, px, py, 2, ACCENT)

        if prev_px is not None:
            draw_line(pixels, img_w, prev_px, prev_py, px, py, ACCENT, 1)
        prev_px, prev_py = px, py

    # Вертикаль на τ_c
    tc_px = chart_x0 + int(transition_tau / 0.76 * chart_w)
    for y in range(chart_y0, chart_y0 + chart_h, 4):
        draw_line(pixels, img_w, tc_px, y, tc_px, min(y + 2, chart_y0 + chart_h),
                  (255, 200, 50), 1)

    tc_label = f"τc={transition_tau:.2f}"
    draw_text(pixels, img_w, tc_px - 30, chart_y0 - 15, tc_label, (255, 200, 50), 2)

    # Записываем PNG
    png_data = make_png(img_w, img_h, pixels)
    with open('schelling.png', 'wb') as f:
        f.write(png_data)

    print(f"Сохранено: schelling.png ({len(png_data)} байт)")
    print()
    print("Шесть типов пороговости, обнаруженных генерацией:")
    print("  1. Количественная (перколяция, SAT, бифуркации)")
    print("  2. Топологическая (CeRu₄Sn₆ — жизнь НА пороге)")
    print("  3. Логическая (спин-3/2 → гравитация)")
    print("  4. Генеративная (гравитационные волны → тёмная материя)")
    print("  5. Эпистемическая (рентгеновские спутники — порог, скрытый моделью)")
    print("  6. Социальная (Шеллинг — порог, усиленный коллективом)")
    print()
    print("Шеллинг — единственный случай, когда порог УСИЛИВАЕТСЯ")
    print("при агрегации. В физических системах переход — свойство")
    print("целого. В социальных — целое радикальнее частей.")


if __name__ == '__main__':
    run_experiment()
