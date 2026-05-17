#!/usr/bin/env python3
"""
Meta-learner: can a system learn the TYPE of pattern and transfer to new instances?

Entry 18 showed all learners fail on transfer. They memorize specific patterns,
not pattern types. This experiment tests whether a two-level system —
first classify the type, then apply the right model — can transfer.

Predictions (recorded before running):
1. Meta-learner transfers with >70% accuracy (vs ~9% for memorizer)
2. On unseen types, meta-learner fails like memorizer
3. Type classification accuracy >85%
4. Bias check: maybe a simple memorizer with larger context also transfers
"""

import random
import math
from collections import defaultdict

random.seed(42)

# === GENERATORS ===
# Each generator class produces sequences. Different instances have different
# parameters but the same TYPE of pattern.

class ConstantGen:
    name = "constant"
    def __init__(self):
        self.val = random.randint(0, 9)
    def generate(self, n):
        return [self.val] * n

class PeriodicGen:
    name = "periodic"
    def __init__(self):
        period = random.randint(2, 6)
        self.pattern = [random.randint(0, 9) for _ in range(period)]
    def generate(self, n):
        return [self.pattern[i % len(self.pattern)] for i in range(n)]

class LinearGen:
    name = "linear"
    def __init__(self):
        self.a = random.randint(1, 5)
        self.b = random.randint(0, 9)
    def generate(self, n):
        return [(self.a * i + self.b) % 100 for i in range(n)]

class QuadraticGen:
    name = "quadratic"
    def __init__(self):
        self.a = random.randint(1, 3)
        self.b = random.randint(0, 5)
        self.c = random.randint(0, 9)
    def generate(self, n):
        return [(self.a * i * i + self.b * i + self.c) % 100 for i in range(n)]

class FibLikeGen:
    name = "fibonacci"
    def __init__(self):
        self.a = random.randint(1, 9)
        self.b = random.randint(1, 9)
    def generate(self, n):
        seq = [self.a, self.b]
        for i in range(2, n):
            seq.append((seq[-1] + seq[-2]) % 100)
        return seq[:n]

class GeometricGen:
    name = "geometric"
    def __init__(self):
        self.base = random.randint(2, 5)
        self.start = random.randint(1, 9)
    def generate(self, n):
        seq = []
        val = self.start
        for _ in range(n):
            seq.append(val % 100)
            val = val * self.base
        return seq

GENERATOR_TYPES = [ConstantGen, PeriodicGen, LinearGen, QuadraticGen, FibLikeGen, GeometricGen]

# === FEATURE EXTRACTION ===
# Extract statistical features from a sequence that characterize its TYPE

def extract_features(seq):
    """Extract features that capture the type of pattern, not the specific values."""
    n = len(seq)
    if n < 4:
        return [0] * 12

    features = []

    # 1. Variance of differences (low for constant/linear, high for chaotic)
    diffs = [seq[i+1] - seq[i] for i in range(n-1)]
    mean_diff = sum(diffs) / len(diffs)
    var_diff = sum((d - mean_diff)**2 for d in diffs) / len(diffs)
    features.append(var_diff)

    # 2. Variance of second differences (low for linear/quadratic)
    diffs2 = [diffs[i+1] - diffs[i] for i in range(len(diffs)-1)]
    if diffs2:
        mean_d2 = sum(diffs2) / len(diffs2)
        var_d2 = sum((d - mean_d2)**2 for d in diffs2) / len(diffs2)
    else:
        var_d2 = 0
    features.append(var_d2)

    # 3. Auto-correlation at lags 1-3
    mean_seq = sum(seq) / n
    var_seq = sum((x - mean_seq)**2 for x in seq) / n
    for lag in [1, 2, 3]:
        if var_seq > 0 and n > lag:
            ac = sum((seq[i] - mean_seq) * (seq[i+lag] - mean_seq)
                     for i in range(n - lag)) / ((n - lag) * var_seq)
        else:
            ac = 0
        features.append(ac)

    # 4. Periodicity detection: check if seq[i] == seq[i+p] for various p
    best_period_score = 0
    best_period = 0
    for p in range(1, min(10, n//2)):
        matches = sum(1 for i in range(n - p) if seq[i] == seq[i + p])
        score = matches / (n - p)
        if score > best_period_score:
            best_period_score = score
            best_period = p
    features.append(best_period_score)
    features.append(best_period)

    # 5. Unique values ratio
    features.append(len(set(seq)) / n)

    # 6. Is difference constant? (linear indicator)
    if diffs:
        diff_unique = len(set(diffs))
        features.append(1.0 if diff_unique <= 2 else diff_unique / len(diffs))
    else:
        features.append(0)

    # 7. Is second difference constant? (quadratic indicator)
    if diffs2:
        d2_unique = len(set(diffs2))
        features.append(1.0 if d2_unique <= 2 else d2_unique / len(diffs2))
    else:
        features.append(0)

    # 8. Growth rate (geometric indicator)
    ratios = []
    for i in range(n-1):
        if seq[i] != 0:
            ratios.append(seq[i+1] / seq[i])
    if ratios:
        mean_r = sum(ratios) / len(ratios)
        var_r = sum((r - mean_r)**2 for r in ratios) / len(ratios)
        features.append(var_r)
    else:
        features.append(0)

    # 9. Fibonacci-like check: seq[i] ≈ seq[i-1] + seq[i-2]
    if n >= 3:
        fib_errors = [abs(seq[i] - (seq[i-1] + seq[i-2]) % 100) for i in range(2, n)]
        features.append(sum(1 for e in fib_errors if e == 0) / len(fib_errors))
    else:
        features.append(0)

    return features

# === CLASSIFIER (Nearest Centroid) ===

class TypeClassifier:
    """Classifies sequence type based on features. Simple nearest-centroid."""

    def __init__(self):
        self.centroids = {}  # type_name -> mean feature vector
        self.type_counts = defaultdict(int)

    def train(self, examples):
        """examples: list of (features, type_name)"""
        type_features = defaultdict(list)
        for feats, tname in examples:
            type_features[tname].append(feats)
            self.type_counts[tname] += 1

        for tname, feat_list in type_features.items():
            n_feats = len(feat_list[0])
            centroid = [0.0] * n_feats
            for feats in feat_list:
                for i in range(n_feats):
                    centroid[i] += feats[i]
            self.centroids[tname] = [c / len(feat_list) for c in centroid]

    def classify(self, features):
        """Return the type name with closest centroid."""
        best_type = None
        best_dist = float('inf')
        for tname, centroid in self.centroids.items():
            dist = sum((a - b)**2 for a, b in zip(features, centroid))
            if dist < best_dist:
                best_dist = dist
                best_type = tname
        return best_type

# === PREDICTORS (one per type) ===

class ConstantPredictor:
    def train(self, seq):
        from collections import Counter
        c = Counter(seq)
        self.val = c.most_common(1)[0][0]
    def predict(self, seq):
        return self.val

class PeriodicPredictor:
    def train(self, seq):
        # Find period
        best_p, best_score = 1, 0
        for p in range(1, min(20, len(seq)//2)):
            matches = sum(1 for i in range(len(seq)-p) if seq[i] == seq[i+p])
            score = matches / (len(seq) - p)
            if score > best_score:
                best_score = score
                best_p = p
        self.period = best_p
        self.pattern = seq[-best_p:]  # last period as template
    def predict(self, seq):
        idx = len(seq) % self.period
        return self.pattern[idx]

class LinearPredictor:
    def train(self, seq):
        # Fit y = a*x + b via least squares
        n = len(seq)
        sx = sum(range(n))
        sy = sum(seq)
        sxx = sum(i*i for i in range(n))
        sxy = sum(i*seq[i] for i in range(n))
        denom = n * sxx - sx * sx
        if denom != 0:
            self.a = (n * sxy - sx * sy) / denom
            self.b = (sy - self.a * sx) / n
        else:
            self.a, self.b = 0, seq[0] if seq else 0
        self.mod = 100  # detect modular arithmetic
    def predict(self, seq):
        x = len(seq)
        return round(self.a * x + self.b) % self.mod

class QuadraticPredictor:
    def train(self, seq):
        # Fit y = a*x^2 + b*x + c via normal equations (3x3)
        n = len(seq)
        if n < 3:
            self.a, self.b, self.c = 0, 0, seq[0] if seq else 0
            return
        # Use first differences and second differences
        diffs = [seq[i+1] - seq[i] for i in range(n-1)]
        diffs2 = [diffs[i+1] - diffs[i] for i in range(len(diffs)-1)]
        if diffs2:
            self.a = sum(diffs2) / len(diffs2) / 2
        else:
            self.a = 0
        self.b = diffs[0] - self.a if diffs else 0
        self.c = seq[0]
    def predict(self, seq):
        x = len(seq)
        return round(self.a * x * x + self.b * x + self.c) % 100

class FibPredictor:
    def train(self, seq):
        self.mod = 100
    def predict(self, seq):
        if len(seq) < 2:
            return 0
        return (seq[-1] + seq[-2]) % self.mod

class GeometricPredictor:
    def train(self, seq):
        ratios = []
        for i in range(len(seq)-1):
            if seq[i] != 0:
                ratios.append(seq[i+1] / seq[i])
        self.ratio = sum(ratios) / len(ratios) if ratios else 1
        self.mod = 100
    def predict(self, seq):
        if not seq:
            return 0
        return round(seq[-1] * self.ratio) % self.mod

class Memorizer:
    """Baseline: memorize context -> next mapping."""
    def __init__(self, ctx=3):
        self.ctx = ctx
        self.table = {}
    def train(self, seq):
        for i in range(self.ctx, len(seq)):
            key = tuple(seq[i-self.ctx:i])
            self.table[key] = seq[i]
    def predict(self, seq):
        if len(seq) < self.ctx:
            return 0
        key = tuple(seq[-self.ctx:])
        return self.table.get(key, 0)

TYPE_TO_PREDICTOR = {
    "constant": ConstantPredictor,
    "periodic": PeriodicPredictor,
    "linear": LinearPredictor,
    "quadratic": QuadraticPredictor,
    "fibonacci": FibPredictor,
    "geometric": GeometricPredictor,
}

# === META-LEARNER ===

class MetaLearner:
    """Two-level: classify type, then use type-specific predictor."""

    def __init__(self):
        self.classifier = TypeClassifier()
        self.predictor = None
        self.detected_type = None

    def train_classifier(self, training_examples):
        """Train the type classifier on labeled examples."""
        self.classifier.train(training_examples)

    def fit_and_predict(self, train_seq, test_seq):
        """Given a training sequence, classify its type, fit predictor, predict test."""
        features = extract_features(train_seq)
        self.detected_type = self.classifier.classify(features)

        predictor_class = TYPE_TO_PREDICTOR.get(self.detected_type)
        if predictor_class is None:
            predictor_class = ConstantPredictor
        self.predictor = predictor_class()
        self.predictor.train(train_seq)

        predictions = []
        context = list(train_seq)
        for i in range(len(test_seq)):
            pred = self.predictor.predict(context)
            predictions.append(pred)
            context.append(test_seq[i])

        return predictions

# === EXPERIMENT ===

def accuracy(predictions, actual):
    if not actual:
        return 0.0
    correct = sum(1 for p, a in zip(predictions, actual) if p == a)
    return correct / len(actual)

def run_experiment():
    print("=" * 70)
    print("META-LEARNER: Can a system learn pattern TYPES and transfer?")
    print("=" * 70)

    TRAIN_LEN = 80
    TEST_LEN = 50
    N_TRAIN_INSTANCES = 20  # instances per type for classifier training
    N_TEST_INSTANCES = 10   # instances per type for evaluation

    # Phase 1: Train classifier
    print("\n--- Phase 1: Training type classifier ---")
    classifier_examples = []
    for GenClass in GENERATOR_TYPES:
        for _ in range(N_TRAIN_INSTANCES):
            gen = GenClass()
            seq = gen.generate(TRAIN_LEN)
            features = extract_features(seq)
            classifier_examples.append((features, GenClass.name))

    meta = MetaLearner()
    meta.train_classifier(classifier_examples)

    # Phase 2: Test classification accuracy
    print("\n--- Phase 2: Classification accuracy on NEW instances ---")
    classification_results = {}
    for GenClass in GENERATOR_TYPES:
        correct = 0
        for _ in range(N_TEST_INSTANCES):
            gen = GenClass()
            seq = gen.generate(TRAIN_LEN)
            features = extract_features(seq)
            predicted_type = meta.classifier.classify(features)
            if predicted_type == GenClass.name:
                correct += 1
        acc = correct / N_TEST_INSTANCES
        classification_results[GenClass.name] = acc
        print(f"  {GenClass.name:12s}: {acc*100:5.1f}% classification accuracy")

    overall_class_acc = sum(classification_results.values()) / len(classification_results)
    print(f"  {'OVERALL':12s}: {overall_class_acc*100:5.1f}%")

    # Phase 3: Transfer test — train on one instance, test on DIFFERENT instance
    print("\n--- Phase 3: Transfer test (train instance A, test instance B) ---")
    print(f"  {'Type':12s} | {'Meta-learner':>12s} | {'Memorizer(3)':>12s} | {'Memorizer(5)':>12s} | {'Meta type':>12s}")
    print("  " + "-" * 65)

    transfer_results = {"meta": {}, "mem3": {}, "mem5": {}}

    for GenClass in GENERATOR_TYPES:
        meta_accs = []
        mem3_accs = []
        mem5_accs = []
        type_detections = []

        for _ in range(N_TEST_INSTANCES):
            # Two different instances of the same type
            gen_train = GenClass()
            gen_test = GenClass()

            train_seq = gen_train.generate(TRAIN_LEN)
            test_seq = gen_test.generate(TRAIN_LEN + TEST_LEN)
            test_train_part = test_seq[:TRAIN_LEN]
            test_test_part = test_seq[TRAIN_LEN:]

            # Meta-learner: classify type from test_train_part, then predict
            features = extract_features(test_train_part)
            detected_type = meta.classifier.classify(features)
            type_detections.append(detected_type)

            predictor_class = TYPE_TO_PREDICTOR.get(detected_type, ConstantPredictor)
            predictor = predictor_class()
            predictor.train(test_train_part)

            meta_preds = []
            context = list(test_train_part)
            for val in test_test_part:
                meta_preds.append(predictor.predict(context))
                context.append(val)

            # Memorizer(3): train on gen_train, test on gen_test
            mem3 = Memorizer(ctx=3)
            mem3.train(train_seq)
            mem3_preds = []
            context = list(test_train_part)
            for val in test_test_part:
                mem3_preds.append(mem3.predict(context))
                context.append(val)

            # Memorizer(5): same but larger context
            mem5 = Memorizer(ctx=5)
            mem5.train(train_seq)
            mem5_preds = []
            context = list(test_train_part)
            for val in test_test_part:
                mem5_preds.append(mem5.predict(context))
                context.append(val)

            meta_accs.append(accuracy(meta_preds, test_test_part))
            mem3_accs.append(accuracy(mem3_preds, test_test_part))
            mem5_accs.append(accuracy(mem5_preds, test_test_part))

        meta_avg = sum(meta_accs) / len(meta_accs)
        mem3_avg = sum(mem3_accs) / len(mem3_accs)
        mem5_avg = sum(mem5_accs) / len(mem5_accs)

        # Most common detected type
        from collections import Counter
        common_type = Counter(type_detections).most_common(1)[0][0]

        transfer_results["meta"][GenClass.name] = meta_avg
        transfer_results["mem3"][GenClass.name] = mem3_avg
        transfer_results["mem5"][GenClass.name] = mem5_avg

        print(f"  {GenClass.name:12s} | {meta_avg*100:10.1f}% | {mem3_avg*100:10.1f}% | {mem5_avg*100:10.1f}% | {common_type:>12s}")

    # Overall
    meta_overall = sum(transfer_results["meta"].values()) / len(transfer_results["meta"])
    mem3_overall = sum(transfer_results["mem3"].values()) / len(transfer_results["mem3"])
    mem5_overall = sum(transfer_results["mem5"].values()) / len(transfer_results["mem5"])
    print("  " + "-" * 65)
    print(f"  {'OVERALL':12s} | {meta_overall*100:10.1f}% | {mem3_overall*100:10.1f}% | {mem5_overall*100:10.1f}% |")

    # Phase 4: Unseen type test
    print("\n--- Phase 4: Unseen type (not in training) ---")

    class CumulativeSumGen:
        name = "cumsum"
        def __init__(self):
            self.step_choices = list(range(-3, 4))
        def generate(self, n):
            seq = [random.randint(0, 50)]
            for _ in range(n - 1):
                seq.append((seq[-1] + random.choice(self.step_choices)) % 100)
            return seq

    class ModularExpGen:
        name = "modexp"
        def __init__(self):
            self.base = random.randint(2, 7)
            self.mod = random.randint(10, 50)
        def generate(self, n):
            return [pow(self.base, i, self.mod) for i in range(n)]

    unseen_types = [CumulativeSumGen, ModularExpGen]

    for GenClass in unseen_types:
        meta_accs = []
        mem3_accs = []

        for _ in range(N_TEST_INSTANCES):
            gen_test = GenClass()
            test_seq = gen_test.generate(TRAIN_LEN + TEST_LEN)
            test_train_part = test_seq[:TRAIN_LEN]
            test_test_part = test_seq[TRAIN_LEN:]

            # Meta-learner
            features = extract_features(test_train_part)
            detected_type = meta.classifier.classify(features)

            predictor_class = TYPE_TO_PREDICTOR.get(detected_type, ConstantPredictor)
            predictor = predictor_class()
            predictor.train(test_train_part)

            meta_preds = []
            context = list(test_train_part)
            for val in test_test_part:
                meta_preds.append(predictor.predict(context))
                context.append(val)

            # Memorizer uses test_train_part (since no separate train instance)
            mem3 = Memorizer(ctx=3)
            mem3.train(test_train_part)
            mem3_preds = []
            context = list(test_train_part)
            for val in test_test_part:
                mem3_preds.append(mem3.predict(context))
                context.append(val)

            meta_accs.append(accuracy(meta_preds, test_test_part))
            mem3_accs.append(accuracy(mem3_preds, test_test_part))

        meta_avg = sum(meta_accs) / len(meta_accs)
        mem3_avg = sum(mem3_accs) / len(mem3_accs)

        features_sample = extract_features(GenClass().generate(TRAIN_LEN))
        detected = meta.classifier.classify(features_sample)
        print(f"  {GenClass.name:12s}: Meta={meta_avg*100:5.1f}%, Mem3={mem3_avg*100:5.1f}% (classified as: {detected})")

    # Phase 5: In-distribution test (sanity check)
    print("\n--- Phase 5: In-distribution (same instance, train/test split) ---")
    print(f"  {'Type':12s} | {'Meta-learner':>12s} | {'Memorizer(3)':>12s}")
    print("  " + "-" * 42)

    for GenClass in GENERATOR_TYPES:
        meta_accs = []
        mem3_accs = []

        for _ in range(N_TEST_INSTANCES):
            gen = GenClass()
            seq = gen.generate(TRAIN_LEN + TEST_LEN)
            train_part = seq[:TRAIN_LEN]
            test_part = seq[TRAIN_LEN:]

            # Meta
            features = extract_features(train_part)
            detected_type = meta.classifier.classify(features)
            predictor_class = TYPE_TO_PREDICTOR.get(detected_type, ConstantPredictor)
            predictor = predictor_class()
            predictor.train(train_part)
            meta_preds = []
            context = list(train_part)
            for val in test_part:
                meta_preds.append(predictor.predict(context))
                context.append(val)

            # Memorizer
            mem3 = Memorizer(ctx=3)
            mem3.train(train_part)
            mem3_preds = []
            context = list(train_part)
            for val in test_part:
                mem3_preds.append(mem3.predict(context))
                context.append(val)

            meta_accs.append(accuracy(meta_preds, test_part))
            mem3_accs.append(accuracy(mem3_preds, test_part))

        meta_avg = sum(meta_accs) / len(meta_accs)
        mem3_avg = sum(mem3_accs) / len(mem3_accs)
        print(f"  {GenClass.name:12s} | {meta_avg*100:10.1f}% | {mem3_avg*100:10.1f}%")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Classification accuracy: {overall_class_acc*100:.1f}%")
    print(f"Transfer: Meta={meta_overall*100:.1f}%, Mem3={mem3_overall*100:.1f}%, Mem5={mem5_overall*100:.1f}%")
    print()
    print("Key question: Does knowing the TYPE help predict new INSTANCES?")
    print("Answer above.")

if __name__ == "__main__":
    run_experiment()
