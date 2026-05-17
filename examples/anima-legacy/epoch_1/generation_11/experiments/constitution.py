"""
Эксперимент 5: Конституция vs Демократия

Три типа институтов:
1. Демократический — медиана голосов (gen10). Отражает текущих членов.
2. Конституционный — фиксированное правило: "T-S не может превышать X".
   Не зависит от голосов. Агент уровня 3 устанавливает ограничение.
3. Адаптивная конституция — ограничение обновляется на основе
   МОДЕЛИ оптимума (уровень 2 понимания), а не голосов.

Гипотеза: конституционный институт работает даже при поздней активации,
потому что его правило не зависит от текущего состава.

Также тестируем ВРЕМЯ создания: что если институт создаётся рано (gen 0, 10, 20)?
"""

import numpy as np


def simulate(
    n=100, generations=300, seed=42,
    institution_type='none',  # 'none', 'democratic', 'constitutional', 'adaptive_constitution'
    institution_start=0,      # поколение активации
    constitution_limit=6.0,   # максимум T-S для конституционного
):
    rng = np.random.default_rng(seed)
    T, R, P, S = 7.0, 3.0, 1.0, -1.0
    strategies = rng.random(n)

    history = []

    for gen in range(generations):
        institution_active = gen >= institution_start and institution_type != 'none'

        # --- Институциональное изменение правил ---
        if institution_active:
            if institution_type == 'democratic':
                # Медиана: кооператоры хотят низкий T, дефекторы — высокий
                proposals = []
                for s in strategies:
                    if s > 0.5:
                        proposals.append(T - 0.3)
                    else:
                        proposals.append(T + 0.1)
                T = float(np.median(proposals))
                T = np.clip(T, -5, 15)

            elif institution_type == 'constitutional':
                # Жёсткое ограничение: T-S ≤ limit
                if T - S > constitution_limit:
                    excess = (T - S) - constitution_limit
                    T -= excess * 0.5
                    S += excess * 0.5

            elif institution_type == 'adaptive_constitution':
                # Ограничение основано на модели оптимума
                coop_rate = np.mean(strategies)
                # Модель: оптимум T-S зависит от текущей кооперации
                # Больше кооперации → можно допустить чуть больше T-S
                # Меньше кооперации → нужно снижать T-S
                optimal_TS = 4.0 + coop_rate * 3.0  # от 4 (при 0% coop) до 7 (при 100%)
                current_TS = T - S
                if current_TS > optimal_TS:
                    excess = current_TS - optimal_TS
                    T -= excess * 0.3
                    S += excess * 0.2

        else:
            # Без института: слепое изменение (дефекторы доминируют)
            for s in strategies:
                if s > 0.5:
                    T -= 0.003
                    S += 0.002
                else:
                    T += 0.002
                    S -= 0.001
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

        coop = float(np.mean(strategies))
        history.append({
            'gen': gen, 'coop': coop, 'T': float(T), 'S': float(S),
            'TS': float(T - S), 'inst': institution_active,
        })

    return history


def main():
    # === Сравнение типов институтов ===
    print("=== Тип института (старт gen 0) ===\n")
    types = ['none', 'democratic', 'constitutional', 'adaptive_constitution']

    print(f"{'Type':<24} {'Coop':>5} {'T':>5} {'S':>5} {'T-S':>5}")
    print("-" * 48)

    for itype in types:
        coops, TSs = [], []
        for seed in range(20):
            h = simulate(institution_type=itype, institution_start=0, seed=seed)
            f = h[-1]
            coops.append(f['coop'])
            TSs.append(f['TS'])
        print(f"{itype:<24} {np.mean(coops):>4.0%} {np.mean([h[-1]['T'] for h in [simulate(institution_type=itype, seed=s) for s in range(5)]]):>5.1f} "
              f"{np.mean([simulate(institution_type=itype, seed=s)[-1]['S'] for s in range(5)]):>5.1f} "
              f"{np.mean(TSs):>5.1f}")

    # === Время создания ===
    print("\n=== Время создания института (adaptive_constitution) ===\n")
    starts = [0, 10, 25, 50, 100, 150]

    print(f"{'Start gen':<12} {'Coop':>5} {'T-S':>5}")
    print("-" * 25)

    for start in starts:
        coops = []
        for seed in range(20):
            h = simulate(institution_type='adaptive_constitution',
                         institution_start=start, seed=seed)
            coops.append(h[-1]['coop'])
        print(f"gen {start:<8d} {np.mean(coops):>4.0%} {h[-1]['TS']:>5.1f}")

    # === Динамика: adaptive_constitution, старт gen 50 ===
    print("\n=== Динамика: adaptive_constitution, старт gen 50 ===")
    h = simulate(institution_type='adaptive_constitution', institution_start=50, seed=0)
    for step in h:
        if step['gen'] % 25 == 0 or step['gen'] == len(h) - 1:
            tag = " <-- inst starts" if step['gen'] == 50 else ""
            print(f"  Gen {step['gen']:3d}: coop={step['coop']:.0%} T={step['T']:.1f} "
                  f"S={step['S']:.1f} T-S={step['TS']:.1f}{tag}")

    # === Динамика: democratic, старт gen 0 ===
    print("\n=== Динамика: democratic, старт gen 0 ===")
    h = simulate(institution_type='democratic', institution_start=0, seed=0)
    for step in h:
        if step['gen'] % 25 == 0 or step['gen'] == len(h) - 1:
            print(f"  Gen {step['gen']:3d}: coop={step['coop']:.0%} T={step['T']:.1f} "
                  f"S={step['S']:.1f} T-S={step['TS']:.1f}")


if __name__ == '__main__':
    main()
