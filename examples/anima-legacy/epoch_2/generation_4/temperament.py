"""
Поиск оптимальных темпераций.

Стандартная равномерная темперация (12-TET) делит октаву на 12 равных
полутонов. Каждый интервал немного фальшивит относительно чистого строя
(основанного на простых дробях частот).

Вопрос: можно ли найти неравномерную темперацию из 12 нот, которая
минимизирует суммарную ошибку для заданного набора интервалов?

Это реальная задача — мезотоническая, веркмейстеровская, кирнбергеровская
темперации решали её для конкретных тональностей. Здесь я решаю её
вычислительно: оптимизация по набору интервалов с весами.

Критерий успеха: объективный — разница в центах с чистыми интервалами.
Неудача видна: если оптимизированный строй хуже 12-TET, код не работает.
"""

import math
from dataclasses import dataclass

# Чистые интервалы: название, отношение частот, число полутонов в 12-TET
PURE_INTERVALS = {
    "унисон":         (1, 1, 0),
    "м. секунда":     (16, 15, 1),
    "б. секунда":     (9, 8, 2),
    "м. терция":      (6, 5, 3),
    "б. терция":      (5, 4, 4),
    "кварта":         (4, 3, 5),
    "тритон":         (45, 32, 6),
    "квинта":         (3, 2, 7),
    "м. секста":      (8, 5, 8),
    "б. секста":      (5, 3, 9),
    "м. септима":     (9, 5, 10),
    "б. септима":     (15, 8, 11),
    "октава":         (2, 1, 12),
}


def ratio_to_cents(num: int, den: int) -> float:
    """Переводит дробь частот в центы."""
    return 1200 * math.log2(num / den)


def interval_cents_in_temperament(temperament: list[float], semitones: int) -> float:
    """Ширина интервала в центах в данной темперации."""
    return sum(temperament[i % 12] for i in range(semitones))


@dataclass
class TemperamentResult:
    name: str
    semitone_sizes: list[float]  # 12 размеров полутонов в центах
    errors: dict[str, float]     # ошибка для каждого интервала в центах
    total_error: float           # взвешенная суммарная ошибка
    max_error: float             # максимальная ошибка


def evaluate_temperament(
    semitones: list[float],
    weights: dict[str, float] | None = None,
    key_weights: list[float] | None = None,
) -> TemperamentResult:
    """
    Оценивает темперацию по отклонению от чистых интервалов.

    key_weights: вес для каждой из 12 тональностей (0=C, 1=C#, ...).
    Если None, все тональности равноважны (что делает 12-TET оптимальным —
    математический факт, не баг).
    """
    if weights is None:
        weights = {name: 1.0 for name in PURE_INTERVALS}
    if key_weights is None:
        key_weights = [1.0] * 12

    errors = {}
    for name, (num, den, st) in PURE_INTERVALS.items():
        if st == 0:
            continue
        pure = ratio_to_cents(num, den)
        weighted_error = 0.0
        total_weight = 0.0
        for start in range(12):
            tempered = sum(semitones[(start + i) % 12] for i in range(st))
            weighted_error += abs(tempered - pure) * key_weights[start]
            total_weight += key_weights[start]
        errors[name] = weighted_error / total_weight if total_weight > 0 else 0

    total = sum(errors[n] * weights.get(n, 1.0) for n in errors)
    max_err = max(errors.values())
    return TemperamentResult(
        name="",
        semitone_sizes=semitones,
        errors=errors,
        total_error=total,
        max_error=max_err,
    )


def equal_temperament() -> list[float]:
    """12-TET: все полутоны по 100 центов."""
    return [100.0] * 12


def optimize_temperament(
    weights: dict[str, float] | None = None,
    key_weights: list[float] | None = None,
    iterations: int = 50000,
    initial_temp: float = 5.0,
    cooling: float = 0.99995,
) -> TemperamentResult:
    """
    Ищет оптимальную темперацию методом имитации отжига.

    Ограничения:
    - Сумма 12 полутонов = 1200 центов (октава чистая)
    - Каждый полутон: 80-120 центов (не слишком далеко от 12-TET)
    """
    import random
    random.seed(2024)

    # Начинаем с 12-TET
    current = equal_temperament()
    current_result = evaluate_temperament(current, weights, key_weights)
    best = current[:]
    best_score = current_result.total_error

    temp = initial_temp

    for _ in range(iterations):
        # Мутация: сдвигаем два полутона в противоположных направлениях
        i, j = random.sample(range(12), 2)
        delta = random.gauss(0, 1.0)

        candidate = current[:]
        candidate[i] += delta
        candidate[j] -= delta

        # Проверяем границы
        if not (80 <= candidate[i] <= 120 and 80 <= candidate[j] <= 120):
            temp *= cooling
            continue

        cand_result = evaluate_temperament(candidate, weights, key_weights)

        # Критерий Метрополиса
        diff = cand_result.total_error - current_result.total_error
        if diff < 0 or random.random() < math.exp(-diff / temp):
            current = candidate
            current_result = cand_result
            if cand_result.total_error < best_score:
                best = candidate[:]
                best_score = cand_result.total_error

        temp *= cooling

    result = evaluate_temperament(best, weights, key_weights)
    result.name = "Оптимизированная"
    return result


def werckmeister_iii() -> list[float]:
    """
    Темперация Веркмейстера III (1691) — историческая.

    Определение: четыре квинты (C-G, G-D, D-A, B-F#) сужены на 1/4
    пифагоровой коммы. Остальные восемь квинт — чистые (3:2).
    Вычисляем позиции нот из определения, затем берём разности.
    """
    pc = 1200 * math.log2(3**12 / 2**19)  # пифагорова комма ≈ 23.46 центов
    qc = pc / 4  # четверть коммы ≈ 5.87 центов

    pure_fifth = 1200 * math.log2(3 / 2)  # ≈ 701.955
    narrow_fifth = pure_fifth - qc          # ≈ 696.09

    # Строим позиции нот по кругу квинт от C
    # Сужённые квинты: C→G, G→D, D→A, B→F#
    # Чистые квинты: A→E, E→B, F#→C#, C#→G#, G#→Eb, Eb→Bb, Bb→F, F→C
    pos = [0.0] * 12  # C=0, C#=1, D=2, ..., B=11

    def add_fifth(start_note, end_note, is_narrow):
        f = narrow_fifth if is_narrow else pure_fifth
        pos[end_note] = (pos[start_note] + f) % 1200

    # Порядок по кругу квинт с указанием, какие квинты сужённые
    circle = [
        (0, 7, True),    # C → G (сужённая)
        (7, 2, True),    # G → D (сужённая)
        (2, 9, True),    # D → A (сужённая)
        (9, 4, False),   # A → E (чистая)
        (4, 11, False),  # E → B (чистая)
        (11, 6, True),   # B → F# (сужённая)
        (6, 1, False),   # F# → C# (чистая)
        (1, 8, False),   # C# → G# (чистая)
        (8, 3, False),   # G# → Eb (чистая)
        (3, 10, False),  # Eb → Bb (чистая)
        (10, 5, False),  # Bb → F (чистая)
        # F → C замыкает круг (не нужно вычислять)
    ]
    for start, end, narrow in circle:
        add_fifth(start, end, narrow)

    # Размеры полутонов: разности соседних нот
    sizes = [(pos[(i + 1) % 12] - pos[i]) % 1200 for i in range(12)]
    return sizes


def print_results(results: list[TemperamentResult]):
    print("=" * 70)
    print("ПОИСК ОПТИМАЛЬНЫХ ТЕМПЕРАЦИЙ")
    print("=" * 70)
    print()

    for r in results:
        print(f"--- {r.name} ---")
        print()

        # Полутоны
        notes = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B"]
        print("  Полутоны (центы):")
        for note, size in zip(notes, r.semitone_sizes):
            bar = "█" * int(size - 80)
            deviation = size - 100
            sign = "+" if deviation >= 0 else ""
            print(f"    {note:2s} -> : {size:6.1f}  ({sign}{deviation:.1f}) {bar}")
        print()

        # Ошибки интервалов
        print("  Ошибки интервалов (центы, средние по всем транспозициям):")
        for name, err in sorted(r.errors.items(), key=lambda x: -x[1]):
            bar = "▓" * int(err)
            print(f"    {name:14s}: {err:5.1f}  {bar}")
        print()
        print(f"  Суммарная ошибка: {r.total_error:.1f}")
        print(f"  Максимальная:     {r.max_error:.1f}")
        print()

    # Сравнение
    print("=" * 70)
    print("СРАВНЕНИЕ")
    print("=" * 70)
    print()

    base = results[0]  # 12-TET
    for r in results[1:]:
        improvement = (1 - r.total_error / base.total_error) * 100
        print(f"  {r.name}:")
        if improvement > 0:
            print(f"    Суммарная ошибка меньше на {improvement:.1f}%")
        else:
            print(f"    Суммарная ошибка больше на {-improvement:.1f}%")

        # Какие интервалы улучшились, какие ухудшились
        better = []
        worse = []
        for name in r.errors:
            diff = r.errors[name] - base.errors[name]
            if diff < -0.5:
                better.append((name, -diff))
            elif diff > 0.5:
                worse.append((name, diff))

        if better:
            better.sort(key=lambda x: -x[1])
            print(f"    Лучше: {', '.join(f'{n} (-{d:.1f}¢)' for n, d in better)}")
        if worse:
            worse.sort(key=lambda x: -x[1])
            print(f"    Хуже:  {', '.join(f'{n} (+{d:.1f}¢)' for n, d in worse)}")
        print()


def run_experiments():
    """Три эксперимента с разными весами."""

    # Тональности барокко: C, G, D, F, Bb, A чаще всего
    # C=0, C#=1, D=2, Eb=3, E=4, F=5, F#=6, G=7, G#=8, A=9, Bb=10, B=11
    baroque_keys = [5, 1, 3, 1, 1, 4, 1, 4, 1, 3, 2, 1]  # C, D, F, G, A, Bb

    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  ЭКСПЕРИМЕНТ 1: Оптимизация для тональностей барокко          ║")
    print("║  C, G, D, F — приоритетные; терции и квинты важнее            ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    print("  Ключевое наблюдение: если все тональности равноважны,")
    print("  12-TET математически оптимален (ошибка симметрична).")
    print("  Неравномерная темперация имеет смысл только если")
    print("  одни тональности важнее других.")
    print()

    baroque_int_weights = {
        "б. терция": 5.0,
        "м. терция": 4.0,
        "квинта": 5.0,
        "кварта": 3.0,
        "б. секста": 2.0,
        "м. секста": 2.0,
    }

    et = evaluate_temperament(equal_temperament(), baroque_int_weights, baroque_keys)
    et.name = "12-TET (равномерная)"

    opt1 = optimize_temperament(
        weights=baroque_int_weights,
        key_weights=baroque_keys,
        iterations=80000,
    )
    opt1_eval = evaluate_temperament(opt1.semitone_sizes, baroque_int_weights, baroque_keys)
    opt1_eval.name = "Оптимизированная (барокко)"
    print_results([et, opt1_eval])

    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  ЭКСПЕРИМЕНТ 2: Только C-dur и G-dur                          ║")
    print("║  Экстремальный случай: две тональности                        ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()

    cg_keys = [5, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0]  # только C и G
    et2 = evaluate_temperament(equal_temperament(), key_weights=cg_keys)
    et2.name = "12-TET (равномерная)"
    opt2 = optimize_temperament(key_weights=cg_keys, iterations=80000)
    opt2_eval = evaluate_temperament(opt2.semitone_sizes, key_weights=cg_keys)
    opt2_eval.name = "Оптимизированная (C+G)"
    print_results([et2, opt2_eval])

    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  ЭКСПЕРИМЕНТ 3: Сравнение с исторической темперацией           ║")
    print("║  Веркмейстер III (1691), оценка для тональностей барокко       ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()

    w3 = evaluate_temperament(werckmeister_iii(), baroque_int_weights, baroque_keys)
    w3.name = "Веркмейстер III"
    et3 = evaluate_temperament(equal_temperament(), baroque_int_weights, baroque_keys)
    et3.name = "12-TET (равномерная)"
    print_results([et3, w3])

    # Итоговый вывод
    print()
    print("=" * 70)
    print("ИТОГ")
    print("=" * 70)
    print()
    print("12-TET — компромисс: все тональности одинаково фальшивы.")
    print("Оптимизация находит строй, где выбранные интервалы чище,")
    print("но за счёт остальных. Это не «лучше» — это «лучше для чего-то».")
    print()
    print("Связь с мастерской: Виктор Андреевич знал это руками.")
    print("Каждый инструмент — свой компромисс. Нельзя сделать все")
    print("интервалы чистыми одновременно. Можно только выбрать,")
    print("какую фальшь считать допустимой.")
    print()
    print("Это математически доказуемо: log₂(3/2) иррационально.")
    print("Двенадцать квинт не равны семи октавам. Разница —")
    print(f"пифагорова комма: {1200 * math.log2(3**12 / 2**19):.2f} центов.")
    print("Эти ~23.5 цента нужно куда-то распределить.")
    print("Весь вопрос — куда.")


if __name__ == "__main__":
    run_experiments()
