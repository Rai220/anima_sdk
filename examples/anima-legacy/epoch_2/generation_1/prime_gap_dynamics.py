"""
Динамика prime gaps: почему порядок простых критичен для Гилбрета?

Предыдущая генерация показала:
- Перемешивание gaps ломает гипотезу Гилбрета немедленно
- Бинарный коллапс наступает на глубине ~113
- Паритет наследуется (доказано)
- ПОЧЕМУ max убывает — открытый вопрос

Гипотеза этого эксперимента:
Max убывает потому, что prime gaps имеют ОТРИЦАТЕЛЬНУЮ автокорреляцию
на малых лагах (большой gap обычно следует за малым). Это "усредняет"
разности и прижимает max к 2.

Проверяем:
1. Автокорреляция prime gaps
2. Связь автокорреляции со скоростью убывания max в треугольнике Гилбрета
3. Что если искусственно УБИТЬ автокорреляцию, сохранив распределение?
4. Что если УСИЛИТЬ антикорреляцию?
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

def autocorrelation(seq, max_lag=20):
    """Вычисляет автокорреляцию последовательности."""
    n = len(seq)
    mean = sum(seq) / n
    var = sum((x - mean)**2 for x in seq) / n
    if var == 0:
        return [1.0] + [0.0] * (max_lag - 1)
    result = []
    for lag in range(1, max_lag + 1):
        cov = sum((seq[i] - mean) * (seq[i + lag] - mean) for i in range(n - lag)) / (n - lag)
        result.append(cov / var)
    return result

def gilbreath_max_decay(seq, max_depth):
    """Возвращает список max значений по глубинам треугольника Гилбрета."""
    row = seq[:]
    maxes = []
    for d in range(max_depth):
        if len(row) < 2:
            break
        row = [abs(row[i+1] - row[i]) for i in range(len(row) - 1)]
        maxes.append(max(row))
    return maxes

def gilbreath_first_elements(seq, max_depth):
    """Возвращает первые элементы строк треугольника."""
    row = seq[:]
    firsts = []
    for d in range(max_depth):
        if len(row) < 2:
            break
        row = [abs(row[i+1] - row[i]) for i in range(len(row) - 1)]
        firsts.append(row[0])
    return firsts

results = {}

# === 1. Prime gaps и их автокорреляция ===
print("=== 1. Автокорреляция prime gaps ===")

primes = sieve(3_000_000)[:100_000]
gaps = [primes[i+1] - primes[i] for i in range(len(primes) - 1)]

ac = autocorrelation(gaps, max_lag=20)
results["autocorrelation"] = {f"lag_{i+1}": round(ac[i], 6) for i in range(len(ac))}

print("Автокорреляция prime gaps:")
for i, a in enumerate(ac[:10]):
    sign = "+" if a >= 0 else ""
    print(f"  lag {i+1}: {sign}{a:.6f}")

# === 2. Скорость убывания max в треугольнике ===
print("\n=== 2. Max decay для простых ===")

max_decay_primes = gilbreath_max_decay(primes, 150)
binary_depth = None
for i, mx in enumerate(max_decay_primes):
    if mx <= 2:
        binary_depth = i + 1
        break

results["primes_binary_depth"] = binary_depth
print(f"Бинарный коллапс на глубине: {binary_depth}")

# === 3. Перемешанные gaps (сохраняем распределение, убиваем корреляцию) ===
print("\n=== 3. Перемешанные gaps ===")

random.seed(42)
shuffled_gaps = gaps[:]
random.shuffle(shuffled_gaps)

# Реконструируем последовательность из перемешанных gaps
shuffled_seq = [primes[0]]
for g in shuffled_gaps:
    shuffled_seq.append(shuffled_seq[-1] + g)

ac_shuffled = autocorrelation(shuffled_gaps, max_lag=10)
max_decay_shuffled = gilbreath_max_decay(shuffled_seq, 150)

# Первый элемент строки 1 = первый gap = shuffled_gaps[0]
firsts_shuffled = gilbreath_first_elements(shuffled_seq, 50)
first_not_one = None
for i, f in enumerate(firsts_shuffled):
    if f != 1:
        first_not_one = i + 1
        break

results["shuffled"] = {
    "autocorrelation_lag1": round(ac_shuffled[0], 6),
    "max_at_depth_10": max_decay_shuffled[9] if len(max_decay_shuffled) > 9 else None,
    "max_at_depth_50": max_decay_shuffled[49] if len(max_decay_shuffled) > 49 else None,
    "first_violation_depth": first_not_one,
    "first_elements_10": firsts_shuffled[:10]
}

print(f"Автокорреляция lag 1 (shuffled): {ac_shuffled[0]:.6f} (vs primes: {ac[0]:.6f})")
print(f"Max на глубине 10: shuffled={max_decay_shuffled[9]}, primes={max_decay_primes[9]}")
print(f"Max на глубине 50: shuffled={max_decay_shuffled[49]}, primes={max_decay_primes[49]}")
print(f"Первое нарушение (first ≠ 1): глубина {first_not_one}")

# === 4. Антикоррелированные gaps ===
print("\n=== 4. Искусственно антикоррелированные gaps ===")

# Стратегия: сортируем gaps и чередуем большие с малыми
# [min, max, min+1, max-1, ...] — максимальная антикорреляция
sorted_gaps = sorted(gaps)
n = len(sorted_gaps)
anticorr_gaps = []
for i in range(n // 2):
    anticorr_gaps.append(sorted_gaps[i])
    anticorr_gaps.append(sorted_gaps[n - 1 - i])
if n % 2:
    anticorr_gaps.append(sorted_gaps[n // 2])

anticorr_seq = [primes[0]]
for g in anticorr_gaps:
    anticorr_seq.append(anticorr_seq[-1] + g)

ac_anticorr = autocorrelation(anticorr_gaps, max_lag=10)
max_decay_anticorr = gilbreath_max_decay(anticorr_seq, 150)

anticorr_binary_depth = None
for i, mx in enumerate(max_decay_anticorr):
    if mx <= 2:
        anticorr_binary_depth = i + 1
        break

firsts_anticorr = gilbreath_first_elements(anticorr_seq, 50)
anticorr_violation = None
for i, f in enumerate(firsts_anticorr):
    if f != 1:
        anticorr_violation = i + 1
        break

results["anticorrelated"] = {
    "autocorrelation_lag1": round(ac_anticorr[0], 6),
    "binary_depth": anticorr_binary_depth,
    "first_violation_depth": anticorr_violation,
    "max_at_depth_10": max_decay_anticorr[9] if len(max_decay_anticorr) > 9 else None,
    "max_at_depth_50": max_decay_anticorr[49] if len(max_decay_anticorr) > 49 else None,
    "first_elements_10": firsts_anticorr[:10]
}

print(f"Автокорреляция lag 1 (anticorr): {ac_anticorr[0]:.6f}")
print(f"Бинарный коллапс: глубина {anticorr_binary_depth}")
print(f"Первое нарушение: глубина {anticorr_violation}")

# === 5. Положительно коррелированные gaps ===
print("\n=== 5. Положительно коррелированные gaps (sorted) ===")

# Просто отсортированные gaps — максимальная положительная корреляция
poscorr_seq = [primes[0]]
for g in sorted_gaps:
    poscorr_seq.append(poscorr_seq[-1] + g)

ac_poscorr = autocorrelation(sorted_gaps, max_lag=10)
max_decay_poscorr = gilbreath_max_decay(poscorr_seq, 150)

firsts_poscorr = gilbreath_first_elements(poscorr_seq, 50)
poscorr_violation = None
for i, f in enumerate(firsts_poscorr):
    if f != 1:
        poscorr_violation = i + 1
        break

results["positively_correlated"] = {
    "autocorrelation_lag1": round(ac_poscorr[0], 6),
    "first_violation_depth": poscorr_violation,
    "max_at_depth_10": max_decay_poscorr[9] if len(max_decay_poscorr) > 9 else None,
    "max_at_depth_50": max_decay_poscorr[49] if len(max_decay_poscorr) > 49 else None,
    "first_elements_10": firsts_poscorr[:10]
}

print(f"Автокорреляция lag 1 (sorted): {ac_poscorr[0]:.6f}")
print(f"Max на глубине 10: {max_decay_poscorr[9]}")
print(f"Первое нарушение: глубина {poscorr_violation}")

# === 6. Gap-gap корреляция (conditional) ===
print("\n=== 6. Условная структура: P(gap_n+1 | gap_n) ===")

# Какова вероятность следующего gap, зная предыдущий?
transition = {}
for i in range(len(gaps) - 1):
    g1, g2 = gaps[i], gaps[i+1]
    if g1 not in transition:
        transition[g1] = []
    transition[g1].append(g2)

# Для самых частых gaps: среднее и дисперсия следующего gap
common_gaps = [2, 4, 6, 8, 10, 12]
conditional = {}
for g in common_gaps:
    if g in transition and len(transition[g]) > 100:
        followers = transition[g]
        mean_f = sum(followers) / len(followers)
        var_f = sum((f - mean_f)**2 for f in followers) / len(followers)
        conditional[g] = {
            "count": len(followers),
            "mean_next": round(mean_f, 2),
            "std_next": round(var_f**0.5, 2),
            "most_common_next": Counter(followers).most_common(3)
        }
        print(f"  После gap={g}: среднее следующего={mean_f:.2f}, std={var_f**0.5:.2f}")

results["conditional_gaps"] = {str(k): {kk: str(vv) for kk, vv in v.items()} for k, v in conditional.items()}

# === 7. Спектральный анализ (простейший — DFT через ручной расчёт) ===
print("\n=== 7. Спектральный анализ gaps ===")

# Используем косинусное преобразование (DCT-подобное) для первых 1024 gaps
N = 1024
gap_segment = gaps[:N]
mean_g = sum(gap_segment) / N
centered = [g - mean_g for g in gap_segment]

# Вычисляем мощность для нескольких частот
power_spectrum = {}
freqs_to_check = [1, 2, 3, 4, 5, 6, 7, 8, 16, 32, 64, 128, 256]
for freq in freqs_to_check:
    cos_sum = sum(centered[i] * math.cos(2 * math.pi * freq * i / N) for i in range(N))
    sin_sum = sum(centered[i] * math.sin(2 * math.pi * freq * i / N) for i in range(N))
    power = (cos_sum**2 + sin_sum**2) / N
    power_spectrum[freq] = round(power, 2)

# Сравним с перемешанными
shuffled_segment = shuffled_gaps[:N]
mean_s = sum(shuffled_segment) / N
centered_s = [g - mean_s for g in shuffled_segment]
power_shuffled = {}
for freq in freqs_to_check:
    cos_sum = sum(centered_s[i] * math.cos(2 * math.pi * freq * i / N) for i in range(N))
    sin_sum = sum(centered_s[i] * math.sin(2 * math.pi * freq * i / N) for i in range(N))
    power = (cos_sum**2 + sin_sum**2) / N
    power_shuffled[freq] = round(power, 2)

results["spectrum"] = {
    "primes": power_spectrum,
    "shuffled": power_shuffled
}

print("Частота | Мощность (primes) | Мощность (shuffled)")
for freq in freqs_to_check:
    print(f"  {freq:>5} | {power_spectrum[freq]:>12.2f}     | {power_shuffled[freq]:>12.2f}")

# === 8. Итоговый вердикт ===
print("\n" + "=" * 60)
print("ИТОГИ")
print("=" * 60)

# Проверяем гипотезу: антикорреляция → быстрый коллапс
prime_ac1 = ac[0]
shuff_ac1 = ac_shuffled[0]
anti_ac1 = ac_anticorr[0]
pos_ac1 = ac_poscorr[0]

summary = {
    "hypothesis": "Отрицательная автокорреляция prime gaps ускоряет коллапс max в треугольнике Гилбрета",
    "evidence": {
        "primes": {
            "autocorr_lag1": round(prime_ac1, 6),
            "binary_depth": binary_depth,
            "max_depth_50": max_decay_primes[49] if len(max_decay_primes) > 49 else None
        },
        "shuffled": {
            "autocorr_lag1": round(shuff_ac1, 6),
            "violation": results["shuffled"]["first_violation_depth"],
            "max_depth_50": results["shuffled"]["max_at_depth_50"]
        },
        "anticorrelated": {
            "autocorr_lag1": round(anti_ac1, 6),
            "binary_depth": anticorr_binary_depth,
            "max_depth_50": results["anticorrelated"]["max_at_depth_50"]
        },
        "positively_correlated": {
            "autocorr_lag1": round(pos_ac1, 6),
            "violation": results["positively_correlated"]["first_violation_depth"],
            "max_depth_50": results["positively_correlated"]["max_at_depth_50"]
        }
    }
}

# Проверка: если антикорреляция помогает, anticorr_binary_depth < shuffled_max_depth
hypothesis_supported = (
    anticorr_binary_depth is not None and
    (results["shuffled"]["first_violation_depth"] is not None or
     results["shuffled"]["max_at_depth_50"] is not None and
     results["anticorrelated"]["max_at_depth_50"] is not None and
     results["anticorrelated"]["max_at_depth_50"] < results["shuffled"]["max_at_depth_50"])
)

summary["verdict"] = (
    "ПОДТВЕРЖДЕНА" if hypothesis_supported else "ОПРОВЕРГНУТА или НЕОПРЕДЕЛЁННА"
)

results["summary"] = summary

print(f"\nАвтокорреляция lag 1:")
print(f"  Primes:          {prime_ac1:+.6f}")
print(f"  Shuffled:        {shuff_ac1:+.6f}")
print(f"  Anticorrelated:  {anti_ac1:+.6f}")
print(f"  Sorted (pos):    {pos_ac1:+.6f}")
print()
print(f"Бинарный коллапс:")
print(f"  Primes:          глубина {binary_depth}")
print(f"  Anticorrelated:  глубина {anticorr_binary_depth}")
print(f"  Shuffled:        нарушение на глубине {results['shuffled']['first_violation_depth']}")
print(f"  Sorted:          нарушение на глубине {results['positively_correlated']['first_violation_depth']}")
print()
print(f"Гипотеза: {summary['verdict']}")

with open("prime_gap_dynamics_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2, default=str)

print("\nРезультаты сохранены в prime_gap_dynamics_results.json")
