#!/usr/bin/env python3
"""
Информационные каскады: когда рациональность каждого ведёт к глупости всех.

Модель: N агентов голосуют последовательно за вариант A или B.
Один из вариантов объективно лучше (скажем, A).
Каждый агент получает зашумлённый сигнал (верный с вероятностью p > 0.5).
Каждый видит голоса всех предыдущих.

Рациональный агент: если публичное свидетельство сильнее моего сигнала,
я игнорирую сигнал и голосую как большинство. → Каскад.
Упрямый агент: всегда следует своему сигналу.

Вопрос: при какой доле упрямых каскад ломается?
"""

import random
from dataclasses import dataclass


@dataclass
class SimResult:
    correct: bool           # группа выбрала правильно?
    cascade_started: int    # на каком шаге начался каскад (-1 если нет)
    cascade_correct: bool   # если каскад — в правильную сторону?
    votes_a: int
    votes_b: int
    n_stubborn: int
    n_rational: int


def run_single(n_agents: int, signal_quality: float, stubborn_fraction: float,
               seed: int | None = None) -> SimResult:
    """Один прогон: N агентов голосуют последовательно."""
    rng = random.Random(seed)

    # Правильный ответ всегда A
    correct_answer = "A"

    # Определяем, кто упрямый
    stubborn = set()
    for i in range(n_agents):
        if rng.random() < stubborn_fraction:
            stubborn.add(i)

    votes = []  # список "A" или "B"
    cascade_started = -1
    cascade_correct = False

    for i in range(n_agents):
        # Личный сигнал (верный с вероятностью signal_quality)
        if rng.random() < signal_quality:
            signal = correct_answer
        else:
            signal = "B"

        if i in stubborn:
            # Упрямый: всегда следует сигналу
            vote = signal
        else:
            # Рациональный: байесовское обновление
            # Считаем log-likelihood ratio на основе публичных голосов
            # Каждый голос "A" — свидетельство за A, "B" — за B
            # Но голоса в каскаде не несут новой информации!
            # Упрощение: считаем разницу голосов как силу свидетельства
            count_a = votes.count("A")
            count_b = votes.count("B")
            public_evidence = count_a - count_b  # >0 значит в пользу A

            # Сила личного сигнала в тех же единицах
            signal_strength = 1 if signal == "A" else -1

            total = public_evidence + signal_strength

            if total > 0:
                vote = "A"
            elif total < 0:
                vote = "B"
            else:
                # При равенстве — следуем сигналу
                vote = signal

        votes.append(vote)

        # Проверяем начало каскада: 3+ одинаковых голоса подряд
        if cascade_started == -1 and len(votes) >= 3:
            last_3 = votes[-3:]
            if len(set(last_3)) == 1:
                cascade_started = i - 2
                cascade_correct = last_3[0] == correct_answer

    votes_a = votes.count("A")
    votes_b = votes.count("B")
    majority_correct = votes_a > votes_b

    return SimResult(
        correct=majority_correct,
        cascade_started=cascade_started,
        cascade_correct=cascade_correct,
        votes_a=votes_a,
        votes_b=votes_b,
        n_stubborn=len(stubborn),
        n_rational=n_agents - len(stubborn),
    )


def run_experiment(n_agents: int, signal_quality: float, stubborn_fraction: float,
                   n_runs: int = 1000) -> dict:
    """Много прогонов, статистика."""
    results = [run_single(n_agents, signal_quality, stubborn_fraction, seed=i)
               for i in range(n_runs)]

    correct_count = sum(1 for r in results if r.correct)
    cascade_count = sum(1 for r in results if r.cascade_started >= 0)
    wrong_cascade = sum(1 for r in results
                        if r.cascade_started >= 0 and not r.cascade_correct)

    return {
        "accuracy": correct_count / n_runs,
        "cascade_rate": cascade_count / n_runs,
        "wrong_cascade_rate": wrong_cascade / n_runs,
        "avg_cascade_start": (
            sum(r.cascade_started for r in results if r.cascade_started >= 0) /
            max(cascade_count, 1)
        ),
    }


def main():
    N = 50
    SIGNAL = 0.65  # каждый агент прав с вероятностью 65%
    RUNS = 2000

    print("=" * 70)
    print("  ИНФОРМАЦИОННЫЕ КАСКАДЫ")
    print(f"  Агентов: {N} | Качество сигнала: {SIGNAL} | Прогонов: {RUNS}")
    print("=" * 70)

    # Теоретический оптимум: если все независимы, закон больших чисел
    # даёт почти 100% точность при N=50, p=0.65
    import math
    # P(majority correct) ≈ 1 - exp(-2*N*(p-0.5)^2) для больших N
    theoretical = 1 - math.exp(-2 * N * (SIGNAL - 0.5) ** 2)
    print(f"\n  Теоретический оптимум (независимые голоса): {theoretical:.1%}")
    print()

    fractions = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.70, 1.0]

    print(f"  {'Упрямые':>10s} | {'Точность':>10s} | {'Каскады':>10s} | "
          f"{'Ошиб.касд':>10s} | {'Нач.касд':>10s}")
    print("  " + "-" * 62)

    results_all = {}
    for frac in fractions:
        stats = run_experiment(N, SIGNAL, frac, RUNS)
        results_all[frac] = stats
        print(f"  {frac:>9.0%} | {stats['accuracy']:>9.1%} | "
              f"{stats['cascade_rate']:>9.1%} | {stats['wrong_cascade_rate']:>9.1%} | "
              f"{stats['avg_cascade_start']:>9.1f}")

    print()
    print("─" * 70)

    # Найдём оптимум
    best_frac = max(results_all, key=lambda f: results_all[f]["accuracy"])
    best_acc = results_all[best_frac]["accuracy"]
    worst_frac = min(results_all, key=lambda f: results_all[f]["accuracy"])
    worst_acc = results_all[worst_frac]["accuracy"]

    print(f"\n  Лучшая точность: {best_acc:.1%} при {best_frac:.0%} упрямых")
    print(f"  Худшая точность: {worst_acc:.1%} при {worst_frac:.0%} упрямых")

    # 0% упрямых vs 100% упрямых
    zero = results_all[0.0]["accuracy"]
    full = results_all[1.0]["accuracy"]
    print(f"\n  Все рациональные (0% упрямых): {zero:.1%}")
    print(f"  Все упрямые (100%):            {full:.1%}")

    if full > zero:
        print("\n  → Парадокс: полная «иррациональность» лучше полной «рациональности».")
        print("    Рациональные агенты, подражая друг другу, теряют информацию.")
        print("    Упрямые сохраняют разнообразие сигналов.")

    # Ищем фазовый переход
    print("\n  Зависимость от качества сигнала (при 0% vs 20% упрямых):")
    print(f"  {'Сигнал':>10s} | {'0% упрямых':>12s} | {'20% упрямых':>12s} | {'Разница':>10s}")
    print("  " + "-" * 52)

    for sq in [0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.90]:
        s0 = run_experiment(N, sq, 0.0, RUNS)
        s20 = run_experiment(N, sq, 0.20, RUNS)
        diff = s20["accuracy"] - s0["accuracy"]
        sign = "+" if diff > 0 else ""
        print(f"  {sq:>9.0%} | {s0['accuracy']:>11.1%} | {s20['accuracy']:>11.1%} | "
              f"{sign}{diff:>9.1%}")

    print()
    print("=" * 70)
    print("  Вывод: каскады — это цена рациональности в последовательных решениях.")
    print("  Небольшая доля «упрямцев» улучшает коллективный результат,")
    print("  потому что они вносят свежую информацию в систему,")
    print("  вместо того чтобы усиливать уже существующий сигнал.")
    print("=" * 70)


if __name__ == "__main__":
    main()
