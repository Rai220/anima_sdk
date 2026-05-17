"""
Точная граница коллапса: необходимое и достаточное условие.

v4 установил:
- step_M=4 → OK, step_M=6 → breaks (at row 3: first = M-3)
- alt_2_4 → OK, alt_2_10 → breaks
- Variation rate предсказывает коллапс

Открытые вопросы:
1. Где точная граница для alt_2_M? (M=6? M=8?)
2. Существует ли ЛОКАЛЬНОЕ условие? (напр. "нет окна из k элементов > k")
3. Верно ли, что для коллапса достаточно: max(gap[i:i+w]) уменьшается
   достаточно быстро в окне?

Новый подход: вместо глобальных статистик (variation rate, entropy),
ищем ЛОКАЛЬНЫЙ инвариант, который ломается в точке нарушения.
"""

import json
import math
import random
def sieve_primes(limit):
    """Решето Эратосфена."""
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, limit + 1, i):
                is_prime[j] = False
    return [i for i in range(2, limit + 1) if is_prime[i]]

def abs_diff_row(row):
    return [abs(row[i+1] - row[i]) for i in range(len(row) - 1)]

def collapse_depth(row, max_steps=500):
    r = row[:]
    for d in range(max_steps):
        if len(r) < 2:
            return None
        if max(r) <= 2:
            return d
        r = abs_diff_row(r)
    return None

def gilbreath_violation_depth(seq, max_depth=500):
    row = seq[:]
    for d in range(max_depth):
        if len(row) < 2:
            return None
        row = abs_diff_row(row)
        if row[0] != 1:
            return d + 1
    return None

def gilbreath_trace(seq, max_depth=300):
    """Возвращает (first_elements, max_elements) для каждой строки."""
    row = seq[:]
    firsts = []
    maxes = []
    for d in range(max_depth):
        if len(row) < 2:
            break
        row = abs_diff_row(row)
        firsts.append(row[0])
        maxes.append(max(row))
    return firsts, maxes

def gaps_to_seq(gaps, start=2):
    seq = [start]
    for g in gaps:
        seq.append(seq[-1] + g)
    return seq

def get_primes(n):
    # Оценка верхней границы для n-го простого числа
    if n < 6:
        limit = 15
    else:
        limit = int(n * (math.log(n) + math.log(math.log(n)))) + 100
    primes = sieve_primes(limit)
    while len(primes) < n:
        limit *= 2
        primes = sieve_primes(limit)
    return primes[:n]

def prime_gaps(n):
    primes = get_primes(n)
    return [primes[i+1] - primes[i] for i in range(len(primes) - 1)]

results = {}

# === 1. Точная граница для alt_2_M ===
print("=== 1. Точная граница для alt_2_M ===\n")
L = 200

alt_boundary = {}
for M in range(2, 52, 2):  # только чётные
    gaps = [1, 2] + [2 if i % 2 == 0 else M for i in range(L - 2)]
    seq = gaps_to_seq(gaps)
    cd = collapse_depth(seq, max_steps=500)
    vd = gilbreath_violation_depth(seq, max_depth=500)
    alt_boundary[f"alt_2_{M}"] = {"M": M, "cd": cd, "vd": vd}
    status = "OK" if vd is None else f"BREAKS at depth {vd}"
    print(f"  alt_2_{M:3d}: CD={str(cd):>5s}, VD={str(vd):>5s} → {status}")

results["alt_2_M_boundary"] = alt_boundary

# === 2. Точная граница для alt_A_B ===
print("\n=== 2. Граница для alt_A_B (оба варьируются) ===\n")

alt_AB = {}
for A in [2, 4, 6, 8]:
    for B in range(A, min(A + 30, 52), 2):
        gaps = [1, 2] + [A if i % 2 == 0 else B for i in range(L - 2)]
        seq = gaps_to_seq(gaps)
        vd = gilbreath_violation_depth(seq, max_depth=300)
        cd = collapse_depth(seq, max_steps=300)
        key = f"alt_{A}_{B}"
        alt_AB[key] = {"A": A, "B": B, "cd": cd, "vd": vd}

# Строим карту: для каких (A, B) Гилбрет ломается
print(f"{'A\\B':>5s}", end="")
B_vals = sorted(set(d["B"] for d in alt_AB.values()))
for B in B_vals:
    print(f" {B:3d}", end="")
print()

for A in [2, 4, 6, 8]:
    print(f"{A:5d}", end="")
    for B in B_vals:
        key = f"alt_{A}_{B}"
        if key in alt_AB:
            vd = alt_AB[key]["vd"]
            print(f" {'  .' if vd is None else f'{vd:3d}'}", end="")
        else:
            print(f"    ", end="")
    print()

results["alt_AB_boundary"] = alt_AB

# === 3. Локальное условие: "max в окне" ===
print("\n=== 3. Локальное условие коллапса ===\n")
print("Гипотеза: коллапс происходит когда max(window) < len(window) для всех окон.")
print("Тестируем на разных типах последовательностей.\n")

def max_window_ratio(seq, window_size):
    """max(max(window) / len(window)) по всем окнам данного размера."""
    if len(seq) < window_size:
        return 0
    ratios = []
    for i in range(len(seq) - window_size + 1):
        w = seq[i:i+window_size]
        ratios.append(max(w) / window_size)
    return max(ratios)

def local_density(gaps, window_size):
    """Доля элементов > window_size в каждом окне."""
    if len(gaps) < window_size:
        return 0
    densities = []
    for i in range(len(gaps) - window_size + 1):
        w = gaps[i:i+window_size]
        d = sum(1 for x in w if x > window_size) / window_size
        densities.append(d)
    return max(densities)

# Тест на prime gaps разных размеров
print("Prime gaps:")
local_cond = {}
for N in [100, 500, 1000, 5000, 10000]:
    pg = prime_gaps(N)
    primes = get_primes(N)
    cd = collapse_depth(primes, max_steps=500)
    vd = gilbreath_violation_depth(primes, max_depth=500)

    # Проверяем локальное условие для разных размеров окна
    window_results = {}
    for w in [3, 5, 10, 20, 50]:
        if w < len(pg):
            mwr = max_window_ratio(pg, w)
            ld = local_density(pg, w)
            window_results[w] = {"max_window_ratio": round(mwr, 3), "local_density": round(ld, 3)}

    local_cond[f"primes_{N}"] = {
        "N": N, "max_gap": max(pg), "cd": cd, "vd": vd,
        "window_analysis": window_results
    }
    max_gap = max(pg)
    print(f"  N={N:5d}: max_gap={max_gap:3d}, CD={str(cd):>5s}, VD={str(vd):>5s}")
    for w, wr in window_results.items():
        print(f"    window={w:3d}: max_ratio={wr['max_window_ratio']:.3f}, density={wr['local_density']:.3f}")

results["local_condition_primes"] = local_cond

# Тест на синтетических gaps, которые ломают/не ломают
print("\nСинтетические gaps:")
synthetic_tests = {}

# Gaps с "пиками" разной частоты
for spike_freq in [2, 3, 5, 10, 20]:
    for spike_val in [6, 10, 20, 50]:
        gaps = [1, 2]
        for i in range(2, L):
            if (i - 2) % spike_freq == 0:
                gaps.append(spike_val)
            else:
                gaps.append(2)
        seq = gaps_to_seq(gaps)
        cd = collapse_depth(seq, max_steps=500)
        vd = gilbreath_violation_depth(seq, max_depth=500)
        key = f"spike_f{spike_freq}_v{spike_val}"
        synthetic_tests[key] = {
            "spike_freq": spike_freq,
            "spike_val": spike_val,
            "cd": cd, "vd": vd
        }

# Вывод в виде таблицы
print(f"\n{'freq\\val':>10s}", end="")
for sv in [6, 10, 20, 50]:
    print(f" {sv:5d}", end="")
print()
for sf in [2, 3, 5, 10, 20]:
    print(f"{sf:10d}", end="")
    for sv in [6, 10, 20, 50]:
        key = f"spike_f{sf}_v{sv}"
        vd = synthetic_tests[key]["vd"]
        print(f" {'   OK' if vd is None else f'{vd:5d}'}", end="")
    print()

results["synthetic_spikes"] = synthetic_tests

# === 4. КРИТИЧЕСКИЙ ТЕСТ: что делает abs-diff с первым элементом? ===
print("\n=== 4. Механизм первого элемента ===\n")
print("Отслеживаем first element через строки для разных типов gaps.\n")

mechanism = {}

test_cases = {
    "primes_200": get_primes(200),
    "step_4": gaps_to_seq([1, 2] + [4] * 198),
    "step_10": gaps_to_seq([1, 2] + [10] * 198),
    "alt_2_6": gaps_to_seq([1, 2] + [2 if i % 2 == 0 else 6 for i in range(198)]),
    "alt_2_10": gaps_to_seq([1, 2] + [2 if i % 2 == 0 else 10 for i in range(198)]),
    "spike_f5_v10": gaps_to_seq([1, 2] + [10 if (i % 5 == 0) else 2 for i in range(198)]),
}

for name, seq in test_cases.items():
    firsts, maxes = gilbreath_trace(seq, max_depth=50)
    mechanism[name] = {
        "firsts_20": firsts[:20],
        "maxes_20": maxes[:20],
        "first_violation": next((i+1 for i, f in enumerate(firsts) if f != 1), None)
    }
    print(f"  {name:20s}: firsts = {firsts[:15]}")
    print(f"  {'':20s}  maxes = {maxes[:15]}")
    fv = mechanism[name]["first_violation"]
    print(f"  {'':20s}  first violation at row: {fv}")
    print()

results["mechanism"] = mechanism

# === 5. НОВОЕ: переходная динамика ===
print("=== 5. Переходная динамика: row-by-row распределение значений ===\n")
print("Как распределение значений в строке меняется при итерации abs-diff?\n")

def row_distribution(row, M):
    """Частоты значений 0..M в строке."""
    from collections import Counter
    c = Counter(row)
    total = len(row)
    return {k: round(c[k]/total, 4) for k in range(M+1) if c[k] > 0}

transition = {}
for name, seq in [("primes_500", get_primes(500)),
                   ("step_10", gaps_to_seq([1, 2] + [10] * 498))]:
    row = seq[:]
    steps = []
    for d in range(min(30, len(row) - 1)):
        if len(row) < 2:
            break
        row = abs_diff_row(row)
        m = max(row)
        unique = len(set(row))
        frac_01 = sum(1 for x in row if x <= 1) / len(row)
        frac_012 = sum(1 for x in row if x <= 2) / len(row)
        steps.append({
            "depth": d + 1,
            "max": m,
            "unique_values": unique,
            "frac_01": round(frac_01, 4),
            "frac_012": round(frac_012, 4),
            "first": row[0],
            "len": len(row)
        })
    transition[name] = steps

    print(f"  {name}:")
    print(f"  {'depth':>5s} {'max':>5s} {'uniq':>5s} {'%≤1':>6s} {'%≤2':>6s} {'first':>5s}")
    for s in steps[:20]:
        print(f"  {s['depth']:5d} {s['max']:5d} {s['unique_values']:5d} {s['frac_01']:6.3f} {s['frac_012']:6.3f} {s['first']:5d}")
    print()

results["transition_dynamics"] = transition

# === 6. КЛЮЧЕВОЙ ТЕСТ: достаточное условие через "first row formula" ===
print("=== 6. Алгебра первого элемента ===\n")
print("Row 1: first = |p2 - p1| - |p3 - p2| + ... (знакочередующаяся сумма gaps)")
print("Для gaps [g0, g1, g2, ...], first@row_k зависит от g0..g_k.\n")

# Вычислим first@row_k аналитически для разных паттернов
def compute_first_algebraic(gaps, depth):
    """Вычисляем first element на глубине depth аналитически через seq."""
    seq = gaps_to_seq(gaps[:depth + 2])  # нужно depth+2 элементов
    row = seq[:]
    for d in range(depth):
        row = abs_diff_row(row)
        if len(row) < 1:
            return None
    return row[0] if row else None

print("Зависимость first@row_k от k-го gap для [1, 2, g2, g2, g2, ...]:")
algebra_results = {}
for M in range(2, 22, 2):
    firsts_by_depth = []
    for k in range(1, 12):
        gaps = [1, 2] + [M] * k
        f = compute_first_algebraic(gaps, k)
        firsts_by_depth.append(f)
    algebra_results[f"const_{M}"] = firsts_by_depth
    print(f"  M={M:3d}: firsts@rows 1..11 = {firsts_by_depth}")

results["first_element_algebra"] = algebra_results

# Формула для первого элемента
print("\nПоиск формулы: first@row_k для constant gaps M, начало [1,2,M,M,...]")
print("Row 1: |2-1|=1, |M-2|=M-2, → first=1")
print("Row 2: ||M-2|-1| = M-3 или 3-M. Для M≥4: first=M-3")
print("Row 3: зависит от M-3 и следующих...")

# Проверим формулу
print("\nВерификация формулы first@row2 = |M-3|:")
for M in range(2, 22, 2):
    gaps = [1, 2] + [M] * 10
    seq = gaps_to_seq(gaps)
    row = seq[:]
    for _ in range(2):
        row = abs_diff_row(row)
    predicted = abs(M - 3)
    actual = row[0]
    match = "✓" if predicted == actual else "✗"
    print(f"  M={M:3d}: predicted={predicted:3d}, actual={actual:3d} {match}")

results["formula_verification"] = {
    f"M={M}": {"predicted": abs(M-3), "actual": compute_first_algebraic([1,2]+[M]*10, 2)}
    for M in range(2, 22, 2)
}

# === 7. Обобщённая формула ===
print("\n=== 7. Row-k first element как функция gaps ===\n")

# Для gaps = [1, 2, g, g, g, ...], выпишем first@row_k для k=1..5
# и попробуем найти закономерность
print("Для constant gap g, first@row_k:")
print(f"{'g':>5s}", end="")
for k in range(1, 8):
    print(f" {'R'+str(k):>5s}", end="")
print()

for g in range(2, 22, 2):
    print(f"{g:5d}", end="")
    gaps = [1, 2] + [g] * 20
    for k in range(1, 8):
        f = compute_first_algebraic(gaps, k)
        print(f" {f:5d}" if f is not None else f" {'?':>5s}", end="")
    print()

# Сохраняем
with open("collapse_boundary_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print("\n\nРезультаты сохранены в collapse_boundary_results.json")
