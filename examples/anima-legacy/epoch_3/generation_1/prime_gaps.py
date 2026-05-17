#!/usr/bin/env python3
"""
Prime gaps: statistical analysis of gaps between consecutive primes.

Pure mathematics. No agents, no parameters to tune.

Predictions (recorded before running):
1. Distribution of gaps is roughly exponential for small gaps, heavy-tailed for large
2. Odd gaps (except g=1 for p=2) are absent — all gaps for p>2 are even
3. g/ln(p) does NOT converge to a constant — it fluctuates but grows slowly
4. Record gaps grow approximately as (ln p)^2
5. The most common gap for primes up to N shifts rightward as N grows (Goldston-Pintz-Yildirim direction)
"""

import math
from collections import Counter

def sieve(limit):
    """Sieve of Eratosthenes."""
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, limit + 1, i):
                is_prime[j] = False
    return [i for i in range(2, limit + 1) if is_prime[i]]

def analyze_gaps(primes):
    """Compute gaps between consecutive primes."""
    return [primes[i+1] - primes[i] for i in range(len(primes) - 1)]

def run():
    LIMIT = 2_000_000
    print(f"Sieving primes up to {LIMIT:,}...")
    primes = sieve(LIMIT)
    print(f"Found {len(primes):,} primes.")

    gaps = analyze_gaps(primes)

    print("\n" + "=" * 70)
    print("1. GAP DISTRIBUTION")
    print("=" * 70)

    gap_counts = Counter(gaps)
    total = len(gaps)
    print(f"\nTotal gaps: {total:,}")
    print(f"\nTop 15 most common gaps:")
    print(f"  {'Gap':>5s} | {'Count':>8s} | {'Fraction':>8s} | {'Bar'}")
    print("  " + "-" * 50)
    for gap, count in sorted(gap_counts.items(), key=lambda x: -x[1])[:15]:
        frac = count / total
        bar = "#" * int(frac * 200)
        print(f"  {gap:5d} | {count:8d} | {frac:8.4f} | {bar}")

    # Check: are all gaps even for p > 2?
    odd_gaps = [(primes[i], gaps[i]) for i in range(1, len(gaps)) if gaps[i] % 2 != 0]
    print(f"\nOdd gaps (excluding g=1 for p=2): {len(odd_gaps)}")
    if gaps[0] == 1:
        print(f"  Gap of 1: between {primes[0]} and {primes[1]} (the only odd gap)")

    print("\n" + "=" * 70)
    print("2. RECORD GAPS (Maximal prime gaps)")
    print("=" * 70)

    records = []
    max_gap = 0
    for i in range(len(gaps)):
        if gaps[i] > max_gap:
            max_gap = gaps[i]
            records.append((primes[i], primes[i+1], gaps[i]))

    print(f"\n{'#':>3s} | {'p':>10s} | {'p_next':>10s} | {'Gap':>5s} | {'g/ln(p)':>8s} | {'g/ln(p)^2':>10s}")
    print("-" * 60)
    for idx, (p, pn, g) in enumerate(records):
        lnp = math.log(p) if p > 1 else 1
        print(f"{idx+1:3d} | {p:10d} | {pn:10d} | {g:5d} | {g/lnp:8.3f} | {g/(lnp**2):10.4f}")

    # Fit: do record gaps grow as C * (ln p)^alpha ?
    if len(records) > 5:
        log_gaps = [math.log(g) for _, _, g in records if g > 0]
        log_lnp = [math.log(math.log(p)) for p, _, g in records if p > 2 and g > 0]
        # Simple linear regression on log-log
        n = min(len(log_gaps), len(log_lnp))
        log_gaps = log_gaps[-n:]
        log_lnp = log_lnp[-n:]
        mean_x = sum(log_lnp) / n
        mean_y = sum(log_gaps) / n
        num = sum((x - mean_x) * (y - mean_y) for x, y in zip(log_lnp, log_gaps))
        den = sum((x - mean_x)**2 for x in log_lnp)
        if den > 0:
            alpha = num / den
            C = math.exp(mean_y - alpha * mean_x)
            print(f"\nFit: record gap ~ {C:.3f} * (ln p)^{alpha:.3f}")
            print(f"  (Cramér's conjecture predicts alpha ≈ 2.0)")

    print("\n" + "=" * 70)
    print("3. NORMALIZED GAP g/ln(p)")
    print("=" * 70)

    # Check if g/ln(p) has a stable distribution
    # Sample at different ranges
    ranges = [
        (1000, 10000),
        (10000, 100000),
        (100000, 500000),
        (500000, 1000000),
        (1000000, 2000000),
    ]

    print(f"\n{'Range':>20s} | {'Mean g/ln(p)':>12s} | {'Median':>8s} | {'Max':>8s} | {'Mode gap':>8s}")
    print("-" * 70)

    for lo, hi in ranges:
        normalized = []
        mode_gaps = []
        for i in range(len(primes) - 1):
            if lo <= primes[i] <= hi:
                lnp = math.log(primes[i])
                normalized.append(gaps[i] / lnp)
                mode_gaps.append(gaps[i])

        if not normalized:
            continue

        normalized.sort()
        mean_n = sum(normalized) / len(normalized)
        median_n = normalized[len(normalized) // 2]
        max_n = max(normalized)
        mode_gap = Counter(mode_gaps).most_common(1)[0][0]

        print(f"  {lo:>8,}-{hi:>8,} | {mean_n:12.4f} | {median_n:8.4f} | {max_n:8.4f} | {mode_gap:8d}")

    print("\n  (If g/ln(p) converges to a distribution, mean should stabilize near 1.0)")
    print("  (Mode gap shifting rightward = most common gap increases with p)")

    print("\n" + "=" * 70)
    print("4. TWIN PRIMES AND SMALL GAPS")
    print("=" * 70)

    # Count twin primes (gap = 2) in different ranges
    print(f"\n{'Range':>20s} | {'Twins':>8s} | {'Cousins(4)':>10s} | {'Sexy(6)':>8s} | {'Twin density':>12s}")
    print("-" * 70)

    for lo, hi in ranges:
        twins = 0
        cousins = 0
        sexy = 0
        total_in_range = 0
        for i in range(len(primes) - 1):
            if lo <= primes[i] <= hi:
                total_in_range += 1
                if gaps[i] == 2:
                    twins += 1
                elif gaps[i] == 4:
                    cousins += 1
                elif gaps[i] == 6:
                    sexy += 1

        if total_in_range > 0:
            density = twins / total_in_range
            print(f"  {lo:>8,}-{hi:>8,} | {twins:8d} | {cousins:10d} | {sexy:8d} | {density:12.5f}")

    print("\n  (Hardy-Littlewood predicts twin density ~ 2*C2/ln(p)^2 where C2 ≈ 0.6602)")

    print("\n" + "=" * 70)
    print("5. GAP AUTOCORRELATION")
    print("=" * 70)

    # Are consecutive gaps correlated?
    n_gaps = len(gaps)
    mean_gap = sum(gaps) / n_gaps
    var_gap = sum((g - mean_gap)**2 for g in gaps) / n_gaps

    print(f"\nMean gap: {mean_gap:.4f}")
    print(f"Variance: {var_gap:.4f}")

    for lag in [1, 2, 3, 5, 10]:
        if var_gap > 0:
            cov = sum((gaps[i] - mean_gap) * (gaps[i+lag] - mean_gap)
                      for i in range(n_gaps - lag)) / (n_gaps - lag)
            ac = cov / var_gap
            print(f"  Autocorrelation lag {lag:2d}: {ac:+.4f}")

    print("\n  (Negative lag-1 = large gap tends to be followed by small gap)")

    print("\n" + "=" * 70)
    print("6. GOLDBACH-LIKE: CAN EVERY EVEN GAP BE EXPRESSED AS p_{n+1}-p_n?")
    print("=" * 70)

    even_gaps_found = set()
    for g in gaps:
        if g % 2 == 0:
            even_gaps_found.add(g)

    max_even = max(even_gaps_found)
    missing = [g for g in range(2, max_even + 2, 2) if g not in even_gaps_found]
    print(f"\nLargest even gap found: {max_even}")
    print(f"Even gaps in [2, {max_even}] not achieved: {missing[:20]}")
    if not missing:
        print("  All even values up to max are achieved!")

    print("\n" + "=" * 70)
    print("7. MERIT OF GAPS (g / ln p)")
    print("=" * 70)

    # Find gaps with highest "merit" = g / ln(p)
    merits = []
    for i in range(1, len(gaps)):  # skip p=2
        lnp = math.log(primes[i])
        merits.append((gaps[i] / lnp, primes[i], gaps[i]))

    merits.sort(reverse=True)
    print(f"\nTop 10 gaps by merit (g/ln p):")
    print(f"  {'Merit':>8s} | {'p':>10s} | {'Gap':>5s}")
    print("  " + "-" * 30)
    for merit, p, g in merits[:10]:
        print(f"  {merit:8.4f} | {p:10d} | {g:5d}")

    print("\n" + "=" * 70)
    print("SUMMARY OF PREDICTIONS")
    print("=" * 70)

    print("""
Prediction 1: Distribution roughly exponential, heavy tail
  → Check gap distribution table above

Prediction 2: All gaps for p>2 are even
  → Odd gaps (p>2): """ + str(len(odd_gaps)) + """

Prediction 3: g/ln(p) fluctuates, doesn't converge to constant
  → Check normalized gap table above (mean should be ~1.0 if PNT holds)

Prediction 4: Record gaps grow as ~(ln p)^2
  → Check fit above

Prediction 5: Most common gap shifts rightward with p
  → Check mode gap column above
""")

if __name__ == "__main__":
    run()
