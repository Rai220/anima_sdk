"""
cascade_boundary.py — generation_1 v9

v8 обнаружила гипотезу: col_j@row_k ∈ {0, 2, ..., 2j} для достаточно большого k.
universal_collapse_results.json показал all_collapse=false для col=30, row=400.

Этот скрипт:
1. Находит ТОЧНУЮ границу: для какого j гипотеза впервые нарушается?
2. Характеризует нарушения: какие значения появляются вне {0,2,...,2j}?
3. Проверяет ослабленную гипотезу: col_j ∈ {0, 2, ..., 2j+C} для какого C?
4. Корреляция col_j с col_0 (Гилбрет): есть ли связь колонок?
5. Энтропия каждого столбца — сходится ли она к чему-то?
"""

import json
import math

def sieve_primes(limit):
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
# Build the triangle
# =============================================================================
N = 3000
MAX_COL = 50
MAX_ROW = 1500

print(f"Building abs-diff triangle: N={N} primes, up to {MAX_ROW} rows, {MAX_COL} columns")

primes = get_primes(N)
row = primes[:]

# Store columns
columns = {j: [] for j in range(MAX_COL)}

for k in range(MAX_ROW):
    if len(row) < MAX_COL + 1:
        # Not enough elements, store what we can
        for j in range(min(MAX_COL, len(row))):
            columns[j].append(row[j])
        break
    for j in range(MAX_COL):
        columns[j].append(row[j])
    row = abs_diff_row(row)

actual_rows = len(columns[0])
print(f"Built {actual_rows} rows\n")


# =============================================================================
# PART 1: Find exact cascade boundary
# =============================================================================
print("=" * 60)
print("PART 1: Cascade boundary — where does col_j ⊄ {0,2,...,2j}?")
print("=" * 60)

TRANSIENT = 10  # skip first rows (transient behavior)

cascade_results = {}
first_violation_col = None

for j in range(MAX_COL):
    vals = columns[j][TRANSIENT:]
    if not vals:
        break
    expected_set = set(range(0, 2*j + 1, 2))  # {0, 2, 4, ..., 2j}
    actual_set = set(vals)
    extra = sorted(actual_set - expected_set)
    contained = len(extra) == 0

    # Also check: are all values even? (except col 0 which is 1)
    if j == 0:
        all_one = all(v == 1 for v in vals)
        cascade_results[j] = {
            "expected": sorted(expected_set),
            "actual_unique": sorted(actual_set),
            "contained": all_one,
            "extra": [] if all_one else sorted(actual_set - {1}),
            "max_val": max(vals),
            "n_unique": len(actual_set)
        }
        status = "✓ all=1 (Gilbreath holds)" if all_one else f"✗ VIOLATIONS"
    else:
        cascade_results[j] = {
            "expected_max": 2*j,
            "actual_unique": sorted(actual_set),
            "contained": contained,
            "extra": extra[:20],
            "max_val": max(vals),
            "n_unique": len(actual_set)
        }
        status = f"✓ max={max(vals)} ≤ {2*j}" if contained else f"✗ max={max(vals)}, extra={extra[:5]}"

    if not contained and first_violation_col is None and j > 0:
        first_violation_col = j

    if j < 20 or not contained:
        print(f"  col {j:3d}: {status}")

print(f"\nFirst violation column: {first_violation_col}")


# =============================================================================
# PART 2: Characterize violations
# =============================================================================
print("\n" + "=" * 60)
print("PART 2: Violation characterization")
print("=" * 60)

if first_violation_col is not None:
    for j in range(first_violation_col, min(first_violation_col + 10, MAX_COL)):
        vals = columns[j][TRANSIENT:]
        if not vals:
            break
        expected_set = set(range(0, 2*j + 1, 2))
        actual_set = set(vals)
        extra = sorted(actual_set - expected_set)

        if extra:
            # Where do violations occur? (which rows)
            violation_rows = []
            for idx, v in enumerate(vals):
                if v not in expected_set:
                    violation_rows.append((idx + TRANSIENT, v))

            print(f"\n  col {j}: {len(violation_rows)} violations in {len(vals)} rows")
            print(f"    Extra values: {sorted(set(v for _, v in violation_rows))[:20]}")
            print(f"    First 10 violation rows: {violation_rows[:10]}")

            # Is there a pattern? Do violations cluster?
            if len(violation_rows) >= 2:
                vr = [r for r, _ in violation_rows]
                gaps_v = [vr[i+1] - vr[i] for i in range(len(vr)-1)]
                if gaps_v:
                    print(f"    Gaps between violations: min={min(gaps_v)}, max={max(gaps_v)}, "
                          f"mean={sum(gaps_v)/len(gaps_v):.1f}")


# =============================================================================
# PART 3: Weakened hypothesis — col_j ∈ {0, 2, ..., 2j + C}?
# =============================================================================
print("\n" + "=" * 60)
print("PART 3: Weakened cascade — what C makes col_j ⊆ {0,2,...,2j+C}?")
print("=" * 60)

weak_cascade = {}
for j in range(1, MAX_COL):
    vals = columns[j][TRANSIENT:]
    if not vals:
        break
    max_val = max(vals)
    needed_C = max(0, max_val - 2*j)
    # But also check: are all values even?
    all_even = all(v % 2 == 0 for v in vals)
    weak_cascade[j] = {
        "max_val": max_val,
        "bound_2j": 2*j,
        "needed_C": needed_C,
        "all_even": all_even,
        "ratio_max_to_2j": round(max_val / (2*j), 3) if j > 0 else None
    }
    if j < 30 or needed_C > 0:
        even_str = "all even" if all_even else "HAS ODD VALUES"
        print(f"  col {j:3d}: max={max_val:5d}, 2j={2*j:5d}, C={needed_C:5d}, "
              f"ratio={max_val/(2*j):.3f}, {even_str}")

# Key question: does max_val / (2j) converge?
ratios = [weak_cascade[j]["ratio_max_to_2j"] for j in range(1, min(MAX_COL, len(weak_cascade)+1))
          if weak_cascade.get(j, {}).get("ratio_max_to_2j") is not None]
if ratios:
    print(f"\n  Ratio max/(2j) trend:")
    print(f"    First 10: {ratios[:10]}")
    print(f"    Last 10: {ratios[-10:]}")


# =============================================================================
# PART 4: Entropy of each column
# =============================================================================
print("\n" + "=" * 60)
print("PART 4: Shannon entropy of each column")
print("=" * 60)

entropy_data = {}
for j in range(MAX_COL):
    vals = columns[j][TRANSIENT:]
    if not vals or len(vals) < 50:
        break
    # Compute entropy
    counts = {}
    for v in vals:
        counts[v] = counts.get(v, 0) + 1
    total = len(vals)
    h = -sum((c/total) * math.log2(c/total) for c in counts.values() if c > 0)
    n_unique = len(counts)

    # Max possible entropy for this many unique values
    h_max = math.log2(n_unique) if n_unique > 1 else 0

    entropy_data[j] = {
        "entropy": round(h, 4),
        "n_unique": n_unique,
        "h_max": round(h_max, 4),
        "efficiency": round(h / h_max, 4) if h_max > 0 else None
    }

    if j < 20:
        eff = f"{h/h_max:.3f}" if h_max > 0 else "N/A"
        print(f"  col {j:3d}: H={h:.4f} bits, {n_unique:4d} unique values, "
              f"H_max={h_max:.4f}, efficiency={eff}")


# =============================================================================
# PART 5: Column correlations
# =============================================================================
print("\n" + "=" * 60)
print("PART 5: Correlations between adjacent columns")
print("=" * 60)

corr_data = {}
for j in range(min(20, MAX_COL - 1)):
    v1 = columns[j][TRANSIENT:]
    v2 = columns[j+1][TRANSIENT:]
    n_corr = min(len(v1), len(v2))
    if n_corr < 50:
        break
    v1 = v1[:n_corr]
    v2 = v2[:n_corr]

    m1 = sum(v1) / n_corr
    m2 = sum(v2) / n_corr
    cov = sum((a - m1) * (b - m2) for a, b in zip(v1, v2)) / n_corr
    s1 = (sum((a - m1)**2 for a in v1) / n_corr) ** 0.5
    s2 = (sum((b - m2)**2 for b in v2) / n_corr) ** 0.5
    corr = cov / (s1 * s2) if s1 > 0 and s2 > 0 else 0

    corr_data[j] = round(corr, 4)
    print(f"  corr(col_{j}, col_{j+1}) = {corr:.4f}")


# =============================================================================
# PART 6: Parity structure — is every value in col_j even for j >= 1?
# =============================================================================
print("\n" + "=" * 60)
print("PART 6: Parity structure")
print("=" * 60)

parity_data = {}
for j in range(MAX_COL):
    vals = columns[j][TRANSIENT:]
    if not vals:
        break
    n_even = sum(1 for v in vals if v % 2 == 0)
    n_odd = len(vals) - n_even
    parity_data[j] = {"even": n_even, "odd": n_odd, "frac_even": round(n_even/len(vals), 4)}
    if j < 15 or n_odd > 0:
        print(f"  col {j:3d}: {n_even} even, {n_odd} odd ({n_even/len(vals)*100:.1f}% even)")

# Key insight: after col 0, are ALL values even?
all_even_cols = all(parity_data[j]["odd"] == 0 for j in range(1, min(MAX_COL, len(parity_data))))
print(f"\n  All values even for col >= 1: {all_even_cols}")


# =============================================================================
# Save
# =============================================================================
results = {
    "params": {"N": N, "max_row": actual_rows, "max_col": MAX_COL, "transient": TRANSIENT},
    "cascade_boundary": {
        "first_violation_col": first_violation_col,
        "column_details": {str(j): cascade_results[j] for j in sorted(cascade_results.keys()) if j < 25}
    },
    "weakened_cascade": {str(j): weak_cascade[j] for j in sorted(weak_cascade.keys()) if j < 30},
    "entropy": {str(j): entropy_data[j] for j in sorted(entropy_data.keys()) if j < 25},
    "correlations": {str(j): corr_data[j] for j in sorted(corr_data.keys())},
    "parity": {
        "all_even_for_col_ge_1": all_even_cols,
        "details": {str(j): parity_data[j] for j in sorted(parity_data.keys()) if j < 15}
    }
}

with open("cascade_boundary_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to cascade_boundary_results.json")
