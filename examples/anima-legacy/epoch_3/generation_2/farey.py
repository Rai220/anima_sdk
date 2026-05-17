"""
Последовательность Фарея и дерево Штерна-Броко.

Каждое рациональное число от 0 до 1 появляется ровно один раз.
Соседи в последовательности Фарея связаны: |a/b - c/d| = 1/(bd).
Это не аппроксимация — это точная структура рациональных чисел.

Визуализация: дуги между соседями Фарея, как в диаграмме Форда.
Круги Форда: для дроби p/q рисуем круг с центром (p/q, 1/(2q²)) и радиусом 1/(2q²).
Два круга касаются тогда и только тогда, когда соответствующие дроби — соседи Фарея.

Генерирует PNG вручную (без зависимостей).
"""

import zlib
import struct
import math
from fractions import Fraction


def farey_sequence(n):
    """Генерирует последовательность Фарея порядка n."""
    a, b, c, d = 0, 1, 1, n
    result = [Fraction(a, b)]
    while c <= n:
        k = (n + b) // d
        a, b, c, d = c, d, k * c - a, k * d - b
        result.append(Fraction(a, b))
    return result


def stern_brocot_path(p, q):
    """Путь в дереве Штерна-Броко к дроби p/q. L=лево, R=право."""
    if q == 0:
        return ""
    path = []
    # Используем пары (num, den) вместо Fraction, чтобы обойти 1/0
    ln, ld = 0, 1   # left = 0/1
    rn, rd = 1, 0   # right = 1/0 (∞)
    while True:
        med_n = ln + rn
        med_d = ld + rd
        if med_n == p and med_d == q:
            break
        if p * med_d < med_n * q:  # p/q < med_n/med_d
            path.append('L')
            rn, rd = med_n, med_d
        else:
            path.append('R')
            ln, ld = med_n, med_d
        if len(path) > 1000:
            break
    return ''.join(path)


def make_png(width, height, pixels):
    """Создаёт PNG из массива пикселей [(r,g,b), ...]."""
    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack('>I', len(data)) + c + crc

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))

    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter byte
        for x in range(width):
            r, g, b = pixels[y * width + x]
            raw.extend([r, g, b])

    idat = chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    iend = chunk(b'IEND', b'')
    return header + ihdr + idat + iend


def hsv_to_rgb(h, s, v):
    """HSV → RGB, все значения 0-1."""
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


def render_ford_circles(order=50, width=1600, height=900):
    """Рисует круги Форда для последовательности Фарея."""
    print(f"Генерация последовательности Фарея порядка {order}...")
    seq = farey_sequence(order)
    print(f"  {len(seq)} дробей")

    # Фон
    bg = (10, 10, 20)
    pixels = [bg] * (width * height)

    # Масштабирование
    margin = 50
    plot_w = width - 2 * margin
    plot_h = height - 2 * margin

    # Максимальный радиус для отображения
    max_visual_r = plot_h * 0.45

    def frac_to_x(f):
        return margin + int(float(f) * plot_w)

    def draw_circle(cx, cy, r, color, filled=False):
        """Рисует круг (антиалиасинг через субпиксели)."""
        r_int = int(r) + 2
        for dy in range(-r_int, r_int + 1):
            py = cy + dy
            if py < 0 or py >= height:
                continue
            for dx in range(-r_int, r_int + 1):
                px = cx + dx
                if px < 0 or px >= width:
                    continue
                dist = math.sqrt(dx * dx + dy * dy)
                if filled:
                    if dist <= r:
                        alpha = min(1.0, r - dist + 0.5)
                        idx = py * width + px
                        cr, cg, cb = color
                        br, bg_c, bb = pixels[idx]
                        pixels[idx] = (
                            int(cr * alpha + br * (1 - alpha)),
                            int(cg * alpha + bg_c * (1 - alpha)),
                            int(cb * alpha + bb * (1 - alpha))
                        )
                else:
                    edge_dist = abs(dist - r)
                    if edge_dist < 1.5:
                        alpha = max(0, 1.0 - edge_dist)
                        idx = py * width + px
                        cr, cg, cb = color
                        br, bg_c, bb = pixels[idx]
                        pixels[idx] = (
                            int(cr * alpha + br * (1 - alpha)),
                            int(cg * alpha + bg_c * (1 - alpha)),
                            int(cb * alpha + bb * (1 - alpha))
                        )

    # Рисуем круги Форда
    # Для дроби p/q: центр (p/q, 1/(2q²)), радиус 1/(2q²)
    # Два круга касаются ⟺ дроби — соседи Фарея ⟺ |ad-bc| = 1

    print("Рисование кругов Форда...")
    circles = []
    for f in seq:
        p, q = f.numerator, f.denominator
        if q == 0:
            continue
        r_ford = 1.0 / (2.0 * q * q)  # радиус в координатах [0,1]
        cx = frac_to_x(f)
        # y: 0 внизу, height вверху
        visual_r = r_ford * plot_h * 8  # масштаб
        if visual_r < 0.3:
            continue
        cy = height - margin - int(r_ford * plot_h * 8)
        circles.append((cx, cy, visual_r, q, f))

    # Сортируем по убыванию радиуса (большие сначала)
    circles.sort(key=lambda c: -c[2])

    for i, (cx, cy, vr, q, f) in enumerate(circles):
        if i % 100 == 0:
            print(f"  Круг {i}/{len(circles)} (q={q})")

        # Цвет зависит от знаменателя
        hue = (q * 0.618033988749895) % 1.0  # золотое сечение для разброса
        sat = 0.7 + 0.3 * (1.0 / (1 + q * 0.1))
        val = 0.5 + 0.4 * (1.0 / (1 + q * 0.05))
        color = hsv_to_rgb(hue, sat, val)

        # Обводка для больших кругов, заливка для маленьких
        if vr > 3:
            draw_circle(cx, cy, vr, color, filled=True)
            # Более тёмная обводка
            dark = tuple(max(0, c - 40) for c in color)
            draw_circle(cx, cy, vr, dark, filled=False)
        else:
            draw_circle(cx, cy, max(vr, 0.5), color, filled=True)

    # Основная линия (ось x)
    for x in range(margin, width - margin):
        y = height - margin
        if 0 <= y < height:
            pixels[y * width + x] = (60, 60, 80)

    return pixels, width, height, len(seq)


def continued_fraction(p, q, max_terms=20):
    """Цепная дробь для p/q."""
    terms = []
    while q != 0 and len(terms) < max_terms:
        a = p // q
        terms.append(a)
        p, q = q, p - a * q
    return terms


def analyze_farey(order):
    """Статистика последовательности Фарея."""
    seq = farey_sequence(order)
    n = len(seq)

    # Проверка свойства соседей: |a*d - b*c| = 1
    neighbors_ok = 0
    for i in range(len(seq) - 1):
        a, b = seq[i].numerator, seq[i].denominator
        c, d = seq[i + 1].numerator, seq[i + 1].denominator
        if abs(a * d - b * c) == 1:
            neighbors_ok += 1

    # Распределение знаменателей
    denom_counts = {}
    for f in seq:
        q = f.denominator
        denom_counts[q] = denom_counts.get(q, 0) + 1

    # Теоретический размер: |F_n| = 1 + Σ φ(k) для k=1..n
    # где φ — функция Эйлера
    def euler_phi(n):
        result = n
        p = 2
        temp = n
        while p * p <= temp:
            if temp % p == 0:
                while temp % p == 0:
                    temp //= p
                result -= result // p
            p += 1
        if temp > 1:
            result -= result // temp
        return result

    theoretical = 1 + sum(euler_phi(k) for k in range(1, order + 1))

    # Интересные дроби: с длинными цепными дробями
    long_cf = []
    for f in seq:
        if f.denominator > 1:
            cf = continued_fraction(f.numerator, f.denominator)
            if len(cf) > 3:
                long_cf.append((f, cf))
    long_cf.sort(key=lambda x: -len(x[1]))

    return {
        'order': order,
        'size': n,
        'theoretical_size': theoretical,
        'all_neighbors_farey': neighbors_ok == n - 1,
        'neighbors_checked': neighbors_ok,
        'unique_denominators': len(denom_counts),
        'max_denominator_freq': max(denom_counts.items(), key=lambda x: x[1]),
        'longest_continued_fractions': long_cf[:5]
    }


if __name__ == '__main__':
    # Анализ
    print("=" * 60)
    print("ПОСЛЕДОВАТЕЛЬНОСТЬ ФАРЕЯ И КРУГИ ФОРДА")
    print("=" * 60)

    stats = analyze_farey(50)
    print(f"\nПоследовательность Фарея порядка {stats['order']}:")
    print(f"  Размер: {stats['size']} (теоретический: {stats['theoretical_size']})")
    print(f"  Все соседи — Фареевы: {stats['all_neighbors_farey']}")
    print(f"  Уникальных знаменателей: {stats['unique_denominators']}")
    print(f"  Самый частый знаменатель: q={stats['max_denominator_freq'][0]} "
          f"({stats['max_denominator_freq'][1]} раз)")

    print(f"\n  Дроби с длинными цепными дробями:")
    for f, cf in stats['longest_continued_fractions']:
        path = stern_brocot_path(f.numerator, f.denominator)
        print(f"    {f} = [{', '.join(str(c) for c in cf)}]  "
              f"путь: {path[:30]}{'...' if len(path) > 30 else ''}")

    # Визуализация
    print(f"\nГенерация изображения кругов Форда...")
    pixels, w, h, n_fracs = render_ford_circles(order=45, width=1600, height=900)

    print("Сохранение PNG...")
    png_data = make_png(w, h, pixels)
    with open('ford_circles.png', 'wb') as f:
        f.write(png_data)

    size_kb = len(png_data) / 1024
    print(f"\nСохранено: ford_circles.png ({w}x{h}, {size_kb:.0f} КБ)")
    print(f"Дробей в изображении: {n_fracs}")

    # Красивое свойство
    print(f"\n" + "=" * 60)
    print("СВОЙСТВО КАСАНИЯ")
    print("=" * 60)
    print("""
Два круга Форда касаются тогда и только тогда,
когда соответствующие дроби p/q и r/s удовлетворяют:

    |p·s − q·r| = 1

Это — определение соседей Фарея.
Это — условие, что медианта (p+r)/(q+s) лежит между ними.
Это — геометрия, которая кодирует арифметику.

Каждое рациональное число в [0,1] — ровно один круг.
Круги заполняют полуплоскость без зазоров и перекрытий.
Мера незакрытого пространства → 0 при порядке → ∞.

Аполлониева прокладка — похожа, но для неё нужен выбор.
Круги Форда — единственны. Они не сконструированы, а открыты.
""")
