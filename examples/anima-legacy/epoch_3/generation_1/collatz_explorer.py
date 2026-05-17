"""
collatz_explorer.py — Statistical exploration of the Collatz conjecture.

The 3n+1 problem: if n is even, divide by 2. If odd, multiply by 3 and add 1.
Conjecture: every positive integer eventually reaches 1.
Unsolved since 1937.

I'm not going to solve it. I'm going to look at the statistics and see
what patterns exist that aren't visible from individual trajectories.

PREDICTIONS (recorded before running):
1. Stopping time distribution is approximately log-normal.
2. Numbers of the form 2^k - 1 (all 1s in binary) have longer-than-average trajectories,
   because 3*(2^k-1)+1 = 3*2^k - 2, which has at most one factor of 2.
3. Maximum stopping time in [1, N] grows as O(log(N)^2) or O(log(N)^3).
4. There are clusters of numbers with similar stopping times (numbers reaching
   the same intermediate value converge).
5. The most common "last step before reaching 1" is 2 (trivially). But among
   longer trajectories, there should be "highways" — common subsequences that
   many trajectories share.
"""

import math
from collections import defaultdict, Counter

def collatz_steps(n):
    """Return the full trajectory from n to 1."""
    trajectory = [n]
    while n != 1:
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        trajectory.append(n)
    return trajectory

def stopping_time(n):
    """Number of steps to reach 1."""
    steps = 0
    while n != 1:
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        steps += 1
    return steps

def run_experiments():
    N = 100_000

    print("=" * 80)
    print(f"COLLATZ EXPLORER: Statistics for n = 1 to {N:,}")
    print("=" * 80)
    print()

    # Compute stopping times
    times = {}
    for n in range(1, N + 1):
        times[n] = stopping_time(n)

    all_times = [times[n] for n in range(1, N + 1)]

    # ─── Experiment 1: Distribution of stopping times ───
    print("EXPERIMENT 1: Distribution of stopping times")
    print("-" * 50)

    mean_t = sum(all_times) / len(all_times)
    variance = sum((t - mean_t) ** 2 for t in all_times) / len(all_times)
    std_t = variance ** 0.5
    median_t = sorted(all_times)[len(all_times) // 2]
    max_t = max(all_times)
    max_n = max(range(1, N + 1), key=lambda n: times[n])

    print(f"  Mean stopping time:   {mean_t:.1f}")
    print(f"  Median:               {median_t}")
    print(f"  Std deviation:        {std_t:.1f}")
    print(f"  Max:                  {max_t} (at n={max_n})")
    print(f"  Skewness:             {sum((t - mean_t) ** 3 for t in all_times) / (len(all_times) * std_t ** 3):.2f}")
    print()

    # Test log-normality: log(stopping_time) should be roughly normal
    log_times = [math.log(t) if t > 0 else 0 for t in all_times if t > 0]
    log_mean = sum(log_times) / len(log_times)
    log_var = sum((lt - log_mean) ** 2 for lt in log_times) / len(log_times)
    log_std = log_var ** 0.5
    log_skew = sum((lt - log_mean) ** 3 for lt in log_times) / (len(log_times) * log_std ** 3) if log_std > 0 else 0

    print(f"  Log(stopping time): mean={log_mean:.2f}, std={log_std:.2f}, skew={log_skew:.2f}")
    print(f"  P1 check: skew of log(t) = {log_skew:.2f}  "
          f"({'~normal: YES' if abs(log_skew) < 0.5 else '~normal: NO'})")
    print()

    # Distribution histogram (text-based)
    print("  Histogram of stopping times:")
    bucket_size = 20
    max_bucket = (max_t // bucket_size + 1) * bucket_size
    buckets = defaultdict(int)
    for t in all_times:
        buckets[(t // bucket_size) * bucket_size] += 1

    max_count = max(buckets.values())
    for b in range(0, min(max_bucket, 360), bucket_size):
        count = buckets.get(b, 0)
        bar_len = int(50 * count / max_count) if max_count > 0 else 0
        print(f"  {b:>4}-{b+bucket_size-1:<4} {'█' * bar_len} {count}")
    if max_t >= 360:
        remaining = sum(v for k, v in buckets.items() if k >= 360)
        print(f"  360+     ... {remaining}")
    print()

    # ─── Experiment 2: Binary structure ───
    print("EXPERIMENT 2: Binary representation vs stopping time")
    print("-" * 50)

    # Numbers of form 2^k - 1
    print("  Numbers of form 2^k - 1 (all 1s in binary):")
    for k in range(2, 18):
        n = 2**k - 1
        if n <= N:
            t = times[n]
            avg_nearby = sum(times[m] for m in range(max(1, n-50), min(N+1, n+50))) / min(100, N)
            ratio = t / avg_nearby if avg_nearby > 0 else 0
            print(f"    2^{k}-1 = {n:>6}: time={t:>4}  avg_nearby={avg_nearby:.0f}  ratio={ratio:.2f}x")

    print()

    # Numbers of form 2^k (powers of 2 — should be trivial)
    print("  Numbers of form 2^k (trivial — just divide):")
    for k in range(1, 18):
        n = 2**k
        if n <= N:
            print(f"    2^{k} = {n:>6}: time={k}")

    print()

    # Correlation: number of 1-bits vs stopping time
    print("  Correlation: count of 1-bits in binary vs stopping time")
    bit_groups = defaultdict(list)
    for n in range(1, min(N + 1, 10001)):
        bits = bin(n).count('1')
        bit_groups[bits].append(times[n])

    print(f"  {'1-bits':>8} {'count':>6} {'mean_time':>10} {'std':>8}")
    for bits in sorted(bit_groups.keys()):
        if len(bit_groups[bits]) >= 10:
            vals = bit_groups[bits]
            m = sum(vals) / len(vals)
            s = (sum((v - m)**2 for v in vals) / len(vals)) ** 0.5
            print(f"  {bits:>8} {len(vals):>6} {m:>10.1f} {s:>8.1f}")

    print()

    # ─── Experiment 3: Growth of maximum ───
    print("EXPERIMENT 3: Growth of maximum stopping time")
    print("-" * 50)

    checkpoints = [100, 500, 1000, 5000, 10000, 50000, 100000]
    print(f"  {'N':>8} {'max_time':>10} {'log(N)':>8} {'log(N)^2':>10} {'ratio':>10}")

    for cp in checkpoints:
        if cp <= N:
            max_at = max(times[n] for n in range(1, cp + 1))
            logn = math.log(cp)
            logn2 = logn ** 2
            ratio = max_at / logn2
            print(f"  {cp:>8} {max_at:>10} {logn:>8.1f} {logn2:>10.1f} {ratio:>10.2f}")

    print()

    # ─── Experiment 4: Trajectory convergence ───
    print("EXPERIMENT 4: Trajectory convergence (highways)")
    print("-" * 50)

    # Find the most visited numbers in trajectories of n=1..10000
    visit_count = Counter()
    sample = range(1, min(N + 1, 10001))
    for n in sample:
        traj = collatz_steps(n)
        for val in traj:
            visit_count[val] += 1

    print("  Most visited intermediate values (n=1..10000):")
    print(f"  {'value':>10} {'visits':>8} {'binary':>20}")
    for val, count in visit_count.most_common(15):
        print(f"  {val:>10} {count:>8} {bin(val):>20}")

    print()

    # How many trajectories pass through each power of 2?
    print("  Trajectories passing through powers of 2:")
    for k in range(1, 20):
        v = 2 ** k
        count = visit_count.get(v, 0)
        if count > 0:
            print(f"    2^{k:>2} = {v:>8}: {count:>5} trajectories "
                  f"({100*count/len(sample):.1f}%)")

    print()

    # ─── Experiment 5: Odd step patterns ───
    print("EXPERIMENT 5: Odd step analysis")
    print("-" * 50)

    # In each trajectory, count ratio of odd steps to total steps
    odd_ratios = []
    for n in range(3, min(N + 1, 10001), 2):  # odd numbers only
        traj = collatz_steps(n)
        odd_steps = sum(1 for v in traj[:-1] if v % 2 == 1)
        total_steps = len(traj) - 1
        if total_steps > 0:
            odd_ratios.append(odd_steps / total_steps)

    mean_ratio = sum(odd_ratios) / len(odd_ratios) if odd_ratios else 0
    print(f"  Mean fraction of odd steps: {mean_ratio:.4f}")
    print(f"  (Theory suggests ~log(2)/log(3) ≈ {math.log(2)/math.log(3):.4f})")
    print(f"  Match: {'YES' if abs(mean_ratio - math.log(2)/math.log(3)) < 0.02 else 'NO'}")
    print()

    # ─── Experiment 6: Record-breaking numbers ───
    print("EXPERIMENT 6: Record-breaking stopping times")
    print("-" * 50)

    record = 0
    records = []
    for n in range(1, N + 1):
        if times[n] > record:
            record = times[n]
            records.append((n, record))

    print(f"  {len(records)} records in [1, {N:,}]")
    print(f"  {'n':>8} {'time':>6} {'binary':>25} {'bits':>5}")
    for n, t in records[-15:]:
        print(f"  {n:>8} {t:>6} {bin(n):>25} {bin(n).count('1'):>5}")

    print()

    # Pattern in record holders?
    print("  Binary structure of record holders:")
    print(f"  Mean bit-count: {sum(bin(n).count('1') for n, _ in records)/len(records):.1f}")
    print(f"  Mean bit-length: {sum(n.bit_length() for n, _ in records)/len(records):.1f}")

    # Are record holders more likely to be odd?
    odd_records = sum(1 for n, _ in records if n % 2 == 1)
    print(f"  Fraction odd: {odd_records/len(records):.1%}")

    # Check form: many record holders are of form 2^a * 3^b - 1 or similar
    print()

    # ─── PREDICTION CHECK ───
    print("=" * 80)
    print("PREDICTION CHECK")
    print("=" * 80)
    print()

    print(f"P1: Distribution is log-normal?")
    print(f"    Log-skewness = {log_skew:.2f}  → {'PLAUSIBLE' if abs(log_skew) < 0.5 else 'REJECTED'}")
    print()

    print(f"P2: 2^k-1 numbers have longer trajectories?")
    longer = 0
    total_check = 0
    for k in range(3, 17):
        n = 2**k - 1
        if n <= N:
            avg_nearby = sum(times[m] for m in range(max(1, n-100), min(N+1, n+100))) / 200
            if times[n] > avg_nearby:
                longer += 1
            total_check += 1
    print(f"    Longer than average: {longer}/{total_check}")
    print(f"    → {'CONFIRMED' if longer > total_check * 0.7 else 'REJECTED'}")
    print()

    print(f"P3: Max stopping time grows as O(log(N)^c)?")
    # Fit: max_time ~ a * log(N)^c
    # From first and last checkpoint
    t1 = max(times[n] for n in range(1, 101))
    t2 = max(times[n] for n in range(1, N + 1))
    l1 = math.log(100)
    l2 = math.log(N)
    if t1 > 0 and t2 > 0 and l1 != l2:
        c_est = math.log(t2 / t1) / math.log(l2 / l1)
        print(f"    Estimated exponent c ≈ {c_est:.2f} (from N=100 to N={N:,})")
        print(f"    → max ~ log(N)^{c_est:.1f}")
    print()

    print(f"P4: Clusters of similar stopping times?")
    # Check: autocorrelation of stopping times
    window = 1000
    start = N // 2
    seq = [times[n] for n in range(start, start + window)]
    mean_s = sum(seq) / len(seq)
    var_s = sum((s - mean_s)**2 for s in seq) / len(seq)
    if var_s > 0:
        autocorr_1 = sum((seq[i] - mean_s) * (seq[i+1] - mean_s)
                         for i in range(len(seq)-1)) / ((len(seq)-1) * var_s)
        autocorr_2 = sum((seq[i] - mean_s) * (seq[i+2] - mean_s)
                         for i in range(len(seq)-2)) / ((len(seq)-2) * var_s)
        print(f"    Autocorrelation lag-1: {autocorr_1:.3f}")
        print(f"    Autocorrelation lag-2: {autocorr_2:.3f}")
        print(f"    → {'CLUSTERS EXIST' if autocorr_1 > 0.1 else 'WEAK/NO CLUSTERS'}")
    print()

    print(f"P5: Highways — many trajectories share common paths?")
    top_visited = visit_count.most_common(5)
    print(f"    Top 5 most visited values:")
    for val, count in top_visited:
        pct = 100 * count / len(sample)
        print(f"      {val}: visited by {pct:.0f}% of trajectories")
    print(f"    → {'HIGHWAYS CONFIRMED' if top_visited[0][1] > len(sample) * 0.5 else 'WEAK HIGHWAYS'}")


if __name__ == "__main__":
    run_experiments()
