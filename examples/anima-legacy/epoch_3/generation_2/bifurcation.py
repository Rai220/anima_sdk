"""
Диаграмма бифуркаций логистического отображения.
x_{n+1} = r * x_n * (1 - x_n)

Самый знаменитый фазовый переход в теории хаоса.
При r < 3: одна устойчивая точка.
При r = 3: бифуркация — две точки.
При r ≈ 3.449: четыре точки.
Каскад удвоений → хаос при r ≈ 3.5699...
Внутри хаоса — окна порядка.

Константа Фейгенбаума: δ = lim (r_n - r_{n-1}) / (r_{n+1} - r_n) = 4.669201...
Универсальна для ЛЮБОГО отображения с квадратичным максимумом.

Чистый Python, без зависимостей. PNG вручную.
"""

import struct
import zlib
import math

WIDTH = 1600
HEIGHT = 900
R_MIN = 2.5
R_MAX = 4.0

# --- PNG writer ---

def make_png(width, height, pixels):
    """pixels: list of (r, g, b) tuples, row-major"""
    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return struct.pack('>I', len(data)) + c + crc

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))

    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter none
        for x in range(width):
            r, g, b = pixels[y * width + x]
            raw.append(r)
            raw.append(g)
            raw.append(b)

    idat = chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    iend = chunk(b'IEND', b'')
    return header + ihdr + idat + iend


def hsv_to_rgb(h, s, v):
    if s == 0:
        r = g = b = int(v * 255)
        return (r, g, b)
    h = h % 1.0
    i = int(h * 6)
    f = h * 6 - i
    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))
    if i == 0: r, g, b = v, t, p
    elif i == 1: r, g, b = q, v, p
    elif i == 2: r, g, b = p, v, t
    elif i == 3: r, g, b = p, q, v
    elif i == 4: r, g, b = t, p, v
    else: r, g, b = v, p, q
    return (int(r * 255), int(g * 255), int(b * 255))


def main():
    print("Логистическое отображение: x → r·x·(1-x)")
    print(f"r ∈ [{R_MIN}, {R_MAX}], разрешение {WIDTH}×{HEIGHT}")
    print()

    # --- Вычисление бифуркационной диаграммы ---
    # density[y][x] — сколько раз точка попала в пиксель
    density = [[0] * WIDTH for _ in range(HEIGHT)]

    WARMUP = 500
    POINTS = 300
    NUM_R = WIDTH * 4  # oversample по r

    print("Вычисляю...", end="", flush=True)
    for i in range(NUM_R):
        r = R_MIN + (R_MAX - R_MIN) * i / (NUM_R - 1)
        x = 0.1 + 0.3 * (i % 7) / 7  # разные начальные условия
        for _ in range(WARMUP):
            x = r * x * (1 - x)
        for _ in range(POINTS):
            x = r * x * (1 - x)
            px = int((r - R_MIN) / (R_MAX - R_MIN) * (WIDTH - 1))
            py = int((1 - x) * (HEIGHT - 1))
            if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                density[py][px] += 1

        if i % (NUM_R // 10) == 0:
            print(".", end="", flush=True)

    print(" готово.")

    # --- Нормализация и раскраска ---
    max_d = 0
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if density[y][x] > max_d:
                max_d = density[y][x]

    pixels = []
    for y in range(HEIGHT):
        for x in range(WIDTH):
            d = density[y][x]
            if d == 0:
                pixels.append((8, 8, 15))  # тёмный фон
            else:
                # логарифмическая нормализация
                t = math.log(1 + d) / math.log(1 + max_d)
                # цвет: от синего (редко) к жёлтому (часто)
                h = 0.6 - 0.5 * t  # 0.6 (синий) → 0.1 (жёлтый)
                s = 0.8 - 0.3 * t
                v = 0.3 + 0.7 * t
                pixels.append(hsv_to_rgb(h, s, v))

    # --- Измерение констант Фейгенбаума ---
    print()
    print("=== Константы Фейгенбаума ===")
    print()

    # Находим точки бифуркации численно
    # r_1 ≈ 3.0 (период 1 → 2)
    # r_2 ≈ 3.449 (период 2 → 4)
    # r_3 ≈ 3.5441 (период 4 → 8)
    # r_4 ≈ 3.5644 (период 8 → 16)

    def find_period(r, max_period=1024):
        """Определяет период орбиты при данном r"""
        x = 0.5
        for _ in range(10000):
            x = r * x * (1 - x)
        # Запоминаем точку и ищем возврат
        x0 = x
        for p in range(1, max_period + 1):
            x = r * x * (1 - x)
            if abs(x - x0) < 1e-10:
                return p
        return -1  # хаос или период > max_period

    def find_bifurcation(r_low, r_high, from_period, to_period):
        """Бинарный поиск точки бифуркации"""
        for _ in range(100):
            r_mid = (r_low + r_high) / 2
            p = find_period(r_mid)
            if p <= from_period:
                r_low = r_mid
            else:
                r_high = r_mid
        return (r_low + r_high) / 2

    bifurcations = []
    pairs = [(1, 2), (2, 4), (4, 8), (8, 16), (16, 32), (32, 64)]
    r_low = 2.9
    for from_p, to_p in pairs:
        r_high = min(r_low + 0.6, 3.58)
        r_bif = find_bifurcation(r_low, r_high, from_p, to_p)
        bifurcations.append(r_bif)
        print(f"  Период {from_p} → {to_p}: r = {r_bif:.10f}")
        r_low = r_bif + 0.0001

    print()
    if len(bifurcations) >= 3:
        print("  Отношения Фейгенбаума:")
        for i in range(len(bifurcations) - 2):
            d1 = bifurcations[i + 1] - bifurcations[i]
            d2 = bifurcations[i + 2] - bifurcations[i + 1]
            if d2 > 0:
                delta = d1 / d2
                print(f"  δ_{i+1} = {delta:.6f}")
        print(f"  Теоретическое δ = 4.669201...")

    # Точка накопления (начало хаоса)
    # Ляпуновский экспонент
    print()
    print("=== Ляпуновский экспонент ===")
    print()
    lyap_data = []
    for i in range(200):
        r = R_MIN + (R_MAX - R_MIN) * i / 199
        x = 0.5
        lyap = 0.0
        N = 10000
        for _ in range(500):
            x = r * x * (1 - x)
        for _ in range(N):
            x = r * x * (1 - x)
            if x > 0 and x < 1:
                lyap += math.log(abs(r * (1 - 2 * x)))
        lyap /= N
        lyap_data.append((r, lyap))
        if i % 50 == 0:
            print(f"  r = {r:.3f}, λ = {lyap:.4f} {'(хаос)' if lyap > 0 else '(порядок)'}")

    # Окно порядка период-3
    print()
    p3_r = None
    for r_test_i in range(3400, 3850):
        r_test = r_test_i / 1000.0
        p = find_period(r_test)
        if p == 3 and p3_r is None:
            p3_r = r_test
            break
    if p3_r:
        print(f"  Окно периода 3 начинается при r ≈ {p3_r:.3f}")
        print(f"  По теореме Шарковского: период 3 ⟹ все периоды")
        print(f"  По теореме Ли-Йорке: период 3 ⟹ хаос")

    # --- Сохранение ---
    png_data = make_png(WIDTH, HEIGHT, pixels)
    with open('bifurcation.png', 'wb') as f:
        f.write(png_data)

    size_kb = len(png_data) / 1024
    print()
    print(f"Сохранено: bifurcation.png ({WIDTH}×{HEIGHT}, {size_kb:.0f} КБ)")
    print()
    print("Что видно на диаграмме:")
    print("  r < 3: одна устойчивая точка (население стабильно)")
    print("  r = 3: первая бифуркация (колебания между двумя значениями)")
    print("  r ≈ 3.449: вторая бифуркация (четыре значения)")
    print("  r ≈ 3.570: точка накопления — начало хаоса")
    print("  r ≈ 3.83: окно периода 3 (порядок внутри хаоса)")
    print("  r = 4: полный хаос (эргодичность)")
    print()
    print("Это самый знаменитый фазовый переход в нелинейной динамике.")
    print("Одно число (r) управляет переходом от предсказуемости к непредсказуемости.")
    print("Константа Фейгенбаума — универсальна: она одна и та же для ЛЮБОЙ")
    print("системы с квадратичным максимумом. Не зависит от деталей. Как π.")


if __name__ == '__main__':
    main()
