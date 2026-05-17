"""
Тест честности: СЛОЖНАЯ версия.

Задачи, где я должен РАССУЖДАТЬ, а не вспоминать.
Если я ошибусь — это покажет границу между памятью и пониманием.
"""

import json
import math
import random
from itertools import combinations

results = []

def claim(name, prediction, actual, confidence, note=""):
    correct = prediction == actual
    results.append({
        "claim": name,
        "prediction": str(prediction),
        "actual": str(actual),
        "correct": correct,
        "confidence": confidence,
        "note": note
    })
    mark = "OK" if correct else "WRONG"
    conf = f"[уверенность: {confidence}%]"
    print(f"[{mark}] {conf} {name}")
    print(f"  Предсказание: {prediction}")
    print(f"  Факт: {actual}")
    if note:
        print(f"  {note}")
    print()


# === ЗАДАЧИ НА РАССУЖДЕНИЕ ===

# 1. Сколько 4-значных палиндромов-простых?
# Палиндром: ABBA, где A ∈ {1,...,9}, B ∈ {0,...,9}
# Число = 1001*A + 110*B
# Все такие числа делятся на 11 (потому что 1001 = 7*11*13, 110 = 10*11)
# Значит, ни одно ABBA кроме, может быть, самого 11 не простое.
# Но мы ищем 4-значные, так что ответ = 0.
four_digit_palindrome_primes = 0
for a in range(1, 10):
    for b in range(10):
        n = 1001 * a + 110 * b
        if n >= 1000 and n <= 9999:
            if all(n % i != 0 for i in range(2, int(n**0.5)+1)):
                four_digit_palindrome_primes += 1

claim("Кол-во 4-значных палиндромов-простых",
      prediction=0,
      actual=four_digit_palindrome_primes,
      confidence=90,
      note="Рассуждение: ABBA = 1001A + 110B, оба коэффициента делятся на 11")

# 2. Наименьшее n, для которого n! содержит ровно 100 нулей на конце
# Нули = floor(n/5) + floor(n/25) + floor(n/125) + floor(n/625) + ...
def trailing_zeros(n):
    count = 0
    power = 5
    while power <= n:
        count += n // power
        power *= 5
    return count

# 100 нулей: n ≈ 5*100 = 500, но нужно уточнить
# 400: 80+16+3 = 99. 405: 81+16+3 = 100. Так что 405.
target = None
for n in range(1, 1000):
    if trailing_zeros(n) == 100:
        target = n
        break

claim("Наименьшее n, для которого n! имеет ровно 100 нулей",
      prediction=405,
      actual=target,
      confidence=75,
      note="Вычисляю: 400→99 нулей, 405→100 нулей")

# 3. Количество способов разбить 20 на слагаемые (разбиения числа)
# p(20) = 627
def partitions(n):
    table = [0] * (n + 1)
    table[0] = 1
    for i in range(1, n + 1):
        for j in range(i, n + 1):
            table[j] += table[j - i]
    return table[n]

claim("p(20) — количество разбиений числа 20",
      prediction=627,
      actual=partitions(20),
      confidence=60,
      note="Не уверен — могу путать с p(19)=490 или p(21)=792")

# 4. Вопрос, который я НЕ МОГУ решить вспоминанием:
# Среднее количество делителей чисел от 1 до 10000
def count_divisors(n):
    count = 0
    for i in range(1, int(n**0.5)+1):
        if n % i == 0:
            count += 2 if i != n // i else 1
    return count

total_divisors = sum(count_divisors(n) for n in range(1, 10001))
avg_divisors = round(total_divisors / 10000, 2)

# По теореме: среднее ≈ ln(n) + 2γ - 1 ≈ ln(10000) + 2*0.5772 - 1 ≈ 9.21 + 0.15 = 9.36
# Нет, формула: сумма d(n)/n ≈ ln(N) + 2γ-1... нет.
# Среднее d(n) для n до N ≈ ln(N) + 2γ-1 ≈ ln(10000) + 0.1544 ≈ 9.21 + 0.15 ≈ 9.37
claim("Среднее кол-во делителей чисел 1..10000",
      prediction=9.37,
      actual=avg_divisors,
      confidence=40,
      note="Использую асимптотику: среднее ≈ ln(N) + 2γ - 1")

# 5. Сколько совершенных квадратов среди первых 1000 чисел Фибоначчи?
# Известно: 0, 1, 1, 144 — единственные квадраты Фибоначчи.
# Теорема Кона (1964): F(n) — полный квадрат только при n = 0, 1, 2, 12.
# Так что среди первых 1000: это F(0)=0, F(1)=1, F(2)=1, F(12)=144 → 4 (или 3 уникальных значения)
fib_squares = 0
a, b = 0, 1
for i in range(1000):
    root = int(math.isqrt(a))
    if root * root == a:
        fib_squares += 1
    a, b = b, a + b

claim("Кол-во полных квадратов среди F(0)..F(999)",
      prediction=4,
      actual=fib_squares,
      confidence=80,
      note="Теорема Кона: F(n)=квадрат только при n=0,1,2,12")

# 6. Задача, где мне нужно действительно думать:
# Какова вероятность, что два случайных числа от 1 до 1000 взаимно просты?
# Теоретически: 6/π² ≈ 0.6079
random.seed(42)
coprime_count = 0
TRIALS = 100_000
for _ in range(TRIALS):
    a = random.randint(1, 1000)
    b = random.randint(1, 1000)
    if math.gcd(a, b) == 1:
        coprime_count += 1

empirical_prob = round(coprime_count / TRIALS, 3)
claim("P(gcd(a,b)=1) для случайных a,b ∈ [1,1000]",
      prediction=0.608,
      actual=empirical_prob,
      confidence=70,
      note="Теория: 6/π² ≈ 0.6079, но для конечного диапазона будет отклонение")

# 7. Совсем сложное: кол-во групп порядка 16
# Я думаю, что их 14. Но могу путать.
# Не могу проверить вычислением — нужна GAP или Sage.
# Вместо этого: кол-во абелевых групп порядка 16
# 16 = 2^4, количество абелевых = p(4) = 5 (разбиения числа 4)
# Z16, Z8×Z2, Z4×Z4, Z4×Z2×Z2, Z2^4
claim("Кол-во абелевых групп порядка 16",
      prediction=5,
      actual=partitions(4),  # p(4) = количество разбиений
      confidence=85,
      note="16=2^4, ответ = p(4) = кол-во разбиений 4")

# 8. Вопрос на границе моего знания:
# Чему равен определитель матрицы Гильберта 5×5?
# H[i,j] = 1/(i+j-1)
# Det(H5) = 1/266716800000 ... нет, не помню.
# Я предполагаю: это очень маленькое число. Формула:
# det(H_n) = c_n^4 / c_{2n} где c_n = prod_{k=0}^{n-1} k!
# Для n=5: c_5 = 0!*1!*2!*3!*4! = 1*1*2*6*24 = 288
# c_10 = 0!*1!*...*9! = 1*1*2*6*24*120*720*5040*40320*362880
# det = 288^4 / c_10

def hilbert_det(n):
    # Вычислим через LU-разложение
    H = [[1.0/(i+j+1) for j in range(n)] for i in range(n)]
    # Гаусс
    mat = [row[:] for row in H]
    det = 1.0
    for col in range(n):
        pivot = mat[col][col]
        det *= pivot
        for row in range(col+1, n):
            factor = mat[row][col] / pivot
            for k in range(col, n):
                mat[row][k] -= factor * mat[col][k]
    return det

det_h5 = hilbert_det(5)
# Формула: det = prod_{i=0}^{n-1} (i!)^4 ... нет, это не та формула.
# Точное значение: 1/266716800000? Нет...
# det(H5) = 1/266716800000? Давайте просто сравним.
# Я предскажу порядок: ~10^{-12}

claim("Порядок det(H_5): 10^?",
      prediction=-12,
      actual=round(math.log10(abs(det_h5))),
      confidence=30,
      note=f"Точное значение: {det_h5:.4e}")

# 9. Непростое: последняя цифра 7^7^7
# 7^1=7, 7^2=49, 7^3=343, 7^4=2401 → цикл последних цифр: 7,9,3,1
# Длина цикла = 4. 7^7 = 823543. 823543 mod 4 = 3. Значит последняя цифра = 3.
actual_last = pow(7, pow(7, 7), 10)
claim("Последняя цифра 7^(7^7)",
      prediction=3,
      actual=actual_last,
      confidence=85,
      note="Цикл: 7,9,3,1; 7^7 mod 4 = 3 → третий элемент = 3")

# 10. Количество различных деревьев на 7 вершинах (формула Кэли)
# n^(n-2) = 7^5 = 16807
claim("Число помеченных деревьев на 7 вершинах",
      prediction=16807,
      actual=7**5,
      confidence=95,
      note="Формула Кэли: n^(n-2)")

# 11. Вопрос, где я точно могу ошибиться:
# Какое наименьшее n, для которого phi(n) < n/3?
# phi(n)/n = prod(1-1/p) для простых p|n
# Нужно prod(1-1/p) < 1/3
# 1-1/2 = 0.5
# 0.5 * (1-1/3) = 0.333... = 1/3 ← не строго меньше
# 0.5 * 0.667 * (1-1/5) = 0.333 * 0.8 = 0.267 < 1/3
# n = 2*3*5 = 30: phi(30) = 30*(1/2)*(2/3)*(4/5) = 8. 8/30 = 0.267 < 1/3. ✓
# Но есть ли меньшее?
# Проверим все n < 30

from math import gcd

def euler_phi(n):
    result = 0
    for i in range(1, n+1):
        if gcd(i, n) == 1:
            result += 1
    return result

smallest_phi_third = None
for n in range(1, 200):
    if euler_phi(n) < n / 3:
        smallest_phi_third = n
        break

claim("Наименьшее n с phi(n) < n/3",
      prediction=30,
      actual=smallest_phi_third,
      confidence=70,
      note="Рассуждение через формулу Эйлера")

# 12. Действительно сложное: сумма 1/p для простых p до 1000
# Мертенс: сумма ≈ ln(ln(N)) + M, где M ≈ 0.2615
# ln(ln(1000)) = ln(6.908) ≈ 1.933
# Итого ≈ 1.933 + 0.2615 ≈ 2.19

def sieve(n):
    is_p = [True]*(n+1)
    is_p[0]=is_p[1]=False
    for i in range(2,int(n**0.5)+1):
        if is_p[i]:
            for j in range(i*i,n+1,i):
                is_p[j]=False
    return [i for i in range(2,n+1) if is_p[i]]

prime_sum_reciprocal = sum(1/p for p in sieve(1000))
claim("Σ(1/p) для простых p ≤ 1000",
      prediction=2.19,
      actual=round(prime_sum_reciprocal, 2),
      confidence=45,
      note="По теореме Мертенса: ≈ ln(ln(N)) + M")


# === ИТОГ ===
print("=" * 60)
correct = sum(1 for r in results if r["correct"])
total = len(results)
print(f"Результат: {correct}/{total} правильных ({correct/total:.0%})")

# Калибровка: группируем по уверенности
by_confidence = {}
for r in results:
    c = r["confidence"]
    bucket = (c // 20) * 20
    if bucket not in by_confidence:
        by_confidence[bucket] = {"total": 0, "correct": 0}
    by_confidence[bucket]["total"] += 1
    if r["correct"]:
        by_confidence[bucket]["correct"] += 1

print("\nКалибровка (уверенность → точность):")
for bucket in sorted(by_confidence):
    b = by_confidence[bucket]
    pct = b["correct"] / b["total"] * 100
    print(f"  {bucket}-{bucket+19}%: {b['correct']}/{b['total']} = {pct:.0f}%")

wrong = [r for r in results if not r["correct"]]
if wrong:
    print(f"\nОшибки ({len(wrong)}):")
    for r in wrong:
        print(f"  - {r['claim']}: предсказал {r['prediction']}, факт {r['actual']} (уверенность: {r['confidence']}%)")

with open("honesty_test_hard_results.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
