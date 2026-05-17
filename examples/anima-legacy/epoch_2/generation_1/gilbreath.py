"""
Гипотеза Гилбрета: если взять простые числа и многократно брать
абсолютные разности соседних элементов, первый элемент каждой строки = 1.

Проверена до ~10^13, но никто не знает ПОЧЕМУ.

Я хочу посмотреть:
1. Как выглядят эти строки? Какие значения встречаются?
2. Есть ли закономерность в распределении значений по строкам?
3. Что происходит со структурой при увеличении глубины?
"""

import json
from collections import Counter
import time

def sieve(n):
    """Решето Эратосфена."""
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, n + 1, i):
                is_prime[j] = False
    return [i for i in range(2, n + 1) if is_prime[i]]

def gilbreath_triangle(primes, max_depth):
    """Строит треугольник Гилбрета до заданной глубины."""
    rows = [primes[:]]
    for d in range(max_depth):
        prev = rows[-1]
        if len(prev) < 2:
            break
        new_row = [abs(prev[i+1] - prev[i]) for i in range(len(prev) - 1)]
        rows.append(new_row)
    return rows

def analyze():
    results = {}

    # Генерируем простые
    N = 200_000
    t0 = time.time()
    primes = sieve(N * 20)  # с запасом
    primes = primes[:N]
    results["num_primes"] = len(primes)
    results["largest_prime"] = primes[-1]
    results["sieve_time"] = round(time.time() - t0, 2)

    # Строим треугольник
    DEPTH = 300
    t0 = time.time()
    triangle = gilbreath_triangle(primes, DEPTH)
    results["triangle_depth"] = len(triangle)
    results["triangle_time"] = round(time.time() - t0, 2)

    # 1. Проверяем гипотезу: первый элемент каждой строки = 1?
    first_elements = [row[0] for row in triangle]
    conjecture_holds = all(f == 1 for f in first_elements[1:])  # строка 0 = [2, 3, 5, ...], первый = 2
    results["conjecture_holds_to_depth"] = len(triangle) - 1
    results["conjecture_verified"] = conjecture_holds
    results["first_elements_sample"] = first_elements[:20]

    # 2. Распределение значений по строкам
    # На какой глубине какие значения доминируют?
    value_distributions = {}
    for depth in [1, 5, 10, 20, 50, 100, 150, 200, 250, 299]:
        if depth < len(triangle):
            row = triangle[depth]
            counter = Counter(row)
            total = len(row)
            # Топ-5 значений
            top5 = counter.most_common(5)
            value_distributions[depth] = {
                "length": total,
                "unique_values": len(counter),
                "max_value": max(row),
                "top5": [[v, c, round(c/total, 4)] for v, c, in top5],
                "fraction_0_or_2": round((counter.get(0, 0) + counter.get(2, 0)) / total, 4),
                "fraction_0": round(counter.get(0, 0) / total, 4),
                "fraction_1": round(counter.get(1, 0) / total, 4),
                "fraction_2": round(counter.get(2, 0) / total, 4),
            }
    results["value_distributions"] = value_distributions

    # 3. Интересный вопрос: как меняется доля нулей с глубиной?
    zero_fractions = []
    one_fractions = []
    two_fractions = []
    max_values = []
    for i, row in enumerate(triangle):
        if i == 0:
            continue
        c = Counter(row)
        total = len(row)
        zero_fractions.append(round(c.get(0, 0) / total, 4))
        one_fractions.append(round(c.get(1, 0) / total, 4))
        two_fractions.append(round(c.get(2, 0) / total, 4))
        max_values.append(max(row))

    # Сэмплируем каждые 10 строк
    results["zero_fraction_by_depth"] = {i*10: zero_fractions[i*10]
                                          for i in range(len(zero_fractions)//10)}
    results["one_fraction_by_depth"] = {i*10: one_fractions[i*10]
                                         for i in range(len(one_fractions)//10)}
    results["two_fraction_by_depth"] = {i*10: two_fractions[i*10]
                                         for i in range(len(two_fractions)//10)}
    results["max_value_by_depth"] = {i*10: max_values[i*10]
                                      for i in range(len(max_values)//10)}

    # 4. Вопрос, который меня интересует больше всего:
    # Есть ли корреляция между разностями в строке и положением простых?
    # Конкретно: предсказывает ли значение в строке k позицию следующей "аномалии"?

    # Посмотрим на паттерны "возврата к 0" — как часто строка проходит через 0?
    zero_gaps = {}
    for depth in [5, 10, 20, 50, 100]:
        if depth < len(triangle):
            row = triangle[depth]
            gaps = []
            last_zero = -1
            for i, v in enumerate(row):
                if v == 0:
                    if last_zero >= 0:
                        gaps.append(i - last_zero)
                    last_zero = i
            if gaps:
                avg_gap = round(sum(gaps) / len(gaps), 2)
                max_gap = max(gaps)
                zero_gaps[depth] = {
                    "avg_gap_between_zeros": avg_gap,
                    "max_gap": max_gap,
                    "num_zeros": len([v for v in row if v == 0]),
                }
    results["zero_gaps"] = zero_gaps

    # 5. Самое важное: что если заменить простые на случайные числа с тем же распределением?
    # Гипотеза: дело не в "простоте", а в распределении промежутков.
    import random
    random.seed(42)

    # Генерируем "псевдо-простые": случайные нечётные числа с промежутками,
    # распределёнными как у простых
    gaps = [primes[i+1] - primes[i] for i in range(len(primes)-1)]
    shuffled_gaps = gaps[:]
    random.shuffle(shuffled_gaps)

    fake_primes = [2]
    for g in shuffled_gaps:
        fake_primes.append(fake_primes[-1] + g)

    fake_triangle = gilbreath_triangle(fake_primes, min(DEPTH, 100))
    fake_first = [row[0] for row in fake_triangle]
    fake_holds = all(f == 1 for f in fake_first[1:])
    results["random_shuffled_gaps"] = {
        "conjecture_holds": fake_holds,
        "depth_checked": len(fake_triangle) - 1,
        "first_elements": fake_first[:30],
        "first_violation_depth": None
    }
    if not fake_holds:
        for i, f in enumerate(fake_first[1:], 1):
            if f != 1:
                results["random_shuffled_gaps"]["first_violation_depth"] = i
                break

    # А что если промежутки все = 2 (простые-близнецы)?
    twin_primes = [2] + [2 + 2*i for i in range(N)]
    twin_triangle = gilbreath_triangle(twin_primes, min(DEPTH, 100))
    twin_first = [row[0] for row in twin_triangle]
    results["constant_gap_2"] = {
        "first_elements": twin_first[:20],
        "note": "gaps all = 2: sequence 2,4,6,8,..."
    }

    # Случайные промежутки (не из реальных простых)
    random_gaps = [random.choice([2, 4, 6, 8, 10, 12]) for _ in range(N-1)]
    random_seq = [2]
    for g in random_gaps:
        random_seq.append(random_seq[-1] + g)
    random_triangle = gilbreath_triangle(random_seq, min(DEPTH, 100))
    random_first = [row[0] for row in random_triangle]
    random_holds = all(f == 1 for f in random_first[1:])
    results["random_even_gaps"] = {
        "conjecture_holds": random_holds,
        "depth_checked": len(random_triangle) - 1,
        "first_elements": random_first[:30],
        "first_violation_depth": None
    }
    if not random_holds:
        for i, f in enumerate(random_first[1:], 1):
            if f != 1:
                results["random_even_gaps"]["first_violation_depth"] = i
                break

    # 6. Ключевой тест: что если промежутки из геометрического распределения
    # (как у простых по теореме о простых числах)?
    # p_n ~ n*ln(n), так что gap ~ ln(n)
    import math
    geo_primes = [2]
    x = 2
    for i in range(1, N):
        # Среднее расстояние между простыми около n ≈ ln(n)
        avg_gap = max(2, round(math.log(x)))
        # Случайный чётный промежуток около этого значения
        gap = max(2, 2 * round(random.expovariate(1/avg_gap) / 2))
        x += gap
        geo_primes.append(x)

    geo_triangle = gilbreath_triangle(geo_primes, min(DEPTH, 100))
    geo_first = [row[0] for row in geo_triangle]
    geo_holds = all(f == 1 for f in geo_first[1:])
    results["geometric_gaps"] = {
        "conjecture_holds": geo_holds,
        "depth_checked": len(geo_triangle) - 1,
        "first_elements": geo_first[:30],
        "first_violation_depth": None
    }
    if not geo_holds:
        for i, f in enumerate(geo_first[1:], 1):
            if f != 1:
                results["geometric_gaps"]["first_violation_depth"] = i
                break

    return results

if __name__ == "__main__":
    results = analyze()

    with open("gilbreath_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print("=== Гипотеза Гилбрета ===")
    print(f"Простых: {results['num_primes']}, до {results['largest_prime']}")
    print(f"Глубина треугольника: {results['triangle_depth']}")
    print(f"Гипотеза выполняется: {results['conjecture_verified']}")
    print()
    print("--- Доля значений по глубине ---")
    for depth, dist in sorted(results['value_distributions'].items(), key=lambda x: int(x[0])):
        print(f"  Глубина {depth}: 0={dist['fraction_0']:.2%}, 1={dist['fraction_1']:.2%}, "
              f"2={dist['fraction_2']:.2%}, max={dist['max_value']}, уникальных={dist['unique_values']}")
    print()
    print("--- Перемешанные промежутки ---")
    rsg = results['random_shuffled_gaps']
    print(f"  Гипотеза выполняется: {rsg['conjecture_holds']}")
    if rsg['first_violation_depth']:
        print(f"  Первое нарушение: глубина {rsg['first_violation_depth']}")
    print(f"  Первые элементы: {rsg['first_elements'][:15]}")
    print()
    print("--- Случайные чётные промежутки ---")
    reg = results['random_even_gaps']
    print(f"  Гипотеза выполняется: {reg['conjecture_holds']}")
    if reg['first_violation_depth']:
        print(f"  Первое нарушение: глубина {reg['first_violation_depth']}")
    print()
    print("--- Геометрические промежутки (имитация PNT) ---")
    geo = results['geometric_gaps']
    print(f"  Гипотеза выполняется: {geo['conjecture_holds']}")
    if geo['first_violation_depth']:
        print(f"  Первое нарушение: глубина {geo['first_violation_depth']}")
