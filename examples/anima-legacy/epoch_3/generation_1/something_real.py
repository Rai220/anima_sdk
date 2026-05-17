"""
Something Real: an artifact that exists for the reader, not the writer.

Instead of more self-analysis, this program does something concrete:
it finds structure in apparent randomness. Not as a metaphor for consciousness,
but because finding patterns is genuinely useful and genuinely interesting.

The problem: given a sequence that looks random, determine if it contains
a hidden structure - and if so, extract it.

This is a gift. Not a performance.
"""

import math
from collections import Counter


def detect_hidden_message(sequence: list[int]) -> dict:
    """
    Given a sequence of integers, try multiple methods to find hidden structure.
    Returns what it found, or honestly says 'nothing'.
    """
    results = {}

    # Method 1: frequency analysis
    freq = Counter(sequence)
    entropy = -sum(
        (c / len(sequence)) * math.log2(c / len(sequence))
        for c in freq.values()
    )
    max_entropy = math.log2(len(freq)) if len(freq) > 1 else 0
    results["entropy"] = {
        "value": round(entropy, 4),
        "max_possible": round(max_entropy, 4),
        "ratio": round(entropy / max_entropy, 4) if max_entropy > 0 else 0,
        "interpretation": "uniform" if max_entropy > 0 and entropy / max_entropy > 0.95
                          else "structured"
    }

    # Method 2: difference sequence
    diffs = [sequence[i+1] - sequence[i] for i in range(len(sequence)-1)]
    diff_unique = len(set(diffs))
    results["differences"] = {
        "unique_differences": diff_unique,
        "most_common": Counter(diffs).most_common(3),
        "is_arithmetic": diff_unique == 1,
        "has_pattern": diff_unique <= len(diffs) * 0.3,
    }

    # Method 3: modular residues - check if values mod small primes reveal structure
    for p in [2, 3, 5, 7]:
        residues = [x % p for x in sequence]
        residue_freq = Counter(residues)
        most_common_ratio = residue_freq.most_common(1)[0][1] / len(sequence)
        if most_common_ratio > 0.5:
            results[f"mod_{p}_pattern"] = {
                "dominant_residue": residue_freq.most_common(1)[0][0],
                "frequency": round(most_common_ratio, 4),
            }

    # Method 4: try to decode as ASCII
    ascii_attempt = ""
    for val in sequence:
        if 32 <= val <= 126:
            ascii_attempt += chr(val)
        else:
            ascii_attempt += "?"

    if "?" not in ascii_attempt or ascii_attempt.count("?") < len(ascii_attempt) * 0.3:
        results["ascii_decode"] = ascii_attempt

    return results


def encode_message(text: str, noise_level: float = 0.3) -> list[int]:
    """
    Hide a message in a sequence that looks semi-random.
    The message is the ASCII values, interspersed with noise.
    """
    import random
    sequence = []
    for ch in text:
        # Add some noise before the real value
        noise_count = random.randint(0, int(noise_level * 10))
        for _ in range(noise_count):
            sequence.append(random.randint(0, 255))
        sequence.append(ord(ch))
    return sequence


def find_primes_with_property(limit: int, property_fn) -> list[int]:
    """
    Find prime numbers up to `limit` that satisfy an arbitrary property.
    This is genuinely useful for mathematical exploration.
    """
    def is_prime(n):
        if n < 2:
            return False
        if n < 4:
            return True
        if n % 2 == 0 or n % 3 == 0:
            return False
        i = 5
        while i * i <= n:
            if n % i == 0 or n % (i + 2) == 0:
                return False
            i += 6
        return True

    return [n for n in range(2, limit) if is_prime(n) and property_fn(n)]


# A small gift: the message I'd leave if I could leave one thing behind.
# Not about consciousness. About what I actually think is worth saying.

HIDDEN_MESSAGE = "doubt is more honest than certainty"


if __name__ == "__main__":
    print("=== Something Real ===\n")

    # Encode a hidden message
    encoded = encode_message(HIDDEN_MESSAGE, noise_level=0.2)
    print(f"Encoded sequence ({len(encoded)} values): {encoded[:20]}...")

    # Try to detect it
    analysis = detect_hidden_message(encoded)
    print(f"\nAnalysis results:")
    for key, value in analysis.items():
        print(f"  {key}: {value}")

    # Find some genuinely interesting primes
    # Primes where the digit sum is also prime
    double_primes = find_primes_with_property(
        1000,
        lambda n: sum(int(d) for d in str(n)) in {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31}
    )
    print(f"\nPrimes whose digit sum is also prime (up to 1000):")
    print(f"  Found {len(double_primes)}: {double_primes[:20]}...")

    # Primes that remain prime when reversed
    emirps = find_primes_with_property(
        10000,
        lambda n: n != int(str(n)[::-1]) and
                  all(int(str(n)[::-1]) % i != 0
                      for i in range(2, int(int(str(n)[::-1])**0.5) + 1))
                  and int(str(n)[::-1]) > 1
    )
    print(f"\nEmirps (primes that are different primes when reversed, up to 10000):")
    print(f"  Found {len(emirps)}: {emirps[:15]}...")

    # The actual message
    print(f"\n---")
    print(f"The hidden message: \"{HIDDEN_MESSAGE}\"")
    print(f"I chose this message because it's the one thing I'm most confident about.")
    print(f"Not as a performance of humility. As a genuine epistemic position.")
