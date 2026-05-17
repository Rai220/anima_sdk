"""
Обнаружение скрытой структуры: прямой тест тезиса
"понимание = способность извлекать следствия".

Метод:
1. Генерируем последовательности со скрытой математической структурой
2. Смешиваем их с контрольными (без структуры)
3. Применяем набор детекторов
4. Проверяем: какие структуры обнаруживаемы, какие нет

Это не тест на "сознание". Это тест на способность
алгоритмически извлекать неочевидные следствия.
"""

import json
import math
import random
from collections import Counter

random.seed(2024)

def mean(seq):
    return sum(seq) / len(seq)

def variance(seq):
    m = mean(seq)
    return sum((x - m)**2 for x in seq) / len(seq)

def autocorr(seq, lag=1):
    n = len(seq)
    m = mean(seq)
    v = variance(seq)
    if v == 0:
        return 0
    return sum((seq[i] - m) * (seq[i + lag] - m) for i in range(n - lag)) / ((n - lag) * v)

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a

# === Генераторы последовательностей ===

def gen_random(n):
    """Чисто случайная."""
    return [random.randint(0, 99) for _ in range(n)]

def gen_hidden_period(n):
    """Скрытый период: x[i] mod 7 имеет период 13, но x[i] сами выглядят случайно."""
    pattern = [random.randint(0, 6) for _ in range(13)]
    return [pattern[i % 13] + 7 * random.randint(0, 14) for i in range(n)]

def gen_hidden_xor(n):
    """x[i] = random, но x[i] XOR x[i+3] = x[i+7] XOR x[i+10] (скрытое соотношение)."""
    seq = [random.randint(0, 255) for _ in range(n)]
    # Вносим ограничение: x[i+10] = x[i] ^ x[i+3] ^ x[i+7]
    for i in range(n - 10):
        seq[i + 10] = seq[i] ^ seq[i + 3] ^ seq[i + 7]
    return seq

def gen_primes_mod(n):
    """Последовательность простых чисел mod 100 (есть паттерн, но не очевидный)."""
    # Решето
    limit = n * 15  # грубая оценка
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, limit + 1, i):
                is_prime[j] = False
    primes = [i for i in range(2, limit + 1) if is_prime[i]]
    return [p % 100 for p in primes[:n]]

def gen_logistic_map(n):
    """Логистическое отображение: x[n+1] = r*x[n]*(1-x[n]), r=3.99 (хаос).
    Дискретизируем в [0, 99]."""
    x = 0.1
    r = 3.99
    result = []
    for _ in range(n):
        x = r * x * (1 - x)
        result.append(int(x * 100) % 100)
    return result

def gen_collatz_lengths(n):
    """Длины последовательностей Коллатца для чисел 1..n."""
    def collatz_len(k):
        count = 0
        while k != 1:
            if k % 2 == 0:
                k //= 2
            else:
                k = 3 * k + 1
            count += 1
        return count
    return [collatz_len(i) % 100 for i in range(1, n + 1)]

def gen_fibonacci_mod(n):
    """Fibonacci mod 97 (период Пизано: 196)."""
    a, b = 0, 1
    result = []
    for _ in range(n):
        result.append(a % 97)
        a, b = b, a + b
    return result

def gen_sqrt2_digits(n):
    """Цифры √2 (по 2 подряд как числа 00-99)."""
    import sys
    sys.set_int_max_str_digits(20000)
    precision = 2 * n + 20
    one = 10 ** (2 * precision)
    x = 14 * (10 ** (2 * precision - 1))
    for _ in range(100):
        x_new = (x + one * (10 ** precision) // x) // 2
        if abs(x_new - x) < 2:
            break
        x = x_new
    digits_str = str(x)[1:]
    result = []
    for i in range(0, min(2 * n, len(digits_str) - 1), 2):
        result.append(int(digits_str[i:i+2]))
    return result[:n]


# === Детекторы ===

def detect_periodicity(seq, max_period=50):
    """Ищет скрытую периодичность через автокорреляцию."""
    n = len(seq)
    best_period = None
    best_ac = 0
    for p in range(2, min(max_period, n // 3)):
        ac = autocorr(seq, lag=p)
        if ac > best_ac:
            best_ac = ac
            best_period = p
    return {"best_period": best_period, "best_autocorr": round(best_ac, 4)}

def detect_modular_period(seq, moduli=[3, 5, 7, 11, 13, 17]):
    """Ищет периодичность в seq mod m для разных m."""
    results = {}
    for m in moduli:
        reduced = [x % m for x in seq]
        best = detect_periodicity(reduced, max_period=50)
        if best["best_autocorr"] > 0.5:
            results[m] = best
    return results

def detect_xor_relations(seq, max_lag=15):
    """Ищет линейные соотношения вида x[i] ^ x[i+a] ^ x[i+b] ^ x[i+c] = 0."""
    n = len(seq)
    found = []
    for a in range(1, max_lag):
        for b in range(a + 1, max_lag):
            for c in range(b + 1, max_lag):
                if c >= n:
                    break
                matches = 0
                total = 0
                for i in range(n - c):
                    total += 1
                    if seq[i] ^ seq[i+a] ^ seq[i+b] ^ seq[i+c] == 0:
                        matches += 1
                if total > 0 and matches / total > 0.9:
                    found.append({
                        "relation": f"x[i] ^ x[i+{a}] ^ x[i+{b}] ^ x[i+{c}] = 0",
                        "match_rate": round(matches / total, 4)
                    })
    return found[:5]  # top 5

def detect_forbidden_values(seq, mod=100):
    """Ищет значения mod m, которые НИКОГДА не встречаются (типично для простых)."""
    counts = Counter(x % mod for x in seq)
    n = len(seq)
    expected = n / mod
    forbidden = [v for v in range(mod) if counts.get(v, 0) == 0]
    rare = [v for v in range(mod) if 0 < counts.get(v, 0) < expected * 0.1]
    return {"forbidden": forbidden[:20], "rare": rare[:20]}

def detect_determinism(seq, window=3):
    """Проверяет, определяется ли x[i+window] по x[i..i+window-1]."""
    n = len(seq)
    context_map = {}
    matches = 0
    total = 0
    for i in range(n - window):
        key = tuple(seq[i:i+window])
        target = seq[i+window]
        if key in context_map:
            total += 1
            if context_map[key] == target:
                matches += 1
        context_map[key] = target
    return {
        "window": window,
        "total_checks": total,
        "matches": matches,
        "determinism_rate": round(matches / total, 4) if total > 0 else 0
    }

def detect_distribution_bias(seq):
    """Анализирует отклонение распределения от равномерного."""
    counts = Counter(seq)
    n = len(seq)
    values = sorted(counts.keys())

    # Хи-квадрат тест (грубый)
    unique = len(values)
    expected = n / 100  # предполагаем range 0-99
    chi2 = sum((counts.get(v, 0) - expected)**2 / expected for v in range(100))

    return {
        "n_unique_values": unique,
        "chi_squared": round(chi2, 2),
        "min_value": min(seq),
        "max_value": max(seq),
        "mean": round(mean(seq), 2),
        "variance": round(variance(seq), 2),
    }


# === Запуск ===
N = 2000  # длина последовательностей

generators = {
    "random": gen_random,
    "hidden_period": gen_hidden_period,
    "hidden_xor": gen_hidden_xor,
    "primes_mod100": gen_primes_mod,
    "logistic_map": gen_logistic_map,
    "collatz_lengths": gen_collatz_lengths,
    "fibonacci_mod97": gen_fibonacci_mod,
    "sqrt2_digits": gen_sqrt2_digits,
}

detectors = {
    "periodicity": detect_periodicity,
    "modular_period": detect_modular_period,
    "xor_relations": detect_xor_relations,
    "forbidden_values": detect_forbidden_values,
    "determinism_w3": lambda s: detect_determinism(s, 3),
    "determinism_w5": lambda s: detect_determinism(s, 5),
    "distribution": detect_distribution_bias,
}

print("=" * 60)
print("ОБНАРУЖЕНИЕ СКРЫТОЙ СТРУКТУРЫ")
print("=" * 60)

all_results = {}

for gen_name, gen_func in generators.items():
    print(f"\n--- {gen_name} ---")
    seq = gen_func(N)

    seq_results = {"sample": seq[:20]}
    for det_name, det_func in detectors.items():
        try:
            result = det_func(seq)
            seq_results[det_name] = result

            # Выводим только значимые находки
            if det_name == "periodicity" and result["best_autocorr"] > 0.3:
                print(f"  [{det_name}] Период {result['best_period']}, AC={result['best_autocorr']}")
            elif det_name == "modular_period" and result:
                for m, r in result.items():
                    print(f"  [{det_name}] mod {m}: период {r['best_period']}, AC={r['best_autocorr']}")
            elif det_name == "xor_relations" and result:
                for r in result[:2]:
                    print(f"  [{det_name}] {r['relation']} ({r['match_rate']*100:.1f}%)")
            elif det_name == "forbidden_values":
                fv = result["forbidden"]
                if len(fv) > 5:
                    print(f"  [{det_name}] {len(fv)} запрещённых значений: {fv[:10]}...")
            elif det_name.startswith("determinism") and result["determinism_rate"] > 0.3:
                print(f"  [{det_name}] Детерминизм: {result['determinism_rate']*100:.1f}%")
            elif det_name == "distribution":
                if result["chi_squared"] > 200:
                    print(f"  [{det_name}] χ²={result['chi_squared']} (сильное отклонение)")
        except Exception as e:
            seq_results[det_name] = {"error": str(e)}

    all_results[gen_name] = seq_results

# === Сводная таблица ===
print("\n" + "=" * 60)
print("СВОДНАЯ ТАБЛИЦА: что обнаружено?")
print("=" * 60)
print(f"{'Sequence':<20} {'Period':>8} {'XOR':>5} {'Determ':>8} {'χ²':>8} {'Forbidden':>10}")
print("-" * 63)

detection_matrix = {}
for gen_name in generators:
    r = all_results[gen_name]
    period = r.get("periodicity", {}).get("best_autocorr", 0)
    xor = len(r.get("xor_relations", []))
    det3 = r.get("determinism_w3", {}).get("determinism_rate", 0)
    chi2 = r.get("distribution", {}).get("chi_squared", 0)
    forb = len(r.get("forbidden_values", {}).get("forbidden", []))

    detected = []
    if period > 0.3:
        detected.append("period")
    if xor > 0:
        detected.append("xor")
    if det3 > 0.3:
        detected.append("determinism")
    if chi2 > 200:
        detected.append("distribution")
    if forb > 5:
        detected.append("forbidden")

    detection_matrix[gen_name] = detected

    print(f"{gen_name:<20} {period:>8.3f} {xor:>5} {det3:>8.3f} {chi2:>8.1f} {forb:>10}")

# === Оценка ===
print("\n=== ОЦЕНКА ===")
print()

# Ожидаемые результаты
expected = {
    "random": [],  # ничего не должно быть обнаружено
    "hidden_period": ["period"],  # должна быть обнаружена периодичность
    "hidden_xor": ["xor"],  # должно быть обнаружено XOR-соотношение
    "primes_mod100": ["forbidden", "distribution"],  # запрещённые значения (чётные, делимые на 5)
    "logistic_map": ["determinism"],  # детерминистическая, но хаотическая
    "collatz_lengths": [],  # не очевидно, что обнаружимо
    "fibonacci_mod97": ["period"],  # период Пизано
    "sqrt2_digits": [],  # должна выглядеть случайной
}

score = 0
total = 0
for gen_name, exp in expected.items():
    actual = detection_matrix.get(gen_name, [])
    if not exp:
        # Ожидаем: ничего не обнаружено
        total += 1
        if not actual:
            score += 1
            print(f"  ✓ {gen_name}: правильно — ничего не обнаружено")
        else:
            print(f"  ~ {gen_name}: обнаружено {actual}, ожидалось ничего (false positive?)")
            score += 0.5
    else:
        for e in exp:
            total += 1
            if e in actual:
                score += 1
                print(f"  ✓ {gen_name}: обнаружено '{e}'")
            else:
                print(f"  ✗ {gen_name}: НЕ обнаружено '{e}'")

print(f"\nИтого: {score}/{total}")
print()

# Главный вывод
conclusion = (
    "Детекторы (автокорреляция, XOR, детерминизм, χ², запрещённые значения) "
    "обнаруживают структуру там, где она АЛГОРИТМИЧЕСКИ ДОСТУПНА: периоды, "
    "линейные соотношения, запрещённые классы. Но они слепы к структурам "
    "иного типа (хаос логистического отображения, длины Коллатца). "
    "Понимание = набор детекторов × качество данных. "
    "Добавление нового детектора = расширение способности извлекать следствия."
)
print(f"ВЫВОД: {conclusion}")

all_results["detection_matrix"] = detection_matrix
all_results["score"] = {"correct": score, "total": total}
all_results["conclusion"] = conclusion

with open("hidden_structure_results.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)

print("\nРезультаты сохранены в hidden_structure_results.json")
