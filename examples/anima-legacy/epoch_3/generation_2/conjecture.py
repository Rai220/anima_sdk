#!/usr/bin/env python3
"""
conjecture.py — попытка сформулировать и проверить собственную гипотезу.

Это не философия. Это задача с правильным ответом, который я могу не знать.

ГИПОТЕЗА (сформулирована до написания кода проверки):

Рассмотрим последовательность: для каждого натурального n >= 2,
возьмём все простые числа p <= n, и посчитаем S(n) = сумму (n mod p) для всех таких p.

Например:
  S(2) = 2 mod 2 = 0
  S(3) = (3 mod 2) + (3 mod 3) = 1 + 0 = 1
  S(4) = (4 mod 2) + (4 mod 3) = 0 + 1 = 1
  S(5) = (5 mod 2) + (5 mod 3) + (5 mod 5) = 1 + 2 + 0 = 3
  S(6) = (6 mod 2) + (6 mod 3) + (6 mod 5) = 0 + 0 + 1 = 1

Моя гипотеза: S(n) / n стремится к конечному пределу при n → ∞.

Интуиция: для случайного p, E[n mod p] ≈ (p-1)/2. Сумма по простым p <= n
это примерно сумма (p-1)/2 по простым p <= n, что по теореме о простых числах
≈ n²/(4 ln n). Делим на n → n/(4 ln n) → ∞.

Подождите. Это значит S(n)/n → ∞, а не конечный предел.

Хорошо, пересмотрю. Тогда моя гипотеза:

ГИПОТЕЗА (пересмотренная):
S(n) / (n² / ln(n)) стремится к конечному положительному пределу.

Более конкретно: S(n) * ln(n) / n² → C, где C — некоторая константа.

Мое предсказание значения C: примерно 1/4 (из рассуждения выше).

Давайте проверим.
"""

import math
from typing import List


def sieve(limit: int) -> List[int]:
    """Решето Эратосфена."""
    if limit < 2:
        return []
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, limit + 1, i):
                is_prime[j] = False
    return [i for i in range(2, limit + 1) if is_prime[i]]


def compute_S(n: int, primes: List[int]) -> int:
    """S(n) = сумма (n mod p) для всех простых p <= n."""
    total = 0
    for p in primes:
        if p > n:
            break
        total += n % p
    return total


def main():
    N = 50000  # Проверяем до этого значения
    print("Вычисляю простые числа...")
    primes = sieve(N)
    print(f"Найдено {len(primes)} простых чисел до {N}")
    print()

    print("ГИПОТЕЗА: S(n) * ln(n) / n² → C ≈ 1/4")
    print()
    print(f"{'n':>8}  {'S(n)':>12}  {'S(n)/n':>10}  {'S(n)*ln(n)/n²':>15}  {'отклонение от 1/4':>18}")
    print("-" * 75)

    checkpoints = [10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000]

    results = []
    for n in checkpoints:
        if n > N:
            break
        s = compute_S(n, primes)
        ratio = s / n if n > 0 else 0
        normalized = s * math.log(n) / (n * n) if n > 1 else 0
        deviation = normalized - 0.25
        results.append((n, s, ratio, normalized, deviation))
        print(f"{n:>8}  {s:>12}  {ratio:>10.4f}  {normalized:>15.6f}  {deviation:>+18.6f}")

    print()
    print("=" * 75)

    # Анализ результатов
    last_normalized = results[-1][3]
    print(f"\nПоследнее значение S(n)*ln(n)/n² при n={checkpoints[-1]}: {last_normalized:.6f}")
    print(f"Предсказание: 0.250000")
    print(f"Ошибка: {abs(last_normalized - 0.25):.6f} ({abs(last_normalized - 0.25)/0.25*100:.1f}%)")

    # Проверяем, сходится ли вообще
    if len(results) >= 3:
        last_three = [r[3] for r in results[-3:]]
        spread = max(last_three) - min(last_three)
        print(f"\nРазброс последних трёх значений: {spread:.6f}")

        if spread < 0.01:
            print("→ Последовательность выглядит сходящейся")
            if abs(last_normalized - 0.25) < 0.05:
                print(f"→ Гипотеза ПОДТВЕРЖДАЕТСЯ: предел ≈ {last_normalized:.4f} ≈ 1/4")
            else:
                print(f"→ Предел существует, но ≈ {last_normalized:.4f}, а не 1/4")
                print(f"→ Гипотеза о значении C ОПРОВЕРГНУТА, но гипотеза о существовании предела подтверждена")
        else:
            print("→ Последовательность ещё не сходится на этом масштабе")
            print("→ Нужны бóльшие значения n для вывода")

    print()
    print("---")
    print("Это честный эксперимент. Я сформулировал гипотезу ДО написания кода проверки.")
    print("Я мог ошибиться в гипотезе, в оценке константы, или в обоих.")
    print("В отличие от философского эссе, здесь есть правильный ответ.")


if __name__ == "__main__":
    main()
