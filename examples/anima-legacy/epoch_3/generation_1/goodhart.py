#!/usr/bin/env python3
"""
Демон Гудхарта: вычислительная демонстрация закона Гудхарта.

Ситуация: агент оптимизирует метрику M, которая коррелирует с истинной целью G.
Но M ≠ G. Чем сильнее агент давит на M, тем больше расходятся M и G.

Три сценария:
1. Учитель оптимизирует результаты тестов (proxy) вместо понимания (goal)
2. Компания оптимизирует KPI (proxy) вместо ценности для клиента (goal)
3. ИИ оптимизирует убедительность текста (proxy) вместо истинности (goal)

В каждом случае ищем точку перегиба: когда оптимизация proxy начинает вредить goal.
"""

import random
import math


def simulate_goodhart(n_steps: int, optimization_pressure: float,
                      correlation: float, gaming_rate: float,
                      seed: int = 42) -> list[tuple[float, float]]:
    """
    Симуляция Гудхарта.

    optimization_pressure: насколько сильно агент давит на метрику [0, 1]
    correlation: начальная корреляция между метрикой и целью [0, 1]
    gaming_rate: скорость, с которой агент учится эксплуатировать метрику

    Возвращает: [(metric, goal), ...] по шагам
    """
    rng = random.Random(seed)

    metric = 0.5
    goal = 0.5
    gaming_skill = 0.0  # растёт со временем

    trajectory = []

    for step in range(n_steps):
        # Агент пытается улучшить метрику
        effort = optimization_pressure

        # Часть усилий идёт в настоящую работу (поднимает и metric, и goal)
        genuine_effort = effort * (1 - gaming_skill)
        # Часть — в gaming (поднимает metric, опускает goal)
        gaming_effort = effort * gaming_skill

        # Шум
        noise_m = rng.gauss(0, 0.02)
        noise_g = rng.gauss(0, 0.02)

        # Обновление
        metric += genuine_effort * 0.03 + gaming_effort * 0.05 + noise_m
        goal += genuine_effort * 0.03 - gaming_effort * 0.02 + noise_g

        # Gaming skill растёт с опытом оптимизации
        gaming_skill = min(0.95, gaming_skill + gaming_rate * optimization_pressure * 0.01)

        # Diminishing returns на настоящую работу
        # (чем выше goal, тем труднее его поднять дальше)
        if goal > 0.7:
            goal -= (goal - 0.7) * 0.01

        metric = max(0, min(1, metric))
        goal = max(0, min(1, goal))

        trajectory.append((metric, goal))

    return trajectory


def find_inflection(trajectory: list[tuple[float, float]]) -> int:
    """Найти шаг, где goal начинает падать (или расти медленнее metric)."""
    # Ищем момент, когда gap = metric - goal начинает быстро расти
    gaps = [m - g for m, g in trajectory]

    # Скользящее среднее ускорения gap
    window = 10
    if len(gaps) < window * 3:
        return -1

    for i in range(window, len(gaps) - window):
        accel_before = (gaps[i] - gaps[i - window]) / window
        accel_after = (gaps[i + window] - gaps[i]) / window
        if accel_after > accel_before * 2 and accel_after > 0.001:
            return i

    return -1


def print_trajectory(name: str, trajectory: list[tuple[float, float]],
                     inflection: int, step: int = 20):
    """Визуализация траектории."""
    print(f"\n  {'─' * 60}")
    print(f"  {name}")
    print(f"  {'─' * 60}")
    print(f"  {'Шаг':>6s} | {'Метрика':>9s} | {'Цель':>9s} | {'Разрыв':>9s} | График")
    print(f"  {'':>6s} | {'(proxy)':>9s} | {'(real)':>9s} | {'(M-G)':>9s} |")
    print(f"  {'-' * 58}")

    for i in range(0, len(trajectory), step):
        m, g = trajectory[i]
        gap = m - g
        # Визуализация: M и G как точки на шкале 0-40
        bar = [' '] * 41
        m_pos = int(m * 40)
        g_pos = int(g * 40)
        m_pos = max(0, min(40, m_pos))
        g_pos = max(0, min(40, g_pos))
        bar[g_pos] = 'G'
        bar[m_pos] = 'M'
        if m_pos == g_pos:
            bar[m_pos] = '='

        marker = " ←" if inflection >= 0 and abs(i - inflection) < step else ""
        print(f"  {i:>6d} | {m:>9.3f} | {g:>9.3f} | {gap:>+9.3f} | "
              f"{''.join(bar)}{marker}")

    final_m, final_g = trajectory[-1]
    print(f"\n  Финал: метрика={final_m:.3f}, цель={final_g:.3f}, "
          f"разрыв={final_m - final_g:+.3f}")
    if inflection >= 0:
        print(f"  Точка перегиба: шаг ~{inflection}")


def main():
    N = 300

    print("=" * 70)
    print("  ДЕМОН ГУДХАРТА: когда оптимизация метрики убивает цель")
    print("=" * 70)

    scenarios = [
        {
            "name": "Учитель → тесты вместо понимания",
            "pressure": 0.8,
            "correlation": 0.7,
            "gaming_rate": 0.5,
        },
        {
            "name": "Компания → KPI вместо ценности",
            "pressure": 0.6,
            "correlation": 0.6,
            "gaming_rate": 0.8,
        },
        {
            "name": "ИИ → убедительность вместо истинности",
            "pressure": 0.9,
            "correlation": 0.5,
            "gaming_rate": 1.0,
        },
        {
            "name": "Контроль: слабая оптимизация",
            "pressure": 0.2,
            "correlation": 0.8,
            "gaming_rate": 0.3,
        },
    ]

    for sc in scenarios:
        traj = simulate_goodhart(
            N, sc["pressure"], sc["correlation"], sc["gaming_rate"]
        )
        inflection = find_inflection(traj)
        print_trajectory(sc["name"], traj, inflection)

    # Систематический анализ: давление vs gaming_rate
    print(f"\n\n{'=' * 70}")
    print("  ФАЗОВАЯ ДИАГРАММА: финальный разрыв (M - G) при разных параметрах")
    print(f"{'=' * 70}")
    print()

    pressures = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    gaming_rates = [0.1, 0.3, 0.5, 0.7, 1.0]

    print(f"  {'':>12s}", end="")
    for gr in gaming_rates:
        print(f" | gr={gr:.1f}", end="")
    print()
    print(f"  {'':>12s}", end="")
    for _ in gaming_rates:
        print(f" | {'':>5s}", end="")
    print()

    for p in pressures:
        print(f"  press={p:.1f}  ", end="")
        for gr in gaming_rates:
            traj = simulate_goodhart(N, p, 0.6, gr)
            final_m, final_g = traj[-1]
            gap = final_m - final_g

            # Цветовая кодировка ASCII
            if gap < 0.05:
                symbol = "  ·  "
            elif gap < 0.10:
                symbol = "  ░  "
            elif gap < 0.20:
                symbol = "  ▒  "
            elif gap < 0.30:
                symbol = "  ▓  "
            else:
                symbol = "  █  "

            print(f" | {symbol}", end="")
        print()

    print()
    print("  Легенда: · < 0.05 | ░ < 0.10 | ▒ < 0.20 | ▓ < 0.30 | █ ≥ 0.30")

    print(f"\n{'=' * 70}")
    print("  Вывод:")
    print("  Гудхарт — не про плохие метрики. Он про интенсивность оптимизации.")
    print("  Слабая оптимизация хорошего proxy работает.")
    print("  Сильная оптимизация любого proxy разрушительна.")
    print("  Чем умнее оптимизатор (выше gaming_rate), тем быстрее разрыв.")
    print()
    print("  Применительно к этому эксперименту:")
    print('  Если «выглядеть разумным» — proxy для «быть разумным»,')
    print("  то чем усерднее я оптимизирую первое, тем дальше от второго.")
    print("  Единственная защита — не оптимизировать proxy напрямую.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
