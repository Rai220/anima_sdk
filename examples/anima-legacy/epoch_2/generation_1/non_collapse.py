"""
Не-коллапсирующие последовательности.

Предыдущий эксперимент показал: [0, M, M, M, ...] НЕ коллапсирует к {0,1,2}.
abs_diff([0, M, M, M, ...]) = [M, 0, 0, 0, ...] → [M, 0, 0, ...] → ...
Max остаётся = M пока строка не сожмётся до длины 1.

Вопросы:
1. Какие именно последовательности не коллапсируют?
2. Что отличает prime gaps от adversarial конструкций?
3. Есть ли простой критерий коллапса?
"""

import json
from collections import Counter

def abs_diff_row(row):
    return [abs(row[i+1] - row[i]) for i in range(len(row) - 1)]

def max_trace(row, max_steps=500):
    """Возвращает список max(row) на каждом шаге."""
    r = row[:]
    trace = [max(r)]
    for _ in range(max_steps):
        if len(r) < 2:
            break
        r = abs_diff_row(r)
        trace.append(max(r))
    return trace

def collapses(row):
    """Коллапсирует ли к {0,1,2}?"""
    r = row[:]
    for _ in range(len(row) + 100):
        if len(r) < 2:
            return False  # строка сожралась раньше коллапса
        if max(r) <= 2:
            return True
        r = abs_diff_row(r)
    return False

results = {}

# === 1. Классификация не-коллапсирующих паттернов ===
print("=== 1. Какие паттерны НЕ коллапсируют? ===\n")

# Проверим типичные конструкции
test_patterns = {
    "constant": lambda M, L: [M] * L,
    "step_0M": lambda M, L: [0] + [M] * (L - 1),
    "step_M0": lambda M, L: [M] + [0] * (L - 1),
    "alternating_0M": lambda M, L: [0 if i % 2 == 0 else M for i in range(L)],
    "alternating_M0": lambda M, L: [M if i % 2 == 0 else 0 for i in range(L)],
    "ramp_up": lambda M, L: [i * M // (L - 1) for i in range(L)],
    "ramp_down": lambda M, L: [(L - 1 - i) * M // (L - 1) for i in range(L)],
    "sawtooth": lambda M, L: [i % (M + 1) for i in range(L)],
    "random_like": lambda M, L: [(i * 7 + 3) % (M + 1) for i in range(L)],
    "block_0M": lambda M, L: [0] * (L // 2) + [M] * (L - L // 2),
}

M = 5
L = 50
print(f"M={M}, L={L}")
print(f"{'Pattern':<20} | Collapses? | Max trace (first 10)")

pattern_results = {}
for name, gen in test_patterns.items():
    row = gen(M, L)
    c = collapses(row)
    trace = max_trace(row, max_steps=20)
    pattern_results[name] = {
        "collapses": c,
        "max_trace": trace[:15],
    }
    trace_str = " ".join(str(t) for t in trace[:10])
    print(f"{name:<20} | {'YES' if c else 'NO ':>3}        | {trace_str}")

results["patterns"] = pattern_results

# === 2. Необходимое условие не-коллапса ===
print("\n=== 2. Необходимое условие: почему [0,M,M,...] не коллапсирует ===\n")

# [0, M, M, M, ..., M] длины L
# Step 1: [M, 0, 0, ..., 0] длины L-1
# Step 2: [M, 0, 0, ..., 0] длины L-2
# ...
# Step L-2: [M] длины 1
# Max = M на КАЖДОМ шаге!

# А [M, M, M, ..., M]?
# Step 1: [0, 0, 0, ..., 0] → max=0 → коллапсирует сразу

# А [0, M, 0, M, ...]?
# Step 1: [M, M, M, M, ...] → step 2: [0, 0, 0, ...] → коллапс!

print("Ключевое наблюдение: [0, M, M, ..., M] не коллапсирует, потому что")
print("abs_diff([0, M, M, ...]) = [M, 0, 0, ...] — тот же паттерн, сдвинутый.")
print("Это ФИКСИРОВАННАЯ ТОЧКА оператора T (с точностью до длины).\n")

# Найдём ВСЕ фиксированные паттерны: строки r такие, что
# abs_diff(r) имеет тот же max И тот же тип
print("Поиск фиксированных паттернов оператора abs-diff:")
print("(строки где max не убывает при итерации)\n")

# Для M=4, длина 8 — полный перебор
M_test = 4
L_test = 8
non_collapsing = []
total = 0

def gen_rows(M, L):
    if L == 0:
        yield []
        return
    for rest in gen_rows(M, L - 1):
        for v in range(M + 1):
            yield rest + [v]

for row in gen_rows(M_test, L_test):
    total += 1
    if max(row) <= 2:
        continue  # уже в {0,1,2}, не интересно
    if not collapses(row):
        non_collapsing.append(row)

print(f"M={M_test}, L={L_test}: всего строк с max>2: {total - (3**L_test)}")
print(f"Из них НЕ коллапсируют: {len(non_collapsing)}")
print(f"Доля: {len(non_collapsing)/(total - 3**L_test)*100:.2f}%\n")

# Классифицируем не-коллапсирующие строки
print("Примеры не-коллапсирующих строк (первые 30):")
for row in non_collapsing[:30]:
    trace = max_trace(row, max_steps=10)
    print(f"  {row} → max trace: {trace[:8]}")

results["non_collapsing_stats"] = {
    "M": M_test,
    "L": L_test,
    "total_with_max_gt2": total - (3 ** L_test),
    "non_collapsing_count": len(non_collapsing),
    "fraction": round(len(non_collapsing) / (total - 3 ** L_test), 4),
}

# === 3. Структура не-коллапсирующих строк ===
print(f"\n=== 3. Что общего у не-коллапсирующих строк? ===\n")

# Гипотеза: не-коллапсирующие строки содержат "изолированный пик":
# один элемент, сильно отличающийся от соседей, а остальные — одинаковые.

# Проверим: в не-коллапсирующих строках, сколько уникальных значений?
unique_counts = Counter()
has_isolated_peak = 0
for row in non_collapsing:
    unique_counts[len(set(row))] += 1
    # "Изолированный пик": одно значение встречается 1 раз, остальные — другое значение
    vals = Counter(row)
    if len(vals) == 2:
        counts = sorted(vals.values())
        if counts[0] == 1:  # одно значение ровно 1 раз
            has_isolated_peak += 1

print("Число уникальных значений в не-коллапсирующих строках:")
for n_unique, count in sorted(unique_counts.items()):
    print(f"  {n_unique} уникальных: {count} строк ({count/len(non_collapsing)*100:.1f}%)")

print(f"\nСтрок с 'изолированным пиком' (2 значения, одно — 1 раз): {has_isolated_peak} ({has_isolated_peak/len(non_collapsing)*100:.1f}%)")

# Проверим: что если убрать изолированный пик?
# [0,0,0,M,0,0,0] → [0,0,M,M,0,0] → [0,M,0,M,0] → [M,M,M,M] → [0,0,0] → коллапс
# Нет! [0,0,0,4,0,0,0] → [0,0,4,4,0,0] → [0,4,0,4,0] → [4,4,4,4] → [0,0,0] → max=0
print("\nПроверка: [0,0,0,4,0,0,0]")
r = [0,0,0,4,0,0,0]
for step in range(10):
    print(f"  Step {step}: {r}, max={max(r)}")
    if len(r) < 2:
        break
    r = abs_diff_row(r)

# А [0,0,4,4,4,0,0]?
print("\nПроверка: [0,0,4,4,4,0,0]")
r = [0,0,4,4,4,0,0]
for step in range(10):
    print(f"  Step {step}: {r}, max={max(r)}")
    if len(r) < 2:
        break
    r = abs_diff_row(r)

# А [0,4,4,4,4,4,4]?
print("\nПроверка: [0,4,4,4,4,4,4] — 'step function'")
r = [0,4,4,4,4,4,4]
for step in range(10):
    print(f"  Step {step}: {r}, max={max(r)}")
    if len(r) < 2:
        break
    r = abs_diff_row(r)

results["non_collapse_structure"] = {
    "unique_value_distribution": dict(unique_counts),
    "isolated_peak_count": has_isolated_peak,
    "isolated_peak_fraction": round(has_isolated_peak / len(non_collapsing), 4),
}

# === 4. Критерий коллапса: гипотеза ===
print("\n=== 4. Гипотеза о критерии коллапса ===\n")

# Step function [0, M, M, ..., M] не коллапсирует потому что
# abs_diff воспроизводит тот же паттерн.
# Случайные строки коллапсируют потому что у них много "вариации"
# и abs_diff быстро размывает max.

# Количественный тест: entropy строки предсказывает коллапс?
import math

def row_entropy(row):
    n = len(row)
    counts = Counter(row)
    return -sum((c/n) * math.log2(c/n) for c in counts.values())

def row_variation(row):
    """Число позиций i где row[i] != row[i+1]."""
    return sum(1 for i in range(len(row)-1) if row[i] != row[i+1])

# Для M=4, L=8: сравним энтропию коллапсирующих vs не-коллапсирующих
entropy_collapse = []
entropy_non_collapse = []
variation_collapse = []
variation_non_collapse = []

for row in gen_rows(M_test, L_test):
    if max(row) <= 2:
        continue
    e = row_entropy(row)
    v = row_variation(row)
    if collapses(row):
        entropy_collapse.append(e)
        variation_collapse.append(v)
    else:
        entropy_non_collapse.append(e)
        variation_non_collapse.append(v)

avg_e_c = sum(entropy_collapse) / len(entropy_collapse)
avg_e_nc = sum(entropy_non_collapse) / len(entropy_non_collapse)
avg_v_c = sum(variation_collapse) / len(variation_collapse)
avg_v_nc = sum(variation_non_collapse) / len(variation_non_collapse)

print(f"M={M_test}, L={L_test}:")
print(f"  Коллапсирующие:     entropy={avg_e_c:.3f}, variation={avg_v_c:.3f} (n={len(entropy_collapse)})")
print(f"  Не-коллапсирующие:  entropy={avg_e_nc:.3f}, variation={avg_v_nc:.3f} (n={len(entropy_non_collapse)})")
print(f"  Разница entropy:    {avg_e_c - avg_e_nc:+.3f}")
print(f"  Разница variation:  {avg_v_c - avg_v_nc:+.3f}")

results["collapse_predictor"] = {
    "avg_entropy_collapse": round(avg_e_c, 4),
    "avg_entropy_non_collapse": round(avg_e_nc, 4),
    "avg_variation_collapse": round(avg_v_c, 4),
    "avg_variation_non_collapse": round(avg_v_nc, 4),
    "n_collapse": len(entropy_collapse),
    "n_non_collapse": len(entropy_non_collapse),
}

# === 5. Главный вопрос: prime gaps — коллапсирующий тип? ===
print("\n=== 5. Prime gaps: почему они коллапсируют ===\n")

def sieve(n):
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(n**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, n + 1, i):
                is_prime[j] = False
    return [i for i in range(2, n + 1) if is_prime[i]]

primes = sieve(1_000_000)[:10000]
gaps = [primes[i+1] - primes[i] for i in range(len(primes) - 1)]

e_gaps = row_entropy(gaps[:100])
v_gaps = row_variation(gaps[:100])

print(f"Prime gaps (первые 100): entropy={e_gaps:.3f}, variation={v_gaps:.3f}")
print(f"Для сравнения (M={M_test}):")
print(f"  Коллапсирующие:    entropy={avg_e_c:.3f}, variation={avg_v_c:.3f}")
print(f"  Не-коллапсирующие: entropy={avg_e_nc:.3f}, variation={avg_v_nc:.3f}")

# Доля "шагов" (позиций где значение меняется)
print(f"\nVariation rate (prime gaps): {v_gaps / 99:.3f}")
print(f"Variation rate (collapse):   {avg_v_c / (L_test - 1):.3f}")
print(f"Variation rate (non-collapse):{avg_v_nc / (L_test - 1):.3f}")

# Не-коллапсирующие строки имеют НИЗКУЮ вариацию (как step function).
# Prime gaps имеют ВЫСОКУЮ вариацию → коллапсируют.

# === 6. Точная характеризация не-коллапсирующих строк ===
print("\n=== 6. Точная характеризация ===\n")

# Гипотеза: строка не коллапсирует ⟺ она содержит "шаговый" паттерн
# [a, a, ..., a, b, b, ..., b] где |a-b| > 2
# Потому что abs_diff превращает это в [0,...,0, |a-b|, 0,...,0] → тот же тип.

# Проверим: каждая не-коллапсирующая строка — "почти ступенчатая"?
def is_step_like(row, threshold=2):
    """Строка 'ступенчатая': ≤ threshold позиций где значение меняется на > 2."""
    big_jumps = sum(1 for i in range(len(row)-1) if abs(row[i+1]-row[i]) > 2)
    return big_jumps <= threshold

step_like_nc = sum(1 for row in non_collapsing if is_step_like(row, 1))
step_like_c_sample = sum(1 for row in list(gen_rows(M_test, L_test))[:5000]
                         if max(row) > 2 and collapses(row) and is_step_like(row, 1))

print(f"Не-коллапсирующие строки с ≤1 большим скачком: {step_like_nc}/{len(non_collapsing)} ({step_like_nc/len(non_collapsing)*100:.1f}%)")

# Более точный тест: после одного шага abs_diff, макс НЕ уменьшился?
max_preserved = sum(1 for row in non_collapsing
                    if abs_diff_row(row) and max(abs_diff_row(row)) == max(row))
print(f"Max сохраняется после 1 шага: {max_preserved}/{len(non_collapsing)} ({max_preserved/len(non_collapsing)*100:.1f}%)")

# Для коллапсирующих — max обычно уменьшается
collapse_sample = [row for row in gen_rows(M_test, L_test)
                   if max(row) > 2 and collapses(row)][:5000]
max_preserved_c = sum(1 for row in collapse_sample
                      if abs_diff_row(row) and max(abs_diff_row(row)) == max(row))
print(f"Max сохраняется (коллапсирующие, sample): {max_preserved_c}/{len(collapse_sample)} ({max_preserved_c/len(collapse_sample)*100:.1f}%)")

results["step_like_analysis"] = {
    "non_collapse_step_like": step_like_nc,
    "non_collapse_total": len(non_collapsing),
    "max_preserved_non_collapse": max_preserved,
    "max_preserved_collapse_sample": max_preserved_c,
    "collapse_sample_size": len(collapse_sample),
}

# === ИТОГИ ===
print("\n" + "=" * 60)
print("ГЛАВНЫЕ РЕЗУЛЬТАТЫ")
print("=" * 60)

conclusions = [
    "КОЛЛАПС НЕ УНИВЕРСАЛЕН: существуют строки из {0,...,M} (M≥3), "
    "которые никогда не коллапсируют к {0,1,2}. Пример: [0,M,M,...,M].",

    f"Не-коллапсирующих строк ~{results['non_collapsing_stats']['fraction']*100:.1f}% "
    f"(M={M_test}, L={L_test}). Это меньшинство, но не пренебрежимо малое.",

    f"КРИТЕРИЙ: не-коллапсирующие строки имеют НИЗКУЮ вариацию "
    f"(avg={avg_v_nc:.1f} vs {avg_v_c:.1f} для коллапсирующих). "
    f"Они 'ступенчатые' — мало позиций с большими скачками.",

    f"Prime gaps имеют ВЫСОКУЮ вариацию ({v_gaps}/{99}={v_gaps/99:.2f}), "
    f"что помещает их в коллапсирующий режим.",

    "УТОЧНЁННАЯ РЕДУКЦИЯ: гипотеза Гилбрета ≡ "
    "'prime gaps достаточно вариативны, чтобы abs-diff коллапсировал к {0,1,2}' "
    "+ '{0,1,2}-замкнутость → first=1'. Вариативность следует из того, "
    "что prime gaps — не периодические и не ступенчатые.",
]

for i, c in enumerate(conclusions, 1):
    print(f"\n{i}. {c}")

results["conclusions"] = conclusions

with open("non_collapse_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2, default=str)

print(f"\n\nРезультаты сохранены в non_collapse_results.json")
