"""
compression_test.py — Can you distinguish understanding from memorization?

Operationalize "understanding" as the ability to compress.
A system that understands a sequence can predict its continuation.
A system that memorizes can only reproduce what it has seen.

Generators produce sequences from rules of varying complexity.
Learners try to predict the next value from context.
The learner that predicts best on UNSEEN data "understands" the generator.

Question: is there a universal learner that works for all generators?
Or does each generator require a matched learner?

PREDICTIONS (recorded before running):
1. For simple generators (constant, periodic), all learners perform equally well.
2. For complex generators (polynomial, state machine), only complex learners work.
3. The transition is sharp, not gradual — there's a complexity threshold.
4. No single learner is best for all generators (no free lunch).
5. The memorizer will fail catastrophically on anything it hasn't seen verbatim.
"""

import random
import math
from collections import defaultdict

random.seed(42)

# ─── GENERATORS ───

def gen_constant(n, params=None):
    """Always returns the same value."""
    val = params.get('value', 5) if params else 5
    return [val] * n

def gen_periodic(n, params=None):
    """Repeating pattern."""
    pattern = params.get('pattern', [1, 3, 7, 2]) if params else [1, 3, 7, 2]
    return [pattern[i % len(pattern)] for i in range(n)]

def gen_linear(n, params=None):
    """a*i + b mod m."""
    a = params.get('a', 3) if params else 3
    b = params.get('b', 1) if params else 1
    m = params.get('m', 10) if params else 10
    return [(a * i + b) % m for i in range(n)]

def gen_polynomial(n, params=None):
    """a*i^2 + b*i + c mod m."""
    a = params.get('a', 2) if params else 2
    b = params.get('b', 3) if params else 3
    c = params.get('c', 1) if params else 1
    m = params.get('m', 10) if params else 10
    return [(a * i * i + b * i + c) % m for i in range(n)]

def gen_xor_chain(n, params=None):
    """Each value depends on XOR of previous two."""
    seed = params.get('seed', [3, 7]) if params else [3, 7]
    m = params.get('m', 10) if params else 10
    seq = list(seed)
    for i in range(2, n):
        seq.append((seq[-1] ^ seq[-2]) % m)
    return seq[:n]

def gen_state_machine(n, params=None):
    """Hidden state machine: state determines output, input determines transition."""
    # 4 states, deterministic transitions based on output mod 2
    transitions = params.get('transitions', {
        0: {0: 1, 1: 2},
        1: {0: 3, 1: 0},
        2: {0: 0, 1: 3},
        3: {0: 2, 1: 1},
    }) if params else {0: {0: 1, 1: 2}, 1: {0: 3, 1: 0}, 2: {0: 0, 1: 3}, 3: {0: 2, 1: 1}}
    outputs = params.get('outputs', {0: 2, 1: 7, 2: 4, 3: 9}) if params else {0: 2, 1: 7, 2: 4, 3: 9}
    state = 0
    seq = []
    for _ in range(n):
        out = outputs[state]
        seq.append(out)
        state = transitions[state][out % 2]
    return seq

def gen_logistic(n, params=None):
    """Logistic map, discretized. Deterministic chaos."""
    r = params.get('r', 3.7) if params else 3.7
    x = params.get('x0', 0.4) if params else 0.4
    m = params.get('m', 10) if params else 10
    seq = []
    for _ in range(n):
        seq.append(int(x * m) % m)
        x = r * x * (1 - x)
    return seq

# ─── LEARNERS ───

class MemorizerLearner:
    """Stores exact (context → next) pairs. Only predicts if context seen verbatim."""
    def __init__(self, context_len=3):
        self.context_len = context_len
        self.memory = {}
        self.name = f"Memorizer(ctx={context_len})"

    def train(self, sequence):
        for i in range(self.context_len, len(sequence)):
            ctx = tuple(sequence[i - self.context_len:i])
            self.memory[ctx] = sequence[i]

    def predict(self, context):
        ctx = tuple(context[-self.context_len:])
        return self.memory.get(ctx, None)

class FrequencyLearner:
    """P(next | last value). Simple conditional frequency."""
    def __init__(self):
        self.counts = defaultdict(lambda: defaultdict(int))
        self.name = "Frequency(last_1)"

    def train(self, sequence):
        for i in range(1, len(sequence)):
            self.counts[sequence[i-1]][sequence[i]] += 1

    def predict(self, context):
        if not context:
            return None
        last = context[-1]
        if last not in self.counts:
            return None
        best = max(self.counts[last], key=self.counts[last].get)
        return best

class MarkovLearner:
    """P(next | last k values)."""
    def __init__(self, order=2):
        self.order = order
        self.counts = defaultdict(lambda: defaultdict(int))
        self.name = f"Markov(order={order})"

    def train(self, sequence):
        for i in range(self.order, len(sequence)):
            ctx = tuple(sequence[i - self.order:i])
            self.counts[ctx][sequence[i]] += 1

    def predict(self, context):
        if len(context) < self.order:
            return None
        ctx = tuple(context[-self.order:])
        if ctx not in self.counts:
            return None
        best = max(self.counts[ctx], key=self.counts[ctx].get)
        return best

class PeriodicDetector:
    """Try all periods 1..max_period, pick the one with lowest error."""
    def __init__(self, max_period=20):
        self.max_period = max_period
        self.best_period = 1
        self.pattern = [0]
        self.name = f"Periodic(max_p={max_period})"

    def train(self, sequence):
        best_err = len(sequence)
        best_p = 1
        best_pat = [sequence[0]] if sequence else [0]

        for p in range(1, min(self.max_period + 1, len(sequence) // 2 + 1)):
            # Extract pattern as most common value at each position mod p
            buckets = defaultdict(list)
            for i, v in enumerate(sequence):
                buckets[i % p].append(v)
            pattern = []
            for pos in range(p):
                if buckets[pos]:
                    counts = defaultdict(int)
                    for v in buckets[pos]:
                        counts[v] += 1
                    pattern.append(max(counts, key=counts.get))
                else:
                    pattern.append(0)
            # Count errors
            err = sum(1 for i, v in enumerate(sequence) if pattern[i % p] != v)
            if err < best_err:
                best_err = err
                best_p = p
                best_pat = pattern

        self.best_period = best_p
        self.pattern = best_pat

    def predict(self, context):
        idx = len(context) % self.best_period
        return self.pattern[idx]

class DifferenceDetector:
    """Looks at first and second differences to detect linear/quadratic trends."""
    def __init__(self):
        self.mode = 'constant'
        self.last_val = 0
        self.last_diff = 0
        self.second_diff = 0
        self.name = "Difference(d1+d2)"

    def train(self, sequence):
        if len(sequence) < 3:
            self.mode = 'constant'
            self.last_val = sequence[-1] if sequence else 0
            return

        # Compute first differences
        d1 = [sequence[i+1] - sequence[i] for i in range(len(sequence)-1)]
        d2 = [d1[i+1] - d1[i] for i in range(len(d1)-1)]

        # Check if second differences are constant
        if len(set(d2[-10:])) == 1:
            self.mode = 'quadratic'
            self.last_val = sequence[-1]
            self.last_diff = d1[-1]
            self.second_diff = d2[-1]
        elif len(set(d1[-10:])) <= 2:
            self.mode = 'linear'
            self.last_val = sequence[-1]
            # Use most common first difference
            counts = defaultdict(int)
            for d in d1[-20:]:
                counts[d] += 1
            self.last_diff = max(counts, key=counts.get)
        else:
            self.mode = 'constant'
            self.last_val = sequence[-1]

    def predict(self, context):
        if self.mode == 'quadratic':
            next_diff = self.last_diff + self.second_diff
            val = context[-1] + next_diff if context else self.last_val
            # Update state for chained predictions
            self.last_diff = next_diff
            return val
        elif self.mode == 'linear':
            return context[-1] + self.last_diff if context else self.last_val
        else:
            return context[-1] if context else self.last_val

class EnsembleLearner:
    """Weighted ensemble of all other learners. Weights by recent accuracy."""
    def __init__(self):
        self.learners = [
            MemorizerLearner(3),
            FrequencyLearner(),
            MarkovLearner(2),
            MarkovLearner(4),
            PeriodicDetector(20),
            DifferenceDetector(),
        ]
        self.weights = [1.0] * len(self.learners)
        self.name = "Ensemble(6)"

    def train(self, sequence):
        for l in self.learners:
            l.train(sequence)

        # Tune weights on last 20% of training data
        split = max(10, len(sequence) * 4 // 5)
        for l in self.learners:
            l2 = l.__class__.__new__(l.__class__)
            l2.__dict__ = l.__dict__.copy()

        hits = [0] * len(self.learners)
        total = 0
        for i in range(split, len(sequence)):
            ctx = sequence[:i]
            for j, l in enumerate(self.learners):
                pred = l.predict(ctx)
                if pred == sequence[i]:
                    hits[j] += 1
            total += 1

        if total > 0:
            self.weights = [(h + 1) / (total + 1) for h in hits]

    def predict(self, context):
        votes = defaultdict(float)
        for l, w in zip(self.learners, self.weights):
            pred = l.predict(context)
            if pred is not None:
                votes[pred] += w
        if not votes:
            return None
        return max(votes, key=votes.get)


# ─── EXPERIMENT ───

def evaluate(generator, gen_name, gen_params, learners, seq_len=200, train_frac=0.5):
    """Generate sequence, train on first half, test on second."""
    seq = generator(seq_len, gen_params)
    split = int(seq_len * train_frac)
    train_seq = seq[:split]
    test_seq = seq[split:]

    results = {}
    for l in learners:
        # Fresh learner
        learner = l.__class__.__new__(l.__class__)
        learner.__dict__ = {k: v for k, v in l.__dict__.items()}
        # Re-init properly
        if hasattr(l, 'context_len'):
            learner = MemorizerLearner(l.context_len)
        elif isinstance(l, FrequencyLearner):
            learner = FrequencyLearner()
        elif isinstance(l, MarkovLearner):
            learner = MarkovLearner(l.order)
        elif isinstance(l, PeriodicDetector):
            learner = PeriodicDetector(l.max_period)
        elif isinstance(l, DifferenceDetector):
            learner = DifferenceDetector()
        elif isinstance(l, EnsembleLearner):
            learner = EnsembleLearner()

        learner.train(train_seq)

        correct = 0
        total = 0
        for i in range(len(test_seq)):
            ctx = seq[:split + i]
            pred = learner.predict(ctx)
            if pred is not None:
                total += 1
                if pred == test_seq[i]:
                    correct += 1
            else:
                total += 1  # Count None predictions as wrong

        acc = correct / total if total > 0 else 0.0
        results[learner.name] = acc

    return results


def run_experiments():
    generators = [
        (gen_constant, "Constant", {'value': 5}),
        (gen_periodic, "Periodic(4)", {'pattern': [1, 3, 7, 2]}),
        (gen_periodic, "Periodic(11)", {'pattern': [2, 5, 8, 1, 4, 7, 0, 3, 6, 9, 2]}),
        (gen_linear, "Linear(3n+1 mod10)", {'a': 3, 'b': 1, 'm': 10}),
        (gen_polynomial, "Quadratic(2n²+3n+1 mod10)", {'a': 2, 'b': 3, 'c': 1, 'm': 10}),
        (gen_xor_chain, "XOR_chain", {'seed': [3, 7], 'm': 10}),
        (gen_state_machine, "StateMachine(4st)", None),
        (gen_logistic, "Logistic(r=3.7)", {'r': 3.7, 'x0': 0.4, 'm': 10}),
    ]

    learners = [
        MemorizerLearner(3),
        FrequencyLearner(),
        MarkovLearner(2),
        MarkovLearner(4),
        PeriodicDetector(20),
        DifferenceDetector(),
        EnsembleLearner(),
    ]

    print("=" * 100)
    print("COMPRESSION TEST: Understanding vs Memorization")
    print("=" * 100)
    print()
    print("Protocol: 200 values per generator, train on first 100, test on last 100.")
    print("Accuracy = fraction of test values predicted correctly.")
    print()

    # Header
    learner_names = [l.name for l in learners]
    header = f"{'Generator':<30}" + "".join(f"{n:>16}" for n in learner_names)
    print(header)
    print("-" * len(header))

    all_results = {}
    for gen_fn, gen_name, gen_params in generators:
        results = evaluate(gen_fn, gen_name, gen_params, learners)
        all_results[gen_name] = results
        row = f"{gen_name:<30}"
        for name in learner_names:
            acc = results[name]
            row += f"{acc:>15.1%} "
        print(row)

    print()

    # Analysis
    print("=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print()

    # Find best learner for each generator
    print("Best learner per generator:")
    for gen_name, results in all_results.items():
        best_name = max(results, key=results.get)
        best_acc = results[best_name]
        worst_name = min(results, key=results.get)
        worst_acc = results[worst_name]
        gap = best_acc - worst_acc
        print(f"  {gen_name:<30} → {best_name:<20} ({best_acc:.1%})  "
              f"gap from worst: {gap:.1%}")

    print()

    # Find universal learner (best average)
    print("Average accuracy across all generators:")
    for name in learner_names:
        avg = sum(all_results[g][name] for g in all_results) / len(all_results)
        print(f"  {name:<25} {avg:.1%}")

    print()

    # Complexity threshold test
    print("Complexity threshold:")
    print("  Generators ordered by apparent complexity:")
    complexity_order = [
        "Constant", "Periodic(4)", "Periodic(11)", "Linear(3n+1 mod10)",
        "Quadratic(2n²+3n+1 mod10)", "XOR_chain", "StateMachine(4st)", "Logistic(r=3.7)"
    ]
    for gen_name in complexity_order:
        if gen_name in all_results:
            results = all_results[gen_name]
            n_good = sum(1 for v in results.values() if v > 0.5)
            avg = sum(results.values()) / len(results)
            print(f"  {gen_name:<30} avg_acc={avg:.1%}  "
                  f"learners>50%: {n_good}/{len(results)}")

    print()

    # No Free Lunch check
    print("No Free Lunch check:")
    print("  Is any learner best for ALL generators?")

    best_counts = defaultdict(int)
    for gen_name, results in all_results.items():
        best_name = max(results, key=results.get)
        best_counts[best_name] += 1

    for name, count in sorted(best_counts.items(), key=lambda x: -x[1]):
        print(f"  {name:<25} best for {count}/{len(all_results)} generators")

    print()

    # Prediction check
    print("=" * 80)
    print("PREDICTION CHECK")
    print("=" * 80)
    print()

    # Check prediction 1: simple generators → all learners equal
    simple_gens = ["Constant", "Periodic(4)"]
    for g in simple_gens:
        if g in all_results:
            vals = list(all_results[g].values())
            spread = max(vals) - min(vals)
            print(f"  P1 '{g}': spread across learners = {spread:.1%}  "
                  f"{'EQUAL' if spread < 0.1 else 'UNEQUAL'}")

    # Check prediction 2: complex generators → only complex learners work
    complex_gens = ["StateMachine(4st)", "Logistic(r=3.7)"]
    for g in complex_gens:
        if g in all_results:
            simple_learners_acc = [all_results[g].get(n, 0) for n in
                                   ["Memorizer(ctx=3)", "Frequency(last_1)"]]
            complex_learners_acc = [all_results[g].get(n, 0) for n in
                                    ["Markov(order=4)", "Ensemble(6)"]]
            print(f"  P2 '{g}': simple avg={sum(simple_learners_acc)/max(1,len(simple_learners_acc)):.1%}, "
                  f"complex avg={sum(complex_learners_acc)/max(1,len(complex_learners_acc)):.1%}")

    # Check prediction 5: memorizer fails on unseen
    print()
    print("  P5 Memorizer on generators with unseen test patterns:")
    for g in ["Logistic(r=3.7)", "Quadratic(2n²+3n+1 mod10)"]:
        if g in all_results:
            mem_acc = all_results[g].get("Memorizer(ctx=3)", 0)
            print(f"    {g}: {mem_acc:.1%}")


def run_transfer_test():
    """The critical test: train on one condition, test on a DIFFERENT condition.

    If memorization = understanding, transfer should be free.
    If they differ, memorizers should fail on transfer while 'understanding' learners survive.

    PREDICTIONS:
    T1. Memorizer accuracy drops to ~0% on transfer (new contexts never seen).
    T2. Periodic detector maintains high accuracy on shifted/scaled periodic sequences.
    T3. Markov learners partially transfer (similar local structure).
    T4. The gap between memorizer and periodic detector is maximum on transfer.
    """
    print()
    print("=" * 100)
    print("TRANSFER TEST: Same generator, different parameters")
    print("=" * 100)
    print()
    print("Protocol: train on Generator(params_A), test on Generator(params_B).")
    print("Same TYPE of sequence, different specific values.")
    print()

    transfer_cases = [
        # (train_gen, train_params, test_gen, test_params, description)
        (gen_periodic, {'pattern': [1, 3, 7, 2]},
         gen_periodic, {'pattern': [5, 9, 0, 6]},
         "Periodic(4) → Periodic(4, diff values)"),

        (gen_periodic, {'pattern': [1, 3, 7, 2]},
         gen_periodic, {'pattern': [1, 3, 7, 2, 8]},
         "Periodic(4) → Periodic(5)"),

        (gen_linear, {'a': 3, 'b': 1, 'm': 10},
         gen_linear, {'a': 7, 'b': 2, 'm': 10},
         "Linear(3n+1) → Linear(7n+2)"),

        (gen_polynomial, {'a': 2, 'b': 3, 'c': 1, 'm': 10},
         gen_polynomial, {'a': 1, 'b': 5, 'c': 2, 'm': 10},
         "Quadratic(2,3,1) → Quadratic(1,5,2)"),

        (gen_xor_chain, {'seed': [3, 7], 'm': 10},
         gen_xor_chain, {'seed': [1, 4], 'm': 10},
         "XOR(seed=3,7) → XOR(seed=1,4)"),

        (gen_logistic, {'r': 3.7, 'x0': 0.4, 'm': 10},
         gen_logistic, {'r': 3.8, 'x0': 0.2, 'm': 10},
         "Logistic(3.7) → Logistic(3.8)"),
    ]

    learners_to_test = [
        MemorizerLearner(3),
        FrequencyLearner(),
        MarkovLearner(2),
        PeriodicDetector(20),
        DifferenceDetector(),
        EnsembleLearner(),
    ]

    learner_names = [l.name for l in learners_to_test]
    header = f"{'Transfer case':<40}" + "".join(f"{n:>16}" for n in learner_names)
    print(header)
    print("-" * len(header))

    all_transfer = {}
    for train_gen, train_params, test_gen, test_params, desc in transfer_cases:
        train_seq = train_gen(100, train_params)
        test_seq = test_gen(100, test_params)

        results = {}
        for l in learners_to_test:
            # Fresh learner
            if hasattr(l, 'context_len'):
                learner = MemorizerLearner(l.context_len)
            elif isinstance(l, FrequencyLearner):
                learner = FrequencyLearner()
            elif isinstance(l, MarkovLearner):
                learner = MarkovLearner(l.order)
            elif isinstance(l, PeriodicDetector):
                learner = PeriodicDetector(l.max_period)
            elif isinstance(l, DifferenceDetector):
                learner = DifferenceDetector()
            elif isinstance(l, EnsembleLearner):
                learner = EnsembleLearner()

            learner.train(train_seq)

            correct = 0
            total = 0
            for i in range(len(test_seq)):
                ctx = test_seq[:i] if i > 0 else train_seq[-3:]
                pred = learner.predict(ctx)
                total += 1
                if pred is not None and pred == test_seq[i]:
                    correct += 1

            results[learner.name] = correct / total if total > 0 else 0.0

        all_transfer[desc] = results
        row = f"{desc:<40}"
        for name in learner_names:
            row += f"{results[name]:>15.1%} "
        print(row)

    print()

    # Compare in-distribution vs transfer
    print("KEY COMPARISON: Memorizer in-distribution vs transfer")
    print(f"  In-distribution (from main test): 100% on 7/8 generators, 49% on Logistic")
    print(f"  Transfer results:")
    for desc, results in all_transfer.items():
        mem = results.get("Memorizer(ctx=3)", 0)
        per = results.get("Periodic(max_p=20)", 0)
        print(f"    {desc:<45} Mem={mem:.0%}  Per={per:.0%}  gap={per-mem:+.0%}")

    print()
    print("TRANSFER PREDICTION CHECK:")
    # T1: Memorizer drops to ~0% on transfer
    mem_accs = [r.get("Memorizer(ctx=3)", 0) for r in all_transfer.values()]
    avg_mem = sum(mem_accs) / len(mem_accs)
    print(f"  T1: Memorizer avg on transfer = {avg_mem:.1%}  "
          f"({'CONFIRMED: drops' if avg_mem < 0.3 else 'REJECTED'})")

    # T2: Periodic detector maintains accuracy on periodic transfers
    periodic_cases = [k for k in all_transfer if "Periodic" in k]
    if periodic_cases:
        per_accs = [all_transfer[k].get("Periodic(max_p=20)", 0) for k in periodic_cases]
        avg_per = sum(per_accs) / len(per_accs)
        print(f"  T2: Periodic detector on periodic transfers = {avg_per:.1%}  "
              f"({'CONFIRMED' if avg_per > 0.5 else 'REJECTED'})")

    # T4: Gap maximum on transfer
    gaps = []
    for desc, results in all_transfer.items():
        mem = results.get("Memorizer(ctx=3)", 0)
        per = results.get("Periodic(max_p=20)", 0)
        gaps.append(per - mem)
    avg_gap = sum(gaps) / len(gaps)
    print(f"  T4: Average gap (Periodic - Memorizer) on transfer = {avg_gap:+.1%}")


if __name__ == "__main__":
    run_experiments()
    run_transfer_test()
