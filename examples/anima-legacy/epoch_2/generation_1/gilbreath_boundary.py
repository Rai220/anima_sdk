"""
Граница Гилбрета: когда именно коллапс перестаёт работать?

Вопрос: можно ли построить последовательность gaps = [1, 2, even, even, ...]
(сохраняя паритетный инвариант), которая НЕ коллапсирует?

Если да — это точно определяет, какое свойство простых чисел нужно для Гилбрета.
Если нет — паритетный инвариант + начальные условия ДОСТАТОЧНЫ.
"""

import json
import random
import math

def abs_diff_row(row):
    return [abs(row[i+1] - row[i]) for i in range(len(row) - 1)]

def collapse_depth(row, max_steps=500):
    """Глубина, на которой max ≤ 2. None если не коллапсирует."""
    r = row[:]
    for d in range(max_steps):
        if len(r) < 2:
            return None
        if max(r) <= 2:
            return d
        r = abs_diff_row(r)
    return None

def gilbreath_violation_depth(seq, max_depth=300):
    """Глубина первого нарушения first≠1."""
    row = seq[:]
    for d in range(max_depth):
        if len(row) < 2:
            return None
        row = abs_diff_row(row)
        if row[0] != 1:
            return d + 1
    return None

results = {}

# === 1. Adversarial gaps с паритетным инвариантом ===
print("=== 1. Adversarial gaps [1, 2, even, even, ...] ===\n")

# Паритетный инвариант: gap[0]=1 (odd), gap[1]=2 (even), остальные — чётные.
# Это гарантирует, что первая строка = [1, even, even, ...]
# По теореме из v3, это гарантирует first=1 на строке 1.
# Но КОЛЛАПС к {0,1,2} — другой вопрос.

# Стратегия: выбираем чётные gaps так, чтобы max не убывал.
# "Step function" подход: gaps = [1, 2, M, M, M, ..., M]
# Это даёт: primes = [2, 3, 5, 5+M, 5+2M, ...]

def make_step_gaps(M, L):
    """gaps = [1, 2, M, M, ..., M]"""
    return [1, 2] + [M] * (L - 2)

def make_alternating_gaps(M_small, M_big, L):
    """gaps = [1, 2, M_small, M_big, M_small, M_big, ...]"""
    return [1, 2] + [M_small if i % 2 == 0 else M_big for i in range(L - 2)]

def gaps_to_seq(gaps, start=2):
    seq = [start]
    for g in gaps:
        seq.append(seq[-1] + g)
    return seq

L = 100
print(f"Длина: {L}")
print(f"{'Pattern':<35} | CD    | Violation | first 5 gaps")

adversarial_results = {}

patterns = {
    "step_M=4":     make_step_gaps(4, L),
    "step_M=10":    make_step_gaps(10, L),
    "step_M=20":    make_step_gaps(20, L),
    "step_M=50":    make_step_gaps(50, L),
    "alt_2_4":      make_alternating_gaps(2, 4, L),
    "alt_2_10":     make_alternating_gaps(2, 10, L),
    "alt_2_20":     make_alternating_gaps(2, 20, L),
    "alt_2_50":     make_alternating_gaps(2, 50, L),
    "alt_4_50":     make_alternating_gaps(4, 50, L),
    "const_2":      [1, 2] + [2] * (L - 2),
    "const_4":      [1, 2] + [4] * (L - 2),
    "const_6":      [1, 2] + [6] * (L - 2),
}

# Добавим "реалистичные" паттерны: gaps растут как log
for growth in ["log", "sqrt"]:
    name = f"growing_{growth}"
    if growth == "log":
        gaps = [1, 2] + [max(2, 2 * round(math.log(i + 3))) for i in range(L - 2)]
    else:
        gaps = [1, 2] + [max(2, 2 * round(math.sqrt(i + 1))) for i in range(L - 2)]
    # Ensure all even
    gaps = [gaps[0], gaps[1]] + [g if g % 2 == 0 else g + 1 for g in gaps[2:]]
    patterns[name] = gaps

for name, gaps in patterns.items():
    seq = gaps_to_seq(gaps)
    cd = collapse_depth(gaps, max_steps=500)
    vd = gilbreath_violation_depth(seq, max_depth=300)
    cd_str = str(cd) if cd is not None else ">500"
    vd_str = str(vd) if vd is not None else "OK"
    adversarial_results[name] = {
        "collapse_depth": cd,
        "violation_depth": vd,
        "gaps_prefix": gaps[:7],
    }
    print(f"{name:<35} | {cd_str:>5} | {vd_str:>9} | {gaps[:5]}")

results["adversarial_gaps"] = adversarial_results

# === 2. Ключевой тест: step gaps ломают Гилбрета? ===
print("\n=== 2. Step gaps: ломают ли Гилбрета? ===\n")

# gaps = [1, 2, M, M, M, ...]
# seq = [2, 3, 5, 5+M, 5+2M, ...]
# Row 1: |3-2|=1, |5-3|=2, |5+M-5|=M, |5+2M-(5+M)|=M, ... = [1, 2, M, M, ...]
# Row 2: |2-1|=1, |M-2|=M-2, |M-M|=0, |M-M|=0, ... = [1, M-2, 0, 0, ...]
# Row 3: |M-2-1|=M-3, |0-(M-2)|=M-2, 0, ... = [M-3, M-2, 0, ...]
# Row 4: |(M-2)-(M-3)|=1, |0-(M-2)|=M-2, ... = [1, M-2, ...]
# ...

# Давайте проследим вручную для M=10
print("Ручная проверка: gaps = [1, 2, 10, 10, 10, 10, 10, 10]")
gaps_test = [1, 2, 10, 10, 10, 10, 10, 10]
seq_test = gaps_to_seq(gaps_test)
print(f"  seq = {seq_test}")

row = seq_test[:]
for d in range(10):
    if len(row) < 2:
        break
    row = abs_diff_row(row)
    print(f"  Row {d+1}: {row}  (first={row[0]}, max={max(row)})")

# === 3. Что если gaps РАСТУТ? (как настоящие prime gaps) ===
print("\n=== 3. Растущие gaps (имитация prime gaps) ===\n")

# Prime gaps растут как O(log p). Это значит: max(gaps[0:N]) ~ c·log(p_N) ~ c·log(N·log N)
# Конкретнее: для N=10000, max gap ≈ 72

# Создадим последовательность gaps с растущим max, но без структуры простых

def make_growing_gaps(N, growth_rate="log"):
    """Генерирует gaps [1, 2, even, even, ...] с растущим max."""
    gaps = [1, 2]
    rng = random.Random(42)
    for i in range(2, N):
        if growth_rate == "log":
            max_gap = max(2, int(2 * math.log(i + 2)))
        elif growth_rate == "sqrt":
            max_gap = max(2, int(2 * math.sqrt(i + 1)))
        else:
            max_gap = growth_rate
        # Случайный чётный gap ≤ max_gap
        g = 2 * rng.randint(1, max(1, max_gap // 2))
        gaps.append(g)
    return gaps

print(f"{'Growth':<12} | N     | max(gap) | CD     | Violation")

growing_results = {}
for growth in ["log", "sqrt"]:
    for N in [100, 500, 1000, 5000]:
        gaps = make_growing_gaps(N, growth)
        seq = gaps_to_seq(gaps)
        mg = max(gaps)
        cd = collapse_depth(gaps, max_steps=500)
        vd = gilbreath_violation_depth(seq, max_depth=300)
        cd_str = str(cd) if cd is not None else ">500"
        vd_str = str(vd) if vd is not None else "OK"
        key = f"{growth}_N{N}"
        growing_results[key] = {
            "max_gap": mg,
            "collapse_depth": cd,
            "violation_depth": vd,
        }
        print(f"{growth:<12} | {N:<5} | {mg:<8} | {cd_str:<6} | {vd_str}")

results["growing_gaps"] = growing_results

# === 4. Сравнение: настоящие простые vs синтетические с тем же ростом ===
print("\n=== 4. Простые vs синтетические ===\n")

def sieve(n):
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, n + 1, i):
                is_prime[j] = False
    return [i for i in range(2, n + 1) if is_prime[i]]

primes = sieve(500_000)[:5000]
real_gaps = [primes[i+1] - primes[i] for i in range(len(primes) - 1)]

# Синтетические gaps с matching distribution
from collections import Counter
gap_dist = Counter(real_gaps[2:])  # пропускаем gap[0]=1, gap[1]=2
gap_pool = []
for g, c in gap_dist.items():
    gap_pool.extend([g] * c)

rng = random.Random(123)
N_trials = 20
print(f"N = {len(primes)}")
print(f"{'Type':<25} | CD     | Violation | max(gap)")

# Настоящие простые
cd_real = collapse_depth(real_gaps, max_steps=500)
vd_real = gilbreath_violation_depth(primes, max_depth=300)
print(f"{'Real primes':<25} | {cd_real if cd_real else '>500':>6} | {'OK' if vd_real is None else vd_real:>9} | {max(real_gaps)}")

# Синтетические: shuffle pool, сохраняя gap[0]=1, gap[1]=2
synth_results = []
for trial in range(N_trials):
    rng_t = random.Random(trial * 100)
    pool_copy = gap_pool[:]
    rng_t.shuffle(pool_copy)
    synth_gaps = [1, 2] + pool_copy[:len(real_gaps) - 2]
    seq = gaps_to_seq(synth_gaps)
    cd = collapse_depth(synth_gaps, max_steps=500)
    vd = gilbreath_violation_depth(seq, max_depth=300)
    synth_results.append({"cd": cd, "vd": vd})

n_collapse = sum(1 for r in synth_results if r["cd"] is not None)
n_violation = sum(1 for r in synth_results if r["vd"] is not None)
cd_list = [r["cd"] for r in synth_results if r["cd"] is not None]
avg_cd = sum(cd_list) / len(cd_list) if cd_list else None
print(f"{'Shuffled (same dist)':<25} | {avg_cd if avg_cd else '>500':>6} | {n_violation:>2}/{N_trials} fail | {max(gap_pool)}")

# Синтетические: случайные чётные gaps с тем же max
max_g = max(real_gaps)
random_results = []
for trial in range(N_trials):
    rng_t = random.Random(trial * 200)
    rand_gaps = [1, 2] + [2 * rng_t.randint(1, max_g // 2) for _ in range(len(real_gaps) - 2)]
    seq = gaps_to_seq(rand_gaps)
    cd = collapse_depth(rand_gaps, max_steps=500)
    vd = gilbreath_violation_depth(seq, max_depth=300)
    random_results.append({"cd": cd, "vd": vd})

n_collapse_r = sum(1 for r in random_results if r["cd"] is not None)
n_violation_r = sum(1 for r in random_results if r["vd"] is not None)
cd_list_r = [r["cd"] for r in random_results if r["cd"] is not None]
avg_cd_r = sum(cd_list_r) / len(cd_list_r) if cd_list_r else None
print(f"{'Random even (same max)':<25} | {avg_cd_r if avg_cd_r else '>500':>6} | {n_violation_r:>2}/{N_trials} fail | {max_g}")

results["primes_vs_synthetic"] = {
    "real": {"cd": cd_real, "vd": vd_real, "max_gap": max(real_gaps)},
    "shuffled": {
        "n_collapse": n_collapse,
        "n_violation": n_violation,
        "avg_cd": round(avg_cd, 1) if avg_cd else None,
    },
    "random_even": {
        "n_collapse": n_collapse_r,
        "n_violation": n_violation_r,
        "avg_cd": round(avg_cd_r, 1) if avg_cd_r else None,
    },
}

# === ИТОГИ ===
print("\n" + "=" * 60)
print("РЕЗУЛЬТАТЫ")
print("=" * 60)

conclusions = []

# Анализ step gaps
step_violations = {k: v for k, v in adversarial_results.items() if k.startswith("step_")}
step_fails = sum(1 for v in step_violations.values() if v["violation_depth"] is not None)
if step_fails > 0:
    conclusions.append(
        f"Step gaps [1,2,M,M,...] ЛОМАЮТ Гилбрета при M≥? — "
        f"{step_fails}/{len(step_violations)} ломают."
    )
else:
    conclusions.append(
        "Step gaps [1,2,M,M,...] НЕ ломают Гилбрета (first=1 всегда)."
    )

# Альтернирующие
alt_violations = {k: v for k, v in adversarial_results.items() if k.startswith("alt_")}
alt_fails = sum(1 for v in alt_violations.values() if v["violation_depth"] is not None)
conclusions.append(
    f"Alternating gaps [1,2,small,big,...]: "
    f"{alt_fails}/{len(alt_violations)} ломают Гилбрета."
)

# Растущие
growing_fails = sum(1 for v in growing_results.values() if v["violation_depth"] is not None)
conclusions.append(
    f"Растущие gaps (log/sqrt рост): {growing_fails}/{len(growing_results)} ломают."
)

# Shuffled vs real
if n_violation > 0:
    conclusions.append(
        f"Shuffled gaps (same distribution, different order): "
        f"{n_violation}/{N_trials} ломают Гилбрета. "
        f"ПОРЯДОК gaps критичен."
    )
elif n_violation == 0:
    conclusions.append(
        f"Shuffled gaps (same distribution): 0/{N_trials} ломают. "
        f"Достаточно РАСПРЕДЕЛЕНИЯ, порядок не критичен."
    )

for i, c in enumerate(conclusions, 1):
    print(f"\n{i}. {c}")

results["conclusions"] = conclusions

with open("gilbreath_boundary_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2, default=str)

print(f"\n\nРезультаты сохранены в gilbreath_boundary_results.json")
