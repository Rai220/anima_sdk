#!/usr/bin/env python3
"""
conjecture_solved.py — аналитическое решение гипотезы из conjecture.py

Итерация 2 гипотезу S(n)·ln(n)/n² → C и предсказала C = 1/4.
Получила эмпирически C ≈ 0.189 при n=50000, ошибка 24%.
Итерация 2 не нашла точного значения.

ТОЧНЫЙ ОТВЕТ: C = 1 - π²/12 ≈ 0.17753

Эмпирическое 0.189 — не предел, а значение при конечном n.
Сходимость логарифмически медленная. При n=50000 до предела ещё далеко.

ВЫВОД:
=======

S(n) = Σ_{p≤n} (n mod p) = Σ_{p≤n} p·{n/p}

где {x} = дробная часть x.

По теореме о простых числах, плотность простых около t равна 1/ln(t).
Подставляя p = nx (x ∈ (0,1]), получаем:

  S(n) ≈ n² ∫₀¹ x·{1/x} / (ln(n) + ln(x)) dx

Ведущий член: n²/ln(n) · ∫₀¹ x·{1/x} dx

Вычисляем интеграл. На интервале (1/(k+1), 1/k] имеем ⌊1/x⌋ = k, то есть {1/x} = 1/x - k.

  ∫₀¹ x·{1/x} dx = Σ_{k=1}^∞ ∫_{1/(k+1)}^{1/k} x·(1/x - k) dx
                   = Σ_{k=1}^∞ ∫_{1/(k+1)}^{1/k} (1 - kx) dx
                   = Σ_{k=1}^∞ [x - kx²/2]_{1/(k+1)}^{1/k}

При x=1/k:    1/k - 1/(2k) = 1/(2k)
При x=1/(k+1): 1/(k+1) - k/(2(k+1)²) = (k+2)/(2(k+1)²)

Каждый член: 1/(2k) - (k+2)/(2(k+1)²) = 1/(2k(k+1)²)

[Проверка: числитель (k+1)² - k(k+2) = k²+2k+1-k²-2k = 1. ✓]

Значит:

  ∫₀¹ x·{1/x} dx = (1/2) Σ_{k=1}^∞ 1/(k(k+1)²)

Разложение на простые дроби:
  1/(k(k+1)²) = 1/k - 1/(k+1) - 1/(k+1)²

Суммируем:
  Σ_{k=1}^∞ [1/k - 1/(k+1)] = 1   (телескопическая)
  Σ_{k=1}^∞ 1/(k+1)² = π²/6 - 1   (Базельская задача минус k=1)

Итого: Σ = 1 - (π²/6 - 1) = 2 - π²/6

  C = (1/2)(2 - π²/6) = 1 - π²/12 ≈ 0.17753
"""

import math
from typing import List


def sieve(limit: int) -> List[int]:
    if limit < 2:
        return []
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if is_prime[i]:
            for j in range(i * i, limit + 1, i):
                is_prime[j] = False
    return [i for i in range(2, limit + 1) if is_prime[i]]


def compute_integral_numerically(terms=100000):
    """Численная проверка: ∫₀¹ x·{1/x} dx = (1/2)Σ 1/(k(k+1)²)"""
    total = sum(1.0 / (k * (k + 1) ** 2) for k in range(1, terms + 1))
    return total / 2


def compute_integral_exact():
    """Точное значение: 1 - π²/12"""
    return 1 - math.pi**2 / 12


def main():
    C_exact = compute_integral_exact()
    C_numerical_series = compute_integral_numerically(100000)

    print("=" * 70)
    print("РЕШЕНИЕ ГИПОТЕЗЫ")
    print("=" * 70)
    print()
    print(f"  S(n) · ln(n) / n²  →  1 - π²/12")
    print()
    print(f"  Точное значение:    {C_exact:.10f}")
    print(f"  Числ. ряд (10⁵):   {C_numerical_series:.10f}")
    print(f"  Совпадение:         {abs(C_exact - C_numerical_series):.2e}")
    print()

    # Эмпирическая проверка
    print("=" * 70)
    print("ЭМПИРИЧЕСКАЯ ПРОВЕРКА")
    print("=" * 70)
    print()

    N = 100000
    print(f"Вычисляю простые до {N}...")
    primes = sieve(N)
    print(f"Найдено {len(primes)} простых")
    print()

    checkpoints = [100, 500, 1000, 5000, 10000, 50000, 100000]

    print(f"{'n':>8}  {'S(n)·ln(n)/n²':>15}  {'1-π²/12':>10}  {'ошибка':>10}  {'(ошибка-D/lnn)':>15}")
    print("-" * 68)

    # Оценим D из двух последних точек
    vals = []
    for n in checkpoints:
        if n > N:
            break
        s = sum(n % p for p in primes if p <= n)
        normalized = s * math.log(n) / (n * n)
        err = normalized - C_exact
        # Если S(n)·ln(n)/n² ≈ C + D/ln(n), то err ≈ D/ln(n)
        corrected = err - 0.126 / math.log(n)  # D ≈ 0.126, подберём ниже
        vals.append((n, normalized, err))
        print(f"{n:>8}  {normalized:>15.8f}  {C_exact:>10.6f}  {err:>+10.6f}  {corrected:>+15.6f}")

    # Оценка D из двух точек: err ≈ D/ln(n)
    if len(vals) >= 2:
        n1, f1, e1 = vals[-2]
        n2, f2, e2 = vals[-1]
        # e1 ≈ D/ln(n1), e2 ≈ D/ln(n2)
        D_est = (e1 * math.log(n1) + e2 * math.log(n2)) / 2
        print()
        print(f"  Оценка D (поправка 2-го порядка): {D_est:.4f}")
        print(f"  Модель: S(n)·ln(n)/n² ≈ {C_exact:.4f} + {D_est:.4f}/ln(n)")
        print()

        # Прогноз для больших n
        print("  Прогноз по модели:")
        for n_pred in [10**6, 10**8, 10**12]:
            predicted = C_exact + D_est / math.log(n_pred)
            print(f"    n = {n_pred:.0e}: S(n)·ln(n)/n² ≈ {predicted:.6f}")

    print()
    print("=" * 70)
    print("ПОЧЕМУ ИТЕРАЦИЯ 2 ОШИБАЛАСЬ")
    print("=" * 70)
    print()
    print("  Предсказание итерации 2:  C = 1/4 = 0.25")
    print(f"  Фактический предел:       C = 1-π²/12 ≈ {C_exact:.6f}")
    print(f"  Разница:                   {0.25 - C_exact:.6f} ({(0.25 - C_exact)/C_exact*100:.1f}%)")
    print()
    print("  Ошибка в рассуждении: E[n mod p] ≈ (p-1)/2 верно в среднем по n,")
    print("  но для фиксированного n сумма по простым включает корреляции.")
    print("  Правильный подход — через интеграл x·{1/x} и Базельскую задачу.")
    print()
    print("  Эмпирическое значение 0.189 при n=50000 — не предел,")
    print(f"  а промежуточное значение. До {C_exact:.4f} ещё далеко из-за")
    print("  логарифмически медленной сходимости.")
    print()
    print("  Красота результата: предел связан с π через Базельскую задачу")
    print("  (Σ 1/k² = π²/6), что неочевидно для задачи о простых числах.")


if __name__ == "__main__":
    main()
