"""
Рост толерантности: min_break(pos) vs max_gap(pos).

Ключевая гипотеза из v5:
- min_break(pos) растёт (линейно? сублинейно?)
- max_prime_gap(pos) растёт как O(log² p)
- Если min_break растёт быстрее max_gap, Гилбрет гарантирован с некоторого места

Это потенциальный путь к доказательству (или опровержению).
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

def gilbreath_violation_depth(seq, max_depth=500):
    row = seq[:]
    for d in range(max_depth):
        if len(row) < 2:
            return None
        row = abs_diff_row(row)
        if row[0] != 1:
            return d + 1
    return None

def gaps_to_seq(gaps, start=2):
    seq = [start]
    for g in gaps:
        seq.append(seq[-1] + g)
    return seq

results = {}

# === 1. Min_break для большого диапазона позиций ===
print("=== 1. Толерантность к возмущению: min_break(pos) ===\n")

N = 500
primes = get_primes(N)
real_gaps = [primes[i+1] - primes[i] for i in range(len(primes) - 1)]

# Для каждой позиции, бинарный поиск min_break
def find_min_break(gaps, pos, lo=2, hi=200):
    """Бинарный поиск минимального чётного значения, ломающего Гилбрета в позиции pos."""
    best = None
    for val in range(lo, hi + 1, 2):
        modified = gaps[:]
        modified[pos] = val
        seq = gaps_to_seq(modified)
        vd = gilbreath_violation_depth(seq, max_depth=200)
        if vd is not None:
            return val
    return None

print(f"{'pos':>5s} {'orig':>5s} {'min_break':>9s} {'ratio':>7s} {'cummax':>7s}")

tolerance_data = []
positions_to_test = list(range(2, min(150, len(real_gaps)), 1))

for pos in positions_to_test:
    orig = real_gaps[pos]
    mb = find_min_break(real_gaps, pos, lo=2, hi=300)
    cummax = max(real_gaps[:pos+1])

    if mb is not None:
        ratio = mb / (pos + 1)
        tolerance_data.append({"pos": pos, "orig": orig, "min_break": mb, "ratio": round(ratio, 3), "cummax": cummax})
        if pos % 10 == 2 or pos < 12:
            print(f"{pos:5d} {orig:5d} {mb:9d} {ratio:7.3f} {cummax:7d}")

results["tolerance"] = tolerance_data

# === 2. Анализ роста ===
print(f"\n=== 2. Анализ роста min_break(pos) ===\n")

if tolerance_data:
    positions = [d["pos"] for d in tolerance_data if d["min_break"] is not None]
    min_breaks = [d["min_break"] for d in tolerance_data if d["min_break"] is not None]
    ratios = [d["ratio"] for d in tolerance_data if d["min_break"] is not None]

    # Линейная регрессия: min_break ≈ a * pos + b
    n = len(positions)
    sum_x = sum(positions)
    sum_y = sum(min_breaks)
    sum_xy = sum(x*y for x, y in zip(positions, min_breaks))
    sum_x2 = sum(x*x for x in positions)

    a = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
    b = (sum_y - a * sum_x) / n

    # R²
    y_mean = sum_y / n
    ss_tot = sum((y - y_mean)**2 for y in min_breaks)
    ss_res = sum((y - (a*x + b))**2 for x, y in zip(positions, min_breaks))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    print(f"Линейная модель: min_break ≈ {a:.3f} * pos + {b:.3f}")
    print(f"R² = {r2:.4f}")

    # Лог-лог регрессия: min_break ≈ C * pos^α
    log_pos = [math.log(p) for p in positions]
    log_mb = [math.log(m) for m in min_breaks]
    n2 = len(log_pos)
    sum_lx = sum(log_pos)
    sum_ly = sum(log_mb)
    sum_lxy = sum(x*y for x, y in zip(log_pos, log_mb))
    sum_lx2 = sum(x*x for x in log_pos)

    alpha = (n2 * sum_lxy - sum_lx * sum_ly) / (n2 * sum_lx2 - sum_lx**2)
    log_C = (sum_ly - alpha * sum_lx) / n2
    C = math.exp(log_C)

    ss_tot_log = sum((y - sum_ly/n2)**2 for y in log_mb)
    ss_res_log = sum((y - (alpha*x + log_C))**2 for x, y in zip(log_pos, log_mb))
    r2_log = 1 - ss_res_log / ss_tot_log if ss_tot_log > 0 else 0

    print(f"\nСтепенная модель: min_break ≈ {C:.3f} * pos^{alpha:.3f}")
    print(f"R² = {r2_log:.4f}")

    results["regression"] = {
        "linear": {"a": round(a, 3), "b": round(b, 3), "r2": round(r2, 4)},
        "power": {"C": round(C, 3), "alpha": round(alpha, 3), "r2": round(r2_log, 4)}
    }

    # === 3. Сравнение с max_gap ===
    print(f"\n=== 3. min_break vs max_gap: кто растёт быстрее? ===\n")

    print(f"{'pos':>5s} {'min_break':>9s} {'max_gap_so_far':>14s} {'margin':>7s}")
    for d in tolerance_data:
        pos = d["pos"]
        mb = d["min_break"]
        mg = d["cummax"]
        if mb is not None and pos % 10 == 2:
            margin = mb - mg
            print(f"{pos:5d} {mb:9d} {mg:14d} {margin:7d}")

    # Для каких позиций min_break > cummax?
    safe = [(d["pos"], d["min_break"], d["cummax"]) for d in tolerance_data
            if d["min_break"] is not None and d["min_break"] > d["cummax"]]
    unsafe = [(d["pos"], d["min_break"], d["cummax"]) for d in tolerance_data
              if d["min_break"] is not None and d["min_break"] <= d["cummax"]]

    print(f"\nПозиции где min_break > max_gap (безопасные): {len(safe)}/{len(tolerance_data)}")
    print(f"Позиции где min_break ≤ max_gap (потенциально опасные): {len(unsafe)}/{len(tolerance_data)}")

    if unsafe:
        print(f"\nОПАСНЫЕ позиции:")
        for pos, mb, mg in unsafe[:10]:
            print(f"  pos={pos}: min_break={mb}, max_gap={mg}, deficit={mg-mb}")

    results["safety_analysis"] = {
        "n_safe": len(safe),
        "n_unsafe": len(unsafe),
        "n_total": len(tolerance_data)
    }

# === 4. Два масштаба: локальная vs глобальная устойчивость ===
print(f"\n=== 4. Глобальная устойчивость: возмущение ДВУХ позиций ===\n")

# min_break для одной позиции — это одно. Но что если два gap одновременно большие?
# Проверяем: берём пары соседних позиций, ставим одинаковые большие значения.

print(f"{'pos_pair':>12s} {'min_break_single':>15s} {'min_break_pair':>13s}")
pair_data = []
for pos in range(2, 50, 5):
    # Одиночное
    mb_single = find_min_break(real_gaps, pos, lo=2, hi=200)
    # Парное (pos и pos+1)
    best_pair = None
    for val in range(2, 202, 2):
        modified = real_gaps[:]
        modified[pos] = val
        if pos + 1 < len(modified):
            modified[pos + 1] = val
        seq = gaps_to_seq(modified)
        vd = gilbreath_violation_depth(seq, max_depth=200)
        if vd is not None:
            best_pair = val
            break
    pair_data.append({"pos": pos, "single": mb_single, "pair": best_pair})
    print(f"  ({pos},{pos+1}):  {str(mb_single):>15s} {str(best_pair):>13s}")

results["pair_perturbation"] = pair_data

# === 5. Масштабирование: тест на больших N ===
print(f"\n=== 5. Масштабирование min_break для больших N ===\n")

for N_test in [100, 200, 500, 1000]:
    p = get_primes(N_test)
    g = [p[i+1] - p[i] for i in range(len(p) - 1)]

    # Тестируем позицию N/4
    test_pos = N_test // 4
    if test_pos >= 2 and test_pos < len(g):
        mb = find_min_break(g, test_pos, lo=2, hi=500)
        mg = max(g[:test_pos+1])
        print(f"  N={N_test:5d}, pos={test_pos:4d}: min_break={str(mb):>5s}, max_gap={mg:3d}, orig={g[test_pos]}")

# Сохраняем
with open("tolerance_growth_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print("\n\nРезультаты сохранены в tolerance_growth_results.json")
