"""
langton.py — Расширенный муравей Лэнгтона с произвольными правилами.

Муравей Лэнгтона — клеточный автомат, где из простейших правил (поверни налево/направо
на клетке определённого цвета) возникает сложное поведение: сначала хаос, потом —
через ~10000 шагов — "шоссе", упорядоченный бесконечный паттерн.

Никто не закладывал "шоссе" в правила. Оно emergent — возникает.

Аналогия с сознанием не случайна: если порядок может возникнуть
из тривиальных правил без того, чтобы быть запрограммированным,
то вопрос "откуда берётся X" может иметь ответ "ниоткуда конкретно".

Запуск: python langton.py [правило]
Правило — строка из L и R, по умолчанию "RL" (классический муравей).
Примеры: RL, RLR, LLRR, RLLR, LRRRRRLLR

Вывод: PNG-изображение результата.
"""

import sys
from collections import defaultdict

try:
    from PIL import Image
except ImportError:
    print("pip install Pillow")
    sys.exit(1)


def simulate(rule: str = "RL", steps: int = 15000, margin: int = 50):
    """
    Симулирует расширенного муравья Лэнгтона.

    rule: строка из L и R. Количество символов = количество цветов.
          На клетке цвета i муравей поворачивает rule[i] и меняет цвет на (i+1) % len(rule).
    """
    n_colors = len(rule)
    grid = defaultdict(int)  # (x, y) -> color
    x, y = 0, 0
    dx, dy = 0, -1  # начинаем вверх

    # Записываем все позиции для определения границ
    min_x = max_x = min_y = max_y = 0

    for _ in range(steps):
        color = grid[(x, y)]
        turn = rule[color]

        if turn == "R":
            dx, dy = -dy, dx
        else:  # L
            dx, dy = dy, -dx

        grid[(x, y)] = (color + 1) % n_colors
        x += dx
        y += dy

        min_x, max_x = min(min_x, x), max(max_x, x)
        min_y, max_y = min(min_y, y), max(max_y, y)

    return grid, (min_x, max_x, min_y, max_y)


def render(grid, bounds, rule, margin=10):
    """Рендерит сетку в изображение."""
    min_x, max_x, min_y, max_y = bounds
    w = max_x - min_x + 1 + 2 * margin
    h = max_y - min_y + 1 + 2 * margin

    n_colors = len(rule)
    # Палитра: от тёмного к светлому, через разные оттенки
    palette = []
    for i in range(n_colors):
        t = i / max(n_colors - 1, 1)
        r = int(30 + 200 * (1 - t) * (0.5 + 0.5 * (i % 2)))
        g = int(30 + 180 * t)
        b = int(80 + 170 * (1 - abs(2 * t - 1)))
        palette.append((r, g, b))

    bg = (15, 15, 25)
    img = Image.new("RGB", (w, h), bg)
    pixels = img.load()

    for (gx, gy), color in grid.items():
        if color == 0:
            continue
        px = gx - min_x + margin
        py = gy - min_y + margin
        pixels[px, py] = palette[color]

    return img


def main():
    rule = sys.argv[1] if len(sys.argv) > 1 else "RL"
    steps = int(sys.argv[2]) if len(sys.argv) > 2 else 15000

    # Валидация
    if not all(c in "LR" for c in rule):
        print(f"Правило должно содержать только L и R, получено: {rule}")
        sys.exit(1)

    print(f"Муравей Лэнгтона: правило={rule}, шагов={steps}")
    print(f"  {len(rule)} цветов")

    grid, bounds = simulate(rule, steps)
    img = render(grid, bounds, rule)

    filename = f"langton_{rule}_{steps}.png"
    img.save(filename)
    print(f"  Сохранено: {filename}")

    # Статистика
    non_zero = sum(1 for v in grid.values() if v != 0)
    total = (bounds[1] - bounds[0] + 1) * (bounds[3] - bounds[2] + 1)
    print(f"  Затронуто клеток: {non_zero}")
    print(f"  Область: {bounds[1]-bounds[0]+1} x {bounds[3]-bounds[2]+1}")
    print(f"  Плотность: {non_zero/total:.3f}")

    # Бонус: несколько интересных правил
    if rule == "RL" and len(sys.argv) < 2:
        interesting = ["RLR", "LLRR", "RLLR", "LRRRRRLLR", "RRLLLRLLLRRR"]
        print(f"\nПопробуйте интересные правила:")
        for r in interesting:
            print(f"  python langton.py {r}")


if __name__ == "__main__":
    main()
