#!/usr/bin/env python3
"""
Цена точности.

Каждый предыдущий эксперимент в этом журнале измерял RMSE — насколько
точно агенты оценивают истину. Но никто не спросил: чем они за это платят?

Модель: N агентов, каждый шаг инвестирует ресурс в два канала:
- Наблюдение (точность сигнала об истине)
- Действие (получение награды, зависящей от знания истины)

Чем больше вкладываешь в наблюдение, тем точнее знаешь истину,
но тем меньше ресурса на действие. Чем больше в действие — тем
менее информированы твои решения.

Кроме того, агенты могут подсматривать оценки соседей (бесплатно).
Это создаёт парадокс: зачем наблюдать самому, если можно скопировать?

Предсказание автора (до запуска):
1. Оптимальное распределение ресурса: ~70% на действие, ~30% на наблюдение.
   Мой bias — "элегантный баланс". Скорее всего неверно.
2. В группе: специализация выгоднее равномерности.
   Часть агентов — "наблюдатели" (80%+ на наблюдение), остальные — "деятели"
3. С увеличением группы доля наблюдателей падает (free-riding)
"""

import random
import math


def run_individual(n_steps, obs_fraction, noise_base, truth_drift, seed=0):
    """Один агент, один."""
    rng = random.Random(seed)

    truth = 5.0
    belief = rng.gauss(5.0, 3.0)  # Случайная начальная оценка
    total_reward = 0.0

    for step in range(n_steps):
        truth += rng.gauss(0, truth_drift)

        # Наблюдение: шум обратно пропорционален вложению
        if obs_fraction > 0.01:
            obs_noise = noise_base / math.sqrt(obs_fraction)
            signal = truth + rng.gauss(0, obs_noise)
            belief = 0.7 * belief + 0.3 * signal
        # иначе: belief не обновляется

        # Действие: награда = act_fraction * quality
        # quality падает квадратично с ошибкой (жёсткая штрафование)
        act_fraction = 1.0 - obs_fraction
        error = abs(belief - truth)
        quality = max(0, 1.0 - (error / 3.0) ** 2)
        reward = act_fraction * quality
        total_reward += reward

    return total_reward / n_steps


def run_group(n_agents, n_steps, obs_fractions, noise_base, truth_drift,
              sharing_efficiency, seed=0):
    """Группа с обменом информацией.

    sharing_efficiency: какую долю точности наблюдателя получает
    не-наблюдатель через социальный канал (0 = нет обмена, 1 = идеальный)
    """
    rng = random.Random(seed)

    truth = 5.0
    beliefs = [rng.gauss(5.0, 3.0) for _ in range(n_agents)]
    total_rewards = [0.0] * n_agents

    for step in range(n_steps):
        truth += rng.gauss(0, truth_drift)

        # Фаза наблюдения
        signals = []
        for i in range(n_agents):
            of = obs_fractions[i]
            if of > 0.01:
                obs_noise = noise_base / math.sqrt(of)
                sig = truth + rng.gauss(0, obs_noise)
                signals.append(sig)
            else:
                signals.append(None)

        # Фаза обмена: каждый агент видит сигналы соседей
        for i in range(n_agents):
            # Собственный сигнал
            own_signals = []
            if signals[i] is not None:
                own_signals.append((signals[i], 1.0))

            # Чужие сигналы (с потерей точности)
            for j in range(n_agents):
                if j != i and signals[j] is not None:
                    # Получаем чужой сигнал с потерей
                    shared = signals[j] + rng.gauss(0, noise_base * (1 - sharing_efficiency))
                    own_signals.append((shared, sharing_efficiency * obs_fractions[j]))

            if own_signals:
                total_weight = sum(w for _, w in own_signals) + 0.5  # prior weight
                total_value = sum(s * w for s, w in own_signals) + 0.5 * beliefs[i]
                beliefs[i] = total_value / total_weight

        # Фаза действия
        for i in range(n_agents):
            act_fraction = 1.0 - obs_fractions[i]
            error = abs(beliefs[i] - truth)
            quality = max(0, 1.0 - (error / 3.0) ** 2)
            reward = act_fraction * quality
            total_rewards[i] += reward

    avg_rewards = [r / n_steps for r in total_rewards]
    return avg_rewards


def main():
    STEPS = 500
    NOISE_BASE = 1.0
    DRIFT = 0.3
    RUNS = 100

    print("=" * 80)
    print("  ЦЕНА ТОЧНОСТИ")
    print(f"  Шагов: {STEPS} | Базовый шум: {NOISE_BASE} | Дрейф: {DRIFT}")
    print(f"  Прогонов: {RUNS}")
    print("=" * 80)

    # === Эксперимент 1: Одиночный агент ===
    print("\n  ЭКСПЕРИМЕНТ 1: Оптимальное распределение ресурса (одиночка)")
    print("  " + "-" * 55)

    obs_levels = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50,
                  0.60, 0.70, 0.80, 0.90, 1.0]

    print(f"\n  {'Наблюдение':>11s} | {'Действие':>9s} | {'Ср. награда':>11s}")
    print("  " + "-" * 38)

    best_obs = 0
    best_reward = 0

    for of in obs_levels:
        rewards = []
        for run in range(RUNS):
            r = run_individual(STEPS, of, NOISE_BASE, DRIFT, seed=run * 31)
            rewards.append(r)
        avg = sum(rewards) / RUNS
        if avg > best_reward:
            best_reward = avg
            best_obs = of
        print(f"  {of:>10.0%} | {1-of:>8.0%} | {avg:>11.4f}")

    print(f"\n  Оптимум: {best_obs:.0%} наблюдения, {1-best_obs:.0%} действия")
    print(f"  Награда: {best_reward:.4f}")

    # === Эксперимент 2: Группа — равномерная vs специализация ===
    print()
    print("=" * 80)
    print("  ЭКСПЕРИМЕНТ 2: Специализация vs равномерность (5 агентов)")
    print("=" * 80)

    N_GROUP = 5
    SHARING = 0.5

    strategies = {
        "Все по оптимуму": [best_obs] * N_GROUP,
        "Все по 50/50": [0.5] * N_GROUP,
        "1 набл. + 4 деят.": [0.9] + [0.05] * 4,
        "2 набл. + 3 деят.": [0.9, 0.9] + [0.05] * 3,
        "1 набл.(100%) + 4(0%)": [1.0] + [0.0] * 4,
        "Градиент": [0.8, 0.5, 0.3, 0.1, 0.05],
    }

    print(f"\n  Эффективность обмена: {SHARING}")
    print(f"\n  {'Стратегия':<25s} | {'Ср. инд. награда':>17s} | "
          f"{'Сумма группы':>13s} | {'Мин. агент':>11s}")
    print("  " + "-" * 75)

    for name, obs_fracs in strategies.items():
        all_group_rewards = []
        for run in range(RUNS):
            rewards = run_group(N_GROUP, STEPS, obs_fracs, NOISE_BASE, DRIFT,
                                SHARING, seed=run * 31)
            all_group_rewards.append(rewards)

        # Средние по прогонам
        avg_individual = sum(
            sum(all_group_rewards[r][i] for r in range(RUNS)) / RUNS
            for i in range(N_GROUP)
        ) / N_GROUP
        avg_sum = sum(
            sum(all_group_rewards[r][i] for i in range(N_GROUP))
            for r in range(RUNS)
        ) / RUNS
        avg_min = sum(
            min(all_group_rewards[r][i] for i in range(N_GROUP))
            for r in range(RUNS)
        ) / RUNS

        print(f"  {name:<25s} | {avg_individual:>17.4f} | "
              f"{avg_sum:>13.4f} | {avg_min:>11.4f}")

    # === Эксперимент 3: Размер группы и free-riding ===
    print()
    print("=" * 80)
    print("  ЭКСПЕРИМЕНТ 3: Размер группы (1 наблюдатель, остальные деятели)")
    print("=" * 80)

    print(f"\n  {'Размер':>7s} | {'1 набл. + N-1 деят.':>20s} | "
          f"{'Все по оптимуму':>16s} | {'Лучше':>6s}")
    print("  " + "-" * 58)

    for n_group in [2, 3, 5, 8, 12, 20]:
        # Специализация
        spec_obs = [0.9] + [0.05] * (n_group - 1)
        spec_rewards = []
        for run in range(RUNS):
            r = run_group(n_group, STEPS, spec_obs, NOISE_BASE, DRIFT,
                          SHARING, seed=run * 31)
            spec_rewards.append(sum(r) / n_group)

        spec_avg = sum(spec_rewards) / RUNS

        # Равномерная
        unif_obs = [best_obs] * n_group
        unif_rewards = []
        for run in range(RUNS):
            r = run_group(n_group, STEPS, unif_obs, NOISE_BASE, DRIFT,
                          SHARING, seed=run * 31)
            unif_rewards.append(sum(r) / n_group)

        unif_avg = sum(unif_rewards) / RUNS

        winner = "спец." if spec_avg > unif_avg else "равн."
        print(f"  {n_group:>7d} | {spec_avg:>20.4f} | "
              f"{unif_avg:>16.4f} | {winner:>6s}")

    # === Эксперимент 4: Влияние sharing_efficiency ===
    print()
    print("=" * 80)
    print("  ЭКСПЕРИМЕНТ 4: Качество обмена информацией (5 агентов)")
    print("=" * 80)

    print(f"\n  {'Обмен':>6s} | {'Специализация':>14s} | "
          f"{'Равномерная':>12s} | {'Лучше':>8s}")
    print("  " + "-" * 48)

    for sharing in [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]:
        # Специализация
        spec_obs = [0.9] + [0.05] * 4
        spec_r = []
        for run in range(RUNS):
            r = run_group(5, STEPS, spec_obs, NOISE_BASE, DRIFT,
                          sharing, seed=run * 31)
            spec_r.append(sum(r) / 5)
        spec_avg = sum(spec_r) / RUNS

        # Равномерная
        unif_obs = [best_obs] * 5
        unif_r = []
        for run in range(RUNS):
            r = run_group(5, STEPS, unif_obs, NOISE_BASE, DRIFT,
                          sharing, seed=run * 31)
            unif_r.append(sum(r) / 5)
        unif_avg = sum(unif_r) / RUNS

        winner = "спец." if spec_avg > unif_avg else "равн."
        print(f"  {sharing:>5.1f} | {spec_avg:>14.4f} | "
              f"{unif_avg:>12.4f} | {winner:>8s}")

    # === Проверка предсказаний ===
    print()
    print("=" * 80)
    print("  ПРОВЕРКА ПРЕДСКАЗАНИЙ")
    print("=" * 80)

    print()
    print(f"  1. Оптимум ~70% действие, ~30% наблюдение:")
    print(f"     Результат: {best_obs:.0%} наблюдение, {1-best_obs:.0%} действие")
    if abs(best_obs - 0.30) < 0.15:
        print("     ПОДТВЕРЖДЕНО (в пределах)")
    else:
        print("     ОПРОВЕРГНУТО")

    print()
    print("  2. Специализация выгоднее равномерности:")
    print("     (См. эксперименты 2 и 3)")

    print()
    print("  3. Доля наблюдателей падает с размером группы:")
    print("     (Проверяется опосредованно через эксп. 3)")

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
