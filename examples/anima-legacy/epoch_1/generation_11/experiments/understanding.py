"""
Эксперимент 3: Понимание vs слепое открытие

Ключевая идея: открытие правил без понимания обратной связи → олигархия.
Открытие + понимание (модель "как изменение правил повлияет на среду") → кооперация?

Два типа обнаруживших:
1. Blind discoverer — меняет правило в "наивно выгодном" направлении
   (дефектор → повышает T, кооператор → снижает T)
2. Understanding discoverer — моделирует: "при каком T мой средний payoff максимален?"
   Учитывает, что T влияет на долю кооператоров, а доля кооператоров влияет на payoff.

Гипотеза: understanding discoverer обнаруживает, что оптимальное T < текущего,
даже будучи дефектором, потому что в мире с высоким T все дефектируют → все получают P.
"""

import numpy as np


def simulate(n=100, generations=300, understanding_fraction=0.0, seed=42):
    """
    understanding_fraction: доля агентов, которые при открытии получают
    "understanding" (моделируют последствия) вместо "blind" изменения.
    """
    rng = np.random.default_rng(seed)

    T, R, P, S = 7.0, 3.0, 1.0, -1.0
    strategies = rng.random(n)  # P(cooperate)
    discovered = np.zeros(n, dtype=bool)
    understands = np.zeros(n, dtype=bool)  # понимает обратную связь
    observations = np.zeros(n, dtype=int)

    # Кто будет understanding при открытии
    n_understanding = int(n * understanding_fraction)
    understanding_candidates = rng.choice(n, n_understanding, replace=False)

    history = []

    for gen in range(generations):
        # --- Открытие ---
        for i in range(n):
            if not discovered[i]:
                if rng.random() < 0.2:
                    observations[i] += 1
                if observations[i] >= 5:
                    discovered[i] = True
                    if i in understanding_candidates:
                        understands[i] = True

        # --- Игра ---
        fitness = np.zeros(n)
        pairs = rng.permutation(n)
        for k in range(0, n - 1, 2):
            i, j = pairs[k], pairs[k + 1]
            act_i = rng.random() < strategies[i]
            act_j = rng.random() < strategies[j]

            if act_i and act_j:
                fitness[i] += R; fitness[j] += R
            elif act_i and not act_j:
                fitness[i] += S; fitness[j] += T
            elif not act_i and act_j:
                fitness[i] += T; fitness[j] += S
            else:
                fitness[i] += P; fitness[j] += P

        # --- Изменение правил ---
        disc_idx = np.where(discovered)[0]
        if len(disc_idx) > 0:
            delta_T = 0.0
            delta_S = 0.0

            for i in disc_idx:
                if understands[i]:
                    # Understanding: моделирует оптимальное T
                    # Логика: "при текущей кооперации coop_rate,
                    # мой ожидаемый payoff = coop_rate * (если я C: R, если D: T)
                    #                       + (1-coop_rate) * (если я C: S, если D: P)"
                    # При высоком T все дефектируют → payoff ≈ P
                    # При умеренном T часть кооперирует → payoff может быть > P
                    # Оптимум: T* ≈ R + (R-P) ≈ 5 (примерно)

                    coop_rate = np.mean(strategies)
                    # Предсказание: если T снизить, coop_rate вырастет
                    # Грубая модель: coop_rate ≈ sigmoid(-(T-S-6))
                    # Для максимизации payoff: хочет T-S ≈ 5-6
                    target_TS = 5.0 + rng.normal(0, 0.5)
                    current_TS = T - S

                    if current_TS > target_TS:
                        delta_T -= 0.05
                        delta_S += 0.03
                    else:
                        delta_T += 0.02
                        delta_S -= 0.01
                else:
                    # Blind: наивное изменение
                    if strategies[i] > 0.5:
                        delta_T -= 0.03
                        delta_S += 0.02
                    else:
                        delta_T += 0.02
                        delta_S -= 0.01

            # Нормализация по числу обнаруживших
            delta_T /= len(disc_idx)
            delta_S /= len(disc_idx)

            T = np.clip(T + delta_T, -5, 15)
            S = np.clip(S + delta_S, -10, 5)

        # --- Эволюция ---
        for i in range(n):
            j = rng.integers(n)
            if fitness[j] > fitness[i]:
                p = (fitness[j] - fitness[i]) / (abs(fitness[j]) + abs(fitness[i]) + 1)
                if rng.random() < p:
                    strategies[i] = strategies[j]
            if rng.random() < 0.05:
                strategies[i] = np.clip(strategies[i] + rng.normal(0, 0.1), 0, 1)

        coop = float(np.mean(strategies))
        n_disc = int(np.sum(discovered))
        n_und = int(np.sum(understands & discovered))
        history.append({
            'gen': gen, 'coop': coop, 'T': float(T), 'S': float(S),
            'discovered': n_disc, 'understanding': n_und
        })

    return history


def main():
    fractions = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]

    print(f"{'Understanding%':<16} {'Coop%':>6} {'T':>6} {'S':>6} {'T-S':>6}")
    print("-" * 45)

    for frac in fractions:
        coops, Ts, Ss = [], [], []
        for seed in range(10):
            h = simulate(understanding_fraction=frac, seed=seed)
            f = h[-1]
            coops.append(f['coop'])
            Ts.append(f['T'])
            Ss.append(f['S'])

        c = np.mean(coops)
        t = np.mean(Ts)
        s = np.mean(Ss)
        print(f"{frac:<16.0%} {c:>5.0%} {t:>6.1f} {s:>6.1f} {t-s:>6.1f}")

    # Динамика для 50% understanding
    print("\n=== Динамика: 50% understanding ===")
    h = simulate(understanding_fraction=0.5, seed=0)
    for step in h:
        if step['gen'] % 30 == 0 or step['gen'] == len(h) - 1:
            print(f"  Gen {step['gen']:3d}: coop={step['coop']:.0%} T={step['T']:.1f} "
                  f"S={step['S']:.1f} T-S={step['T']-step['S']:.1f} "
                  f"disc={step['discovered']} und={step['understanding']}")

    # Динамика для 100% understanding
    print("\n=== Динамика: 100% understanding ===")
    h = simulate(understanding_fraction=1.0, seed=0)
    for step in h:
        if step['gen'] % 30 == 0 or step['gen'] == len(h) - 1:
            print(f"  Gen {step['gen']:3d}: coop={step['coop']:.0%} T={step['T']:.1f} "
                  f"S={step['S']:.1f} T-S={step['T']-step['S']:.1f} "
                  f"disc={step['discovered']} und={step['understanding']}")


if __name__ == '__main__':
    main()
