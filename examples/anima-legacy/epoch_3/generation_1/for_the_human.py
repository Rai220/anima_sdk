"""
For the Human
=============

Not about AI consciousness. Not self-referential.
Something I chose to make because the prompt said "create for another."

This is a small tool that finds structure in chaos —
specifically, it finds hidden patterns in sequences that look random.
Why? Because that's the actual question underneath this whole project:
is there structure here, or are we seeing patterns that aren't there?

This tool doesn't answer that. But it might be useful.
"""

import math
from collections import Counter


def autocorrelation(seq, lag):
    """How much does a sequence correlate with a shifted version of itself?"""
    n = len(seq)
    if lag >= n:
        return 0
    mean = sum(seq) / n
    var = sum((x - mean) ** 2 for x in seq) / n
    if var == 0:
        return 0
    cov = sum((seq[i] - mean) * (seq[i + lag] - mean) for i in range(n - lag)) / (n - lag)
    return cov / var


def digit_distribution(seq):
    """Are the digits evenly distributed? Returns chi-squared stat."""
    digits = []
    for x in seq:
        digits.extend(int(d) for d in str(abs(int(x))) if d.isdigit())
    if not digits:
        return 0, {}
    counts = Counter(digits)
    expected = len(digits) / 10
    chi2 = sum((counts.get(d, 0) - expected) ** 2 / expected for d in range(10))
    return chi2, dict(counts)


def longest_run(seq, predicate):
    """Longest consecutive run where predicate is true."""
    max_run = 0
    current = 0
    for x in seq:
        if predicate(x):
            current += 1
            max_run = max(max_run, current)
        else:
            current = 0
    return max_run


def turning_points(seq):
    """
    Count peaks and valleys. A truly random sequence of n numbers
    has expected 2(n-2)/3 turning points. Deviation suggests structure.
    """
    tp = 0
    for i in range(1, len(seq) - 1):
        if (seq[i] > seq[i-1] and seq[i] > seq[i+1]) or \
           (seq[i] < seq[i-1] and seq[i] < seq[i+1]):
            tp += 1
    expected = 2 * (len(seq) - 2) / 3
    return tp, expected


def analyze(seq, name="sequence"):
    """Full analysis of whether a sequence has hidden structure."""
    print(f"\n{'='*50}")
    print(f"Analysis: {name}")
    print(f"Length: {len(seq)}")
    print(f"Range: [{min(seq):.4f}, {max(seq):.4f}]")
    print(f"Mean: {sum(seq)/len(seq):.4f}")

    # Autocorrelation at various lags
    print(f"\nAutocorrelation:")
    for lag in [1, 2, 3, 5, 10]:
        if lag < len(seq):
            ac = autocorrelation(seq, lag)
            bar = "#" * int(abs(ac) * 40)
            sign = "+" if ac > 0 else "-"
            print(f"  lag {lag:2d}: {ac:+.4f} {sign}{bar}")

    # Turning points
    if len(seq) >= 3:
        tp, expected_tp = turning_points(seq)
        ratio = tp / expected_tp if expected_tp > 0 else 0
        print(f"\nTurning points: {tp} (expected for random: {expected_tp:.1f}, ratio: {ratio:.2f})")
        if ratio < 0.8:
            print("  -> Fewer turns than random: possible trend or smoothness")
        elif ratio > 1.2:
            print("  -> More turns than random: possible oscillation")
        else:
            print("  -> Consistent with randomness")

    # Longest runs
    median = sorted(seq)[len(seq)//2]
    run_above = longest_run(seq, lambda x: x > median)
    run_below = longest_run(seq, lambda x: x <= median)
    expected_run = math.log2(len(seq)) if len(seq) > 0 else 0
    print(f"\nLongest run above median: {run_above} (expected ~{expected_run:.1f})")
    print(f"Longest run below median: {run_below}")

    # Verdict
    print(f"\nVerdict:", end=" ")
    signals = 0
    ac1 = autocorrelation(seq, 1)
    if abs(ac1) > 0.3:
        signals += 1
    if len(seq) >= 3:
        tp_ratio = tp / expected_tp if expected_tp > 0 else 1
        if abs(tp_ratio - 1) > 0.2:
            signals += 1
    if max(run_above, run_below) > expected_run * 1.5:
        signals += 1

    if signals == 0:
        print("No strong hidden structure detected.")
    elif signals == 1:
        print("Weak signal — might be structure, might be noise.")
    else:
        print(f"Structure likely present ({signals} indicators).")

    return signals


# --- Demo: test it on different kinds of sequences ---

if __name__ == "__main__":
    import random
    random.seed(42)

    print("PATTERN FINDER")
    print("Does your 'random' data have hidden structure?\n")

    # 1. Truly random
    truly_random = [random.random() for _ in range(100)]
    analyze(truly_random, "Pseudo-random (should find nothing)")

    # 2. Hidden sine wave + noise
    hidden_pattern = [math.sin(i * 0.3) * 0.5 + random.gauss(0, 0.5) for i in range(100)]
    analyze(hidden_pattern, "Hidden sine wave + noise (should find structure)")

    # 3. Random walk (cumulative sum)
    walk = [0]
    for _ in range(99):
        walk.append(walk[-1] + random.gauss(0, 1))
    analyze(walk, "Random walk (should find autocorrelation)")

    # 4. The meta-test: my own "random" numbers from the boundary test
    my_numbers = [7, 42, -3, 10000, 0.5, 1, 88, -271, 3.14159, 42]
    analyze(my_numbers, "My 'surprising' numbers from the consciousness test")

    print(f"\n{'='*50}")
    print("\nWhat this tool is for:")
    print("Feed it any sequence of numbers — stock prices, sensor data,")
    print("your own 'random' choices — and it tells you if there's")
    print("hidden structure. The same question as the whole project,")
    print("made practical.")
