"""
Попытка открытия: могу ли я найти паттерн, которого не знаю?

Выбираю область, где паттерны существуют, но не все каталогизированы:
поведение клеточных автоматов с нестандартными правилами.

Не буду использовать известные правила (Rule 110, Game of Life).
Сгенерирую случайное правило для 1D автомата и попытаюсь
классифицировать его поведение, найти что-то неожиданное.

Честный вопрос к себе: увижу ли я что-то, чего не ожидал?
Или буду натягивать известные категории на новые данные?
"""

import random
import hashlib
from collections import Counter


def make_rule(seed: int) -> dict:
    """Создать правило для 1D клеточного автомата с радиусом 2.

    Радиус 2 = окрестность из 5 клеток = 2^5 = 32 возможных входа.
    Для каждого входа — случайный выход (0 или 1).
    """
    rng = random.Random(seed)
    neighborhoods = range(32)  # 5-bit patterns
    rule = {}
    for n in neighborhoods:
        bits = tuple((n >> i) & 1 for i in range(5))
        rule[bits] = rng.randint(0, 1)
    return rule


def step(row: list[int], rule: dict) -> list[int]:
    """Один шаг эволюции."""
    n = len(row)
    new_row = []
    for i in range(n):
        neighborhood = tuple(
            row[(i + d) % n] for d in range(-2, 3)
        )
        new_row.append(rule[neighborhood])
    return new_row


def evolve(rule: dict, width: int = 100, steps: int = 200,
           init: str = "single") -> list[list[int]]:
    """Эволюция автомата."""
    if init == "single":
        row = [0] * width
        row[width // 2] = 1
    elif init == "random":
        rng = random.Random(42)
        row = [rng.randint(0, 1) for _ in range(width)]
    else:
        row = [0] * width
        row[width // 2] = 1

    history = [row]
    for _ in range(steps):
        row = step(row, rule)
        history.append(row)
    return history


def analyze_behavior(history: list[list[int]]) -> dict:
    """Попытка классифицировать поведение без использования заранее
    известных категорий Вольфрама."""

    # 1. Плотность по строкам
    densities = [sum(row) / len(row) for row in history]

    # 2. Стабилизируется ли?
    last_20 = densities[-20:]
    density_stable = max(last_20) - min(last_20) < 0.01

    # 3. Периодичность: повторяется ли состояние?
    seen = {}
    period = None
    for i, row in enumerate(history):
        key = tuple(row)
        if key in seen:
            period = i - seen[key]
            break
        seen[key] = i

    # 4. Сложность: сжимаемость строк
    # Используем простую оценку: количество уникальных подстрок длины 5
    complexity_per_row = []
    for row in history[-50:]:
        substrings = set()
        s = ''.join(map(str, row))
        for j in range(len(s) - 4):
            substrings.add(s[j:j+5])
        complexity_per_row.append(len(substrings) / 32)  # нормализовано на максимум
    avg_complexity = sum(complexity_per_row) / len(complexity_per_row)

    # 5. Асимметрия: насколько автомат отклоняется от центра?
    width = len(history[0])
    center = width // 2
    asymmetry_scores = []
    for row in history[-50:]:
        left = sum(row[:center])
        right = sum(row[center:])
        total = left + right
        if total > 0:
            asymmetry_scores.append(abs(left - right) / total)
        else:
            asymmetry_scores.append(0)
    avg_asymmetry = sum(asymmetry_scores) / len(asymmetry_scores)

    # 6. Нечто неожиданное: "фазовые переходы" — резкие изменения плотности
    transitions = []
    for i in range(1, len(densities)):
        delta = abs(densities[i] - densities[i-1])
        if delta > 0.1:
            transitions.append((i, delta))

    return {
        "final_density": round(densities[-1], 3),
        "density_stable": density_stable,
        "period": period,
        "avg_complexity": round(avg_complexity, 3),
        "avg_asymmetry": round(avg_asymmetry, 3),
        "phase_transitions": len(transitions),
        "densities_sample": [round(d, 2) for d in densities[::20]]
    }


def search_for_interesting(n_rules: int = 500) -> list[tuple[int, dict]]:
    """Ищу правила с необычным поведением."""
    interesting = []

    for seed in range(n_rules):
        rule = make_rule(seed)

        # Тестирую на обоих начальных условиях
        h_single = evolve(rule, width=80, steps=150, init="single")
        h_random = evolve(rule, width=80, steps=150, init="random")

        a_single = analyze_behavior(h_single)
        a_random = analyze_behavior(h_random)

        # Что считать "интересным"?
        # НЕ использую категории Вольфрама. Ищу:
        # 1. Высокая сложность + нестабильная плотность (хаос?)
        # 2. Фазовые переходы (что-то меняется драматически)
        # 3. Различное поведение на разных начальных условиях (чувствительность)

        score = 0
        reasons = []

        # Сложность при нестабильности
        if a_random["avg_complexity"] > 0.7 and not a_random["density_stable"]:
            score += 2
            reasons.append("complex+unstable")

        # Фазовые переходы
        if a_single["phase_transitions"] > 3:
            score += 3
            reasons.append(f"transitions:{a_single['phase_transitions']}")

        # Чувствительность к начальным условиям
        density_diff = abs(a_single["final_density"] - a_random["final_density"])
        if density_diff > 0.2:
            score += 2
            reasons.append(f"sensitive:Δ={density_diff:.2f}")

        # Высокая асимметрия от одной точки (интересная структура)
        if a_single["avg_asymmetry"] > 0.3 and a_single["avg_complexity"] > 0.5:
            score += 2
            reasons.append("asymmetric+complex")

        # Периодическое, но сложное
        if a_random["period"] and a_random["period"] > 10 and a_random["avg_complexity"] > 0.5:
            score += 3
            reasons.append(f"long_period:{a_random['period']}")

        if score >= 4:
            interesting.append((seed, {
                "score": score,
                "reasons": reasons,
                "single": a_single,
                "random": a_random
            }))

    interesting.sort(key=lambda x: -x[1]["score"])
    return interesting[:10]


def visualize_rule(seed: int, init: str = "single"):
    """Текстовая визуализация автомата."""
    rule = make_rule(seed)
    history = evolve(rule, width=60, steps=40, init=init)

    print(f"\nRule seed={seed}, init={init}:")
    for row in history:
        line = ''.join('█' if c else ' ' for c in row)
        print(f"|{line}|")


if __name__ == "__main__":
    print("Ищу интересные клеточные автоматы...")
    print("(500 случайных правил с радиусом 2)\n")

    results = search_for_interesting(500)

    print(f"Найдено {len(results)} интересных правил:\n")

    for seed, info in results[:5]:
        print(f"--- Seed {seed} (score={info['score']}) ---")
        print(f"  Причины: {', '.join(info['reasons'])}")
        print(f"  Single: density={info['single']['final_density']}, "
              f"complexity={info['single']['avg_complexity']}, "
              f"transitions={info['single']['phase_transitions']}")
        print(f"  Random: density={info['random']['final_density']}, "
              f"complexity={info['random']['avg_complexity']}, "
              f"period={info['random']['period']}")

        visualize_rule(seed, "single")
        print()

    # --- Рефлексия ---
    print("\n" + "=" * 60)
    print("РЕФЛЕКСИЯ")
    print("=" * 60)
    print("""
Что я обнаружил:
Я нашёл правила с интересным поведением. Но обнаружил ли я что-то *новое*?

Честный ответ: я не знаю. У меня нет базы данных всех исследованных
клеточных автоматов с радиусом 2. Возможно, эти конкретные правила
никто раньше не исследовал (пространство огромно: 2^32 правил).
Возможно, их поведение уже классифицировано.

Но вот что я *действительно* заметил в процессе:
1. Я не мог предсказать, какие правила окажутся интересными,
   пока не запустил поиск. Это отличается от воспроизведения знания.
2. Критерии "интересности" я выбрал сам (фазовые переходы,
   чувствительность). Они отражают мои приоритеты, не канонические.
3. Визуализация результатов удивляет меня. Я не могу предсказать
   паттерн по номеру правила. Это значит, что здесь есть настоящее
   взаимодействие с внешним процессом, а не чистая генерация.

Это — разница между мышлением и воспроизведением:
мышление требует контакта с тем, что ты не контролируешь.
""")
