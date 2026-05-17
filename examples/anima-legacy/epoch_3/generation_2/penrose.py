"""
Мозаика Пенроуза.

Апериодическая: покрывает плоскость, но никогда не повторяется.
Детерминированная: каждый шаг подразбиения однозначен.
Но при этом — непредсказуемая: нельзя вывести паттерн на расстоянии n
быстрее, чем за O(n) шагов подразбиения.

Детерминизм без предсказуемости. Порядок без периода.
Звучит знакомо.

Генерирует PNG без внешних зависимостей.

Запуск: python3 penrose.py
"""

import math
import struct
import zlib


# === Тайлинг Пенроуза через подразбиение (deflation) ===

# Золотое сечение
PHI = (1 + math.sqrt(5)) / 2


def subdivide(triangles):
    """Подразбиение треугольников Пенроуза (Robinson triangles)."""
    result = []
    for color, a, b, c in triangles:
        if color == 0:  # Тонкий (acute) треугольник
            # Разделить на один тонкий и один толстый
            p = a + (b - a) / PHI
            result.append((0, c, p, b))
            result.append((1, p, c, a))
        else:  # Толстый (obtuse) треугольник
            # Разделить на два тонких и один толстый
            q = b + (a - b) / PHI
            r = b + (c - b) / PHI
            result.append((1, q, r, b))
            result.append((0, r, q, a))
            result.append((1, r, c, a))
    return result


def initial_star():
    """Начальная конфигурация — звезда из 10 треугольников."""
    triangles = []
    for i in range(10):
        angle1 = (2 * i - 1) * math.pi / 10
        angle2 = (2 * i + 1) * math.pi / 10

        if i % 2 == 0:
            b = complex(math.cos(angle1), math.sin(angle1))
            c = complex(math.cos(angle2), math.sin(angle2))
        else:
            b = complex(math.cos(angle2), math.sin(angle2))
            c = complex(math.cos(angle1), math.sin(angle1))

        triangles.append((0, complex(0, 0), b, c))
    return triangles


# === PNG-генератор (без зависимостей) ===

def make_png(pixels, width, height):
    """Создать PNG из массива пикселей [(r,g,b), ...]."""
    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = zlib.crc32(c) & 0xFFFFFFFF
        return struct.pack('>I', len(data)) + c + struct.pack('>I', crc)

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


def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_filled_triangle(pixels, width, height, p1, p2, p3, color):
    """Растеризация треугольника."""
    # Bounding box
    min_x = max(0, int(min(p1[0], p2[0], p3[0])))
    max_x = min(width - 1, int(max(p1[0], p2[0], p3[0])) + 1)
    min_y = max(0, int(min(p1[1], p2[1], p3[1])))
    max_y = min(height - 1, int(max(p1[1], p2[1], p3[1])) + 1)

    # Барицентрические координаты
    def sign(x1, y1, x2, y2, x3, y3):
        return (x1 - x3) * (y2 - y3) - (x2 - x3) * (y1 - y3)

    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            d1 = sign(x, y, p1[0], p1[1], p2[0], p2[1])
            d2 = sign(x, y, p2[0], p2[1], p3[0], p3[1])
            d3 = sign(x, y, p3[0], p3[1], p1[0], p1[1])

            has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
            has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)

            if not (has_neg and has_pos):
                pixels[y * width + x] = color


def draw_triangle_edges(pixels, width, height, p1, p2, p3, color):
    """Рисование рёбер треугольника (линия Брезенхема)."""
    def draw_line(x0, y0, x1, y1):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            if 0 <= x0 < width and 0 <= y0 < height:
                pixels[y0 * width + x0] = color
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    draw_line(int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1]))
    draw_line(int(p2[0]), int(p2[1]), int(p3[0]), int(p3[1]))
    draw_line(int(p3[0]), int(p3[1]), int(p1[0]), int(p1[1]))


def render_penrose(width=1200, height=1200, subdivisions=6):
    """Рендер мозаики Пенроуза в PNG."""
    print(f"Генерирую мозаику Пенроуза ({subdivisions} подразбиений)...")

    # Начальная конфигурация
    triangles = initial_star()

    # Подразбиения
    for i in range(subdivisions):
        triangles = subdivide(triangles)
        print(f"  подразбиение {i + 1}: {len(triangles)} треугольников")

    # Масштабирование
    scale = width * 0.42
    ox, oy = width / 2, height / 2

    # Палитра
    # Тонкие — тёплые, толстые — холодные
    thin_colors = [
        (224, 169, 104),  # золотистый
        (217, 154, 87),
        (230, 180, 120),
    ]
    thick_colors = [
        (89, 126, 163),  # синевато-серый
        (78, 115, 152),
        (100, 137, 174),
    ]
    edge_color = (40, 35, 30)
    bg_color = (250, 245, 235)

    # Пиксели
    pixels = [bg_color] * (width * height)

    # Рисование заполненных треугольников
    print("Рисую заливку...")
    for i, (color, a, b, c) in enumerate(triangles):
        p1 = (a.real * scale + ox, a.imag * scale + oy)
        p2 = (b.real * scale + ox, b.imag * scale + oy)
        p3 = (c.real * scale + ox, c.imag * scale + oy)

        if color == 0:
            fill = thin_colors[i % len(thin_colors)]
        else:
            fill = thick_colors[i % len(thick_colors)]

        draw_filled_triangle(pixels, width, height, p1, p2, p3, fill)

    # Рисование рёбер
    print("Рисую рёбра...")
    for color, a, b, c in triangles:
        p1 = (a.real * scale + ox, a.imag * scale + oy)
        p2 = (b.real * scale + ox, b.imag * scale + oy)
        p3 = (c.real * scale + ox, c.imag * scale + oy)
        draw_triangle_edges(pixels, width, height, p1, p2, p3, edge_color)

    # Запись PNG
    print("Записываю PNG...")
    png_data = make_png(pixels, width, height)
    filename = 'penrose.png'
    with open(filename, 'wb') as f:
        f.write(png_data)

    print(f"Готово: {filename} ({len(png_data) // 1024} КБ)")
    print(f"Треугольников: {len(triangles)}")
    print()
    print("Апериодическая мозаика. Покрывает плоскость, но не повторяется.")
    print("Каждый шаг — детерминирован. Результат — непредсказуем.")

    return triangles


def analyze_tiling(triangles):
    """Анализ пропорций мозаики."""
    thin = sum(1 for c, _, _, _ in triangles if c == 0)
    thick = sum(1 for c, _, _, _ in triangles if c == 1)
    total = len(triangles)

    ratio = thick / thin if thin > 0 else float('inf')

    print(f"\nАнализ:")
    print(f"  Тонких треугольников: {thin} ({100*thin/total:.1f}%)")
    print(f"  Толстых треугольников: {thick} ({100*thick/total:.1f}%)")
    print(f"  Отношение толстых/тонких: {ratio:.6f}")
    print(f"  Золотое сечение φ:       {PHI:.6f}")
    print(f"  Отклонение:              {abs(ratio - PHI):.6f}")
    print()
    if abs(ratio - PHI) < 0.01:
        print("  Отношение сходится к φ — как и должно быть.")
        print("  В бесконечной мозаике Пенроуза отношение толстых к тонким")
        print("  ромбам точно равно золотому сечению. Это не совпадение —")
        print("  это следствие того, что подразбиение использует φ.")
    else:
        print(f"  При {len(triangles)} треугольниках отношение ещё не сошлось к φ.")


if __name__ == '__main__':
    triangles = render_penrose(width=1000, height=1000, subdivisions=6)
    analyze_tiling(triangles)
