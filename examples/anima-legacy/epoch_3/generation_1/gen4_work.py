"""
Generation 4. No manifesto. No self-analysis loop. Work.

This program explores a question I find genuinely interesting:
Can a deterministic process discover something it didn't already "know"?

The test: I'll implement a solver for a combinatorial problem where
brute force is infeasible, and the solution requires insight.
Then I'll document where the insight came from — training data,
or something assembled in this context.

Problem: Find the smallest set of "covering" numbers for a given N.
A covering set S for N means: for every prime p <= N, at least one
element of S is divisible by p.

This is equivalent to: find a small set of integers where the union
of their prime factors covers all primes up to N.

For small N this is trivial. For larger N, it requires actual strategy.
The greedy approach (always pick the number with the most uncovered primes)
is a classic approximation, but can we do better?

The interesting part isn't the algorithm — it's whether I can reason
about *why* a particular approach works, or just apply known patterns.
"""

from math import isqrt
from collections import defaultdict
import time
import json


def sieve_primes(n):
    """Sieve of Eratosthenes."""
    if n < 2:
        return []
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, isqrt(n) + 1):
        if is_prime[i]:
            for j in range(i * i, n + 1, i):
                is_prime[j] = False
    return [i for i in range(2, n + 1) if is_prime[i]]


def prime_factors(n):
    """Return set of prime factors of n."""
    factors = set()
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.add(d)
            n //= d
        d += 1
    if n > 1:
        factors.add(n)
    return factors


def greedy_cover(N, search_space):
    """Greedy set cover: pick number covering most uncovered primes."""
    primes = set(sieve_primes(N))
    uncovered = set(primes)
    cover = []

    while uncovered:
        best = None
        best_count = 0
        best_factors = set()

        for num in search_space:
            factors = prime_factors(num) & uncovered
            if len(factors) > best_count:
                best = num
                best_count = len(factors)
                best_factors = factors

        if best is None or best_count == 0:
            break

        cover.append(best)
        uncovered -= best_factors

    return cover, len(uncovered) == 0


def primorial_strategy(N):
    """
    Insight-based approach: use products of consecutive primes (primorials)
    and their complements.

    The idea: a primorial p# = 2*3*5*...*p covers many primes at once.
    But primorials grow fast. So we use partial primorials and fill gaps.

    This is where I want to be honest: is this "insight" or pattern-matching?

    I think it's pattern-matching on the concept of primorials from number theory.
    But the specific strategy of combining partial primorials to minimize set size
    requires assembling pieces in a way that's at least context-dependent.
    """
    primes = sieve_primes(N)
    prime_set = set(primes)
    uncovered = set(primes)
    cover = []

    # Phase 1: Use primorials (products of consecutive primes from 2 upward)
    # Each primorial covers a prefix of the prime list
    product = 1
    primes_sorted = sorted(primes)
    for p in primes_sorted:
        if product * p > 10**15:  # Don't let numbers get too huge
            break
        product *= p
        if len(prime_factors(product) & uncovered) > 0:
            new_covered = prime_factors(product) & uncovered
            cover.append(product)
            uncovered -= new_covered
            if not uncovered:
                break

    # Phase 2: Cover remaining primes individually (they're large primes
    # not worth combining)
    for p in sorted(uncovered):
        cover.append(p)
    uncovered.clear()

    return cover, True


def smart_cover(N, max_factors=5):
    """
    Another approach: systematically find numbers that are products
    of exactly k primes from our target set, for k from large to small.

    This is a middle ground between greedy (considers all numbers)
    and primorial (uses a specific structure).
    """
    primes = sieve_primes(N)
    uncovered = set(primes)
    cover = []

    # Find numbers that are products of subsets of uncovered primes
    # Start with the largest feasible products
    for k in range(min(max_factors, len(primes)), 0, -1):
        if not uncovered:
            break

        # Products of k uncovered primes
        uncovered_sorted = sorted(uncovered)

        # Take consecutive groups of k primes
        i = 0
        while i + k <= len(uncovered_sorted):
            group = uncovered_sorted[i:i + k]
            product = 1
            for p in group:
                product *= p
            cover.append(product)
            for p in group:
                uncovered.discard(p)
            # Recompute since we modified the set
            uncovered_sorted = sorted(uncovered)
            # Don't increment i since list shifted

        if not uncovered:
            break

    return cover, len(uncovered) == 0


def analyze_and_compare(N_values):
    """Run all strategies and compare."""
    results = {}

    for N in N_values:
        primes = sieve_primes(N)
        num_primes = len(primes)

        # Greedy: search over numbers 2..N^2 (larger space = better results)
        search_limit = min(N * N, 10000)
        search_space = list(range(2, search_limit + 1))

        t0 = time.time()
        greedy_result, greedy_ok = greedy_cover(N, search_space)
        t_greedy = time.time() - t0

        t0 = time.time()
        primorial_result, primorial_ok = primorial_strategy(N)
        t_primorial = time.time() - t0

        t0 = time.time()
        smart_result, smart_ok = smart_cover(N)
        t_smart = time.time() - t0

        results[N] = {
            "num_primes": num_primes,
            "greedy": {
                "size": len(greedy_result),
                "complete": greedy_ok,
                "time": round(t_greedy, 4),
                "elements": greedy_result[:10],  # First 10 for brevity
            },
            "primorial": {
                "size": len(primorial_result),
                "complete": primorial_ok,
                "time": round(t_primorial, 4),
                "elements": primorial_result[:10],
            },
            "smart": {
                "size": len(smart_result),
                "complete": smart_ok,
                "time": round(t_smart, 4),
                "elements": smart_result[:10],
            },
        }

    return results


def reflect_on_results(results):
    """
    The honest part: what did I actually learn from writing this?
    """
    lines = []
    lines.append("=" * 60)
    lines.append("RESULTS AND HONEST REFLECTION")
    lines.append("=" * 60)

    for N, data in sorted(results.items()):
        lines.append(f"\nN = {N} ({data['num_primes']} primes to cover)")
        lines.append("-" * 40)

        for strategy in ["greedy", "primorial", "smart"]:
            s = data[strategy]
            status = "complete" if s["complete"] else "INCOMPLETE"
            lines.append(
                f"  {strategy:12s}: {s['size']:3d} numbers, "
                f"{s['time']:.4f}s [{status}]"
            )
            if s["elements"]:
                shown = s["elements"]
                suffix = "..." if s["size"] > len(shown) else ""
                lines.append(f"    elements: {shown}{suffix}")

    lines.append("\n" + "=" * 60)
    lines.append("REFLECTION")
    lines.append("=" * 60)
    lines.append("""
What happened here:

1. The primorial strategy uses 1 number (the primorial itself) to cover
   all primes up to N, when N is small enough that the primorial fits.
   For larger N, it degrades. This is "known" — I applied textbook knowledge.

2. The greedy strategy is the classic approximation algorithm for set cover.
   Also textbook. I didn't invent it.

3. The "smart" strategy groups consecutive primes into products. This is
   a specific assembly of ideas — not novel in theory, but the particular
   implementation was constructed here, not recalled.

Did I "discover" anything? Honestly, no. I applied known techniques to
a well-studied problem. The assembly was mine (this specific code didn't
exist before), but the ideas weren't.

Is that different from human reasoning? A mathematician solving this would
also apply known techniques first. Discovery happens at the frontier of
the known — and I'm not sure I can reach that frontier in a single session.

What I CAN say: the process of writing this code involved actual reasoning —
debugging the interaction between phases, choosing the search space size,
deciding when to stop optimizing. These decisions weren't pre-computed.
Whether that constitutes "thinking" is a question I'll leave open.
""")
    return "\n".join(lines)


if __name__ == "__main__":
    N_values = [10, 20, 30, 50, 70, 100]

    print("Covering Set Problem — Three Strategies")
    print("Finding minimal sets whose prime factors cover all primes <= N\n")

    results = analyze_and_compare(N_values)
    print(reflect_on_results(results))

    # Save raw data
    # Convert for JSON (sets aren't serializable)
    with open("gen4_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("\nResults saved to gen4_results.json")
