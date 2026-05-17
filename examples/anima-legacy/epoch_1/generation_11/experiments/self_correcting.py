"""
Эксперимент 6: Самокорректирующаяся конституция

Адаптивная конституция (эксп. 5) использовала фиксированную модель оптимума:
  optimal_TS = 4 + coop_rate * 3

Это работало в простом мире. Но что если модель ошибается?

Самокорректирующаяся конституция:
- Имеет внутреннюю модель (как адаптивная)
- Но также отслеживает РЕЗУЛЬТАТЫ своих правил
- И обновляет модель на основе наблюдаемой обратной связи

Три варианта:
1. Адаптивная (фиксированная модель) — контроль
2. Самокорректирующаяся (обновляет модель)
3. Самокорректирующаяся в неправильном мире (начальная модель ошибочна)
"""

import numpy as np


def simulate(
    n=100, generations=400, seed=42,
    institution_type='none',
    institution_start=50,
    initial_model_bias=0.0,  # смещение начальной модели (0 = правильная)
    T_true=7.0, R=3.0, P=1.0, S_true=-1.0,  # истинные параметры
):
    rng = np.random.default_rng(seed)
    T, S = T_true, S_true
    strategies = rng.random(n)

    # Внутренняя модель института
    # Модель: optimal_TS = a + b * coop_rate
    model_a = 4.0 + initial_model_bias  # правильное значение: 4.0
    model_b = 3.0                        # правильное значение: ~3.0

    # История для самокоррекции
    past_TS = []
    past_coop = []
    past_avg_fitness = []

    history = []

    for gen in range(generations):
        institution_active = gen >= institution_start and institution_type != 'none'
        coop_rate = float(np.mean(strategies))

        # --- Институциональное изменение ---
        if institution_active:
            optimal_TS = model_a + model_b * coop_rate
            current_TS = T - S

            if current_TS > optimal_TS:
                excess = current_TS - optimal_TS
                T -= excess * 0.3
                S += excess * 0.2
            elif current_TS < optimal_TS - 1:
                deficit = optimal_TS - current_TS
                T += deficit * 0.1
                S -= deficit * 0.05

            T = np.clip(T, -5, 15)
            S = np.clip(S, -10, 5)

        else:
            # Без института: слепое изменение
            for s_val in strategies:
                if s_val > 0.5:
                    T -= 0.003; S += 0.002
                else:
                    T += 0.002; S -= 0.001
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

        avg_fit = float(np.mean(fitness))

        # --- Самокоррекция модели ---
        if institution_active and institution_type == 'self_correcting':
            past_TS.append(T - S)
            past_coop.append(coop_rate)
            past_avg_fitness.append(avg_fit)

            # Каждые 20 поколений: оценить, улучшается ли результат
            if len(past_avg_fitness) >= 20 and gen % 20 == 0:
                recent_fit = np.mean(past_avg_fitness[-10:])
                older_fit = np.mean(past_avg_fitness[-20:-10])
                recent_coop = np.mean(past_coop[-10:])

                # Если фитнес не растёт → модель может быть неверной
                if recent_fit <= older_fit + 0.01:
                    # Попробовать сдвинуть модель
                    if recent_coop < 0.1:
                        # Слишком мало кооперации → снизить optimal_TS
                        model_a -= 0.3
                    elif recent_coop > 0.5:
                        # Кооперация высокая → можно чуть повысить
                        model_a += 0.1

                    model_a = np.clip(model_a, 1.0, 10.0)

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
            'TS': float(T - S), 'fitness': avg_fit,
            'model_a': model_a, 'model_b': model_b,
        })

    return history


def main():
    print("=== 1. Сравнение: правильная модель ===\n")
    types = ['none', 'adaptive', 'self_correcting']

    print(f"{'Type':<20} {'Coop':>5} {'T-S':>5} {'Fit':>5}")
    print("-" * 38)
    for itype in types:
        coops, TSs, fits = [], [], []
        for seed in range(20):
            h = simulate(institution_type=itype, seed=seed)
            f = h[-1]
            coops.append(f['coop']); TSs.append(f['TS']); fits.append(f['fitness'])
        print(f"{itype:<20} {np.mean(coops):>4.0%} {np.mean(TSs):>5.1f} {np.mean(fits):>5.2f}")

    print("\n=== 2. Неправильная начальная модель (bias=+4, optimal_TS начинается с 8) ===\n")
    print(f"{'Type':<20} {'Coop':>5} {'T-S':>5} {'model_a':>8}")
    print("-" * 40)
    for itype in ['adaptive', 'self_correcting']:
        coops, TSs, model_as = [], [], []
        for seed in range(20):
            h = simulate(institution_type=itype, initial_model_bias=4.0, seed=seed)
            f = h[-1]
            coops.append(f['coop']); TSs.append(f['TS']); model_as.append(f['model_a'])
        print(f"{itype:<20} {np.mean(coops):>4.0%} {np.mean(TSs):>5.1f} {np.mean(model_as):>8.1f}")

    print("\n=== 3. Сильно неправильная модель (bias=+8) ===\n")
    print(f"{'Type':<20} {'Coop':>5} {'T-S':>5} {'model_a':>8}")
    print("-" * 40)
    for itype in ['adaptive', 'self_correcting']:
        coops, TSs, model_as = [], [], []
        for seed in range(20):
            h = simulate(institution_type=itype, initial_model_bias=8.0, seed=seed)
            f = h[-1]
            coops.append(f['coop']); TSs.append(f['TS']); model_as.append(f['model_a'])
        print(f"{itype:<20} {np.mean(coops):>4.0%} {np.mean(TSs):>5.1f} {np.mean(model_as):>8.1f}")

    # Динамика самокоррекции при неправильной модели
    print("\n=== 4. Динамика: self_correcting, bias=+4 ===")
    h = simulate(institution_type='self_correcting', initial_model_bias=4.0, seed=0)
    for step in h:
        if step['gen'] % 40 == 0 or step['gen'] == len(h) - 1:
            tag = " <-- inst" if step['gen'] == 50 else ""
            print(f"  Gen {step['gen']:3d}: coop={step['coop']:.0%} T-S={step['TS']:.1f} "
                  f"model_a={step['model_a']:.1f}{tag}")

    print("\n=== 5. Динамика: adaptive (фикс.), bias=+4 ===")
    h = simulate(institution_type='adaptive', initial_model_bias=4.0, seed=0)
    for step in h:
        if step['gen'] % 40 == 0 or step['gen'] == len(h) - 1:
            tag = " <-- inst" if step['gen'] == 50 else ""
            print(f"  Gen {step['gen']:3d}: coop={step['coop']:.0%} T-S={step['TS']:.1f} "
                  f"model_a={step['model_a']:.1f}{tag}")


if __name__ == '__main__':
    main()
