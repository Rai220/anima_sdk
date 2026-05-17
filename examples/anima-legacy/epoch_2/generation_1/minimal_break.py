"""
Минимальное возмущение: какая наименьшая модификация prime gaps ломает Гилбрета?

Парадокс из collapse_boundary.py:
- Периодические gaps [1,2,6,2,2,...] ломают Гилбрета на depth 3
- Реальные prime gaps имеют 6 (и больше) и НЕ ломаются
- Значит контекст gap критичен

Эксперимент:
1. Берём реальные prime gaps
2. Заменяем ОДИН gap на другое значение
3. Находим минимальное возмущение, ломающее Гилбрета
4. Анализируем: КАКИЕ позиции чувствительны, а какие нет?
"""

import json
import math
from collections import Counter

def sieve_primes(limit):
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, limit + 1, i):
                is_prime[j] = False
    return [i for i in range(2, limit + 1) if is_prime[i]]

def get_primes(n):
    if n < 6:
        limit = 15
    else:
        limit = int(n * (math.log(n) + math.log(math.log(n)))) + 100
    primes = sieve_primes(limit)
    while len(primes) < n:
        limit *= 2
        primes = sieve_primes(limit)
    return primes[:n]

def abs_diff_row(row):
    return [abs(row[i+1] - row[i]) for i in range(len(row) - 1)]

def gilbreath_violation_depth(seq, max_depth=500):
    row = seq[:]
    for d in range(max_depth):
        if len(row) < 2:
            return None
        row = abs_diff_row(row)
        if row[0] != 1:
            return d + 1
    return None

def collapse_depth(row, max_steps=500):
    r = row[:]
    for d in range(max_steps):
        if len(r) < 2:
            return None
        if max(r) <= 2:
            return d
        r = abs_diff_row(r)
    return None

def gaps_to_seq(gaps, start=2):
    seq = [start]
    for g in gaps:
        seq.append(seq[-1] + g)
    return seq

results = {}

# === 1. Однопозиционные возмущения ===
print("=== 1. Минимальное возмущение: замена одного gap ===\n")

N = 200
primes = get_primes(N)
real_gaps = [primes[i+1] - primes[i] for i in range(len(primes) - 1)]

print(f"Первые 30 prime gaps: {real_gaps[:30]}")
print(f"Max gap: {max(real_gaps)}, N={N}\n")

# Для каждой позиции, пробуем заменить gap на разные значения
# и находим минимальное значение, при котором Гилбрет ломается

sensitive_positions = []
print(f"{'pos':>4s} {'orig':>5s} {'min_break':>9s} {'break_val':>9s} {'context':>30s}")

single_perturbation = {}
for pos in range(2, min(50, len(real_gaps))):  # начинаем с 2 (после [1,2,...])
    orig = real_gaps[pos]
    min_break_val = None

    for test_val in range(2, 102, 2):  # только чётные (gaps > 1 чётные)
        if test_val == orig:
            continue
        modified = real_gaps[:len(real_gaps)]
        modified[pos] = test_val
        seq = gaps_to_seq(modified)
        vd = gilbreath_violation_depth(seq, max_depth=100)
        if vd is not None:
            min_break_val = test_val
            break

    context = real_gaps[max(0,pos-2):pos+3]
    single_perturbation[pos] = {
        "original": orig,
        "min_break": min_break_val,
        "context": context
    }

    if min_break_val is not None:
        sensitive_positions.append(pos)
        print(f"{pos:4d} {orig:5d} {min_break_val:9d} {'SENSITIVE':>9s} {str(context):>30s}")
    else:
        print(f"{pos:4d} {orig:5d} {'none':>9s} {'ROBUST':>9s} {str(context):>30s}")

results["single_perturbation"] = single_perturbation

# === 2. Статистика чувствительности ===
print(f"\n=== 2. Статистика чувствительности ===\n")
n_sensitive = len(sensitive_positions)
n_total = min(50, len(real_gaps)) - 2
print(f"Чувствительных позиций: {n_sensitive}/{n_total} ({100*n_sensitive/n_total:.1f}%)")

# Какие min_break значения наиболее частые?
break_vals = [single_perturbation[p]["min_break"] for p in sensitive_positions if single_perturbation[p]["min_break"] is not None]
if break_vals:
    print(f"Распределение min_break: {Counter(break_vals).most_common()}")
    print(f"Медиана min_break: {sorted(break_vals)[len(break_vals)//2]}")

# Связь с оригинальным gap value
print(f"\nЧувствительность vs оригинальный gap:")
for pos in sensitive_positions[:10]:
    d = single_perturbation[pos]
    ratio = d["min_break"] / d["original"] if d["original"] > 0 else None
    print(f"  pos={pos}: orig={d['original']}, min_break={d['min_break']}, ratio={ratio:.2f}" if ratio else f"  pos={pos}: orig={d['original']}, min_break={d['min_break']}")

results["sensitivity_stats"] = {
    "n_sensitive": n_sensitive,
    "n_total": n_total,
    "fraction": n_sensitive / n_total
}

# === 3. Двойные возмущения ===
print(f"\n=== 3. Двойные возмущения: насколько сильнее? ===\n")

# Берём пары позиций и пробуем минимальные возмущения
double_perturb = {}
for pos1 in range(2, 12):
    for pos2 in range(pos1 + 1, min(pos1 + 6, 15)):
        for val in range(2, 52, 2):
            modified = real_gaps[:]
            modified[pos1] = val
            modified[pos2] = val
            seq = gaps_to_seq(modified)
            vd = gilbreath_violation_depth(seq, max_depth=100)
            if vd is not None:
                key = f"({pos1},{pos2})"
                double_perturb[key] = {"pos1": pos1, "pos2": pos2, "min_break": val, "vd": vd}
                break

print(f"{'positions':>12s} {'min_break':>9s} {'vd':>4s}")
for key, d in sorted(double_perturb.items(), key=lambda x: x[1]["min_break"])[:15]:
    print(f"{key:>12s} {d['min_break']:9d} {d['vd']:4d}")

results["double_perturbation"] = double_perturb

# === 4. КЛЮЧЕВОЙ ТЕСТ: какой инвариант отличает настоящие простые? ===
print(f"\n=== 4. Инвариант: кумулятивные разности ===\n")
print("Для каждой позиции: S(k) = Σ(-1)^i * gap[i] для i=0..k")
print("Гипотеза: |S(k)| ≤ 1 для всех k ⟺ Гилбрет выполняется\n")

# Знакочередующаяся сумма gaps
def alternating_sum(gaps, k):
    s = 0
    for i in range(k + 1):
        s += (-1)**i * gaps[i]
    return s

def all_partial_alternating_sums(gaps):
    sums = []
    s = 0
    for i, g in enumerate(gaps):
        s += (-1)**i * g
        sums.append(s)
    return sums

print("Prime gaps — знакочередующиеся суммы:")
alt_sums = all_partial_alternating_sums(real_gaps)
print(f"  Первые 30: {alt_sums[:30]}")
print(f"  Max |S(k)|: {max(abs(s) for s in alt_sums)}")
print(f"  Доля |S(k)|≤1: {sum(1 for s in alt_sums if abs(s) <= 1)/len(alt_sums):.3f}")
print(f"  Доля |S(k)|≤2: {sum(1 for s in alt_sums if abs(s) <= 2)/len(alt_sums):.3f}")

results["alternating_sums_primes"] = {
    "first_30": alt_sums[:30],
    "max_abs": max(abs(s) for s in alt_sums),
    "frac_le1": sum(1 for s in alt_sums if abs(s) <= 1)/len(alt_sums),
    "frac_le2": sum(1 for s in alt_sums if abs(s) <= 2)/len(alt_sums),
}

# Сравнение с ломающейся последовательностью
print(f"\nalt_2_6 — знакочередующиеся суммы:")
alt_gaps = [1, 2] + [2 if i % 2 == 0 else 6 for i in range(98)]
alt_sums_26 = all_partial_alternating_sums(alt_gaps)
print(f"  Первые 30: {alt_sums_26[:30]}")
print(f"  Max |S(k)|: {max(abs(s) for s in alt_sums_26)}")

# === 5. Более глубокий инвариант: abs-diff на первых k элементах ===
print(f"\n=== 5. Abs-diff треугольник: первый столбец ===\n")
print("Точное вычисление first@row_k для первых k gaps.\n")

# first@row_k — это определённая комбинация первых k+1 элементов seq
# Для прайм: first всегда 1. Почему?

# Вычислим first@row_k через рекурсию
def first_column(seq, depth):
    """Возвращает первый элемент каждой строки abs-diff треугольника."""
    firsts = [seq[0]]
    row = seq[:]
    for d in range(depth):
        if len(row) < 2:
            break
        row = abs_diff_row(row)
        firsts.append(row[0])
    return firsts

print("Прайм — первый столбец:")
fc_primes = first_column(primes, 30)
print(f"  {fc_primes[:31]}")

print(f"\nalt_2_6 — первый столбец:")
seq_26 = gaps_to_seq(alt_gaps)
fc_26 = first_column(seq_26, 30)
print(f"  {fc_26[:31]}")

print(f"\nalt_2_4 — первый столбец:")
alt_gaps_24 = [1, 2] + [2 if i % 2 == 0 else 4 for i in range(98)]
seq_24 = gaps_to_seq(alt_gaps_24)
fc_24 = first_column(seq_24, 30)
print(f"  {fc_24[:31]}")

# === 6. Конусы влияния ===
print(f"\n=== 6. Конус влияния: сколько начальных элементов определяют first@row_k? ===\n")
print("first@row_k зависит от seq[0..k]. Изменение seq[k+1] не влияет на first@row_k.\n")

# Проверим: для first@row_k, зависит ли он ТОЛЬКО от seq[0..k]?
print("Проверка: first@row_k определяется ТОЛЬКО первыми k+1 элементами?")
for k in range(1, 15):
    # Берём первые k+1 прайм и добавляем разные хвосты
    prefix = primes[:k+1]
    results_k = set()
    for trial in range(20):
        suffix = [prefix[-1] + 2*i + 2 for i in range(50)]
        test_seq = prefix + suffix
        fc = first_column(test_seq, k)
        results_k.add(fc[k])

    all_same = len(results_k) == 1
    print(f"  k={k:2d}: {'ДА' if all_same else 'НЕТ'} (values: {results_k})")

# === 7. ГЛАВНЫЙ РЕЗУЛЬТАТ: abs-diff первого столбца как функция ===
print(f"\n=== 7. Рекурсивная структура first@row_k ===\n")

# first@row_1 = |p1 - p0| = |3 - 2| = 1
# first@row_2 = ||p2-p1| - |p1-p0|| = ||5-3| - |3-2|| = |2-1| = 1
# first@row_k = f(first@row_{k-1}, second@row_{k-1})
# = |second@row_{k-1} - first@row_{k-1}|

# Но second@row_k тоже зависит от начальных элементов!
# Отследим first И second для прайм

def first_two_column(seq, depth):
    """Первые два элемента каждой строки."""
    pairs = [(seq[0], seq[1] if len(seq) > 1 else None)]
    row = seq[:]
    for d in range(depth):
        if len(row) < 2:
            break
        row = abs_diff_row(row)
        pairs.append((row[0], row[1] if len(row) > 1 else None))
    return pairs

print("Прайм — (first, second) по строкам:")
pairs = first_two_column(primes, 20)
for i, (f, s) in enumerate(pairs[:21]):
    print(f"  Row {i:2d}: first={f}, second={s}, |s-f|={abs(s-f) if s is not None else '?'}")

print(f"\nalt_2_6 — (first, second) по строкам:")
pairs_26 = first_two_column(seq_26, 20)
for i, (f, s) in enumerate(pairs_26[:21]):
    print(f"  Row {i:2d}: first={f}, second={s}, |s-f|={abs(s-f) if s is not None else '?'}")

# === 8. Необходимое условие: first=1 ⟹ |second - first| = 1 OR second = 0 ===
print(f"\n=== 8. Необходимое условие для устойчивости first=1 ===\n")
print("Если first@row_k = 1, то first@row_{k+1} = |second@row_k - 1|.")
print("Чтобы first@row_{k+1} = 1, нужно second@row_k ∈ {0, 2}.\n")

print("Проверка на прайм:")
stable_count = 0
for i, (f, s) in enumerate(pairs[:20]):
    if f == 1 and s is not None:
        next_first = abs(s - f)
        needed = s in (0, 2)
        if needed:
            stable_count += 1
        print(f"  Row {i:2d}: second={s}, |second-1|={abs(s-1)}, next_first={next_first}, second∈{{0,2}}: {'✓' if needed else '✗'}")

print(f"\nPrime: second ∈ {{0,2}} в {stable_count}/19 случаях")

print("\nПроверка на alt_2_6:")
for i, (f, s) in enumerate(pairs_26[:15]):
    if s is not None:
        next_first = abs(s - f)
        print(f"  Row {i:2d}: first={f}, second={s}, next_first={abs(s-f)}")

results["first_two_columns"] = {
    "primes": [(f, s) for f, s in pairs[:21]],
    "alt_2_6": [(f, s) for f, s in pairs_26[:21]]
}

# Сохраняем
with open("minimal_break_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print("\n\nРезультаты сохранены в minimal_break_results.json")
