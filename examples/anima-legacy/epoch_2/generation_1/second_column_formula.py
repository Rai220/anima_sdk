"""
Цель: найти явную формулу для second@row_k в abs-diff треугольнике простых.

second@row_k — второй элемент k-й строки.
Гилбрет ⟺ second@row_k ∈ {0,2} для всех k.

Вопрос 1: Чему ТОЧНО равен second@row_k как функция gaps?
Вопрос 2: Есть ли закономерность в чередовании 0 и 2?
Вопрос 3: Связь min_break(pos) со структурой second column?
"""

import json
import math

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

def get_triangle_element(seq, row, col):
    """Получить элемент (row, col) abs-diff треугольника."""
    current = seq[:]
    for _ in range(row):
        if len(current) < 2:
            return None
        current = abs_diff_row(current)
    if col >= len(current):
        return None
    return current[col]

results = {}

# === 1. Вычислить second column для большого N ===
print("=== 1. Second column: second@row_k для N=2000 простых ===\n")

N = 2000
primes = get_primes(N)
gaps = [primes[i+1] - primes[i] for i in range(len(primes) - 1)]

# Строим second column итеративно (эффективнее чем пересчёт треугольника)
# row_0 = primes, second@row_0 = primes[1] = 3
# row_1 = gaps, second@row_1 = gaps[1]
# row_k+1[i] = |row_k[i+1] - row_k[i]|

row = primes[:]
second_col = []
first_col = []

max_rows = min(500, N - 1)
for k in range(max_rows):
    if len(row) < 2:
        break
    first_col.append(row[0])
    second_col.append(row[1] if len(row) > 1 else None)
    row = abs_diff_row(row)

print(f"Вычислено {len(second_col)} строк second column")
print(f"\nПервые 30 значений second@row_k:")
for k in range(min(30, len(second_col))):
    print(f"  row {k:3d}: first={first_col[k]:5d}, second={second_col[k]:5d}")

# === 2. Статистика second column (начиная с row 1, т.к. row 0 — это сами простые) ===
print(f"\n=== 2. Статистика second@row_k для k >= 1 ===\n")

# row_0 = primes (first=2, second=3)
# row_1 = gaps (first=1, second=gaps[1])
# row_k для k>=1 — это где Гилбрет действует

sc_from_1 = second_col[1:]  # начиная с row_1

values = set(sc_from_1)
print(f"Уникальные значения second@row_k (k≥1): {sorted(values)}")

count_0 = sc_from_1.count(0)
count_2 = sc_from_1.count(2)
other = len(sc_from_1) - count_0 - count_2
print(f"  count(0) = {count_0}")
print(f"  count(2) = {count_2}")
print(f"  other = {other}")

if other > 0:
    print(f"  НАРУШЕНИЯ: {[(k+1, sc_from_1[k]) for k in range(len(sc_from_1)) if sc_from_1[k] not in (0, 2)]}")
else:
    print(f"  Подтверждено: second ∈ {{0,2}} для всех {len(sc_from_1)} строк")

results["second_column_stats"] = {
    "n_rows": len(sc_from_1),
    "count_0": count_0,
    "count_2": count_2,
    "other": other,
    "unique_values": sorted(values)
}

# === 3. Паттерн 0/2 — есть ли закономерность? ===
print(f"\n=== 3. Паттерн 0/2 в second column ===\n")

# Кодируем: 0 -> 0, 2 -> 1
binary = [1 if s == 2 else 0 for s in sc_from_1]

# Частоты пар
pairs = {}
for i in range(len(binary) - 1):
    p = (binary[i], binary[i+1])
    pairs[p] = pairs.get(p, 0) + 1
print(f"Частоты пар (0→0, 0→1, 1→0, 1→1):")
for p in [(0,0), (0,1), (1,0), (1,1)]:
    print(f"  {p}: {pairs.get(p, 0)}")

# Частоты троек
triples = {}
for i in range(len(binary) - 2):
    t = (binary[i], binary[i+1], binary[i+2])
    triples[t] = triples.get(t, 0) + 1
print(f"\nЧастоты троек:")
for t in sorted(triples.keys()):
    print(f"  {t}: {triples[t]}")

# Run lengths (длины серий одинаковых)
runs = []
current_val = binary[0]
current_len = 1
for i in range(1, len(binary)):
    if binary[i] == current_val:
        current_len += 1
    else:
        runs.append((current_val, current_len))
        current_val = binary[i]
        current_len = 1
runs.append((current_val, current_len))

run_lengths_0 = [r[1] for r in runs if r[0] == 0]
run_lengths_1 = [r[1] for r in runs if r[0] == 1]
print(f"\nДлины серий '0': min={min(run_lengths_0)}, max={max(run_lengths_0)}, mean={sum(run_lengths_0)/len(run_lengths_0):.2f}")
print(f"Длины серий '2': min={min(run_lengths_1)}, max={max(run_lengths_1)}, mean={sum(run_lengths_1)/len(run_lengths_1):.2f}")

results["pattern_analysis"] = {
    "pairs": {str(k): v for k, v in pairs.items()},
    "run_lengths_0": {"min": min(run_lengths_0), "max": max(run_lengths_0), "mean": round(sum(run_lengths_0)/len(run_lengths_0), 3)},
    "run_lengths_2": {"min": min(run_lengths_1), "max": max(run_lengths_1), "mean": round(sum(run_lengths_1)/len(run_lengths_1), 3)}
}

# === 4. КЛЮЧЕВОЙ ВОПРОС: second@row_k через gaps ===
print(f"\n=== 4. Формула: second@row_k как функция gaps ===\n")

# row_0 = [p_0, p_1, p_2, ...]
# row_1 = [g_0, g_1, g_2, ...] = [|p1-p0|, |p2-p1|, ...]
# row_1[1] = g_1 = p_2 - p_1
# row_2[0] = |g_1 - g_0|, row_2[1] = |g_2 - g_1|
# row_3[0] = ||g_2-g_1| - |g_1-g_0||, row_3[1] = ||g_3-g_2| - |g_2-g_1||

# Гипотеза: second@row_k зависит от g_1, g_2, ..., g_k
# Проверим: second@row_k зависит от КАКИХ ИМЕННО gaps?

# Для row_k (k >= 1):
# row_k[1] зависит от row_{k-1}[1] и row_{k-1}[2]
# Индуктивно: row_k[1] зависит от row_0[1..k+1] = primes[1..k+1]
# То есть от gaps[0..k]

# Проверим это: вычислим second@row_k из подпоследовательности gaps[0..k]
print("Проверка: second@row_k зависит только от gaps[0..k]?")

row_full = gaps[:]
row_truncated_results = []
mismatches = 0

for k in range(1, min(100, len(gaps))):
    # Полное вычисление
    row_f = gaps[:]
    for _ in range(k):
        row_f = abs_diff_row(row_f)
    second_full = row_f[1] if len(row_f) > 1 else None

    # Из усечённой последовательности gaps[0..k+1]
    row_t = gaps[:k+2]  # k+2 элементов хватит для 1 шага row_k
    for _ in range(k):
        row_t = abs_diff_row(row_t)
    second_trunc = row_t[1] if len(row_t) > 1 else None

    if second_full != second_trunc:
        mismatches += 1
        print(f"  MISMATCH at row {k}: full={second_full}, trunc={second_trunc}")

if mismatches == 0:
    print(f"  Подтверждено: second@row_k зависит только от gaps[0..k+1] (99 строк проверено)")

# === 5. Рекурсия для second column ===
print(f"\n=== 5. Рекурсия для second column ===\n")

# row_{k+1}[1] = |row_k[2] - row_k[1]|
# Нам нужно знать row_k[1] (= second@row_k) и row_k[2] (= third@row_k)
# Значит second column удовлетворяет:
# second@row_{k+1} = |third@row_k - second@row_k|
# Это замкнуто только если мы знаем third column тоже.

# Но мы можем вычислить third column
third_col = []
row = primes[:]
for k in range(max_rows):
    if len(row) > 2:
        third_col.append(row[2])
    else:
        break
    row = abs_diff_row(row)

print(f"Рекурсия: second@row_{{k+1}} = |third@row_k - second@row_k|")
print(f"\nПроверка на 30 строках:")
verified = 0
for k in range(min(30, len(second_col) - 1, len(third_col))):
    expected = abs(third_col[k] - second_col[k])
    actual = second_col[k+1] if k+1 < len(second_col) else None
    ok = "OK" if expected == actual else "FAIL"
    if k < 15:
        print(f"  row {k:3d}: |third({third_col[k]}) - second({second_col[k]})| = {expected}, actual second@{k+1} = {actual} [{ok}]")
    if expected == actual:
        verified += 1

print(f"\nВерифицировано: {verified}/{min(30, len(second_col)-1)}")

# === 6. НОВЫЙ ВОПРОС: third column — тоже ограничена? ===
print(f"\n=== 6. Third column: third@row_k для k >= 1 ===\n")

tc_from_1 = third_col[1:]
tc_values = sorted(set(tc_from_1))
print(f"Уникальные значения third@row_k (k≥1): {tc_values[:30]}{'...' if len(tc_values) > 30 else ''}")
print(f"Количество уникальных: {len(tc_values)}")
print(f"max = {max(tc_from_1)}, min = {min(tc_from_1)}")

# Если second ∈ {0,2} и second_{k+1} = |third_k - second_k|, то:
# |third_k - second_k| ∈ {0,2}
# Значит third_k ∈ {second_k-2, second_k, second_k+2}
# Если second_k ∈ {0,2}, то third_k ∈ {-2,0,2,4} ∩ Z_≥0 = {0,2,4}
# НО third_k — это abs-diff, значит ≥ 0

print(f"\nСледствие: если second ∈ {{0,2}} и second_{{k+1}} = |third_k - second_k|,")
print(f"то third_k ∈ {{0, 2, 4}}")
print(f"\nПроверка: third@row_k ∈ {{0,2,4}} для k≥1?")
tc_in_024 = sum(1 for t in tc_from_1 if t in (0, 2, 4))
tc_not_024 = sum(1 for t in tc_from_1 if t not in (0, 2, 4))
print(f"  В {{0,2,4}}: {tc_in_024}")
print(f"  Вне {{0,2,4}}: {tc_not_024}")
if tc_not_024 > 0:
    violations = [(k+1, tc_from_1[k]) for k in range(len(tc_from_1)) if tc_from_1[k] not in (0, 2, 4)]
    print(f"  Нарушения (первые 10): {violations[:10]}")

results["third_column"] = {
    "unique_values": tc_values[:50],
    "n_in_024": tc_in_024,
    "n_not_024": tc_not_024
}

# === 7. Fourth, fifth... columns — каскад ограничений? ===
print(f"\n=== 7. Каскад: col_j@row_k — какие значения возможны? ===\n")

# Гипотеза: col_j@row_k ∈ {0, 2, 4, ..., 2j} для k достаточно большого?
# Это было бы ОЧЕНЬ сильный результат.

columns = {}
max_col = 8
row = primes[:]
for k in range(max_rows):
    for j in range(min(max_col, len(row))):
        if j not in columns:
            columns[j] = []
        columns[j].append(row[j])
    if len(row) < 2:
        break
    row = abs_diff_row(row)

print(f"{'col':>5s} {'unique_vals (k>=5)':>60s} {'max':>5s}")
cascade_data = {}
for j in range(max_col):
    vals = columns[j][5:]  # skip first 5 rows (transient)
    unique = sorted(set(vals))
    cascade_data[j] = {
        "unique": unique[:20],
        "n_unique": len(unique),
        "max": max(vals) if vals else 0,
        "expected_max": 2*j
    }
    u_str = str(unique[:15])
    if len(unique) > 15:
        u_str += f"... ({len(unique)} total)"
    print(f"  {j:3d}   {u_str:>60s}   {max(vals) if vals else 0:5d}")

results["cascade"] = cascade_data

# === 8. Проверка гипотезы: col_j values ⊆ {0, 2, 4, ..., 2j}? ===
print(f"\n=== 8. Гипотеза: col_j@row_k ∈ {{0, 2, ..., 2j}} для k ≥ j+1? ===\n")

for j in range(max_col):
    vals = columns[j][j+1:]  # начиная с row j+1
    expected = set(range(0, 2*j + 1, 2))  # {0, 2, 4, ..., 2j}
    actual = set(vals)
    contained = actual.issubset(expected)
    extra = actual - expected
    print(f"  col {j}: expected ⊆ {sorted(expected)}, actual unique = {sorted(actual)[:10]}, contained = {contained}")
    if extra:
        print(f"         extra values: {sorted(extra)[:10]}")

# === 9. Переход min_break: структурная причина ===
print(f"\n=== 9. Почему min_break растёт? Анализ глубины нарушения ===\n")

# Когда мы подставляем большой gap в позицию pos, на КАКОЙ глубине ломается first=1?
# Гипотеза: глубина нарушения = pos (или пропорциональна pos)

def gilbreath_violation_info(seq, max_depth=500):
    """Возвращает (depth, second_value) первого нарушения."""
    row = seq[:]
    for d in range(max_depth):
        if len(row) < 2:
            return None
        row = abs_diff_row(row)
        if row[0] != 1:
            return (d + 1, row[0], row[1] if len(row) > 1 else None)
    return None

def gaps_to_seq(gaps_list, start=2):
    seq = [start]
    for g in gaps_list:
        seq.append(seq[-1] + g)
    return seq

N_small = 500
primes_s = get_primes(N_small)
gaps_s = [primes_s[i+1] - primes_s[i] for i in range(len(primes_s) - 1)]

print(f"{'pos':>5s} {'break_val':>9s} {'depth':>6s} {'first@depth':>11s} {'second@depth':>12s}")
depth_data = []
for pos in range(2, min(80, len(gaps_s)), 3):
    # Находим минимальный ломающий gap
    for val in range(2, 302, 2):
        modified = gaps_s[:]
        modified[pos] = val
        seq = gaps_to_seq(modified)
        info = gilbreath_violation_info(seq, max_depth=300)
        if info is not None:
            depth, first_val, second_val = info
            depth_data.append({"pos": pos, "break_val": val, "depth": depth, "first": first_val, "second": second_val})
            if pos % 6 == 2 or pos < 15:
                print(f"{pos:5d} {val:9d} {depth:6d} {first_val:11d} {str(second_val):>12s}")
            break

# Корреляция depth vs pos
if depth_data:
    depths = [d["depth"] for d in depth_data]
    positions = [d["pos"] for d in depth_data]

    # Простая корреляция
    n = len(depths)
    mean_d = sum(depths) / n
    mean_p = sum(positions) / n
    cov = sum((d - mean_d) * (p - mean_p) for d, p in zip(depths, positions)) / n
    std_d = (sum((d - mean_d)**2 for d in depths) / n) ** 0.5
    std_p = (sum((p - mean_p)**2 for p in positions) / n) ** 0.5
    corr = cov / (std_d * std_p) if std_d > 0 and std_p > 0 else 0

    print(f"\nКорреляция depth vs pos: {corr:.4f}")
    print(f"Среднее depth/pos: {sum(d/p for d,p in zip(depths, positions))/len(depths):.3f}")

results["depth_analysis"] = depth_data

# === 10. Главная новая гипотеза ===
print(f"\n=== 10. ОБОБЩЕНИЕ: теорема о каскаде ===\n")

print("""
ГИПОТЕЗА (каскад ограничений в abs-diff треугольнике простых):

Для простых чисел p_0, p_1, p_2, ..., пусть T[k][j] — элемент
(строка k, столбец j) abs-diff треугольника.

Тогда для достаточно большого k:
  T[k][j] ∈ {0, 2, 4, ..., 2j}

В частности:
  j=0: T[k][0] ∈ {0} ∪ {1}  — но мы знаем T[k][0] = 1 (Гилбрет)
  j=1: T[k][1] ∈ {0, 2}      — наш second column результат
  j=2: T[k][2] ∈ {0, 2, 4}   — third column
  j=3: T[k][3] ∈ {0, 2, 4, 6}
  ...

Если это верно, это ЭКВИВАЛЕНТНО утверждению, что КАЖДЫЙ столбец
abs-diff треугольника ограничен.

Более того: Гилбрет (j=0) — лишь ЧАСТНЫЙ СЛУЧАЙ этого каскада.
""")

# Сохраняем
with open("second_column_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print("Результаты сохранены в second_column_results.json")
