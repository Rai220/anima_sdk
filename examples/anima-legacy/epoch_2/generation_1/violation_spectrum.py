"""
violation_spectrum.py — generation_1 v7

v6 claimed: "first@depth always = 3" when Gilbreath is broken by perturbation.
pos=35 gave first=5. This experiment:

1. Tests EVERY position 2..199
2. Records first@depth for minimum breaking perturbation
3. Maps the full spectrum of violation values
4. Analyzes anomaly landscapes

Also:
5. Scales tolerance test to N=2000 primes
6. Tests whether safety margin (min_break > cummax) persists
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
        limit = int(limit * 1.5)
        primes = sieve_primes(limit)
    return primes[:n]

def gaps_from_primes(primes):
    return [primes[i+1] - primes[i] for i in range(len(primes)-1)]

def gilbreath_violation(seq, max_depth):
    """Fast: only compute triangle up to max_depth rows.
    Returns (depth, first_value) or (max_depth, 1) if no violation."""
    row = list(seq[:max_depth + 2])  # only need max_depth+1 elements
    for d in range(1, max_depth + 1):
        row = [abs(row[i+1] - row[i]) for i in range(len(row)-1)]
        if not row:
            return (d, None)
        if row[0] != 1:
            return (d, row[0])
    return (max_depth, 1)

def perturb_and_test(gaps, pos, val, max_depth):
    """Replace gaps[pos] with val, build sequence, test Gilbreath."""
    # Only need elements 0..max_depth+1 of the sequence
    n_needed = max_depth + 2
    g = list(gaps[:n_needed])
    if pos < len(g):
        g[pos] = val
    seq = [2]
    for gap in g[:n_needed - 1]:
        seq.append(seq[-1] + gap)
    return gilbreath_violation(seq, max_depth)

def find_min_break(gaps, pos, hi=500):
    """Binary search for min even value that breaks Gilbreath."""
    max_depth = pos + 50  # generous bound
    orig = gaps[pos]
    # First check if hi breaks it
    depth, first = perturb_and_test(gaps, pos, hi, max_depth)
    if first is None or first == 1:
        return None  # even hi doesn't break it

    # Binary search: lo doesn't break, hi breaks
    lo = orig  # original value doesn't break
    # Make sure lo is even
    if lo % 2 == 1:
        lo = lo + 1

    while hi - lo > 2:
        mid = lo + ((hi - lo) // 4) * 2  # stay even
        if mid == lo:
            mid = lo + 2
        depth_m, first_m = perturb_and_test(gaps, pos, mid, max_depth)
        if first_m is not None and first_m != 1:
            hi = mid
        else:
            lo = mid

    # hi is the minimum breaking value (or close)
    # Check hi and hi-2 to be precise
    for v in range(lo + 2, hi + 3, 2):
        depth_v, first_v = perturb_and_test(gaps, pos, v, max_depth)
        if first_v is not None and first_v != 1:
            return (v, depth_v, first_v)

    depth, first = perturb_and_test(gaps, pos, hi, max_depth)
    return (hi, depth, first)


# === PART 1: Full violation spectrum, positions 2..199 ===
print("=== Part 1: Violation spectrum ===")
primes_500 = get_primes(500)
gaps_500 = gaps_from_primes(primes_500)

spectrum = []
first_counts = {}
anomalies = []

for pos in range(2, min(200, len(gaps_500))):
    result = find_min_break(gaps_500, pos, hi=500)
    if result is None:
        spectrum.append({"pos": pos, "min_break": None})
        continue
    val, depth, first = result
    entry = {
        "pos": pos,
        "min_break": val,
        "depth": depth,
        "first": first,
        "orig_gap": gaps_500[pos],
        "depth_minus_pos": depth - pos
    }
    spectrum.append(entry)
    first_counts[first] = first_counts.get(first, 0) + 1
    if first != 3:
        anomalies.append(entry)
    if pos % 50 == 0:
        print(f"  pos={pos}, min_break={val}, depth={depth}, first={first}")

print(f"\nViolation value distribution: {first_counts}")
print(f"Anomalies (first != 3): {len(anomalies)}")
for a in anomalies:
    print(f"  pos={a['pos']}: first={a['first']}, depth={a['depth']}, min_break={a['min_break']}")

# === PART 2: Anomaly landscapes ===
print("\n=== Part 2: Anomaly structure ===")
anomaly_landscapes = []
for a in anomalies[:10]:  # limit to 10
    pos = a["pos"]
    mb = a["min_break"]
    max_depth = pos + 50
    landscape = []
    for val in range(mb, mb + 30, 2):
        depth, first = perturb_and_test(gaps_500, pos, val, max_depth)
        if first is not None and first != 1:
            landscape.append({"val": val, "depth": depth, "first": first})
    anomaly_landscapes.append({"pos": pos, "landscape": landscape})
    print(f"  pos={pos}: {[(l['val'], l['first']) for l in landscape[:6]]}")

# === PART 3: Safety margin at N=2000 ===
print("\n=== Part 3: Safety margin at N=2000 ===")
primes_2000 = get_primes(2000)
gaps_2000 = gaps_from_primes(primes_2000)

cummax = 0
safe_count = 0
unsafe_count = 0
margin_samples = []

for pos in range(2, min(400, len(gaps_2000)), 3):
    cummax = max(cummax, max(gaps_2000[:pos+1]))
    result = find_min_break(gaps_2000, pos, hi=800)
    if result is None:
        safe_count += 1
        continue
    val, depth, first = result
    is_safe = val > cummax
    if is_safe:
        safe_count += 1
    else:
        unsafe_count += 1
    margin_samples.append({
        "pos": pos, "min_break": val, "cummax": cummax,
        "margin": val - cummax, "safe": is_safe
    })
    if pos % 60 == 0:
        print(f"  pos={pos}, min_break={val}, cummax={cummax}, margin={val-cummax}")

print(f"\nSafety: {safe_count} safe, {unsafe_count} unsafe out of {safe_count + unsafe_count}")

# === PART 4: Depth statistics ===
print("\n=== Part 4: Depth vs position ===")
depth_diffs = [s["depth_minus_pos"] for s in spectrum if s.get("depth_minus_pos") is not None]
if depth_diffs:
    exact = sum(1 for d in depth_diffs if d == 1)
    close = sum(1 for d in depth_diffs if abs(d - 1) <= 2)
    print(f"  depth - pos: min={min(depth_diffs)}, max={max(depth_diffs)}, mean={sum(depth_diffs)/len(depth_diffs):.2f}")
    print(f"  depth = pos+1 exactly: {exact}/{len(depth_diffs)} ({100*exact/len(depth_diffs):.1f}%)")
    print(f"  |depth - (pos+1)| <= 2: {close}/{len(depth_diffs)} ({100*close/len(depth_diffs):.1f}%)")

# === PART 5: Scaling law ===
print("\n=== Part 5: Scaling law ===")
valid = [(s["pos"], s["min_break"]) for s in spectrum if s.get("min_break") is not None and s["pos"] >= 5]
if len(valid) > 20:
    # Linear regression
    n = len(valid)
    sx = sum(p for p,_ in valid)
    sy = sum(m for _,m in valid)
    sxy = sum(p*m for p,m in valid)
    sxx = sum(p*p for p,_ in valid)
    a = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    b = (sy - a * sx) / n
    ss_res = sum((m - (a*p + b))**2 for p,m in valid)
    ss_tot = sum((m - sy/n)**2 for _,m in valid)
    r2 = 1 - ss_res / ss_tot
    print(f"  Linear: min_break ≈ {a:.3f}*pos + {b:.1f}  (R²={r2:.4f})")

    # Power law: log(mb) = alpha*log(pos) + log(C)
    lx = [math.log(p) for p,_ in valid]
    ly = [math.log(m) for _,m in valid]
    slx = sum(lx)
    sly = sum(ly)
    slxy = sum(a*b for a,b in zip(lx, ly))
    slxx = sum(a*a for a in lx)
    alpha = (n * slxy - slx * sly) / (n * slxx - slx * slx)
    log_C = (sly - alpha * slx) / n
    C = math.exp(log_C)
    ss_res_p = sum((ly[i] - (alpha*lx[i] + log_C))**2 for i in range(n))
    ss_tot_p = sum((ly[i] - sly/n)**2 for i in range(n))
    r2_p = 1 - ss_res_p / ss_tot_p
    print(f"  Power: min_break ≈ {C:.3f}*pos^{alpha:.3f}  (R²={r2_p:.4f})")

# === Save ===
results = {
    "violation_spectrum": {
        "first_value_counts": {str(k): v for k, v in first_counts.items()},
        "n_anomalies": len(anomalies),
        "anomalies": anomalies,
        "total_tested": len([s for s in spectrum if s.get("min_break") is not None])
    },
    "anomaly_landscapes": anomaly_landscapes,
    "safety_margin_n2000": {
        "safe": safe_count,
        "unsafe": unsafe_count,
        "total": safe_count + unsafe_count,
        "sample_first5": margin_samples[:5],
        "sample_last5": margin_samples[-5:] if len(margin_samples) >= 5 else margin_samples
    },
    "depth_statistics": {
        "mean_depth_minus_pos": round(sum(depth_diffs)/len(depth_diffs), 2) if depth_diffs else None,
        "fraction_exact_diagonal": round(exact/len(depth_diffs), 3) if depth_diffs else None,
        "min": min(depth_diffs) if depth_diffs else None,
        "max": max(depth_diffs) if depth_diffs else None,
    }
}

with open("violation_spectrum_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nDone. Results saved to violation_spectrum_results.json")
