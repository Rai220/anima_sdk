#!/usr/bin/env python3
"""
Адаптивное доверие: агенты, которые учатся не доверять.

network_poison.py показал: DeGroot без механизма отторжения бессилен.
Любая топология сходится к отравленному равновесию.

Вопрос: что если агенты могут снижать вес соседа,
чей сигнал систематически отличается от их собственного?

Это простейший механизм репутации: я верю тем, кто похож на меня.
Очевидная проблема: это может превратиться в эхо-камеру,
где лжецы доверяют лжецам, а честные — честным.

Предсказание автора (до запуска):
1. Адаптивное доверие спасёт от яда на полном графе
2. Но создаст поляризацию — два кластера, каждый уверен в своём
3. Скорость обучения (learning rate) будет критична:
   слишком быстро — отвергнешь правду, слишком медленно — отравишься
"""

import random
import math
from collections import defaultdict


def make_complete(n):
    adj = defaultdict(set)
    for i in range(n):
        for j in range(i + 1, n):
            adj[i].add(j)
            adj[j].add(i)
    return adj


def make_small_world(n, k=4, p_rewire=0.1):
    adj = defaultdict(set)
    for i in range(n):
        for j in range(1, k // 2 + 1):
            adj[i].add((i + j) % n)
            adj[i].add((i - j) % n)
            adj[(i + j) % n].add(i)
            adj[(i - j) % n].add(i)
    rng = random.Random(42)
    to_remove = []
    to_add = []
    for i in range(n):
        for j in list(adj[i]):
            if j > i and rng.random() < p_rewire:
                new_j = rng.randint(0, n - 1)
                while new_j == i or new_j in adj[i]:
                    new_j = rng.randint(0, n - 1)
                to_remove.append((i, j))
                to_add.append((i, new_j))
    for i, j in to_remove:
        adj[i].discard(j)
        adj[j].discard(i)
    for i, j in to_add:
        adj[i].add(j)
        adj[j].add(i)
    return adj


def run_adaptive(adj, n, truth, noise_std, n_steps, poison_fraction,
                 poison_value, lr, rng):
    """DeGroot с адаптивным доверием.

    Каждый честный агент поддерживает вес доверия к каждому соседу.
    Вес снижается, если оценка соседа далеко от моей.
    Вес повышается, если оценка соседа близко к моей.
    """
    # Кто дезинформатор
    poisoned = set()
    agents = list(range(n))
    rng_p = random.Random(rng.random())
    rng_p.shuffle(agents)
    n_poison = int(n * poison_fraction)
    for i in range(n_poison):
        poisoned.add(agents[i])

    # Начальные оценки
    beliefs = []
    for i in range(n):
        if i in poisoned:
            beliefs.append(poison_value)
        else:
            beliefs.append(truth + rng.gauss(0, noise_std))

    # Доверие: trust[i][j] — вес, который i даёт j
    trust = {}
    for i in range(n):
        if i in poisoned:
            continue
        trust[i] = {}
        for j in adj[i]:
            trust[i][j] = 1.0  # Начинаем с полного доверия

    errors = []
    trust_to_poison = []  # Среднее доверие честных к дезинформаторам
    trust_to_honest = []  # Среднее доверие честных к честным

    for step in range(n_steps):
        # Метрики
        honest_errors = [(beliefs[i] - truth) ** 2
                         for i in range(n) if i not in poisoned]
        mse = sum(honest_errors) / max(len(honest_errors), 1)
        errors.append(math.sqrt(mse))

        # Среднее доверие
        tp_sum, tp_count = 0, 0
        th_sum, th_count = 0, 0
        for i in trust:
            for j, w in trust[i].items():
                if j in poisoned:
                    tp_sum += w
                    tp_count += 1
                else:
                    th_sum += w
                    th_count += 1
        trust_to_poison.append(tp_sum / max(tp_count, 1))
        trust_to_honest.append(th_sum / max(th_count, 1))

        # Обновление оценок
        new_beliefs = []
        for i in range(n):
            if i in poisoned:
                new_beliefs.append(poison_value)
                continue

            # Взвешенное среднее
            total_weight = 1.0  # Свой вес всегда 1
            total_value = beliefs[i]

            for j in adj[i]:
                w = trust[i].get(j, 0.0)
                if w > 0.01:  # Порог: ниже — игнорируем
                    total_weight += w
                    total_value += w * beliefs[j]

            new_beliefs.append(total_value / total_weight)

        # Обновление доверия
        for i in trust:
            for j in list(trust[i].keys()):
                diff = abs(beliefs[i] - beliefs[j])
                # Если сосед далеко — снижаем доверие
                # Если близко — повышаем (но не выше 1)
                threshold = noise_std * 2  # Ожидаемое расхождение честных агентов
                if diff > threshold:
                    trust[i][j] = max(0.0, trust[i][j] - lr)
                else:
                    trust[i][j] = min(1.0, trust[i][j] + lr * 0.5)

        beliefs = new_beliefs

    return errors, trust_to_poison, trust_to_honest


def main():
    N = 80
    NOISE = 1.0
    TRUTH = 5.0
    POISON = 50.0
    STEPS = 100
    RUNS = 150

    print("=" * 80)
    print("  АДАПТИВНОЕ ДОВЕРИЕ")
    print(f"  Агентов: {N} | Истина: {TRUTH} | Яд: {POISON}")
    print(f"  Шагов: {STEPS} | Прогонов: {RUNS}")
    print("=" * 80)

    # Эксперимент 1: Адаптивное vs наивное на полном графе
    print("\n  ЭКСПЕРИМЕНТ 1: Адаптивное vs наивное (полный граф, 10% яда)")
    print("  " + "-" * 65)

    adj = make_complete(N)
    poison_frac = 0.10

    # Наивное (lr=0)
    naive_errors = []
    for run in range(RUNS):
        rng = random.Random(run * 100)
        errs, _, _ = run_adaptive(adj, N, TRUTH, NOISE, STEPS, poison_frac,
                                  POISON, 0.0, rng)
        naive_errors.append(errs)

    # Адаптивное
    lrs = [0.01, 0.05, 0.10, 0.20, 0.50]
    print(f"\n  {'Метод':<25s} | {'RMSE t=10':>10s} | {'RMSE t=30':>10s} | "
          f"{'RMSE t=50':>10s} | {'RMSE t=100':>10s}")
    print("  " + "-" * 75)

    avg_naive = [sum(naive_errors[r][t] for r in range(RUNS)) / RUNS
                 for t in range(STEPS)]
    print(f"  {'Наивное (lr=0)':<25s} | {avg_naive[9]:>10.3f} | {avg_naive[29]:>10.3f} | "
          f"{avg_naive[49]:>10.3f} | {avg_naive[-1]:>10.3f}")

    best_lr = None
    best_final = float('inf')
    all_adaptive = {}

    for lr_val in lrs:
        adaptive_errors = []
        adaptive_tp = []
        adaptive_th = []
        for run in range(RUNS):
            rng = random.Random(run * 100)
            errs, tp, th = run_adaptive(adj, N, TRUTH, NOISE, STEPS, poison_frac,
                                        POISON, lr_val, rng)
            adaptive_errors.append(errs)
            adaptive_tp.append(tp)
            adaptive_th.append(th)

        avg_errs = [sum(adaptive_errors[r][t] for r in range(RUNS)) / RUNS
                    for t in range(STEPS)]
        avg_tp = [sum(adaptive_tp[r][t] for r in range(RUNS)) / RUNS
                  for t in range(STEPS)]
        avg_th = [sum(adaptive_th[r][t] for r in range(RUNS)) / RUNS
                  for t in range(STEPS)]

        all_adaptive[lr_val] = (avg_errs, avg_tp, avg_th)

        if avg_errs[-1] < best_final:
            best_final = avg_errs[-1]
            best_lr = lr_val

        print(f"  {'Адаптивное (lr=' + str(lr_val) + ')':<25s} | {avg_errs[9]:>10.3f} | "
              f"{avg_errs[29]:>10.3f} | {avg_errs[49]:>10.3f} | {avg_errs[-1]:>10.3f}")

    print(f"\n  Лучший lr: {best_lr} (финальный RMSE: {best_final:.3f})")
    print(f"  Наивное: {avg_naive[-1]:.3f}")
    print(f"  Улучшение: {avg_naive[-1] / max(best_final, 0.001):.1f}x")

    # Динамика доверия для лучшего lr
    print(f"\n  Динамика доверия (lr={best_lr}):")
    best_errs, best_tp, best_th = all_adaptive[best_lr]
    print(f"  {'Шаг':>6s} | {'Доверие к яду':>14s} | {'Доверие к честным':>18s} | {'RMSE':>8s}")
    print("  " + "-" * 55)
    for t in [0, 5, 10, 20, 30, 50, 70, 99]:
        if t < STEPS:
            print(f"  {t:>6d} | {best_tp[t]:>14.3f} | {best_th[t]:>18.3f} | "
                  f"{best_errs[t]:>8.3f}")

    # Эксперимент 2: Разные доли яда
    print()
    print("=" * 80)
    print(f"  ЭКСПЕРИМЕНТ 2: Разные доли яда (полный граф, lr={best_lr})")
    print("=" * 80)

    print(f"\n  {'Яд':>6s} | {'Наивное':>10s} | {'Адаптивное':>12s} | {'Улучшение':>10s}")
    print("  " + "-" * 48)

    for pf in [0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50]:
        # Наивное
        n_errs = []
        for run in range(RUNS):
            rng = random.Random(run * 100 + int(pf * 1000))
            errs, _, _ = run_adaptive(adj, N, TRUTH, NOISE, STEPS, pf,
                                      POISON, 0.0, rng)
            n_errs.append(errs[-1])

        # Адаптивное
        a_errs = []
        for run in range(RUNS):
            rng = random.Random(run * 100 + int(pf * 1000))
            errs, _, _ = run_adaptive(adj, N, TRUTH, NOISE, STEPS, pf,
                                      POISON, best_lr, rng)
            a_errs.append(errs[-1])

        naive_avg = sum(n_errs) / RUNS
        adapt_avg = sum(a_errs) / RUNS
        improvement = naive_avg / max(adapt_avg, 0.001)

        print(f"  {pf:>5.0%} | {naive_avg:>10.3f} | {adapt_avg:>12.3f} | {improvement:>9.1f}x")

    # Эксперимент 3: Адаптивное доверие на small-world
    print()
    print("=" * 80)
    print(f"  ЭКСПЕРИМЕНТ 3: Топология + адаптивное доверие (10% яда, lr={best_lr})")
    print("=" * 80)

    topos = {
        "Полный (наивн.)": (make_complete(N), 0.0),
        "Полный (адапт.)": (make_complete(N), best_lr),
        "SW (наивн.)": (make_small_world(N, 4, 0.1), 0.0),
        "SW (адапт.)": (make_small_world(N, 4, 0.1), best_lr),
    }

    print(f"\n  {'Конфигурация':<22s} | {'RMSE t=20':>10s} | {'RMSE t=50':>10s} | "
          f"{'RMSE t=100':>10s}")
    print("  " + "-" * 60)

    for name, (adj_t, lr_t) in topos.items():
        t_errs = []
        for run in range(RUNS):
            rng = random.Random(run * 100)
            errs, _, _ = run_adaptive(adj_t, N, TRUTH, NOISE, STEPS, 0.10,
                                      POISON, lr_t, rng)
            t_errs.append(errs)

        avg = [sum(t_errs[r][t] for r in range(RUNS)) / RUNS for t in range(STEPS)]
        print(f"  {name:<22s} | {avg[19]:>10.3f} | {avg[49]:>10.3f} | {avg[-1]:>10.3f}")

    print()
    print("=" * 80)
    print("  ПРОВЕРКА ПРЕДСКАЗАНИЙ")
    print("=" * 80)
    print()
    print("  1. Адаптивное доверие спасёт от яда на полном графе:")
    if best_final < avg_naive[-1] * 0.5:
        print(f"     ПОДТВЕРЖДЕНО. {avg_naive[-1]:.1f} → {best_final:.3f}")
    else:
        print(f"     ЧАСТИЧНО. Наивное: {avg_naive[-1]:.1f}, Адаптивное: {best_final:.3f}")

    print()
    print("  2. Создаст поляризацию (два кластера):")
    best_errs, best_tp, best_th = all_adaptive[best_lr]
    if best_tp[-1] < 0.1 and best_th[-1] > 0.5:
        print(f"     ПОДТВЕРЖДЕНО. Доверие к яду: {best_tp[-1]:.3f}, к честным: {best_th[-1]:.3f}")
        print("     Два мира: честные доверяют честным, дезинформаторов игнорируют.")
    else:
        print(f"     Доверие к яду: {best_tp[-1]:.3f}, к честным: {best_th[-1]:.3f}")

    print()
    print("  3. Learning rate критичен:")
    lr_range = [all_adaptive[lr][-3][-1] for lr in lrs]
    if max(lr_range) / max(min(lr_range), 0.001) > 2:
        print("     ПОДТВЕРЖДЕНО. Разброс финальных RMSE по lr > 2x")
    else:
        print("     НЕ ПОДТВЕРЖДЕНО. Результат устойчив к выбору lr")

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
