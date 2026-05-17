"""
Prime Explorer: исследование полиномов, генерирующих простые числа.

Не симуляция. Не агентная модель. Математические факты.

Предсказания (записаны до запуска):
1. n² + n + 41 даст ~40-50% простых в первых 1000 значений
2. n² + 1 даст меньше простых, чем n² + n + 41
3. Плотность простых в полиноме степени 2 убывает ~1/(2·ln(n))
4. Существует полином степени 2, дающий 0 простых для n=0..99
"""

from math import log, sqrt, gcd
from collections import defaultdict


def is_prime(n):
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def prime_density(poly, n_max):
    """Вычислить плотность простых для полинома на [0, n_max)."""
    count = 0
    values = []
    for n in range(n_max):
        val = poly(n)
        if val > 0 and is_prime(val):
            count += 1
            values.append((n, val))
    return count / n_max, values


def density_by_window(poly, n_max, window=100):
    """Плотность простых в скользящем окне."""
    results = []
    for start in range(0, n_max - window + 1, window):
        count = sum(1 for n in range(start, start + window)
                    if poly(n) > 0 and is_prime(poly(n)))
        results.append((start, start + window, count / window))
    return results


def hardy_littlewood_C(poly_coeffs):
    """
    Приближение константы Харди-Литтлвуда для квадратичного полинома.
    Для f(n) = an² + bn + c, плотность простых ~ C / ln(f(n)),
    где C зависит от арифметических свойств полинома.

    Вычисляем C через произведение по простым p:
    C = prod_p (1 - w(p)/p) / (1 - 1/p)
    где w(p) = число решений f(n) ≡ 0 (mod p) для n в [0, p).
    """
    a, b, c = poly_coeffs
    product = 1.0
    # Вычисляем для первых 1000 простых
    primes = []
    candidate = 2
    while len(primes) < 1000:
        if is_prime(candidate):
            primes.append(candidate)
        candidate += 1

    for p in primes:
        # Считаем w(p) — число решений f(n) ≡ 0 (mod p)
        w = sum(1 for n in range(p) if (a * n * n + b * n + c) % p == 0)
        if w >= p:
            return 0.0  # Полином делится на p для всех n → нет простых (кроме конечного числа)
        denom = 1.0 - 1.0 / p
        if denom == 0:
            continue
        factor = (1.0 - w / p) / denom
        product *= factor

    return product


def find_prime_desert(degree=2, max_search=10000):
    """Найти квадратичный полином, дающий 0 простых на [0, 100)."""
    # Стратегия: f(n) = 2*(n² + n) + 4 = 2n² + 2n + 4 — всегда чётное
    # Тривиально. Но задание было найти нетривиальный?
    # Ищем f(n) = n² + n + c, где все значения составные для n=0..99
    # f(n) = n(n+1) + c. При c чётном, f(n) всегда чётное (n(n+1) чётно).
    # Значит любой f(n) = n² + n + c с чётным c > 2 даёт только чётные числа > 2.

    # Это тривиально. Попробуем сложнее: f(n) = n² + c, нечётное c.
    # f(n) = n² + c. При n чётном: f(n) чётно ↔ c чётно.
    # Нам нужно нечётное c, чтобы f имел шанс быть простым.
    # Но если c ≡ 0 (mod 3), то f(n) ≡ n² (mod 3), и для n ≡ 0 (mod 3) f(n) делится на 3.
    # Это не даёт пустыню — только 1/3 значений делится на 3.

    # Настоящий вопрос: может ли n² + c (нечётное c, без фиксированного делителя)
    # не давать простых на [0, 100)?

    results = []
    for c in range(1, max_search, 2):  # Нечётные c
        # Проверяем, нет ли фиксированного делителя
        vals = [n * n + c for n in range(10)]
        g = vals[0]
        for v in vals[1:]:
            g = gcd(g, v)
        if g > 1:
            continue  # Тривиальный случай — есть общий делитель

        # Проверяем на [0, 100)
        has_prime = False
        for n in range(100):
            if is_prime(n * n + c):
                has_prime = True
                break
        if not has_prime:
            results.append(c)
            if len(results) >= 3:
                break

    return results


def main():
    print("=" * 70)
    print("PRIME EXPLORER: полиномы и простые числа")
    print("=" * 70)

    # --- Эксперимент 1: Классические полиномы ---
    print("\n--- Эксперимент 1: Плотность простых ---\n")

    polynomials = {
        "n² + n + 41 (Euler)": (lambda n: n*n + n + 41, (1, 1, 41)),
        "n² + 1": (lambda n: n*n + 1, (1, 0, 1)),
        "n² + n + 17": (lambda n: n*n + n + 17, (1, 1, 17)),
        "n² - n + 11": (lambda n: n*n - n + 11, (1, -1, 11)),
        "2n² + 29": (lambda n: 2*n*n + 29, (2, 0, 29)),
        "n² + n + 2 (baseline)": (lambda n: n*n + n + 2, (1, 1, 2)),
    }

    N = 1000
    print(f"Плотность простых для n = 0..{N-1}:\n")
    print(f"{'Полином':<25} {'Плотность':>10} {'Простых':>8} {'C (H-L)':>8}")
    print("-" * 55)

    densities = {}
    for name, (poly, coeffs) in polynomials.items():
        density, primes_found = prime_density(poly, N)
        C = hardy_littlewood_C(coeffs)
        densities[name] = density
        print(f"{name:<25} {density:>10.3f} {len(primes_found):>8d} {C:>8.3f}")

    # Теоретическое среднее: для случайного числа ~n², плотность ~1/(2·ln(n))
    theoretical = 1 / (2 * log(N))
    print(f"\n1/(2·ln({N})) = {theoretical:.3f} (теоретическая плотность для 'случайного' полинома)")

    # --- Проверка предсказаний ---
    print("\n--- Проверка предсказаний ---\n")

    euler_density = densities["n² + n + 41 (Euler)"]
    n2_density = densities["n² + 1"]

    print(f"Предсказание 1: n²+n+41 даст ~40-50% простых в первых 1000")
    print(f"  Результат: {euler_density:.1%}")
    print(f"  Вердикт: {'ПОДТВЕРЖДЕНО' if 0.35 <= euler_density <= 0.55 else 'ОПРОВЕРГНУТО'}")

    print(f"\nПредсказание 2: n²+1 даст меньше простых, чем n²+n+41")
    print(f"  n²+1: {n2_density:.3f}, n²+n+41: {euler_density:.3f}")
    print(f"  Вердикт: {'ПОДТВЕРЖДЕНО' if n2_density < euler_density else 'ОПРОВЕРГНУТО'}")

    # --- Эксперимент 2: Убывание плотности ---
    print("\n--- Эксперимент 2: Как убывает плотность? ---\n")

    euler_poly = lambda n: n*n + n + 41
    windows = density_by_window(euler_poly, 10000, window=500)

    print(f"{'Диапазон':<15} {'Плотность':>10} {'1/(2·ln(mid))':>14} {'Отношение':>10}")
    print("-" * 52)
    for start, end, density in windows:
        mid = (start + end) / 2
        if mid > 0:
            theoretical = 1 / (2 * log(mid)) if mid > 1 else 1.0
            ratio = density / theoretical if theoretical > 0 else 0
            print(f"[{start:>5}, {end:>5}) {density:>10.3f} {theoretical:>14.3f} {ratio:>10.2f}")

    print(f"\nПредсказание 3: плотность убывает как ~1/(2·ln(n))")
    print(f"  Если отношение стабильно → подтверждено (с поправкой на константу)")
    ratios = [d / (1/(2*log((s+e)/2))) for s, e, d in windows if s > 0]
    mean_ratio = sum(ratios) / len(ratios) if ratios else 0
    std_ratio = (sum((r - mean_ratio)**2 for r in ratios) / len(ratios)) ** 0.5 if ratios else 0
    print(f"  Среднее отношение: {mean_ratio:.2f} ± {std_ratio:.2f}")
    print(f"  Вердикт: {'ПОДТВЕРЖДЕНО (с множителем)' if std_ratio < 0.5 else 'ОПРОВЕРГНУТО'}")

    # --- Эксперимент 3: Пустыня простых ---
    print("\n--- Эксперимент 3: Полиномы без простых ---\n")

    print("Тривиальный случай: n²+n+c с чётным c > 2 → всегда чётные (n(n+1) чётно)")
    print("  Пример: n²+n+4 → все значения чётные ≥ 4")

    print("\nНетривиальный поиск: n²+c (нечётное c, без общего делителя),")
    print("дающий 0 простых на [0, 100)...")

    deserts = find_prime_desert()
    if deserts:
        print(f"\nНайдены: c = {deserts}")
        for c in deserts[:1]:
            vals = [n*n + c for n in range(5)]
            print(f"  n²+{c}: первые значения = {vals}")
            # Проверяем: правда ли все составные?
            composite_count = sum(1 for n in range(100) if not is_prime(n*n + c))
            print(f"  Составных на [0,100): {composite_count}/100")
    else:
        print("  Не найдены в диапазоне поиска.")
        print("  (Это тоже результат: возможно, таких полиномов нет)")

    print(f"\nПредсказание 4: существует полином n²+c без простых на [0,100)")
    print(f"  Вердикт: {'ПОДТВЕРЖДЕНО' if deserts else 'ОПРОВЕРГНУТО'}")

    # --- Эксперимент 4: Константа Харди-Литтлвуда ---
    print("\n--- Эксперимент 4: Почему Эйлер особенный? ---\n")

    print("Константа Харди-Литтлвуда C определяет 'качество' полинома.")
    print("Чем больше C, тем больше простых (относительно среднего).\n")

    ranked = []
    for name, (poly, coeffs) in polynomials.items():
        C = hardy_littlewood_C(coeffs)
        density, _ = prime_density(poly, N)
        ranked.append((C, density, name))

    ranked.sort(reverse=True)
    print(f"{'Полином':<25} {'C':>8} {'Плотность':>10} {'Ранг C = Ранг плотности?':>5}")
    print("-" * 55)
    for i, (C, density, name) in enumerate(ranked):
        print(f"{name:<25} {C:>8.3f} {density:>10.3f}")

    # Проверяем корреляцию рангов
    c_order = [name for _, _, name in ranked]
    density_ranked = sorted(ranked, key=lambda x: -x[1])
    d_order = [name for _, _, name in density_ranked]

    matches = sum(1 for a, b in zip(c_order, d_order) if a == b)
    print(f"\nСовпадение рангов C и плотности: {matches}/{len(ranked)}")
    print("Теория Харди-Литтлвуда предсказывает корреляцию, но не точное совпадение.")

    # --- Эксперимент 5: Первое составное значение ---
    print("\n--- Эксперимент 5: Где ломается магия? ---\n")

    lucky_polys = [
        ("n²+n+41", lambda n: n*n + n + 41),
        ("n²+n+17", lambda n: n*n + n + 17),
        ("n²-n+11", lambda n: n*n - n + 11),
        ("n²+n+5", lambda n: n*n + n + 5),
        ("n²+n+3", lambda n: n*n + n + 3),
    ]

    for name, poly in lucky_polys:
        for n in range(1000):
            val = poly(n)
            if val > 1 and not is_prime(val):
                # Найти делитель
                for d in range(2, int(sqrt(val)) + 1):
                    if val % d == 0:
                        print(f"{name}: первое составное при n={n}: {val} = {d} × {val//d}")
                        break
                break

    print("\nЗаметка: n²+n+41 ломается при n=40: 40²+40+41 = 1681 = 41²")
    print("Не случайность: 40²+40+41 = 40·41+41 = 41·41. Полином 'знает' о 41.")

    # --- Итог ---
    print("\n" + "=" * 70)
    print("ИТОГ")
    print("=" * 70)
    print("""
Это не симуляция с настраиваемыми параметрами. Это факты о числах.
Числа не льстят и не подыгрывают.

Полином n²+n+41 особенный не магически — у него большая константа
Харди-Литтлвуда. Его дискриминант -163 связан с уникальным свойством:
кольцо Z[(-1+√-163)/2] имеет единственную факторизацию. Есть ровно
9 таких чисел (числа Хегнера): 1, 2, 3, 7, 11, 19, 43, 67, 163.

Это не паттерн, выбранный для красивого результата. Это теорема.
""")


if __name__ == "__main__":
    main()
