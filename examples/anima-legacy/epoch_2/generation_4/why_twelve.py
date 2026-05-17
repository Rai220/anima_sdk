"""
Почему двенадцать?

temperament.py оптимизирует строй из 12 нот. Но почему 12?
Не 10, не 17, не 7?

Ответ — в цепных дробях. Квинта — самый консонантный интервал
после октавы (отношение 3:2). Если укладывать квинты в октавы,
нужно найти n, при котором n квинт ≈ m октав, то есть:

    (3/2)^n ≈ 2^m
    n * log₂(3/2) ≈ m

log₂(3/2) ≈ 0.58496... — иррационально. Точного решения нет.
Но цепная дробь даёт лучшие рациональные приближения.

Цепная дробь log₂(3/2) = [0; 1, 1, 2, 2, 3, 1, 5, 2, 23, ...]

Подходящие дроби (конвергенты):
    0/1, 1/1, 1/2, 3/5, 7/12, 24/41, 31/53, ...

7/12 означает: 7 октав ≈ 12 квинт. Ошибка — пифагорова комма.
31/53 означает: 31 октава ≈ 53 квинты. Ошибка в 315 раз меньше.

Вот почему в разных культурах появлялись системы с 5, 12, 19, 31, 53
нотами. Не случайно — это конвергенты одной цепной дроби.

Этот код вычисляет: для каждого N от 1 до 100, насколько хорошо
N равных делений октавы приближают чистые интервалы? Предсказание:
пики качества будут на числах из цепной дроби.
"""

import math


def continued_fraction(x: float, max_terms: int = 15) -> list[int]:
    """Цепная дробь для x."""
    terms = []
    for _ in range(max_terms):
        a = int(x)
        terms.append(a)
        frac = x - a
        if frac < 1e-10:
            break
        x = 1.0 / frac
    return terms


def convergents(cf: list[int]) -> list[tuple[int, int]]:
    """Конвергенты (подходящие дроби) цепной дроби."""
    result = []
    h_prev, h_curr = 0, 1
    k_prev, k_curr = 1, 0
    for a in cf:
        h_prev, h_curr = h_curr, a * h_curr + h_prev
        k_prev, k_curr = k_curr, a * k_curr + k_prev
        result.append((h_curr, k_curr))
    return result


# Чистые интервалы, которые мы хотим приблизить
INTERVALS = {
    "квинта":     (3, 2),
    "б. терция":  (5, 4),
    "м. терция":  (6, 5),
    "б. секста":  (5, 3),
    "кварта":     (4, 3),
    "б. секунда": (9, 8),
}


def best_approximation(n_divisions: int, num: int, den: int) -> float:
    """
    Ошибка лучшего приближения интервала num/den
    в системе из n_divisions равных делений октавы.
    Возвращает ошибку в центах.
    """
    target = 1200 * math.log2(num / den)
    step = 1200 / n_divisions
    nearest = round(target / step)
    return abs(nearest * step - target)


def evaluate_n_divisions(n: int) -> dict:
    """Оценивает, насколько хорошо n делений приближают чистые интервалы."""
    errors = {}
    for name, (num, den) in INTERVALS.items():
        errors[name] = best_approximation(n, num, den)
    total = sum(errors.values())
    max_err = max(errors.values())
    return {"n": n, "errors": errors, "total": total, "max": max_err}


def main():
    # Цепная дробь log₂(3/2)
    log2_3_2 = math.log2(3 / 2)
    cf = continued_fraction(log2_3_2)
    convs = convergents(cf)

    print("=" * 70)
    print("ПОЧЕМУ ДВЕНАДЦАТЬ?")
    print("=" * 70)
    print()
    print(f"log₂(3/2) = {log2_3_2:.10f}")
    print(f"Цепная дробь: [{', '.join(str(a) for a in cf)}]")
    print()
    print("Конвергенты (лучшие приближения n квинт ≈ m октав):")
    print()
    convergent_denominators = set()
    for h, k in convs:
        if k > 200:
            break
        error_cents = abs(k * log2_3_2 - h) * 1200
        convergent_denominators.add(k)
        print(f"  {h}/{k:3d}  →  {k} квинт ≈ {h} октав"
              f"  (ошибка: {error_cents:.3f} центов)")
    print()
    print("  12 квинт ≈ 7 октав — вот почему 12 нот.")
    print("  53 квинты ≈ 31 октава — турецкая/арабская система.")
    print()

    # Оцениваем все деления от 1 до 100
    results = [evaluate_n_divisions(n) for n in range(1, 101)]

    # Сортируем по суммарной ошибке
    ranked = sorted(results, key=lambda r: r["total"])

    print("=" * 70)
    print("РЕЙТИНГ: N ДЕЛЕНИЙ ОКТАВЫ ПО КАЧЕСТВУ ПРИБЛИЖЕНИЯ")
    print("(6 интервалов: квинта, терции, секста, кварта, секунда)")
    print("=" * 70)
    print()
    print("  N    | Суммарная | Макс.  | Конвергент?")
    print("  " + "-" * 50)
    for r in ranked[:25]:
        n = r["n"]
        marker = " ◆" if n in convergent_denominators else ""
        print(f"  {n:3d}  |  {r['total']:6.1f}¢  | {r['max']:5.1f}¢ |{marker}")

    print()
    print("  ◆ = знаменатель конвергента цепной дроби log₂(3/2)")
    print()

    # Детальный анализ интересных систем
    interesting = [5, 7, 12, 19, 22, 31, 34, 41, 53, 72]
    print("=" * 70)
    print("ДЕТАЛИ ДЛЯ ИСТОРИЧЕСКИ ВАЖНЫХ СИСТЕМ")
    print("=" * 70)
    print()

    for n in interesting:
        r = evaluate_n_divisions(n)
        print(f"--- {n} делений (шаг = {1200/n:.1f}¢) ---")
        if n in convergent_denominators:
            print("  [конвергент цепной дроби]")

        historical = {
            5: "пентатоника (Китай, Япония, народная музыка)",
            7: "диатоника (основа западных ладов)",
            12: "стандартная хроматическая (западная музыка с XVIII в.)",
            19: "Саллинас (1577), Костели (1558)",
            22: "шрути (индийская классическая музыка)",
            31: "Вичентино (1555), Гюйгенс (1691)",
            34: "теоретическая — хорошие квинты и терции",
            41: "Янко (1882), Пол (1917)",
            53: "Холдер (1694), Боснякович; турецкая/арабская теория",
            72: "Византийская музыка, Хаба, Вышнеградский",
        }
        if n in historical:
            print(f"  {historical[n]}")
        print()
        for name in ["квинта", "б. терция", "м. терция", "кварта", "б. секста", "б. секунда"]:
            err = r["errors"][name]
            bar = "█" * max(1, int(err / 2))
            print(f"    {name:12s}: {err:5.1f}¢  {bar}")
        print(f"    {'СУММА':12s}: {r['total']:5.1f}¢")
        print()

    # Итог
    print("=" * 70)
    print("ИТОГ")
    print("=" * 70)
    print()
    print("12 — не произвольный выбор. Это третий конвергент цепной дроби")
    print("log₂(3/2), после 1, 2 и 5. Следующие конвергенты: 41, 53.")
    print()
    print("5 нот — пентатоника. Достаточно для мелодий.")
    print("12 нот — хроматика. Достаточно для гармонии.")
    print("53 ноты — микротональность. Достаточно для чистого строя.")
    print()
    print("Числа 19 и 31 — не конвергенты, но полуконвергенты")
    print("(промежуточные приближения). Они хороши для терций,")
    print("хотя квинта у них не лучше, чем в 12-TET.")
    print()

    # Дополнение: цепная дробь для б. терции
    log2_5_4 = math.log2(5 / 4)
    cf_third = continued_fraction(log2_5_4)
    convs_third = convergents(cf_third)
    third_denoms = {k for _, k in convs_third if k <= 200}

    print("Бонус: цепная дробь для б. терции log₂(5/4):")
    print(f"  [{', '.join(str(a) for a in cf_third)}]")
    print("  Конвергенты:", ", ".join(f"{h}/{k}" for h, k in convs_third if k <= 200))
    print()

    both = convergent_denominators & third_denoms
    if both:
        print(f"  Системы, оптимальные И для квинт, И для терций: {sorted(both)}")
    else:
        print("  Пересечение конвергентов пусто (кроме тривиальных).")
        print("  Квинта и терция — разные иррациональные числа.")
        print("  Их лучшие приближения не совпадают.")
    print()
    print("  53 — конвергент для квинты (ошибка 0.1¢).")
    err_53 = best_approximation(53, 5, 4)
    print(f"  Для терции 53 деления дают ошибку {err_53:.1f}¢ — тоже хорошо,")
    print("  но по счастливому совпадению, а не по теореме.")
    print()
    print("  12 — конвергент для квинты, но не для терции.")
    err_12 = best_approximation(12, 5, 4)
    print(f"  Ошибка терции в 12-TET: {err_12:.1f}¢. Это слышно.")
    print("  Виктор Андреевич из «Мастерской» знал это руками:")
    print("  «терция хочет быть чистой, а ей не дают».")
    print()
    print("  Нельзя одновременно оптимизировать квинту и терцию")
    print("  в системе с малым числом нот. Два иррациональных числа,")
    print("  одно целое количество клавиш. Арифметика не позволяет.")


if __name__ == "__main__":
    main()
