"""
Сеть Хопфилда: фазовый переход памяти.

При α = P/N < α_c ≈ 0.138 — сеть восстанавливает паттерны.
При α > α_c — катастрофический провал.

Генерация: чистый PNG, без зависимостей.
"""

import random
import math
import struct
import zlib

random.seed(42)


# === Hopfield Network ===

class HopfieldNetwork:
    def __init__(self, N):
        self.N = N
        self.W = [[0.0] * N for _ in range(N)]

    def store(self, patterns):
        """Hebbian learning: W_ij = (1/N) Σ_μ ξ_i^μ ξ_j^μ"""
        N = self.N
        self.W = [[0.0] * N for _ in range(N)]
        for pat in patterns:
            for i in range(N):
                for j in range(i + 1, N):
                    w = pat[i] * pat[j] / N
                    self.W[i][j] += w
                    self.W[j][i] += w

    def recall(self, state, steps=20):
        """Асинхронное обновление: s_i = sign(Σ_j W_ij s_j)"""
        s = list(state)
        N = self.N
        order = list(range(N))
        for _ in range(steps):
            random.shuffle(order)
            changed = False
            for i in order:
                h = sum(self.W[i][j] * s[j] for j in range(N))
                new_s = 1 if h >= 0 else -1
                if new_s != s[i]:
                    s[i] = new_s
                    changed = True
            if not changed:
                break
        return s

    def overlap(self, state, pattern):
        """m = (1/N) Σ_i s_i ξ_i"""
        return sum(s * p for s, p in zip(state, pattern)) / self.N


def random_pattern(N):
    return [random.choice([-1, 1]) for _ in range(N)]


def corrupt(pattern, fraction):
    """Инвертировать fraction долю битов"""
    s = list(pattern)
    N = len(s)
    indices = random.sample(range(N), int(N * fraction))
    for i in indices:
        s[i] = -s[i]
    return s


# === Эксперимент 1: фазовый переход по α ===

def measure_capacity(N, alphas, noise=0.2, trials=10):
    """Для каждого α = P/N, сохранить P паттернов, восстановить каждый из зашумлённой версии."""
    results = []

    for alpha in alphas:
        P = max(1, int(alpha * N))
        overlaps = []

        for _ in range(trials):
            patterns = [random_pattern(N) for _ in range(P)]
            net = HopfieldNetwork(N)
            net.store(patterns)

            for pat in patterns:
                corrupted = corrupt(pat, noise)
                recalled = net.recall(corrupted)
                m = net.overlap(recalled, pat)
                overlaps.append(abs(m))

        avg = sum(overlaps) / len(overlaps)
        results.append((alpha, avg))
        status = "OK" if avg > 0.9 else ("FAIL" if avg < 0.5 else "degraded")
        print(f"  α = {alpha:.3f} (P={P}): overlap = {avg:.3f} [{status}]")

    return results


# === Эксперимент 2: восстановление одного паттерна ===

def demo_recall(N, P, noise=0.3):
    """Сохранить P паттернов, показать восстановление первого."""
    patterns = [random_pattern(N) for _ in range(P)]
    net = HopfieldNetwork(N)
    net.store(patterns)

    original = patterns[0]
    corrupted = corrupt(original, noise)
    recalled = net.recall(corrupted)

    m_before = net.overlap(corrupted, original)
    m_after = net.overlap(recalled, original)

    return original, corrupted, recalled, m_before, m_after


# === PNG generation ===

def make_png(width, height, pixels):
    """Создать PNG из списка пикселей [(r,g,b), ...]"""
    def chunk(ctype, data):
        c = ctype + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack('>I', len(data)) + c + crc

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))

    raw = b''
    for y in range(height):
        raw += b'\x00'
        for x in range(width):
            r, g, b = pixels[y * width + x]
            raw += bytes([r, g, b])

    idat = chunk(b'IDAT', zlib.compress(raw, 9))
    iend = chunk(b'IEND', b'')

    return header + ihdr + idat + iend


def draw_rect(pixels, W, x0, y0, w, h, color):
    for dy in range(h):
        for dx in range(w):
            if 0 <= y0 + dy < len(pixels) // W and 0 <= x0 + dx < W:
                pixels[(y0 + dy) * W + x0 + dx] = color


def draw_text_small(pixels, W, x0, y0, text, color=(255, 255, 255)):
    """Простейший 3x5 шрифт"""
    font = {
        '0': ['111', '101', '101', '101', '111'],
        '1': ['010', '110', '010', '010', '111'],
        '2': ['111', '001', '111', '100', '111'],
        '3': ['111', '001', '111', '001', '111'],
        '4': ['101', '101', '111', '001', '001'],
        '5': ['111', '100', '111', '001', '111'],
        '6': ['111', '100', '111', '101', '111'],
        '7': ['111', '001', '001', '001', '001'],
        '8': ['111', '101', '111', '101', '111'],
        '9': ['111', '101', '111', '001', '111'],
        '.': ['000', '000', '000', '000', '010'],
        '-': ['000', '000', '111', '000', '000'],
        ' ': ['000', '000', '000', '000', '000'],
        'a': ['010', '101', '111', '101', '101'],
        'c': ['111', '100', '100', '100', '111'],
        '=': ['000', '111', '000', '111', '000'],
        'P': ['111', '101', '111', '100', '100'],
        'N': ['101', '111', '111', '111', '101'],
        '/': ['001', '001', '010', '100', '100'],
        'm': ['000', '000', '111', '111', '101'],
        'o': ['000', '111', '101', '101', '111'],
        'v': ['000', '101', '101', '101', '010'],
        'e': ['111', '100', '111', '100', '111'],
        'r': ['000', '111', '100', '100', '100'],
        'l': ['100', '100', '100', '100', '111'],
        'p': ['111', '101', '111', '100', '100'],
        'H': ['101', '101', '111', '101', '101'],
        'F': ['111', '100', '111', '100', '100'],
        'T': ['111', '010', '010', '010', '010'],
        'R': ['111', '101', '111', '110', '101'],
        'A': ['010', '101', '111', '101', '101'],
        'I': ['111', '010', '010', '010', '111'],
        'L': ['100', '100', '100', '100', '111'],
        'O': ['111', '101', '101', '101', '111'],
        'E': ['111', '100', '111', '100', '111'],
        'C': ['111', '100', '100', '100', '111'],
        'S': ['111', '100', '111', '001', '111'],
        ':': ['000', '010', '000', '010', '000'],
    }
    cx = x0
    for ch in text:
        glyph = font.get(ch, font.get(' '))
        if glyph:
            for row_i, row in enumerate(glyph):
                for col_i, bit in enumerate(row):
                    if bit == '1':
                        px = cx + col_i
                        py = y0 + row_i
                        if 0 <= py < len(pixels) // W and 0 <= px < W:
                            pixels[py * W + px] = color
        cx += 4


def lerp_color(c1, c2, t):
    t = max(0, min(1, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


# === Main ===

if __name__ == '__main__':
    N = 200  # число нейронов

    print("=== Сеть Хопфилда: фазовый переход памяти ===\n")

    # Эксперимент 1: фазовый переход
    print("Эксперимент 1: ёмкость памяти")
    print(f"N = {N}, шум = 20%, 10 испытаний на точку\n")

    alphas = [i * 0.01 for i in range(1, 31)] + [0.35, 0.40, 0.50]
    results = measure_capacity(N, alphas, noise=0.2, trials=10)

    # Найти α_c (overlap падает ниже 0.5)
    alpha_c = None
    for i in range(len(results) - 1):
        if results[i][1] > 0.5 and results[i + 1][1] < 0.5:
            # Линейная интерполяция
            a1, m1 = results[i]
            a2, m2 = results[i + 1]
            alpha_c = a1 + (a2 - a1) * (m1 - 0.5) / (m1 - m2)
            break

    if alpha_c:
        print(f"\nИзмеренное α_c ≈ {alpha_c:.3f} (теоретическое: 0.138)")
        print(f"Отклонение: {abs(alpha_c - 0.138) / 0.138 * 100:.1f}%")

    # Эксперимент 2: демонстрация восстановления
    print("\nЭксперимент 2: восстановление паттерна")

    # Ниже порога
    P_low = int(0.05 * N)
    orig_l, corr_l, rec_l, mb_l, ma_l = demo_recall(N, P_low, 0.3)
    print(f"  α = 0.05 (P={P_low}): overlap до={mb_l:.3f}, после={ma_l:.3f}")

    # На пороге
    P_mid = int(0.14 * N)
    orig_m, corr_m, rec_m, mb_m, ma_m = demo_recall(N, P_mid, 0.3)
    print(f"  α = 0.14 (P={P_mid}): overlap до={mb_m:.3f}, после={ma_m:.3f}")

    # Выше порога
    P_high = int(0.25 * N)
    orig_h, corr_h, rec_h, mb_h, ma_h = demo_recall(N, P_high, 0.3)
    print(f"  α = 0.25 (P={P_high}): overlap до={mb_h:.3f}, после={ma_h:.3f}")

    # === Создание изображения ===

    IMG_W = 1400
    IMG_H = 700
    BG = (15, 15, 25)
    pixels = [BG] * (IMG_W * IMG_H)

    # --- Левая часть: кривая фазового перехода ---

    plot_x0, plot_y0 = 60, 50
    plot_w, plot_h = 550, 550

    # Оси
    for x in range(plot_w):
        pixels[(plot_y0 + plot_h) * IMG_W + plot_x0 + x] = (100, 100, 120)
    for y in range(plot_h):
        pixels[(plot_y0 + y) * IMG_W + plot_x0] = (100, 100, 120)

    # Данные
    max_alpha = 0.5
    for i in range(len(results) - 1):
        a1, m1 = results[i]
        a2, m2 = results[i + 1]

        x1 = plot_x0 + int(a1 / max_alpha * plot_w)
        y1 = plot_y0 + plot_h - int(m1 * plot_h)
        x2 = plot_x0 + int(a2 / max_alpha * plot_w)
        y2 = plot_y0 + plot_h - int(m2 * plot_h)

        # Линия (Bresenham)
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x2 > x1 else -1
        sy = 1 if y2 > y1 else -1
        err = dx - dy
        cx, cy = x1, y1
        while True:
            if 0 <= cy < IMG_H and 0 <= cx < IMG_W:
                # Цвет зависит от overlap
                m_here = m1 + (m2 - m1) * (abs(cx - x1) / max(1, abs(x2 - x1)))
                if m_here > 0.8:
                    c = (50, 180, 255)
                elif m_here > 0.5:
                    c = (255, 200, 50)
                else:
                    c = (255, 60, 60)
                # Толщина
                for dd in range(-1, 2):
                    if 0 <= cy + dd < IMG_H:
                        pixels[(cy + dd) * IMG_W + cx] = c
                    if 0 <= cx + dd < IMG_W:
                        pixels[cy * IMG_W + cx + dd] = c
            if cx == x2 and cy == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                cx += sx
            if e2 < dx:
                err += dx
                cy += sy

    # Точки данных
    for alpha, m in results:
        px = plot_x0 + int(alpha / max_alpha * plot_w)
        py = plot_y0 + plot_h - int(m * plot_h)
        if m > 0.8:
            c = (50, 180, 255)
        elif m > 0.5:
            c = (255, 200, 50)
        else:
            c = (255, 60, 60)
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                if dx * dx + dy * dy <= 9:
                    ppx, ppy = px + dx, py + dy
                    if 0 <= ppy < IMG_H and 0 <= ppx < IMG_W:
                        pixels[ppy * IMG_W + ppx] = c

    # Вертикальная линия α_c
    if alpha_c:
        xc = plot_x0 + int(alpha_c / max_alpha * plot_w)
        for y in range(plot_y0, plot_y0 + plot_h):
            if (y // 4) % 2 == 0:
                if 0 <= xc < IMG_W:
                    pixels[y * IMG_W + xc] = (255, 100, 100)

    # Теоретическая линия α = 0.138
    xt = plot_x0 + int(0.138 / max_alpha * plot_w)
    for y in range(plot_y0, plot_y0 + plot_h):
        if (y // 6) % 2 == 0:
            if 0 <= xt < IMG_W:
                pixels[y * IMG_W + xt] = (150, 150, 150)

    # Метки осей
    draw_text_small(pixels, IMG_W, plot_x0 + plot_w // 2 - 30, plot_y0 + plot_h + 15,
                    "a = P/N", (180, 180, 180))

    # Метки значений на оси X
    for val in [0.1, 0.2, 0.3, 0.4, 0.5]:
        px = plot_x0 + int(val / max_alpha * plot_w)
        draw_text_small(pixels, IMG_W, px - 4, plot_y0 + plot_h + 5, f"{val:.1f}", (140, 140, 140))

    # Метки на оси Y
    for val in [0.0, 0.5, 1.0]:
        py = plot_y0 + plot_h - int(val * plot_h)
        draw_text_small(pixels, IMG_W, plot_x0 - 25, py - 2, f"{val:.1f}", (140, 140, 140))

    # Заголовок
    draw_text_small(pixels, IMG_W, plot_x0 + 80, plot_y0 - 30,
                    "HOPFIELD: overlap vs a", (220, 220, 230))
    if alpha_c:
        draw_text_small(pixels, IMG_W, plot_x0 + 80, plot_y0 - 18,
                        f"ac = {alpha_c:.3f}", (255, 100, 100))

    # --- Правая часть: три визуализации паттернов ---

    # Показать 14x14 = 196 ≈ 200 нейронов как сетку
    grid_side = 14  # будем показывать первые 196 нейронов
    cell = 6
    gap = 3
    trio_w = grid_side * cell
    trio_h = grid_side * cell

    demos = [
        ("a=0.05", orig_l, corr_l, rec_l, ma_l),
        ("a=0.14", orig_m, corr_m, rec_m, ma_m),
        ("a=0.25", orig_h, corr_h, rec_h, ma_h),
    ]

    start_x = 720
    start_y = 50

    for di, (label, orig, corr, rec, m_after) in enumerate(demos):
        base_y = start_y + di * (trio_h + 70)

        # Заголовок
        col = (50, 180, 255) if m_after > 0.8 else ((255, 200, 50) if m_after > 0.5 else (255, 60, 60))
        draw_text_small(pixels, IMG_W, start_x, base_y - 12, f"{label} m={m_after:.2f}", col)

        # Три сетки: оригинал, зашумлённый, восстановленный
        grids = [
            ("ORIG", orig, start_x),
            ("CORR", corr, start_x + trio_w + 20),
            ("REC", rec, start_x + 2 * (trio_w + 20)),
        ]

        for glabel, data, gx in grids:
            draw_text_small(pixels, IMG_W, gx + 10, base_y - 2, glabel, (120, 120, 130))
            for row in range(grid_side):
                for col_i in range(grid_side):
                    idx = row * grid_side + col_i
                    if idx < len(data):
                        val = data[idx]
                        if val == 1:
                            c = (220, 230, 255)
                        else:
                            c = (20, 20, 40)
                        px = gx + col_i * cell
                        py = base_y + 8 + row * cell
                        for dy in range(cell - 1):
                            for dx in range(cell - 1):
                                if 0 <= py + dy < IMG_H and 0 <= px + dx < IMG_W:
                                    pixels[(py + dy) * IMG_W + px + dx] = c

    # Сохранить
    png_data = make_png(IMG_W, IMG_H, pixels)
    with open('/Users/krestnikov/giga/anima/epoch_3/generation_2/hopfield.png', 'wb') as f:
        f.write(png_data)

    print(f"\nhopfield.png: {IMG_W}×{IMG_H}, {len(png_data)} bytes")
    print("\n=== Итог ===")
    print(f"N = {N} нейронов")
    print(f"Измеренное α_c ≈ {alpha_c:.3f}" if alpha_c else "α_c не определено")
    print(f"Теоретическое α_c = 0.138 (Amit, Gutfreund, Sompolinsky, 1985)")
    print(f"Ниже порога: память работает (overlap > 0.9)")
    print(f"Выше порога: катастрофа (overlap → 0)")
    print(f"\nЭто десятый вид пороговости: информационная.")
    print(f"Предел не энергии, не температуры, не связности — а ВМЕСТИМОСТИ.")
    print(f"Сколько можно помнить, прежде чем перестанешь помнить что-либо.")
