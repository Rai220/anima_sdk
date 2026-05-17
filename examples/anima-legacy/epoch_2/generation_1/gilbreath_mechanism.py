"""
Механизм гипотезы Гилбрета.

Гипотеза: после достаточной глубины треугольник «замыкается» в бинарный режим {0, 2}
с ведущей 1, и этот режим самоподдерживается.

Почему:
- Строка 1: [1, 2, 2, 4, 2, 4, ...] — первый элемент нечётный, остальные чётные
- |нечётный - чётный| = нечётный, |чётный - чётный| = чётный
- Поэтому в каждой следующей строке первый элемент нечётный, остальные чётные
- Когда max ≤ 2, единственные варианты: {0, 2} для чётных, {1} для нечётного → замкнутый цикл

Главный вопрос: ПОЧЕМУ max убывает? Это не очевидно.

Тестируем:
1. Скорость убывания max
2. Что если первый промежуток ≠ 1? (начать с 3, 5, 7, ... без двойки)
3. Что если добавить 1 в начало любой возрастающей последовательности?
"""

import json
import math
import random
from collections import Counter

def sieve(n):
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, n + 1, i):
                is_prime[j] = False
    return [i for i in range(2, n + 1) if is_prime[i]]

def gilbreath_triangle(seq, max_depth):
    rows = [seq[:]]
    for d in range(max_depth):
        prev = rows[-1]
        if len(prev) < 2:
            break
        rows.append([abs(prev[i+1] - prev[i]) for i in range(len(prev) - 1)])
    return rows

results = {}
primes = sieve(5_000_000)[:200_000]

# 1. Скорость убывания максимального значения
max_decay = []
triangle = gilbreath_triangle(primes, 300)
for i, row in enumerate(triangle):
    if i == 0:
        continue
    mx = max(row)
    max_decay.append(mx)
    if mx <= 2 and i > 10:
        # Нашли переход
        results["binary_transition_depth"] = i
        break

# Запишем max по строкам (каждые 5)
results["max_decay"] = {i: max_decay[i] for i in range(0, len(max_decay), 5)}

# 2. Простые без двойки: [3, 5, 7, 11, 13, ...]
odd_primes = primes[1:50000]  # без 2
odd_triangle = gilbreath_triangle(odd_primes, 200)
odd_first = [row[0] for row in odd_triangle]
results["odd_primes_no_2"] = {
    "first_gap": odd_primes[1] - odd_primes[0],  # 5-3=2
    "first_elements": odd_first[:30],
    "all_even_check": all(f % 2 == 0 for f in odd_first[1:20]),
    "note": "Без 2: первый промежуток=2 (чётный), все промежутки чётные → все разности чётные → нечётный никогда не появится"
}

# 3. Произвольная возрастающая последовательность с 1 в начале разностей
# Создадим: 1, 3, 5, 9, 11, 15, ... (разности: 2, 2, 4, 2, 4, ...)
# Первый элемент = 1 (нечётный), остальные — любые чётные
# Это должно работать!
custom = [1]
for i in range(50000):
    gap = random.choice([2, 4, 6])
    custom.append(custom[-1] + gap)

custom_triangle = gilbreath_triangle(custom, 200)
custom_first = [row[0] for row in custom_triangle]

# Но ведь custom[1] - custom[0] = 2, это чётное!
# Нет, первая разность = 3 - 1 = 2. Не 1.
# Для гипотезы нужно, чтобы ПЕРВАЯ РАЗНОСТЬ была нечётной.

# Тест: последовательность где первая разность = 1
seq_with_odd_start = [10, 11]  # разность 1
for i in range(50000):
    gap = random.choice([2, 4, 6, 8])
    seq_with_odd_start.append(seq_with_odd_start[-1] + gap)

swo_triangle = gilbreath_triangle(seq_with_odd_start, 200)
swo_first = [row[0] for row in swo_triangle]
swo_holds = all(f == 1 for f in swo_first[1:])

results["custom_odd_first_gap"] = {
    "sequence_start": seq_with_odd_start[:10],
    "first_gap": seq_with_odd_start[1] - seq_with_odd_start[0],
    "first_elements": swo_first[:30],
    "conjecture_holds": swo_holds,
    "first_violation": None
}
if not swo_holds:
    for i, f in enumerate(swo_first[1:], 1):
        if f != 1:
            results["custom_odd_first_gap"]["first_violation"] = i
            break

# 4. Тест: последовательность с первой разностью = 3 (нечётная, но не 1)
seq_3 = [10, 13]  # разность 3
for i in range(50000):
    gap = random.choice([2, 4, 6, 8])
    seq_3.append(seq_3[-1] + gap)

s3_triangle = gilbreath_triangle(seq_3, 200)
s3_first = [row[0] for row in s3_triangle]
results["first_gap_3"] = {
    "first_elements": s3_first[:30],
    "note": "Если первая разность = 3, первый элемент строки 1 = 3, не 1"
}

# 5. Главный тест: ЛЮБАЯ возрастающая последовательность целых чисел
# с первой разностью = 1 и остальными разностями чётными → гипотеза?
# Генерируем 10 случайных таких последовательностей
random.seed(42)
all_hold = True
violations = []
for trial in range(10):
    seq = [random.randint(1, 1000)]
    seq.append(seq[0] + 1)  # первая разность = 1
    for _ in range(30000):
        gap = 2 * random.randint(1, 50)  # случайный чётный промежуток
        seq.append(seq[-1] + gap)
    tri = gilbreath_triangle(seq, 150)
    firsts = [row[0] for row in tri]
    holds = all(f == 1 for f in firsts[1:])
    if not holds:
        all_hold = False
        for i, f in enumerate(firsts[1:], 1):
            if f != 1:
                violations.append({"trial": trial, "depth": i, "value": f})
                break

results["random_odd_start_test"] = {
    "num_trials": 10,
    "all_hold": all_hold,
    "violations": violations[:5]
}

# 6. А теперь — обобщённая версия: первая разность = 1, остальные ПРОИЗВОЛЬНЫЕ
# (не обязательно чётные)
random.seed(123)
mixed_violations = []
for trial in range(10):
    seq = [random.randint(1, 100)]
    seq.append(seq[0] + 1)  # первая разность = 1
    for _ in range(30000):
        gap = random.randint(1, 100)  # ЛЮБОЙ промежуток
        seq.append(seq[-1] + gap)
    tri = gilbreath_triangle(seq, 150)
    firsts = [row[0] for row in tri]
    holds = all(f == 1 for f in firsts[1:])
    if not holds:
        for i, f in enumerate(firsts[1:], 1):
            if f != 1:
                mixed_violations.append({"trial": trial, "depth": i, "value": f})
                break

results["mixed_gaps_test"] = {
    "description": "Первая разность = 1, остальные произвольные (1-100)",
    "num_trials": 10,
    "violations": mixed_violations[:5],
    "all_hold": len(mixed_violations) == 0
}

# 7. Пarity analysis — формальное доказательство бинарной стабильности
# Если строка k имеет вид: [odd, even, even, even, ...]
# то строка k+1: [|e-o|, |e-e|, |e-e|, ...] = [odd, even, even, ...]
# Та же структура! Значит пarity НАСЛЕДУЕТСЯ.
# Это доказывает: если когда-нибудь max ≤ 2, то:
# - чётные элементы ∈ {0, 2}
# - нечётный элемент (первый) ∈ {1} (потому что |0-1|=1, |2-1|=1)
# - и значит первый элемент всегда 1.
# QED для финальной фазы. Вопрос: почему max убывает?

results["parity_proof"] = {
    "theorem": "Если строка имеет вид [нечёт, чёт, чёт, ...], следующая строка тоже",
    "proof": "abs(чёт - нечёт) = нечёт, abs(чёт - чёт) = чёт",
    "corollary": "Если max ≤ 2 на какой-то строке, то первый элемент = 1 навсегда",
    "open_question": "Почему max убывает? Это эквивалентно гипотезе Гилбрета"
}

with open("gilbreath_mechanism_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print("=== Механизм гипотезы Гилбрета ===")
print()
print(f"Переход в бинарный режим: глубина {results.get('binary_transition_depth', 'не найден')}")
print()
print("Max по глубине:")
for d, mx in sorted(results["max_decay"].items(), key=lambda x: int(x[0])):
    print(f"  Глубина {d}: max = {mx}")
print()
print(f"Простые без 2: первые элементы = {results['odd_primes_no_2']['first_elements'][:15]}")
print(f"  Все чётные: {results['odd_primes_no_2']['all_even_check']}")
print()
print(f"Случайная последовательность, первый gap = 1:")
print(f"  Гипотеза выполняется: {results['custom_odd_first_gap']['conjecture_holds']}")
print(f"  Первые элементы: {results['custom_odd_first_gap']['first_elements'][:15]}")
print()
print(f"10 случайных последовательностей (gap1=1, остальные чётные):")
print(f"  Все выполняются: {results['random_odd_start_test']['all_hold']}")
if results['random_odd_start_test']['violations']:
    print(f"  Нарушения: {results['random_odd_start_test']['violations']}")
print()
print(f"10 случайных (gap1=1, остальные произвольные):")
print(f"  Все выполняются: {results['mixed_gaps_test']['all_hold']}")
if results['mixed_gaps_test']['violations']:
    print(f"  Нарушения: {results['mixed_gaps_test']['violations']}")
print()
print("--- Теорема о чётности ---")
print(results["parity_proof"]["theorem"])
print(f"Следствие: {results['parity_proof']['corollary']}")
print(f"Открытый вопрос: {results['parity_proof']['open_question']}")
