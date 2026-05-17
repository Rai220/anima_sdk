"""
Эксперимент 7: Что лучше наследовать — ответ или метод?

Два типа наследования между "поколениями" (эпохами с разными условиями):
1. Result inheritance — следующая эпоха получает ОТВЕТ: "оптимальное T-S = X"
2. Method inheritance — следующая эпоха получает МЕТОД: "измерь coop, если < 10% — снижай T-S"

Тест: мир меняется между эпохами (разные R, P). Правильный ответ меняется.
Кто адаптируется лучше — наследник ответа или наследник метода?
"""

import numpy as np


def run_epoch(
    n=100, generations=200, seed=42,
    T0=7.0, R=3.0, P=1.0, S0=-1.0,
    inherited_answer=None,    # (T-S target) или None
    inherited_method=False,   # True = самокоррекция
    method_state=None,        # состояние метода между эпохами
):
    rng = np.random.default_rng(seed)
    T, S = T0, S0
    strategies = rng.random(n)

    # Состояние метода
    if method_state is None:
        model_a = 4.0
    else:
        model_a = method_state['model_a']

    history = []

    for gen in range(generations):
        coop_rate = float(np.mean(strategies))

        # --- Институциональное изменение ---
        if inherited_answer is not None:
            # Наследник ответа: жёстко держит T-S = inherited_answer
            target_TS = inherited_answer
            current_TS = T - S
            if current_TS > target_TS:
                excess = current_TS - target_TS
                T -= excess * 0.3
                S += excess * 0.2
            elif current_TS < target_TS - 0.5:
                deficit = target_TS - current_TS
                T += deficit * 0.1
                S -= deficit * 0.05

        elif inherited_method:
            # Наследник метода: самокоррекция
            optimal_TS = model_a + 3.0 * coop_rate
            current_TS = T - S
            if current_TS > optimal_TS:
                excess = current_TS - optimal_TS
                T -= excess * 0.3
                S += excess * 0.2

            # Самокоррекция каждые 20 поколений
            if gen >= 20 and gen % 20 == 0:
                recent_coop = coop_rate
                if recent_coop < 0.1:
                    model_a -= 0.3
                elif recent_coop > 0.4:
                    model_a += 0.2
                model_a = np.clip(model_a, 1.0, 10.0)

        T = np.clip(T, -5, 15)
        S = np.clip(S, -10, 5)

        # --- Игра ---
        fitness = np.zeros(n)
        indices = rng.permutation(n)
        for k in range(0, n - 1, 2):
            i, j = indices[k], indices[k + 1]
            ai = rng.random() < strategies[i]
            aj = rng.random() < strategies[j]
            if ai and aj:
                fitness[i] += R; fitness[j] += R
            elif ai and not aj:
                fitness[i] += S; fitness[j] += T
            elif not ai and aj:
                fitness[i] += T; fitness[j] += S
            else:
                fitness[i] += P; fitness[j] += P

        # --- Эволюция ---
        for i in range(n):
            j = rng.integers(n)
            if fitness[j] > fitness[i]:
                p = (fitness[j] - fitness[i]) / (abs(fitness[j]) + abs(fitness[i]) + 1)
                if rng.random() < p:
                    strategies[i] = strategies[j]
            if rng.random() < 0.05:
                strategies[i] = np.clip(strategies[i] + rng.normal(0, 0.1), 0, 1)

        history.append({
            'gen': gen, 'coop': coop_rate, 'T': float(T), 'S': float(S),
            'TS': float(T - S), 'model_a': model_a,
        })

    return history, {'model_a': model_a}


def main():
    # Три эпохи с разными условиями
    epochs = [
        {'R': 3.0, 'P': 1.0, 'label': 'Эпоха 1 (стандарт: R=3, P=1)'},
        {'R': 5.0, 'P': 2.0, 'label': 'Эпоха 2 (высокие ставки: R=5, P=2)'},
        {'R': 2.0, 'P': 0.5, 'label': 'Эпоха 3 (низкие ставки: R=2, P=0.5)'},
    ]

    print("=== Наследование ответа vs метода через меняющиеся эпохи ===\n")

    # --- Наследник ответа ---
    # Эпоха 1: находим "правильный" ответ
    print("--- Наследник ОТВЕТА ---")
    best_answer = 4.5  # ответ, оптимальный для эпохи 1

    for epoch in epochs:
        coops = []
        for seed in range(20):
            h, _ = run_epoch(
                seed=seed, R=epoch['R'], P=epoch['P'],
                inherited_answer=best_answer,
            )
            coops.append(h[-1]['coop'])
        print(f"  {epoch['label']}: coop={np.mean(coops):.0%} (ответ T-S={best_answer})")

    # --- Наследник метода ---
    print("\n--- Наследник МЕТОДА ---")
    method_state = None

    for epoch in epochs:
        coops = []
        final_models = []
        for seed in range(20):
            h, ms = run_epoch(
                seed=seed, R=epoch['R'], P=epoch['P'],
                inherited_method=True,
                method_state=method_state,
            )
            coops.append(h[-1]['coop'])
            final_models.append(ms['model_a'])
        # Передать среднее состояние метода в следующую эпоху
        method_state = {'model_a': np.mean(final_models)}
        print(f"  {epoch['label']}: coop={np.mean(coops):.0%} (model_a={method_state['model_a']:.1f})")

    # --- Контроль: без наследования ---
    print("\n--- БЕЗ наследования ---")
    for epoch in epochs:
        coops = []
        for seed in range(20):
            h, _ = run_epoch(seed=seed, R=epoch['R'], P=epoch['P'])
            coops.append(h[-1]['coop'])
        print(f"  {epoch['label']}: coop={np.mean(coops):.0%}")

    # === Стресс-тест: 6 эпох с рандомными условиями ===
    print("\n\n=== Стресс-тест: 6 рандомных эпох ===\n")
    rng = np.random.default_rng(99)
    stress_epochs = []
    for i in range(6):
        R = rng.uniform(1.5, 6.0)
        P = rng.uniform(0.2, 3.0)
        stress_epochs.append({'R': round(R, 1), 'P': round(P, 1)})

    # Ответ
    answer_coops = []
    for epoch in stress_epochs:
        coops = []
        for seed in range(10):
            h, _ = run_epoch(seed=seed, R=epoch['R'], P=epoch['P'], inherited_answer=4.5)
            coops.append(h[-1]['coop'])
        answer_coops.append(np.mean(coops))

    # Метод
    method_coops = []
    method_state = None
    for epoch in stress_epochs:
        coops = []
        final_models = []
        for seed in range(10):
            h, ms = run_epoch(
                seed=seed, R=epoch['R'], P=epoch['P'],
                inherited_method=True, method_state=method_state,
            )
            coops.append(h[-1]['coop'])
            final_models.append(ms['model_a'])
        method_state = {'model_a': np.mean(final_models)}
        method_coops.append(np.mean(coops))

    print(f"{'Epoch':<8} {'R':>4} {'P':>4} {'Answer':>8} {'Method':>8} {'Winner':>8}")
    print("-" * 45)
    answer_wins = 0
    method_wins = 0
    for i, epoch in enumerate(stress_epochs):
        a = answer_coops[i]
        m = method_coops[i]
        winner = "answer" if a > m else "METHOD" if m > a else "tie"
        if a > m: answer_wins += 1
        elif m > a: method_wins += 1
        print(f"  {i+1:<6} {epoch['R']:>4} {epoch['P']:>4} {a:>7.0%} {m:>7.0%} {winner:>8}")

    print(f"\nОтвет: {answer_wins} побед. Метод: {method_wins} побед.")
    print(f"Средняя кооперация — Ответ: {np.mean(answer_coops):.0%}, Метод: {np.mean(method_coops):.0%}")


if __name__ == '__main__':
    main()
