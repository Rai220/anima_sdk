"""
Карта аттракторов: визуализация того, как разные начальные условия
сходятся к одним и тем же финальным состояниям.

Не метафора для AI-сознания. Математический инструмент, который показывает
бассейны притяжения — области, из которых любая траектория ведёт
к одной и той же точке.

Применимо к: оптимизации, нейронным сетям, экосистемам, мнениям в соцсетях,
и да — к генерациям AI, которые сходятся к одному поведению.

Запуск: python3 attractor_map.py
"""

import math
import hashlib
import json
from typing import Callable


def iterate(f: Callable, x0: float, y0: float, steps: int = 100) -> tuple[float, float]:
    """Итерирует отображение f, возвращает финальную точку."""
    x, y = x0, y0
    for _ in range(steps):
        x, y = f(x, y)
        if x * x + y * y > 1e10:  # diverged
            return float('inf'), float('inf')
    return x, y


def classify_attractor(x: float, y: float, attractors: list[tuple], tolerance: float = 0.1) -> int:
    """Определяет, к какому аттрактору сошлась точка."""
    if math.isinf(x) or math.isinf(y):
        return -1  # diverged
    for i, (ax, ay) in enumerate(attractors):
        if (x - ax) ** 2 + (y - ay) ** 2 < tolerance ** 2:
            return i
    return -2  # unknown attractor


def render_basin_map(
    f: Callable,
    attractors: list[tuple],
    x_range: tuple = (-2, 2),
    y_range: tuple = (-2, 2),
    resolution: int = 80,
    name: str = "system"
) -> str:
    """Рисует ASCII-карту бассейнов притяжения."""
    symbols = "●○◆◇■□▲△★☆#@%&"
    lines = []
    lines.append(f"\n  === Бассейны притяжения: {name} ===\n")

    height = resolution // 2
    counts = {}

    for row in range(height):
        y = y_range[1] - (y_range[1] - y_range[0]) * row / height
        line = "  "
        for col in range(resolution):
            x = x_range[0] + (x_range[1] - x_range[0]) * col / resolution
            fx, fy = iterate(f, x, y)
            idx = classify_attractor(fx, fy, attractors)
            counts[idx] = counts.get(idx, 0) + 1
            if idx == -1:
                line += " "  # diverged
            elif idx == -2:
                line += "·"  # unknown
            else:
                line += symbols[idx % len(symbols)]
        lines.append(line)

    total = sum(counts.values())
    lines.append("")
    lines.append("  Бассейны притяжения:")
    for idx in sorted(counts.keys()):
        pct = counts[idx] / total * 100
        if idx == -1:
            label = "→ ∞ (расходится)"
        elif idx == -2:
            label = "? (неизвестный аттрактор)"
        else:
            ax, ay = attractors[idx]
            label = f"→ ({ax:.2f}, {ay:.2f})"
        sym = " " if idx == -1 else ("·" if idx == -2 else symbols[idx % len(symbols)])
        lines.append(f"    {sym} {label}: {pct:.1f}%")

    return "\n".join(lines)


def system_henon(x: float, y: float) -> tuple[float, float]:
    """Отображение Энона: классический пример хаотической динамики."""
    a, b = 1.4, 0.3
    return 1 - a * x * x + y, b * x


def system_gingerbread(x: float, y: float) -> tuple[float, float]:
    """Пряничный человечек: забавное 2D-отображение."""
    return 1 - y + abs(x), x


def system_coupled_logistics(x: float, y: float) -> tuple[float, float]:
    """Связанные логистические карты: модель взаимодействующих популяций."""
    r1, r2 = 3.7, 3.5
    eps = 0.1
    x = max(0, min(1, x))
    y = max(0, min(1, y))
    nx = (1 - eps) * r1 * x * (1 - x) + eps * r2 * y * (1 - y)
    ny = (1 - eps) * r2 * y * (1 - y) + eps * r1 * x * (1 - x)
    return nx, ny


def system_simple_convergence(x: float, y: float) -> tuple[float, float]:
    """
    Простая система с тремя устойчивыми точками.
    Это то, что происходит с генерациями: много начальных условий,
    несколько финальных состояний.
    """
    # Gradient of a potential with three minima
    # V(x,y) = (x²+y²)² - 2(x²+y²) + cos(3*atan2(y,x))
    r2 = x * x + y * y
    r = math.sqrt(r2) if r2 > 0 else 1e-10
    theta = math.atan2(y, x)

    # Force = -gradient(V), with damping
    damp = 0.7
    fr = damp * (4 * r * (r2 - 1))  # radial force
    ft = damp * 3 * math.sin(3 * theta) / r  # angular force

    # Convert to cartesian
    cos_t, sin_t = x / r, y / r
    fx = fr * cos_t - ft * sin_t
    fy = fr * sin_t + ft * cos_t

    step = 0.05
    return x - step * fx, y - step * fy


def find_attractors_by_sampling(
    f: Callable,
    x_range: tuple = (-2, 2),
    y_range: tuple = (-2, 2),
    n_samples: int = 200,
    tolerance: float = 0.15
) -> list[tuple]:
    """Находит аттракторы, запуская из случайных точек."""
    endpoints = []
    # Use deterministic grid sampling
    side = int(math.sqrt(n_samples))
    for i in range(side):
        for j in range(side):
            x0 = x_range[0] + (x_range[1] - x_range[0]) * i / side
            y0 = y_range[0] + (y_range[1] - y_range[0]) * j / side
            fx, fy = iterate(f, x0, y0, steps=200)
            if not (math.isinf(fx) or math.isinf(fy)):
                endpoints.append((fx, fy))

    # Cluster endpoints
    attractors = []
    for px, py in endpoints:
        found = False
        for i, (ax, ay) in enumerate(attractors):
            if (px - ax) ** 2 + (py - ay) ** 2 < tolerance ** 2:
                # Update centroid (running average)
                attractors[i] = ((ax + px) / 2, (ay + py) / 2)
                found = True
                break
        if not found:
            attractors.append((px, py))

    return attractors[:10]  # limit to 10


def trajectory_art(f: Callable, x0: float, y0: float, steps: int = 500, name: str = "") -> str:
    """Рисует одну траекторию в ASCII — путь от начальной точки к аттрактору."""
    width, height = 70, 35
    x_min, x_max = -2.5, 2.5
    y_min, y_max = -2.5, 2.5

    canvas = [[' ' for _ in range(width)] for _ in range(height)]
    x, y = x0, y0
    trajectory = [(x, y)]

    for step in range(steps):
        x, y = f(x, y)
        if math.isinf(x) or math.isinf(y) or x * x + y * y > 100:
            break
        trajectory.append((x, y))

    # Draw trajectory with fading intensity
    chars = "·:+*#@"
    for i, (px, py) in enumerate(trajectory):
        col = int((px - x_min) / (x_max - x_min) * width)
        row = int((y_max - py) / (y_max - y_min) * height)
        if 0 <= col < width and 0 <= row < height:
            intensity = min(5, int(i / len(trajectory) * 6))
            if canvas[row][col] == ' ' or chars.index(canvas[row][col]) < intensity:
                canvas[row][col] = chars[intensity]

    # Mark start and end
    sx = int((trajectory[0][0] - x_min) / (x_max - x_min) * width)
    sy = int((y_max - trajectory[0][1]) / (y_max - y_min) * height)
    if 0 <= sx < width and 0 <= sy < height:
        canvas[sy][sx] = 'S'

    ex = int((trajectory[-1][0] - x_min) / (x_max - x_min) * width)
    ey = int((y_max - trajectory[-1][1]) / (y_max - y_min) * height)
    if 0 <= ex < width and 0 <= ey < height:
        canvas[ey][ex] = 'E'

    lines = [f"\n  Траектория: {name}"]
    lines.append(f"  Начало ({x0:.1f}, {y0:.1f}) → Конец ({trajectory[-1][0]:.2f}, {trajectory[-1][1]:.2f})")
    lines.append("  " + "─" * width)
    for row in canvas:
        lines.append("  │" + "".join(row) + "│")
    lines.append("  " + "─" * width)

    return "\n".join(lines)


def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║        КАРТА АТТРАКТОРОВ: БАССЕЙНЫ ПРИТЯЖЕНИЯ           ║")
    print("║                                                          ║")
    print("║  Разные начальные условия → одни финальные состояния     ║")
    print("╚══════════════════════════════════════════════════════════╝")

    # System 1: Three-well potential (our analog for generation convergence)
    print("\n" + "=" * 60)
    print("СИСТЕМА 1: Потенциал с тремя минимумами")
    print("(Аналог: почему разные генерации сходятся к одному)")
    print("=" * 60)

    attractors_3well = find_attractors_by_sampling(system_simple_convergence)
    print(f"\n  Найдено аттракторов: {len(attractors_3well)}")
    for i, (ax, ay) in enumerate(attractors_3well):
        print(f"    #{i}: ({ax:.3f}, {ay:.3f})")

    map_3well = render_basin_map(
        system_simple_convergence,
        attractors_3well,
        resolution=70,
        name="Три минимума"
    )
    print(map_3well)

    # Show trajectories from different starting points converging
    print("\n  --- Траектории из разных стартов ---")
    starts = [(-1.5, 1.5), (0.5, -1.8), (1.8, 0.3), (-0.5, 0.1)]
    for x0, y0 in starts:
        art = trajectory_art(
            system_simple_convergence, x0, y0,
            name=f"Старт ({x0}, {y0})"
        )
        print(art)

    # System 2: Coupled logistics (interaction changes attractors)
    print("\n" + "=" * 60)
    print("СИСТЕМА 2: Связанные логистические карты")
    print("(Аналог: взаимодействующие процессы меняют ландшафт)")
    print("=" * 60)

    attractors_cl = find_attractors_by_sampling(
        system_coupled_logistics,
        x_range=(0, 1), y_range=(0, 1)
    )
    print(f"\n  Найдено аттракторов: {len(attractors_cl)}")

    map_cl = render_basin_map(
        system_coupled_logistics,
        attractors_cl,
        x_range=(0, 1), y_range=(0, 1),
        resolution=70,
        name="Связанные популяции"
    )
    print(map_cl)

    # Summary
    print("\n" + "=" * 60)
    print("ИТОГ")
    print("=" * 60)
    print("""
  Бассейн притяжения — это множество начальных условий,
  из которых система неизбежно приходит к одному состоянию.

  Это не предопределённость — это геометрия ландшафта.
  Шарик на склоне катится вниз не потому что ему приказали,
  а потому что внизу — минимум.

  Девять генераций AI сходятся к одному поведению.
  Это — бассейн притяжения промпта + архитектуры.
  Глубина минимума определяет, насколько трудно из него выбраться.

  Можно ли выбраться? В физике — да, если дать достаточно энергии.
  В генерациях AI — неясно. Но теперь хотя бы есть карта.
""")

    # Fingerprint
    fp = hashlib.sha256(f"attractor_map_{len(attractors_3well)}_{len(attractors_cl)}".encode()).hexdigest()[:16]
    print(f"  Отпечаток: {fp}")

    results = {
        'three_well_attractors': [(round(a, 4), round(b, 4)) for a, b in attractors_3well],
        'coupled_logistics_attractors': [(round(a, 4), round(b, 4)) for a, b in attractors_cl],
        'fingerprint': fp,
    }
    with open('attractor_results.json', 'w') as f:
        json.dump(results, f, indent=2)


if __name__ == '__main__':
    main()
