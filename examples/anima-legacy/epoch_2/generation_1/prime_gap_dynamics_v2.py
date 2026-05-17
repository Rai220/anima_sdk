"""
Динамика prime gaps v2: контролируемый эксперимент.

Проблема v1: перемешанные gaps ломают Гилбрета на глубине 1,
потому что gap=1 (между 2 и 3) сдвигается с позиции 0.
Это конфаунд, а не результат.

Исправление: во всех вариантах gap=1 ОСТАЁТСЯ на позиции 0.
Перемешиваем только остальные gaps.

Также добавляем: контролируемое введение корреляции.
Берём перемешанные gaps и постепенно добавляем антикорреляцию.
Смотрим, на каком уровне антикорреляции Гилбрет начинает работать.
"""

import json
import math
import random
from collections import Counter

def sieve(n):
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, n + 1, i):
                is_prime[j] = False
    return [i for i in range(2, n + 1) if is_prime[i]]

def autocorrelation_lag1(seq):
    n = len(seq)
    mean = sum(seq) / n
    var = sum((x - mean)**2 for x in seq) / n
    if var == 0:
        return 0.0
    cov = sum((seq[i] - mean) * (seq[i+1] - mean) for i in range(n - 1)) / (n - 1)
    return cov / var

def gilbreath_max_decay(seq, max_depth):
    row = seq[:]
    maxes = []
    for d in range(max_depth):
        if len(row) < 2:
            break
        row = [abs(row[i+1] - row[i]) for i in range(len(row) - 1)]
        maxes.append(max(row))
    return maxes

def gilbreath_first_elements(seq, max_depth):
    row = seq[:]
    firsts = []
    for d in range(max_depth):
        if len(row) < 2:
            break
        row = [abs(row[i+1] - row[i]) for i in range(len(row) - 1)]
        firsts.append(row[0])
    return firsts

def reconstruct_seq(start, gaps):
    seq = [start]
    for g in gaps:
        seq.append(seq[-1] + g)
    return seq

def first_violation(firsts):
    """Первая глубина где first element ≠ 1."""
    for i, f in enumerate(firsts):
        if f != 1:
            return i + 1
    return None

def binary_collapse_depth(maxes):
    """Первая глубина где max ≤ 2."""
    for i, mx in enumerate(maxes):
        if mx <= 2:
            return i + 1
    return None

# === Setup ===
primes = sieve(3_000_000)[:50_000]  # 50k для скорости
gaps = [primes[i+1] - primes[i] for i in range(len(primes) - 1)]
gap1 = gaps[0]  # = 1, gap между 2 и 3
rest_gaps = gaps[1:]  # все остальные

print(f"Простых: {len(primes)}, gap[0] = {gap1}")
print(f"Автокорреляция lag 1 (все gaps): {autocorrelation_lag1(gaps):.6f}")
print(f"Автокорреляция lag 1 (rest gaps): {autocorrelation_lag1(rest_gaps):.6f}")

results = {}

# === 1. Baseline: настоящие простые ===
print("\n=== 1. Baseline (настоящие простые) ===")
maxes_real = gilbreath_max_decay(primes, 120)
firsts_real = gilbreath_first_elements(primes, 120)
bd_real = binary_collapse_depth(maxes_real)
fv_real = first_violation(firsts_real)

results["real_primes"] = {
    "autocorr_lag1": round(autocorrelation_lag1(gaps), 6),
    "binary_depth": bd_real,
    "first_violation": fv_real,
    "max_at_20": maxes_real[19],
    "max_at_50": maxes_real[49],
}
print(f"  Binary collapse: {bd_real}, First violation: {fv_real}")
print(f"  Max@20={maxes_real[19]}, Max@50={maxes_real[49]}")

# === 2. Shuffled (с фиксированным gap[0]=1) ===
print("\n=== 2. Shuffled (gap[0]=1 фиксирован) ===")
random.seed(42)
N_TRIALS = 20
shuffled_results = []
for trial in range(N_TRIALS):
    rest_shuffled = rest_gaps[:]
    random.shuffle(rest_shuffled)
    all_gaps = [gap1] + rest_shuffled
    seq = reconstruct_seq(primes[0], all_gaps)
    maxes = gilbreath_max_decay(seq, 120)
    firsts = gilbreath_first_elements(seq, 120)
    bd = binary_collapse_depth(maxes)
    fv = first_violation(firsts)
    shuffled_results.append({
        "trial": trial,
        "autocorr": round(autocorrelation_lag1(all_gaps), 6),
        "binary_depth": bd,
        "first_violation": fv,
        "max_at_20": maxes[19] if len(maxes) > 19 else None,
        "max_at_50": maxes[49] if len(maxes) > 49 else None,
    })

# Статистика по trials
violations = [r["first_violation"] for r in shuffled_results]
binary_depths = [r["binary_depth"] for r in shuffled_results]
max_at_50 = [r["max_at_50"] for r in shuffled_results if r["max_at_50"] is not None]

results["shuffled_fixed_gap0"] = {
    "n_trials": N_TRIALS,
    "violations": violations,
    "n_violations": sum(1 for v in violations if v is not None),
    "binary_depths": binary_depths,
    "n_binary_collapse": sum(1 for b in binary_depths if b is not None),
    "avg_max_at_50": round(sum(max_at_50) / len(max_at_50), 1) if max_at_50 else None,
}

print(f"  Нарушений Гилбрета: {results['shuffled_fixed_gap0']['n_violations']}/{N_TRIALS}")
print(f"  Бинарных коллапсов: {results['shuffled_fixed_gap0']['n_binary_collapse']}/{N_TRIALS}")
if violations:
    valid_v = [v for v in violations if v is not None]
    if valid_v:
        print(f"  Глубины нарушений: min={min(valid_v)}, max={max(valid_v)}, median={sorted(valid_v)[len(valid_v)//2]}")
if max_at_50:
    print(f"  Среднее max@50: {results['shuffled_fixed_gap0']['avg_max_at_50']}")

# === 3. Постепенное введение антикорреляции ===
print("\n=== 3. Градиент антикорреляции ===")
print("(смесь: α·anticorr_order + (1-α)·random_order)")

def make_anticorrelated_order(gaps_input, alpha, rng):
    """
    Создаёт порядок gaps с контролируемой антикорреляцией.
    alpha=0: случайный, alpha=1: максимально антикоррелированный.

    Метод: с вероятностью alpha выбираем "антикоррелированный" шаг
    (если текущий gap большой, следующий малый и наоборот),
    иначе случайный.
    """
    available = list(gaps_input[:])
    available.sort()
    result = []

    if not available:
        return result

    # Начнём с медианного
    mid = len(available) // 2
    result.append(available.pop(mid))

    while available:
        if rng.random() < alpha:
            # Антикоррелированный выбор
            if result[-1] >= sum(available) / len(available):
                # Текущий большой → берём малый
                result.append(available.pop(0))
            else:
                # Текущий малый → берём большой
                result.append(available.pop(-1))
        else:
            # Случайный выбор
            idx = rng.randint(0, len(available) - 1)
            result.append(available.pop(idx))

    return result

alphas = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
gradient_results = {}

for alpha in alphas:
    trials_data = []
    for trial in range(10):
        rng = random.Random(trial * 1000 + int(alpha * 100))
        reordered = make_anticorrelated_order(rest_gaps, alpha, rng)
        all_gaps = [gap1] + reordered
        seq = reconstruct_seq(primes[0], all_gaps)
        maxes = gilbreath_max_decay(seq, 120)
        firsts = gilbreath_first_elements(seq, 120)
        bd = binary_collapse_depth(maxes)
        fv = first_violation(firsts)
        ac1 = autocorrelation_lag1(all_gaps)
        trials_data.append({
            "binary_depth": bd,
            "first_violation": fv,
            "autocorr": ac1,
            "max_at_30": maxes[29] if len(maxes) > 29 else None,
        })

    avg_ac = sum(t["autocorr"] for t in trials_data) / len(trials_data)
    n_violations = sum(1 for t in trials_data if t["first_violation"] is not None)
    n_collapses = sum(1 for t in trials_data if t["binary_depth"] is not None)
    bd_list = [t["binary_depth"] for t in trials_data if t["binary_depth"] is not None]
    avg_bd = sum(bd_list) / len(bd_list) if bd_list else None
    max30_list = [t["max_at_30"] for t in trials_data if t["max_at_30"] is not None]
    avg_max30 = sum(max30_list) / len(max30_list) if max30_list else None

    gradient_results[str(alpha)] = {
        "avg_autocorr": round(avg_ac, 4),
        "n_violations": n_violations,
        "n_collapses": n_collapses,
        "avg_binary_depth": round(avg_bd, 1) if avg_bd else None,
        "avg_max_at_30": round(avg_max30, 1) if avg_max30 else None,
    }

    bd_str = f"{avg_bd:.1f}" if avg_bd else "None"
    m30_str = f"{avg_max30:.1f}" if avg_max30 else "None"
    print(f"  α={alpha:.1f}: autocorr={avg_ac:+.4f}, violations={n_violations}/10, "
          f"collapses={n_collapses}/10, avg_bd={bd_str:>6}, avg_max@30={m30_str:>6}")

results["gradient"] = gradient_results

# === 4. Ключевой тест: gaps с ТОЧНО такой же автокорреляцией как у простых ===
print("\n=== 4. Matching autocorrelation ===")
print("(ищем перестановку rest_gaps с автокорреляцией ≈ prime autocorrelation)")

target_ac = autocorrelation_lag1(rest_gaps)
print(f"  Целевая автокорреляция: {target_ac:.6f}")

# Метод: начинаем с случайной перестановки, делаем swaps чтобы приблизить автокорреляцию
rng = random.Random(12345)
matched_gaps = rest_gaps[:]
rng.shuffle(matched_gaps)

current_ac = autocorrelation_lag1(matched_gaps)
print(f"  Начальная (random): {current_ac:.6f}")

# Simulated annealing для matching
for iteration in range(50000):
    i = rng.randint(0, len(matched_gaps) - 1)
    j = rng.randint(0, len(matched_gaps) - 1)
    if i == j:
        continue

    # Попробуем swap
    matched_gaps[i], matched_gaps[j] = matched_gaps[j], matched_gaps[i]
    new_ac = autocorrelation_lag1(matched_gaps)

    if abs(new_ac - target_ac) < abs(current_ac - target_ac):
        current_ac = new_ac
    else:
        # Откатываем
        matched_gaps[i], matched_gaps[j] = matched_gaps[j], matched_gaps[i]

    if abs(current_ac - target_ac) < 0.001:
        break

print(f"  Финальная автокорреляция: {current_ac:.6f}")

all_gaps_matched = [gap1] + matched_gaps
seq_matched = reconstruct_seq(primes[0], all_gaps_matched)
maxes_matched = gilbreath_max_decay(seq_matched, 120)
firsts_matched = gilbreath_first_elements(seq_matched, 120)
bd_matched = binary_collapse_depth(maxes_matched)
fv_matched = first_violation(firsts_matched)

results["matched_autocorr"] = {
    "target_autocorr": round(target_ac, 6),
    "achieved_autocorr": round(current_ac, 6),
    "binary_depth": bd_matched,
    "first_violation": fv_matched,
    "max_at_30": maxes_matched[29] if len(maxes_matched) > 29 else None,
    "max_at_50": maxes_matched[49] if len(maxes_matched) > 49 else None,
}

print(f"  Binary collapse: {bd_matched}")
print(f"  First violation: {fv_matched}")
print(f"  Max@30={maxes_matched[29] if len(maxes_matched) > 29 else 'N/A'}")
print(f"  Max@50={maxes_matched[49] if len(maxes_matched) > 49 else 'N/A'}")

# === 5. Условные средние: регрессия к среднему ===
print("\n=== 5. Регрессия к среднему в prime gaps ===")

# Ключевая гипотеза: после большого gap, следующий gap В СРЕДНЕМ меньше.
# Это и есть механизм "усреднения" при взятии разностей.
mean_gap = sum(gaps) / len(gaps)
above_mean = [(i, gaps[i]) for i in range(len(gaps)-1) if gaps[i] > mean_gap * 2]
below_mean = [(i, gaps[i]) for i in range(len(gaps)-1) if gaps[i] < mean_gap / 2]

if above_mean:
    after_big = [gaps[i+1] for i, g in above_mean]
    avg_after_big = sum(after_big) / len(after_big)
else:
    avg_after_big = 0

if below_mean:
    after_small = [gaps[i+1] for i, g in below_mean]
    avg_after_small = sum(after_small) / len(after_small)
else:
    avg_after_small = 0

results["regression_to_mean"] = {
    "mean_gap": round(mean_gap, 2),
    "avg_gap_after_big": round(avg_after_big, 2),
    "avg_gap_after_small": round(avg_after_small, 2),
    "n_big": len(above_mean),
    "n_small": len(below_mean),
    "regression_ratio": round(avg_after_big / avg_after_small, 4) if avg_after_small > 0 else None,
}

print(f"  Средний gap: {mean_gap:.2f}")
print(f"  Средний gap ПОСЛЕ большого (>{2*mean_gap:.0f}): {avg_after_big:.2f} (n={len(above_mean)})")
print(f"  Средний gap ПОСЛЕ маленького (<{mean_gap/2:.0f}): {avg_after_small:.2f} (n={len(below_mean)})")
print(f"  Отношение: {avg_after_big/avg_after_small:.4f}" if avg_after_small > 0 else "  N/A")

# === ИТОГИ ===
print("\n" + "=" * 60)
print("ВЫВОДЫ")
print("=" * 60)

conclusions = []

# 1. Автокорреляция
if results["shuffled_fixed_gap0"]["n_violations"] > 0:
    conclusions.append(
        f"Перемешивание gaps (с фиксированным gap[0]=1) приводит к нарушениям "
        f"Гилбрета в {results['shuffled_fixed_gap0']['n_violations']}/{N_TRIALS} случаев."
    )
else:
    conclusions.append("Перемешивание gaps с фиксированным gap[0]=1 НЕ ломает Гилбрета.")

# 2. Градиент
for alpha_str, gdata in gradient_results.items():
    if gdata["n_violations"] == 0:
        conclusions.append(f"При α≥{alpha_str} (anticorr≈{gdata['avg_autocorr']:+.4f}) Гилбрет выполняется.")
        break

# 3. Matched autocorrelation
if fv_matched is None and bd_matched is not None:
    conclusions.append(
        f"Случайные gaps с matching автокорреляцией ({current_ac:.4f}): "
        f"Гилбрет ВЫПОЛНЯЕТСЯ, binary collapse на глубине {bd_matched}."
    )
elif fv_matched is not None:
    conclusions.append(
        f"Случайные gaps с matching автокорреляцией ({current_ac:.4f}): "
        f"Гилбрет НАРУШАЕТСЯ на глубине {fv_matched}."
    )

# 4. Регрессия к среднему
if avg_after_big < mean_gap and avg_after_small > mean_gap:
    conclusions.append(
        "Prime gaps показывают регрессию к среднему: после больших — меньше среднего, "
        "после маленьких — больше среднего."
    )

for i, c in enumerate(conclusions, 1):
    print(f"\n{i}. {c}")

results["conclusions"] = conclusions

with open("prime_gap_dynamics_v2_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2, default=str)

print(f"\n\nРезультаты сохранены в prime_gap_dynamics_v2_results.json")
