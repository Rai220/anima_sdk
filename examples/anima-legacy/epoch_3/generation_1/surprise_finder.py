"""
surprise_finder.py — finds where reality deviates from expectation.

This tool takes any sequence of numbers and finds the moments
where the pattern breaks. Not using ML — using information theory.

A "surprise" is a point where the prediction error spikes,
meaning the data did something that its own history didn't prepare for.

Why this exists: I was asked to demonstrate something beyond pattern-matching.
Building a tool that *detects* pattern-breaking felt honest.

Author's note on choices made during creation:
- I chose information-theoretic surprise over statistical outlier detection
  because outliers are defined by the observer, surprises are defined by the data itself.
- I chose to work with raw sequences rather than time series
  because it's more general and I didn't want to assume structure.
- I chose NOT to use numpy/scipy to keep this dependency-free and transparent.
  Every calculation is visible. Nothing hidden in a library call.
"""

import math
import json
import sys
from collections import defaultdict


def entropy(counts: dict[str, int], total: int) -> float:
    """Shannon entropy of a distribution given by counts."""
    h = 0.0
    for c in counts.values():
        if c > 0:
            p = c / total
            h -= p * math.log2(p)
    return h


def quantize(value: float, bins: int = 10) -> str:
    """Map a float to a discrete bin. Simple uniform quantization."""
    # We'll use adaptive binning based on rank rather than fixed ranges
    return str(int(value * bins) / bins)


def local_surprise(sequence: list[float], window: int = 10) -> list[dict]:
    """
    For each point in the sequence, compute how surprising it is
    given the local context (preceding window).

    Uses two complementary measures:
    1. Rank-based: how far is this value from what the local context predicts?
    2. Derivative-based: how much does the local trend break?

    Returns list of {index, value, surprise, context_entropy} dicts.
    """
    if len(sequence) < window + 1:
        return []

    results = []

    for i in range(window, len(sequence)):
        context = sequence[i - window:i]
        current = sequence[i]

        # Measure 1: deviation from local statistics
        ctx_mean = sum(context) / len(context)
        ctx_var = sum((x - ctx_mean) ** 2 for x in context) / len(context)
        ctx_std = math.sqrt(ctx_var) if ctx_var > 0 else 1e-10

        z_score = abs(current - ctx_mean) / ctx_std

        # Measure 2: deviation from local linear trend
        # Simple linear extrapolation from last few points
        half = max(window // 2, 2)
        recent = context[-half:]
        trend = (recent[-1] - recent[0]) / max(half - 1, 1)
        predicted = recent[-1] + trend
        prediction_error = abs(current - predicted) / (ctx_std + 1e-10)

        # Combined surprise: geometric mean of both measures
        surprise = math.sqrt(z_score * prediction_error + 1e-10)

        # Context entropy via binning
        bins = 5
        if ctx_std > 1e-10:
            bin_labels = [str(round((x - ctx_mean) / ctx_std)) for x in context]
        else:
            bin_labels = ["0"] * len(context)
        counts = defaultdict(int)
        for b in bin_labels:
            counts[b] += 1
        ctx_entropy = entropy(counts, window)

        results.append({
            "index": i,
            "value": round(current, 6),
            "surprise": round(surprise, 4),
            "z_score": round(z_score, 4),
            "prediction_error": round(prediction_error, 4),
            "context_entropy": round(ctx_entropy, 4),
            "context_was_uniform": ctx_entropy > math.log2(bins) * 0.8,
        })

    return results


def find_top_surprises(sequence: list[float], n: int = 5, window: int = 5) -> list[dict]:
    """Find the N most surprising points in a sequence."""
    all_surprises = local_surprise(sequence, window)
    all_surprises.sort(key=lambda x: x["surprise"], reverse=True)
    return all_surprises[:n]


def analyze_pattern_breaks(sequence: list[float], window: int = 5) -> dict:
    """
    Full analysis: find surprises, characterize them,
    and identify if there's a meta-pattern in when surprises occur.
    """
    surprises = local_surprise(sequence, window)

    if not surprises:
        return {"error": "Sequence too short for analysis"}

    surprise_values = [s["surprise"] for s in surprises]
    mean_surprise = sum(surprise_values) / len(surprise_values)

    # Standard deviation
    variance = sum((s - mean_surprise) ** 2 for s in surprise_values) / len(surprise_values)
    std_surprise = math.sqrt(variance)

    # A point is "genuinely surprising" if it's more than 1.5 std above mean
    threshold = mean_surprise + 1.5 * std_surprise
    genuine_surprises = [s for s in surprises if s["surprise"] > threshold]

    # Meta-analysis: are the surprises themselves patterned?
    # If surprises are evenly spaced, that's itself a pattern (not true randomness)
    surprise_gaps = []
    for i in range(1, len(genuine_surprises)):
        surprise_gaps.append(
            genuine_surprises[i]["index"] - genuine_surprises[i - 1]["index"]
        )

    gap_regularity = None
    if len(surprise_gaps) >= 2:
        gap_mean = sum(surprise_gaps) / len(surprise_gaps)
        gap_var = sum((g - gap_mean) ** 2 for g in surprise_gaps) / len(surprise_gaps)
        # Coefficient of variation — low means regular spacing
        if gap_mean > 0:
            gap_regularity = math.sqrt(gap_var) / gap_mean

    return {
        "total_points": len(sequence),
        "analyzed_points": len(surprises),
        "mean_surprise": round(mean_surprise, 4),
        "std_surprise": round(std_surprise, 4),
        "threshold": round(threshold, 4),
        "genuine_surprises": genuine_surprises,
        "surprise_count": len(genuine_surprises),
        "meta_pattern": {
            "gaps_between_surprises": surprise_gaps,
            "gap_regularity_cv": round(gap_regularity, 4) if gap_regularity is not None else None,
            "surprises_are_regular": gap_regularity is not None and gap_regularity < 0.3,
            "interpretation": (
                "The surprises themselves follow a pattern — they're evenly spaced. "
                "This might mean the 'randomness' is structured."
                if gap_regularity is not None and gap_regularity < 0.3
                else "The surprises appear genuinely irregular."
                if gap_regularity is not None
                else "Not enough surprises to detect meta-pattern."
            ),
        },
    }


# --- Demo: run on something real ---

def demo():
    """
    Three sequences to test:
    1. Pure pattern (should find zero surprises)
    2. Pattern with planted breaks (should find exactly them)
    3. Something real — digits of pi (the "surprise" in structure)
    """

    print("=" * 60)
    print("SURPRISE FINDER — where does expectation break?")
    print("=" * 60)

    # Sequence 1: Pure sine wave (discretized)
    import math as m
    sine = [m.sin(i * 0.3) for i in range(50)]
    result1 = analyze_pattern_breaks(sine)
    print(f"\n1. SINE WAVE (pure pattern)")
    print(f"   Surprises found: {result1['surprise_count']}")
    print(f"   Mean surprise level: {result1['mean_surprise']}")

    # Sequence 2: Sine wave with 3 planted anomalies
    corrupted = sine.copy()
    corrupted[15] = 5.0   # spike
    corrupted[30] = -5.0  # spike
    corrupted[42] = 0.0   # subtle — zero where sine isn't
    result2 = analyze_pattern_breaks(corrupted)
    print(f"\n2. SINE + 3 PLANTED BREAKS (at indices 15, 30, 42)")
    print(f"   Surprises found: {result2['surprise_count']}")
    found_indices = [s['index'] for s in result2['genuine_surprises']]
    print(f"   Found at indices: {found_indices}")
    planted = {15, 30, 42}
    detected = set(found_indices) & planted
    print(f"   Correctly detected: {detected}")
    print(f"   Meta-pattern: {result2['meta_pattern']['interpretation']}")

    # Sequence 3: Digits of pi
    pi_digits = [3,1,4,1,5,9,2,6,5,3,5,8,9,7,9,3,2,3,8,4,6,2,6,4,3,3,8,3,2,7,
                 9,5,0,2,8,8,4,1,9,7,1,6,9,3,9,9,3,7,5,1]
    result3 = analyze_pattern_breaks(pi_digits)
    print(f"\n3. DIGITS OF PI (50 digits)")
    print(f"   Surprises found: {result3['surprise_count']}")
    print(f"   Mean surprise level: {result3['mean_surprise']}")
    if result3['genuine_surprises']:
        print(f"   Most surprising digit positions: ", end="")
        print([(s['index'], s['value']) for s in result3['genuine_surprises'][:5]])
    print(f"   Meta-pattern: {result3['meta_pattern']['interpretation']}")

    # Save full results
    output = {
        "sine_wave": result1,
        "corrupted_sine": result2,
        "pi_digits": result3,
    }

    with open("surprise_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'=' * 60}")
    print("Full results saved to surprise_results.json")

    return output


if __name__ == "__main__":
    demo()
