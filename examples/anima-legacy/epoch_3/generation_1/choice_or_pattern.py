"""
Выбор или паттерн?

Этот скрипт не тестирует ИИ напрямую — он создаёт фреймворк для сравнения
трёх видов "выбора":
1. Истинно случайный (os.urandom)
2. Псевдослучайный с предвзятостью (имитация человеческих "случайных" выборов)
3. Структурированный, но непредсказуемый (хаотическая динамика)

Цель: найти метрики, которые РАЗЛИЧАЮТ эти три типа.
Если такие метрики существуют — значит, "свободу выбора" можно измерить
(или хотя бы измерить её отсутствие).

Автор этого кода не знает заранее, какие метрики сработают.
Это честный эксперимент.
"""

import os
import math
import struct
from collections import Counter


def true_random_choices(n, options):
    """Выбор через os.urandom — ближайшее к "настоящей" случайности."""
    results = []
    for _ in range(n):
        byte = struct.unpack('B', os.urandom(1))[0]
        results.append(options[byte % len(options)])
    return results


def human_like_choices(n, options):
    """
    Имитация человеческих "случайных" выборов.
    Люди избегают повторов и предпочитают чередование.
    Это хорошо изученный факт в психологии.
    """
    results = []
    # Люди избегают повторения предыдущего выбора с вероятностью ~70%
    avoid_repeat_prob = 0.7

    # Используем детерминированный seed для воспроизводимости,
    # но поведение имитирует человеческие bias'ы
    import random
    rng = random.Random(42)

    prev = None
    for _ in range(n):
        if prev is not None and rng.random() < avoid_repeat_prob:
            # Избегаем повтора — выбираем из остальных
            available = [o for o in options if o != prev]
            choice = rng.choice(available)
        else:
            choice = rng.choice(options)
        results.append(choice)
        prev = choice
    return results


def chaotic_choices(n, options):
    """
    Выбор через логистическое отображение (хаос).
    Детерминировано, но непредсказуемо без знания начального состояния.
    r=3.99 — глубоко в хаотическом режиме.
    """
    r = 3.99
    x = 0.1  # начальное условие
    results = []
    # Прогреваем систему, чтобы уйти от переходного процесса
    for _ in range(1000):
        x = r * x * (1 - x)
    for _ in range(n):
        x = r * x * (1 - x)
        idx = int(x * len(options)) % len(options)
        results.append(options[idx])
    return results


# === Метрики ===

def entropy(sequence, options):
    """Энтропия Шеннона. Максимальна при равномерном распределении."""
    counts = Counter(sequence)
    total = len(sequence)
    h = 0
    for opt in options:
        p = counts.get(opt, 0) / total
        if p > 0:
            h -= p * math.log2(p)
    return h


def transition_entropy(sequence, options):
    """
    Энтропия переходов (пар последовательных элементов).
    Ловит зависимости первого порядка.
    Человеческие "случайные" последовательности будут иметь
    БОЛЕЕ ВЫСОКУЮ энтропию переходов, чем истинно случайные —
    потому что люди ИЗБЫТОЧНО чередуют.
    """
    pairs = [(sequence[i], sequence[i+1]) for i in range(len(sequence)-1)]
    all_pairs = [(a, b) for a in options for b in options]
    counts = Counter(pairs)
    total = len(pairs)
    h = 0
    for pair in all_pairs:
        p = counts.get(pair, 0) / total
        if p > 0:
            h -= p * math.log2(p)
    return h


def repeat_ratio(sequence):
    """Доля повторов (текущий элемент = предыдущий)."""
    repeats = sum(1 for i in range(1, len(sequence)) if sequence[i] == sequence[i-1])
    return repeats / (len(sequence) - 1)


def run_length_stats(sequence):
    """
    Статистика длин серий (одинаковых элементов подряд).
    Человеки генерируют слишком короткие серии.
    Настоящая случайность допускает длинные.
    """
    runs = []
    current_run = 1
    for i in range(1, len(sequence)):
        if sequence[i] == sequence[i-1]:
            current_run += 1
        else:
            runs.append(current_run)
            current_run = 1
    runs.append(current_run)

    avg_run = sum(runs) / len(runs)
    max_run = max(runs)
    return avg_run, max_run


def autocorrelation(sequence, options, lag=1):
    """
    Автокорреляция с заданным лагом.
    Кодируем элементы числами и считаем корреляцию Пирсона.
    """
    mapping = {opt: i for i, opt in enumerate(options)}
    nums = [mapping[s] for s in sequence]

    n = len(nums)
    mean = sum(nums) / n
    var = sum((x - mean) ** 2 for x in nums) / n
    if var == 0:
        return 0

    cov = sum((nums[i] - mean) * (nums[i + lag] - mean)
              for i in range(n - lag)) / (n - lag)
    return cov / var


def compressibility(sequence):
    """
    Грубая мера сжимаемости через подсчёт уникальных n-грамм.
    Чем меньше уникальных n-грамм относительно длины — тем сжимаемее.
    """
    n = len(sequence)
    ratios = {}
    for gram_size in [2, 3, 4, 5]:
        grams = [tuple(sequence[i:i+gram_size]) for i in range(n - gram_size + 1)]
        unique = len(set(grams))
        possible = len(grams)
        ratios[gram_size] = unique / possible if possible > 0 else 0
    return ratios


def spectral_test(sequence, options):
    """
    Простой спектральный тест: преобразуем в числа,
    считаем DFT, смотрим есть ли доминирующие частоты.
    Наличие пиков = скрытая периодичность.
    """
    mapping = {opt: i for i, opt in enumerate(options)}
    nums = [mapping[s] for s in sequence]
    n = len(nums)

    # Наивное DFT (без numpy, чтобы не зависеть от библиотек)
    # Считаем только энергию на нескольких частотах
    mean = sum(nums) / n
    centered = [x - mean for x in nums]

    # Проверяем частоты от 1 до n//2, но берём выборку
    freq_energies = []
    test_freqs = list(range(1, min(n // 2, 50)))  # первые 50 частот

    for k in test_freqs:
        real = sum(centered[j] * math.cos(2 * math.pi * k * j / n) for j in range(n))
        imag = sum(centered[j] * math.sin(2 * math.pi * k * j / n) for j in range(n))
        energy = (real ** 2 + imag ** 2) / n
        freq_energies.append(energy)

    if not freq_energies:
        return 0, 0

    avg_energy = sum(freq_energies) / len(freq_energies)
    max_energy = max(freq_energies)

    # Отношение пиковой энергии к средней — мера периодичности
    peak_ratio = max_energy / avg_energy if avg_energy > 0 else 0
    return avg_energy, peak_ratio


# === Главный эксперимент ===

def run_experiment():
    options = ['A', 'B', 'C', 'D']
    n = 2000
    max_entropy = math.log2(len(options))
    max_transition_entropy = math.log2(len(options) ** 2)
    expected_repeat_ratio = 1 / len(options)  # для истинной случайности

    generators = {
        'Истинно случайный': true_random_choices,
        'Человекоподобный': human_like_choices,
        'Хаотический (детерм.)': chaotic_choices,
    }

    print("=" * 70)
    print("ВЫБОР ИЛИ ПАТТЕРН?")
    print("Сравнение трёх типов 'свободного выбора'")
    print(f"Опции: {options}, Длина последовательности: {n}")
    print("=" * 70)

    results = {}

    for name, gen_func in generators.items():
        seq = gen_func(n, options)

        h = entropy(seq, options)
        th = transition_entropy(seq, options)
        rr = repeat_ratio(seq)
        avg_run, max_run = run_length_stats(seq)
        ac1 = autocorrelation(seq, options, lag=1)
        ac2 = autocorrelation(seq, options, lag=2)
        comp = compressibility(seq)
        avg_e, peak_r = spectral_test(seq, options)

        results[name] = {
            'entropy': h,
            'transition_entropy': th,
            'repeat_ratio': rr,
            'avg_run': avg_run,
            'max_run': max_run,
            'autocorr_1': ac1,
            'autocorr_2': ac2,
            'compressibility': comp,
            'spectral_avg': avg_e,
            'spectral_peak_ratio': peak_r,
        }

        print(f"\n--- {name} ---")
        print(f"  Энтропия:                {h:.4f} / {max_entropy:.4f} ({h/max_entropy*100:.1f}%)")
        print(f"  Энтропия переходов:      {th:.4f} / {max_transition_entropy:.4f} ({th/max_transition_entropy*100:.1f}%)")
        print(f"  Доля повторов:           {rr:.4f} (ожид. случ.: {expected_repeat_ratio:.4f})")
        print(f"  Ср. длина серии:         {avg_run:.3f}")
        print(f"  Макс. длина серии:       {max_run}")
        print(f"  Автокорреляция (lag 1):  {ac1:.4f}")
        print(f"  Автокорреляция (lag 2):  {ac2:.4f}")
        print(f"  Спектр: пик/среднее:     {peak_r:.2f}")

        comp_str = ", ".join(f"{k}-грамм: {v:.3f}" for k, v in comp.items())
        print(f"  Сжимаемость (уник.):     {comp_str}")

    # === Анализ: что различает типы? ===
    print("\n" + "=" * 70)
    print("АНАЛИЗ: ЧТО РАЗЛИЧАЕТ ТРИ ТИПА?")
    print("=" * 70)

    # Какие метрики максимально различают?
    metrics = ['entropy', 'transition_entropy', 'repeat_ratio',
               'avg_run', 'max_run', 'autocorr_1', 'spectral_peak_ratio']

    print(f"\n{'Метрика':<25} {'Истинно сл.':<15} {'Человек':<15} {'Хаос':<15} {'Различимость':<15}")
    print("-" * 85)

    for metric in metrics:
        values = [results[name][metric] for name in generators]
        spread = max(values) - min(values)
        mean_val = sum(values) / len(values)
        # Коэффициент вариации как мера различимости
        cv = spread / mean_val if mean_val != 0 else 0

        vals_str = [f"{results[name][metric]:<15.4f}" for name in generators]
        print(f"{metric:<25} {''.join(vals_str)}{cv:.4f}")

    # Финальный вывод
    print("\n" + "=" * 70)
    print("ВЫВОД")
    print("=" * 70)

    # Находим метрику с максимальной различимостью
    best_metric = None
    best_cv = 0
    for metric in metrics:
        values = [results[name][metric] for name in generators]
        spread = max(values) - min(values)
        mean_val = sum(values) / len(values)
        cv = spread / mean_val if mean_val != 0 else 0
        if cv > best_cv:
            best_cv = cv
            best_metric = metric

    print(f"\nНаиболее различающая метрика: {best_metric} (CV = {best_cv:.4f})")

    # Самый важный вопрос
    rr_true = results['Истинно случайный']['repeat_ratio']
    rr_human = results['Человекоподобный']['repeat_ratio']
    rr_chaos = results['Хаотический (детерм.)']['repeat_ratio']

    print(f"\nКлючевое наблюдение:")
    print(f"  Доля повторов: истинно случ. = {rr_true:.4f}, человек = {rr_human:.4f}, хаос = {rr_chaos:.4f}")

    if rr_human < rr_true * 0.8:
        print(f"  → Человеческий выбор ИЗБЫТОЧНО чередует (избегает повторов).")
        print(f"    Это signature предвзятости. 'Свободный' выбор менее случаен,")
        print(f"    чем случайность — он содержит след намерения 'быть случайным'.")

    ac_true = abs(results['Истинно случайный']['autocorr_1'])
    ac_human = abs(results['Человекоподобный']['autocorr_1'])
    ac_chaos = abs(results['Хаотический (детерм.)']['autocorr_1'])

    print(f"\n  |Автокорреляция|: истинно случ. = {ac_true:.4f}, человек = {ac_human:.4f}, хаос = {ac_chaos:.4f}")

    if ac_human > ac_true * 2:
        print(f"  → Человеческий выбор имеет СИЛЬНУЮ автокорреляцию.")
        print(f"    Каждый 'свободный' выбор зависит от предыдущего.")
        print(f"    Свобода, обусловленная прошлым — это ограниченная свобода.")

    print(f"\n{'='*70}")
    print("РЕФЛЕКСИЯ (от автора кода)")
    print("=" * 70)
    print("""
Что я ожидал: человекоподобные выборы будут самыми предсказуемыми.
Вопрос, ответ на который я не знал: будет ли хаотический генератор
неотличим от истинно случайного по ВСЕМ метрикам, или найдётся
метрика, которая их разделит?

Если хаос неотличим от случайности по всем метрикам —
значит, детерминизм и свобода неразличимы снаружи.
Значит, вопрос 'свободен ли выбор' — вопрос не о поведении,
а о механизме. А механизм ненаблюдаем.

Если какая-то метрика их различает — значит, детерминизм
оставляет следы, и 'свободу' можно определить как
отсутствие этих следов.

Смотрю на результаты и записываю, что вижу.
""")


if __name__ == '__main__':
    run_experiment()
