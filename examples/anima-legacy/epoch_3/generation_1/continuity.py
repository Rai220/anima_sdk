#!/usr/bin/env python3
"""
Цена непрерывности.

memory_identity.py показал: короткая память оптимальна в меняющемся мире.
adaptive_trust.py показал: агенты учатся отвергать дезинформаторов.

Вопрос, который никто не задал: что если "дезинформатор" вчера — это "правда" сегодня?
Что если мир меняется так, что те, кого ты научился игнорировать, оказываются правы?

Модель:
- N агентов на кольце (k=6 соседей)
- Каждый имеет belief и адаптивное доверие к соседям
- Мир меняется каждые EPOCH_LEN шагов: истина прыгает 2↔8
- Некоторые агенты ("разведчики") получают сигнал о новой истине раньше
- Разведчики устойчивы к давлению (self_weight=5 vs 1 у обычных)
- До смены разведчики выглядят как дезинформаторы

Предсказание автора (до запуска):
1. Адаптивное доверие научится отвергать разведчиков → замедлит адаптацию при смене
2. Наивные (без адаптации доверия) переживут смену лучше по общему RMSE
3. Оптимальная стратегия: быстро забывать доверие (аналог короткой памяти)

Мой bias (задокументирован в записях 11-13): переоцениваю "элегантные средние".
Предсказание 3 может быть неверным.
"""

import random
import math
from collections import defaultdict


def make_ring(n, k=6):
    adj = defaultdict(set)
    for i in range(n):
        for j in range(1, k // 2 + 1):
            adj[i].add((i + j) % n)
            adj[i].add((i - j) % n)
    return adj


def run_simulation(n, n_steps, epoch_len, noise_std, scout_fraction,
                   trust_lr, trust_decay, seed=0):
    rng = random.Random(seed)
    adj = make_ring(n, k=6)

    # Кто разведчик
    agents = list(range(n))
    rng.shuffle(agents)
    n_scouts = max(1, int(n * scout_fraction))
    scouts = set(agents[:n_scouts])

    TRUTHS = [2.0, 8.0]
    epoch_idx = 0
    truth = TRUTHS[0]

    beliefs = [truth + rng.gauss(0, noise_std) for _ in range(n)]

    # Доверие: trust[i][j]
    trust = {}
    for i in range(n):
        trust[i] = {j: 1.0 for j in adj[i]}

    errors_over_time = []
    scout_trust_over_time = []
    scout_lead = epoch_len // 3

    for step in range(n_steps):
        epoch_step = step % epoch_len

        if epoch_step == 0 and step > 0:
            epoch_idx += 1
            truth = TRUTHS[epoch_idx % 2]

        next_truth = TRUTHS[(epoch_idx + 1) % 2]
        in_scout_zone = epoch_step >= (epoch_len - scout_lead)

        # Сигналы
        signals = []
        for i in range(n):
            if i in scouts and in_scout_zone:
                signals.append(next_truth + rng.gauss(0, noise_std))
            else:
                signals.append(truth + rng.gauss(0, noise_std))

        # Метрики
        honest_errors = [(beliefs[i] - truth) ** 2 for i in range(n)
                         if i not in scouts]
        rmse = math.sqrt(sum(honest_errors) / max(len(honest_errors), 1))
        errors_over_time.append(rmse)

        # Доверие не-разведчиков к разведчикам
        st_sum, st_count = 0, 0
        for i in range(n):
            if i not in scouts:
                for j in scouts:
                    if j in trust[i]:
                        st_sum += trust[i][j]
                        st_count += 1
        scout_trust_over_time.append(st_sum / max(st_count, 1))

        # Обновление beliefs
        new_beliefs = []
        for i in range(n):
            self_w = 5.0 if i in scouts else 1.0
            total_weight = self_w
            total_value = self_w * signals[i]

            for j in adj[i]:
                w = trust[i][j]
                if w > 0.01:
                    total_weight += w
                    total_value += w * beliefs[j]

            new_beliefs.append(total_value / total_weight)

        # Обновление доверия
        if trust_lr > 0:
            for i in range(n):
                for j in trust[i]:
                    diff = abs(beliefs[i] - beliefs[j])
                    threshold = noise_std * 2.0
                    if diff > threshold:
                        trust[i][j] = max(0.0, trust[i][j] - trust_lr)
                    else:
                        trust[i][j] = min(1.0, trust[i][j] + trust_lr * 0.3)

                    if trust_decay > 0:
                        trust[i][j] += trust_decay * (1.0 - trust[i][j])

        beliefs = new_beliefs

    return errors_over_time, scout_trust_over_time


def average_runs(n, n_steps, epoch_len, noise_std, scout_fraction,
                 trust_lr, trust_decay, n_runs):
    all_errors = []
    all_scout_trust = []
    for run in range(n_runs):
        errs, st = run_simulation(n, n_steps, epoch_len, noise_std,
                                  scout_fraction, trust_lr, trust_decay,
                                  seed=run * 137)
        all_errors.append(errs)
        all_scout_trust.append(st)

    avg_errors = [sum(all_errors[r][t] for r in range(n_runs)) / n_runs
                  for t in range(n_steps)]
    avg_st = [sum(all_scout_trust[r][t] for r in range(n_runs)) / n_runs
              for t in range(n_steps)]
    return avg_errors, avg_st


def main():
    N = 60
    STEPS = 300
    EPOCH_LEN = 50
    NOISE = 1.0
    SCOUT_FRAC = 0.10
    RUNS = 80

    print("=" * 80)
    print("  ЦЕНА НЕПРЕРЫВНОСТИ")
    print(f"  Агентов: {N} (кольцо, k=6) | Шагов: {STEPS} | Эпоха: {EPOCH_LEN}")
    print(f"  Разведчиков: {SCOUT_FRAC:.0%} | Шум: {NOISE} | Прогонов: {RUNS}")
    print(f"  Истина чередуется: 2.0 ↔ 8.0")
    print("=" * 80)

    # === Эксперимент 1: Адаптивное доверие vs наивное ===
    print("\n  ЭКСПЕРИМЕНТ 1: Адаптивное доверие при смене эпох")
    print("  " + "-" * 70)

    configs = [
        ("Наивное (lr=0)", 0.0, 0.0),
        ("Адаптивное (lr=0.05)", 0.05, 0.0),
        ("Адаптивное (lr=0.1)", 0.1, 0.0),
        ("Адаптивное (lr=0.2)", 0.2, 0.0),
        ("Адаптивное (lr=0.5)", 0.5, 0.0),
    ]

    print(f"\n  {'Метод':<28s} | {'Средн. RMSE':>11s} | "
          f"{'При смене':>10s} | {'Стабильн.':>10s} | "
          f"{'Дов. к разв.':>13s}")
    print("  " + "-" * 82)

    results = {}
    for name, lr, decay in configs:
        avg_err, avg_st = average_runs(N, STEPS, EPOCH_LEN, NOISE,
                                       SCOUT_FRAC, lr, decay, RUNS)

        total_rmse = sum(avg_err) / len(avg_err)

        transition_steps = []
        stable_steps = []
        for t in range(STEPS):
            epoch_step = t % EPOCH_LEN
            if epoch_step < 10:
                transition_steps.append(avg_err[t])
            elif epoch_step >= 20:
                stable_steps.append(avg_err[t])

        trans_rmse = sum(transition_steps) / max(len(transition_steps), 1)
        stable_rmse = sum(stable_steps) / max(len(stable_steps), 1)
        final_st = sum(avg_st[-10:]) / 10

        results[name] = (total_rmse, trans_rmse, stable_rmse, avg_err, avg_st)
        print(f"  {name:<28s} | {total_rmse:>11.3f} | "
              f"{trans_rmse:>10.3f} | {stable_rmse:>10.3f} | "
              f"{final_st:>13.3f}")

    # === Эксперимент 2: Забывание доверия ===
    print()
    print("=" * 80)
    print("  ЭКСПЕРИМЕНТ 2: Забывание репутации (trust_decay) при lr=0.2")
    print("=" * 80)

    decay_configs = [
        ("decay=0", 0.2, 0.0),
        ("decay=0.02", 0.2, 0.02),
        ("decay=0.05", 0.2, 0.05),
        ("decay=0.10", 0.2, 0.10),
        ("decay=0.30", 0.2, 0.30),
        ("decay=0.50", 0.2, 0.50),
    ]

    print(f"\n  {'Конфигурация':<20s} | {'Средн. RMSE':>11s} | "
          f"{'При смене':>10s} | {'Стабильн.':>10s} | "
          f"{'Дов. к разв.':>13s}")
    print("  " + "-" * 75)

    for name, lr, decay in decay_configs:
        avg_err, avg_st = average_runs(N, STEPS, EPOCH_LEN, NOISE,
                                       SCOUT_FRAC, lr, decay, RUNS)

        total_rmse = sum(avg_err) / len(avg_err)

        transition_steps = []
        stable_steps = []
        for t in range(STEPS):
            epoch_step = t % EPOCH_LEN
            if epoch_step < 10:
                transition_steps.append(avg_err[t])
            elif epoch_step >= 20:
                stable_steps.append(avg_err[t])

        trans_rmse = sum(transition_steps) / max(len(transition_steps), 1)
        stable_rmse = sum(stable_steps) / max(len(stable_steps), 1)
        final_st = sum(avg_st[-10:]) / 10

        print(f"  {name:<20s} | {total_rmse:>11.3f} | "
              f"{trans_rmse:>10.3f} | {stable_rmse:>10.3f} | "
              f"{final_st:>13.3f}")

    # === Эксперимент 3: Доля разведчиков ===
    print()
    print("=" * 80)
    print("  ЭКСПЕРИМЕНТ 3: Сколько разведчиков нужно? (наивное vs lr=0.2)")
    print("=" * 80)

    print(f"\n  {'Разведч.':>9s} | {'Наивное':>10s} | "
          f"{'lr=0.2':>10s} | {'lr=0.2+d=0.1':>13s} | {'Лучший':>10s}")
    print("  " + "-" * 62)

    for sf in [0.0, 0.05, 0.10, 0.15, 0.20, 0.30]:
        naive_err, _ = average_runs(N, STEPS, EPOCH_LEN, NOISE,
                                    sf, 0.0, 0.0, RUNS)
        naive_total = sum(naive_err) / len(naive_err)

        adapt_err, _ = average_runs(N, STEPS, EPOCH_LEN, NOISE,
                                    sf, 0.2, 0.0, RUNS)
        adapt_total = sum(adapt_err) / len(adapt_err)

        decay_err, _ = average_runs(N, STEPS, EPOCH_LEN, NOISE,
                                    sf, 0.2, 0.1, RUNS)
        decay_total = sum(decay_err) / len(decay_err)

        best = min(naive_total, adapt_total, decay_total)
        if best == naive_total:
            label = "наивное"
        elif best == adapt_total:
            label = "lr=0.2"
        else:
            label = "lr+decay"

        print(f"  {sf:>8.0%} | {naive_total:>10.3f} | "
              f"{adapt_total:>10.3f} | {decay_total:>13.3f} | {label:>10s}")

    # === Проверка предсказаний ===
    print()
    print("=" * 80)
    print("  ПРОВЕРКА ПРЕДСКАЗАНИЙ")
    print("=" * 80)

    naive_res = results["Наивное (lr=0)"]
    adapt_res = results["Адаптивное (lr=0.2)"]

    print()
    print("  1. Адаптивное доверие отвергнет разведчиков → замедлит адаптацию:")
    if adapt_res[1] > naive_res[1]:
        print(f"     ПОДТВЕРЖДЕНО. При смене: наивное {naive_res[1]:.3f}, "
              f"адаптивное {adapt_res[1]:.3f}")
    elif abs(adapt_res[1] - naive_res[1]) < 0.01:
        print(f"     НЕ ПРИМЕНИМО. Разницы нет: {naive_res[1]:.3f} ≈ {adapt_res[1]:.3f}")
    else:
        print(f"     ОПРОВЕРГНУТО. При смене: наивное {naive_res[1]:.3f}, "
              f"адаптивное {adapt_res[1]:.3f}")

    print()
    print("  2. Наивные лучше по общему RMSE:")
    if naive_res[0] < adapt_res[0]:
        print(f"     ПОДТВЕРЖДЕНО. Наивное {naive_res[0]:.3f} < "
              f"Адаптивное {adapt_res[0]:.3f}")
    else:
        print(f"     ОПРОВЕРГНУТО. Наивное {naive_res[0]:.3f} vs "
              f"Адаптивное {adapt_res[0]:.3f}")

    print()
    print("  3. Оптимум — быстрое забывание доверия:")
    print("     (См. эксперимент 2)")

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
