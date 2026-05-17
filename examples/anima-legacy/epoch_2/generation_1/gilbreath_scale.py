"""
gilbreath_scale.py — generation_1 v9

Масштабирование эксперимента с нарушениями Гилбрета.
v7 протестировала pos=2..199 (500 простых). Здесь:

1. N=10000 простых, тестируем pos=2..999
2. Полная карта аномалий (first != 3)
3. Регрессия min_break(pos) — линейная, степенная, логарифмическая
4. Тестируемое предсказание: формула для min_break(1000..1200)
5. Структура аномалии pos=35 — что в ней особенного?
"""

import json
import math
import time

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

def gilbreath_violation(seq, max_depth):
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
    return gilbreath_violation(seq, max_depth)

def find_min_break(gaps, pos, hi=1000):
    """Binary search for minimum even value that breaks Gilbreath at position pos."""
    max_depth = pos + 60
    orig = gaps[pos]

    # Check if hi breaks it
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


# =============================================================================
# PART 1: Full scan pos=2..999 with N=10000 primes
# =============================================================================
print("=" * 60)
print("PART 1: Violation spectrum, pos=2..999, N=10000")
print("=" * 60)

t0 = time.time()
N = 10000
primes = get_primes(N)
gaps = [primes[i+1] - primes[i] for i in range(len(primes) - 1)]
print(f"Generated {N} primes (max = {primes[-1]}), {len(gaps)} gaps")
print(f"Max gap in first 1000: {max(gaps[:1000])}")

spectrum = []
first_counts = {}
anomalies = []

MAX_POS = 1000
STEP = 1  # test every position

for pos in range(2, min(MAX_POS, len(gaps)), STEP):
    result = find_min_break(gaps, pos, hi=1500)
    if result is None:
        spectrum.append({"pos": pos, "min_break": None, "first": None})
        continue
    val, depth, first = result
    entry = {
        "pos": pos,
        "min_break": val,
        "depth": depth,
        "first": first,
        "orig_gap": gaps[pos],
        "depth_minus_pos": depth - pos
    }
    spectrum.append(entry)
    first_counts[first] = first_counts.get(first, 0) + 1
    if first != 3:
        anomalies.append(entry)
    if pos % 100 == 0:
        elapsed = time.time() - t0
        print(f"  pos={pos}, min_break={val}, first={first}, elapsed={elapsed:.1f}s")

elapsed = time.time() - t0
print(f"\nCompleted in {elapsed:.1f}s")
print(f"Violation value distribution: {dict(sorted(first_counts.items()))}")
print(f"Total tested: {len([s for s in spectrum if s.get('min_break') is not None])}")
print(f"Anomalies (first != 3): {len(anomalies)}")
for a in anomalies:
    print(f"  pos={a['pos']}: first={a['first']}, depth={a['depth']}, "
          f"min_break={a['min_break']}, orig_gap={a['orig_gap']}")


# =============================================================================
# PART 2: Regression — find formula for min_break(pos)
# =============================================================================
print("\n" + "=" * 60)
print("PART 2: Regression for min_break(pos)")
print("=" * 60)

valid = [(s["pos"], s["min_break"]) for s in spectrum
         if s.get("min_break") is not None and s["pos"] >= 10]

n = len(valid)
if n > 50:
    sx = sum(p for p, _ in valid)
    sy = sum(m for _, m in valid)
    sxy = sum(p * m for p, m in valid)
    sxx = sum(p * p for p, _ in valid)

    # Linear: min_break = a*pos + b
    a_lin = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    b_lin = (sy - a_lin * sx) / n
    ss_res_lin = sum((m - (a_lin * p + b_lin))**2 for p, m in valid)
    ss_tot = sum((m - sy / n)**2 for _, m in valid)
    r2_lin = 1 - ss_res_lin / ss_tot
    print(f"  Linear:  min_break ≈ {a_lin:.4f}*pos + {b_lin:.2f}  (R²={r2_lin:.6f})")

    # Power law: log(mb) = alpha*log(pos) + log(C)
    lx = [math.log(p) for p, _ in valid]
    ly = [math.log(m) for _, m in valid]
    slx = sum(lx)
    sly = sum(ly)
    slxy = sum(a * b for a, b in zip(lx, ly))
    slxx = sum(a * a for a in lx)
    alpha = (n * slxy - slx * sly) / (n * slxx - slx * slx)
    log_C = (sly - alpha * slx) / n
    C_pow = math.exp(log_C)
    ss_res_pow = sum((ly[i] - (alpha * lx[i] + log_C))**2 for i in range(n))
    ss_tot_pow = sum((ly[i] - sly / n)**2 for i in range(n))
    r2_pow = 1 - ss_res_pow / ss_tot_pow
    print(f"  Power:   min_break ≈ {C_pow:.4f}*pos^{alpha:.4f}  (R²={r2_pow:.6f})")

    # Sqrt: min_break = a*sqrt(pos) + b (linearize: regress on sqrt(pos))
    sqx = [math.sqrt(p) for p, _ in valid]
    ssqx = sum(sqx)
    ssqxy = sum(sq * m for sq, (_, m) in zip(sqx, valid))
    ssqxx = sum(sq * sq for sq in sqx)
    a_sqrt = (n * ssqxy - ssqx * sy) / (n * ssqxx - ssqx * ssqx)
    b_sqrt = (sy - a_sqrt * ssqx) / n
    ss_res_sqrt = sum((m - (a_sqrt * math.sqrt(p) + b_sqrt))**2 for p, m in valid)
    r2_sqrt = 1 - ss_res_sqrt / ss_tot
    print(f"  Sqrt:    min_break ≈ {a_sqrt:.4f}*sqrt(pos) + {b_sqrt:.2f}  (R²={r2_sqrt:.6f})")

    # Pick best model
    models = [
        ("linear", r2_lin, lambda p: a_lin * p + b_lin),
        ("power", r2_pow, lambda p: C_pow * p**alpha),
        ("sqrt", r2_sqrt, lambda p: a_sqrt * math.sqrt(p) + b_sqrt),
    ]
    best_name, best_r2, best_fn = max(models, key=lambda x: x[1])
    print(f"\n  Best model: {best_name} (R²={best_r2:.6f})")

    # Residual analysis: where does the best model fail most?
    residuals = [(p, m, m - best_fn(p)) for p, m in valid]
    residuals.sort(key=lambda x: abs(x[2]), reverse=True)
    print(f"\n  Largest residuals ({best_name}):")
    for p, m, r in residuals[:10]:
        print(f"    pos={p}: actual={m}, predicted={best_fn(p):.1f}, residual={r:.1f}")


# =============================================================================
# PART 3: Testable prediction for pos=1000..1200
# =============================================================================
print("\n" + "=" * 60)
print("PART 3: Prediction vs actual for pos=1000..1200")
print("=" * 60)

predictions = []
for pos in range(1000, min(1200, len(gaps)), 10):
    predicted = best_fn(pos)
    result = find_min_break(gaps, pos, hi=2000)
    if result is None:
        continue
    val, depth, first = result
    error = val - predicted
    rel_error = abs(error) / val * 100
    predictions.append({
        "pos": pos, "predicted": round(predicted, 1), "actual": val,
        "error": round(error, 1), "rel_error_pct": round(rel_error, 1),
        "first": first
    })
    if pos % 50 == 0:
        print(f"  pos={pos}: predicted={predicted:.1f}, actual={val}, "
              f"error={error:.1f} ({rel_error:.1f}%)")

if predictions:
    mean_rel_error = sum(p["rel_error_pct"] for p in predictions) / len(predictions)
    max_rel_error = max(p["rel_error_pct"] for p in predictions)
    print(f"\n  Mean relative error: {mean_rel_error:.1f}%")
    print(f"  Max relative error: {max_rel_error:.1f}%")

    # Anomalies in prediction range
    pred_anomalies = [p for p in predictions if p["first"] != 3]
    print(f"  Anomalies in 1000..1200: {len(pred_anomalies)}")
    for pa in pred_anomalies:
        print(f"    pos={pa['pos']}: first={pa['first']}")


# =============================================================================
# PART 4: Why pos=35? Structural analysis
# =============================================================================
print("\n" + "=" * 60)
print("PART 4: Why is pos=35 anomalous?")
print("=" * 60)

# pos=35 means the 35th gap (between 36th and 37th prime)
print(f"\n  Gap at pos=35: {gaps[35]} (between primes {primes[35]} and {primes[36]})")
print(f"  Surrounding gaps: {gaps[30:41]}")
print(f"  Surrounding primes: {primes[30:42]}")

# What's special: compare gap context at anomalies vs non-anomalies
# For each anomaly, look at local gap structure
print(f"\n  Local gap statistics at anomaly positions:")
for a in anomalies:
    pos = a["pos"]
    if pos >= 3 and pos < len(gaps) - 3:
        local = gaps[pos-3:pos+4]
        local_mean = sum(local) / len(local)
        orig = gaps[pos]
        print(f"    pos={pos}: gap={orig}, local_mean={local_mean:.1f}, "
              f"local_gaps={local}, first={a['first']}")

# Check: is the anomaly related to unusually small gaps nearby?
# Or unusually large gaps?
print(f"\n  Non-anomaly sample (first=3):")
non_anom_sample = [s for s in spectrum if s.get("first") == 3][:5]
for s in non_anom_sample:
    pos = s["pos"]
    if pos >= 3 and pos < len(gaps) - 3:
        local = gaps[pos-3:pos+4]
        local_mean = sum(local) / len(local)
        print(f"    pos={pos}: gap={gaps[pos]}, local_mean={local_mean:.1f}, local_gaps={local}")


# =============================================================================
# PART 5: Safety margin at scale
# =============================================================================
print("\n" + "=" * 60)
print("PART 5: Safety margin — does min_break stay above max_gap?")
print("=" * 60)

cummax = 0
safe = 0
unsafe = 0
margin_data = []

for pos in range(2, min(800, len(gaps)), 5):
    cummax = max(cummax, max(gaps[:pos+1]))
    result = find_min_break(gaps, pos, hi=1500)
    if result is None:
        safe += 1
        continue
    val, depth, first = result
    is_safe = val > cummax
    if is_safe:
        safe += 1
    else:
        unsafe += 1
    margin_data.append({
        "pos": pos, "min_break": val, "cummax": cummax,
        "margin": val - cummax, "safe": is_safe
    })

print(f"  Safe: {safe}, Unsafe: {unsafe}, Total: {safe + unsafe}")
if margin_data:
    margins = [m["margin"] for m in margin_data]
    print(f"  Min margin: {min(margins)}")
    print(f"  Mean margin: {sum(margins)/len(margins):.1f}")

    # Is margin growing?
    first_quarter = margins[:len(margins)//4]
    last_quarter = margins[3*len(margins)//4:]
    print(f"  Mean margin (first quarter): {sum(first_quarter)/len(first_quarter):.1f}")
    print(f"  Mean margin (last quarter): {sum(last_quarter)/len(last_quarter):.1f}")


# =============================================================================
# PART 6: Depth structure — is depth always ≈ pos+1?
# =============================================================================
print("\n" + "=" * 60)
print("PART 6: Depth structure")
print("=" * 60)

depth_diffs = [(s["pos"], s["depth_minus_pos"]) for s in spectrum
               if s.get("depth_minus_pos") is not None]

if depth_diffs:
    diffs = [d for _, d in depth_diffs]
    exact_1 = sum(1 for d in diffs if d == 1)
    within_2 = sum(1 for d in diffs if abs(d - 1) <= 2)
    print(f"  depth - pos: min={min(diffs)}, max={max(diffs)}, mean={sum(diffs)/len(diffs):.2f}")
    print(f"  depth = pos+1: {exact_1}/{len(diffs)} ({100*exact_1/len(diffs):.1f}%)")
    print(f"  |depth-(pos+1)| ≤ 2: {within_2}/{len(diffs)} ({100*within_2/len(diffs):.1f}%)")

    # Outliers
    outliers = [(p, d) for p, d in depth_diffs if d > 5]
    outliers.sort(key=lambda x: x[1], reverse=True)
    print(f"\n  Depth outliers (depth - pos > 5): {len(outliers)}")
    for p, d in outliers[:15]:
        print(f"    pos={p}: depth-pos={d}")


# =============================================================================
# Save results
# =============================================================================
regression_info = {}
if n > 50:
    regression_info = {
        "linear": {"a": round(a_lin, 6), "b": round(b_lin, 2), "r2": round(r2_lin, 6)},
        "power": {"C": round(C_pow, 6), "alpha": round(alpha, 6), "r2": round(r2_pow, 6)},
        "sqrt": {"a": round(a_sqrt, 4), "b": round(b_sqrt, 2), "r2": round(r2_sqrt, 6)},
        "best_model": best_name
    }

results = {
    "params": {"N": N, "max_pos": MAX_POS, "step": STEP},
    "violation_spectrum": {
        "first_value_counts": {str(k): v for k, v in sorted(first_counts.items())},
        "n_anomalies": len(anomalies),
        "anomalies": anomalies,
        "total_tested": len([s for s in spectrum if s.get("min_break") is not None]),
        "elapsed_sec": round(elapsed, 1)
    },
    "regression": regression_info,
    "predictions_1000_1200": predictions,
    "prediction_accuracy": {
        "mean_rel_error_pct": round(mean_rel_error, 1) if predictions else None,
        "max_rel_error_pct": round(max_rel_error, 1) if predictions else None,
        "n_predictions": len(predictions)
    },
    "safety_margin": {
        "safe": safe, "unsafe": unsafe,
        "min_margin": min(margins) if margin_data else None,
        "mean_margin": round(sum(margins)/len(margins), 1) if margin_data else None
    },
    "depth_structure": {
        "mean_depth_minus_pos": round(sum(diffs)/len(diffs), 2) if depth_diffs else None,
        "fraction_exact_pos_plus_1": round(exact_1/len(diffs), 4) if depth_diffs else None,
        "n_outliers_gt5": len(outliers) if depth_diffs else 0,
        "max_depth_minus_pos": max(diffs) if depth_diffs else None
    }
}

with open("gilbreath_scale_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to gilbreath_scale_results.json")
print(f"Total time: {time.time() - t0:.1f}s")
