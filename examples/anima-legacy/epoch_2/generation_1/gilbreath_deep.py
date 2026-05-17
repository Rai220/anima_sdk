"""
gilbreath_deep.py — generation_1 v10

Три задачи, которые v9 не могла решить:

1. МАСШТАБ: N=100000 простых, верификация {0,2} collapse на 50 столбцах × 5000+ строк
2. АНОМАЛИИ: полный скан pos=2..4999 — сколько аномалий, все ли first=5, появится ли first=7?
3. АНАТОМИЯ first=5: ЧТО делает позицию аномальной?

Оптимизация: numpy для треугольника, bytearray для решета.
"""

import json
import math
import time
import sys

# =============================================================================
# Утилиты
# =============================================================================

def sieve_primes(limit):
    """Решето Эратосфена, bytearray для скорости."""
    is_prime = bytearray(b'\x01') * (limit + 1)
    is_prime[0] = is_prime[1] = 0
    for i in range(2, int(limit**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, limit + 1, i):
                is_prime[j] = 0
    return [i for i in range(2, limit + 1) if is_prime[i]]

def get_primes(n):
    if n < 6:
        limit = 15
    else:
        limit = int(n * (math.log(n) + math.log(math.log(n)))) + 100
    primes = sieve_primes(limit)
    while len(primes) < n:
        limit = int(limit * 1.5)
        primes = sieve_primes(limit)
    return primes[:n]

def abs_diff_row(row):
    return [abs(row[i+1] - row[i]) for i in range(len(row) - 1)]

# =============================================================================
# ЧАСТЬ 1: Верификация {0,2} collapse при N=100000
# =============================================================================
print("=" * 70)
print("ЧАСТЬ 1: Верификация {0,2} collapse — N=100000, 100 столбцов")
print("=" * 70)

t0 = time.time()

N = 100000
print(f"Генерация {N} простых...")
primes = get_primes(N)
print(f"  Готово за {time.time()-t0:.1f}s. Max prime = {primes[-1]}")

gaps = [primes[i+1] - primes[i] for i in range(len(primes) - 1)]
max_gap = max(gaps)
print(f"  Max gap = {max_gap}")

# Строим треугольник: храним только столбцы 0..99 для каждой строки
MAX_COL = 100
MAX_ROW = 6000  # сколько строк abs-diff можем построить
TRANSIENT = 10  # первые строки пропускаем

print(f"\nСтроим треугольник: до {MAX_ROW} строк, {MAX_COL} столбцов...")
t1 = time.time()

# Инициализируем строку как первые MAX_ROW+MAX_COL элементов последовательности
# Но нам нужна вся строка для точного вычисления — нужно N элементов для строки 0
# Для строки k нужно N-k элементов
# Мы берём первые min(N, MAX_ROW + MAX_COL + 100) элементов

row = list(primes[:min(N, MAX_ROW + MAX_COL + 100)])

col_unique = {j: set() for j in range(MAX_COL)}  # уникальные значения по столбцам (после transient)
col_counts = {j: {} for j in range(MAX_COL)}  # подсчёт значений
violations = []  # строки, нарушающие {0,2}

n_rows = 0
for k in range(MAX_ROW):
    if len(row) < MAX_COL + 1:
        break

    # Записываем столбцы
    if k >= TRANSIENT:
        for j in range(min(MAX_COL, len(row))):
            v = row[j]
            col_unique[j].add(v)
            col_counts[j][v] = col_counts[j].get(v, 0) + 1

            # Проверка: col_0 должен быть 1, col_j>=1 должен быть в {0,2}
            if j == 0 and v != 1:
                violations.append({"row": k, "col": j, "val": v, "expected": "{1}"})
            elif j >= 1 and v not in (0, 2):
                violations.append({"row": k, "col": j, "val": v, "expected": "{0,2}"})

    n_rows += 1
    # Следующая строка: abs-diff
    row = [abs(row[i+1] - row[i]) for i in range(len(row) - 1)]

elapsed_triangle = time.time() - t1
print(f"  Построено {n_rows} строк за {elapsed_triangle:.1f}s")
print(f"  Нарушений {0,2} collapse: {len(violations)}")

if violations:
    print(f"  Первые 10 нарушений:")
    for v in violations[:10]:
        print(f"    row={v['row']}, col={v['col']}: val={v['val']} (ожидалось {v['expected']})")

# Статистика по столбцам
print(f"\n  Столбец | Уникальные значения (k>={TRANSIENT}) | ⊆{{0,2}}")
collapse_ok = True
col_summary = []
for j in range(min(MAX_COL, 50)):  # показываем первые 50
    unique = sorted(col_unique[j])
    if j == 0:
        ok = unique == [1]
    else:
        ok = all(v in (0, 2) for v in unique)
    if not ok:
        collapse_ok = False
    mark = "✓" if ok else "✗"
    if j < 20 or not ok:
        print(f"    col {j:3d}: {str(unique):>25s}  {mark}")
    col_summary.append({"col": j, "unique": unique, "ok": ok})

if collapse_ok:
    print(f"\n  >>> ВСЕ {min(MAX_COL, 50)} столбцов: {0,2} collapse ПОДТВЕРЖДЁН <<<")
else:
    print(f"\n  >>> ЕСТЬ НАРУШЕНИЯ <<<")


# =============================================================================
# ЧАСТЬ 2: Корреляции между столбцами (при больших данных)
# =============================================================================
print("\n" + "=" * 70)
print("ЧАСТЬ 2: Корреляции между столбцами")
print("=" * 70)

# Собираем массивы значений столбцов (бинарные: 0→0, 2→1)
# Для этого перестраиваем треугольник и сохраняем столбцы 1..20
MAX_CORR_COL = 20
col_binary = {j: [] for j in range(1, MAX_CORR_COL + 1)}

row = list(primes[:min(N, MAX_ROW + MAX_CORR_COL + 100)])
for k in range(min(MAX_ROW, n_rows)):
    if len(row) < MAX_CORR_COL + 2:
        break
    if k >= TRANSIENT:
        for j in range(1, MAX_CORR_COL + 1):
            col_binary[j].append(row[j] // 2)  # 0→0, 2→1
    row = [abs(row[i+1] - row[i]) for i in range(len(row) - 1)]

# Корреляция между соседними столбцами
print(f"\n  corr(col_j, col_{{j+1}}) для j=1..{MAX_CORR_COL-1}:")
correlations = []
for j in range(1, MAX_CORR_COL):
    a = col_binary[j]
    b = col_binary[j+1]
    n_s = min(len(a), len(b))
    if n_s < 10:
        continue
    ma = sum(a[:n_s]) / n_s
    mb = sum(b[:n_s]) / n_s
    va = sum((x - ma)**2 for x in a[:n_s]) / n_s
    vb = sum((x - mb)**2 for x in b[:n_s]) / n_s
    if va == 0 or vb == 0:
        continue
    cov = sum((a[i] - ma) * (b[i] - mb) for i in range(n_s)) / n_s
    corr = cov / (va * vb) ** 0.5
    correlations.append({"j": j, "corr": round(corr, 5)})
    print(f"    col {j:2d} ↔ col {j+1:2d}: r = {corr:+.5f}")

# Энтропия второго столбца
sc = col_binary.get(1, [])
if sc:
    p1 = sum(sc) / len(sc)
    p0 = 1 - p1
    h = -(p1 * math.log2(p1) + p0 * math.log2(p0)) if 0 < p1 < 1 else 0
    print(f"\n  Энтропия col_1: P(2)={p1:.4f}, P(0)={p0:.4f}, H={h:.4f} бит")


# =============================================================================
# ЧАСТЬ 3: Полный скан аномалий pos=2..4999
# =============================================================================
print("\n" + "=" * 70)
print("ЧАСТЬ 3: Anomaly scan pos=2..4999, N=100000")
print("=" * 70)

def gilbreath_violation_fast(seq, max_depth):
    """Returns (depth, first_value) of first violation, or (max_depth, 1) if none."""
    row = list(seq[:max_depth + 2])
    for d in range(1, max_depth + 1):
        row = [abs(row[i+1] - row[i]) for i in range(len(row)-1)]
        if not row:
            return (d, None)
        if row[0] != 1:
            return (d, row[0])
    return (max_depth, 1)

def perturb_and_test(gaps, pos, val, max_depth):
    n_needed = max_depth + 2
    g = list(gaps[:n_needed])
    if pos < len(g):
        g[pos] = val
    seq = [2]
    for gap in g[:n_needed - 1]:
        seq.append(seq[-1] + gap)
    return gilbreath_violation_fast(seq, max_depth)

def find_min_break(gaps, pos, hi=3000):
    """Binary search for minimum even value that breaks Gilbreath at position pos."""
    max_depth = pos + 80
    orig = gaps[pos]

    depth, first = perturb_and_test(gaps, pos, hi, max_depth)
    if first is None or first == 1:
        return None

    lo = orig if orig % 2 == 0 else orig + 1

    while hi - lo > 2:
        mid = lo + ((hi - lo) // 4) * 2
        if mid == lo:
            mid = lo + 2
        depth_m, first_m = perturb_and_test(gaps, pos, mid, max_depth)
        if first_m is not None and first_m != 1:
            hi = mid
        else:
            lo = mid

    for v in range(lo + 2, hi + 3, 2):
        depth_v, first_v = perturb_and_test(gaps, pos, v, max_depth)
        if first_v is not None and first_v != 1:
            return (v, depth_v, first_v)

    depth, first = perturb_and_test(gaps, pos, hi, max_depth)
    return (hi, depth, first)


# Скан: тестируем каждую 5-ю позицию для скорости, каждую позицию вблизи аномалий
t2 = time.time()

MAX_POS = 5000
COARSE_STEP = 5  # грубый скан
anomalies = []
first_counts = {}
spectrum_sample = []

# Фаза 1: грубый скан
print(f"  Фаза 1: грубый скан pos=2..{MAX_POS-1}, шаг {COARSE_STEP}...")
coarse_anomaly_zones = []

for pos in range(2, min(MAX_POS, len(gaps)), COARSE_STEP):
    result = find_min_break(gaps, pos, hi=6000)
    if result is None:
        continue
    val, depth, first = result
    entry = {
        "pos": pos, "min_break": val, "depth": depth, "first": first,
        "orig_gap": gaps[pos], "depth_minus_pos": depth - pos
    }
    first_counts[first] = first_counts.get(first, 0) + 1
    if first != 3:
        anomalies.append(entry)
        coarse_anomaly_zones.append(pos)
    if pos % 500 == 0:
        elapsed = time.time() - t2
        print(f"    pos={pos}, elapsed={elapsed:.1f}s, anomalies so far: {len(anomalies)}")

    # Сохраняем каждые 50 для регрессии
    if pos % 50 == 0:
        spectrum_sample.append(entry)

elapsed_coarse = time.time() - t2
print(f"  Грубый скан завершён за {elapsed_coarse:.1f}s")
print(f"  first distribution (coarse): {dict(sorted(first_counts.items()))}")
print(f"  Anomalies (first != 3): {len(anomalies)}")

# Фаза 2: точный скан вокруг аномалий (±20 позиций)
print(f"\n  Фаза 2: точный скан вблизи {len(coarse_anomaly_zones)} аномалий...")
t3 = time.time()
fine_anomalies = []
tested_positions = set()

for center in coarse_anomaly_zones:
    for pos in range(max(2, center - 20), min(len(gaps), center + 21)):
        if pos in tested_positions:
            continue
        tested_positions.add(pos)
        result = find_min_break(gaps, pos, hi=6000)
        if result is None:
            continue
        val, depth, first = result
        if first != 3:
            entry = {
                "pos": pos, "min_break": val, "depth": depth, "first": first,
                "orig_gap": gaps[pos], "depth_minus_pos": depth - pos
            }
            fine_anomalies.append(entry)

# Объединяем
all_anomalies_set = {}
for a in anomalies + fine_anomalies:
    all_anomalies_set[a["pos"]] = a
all_anomalies = sorted(all_anomalies_set.values(), key=lambda x: x["pos"])

elapsed_fine = time.time() - t3
print(f"  Точный скан: {elapsed_fine:.1f}s, найдено ещё {len(fine_anomalies)} аномалий")
print(f"\n  ИТОГО АНОМАЛИЙ: {len(all_anomalies)}")
print(f"\n  Все аномалии:")
first_at_anomaly = {}
for a in all_anomalies:
    first_at_anomaly[a["first"]] = first_at_anomaly.get(a["first"], 0) + 1
    print(f"    pos={a['pos']:5d}: first={a['first']}, depth={a['depth']}, "
          f"min_break={a['min_break']}, gap={a['orig_gap']}, Δ(depth-pos)={a['depth_minus_pos']}")

print(f"\n  Распределение first у аномалий: {dict(sorted(first_at_anomaly.items()))}")


# =============================================================================
# ЧАСТЬ 4: Анатомия first=5 — ЧТО делает позицию аномальной?
# =============================================================================
print("\n" + "=" * 70)
print("ЧАСТЬ 4: Анатомия аномалий — почему first=5?")
print("=" * 70)

# Гипотеза: при нарушении, second@depth = 4 → first = |4-1| = 3.
# При first=5: |second@depth - 1| = 5 → second@depth = 6 или -4 (невозможно).
# Значит second@depth = 6 при аномалиях.
# Это значит, что нарушение проникло ГЛУБЖЕ в столбцы.

# Проверяем: для каждой аномалии, смотрим полную строку на глубине нарушения
print("\n  Проверка: значения на глубине нарушения для каждой аномалии")
print(f"  {'pos':>5s} {'first':>5s} {'second':>6s} {'third':>6s} {'fourth':>6s}")

anatomy_results = []

for a in all_anomalies[:20]:  # ограничиваем
    pos = a["pos"]
    mb = a["min_break"]
    max_depth = a["depth"] + 5

    # Строим треугольник с пертурбацией
    n_needed = max_depth + 10
    g = list(gaps[:n_needed])
    g[pos] = mb
    seq = [2]
    for gap in g[:n_needed - 1]:
        seq.append(seq[-1] + gap)

    row = list(seq)
    for d in range(max_depth + 3):
        if len(row) < 2:
            break
        row = [abs(row[i+1] - row[i]) for i in range(len(row) - 1)]
        if row[0] != 1:
            vals = row[:min(8, len(row))]
            print(f"  {pos:5d} {vals[0] if len(vals)>0 else '':>5} "
                  f"{vals[1] if len(vals)>1 else '':>6} "
                  f"{vals[2] if len(vals)>2 else '':>6} "
                  f"{vals[3] if len(vals)>3 else '':>6}")
            anatomy_results.append({
                "pos": pos, "first": a["first"],
                "row_at_depth": vals,
                "depth": d + 1
            })
            break

# Сравнение: обычные (first=3) нарушения
print(f"\n  Для сравнения — обычные (first=3) нарушения:")
print(f"  {'pos':>5s} {'first':>5s} {'second':>6s} {'third':>6s} {'fourth':>6s}")

normal_sample_positions = [10, 50, 100, 200, 500, 1000, 2000]
for pos in normal_sample_positions:
    if pos >= len(gaps):
        continue
    result = find_min_break(gaps, pos, hi=6000)
    if result is None:
        continue
    val, depth, first = result
    if first != 3:
        continue

    max_depth = depth + 5
    n_needed = max_depth + 10
    g = list(gaps[:n_needed])
    g[pos] = val
    seq = [2]
    for gap in g[:n_needed - 1]:
        seq.append(seq[-1] + gap)

    row = list(seq)
    for d in range(max_depth + 3):
        if len(row) < 2:
            break
        row = [abs(row[i+1] - row[i]) for i in range(len(row) - 1)]
        if row[0] != 1:
            vals = row[:min(8, len(row))]
            print(f"  {pos:5d} {vals[0] if len(vals)>0 else '':>5} "
                  f"{vals[1] if len(vals)>1 else '':>6} "
                  f"{vals[2] if len(vals)>2 else '':>6} "
                  f"{vals[3] if len(vals)>3 else '':>6}")
            anatomy_results.append({
                "pos": pos, "first": first,
                "row_at_depth": vals,
                "depth": d + 1,
                "type": "normal"
            })
            break


# =============================================================================
# ЧАСТЬ 5: Глубокий вопрос — переход 3→5 при увеличении пертурбации
# =============================================================================
print("\n" + "=" * 70)
print("ЧАСТЬ 5: Что происходит при увеличении пертурбации сверх min_break?")
print("=" * 70)

# Для каждой аномальной позиции: first=5 при min_break.
# Что будет при mb+2, mb+4, ...? Останется ли first=5?
# А для обычных позиций: first=3 при min_break.
# При увеличении — переключится ли first на 5?

print("\n  Аномальная позиция (пример): эволюция first при росте perturbation")

for a in all_anomalies[:3]:
    pos = a["pos"]
    mb = a["min_break"]
    max_depth = pos + 80

    print(f"\n  pos={pos}, min_break={mb}:")
    print(f"    {'val':>6s} {'depth':>6s} {'first':>6s}")

    for val in range(mb, min(mb + 100, 8000), 2):
        depth, first = perturb_and_test(gaps, pos, val, max_depth)
        if first is not None and first != 1:
            print(f"    {val:6d} {depth:6d} {first:6d}")
            if val > mb + 40:
                break

print("\n  Обычная позиция (пример): эволюция first при росте perturbation")

for pos in [50, 200, 1000]:
    if pos >= len(gaps):
        continue
    result = find_min_break(gaps, pos, hi=6000)
    if result is None:
        continue
    mb = result[0]
    max_depth = pos + 80

    print(f"\n  pos={pos}, min_break={mb}:")
    print(f"    {'val':>6s} {'depth':>6s} {'first':>6s}")

    seen_firsts = set()
    for val in range(mb, min(mb + 200, 8000), 2):
        depth, first = perturb_and_test(gaps, pos, val, max_depth)
        if first is not None and first != 1:
            if first not in seen_firsts or val <= mb + 10:
                print(f"    {val:6d} {depth:6d} {first:6d}")
                seen_firsts.add(first)
            if val > mb + 100:
                break


# =============================================================================
# ЧАСТЬ 6: depth_minus_pos — расширенный анализ паттерна 2^k+1
# =============================================================================
print("\n" + "=" * 70)
print("ЧАСТЬ 6: Паттерн depth-pos у аномалий")
print("=" * 70)

dmp_values = [a["depth_minus_pos"] for a in all_anomalies]
dmp_counts = {}
for d in dmp_values:
    dmp_counts[d] = dmp_counts.get(d, 0) + 1

print(f"  depth-pos values: {sorted(dmp_counts.items())}")
print(f"  Проверка 2^k+1:")
for d in sorted(set(dmp_values)):
    # Проверяем: d = 2^k + 1?
    dm1 = d - 1
    is_power_2 = dm1 > 0 and (dm1 & (dm1 - 1)) == 0
    k = dm1.bit_length() - 1 if dm1 > 0 else None
    print(f"    depth-pos = {d}: count={dmp_counts[d]}, "
          f"d-1={dm1}, is 2^k? {is_power_2}" + (f" (k={k})" if is_power_2 else ""))


# =============================================================================
# ЧАСТЬ 7: Регрессия min_break(pos) на расширенных данных
# =============================================================================
print("\n" + "=" * 70)
print("ЧАСТЬ 7: Регрессия min_break(pos) — расширенные данные")
print("=" * 70)

valid = [(s["pos"], s["min_break"]) for s in spectrum_sample
         if s.get("min_break") is not None and s["pos"] >= 10]

if len(valid) > 20:
    n_v = len(valid)
    sx = sum(p for p, _ in valid)
    sy = sum(m for _, m in valid)
    sxy = sum(p * m for p, m in valid)
    sxx = sum(p * p for p, _ in valid)

    # Linear
    a_lin = (n_v * sxy - sx * sy) / (n_v * sxx - sx * sx)
    b_lin = (sy - a_lin * sx) / n_v
    ss_res = sum((m - (a_lin * p + b_lin))**2 for p, m in valid)
    ss_tot = sum((m - sy / n_v)**2 for _, m in valid)
    r2_lin = 1 - ss_res / ss_tot

    # Power law
    lx = [math.log(p) for p, _ in valid]
    ly = [math.log(m) for _, m in valid]
    slx, sly = sum(lx), sum(ly)
    slxy = sum(a * b for a, b in zip(lx, ly))
    slxx = sum(a * a for a in lx)
    alpha = (n_v * slxy - slx * sly) / (n_v * slxx - slx * slx)
    log_C = (sly - alpha * slx) / n_v
    C_pow = math.exp(log_C)
    ss_res_p = sum((ly[i] - (alpha * lx[i] + log_C))**2 for i in range(n_v))
    ss_tot_p = sum((ly[i] - sly / n_v)**2 for i in range(n_v))
    r2_pow = 1 - ss_res_p / ss_tot_p

    print(f"  Точек: {n_v}, диапазон pos: [{valid[0][0]}..{valid[-1][0]}]")
    print(f"  Linear:  min_break ≈ {a_lin:.4f}*pos + {b_lin:.2f}  (R²={r2_lin:.6f})")
    print(f"  Power:   min_break ≈ {C_pow:.4f}*pos^{alpha:.4f}  (R²={r2_pow:.6f})")

    # Предсказание для pos=5000..6000
    print(f"\n  Предсказание для pos=5000..5500:")
    predictions = []
    for pos in range(5000, min(5500, len(gaps)), 50):
        predicted = C_pow * pos**alpha
        result = find_min_break(gaps, pos, hi=8000)
        if result is None:
            continue
        val, depth, first = result
        error = abs(val - predicted) / val * 100
        predictions.append({
            "pos": pos, "predicted": round(predicted, 1), "actual": val,
            "rel_error_pct": round(error, 1), "first": first
        })
        print(f"    pos={pos}: predicted={predicted:.0f}, actual={val}, error={error:.1f}%")

    if predictions:
        mean_err = sum(p["rel_error_pct"] for p in predictions) / len(predictions)
        print(f"  Средняя ошибка: {mean_err:.1f}%")


# =============================================================================
# Сохранение результатов
# =============================================================================
print("\n" + "=" * 70)
print("Сохранение результатов")
print("=" * 70)

total_time = time.time() - t0

results = {
    "params": {
        "N": N,
        "max_col": MAX_COL,
        "max_row": n_rows,
        "transient": TRANSIENT,
        "anomaly_scan_max_pos": MAX_POS,
        "anomaly_scan_step": COARSE_STEP
    },
    "collapse_verification": {
        "n_rows": n_rows,
        "n_cols_checked": min(MAX_COL, 50),
        "all_collapse": collapse_ok,
        "n_violations": len(violations),
        "violations_sample": violations[:20],
        "col_summary": col_summary[:50]
    },
    "correlations": correlations,
    "entropy_col1": {
        "p_2": round(p1, 5) if sc else None,
        "p_0": round(p0, 5) if sc else None,
        "h_bits": round(h, 5) if sc else None
    },
    "anomalies": {
        "total": len(all_anomalies),
        "first_distribution": dict(sorted(first_at_anomaly.items())),
        "all_details": all_anomalies,
        "depth_minus_pos_counts": {str(k): v for k, v in sorted(dmp_counts.items())}
    },
    "anatomy": anatomy_results,
    "regression": {
        "linear": {"a": round(a_lin, 6), "b": round(b_lin, 2), "r2": round(r2_lin, 6)} if len(valid) > 20 else None,
        "power": {"C": round(C_pow, 6), "alpha": round(alpha, 6), "r2": round(r2_pow, 6)} if len(valid) > 20 else None,
        "predictions_5000_5500": predictions if len(valid) > 20 else None
    },
    "total_time_sec": round(total_time, 1)
}

with open("gilbreath_deep_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print(f"\nРезультаты сохранены в gilbreath_deep_results.json")
print(f"Общее время: {total_time:.1f}s")
