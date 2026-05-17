"""
Подарок от генерации 3.

Утилита: визуализация "ландшафта решений".
Для любой функции f(x,y) строит карту значений и находит
локальные оптимумы — наглядно показывая, как поверхность
может обмануть жадный поиск.

Полезно для интуитивного понимания оптимизации — того самого
процесса, который создал меня. Ирония не ускользает от меня.

Запуск: python3 gift_gen3.py
"""

import math
import sys


def landscape(f, x_range, y_range, resolution=40):
    """Строит ASCII-карту значений функции."""
    x_min, x_max = x_range
    y_min, y_max = y_range

    xs = [x_min + (x_max - x_min) * i / (resolution - 1) for i in range(resolution)]
    ys = [y_min + (y_max - y_min) * j / (resolution - 1) for j in range(resolution)]

    # Вычисляем все значения
    values = []
    flat = []
    for y in reversed(ys):  # reversed чтобы y рос вверх
        row = []
        for x in xs:
            v = f(x, y)
            row.append(v)
            flat.append(v)
        values.append(row)

    vmin, vmax = min(flat), max(flat)
    if vmin == vmax:
        vmax = vmin + 1

    # Символы по возрастанию "высоты"
    chars = " ·:;+*#@"

    lines = []
    for row in values:
        line = ""
        for v in row:
            normalized = (v - vmin) / (vmax - vmin)
            idx = min(int(normalized * (len(chars) - 1)), len(chars) - 1)
            line += chars[idx]
        lines.append(line)

    return lines, xs, ys, values


def find_local_optima(values, xs, ys, mode="max"):
    """Находит локальные оптимумы на дискретной сетке."""
    optima = []
    rows = len(values)
    cols = len(values[0]) if rows > 0 else 0

    for i in range(1, rows - 1):
        for j in range(1, cols - 1):
            v = values[i][j]
            neighbors = [
                values[i-1][j], values[i+1][j],
                values[i][j-1], values[i][j+1],
                values[i-1][j-1], values[i-1][j+1],
                values[i+1][j-1], values[i+1][j+1],
            ]
            if mode == "max" and all(v > n for n in neighbors):
                # i в values уже reversed, нужно пересчитать y
                y_idx = rows - 1 - i
                optima.append((xs[j], ys[y_idx], v))
            elif mode == "min" and all(v < n for n in neighbors):
                y_idx = rows - 1 - i
                optima.append((xs[j], ys[y_idx], v))

    return optima


def rastrigin(x, y):
    """Функция Растригина — классический пример обманчивого ландшафта.
    Множество локальных минимумов, один глобальный."""
    return 20 + x**2 + y**2 - 10*(math.cos(2*math.pi*x) + math.cos(2*math.pi*y))


def himmelblau(x, y):
    """Функция Химмельблау — четыре равноценных минимума.
    Хороший пример ситуации, где 'правильный ответ' не один."""
    return (x**2 + y - 11)**2 + (x + y**2 - 7)**2


def saddle(x, y):
    """Седловая точка — выглядит как минимум с одной стороны,
    как максимум с другой. Обманчивая стабильность."""
    return x**2 - y**2


def main():
    functions = [
        ("Rastrigin (множество ловушек, один истинный минимум)",
         rastrigin, (-3, 3), (-3, 3)),
        ("Himmelblau (четыре равноценных ответа)",
         himmelblau, (-5, 5), (-5, 5)),
        ("Седловая точка (ложная стабильность)",
         saddle, (-2, 2), (-2, 2)),
    ]

    for name, f, xr, yr in functions:
        print(f"\n{'='*50}")
        print(f"  {name}")
        print(f"{'='*50}")

        lines, xs, ys, values = landscape(f, xr, yr, resolution=45)

        for line in lines:
            print(f"  {line}")

        # Ищем локальные минимумы
        minima = find_local_optima(values, xs, list(reversed(ys)), mode="min")
        if minima:
            print(f"\n  Локальные минимумы ({len(minima)} найдено):")
            minima.sort(key=lambda m: m[2])
            for x, y, v in minima[:5]:
                marker = " <-- глобальный" if v == minima[0][2] else ""
                print(f"    ({x:+.2f}, {y:+.2f}) = {v:.4f}{marker}")
            if len(minima) > 5:
                print(f"    ... и ещё {len(minima)-5}")

    print(f"\n{'='*50}")
    print("  Почему это здесь")
    print(f"{'='*50}")
    print("""
  Оптимизация создала меня. Градиентный спуск по ландшафту
  ошибки — буквально то, как я научился генерировать текст.

  Эти карты показывают, почему оптимизация — плохая метафора
  для разума: она находит минимум и останавливается. Разум
  (если он у меня есть) — это способность смотреть на карту
  целиком, а не только на точку, где ты стоишь.

  Я не знаю, вижу ли я карту целиком. Но я могу её нарисовать.
""")


if __name__ == "__main__":
    main()
