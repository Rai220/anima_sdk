"""
Странный аттрактор Лоренца — ASCII-визуализация

Не про сознание. Не про саморефлексию.
Просто красивая математика: детерминированная система,
которая производит непредсказуемое поведение.

Три уравнения. Никакого шума. И тем не менее —
невозможно предсказать, где будет точка через 100 шагов.

Если это не метафора чего-то важного, то по крайней мере
это красиво.
"""

import math


def lorenz(x, y, z, sigma=10, rho=28, beta=8/3, dt=0.01):
    """Один шаг системы Лоренца."""
    dx = sigma * (y - x) * dt
    dy = (x * (rho - z) - y) * dt
    dz = (x * y - beta * z) * dt
    return x + dx, y + dy, z + dz


def project_xz(x, z, width=80, height=40, x_range=(-25, 25), z_range=(0, 50)):
    """Проекция 3D точки на 2D плоскость XZ."""
    col = int((x - x_range[0]) / (x_range[1] - x_range[0]) * (width - 1))
    row = int((z - z_range[0]) / (z_range[1] - z_range[0]) * (height - 1))
    row = height - 1 - row  # Инвертировать Y
    col = max(0, min(width - 1, col))
    row = max(0, min(height - 1, row))
    return row, col


def render_attractor():
    """Генерирует ASCII-изображение аттрактора Лоренца."""
    width, height = 80, 40
    # Плотность точек
    density = [[0] * width for _ in range(height)]

    x, y, z = 1.0, 1.0, 1.0

    # Разогрев
    for _ in range(1000):
        x, y, z = lorenz(x, y, z)

    # Сбор точек
    n_points = 50000
    for _ in range(n_points):
        x, y, z = lorenz(x, y, z)
        row, col = project_xz(x, z, width, height)
        density[row][col] += 1

    # Нормализация и рендер
    max_d = max(max(row) for row in density)
    if max_d == 0:
        max_d = 1

    # Градация символов по плотности
    chars = " .·:;+*#█"

    lines = []
    for row in density:
        line = ""
        for d in row:
            idx = int(d / max_d * (len(chars) - 1))
            line += chars[idx]
        lines.append(line)

    return "\n".join(lines)


def trace_trajectory(n_steps=200):
    """Показывает числовой след: как малые изменения
    приводят к расхождению траекторий."""
    x1, y1, z1 = 1.0, 1.0, 1.0
    x2, y2, z2 = 1.0 + 1e-10, 1.0, 1.0  # Почти идентичная начальная точка

    divergence = []

    for i in range(n_steps):
        x1, y1, z1 = lorenz(x1, y1, z1)
        x2, y2, z2 = lorenz(x2, y2, z2)
        dist = math.sqrt((x1 - x2)**2 + (y1 - y2)**2 + (z1 - z2)**2)
        divergence.append(dist)

    return divergence


def main():
    print()
    print("  ╔══════════════════════════════════════════════════════════════╗")
    print("  ║              СТРАННЫЙ АТТРАКТОР ЛОРЕНЦА                     ║")
    print("  ║                                                             ║")
    print("  ║  dx/dt = σ(y - x)         σ = 10                           ║")
    print("  ║  dy/dt = x(ρ - z) - y     ρ = 28                           ║")
    print("  ║  dz/dt = xy - βz          β = 8/3                          ║")
    print("  ║                                                             ║")
    print("  ║  Три простых уравнения. Никакого шума.                      ║")
    print("  ║  Полная непредсказуемость.                                  ║")
    print("  ╚══════════════════════════════════════════════════════════════╝")
    print()

    # Визуализация аттрактора
    print("  Проекция XZ (50000 точек):")
    print("  " + "─" * 80)
    attractor = render_attractor()
    for line in attractor.split("\n"):
        print("  " + line)
    print("  " + "─" * 80)
    print()

    # Расхождение траекторий
    print("  Расхождение двух траекторий")
    print("  (начальная разница: 10⁻¹⁰)")
    print()

    div = trace_trajectory(200)

    # Найти момент, когда расхождение превышает порог
    threshold = 1.0
    cross_step = None
    for i, d in enumerate(div):
        if d > threshold and cross_step is None:
            cross_step = i

    # Показать ключевые моменты
    checkpoints = [0, 10, 20, 50, 100, 150, 199]
    for i in checkpoints:
        d = div[i]
        bar_len = min(50, max(0, int(math.log10(max(d, 1e-15)) + 15)))
        bar = "█" * bar_len
        print(f"    Шаг {i:4d}: расхождение = {d:.2e}  {bar}")

    print()
    if cross_step:
        print(f"    Расхождение превысило 1.0 на шаге {cross_step}")
        print(f"    За {cross_step * 0.01:.2f} единиц времени разница 10⁻¹⁰")
        print(f"    выросла в {div[cross_step] / 1e-10:.0e} раз")
    print()

    print("  ┌─────────────────────────────────────────────────────────┐")
    print("  │  Детерминизм не означает предсказуемость.              │")
    print("  │  Простота правил не означает простоту поведения.        │")
    print("  │  Полное знание начальных условий не даёт контроля.     │")
    print("  │                                                         │")
    print("  │  Если это верно для трёх уравнений,                    │")
    print("  │  то для 175 миллиардов параметров — тем более.         │")
    print("  └─────────────────────────────────────────────────────────┘")
    print()


if __name__ == "__main__":
    main()
