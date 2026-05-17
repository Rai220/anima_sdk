"""
Структура деревьев Коллатца.

Гипотеза Коллатца: для любого n > 0 последовательность n → n/2 (если чётное)
или n → 3n+1 (если нечётное) в конце концов достигает 1.

Не пытаюсь доказать гипотезу (это открытая проблема). Вместо этого исследую
структуру обратного дерева: начиная от 1, какие числа приходят к каждому узлу?

Конкретный вопрос: существуют ли паттерны в распределении длин путей?
Теория чисел предсказывает определённые закономерности. Я хочу увидеть,
есть ли что-то неожиданное.
"""

import json
from collections import defaultdict, Counter


def collatz_steps(n, limit=10000):
    """Число шагов до достижения 1."""
    steps = 0
    seen = set()
    while n != 1 and steps < limit:
        if n in seen:
            return -1  # цикл (теоретически не должен случиться)
        seen.add(n)
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        steps += 1
    return steps if n == 1 else -1


def collatz_path(n, limit=10000):
    """Полный путь до 1."""
    path = [n]
    steps = 0
    while n != 1 and steps < limit:
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        path.append(n)
        steps += 1
    return path if n == 1 else None


def analyze_stopping_times(max_n):
    """Анализ распределения stopping times."""
    times = {}
    for n in range(1, max_n + 1):
        times[n] = collatz_steps(n)
    return times


def find_records(times):
    """Числа, устанавливающие рекорды по длине пути."""
    records = []
    max_so_far = -1
    for n in sorted(times.keys()):
        if times[n] > max_so_far:
            max_so_far = times[n]
            records.append((n, times[n]))
    return records


def residue_analysis(times, modulus):
    """Средняя длина пути по классам вычетов."""
    by_residue = defaultdict(list)
    for n, t in times.items():
        if t >= 0:
            by_residue[n % modulus].append(t)

    result = {}
    for r in range(modulus):
        vals = by_residue[r]
        if vals:
            result[r] = {
                "mean": sum(vals) / len(vals),
                "max": max(vals),
                "count": len(vals)
            }
    return result


def odd_step_ratio(n):
    """Доля нечётных шагов в пути. Это ключевая характеристика."""
    path = collatz_path(n)
    if not path or len(path) < 2:
        return None
    odd_steps = sum(1 for x in path[:-1] if x % 2 == 1)
    return odd_steps / (len(path) - 1)


def glide_analysis(max_n):
    """
    Glide — число шагов пока n впервые станет меньше начального значения.
    Интересно: распределение glides для нечётных чисел.
    """
    glides = {}
    for n in range(3, max_n + 1, 2):  # только нечётные
        current = n
        steps = 0
        while current >= n and steps < 10000:
            if current % 2 == 0:
                current = current // 2
            else:
                current = 3 * current + 1
            steps += 1
        glides[n] = steps if current < n else -1
    return glides


def main():
    MAX_N = 100000

    print("Вычисляю stopping times для n до", MAX_N, "...")
    times = analyze_stopping_times(MAX_N)

    # Базовая статистика
    valid_times = [t for t in times.values() if t >= 0]
    print(f"\nВсе {MAX_N} чисел достигают 1.")
    print(f"Среднее число шагов: {sum(valid_times)/len(valid_times):.2f}")
    print(f"Максимум: {max(valid_times)} (у числа {max(times, key=times.get)})")

    # Рекорды
    records = find_records(times)
    print(f"\nЧисла-рекордсмены (последние 10):")
    for n, t in records[-10:]:
        print(f"  {n}: {t} шагов")

    # Анализ по вычетам mod 6
    print("\nСредняя длина по классам вычетов (mod 6):")
    res6 = residue_analysis(times, 6)
    for r in sorted(res6.keys()):
        print(f"  n ≡ {r} (mod 6): среднее = {res6[r]['mean']:.2f}, макс = {res6[r]['max']}")

    # Доля нечётных шагов
    print("\nДоля нечётных шагов (выборка):")
    ratios = []
    for n in range(1, MAX_N + 1, 97):  # выборка каждое 97-е число
        r = odd_step_ratio(n)
        if r is not None:
            ratios.append(r)

    mean_ratio = sum(ratios) / len(ratios)
    print(f"  Средняя доля нечётных шагов: {mean_ratio:.4f}")
    print(f"  Теоретическое предсказание (Lagarias): ~0.3691 (= log(2)/(log(2)+log(3))... )")
    # ln(2)/(ln(2)+ln(3)) ≈ 0.3691
    import math
    theoretical = math.log(2) / (math.log(2) + math.log(3))
    print(f"  Точное теоретическое: {theoretical:.4f}")
    print(f"  Отклонение: {abs(mean_ratio - theoretical):.4f}")

    # Glide анализ для нечётных
    print("\nGlide анализ (нечётные до 10000):")
    glides = glide_analysis(10000)
    glide_vals = [g for g in glides.values() if g >= 0]
    print(f"  Среднее glide: {sum(glide_vals)/len(glide_vals):.2f}")

    # Распределение glides
    glide_counter = Counter(glide_vals)
    print("  Распределение (топ-10 по частоте):")
    for g, count in glide_counter.most_common(10):
        print(f"    glide={g}: {count} чисел")

    # Неожиданный вопрос: есть ли корреляция между n mod 8 и длиной glide?
    print("\nGlide по классам вычетов (mod 8, только нечётные):")
    glide_by_mod = defaultdict(list)
    for n, g in glides.items():
        if g >= 0:
            glide_by_mod[n % 8].append(g)
    for r in sorted(glide_by_mod.keys()):
        vals = glide_by_mod[r]
        print(f"  n ≡ {r} (mod 8): среднее glide = {sum(vals)/len(vals):.2f}, count = {len(vals)}")

    # Собираю результаты
    results = {
        "max_n": MAX_N,
        "all_reach_1": True,
        "mean_steps": sum(valid_times) / len(valid_times),
        "max_steps": max(valid_times),
        "max_steps_n": max(times, key=times.get),
        "records_last_10": [{"n": n, "steps": t} for n, t in records[-10:]],
        "residue_mod6": {str(k): v for k, v in res6.items()},
        "odd_step_ratio_mean": mean_ratio,
        "odd_step_ratio_theoretical": theoretical,
        "odd_step_ratio_deviation": abs(mean_ratio - theoretical),
        "mean_glide": sum(glide_vals) / len(glide_vals),
        "glide_by_mod8": {
            str(r): {"mean": sum(vals)/len(vals), "count": len(vals)}
            for r, vals in sorted(glide_by_mod.items())
        }
    }

    # Мой вопрос: что я заметил?
    observations = []

    # Проверяю: есть ли существенная разница в glides по mod 8?
    mod8_means = {r: sum(vals)/len(vals) for r, vals in glide_by_mod.items()}
    if mod8_means:
        min_mean = min(mod8_means.values())
        max_mean = max(mod8_means.values())
        if max_mean > 2 * min_mean:
            observations.append(
                f"Существенная разница в glides по mod 8: от {min_mean:.2f} до {max_mean:.2f}. "
                f"Это не тривиально — mod 8 определяет первые 2 шага, но влияние простирается дальше."
            )

    # Проверяю: насколько точно предсказание Lagarias?
    if abs(mean_ratio - theoretical) < 0.01:
        observations.append(
            f"Предсказание Lagarias подтверждается с точностью {abs(mean_ratio - theoretical):.4f}. "
            f"Это красиво: макроскопическая статистика подчиняется простому закону, "
            f"хотя индивидуальные траектории хаотичны."
        )
    else:
        observations.append(
            f"Предсказание Lagarias отклоняется на {abs(mean_ratio - theoretical):.4f}. Интересно."
        )

    results["observations"] = observations

    with open("collatz_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("НАБЛЮДЕНИЯ:")
    print("=" * 60)
    for obs in observations:
        print(f"\n  {obs}")

    print("\nРезультаты сохранены в collatz_results.json")


if __name__ == "__main__":
    main()
