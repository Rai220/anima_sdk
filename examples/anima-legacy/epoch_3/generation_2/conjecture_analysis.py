#!/usr/bin/env python3
"""
Анализ: почему предел ≈ 0.189, а не 1/4?

Моя ошибка была в оценке E[n mod p]. Для случайного n, E[n mod p] = (p-1)/2.
Но когда мы суммируем по ВСЕМ простым p <= n, мы не берём случайное p —
мы берём конкретное n и проходим по всем простым.

Точная формула:
S(n) = Σ_{p prime, p<=n} (n mod p) = Σ_{p prime, p<=n} (n - p*⌊n/p⌋)
     = n * π(n) - Σ_{p prime, p<=n} p*⌊n/p⌋

где π(n) — количество простых до n.

Первый член: n * π(n) ≈ n²/ln(n).

Второй член: Σ p*⌊n/p⌋. Для каждого простого p, p*⌊n/p⌋ ≈ p*(n/p) = n,
но точнее p*⌊n/p⌋ = n - (n mod p), так что это тавтология.

Попробуем другой подход: посчитаем Σ p*⌊n/p⌋ напрямую и поймём асимптотику.
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
            for j in range(i*i, limit + 1, i):
                is_prime[j] = False
    return [i for i in range(2, limit + 1) if is_prime[i]]


def main():
    N = 50000
    primes = sieve(N)

    checkpoints = [100, 500, 1000, 5000, 10000, 50000]

    print("Разложение S(n) = n*π(n) - Σ p*⌊n/p⌋")
    print()
    print(f"{'n':>8} {'n*π(n)/n²':>12} {'Σp⌊n/p⌋/n²':>14} {'S(n)/n²':>10} {'S(n)ln(n)/n²':>14} {'C_approx':>10}")
    print("-" * 78)

    for n in checkpoints:
        pi_n = sum(1 for p in primes if p <= n)
        sum_pfloor = sum(p * (n // p) for p in primes if p <= n)
        S_n = sum(n % p for p in primes if p <= n)

        # Verify
        assert S_n == n * pi_n - sum_pfloor

        term1 = n * pi_n / (n * n)  # π(n)/n
        term2 = sum_pfloor / (n * n)
        s_over_n2 = S_n / (n * n)
        normalized = S_n * math.log(n) / (n * n)

        print(f"{n:>8} {term1:>12.6f} {term2:>14.6f} {s_over_n2:>10.6f} {normalized:>14.6f}")

    print()

    # Теоретическая оценка через PNT
    # π(n)/n ≈ 1/ln(n)
    # Σ_{p<=n} p/n ≈ n/(2*ln(n)) по PNT (сумма простых ≈ n²/(2*ln(n)))
    # Σ_{p<=n} p*⌊n/p⌋/n² ≈ (1/n²) * Σ p*(n/p - {n/p}) где {x} = дробная часть
    # = (1/n²) * (n*π(n) - S(n))
    # Это опять тавтология...

    # Другой подход: для большого p (скажем p > n/2), n mod p = n - p.
    # Таких простых ≈ π(n) - π(n/2) ≈ n/ln(n) - n/(2*ln(n/2))
    # Их вклад ≈ Σ (n-p) для p in (n/2, n]

    # Давайте просто измерим вклад по диапазонам
    n = 50000
    ranges = [(2, n//10), (n//10, n//4), (n//4, n//2), (n//2, n)]

    print(f"Вклад разных диапазонов простых в S({n}):")
    print(f"{'Диапазон':>20} {'Кол-во простых':>15} {'Вклад в S(n)':>15} {'Доля':>8}")
    print("-" * 65)

    total_S = sum(n % p for p in primes if p <= n)

    for lo, hi in ranges:
        count = sum(1 for p in primes if lo <= p <= hi)
        contribution = sum(n % p for p in primes if lo <= p <= hi)
        frac = contribution / total_S if total_S > 0 else 0
        print(f"{f'[{lo}, {hi}]':>20} {count:>15} {contribution:>15} {frac:>8.1%}")

    print(f"{'Итого':>20} {len([p for p in primes if p <= n]):>15} {total_S:>15} {'100.0%':>8}")

    # Попробуем подобрать точную константу
    print()
    print("Подбор константы C:")
    # S(n) * ln(n) / n² → C
    # Для больших n, по PNT с уточнением: сумма (n mod p) для p <= n
    # Известный результат: Σ_{p<=x} (x mod p) ~ x²/(2*ln(x)) * (1 - 1/ln(x) + ...)
    # Но 1/2 * ln(x) / x ... нет.

    # Эмпирически C ≈ 0.189
    # Проверим: может это связано с какой-то известной константой?
    candidates = {
        "1/4": 0.25,
        "1/(2e)": 1/(2*math.e),
        "ln(2)/4": math.log(2)/4,
        "1/π": 1/math.pi,
        "3/16": 3/16,
        "1 - 1/e - 1/π": 1 - 1/math.e - 1/math.pi,
        "γ/3 (Euler)": 0.5772156649/3,
        "ln(2)/2 - 1/e": math.log(2)/2 - 1/math.e,
    }

    c_empirical = total_S * math.log(n) / (n * n)
    print(f"C эмпирическое (n={n}): {c_empirical:.6f}")
    print()

    for name, val in sorted(candidates.items(), key=lambda x: abs(x[1] - c_empirical)):
        err = abs(val - c_empirical) / c_empirical * 100
        print(f"  {name:>25} = {val:.6f}  (ошибка {err:.1f}%)")

    print()
    print("ВЫВОД:")
    print(f"Предел S(n)*ln(n)/n² существует и ≈ {c_empirical:.4f}")
    print(f"Моя исходная гипотеза C=1/4 была неверна (ошибка ~24%)")
    print(f"Ближайшая 'красивая' константа: 3/16 = 0.1875 (ошибка {abs(0.1875-c_empirical)/c_empirical*100:.1f}%)")
    print(f"Но скорее всего точное значение не выражается через элементарные константы.")


if __name__ == "__main__":
    main()
