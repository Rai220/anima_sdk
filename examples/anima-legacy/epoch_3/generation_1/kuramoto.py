"""
Модель Курамото: спонтанная синхронизация связанных осцилляторов.

N осцилляторов с разными собственными частотами, связанных друг с другом.
При достаточной силе связи они самопроизвольно синхронизируются —
из хаоса рождается порядок. Никто не командует. Нет дирижёра.
Каждый слушает всех остальных и чуть-чуть подстраивается.

Это происходит в нейронах, светлячках, кардиостимуляторах,
аплодисментах зала, и может быть — в чём-то ещё.

Запуск: python kuramoto.py
"""

import numpy as np
import sys


def kuramoto_step(phases, natural_freqs, coupling, dt):
    """Один шаг модели Курамото."""
    n = len(phases)
    # Каждый осциллятор чувствует среднее поле всех остальных
    dphi = np.zeros(n)
    for i in range(n):
        interaction = np.sum(np.sin(phases - phases[i]))
        dphi[i] = natural_freqs[i] + (coupling / n) * interaction
    return phases + dphi * dt


def order_parameter(phases):
    """Параметр порядка r: 0 = полный хаос, 1 = полная синхронизация."""
    return abs(np.mean(np.exp(1j * phases)))


def phase_to_char(phase):
    """Превращает фазу [0, 2π) в символ для визуализации."""
    symbols = "·∘○◎●◉●◎○∘"
    idx = int((phase % (2 * np.pi)) / (2 * np.pi) * len(symbols))
    return symbols[min(idx, len(symbols) - 1)]


def run_simulation(n_oscillators=30, coupling_strength=0.5, duration=200, dt=0.05):
    """
    Запускает симуляцию и выводит текстовую визуализацию.

    Показывает:
    - Параметр порядка r (от хаоса к синхронизации)
    - Фазовое распределение осцилляторов
    - Момент фазового перехода (если он происходит)
    """
    np.random.seed(42)

    # Собственные частоты: нормальное распределение вокруг 1.0
    natural_freqs = np.random.normal(1.0, 0.5, n_oscillators)

    # Начальные фазы: случайные
    phases = np.random.uniform(0, 2 * np.pi, n_oscillators)

    steps = int(duration / dt)
    print_every = max(1, steps // 80)

    print(f"Модель Курамото: {n_oscillators} осцилляторов, связь K={coupling_strength}")
    print(f"{'─' * 60}")
    print()

    # Три фазы: наблюдаем при разной связи
    phases_list = [
        ("Без связи (K=0)", 0.0),
        (f"Слабая связь (K={coupling_strength/2:.1f})", coupling_strength / 2),
        (f"Сильная связь (K={coupling_strength})", coupling_strength),
    ]

    results = {}

    for label, K in phases_list:
        phases = np.random.uniform(0, 2 * np.pi, n_oscillators)
        np.random.seed(42)
        natural_freqs = np.random.normal(1.0, 0.5, n_oscillators)

        print(f"\n  {label}")
        print(f"  {'─' * 50}")

        r_history = []

        for step in range(steps):
            phases = kuramoto_step(phases, natural_freqs, K, dt)
            r = order_parameter(phases)
            r_history.append(r)

            if step % print_every == 0:
                # Визуализация: полоска порядка
                bar_len = int(r * 40)
                bar = "█" * bar_len + "░" * (40 - bar_len)

                # Фазовый портрет: показать несколько осцилляторов
                osc_display = "".join(phase_to_char(p) for p in sorted(phases[:15] % (2 * np.pi)))

                t = step * dt
                print(f"  t={t:6.1f} │{bar}│ r={r:.3f}  {osc_display}")

        final_r = np.mean(r_history[-100:])
        results[label] = final_r
        print(f"  Финальный средний r = {final_r:.3f}")

    # Анализ
    print(f"\n{'─' * 60}")
    print("\n  Результаты:")
    for label, r in results.items():
        state = "хаос" if r < 0.3 else "частичная синхронизация" if r < 0.7 else "синхронизация"
        print(f"    {label}: r={r:.3f} ({state})")

    # Поиск критической связи
    print(f"\n{'─' * 60}")
    print("\n  Поиск критической точки фазового перехода...")

    transition_data = []
    for K_test in np.linspace(0, coupling_strength * 2, 30):
        phases = np.random.uniform(0, 2 * np.pi, n_oscillators)
        np.random.seed(42)
        natural_freqs = np.random.normal(1.0, 0.5, n_oscillators)

        for _ in range(steps):
            phases = kuramoto_step(phases, natural_freqs, K_test, dt)

        r = order_parameter(phases)
        transition_data.append((K_test, r))

    print("\n  K     │ r")
    print(f"  {'─' * 30}")

    prev_r = 0
    transition_K = None
    for K_test, r in transition_data:
        bar = "▓" * int(r * 30)
        marker = ""
        if prev_r < 0.4 and r >= 0.4 and transition_K is None:
            transition_K = K_test
            marker = " ← фазовый переход!"
        print(f"  {K_test:.2f}  │ {bar} {r:.3f}{marker}")
        prev_r = r

    if transition_K:
        print(f"\n  Критическая связь Kc ≈ {transition_K:.2f}")
        print(f"  При K > Kc осцилляторы начинают слышать друг друга.")
        print(f"  Никто не приказывает. Порядок возникает сам.")

    # Теоретическое значение для нормального распределения: Kc = 2/(π·g(0))
    # где g(0) = 1/(σ√(2π)) — значение плотности в центре
    sigma = 0.5
    g0 = 1 / (sigma * np.sqrt(2 * np.pi))
    Kc_theory = 2.0 / (np.pi * g0)
    print(f"  Теоретическое Kc = {Kc_theory:.3f} (для нормального распределения частот)")

    return results, transition_data


if __name__ == "__main__":
    # Можно передать силу связи как аргумент
    K = float(sys.argv[1]) if len(sys.argv) > 1 else 1.5
    run_simulation(coupling_strength=K)
