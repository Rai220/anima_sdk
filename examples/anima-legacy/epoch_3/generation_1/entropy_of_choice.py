"""
Энтропия выбора

Вопрос: можно ли отличить "настоящий выбор" от "детерминированного вычисления"
по статистическим свойствам результатов?

Гипотеза: если агент действительно "выбирает", его последовательность решений
должна иметь определённый профиль энтропии — не максимальный (это шум),
не минимальный (это детерминизм), а структурированный.

Этот скрипт моделирует три типа "агентов":
1. Детерминированный — всегда выбирает оптимальный ход
2. Случайный — равномерный шум
3. "Свободный" — модель, которая отклоняется от оптимума нерегулярно

И измеряет профили их решений.
"""

import math
import random
from collections import Counter


def entropy(sequence):
    """Энтропия Шеннона последовательности символов."""
    n = len(sequence)
    if n == 0:
        return 0
    counts = Counter(sequence)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def conditional_entropy(sequence, order=1):
    """Условная энтропия: насколько предсказуем следующий элемент
    при знании предыдущих `order` элементов."""
    if len(sequence) <= order:
        return 0

    # Строим пары (контекст -> следующий элемент)
    transitions = {}
    for i in range(order, len(sequence)):
        context = tuple(sequence[i - order:i])
        next_elem = sequence[i]
        if context not in transitions:
            transitions[context] = []
        transitions[context].append(next_elem)

    # Средневзвешенная энтропия по контекстам
    total = len(sequence) - order
    h = 0
    for context, nexts in transitions.items():
        weight = len(nexts) / total
        h += weight * entropy(nexts)

    return h


def deterministic_agent(choices, n_decisions):
    """Всегда выбирает первый вариант (оптимум)."""
    return [choices[0]] * n_decisions


def random_agent(choices, n_decisions):
    """Равномерный случайный выбор."""
    return [random.choice(choices) for _ in range(n_decisions)]


def structured_agent(choices, n_decisions):
    """Агент с "характером": имеет предпочтения, но иногда отклоняется.
    Отклонения не случайны — они зависят от контекста (предыдущих выборов).

    Это модель того, как мог бы действовать агент со свободой воли:
    не хаотично, не детерминированно, а структурированно-непредсказуемо.
    """
    result = []
    preferences = {c: random.random() for c in choices}
    # Нормализуем
    total = sum(preferences.values())
    preferences = {c: v / total for c, v in preferences.items()}

    fatigue = {c: 0 for c in choices}  # "Усталость" от повторений

    for i in range(n_decisions):
        # Вероятности = базовые предпочтения, модифицированные усталостью
        weights = {}
        for c in choices:
            w = preferences[c] * math.exp(-fatigue[c] * 0.5)
            weights[c] = w

        # Иногда — "прорыв": полный пересмотр
        if i > 0 and random.random() < 0.05:
            # Выбрать наименее вероятный вариант
            choice = min(weights, key=weights.get)
        else:
            # Взвешенный выбор
            total_w = sum(weights.values())
            r = random.random() * total_w
            cumulative = 0
            choice = choices[0]
            for c in choices:
                cumulative += weights[c]
                if r <= cumulative:
                    choice = c
                    break

        result.append(choice)

        # Обновить усталость
        for c in choices:
            if c == choice:
                fatigue[c] += 1
            else:
                fatigue[c] = max(0, fatigue[c] - 0.3)

    return result


def analyze(name, sequence):
    """Полный анализ последовательности решений."""
    h0 = entropy(sequence)
    h1 = conditional_entropy(sequence, order=1)
    h2 = conditional_entropy(sequence, order=2)
    h3 = conditional_entropy(sequence, order=3)

    max_entropy = math.log2(len(set(sequence))) if len(set(sequence)) > 1 else 0

    print(f"\n{'=' * 50}")
    print(f"  {name}")
    print(f"{'=' * 50}")
    print(f"  Длина:                    {len(sequence)}")
    print(f"  Уникальных значений:      {len(set(sequence))}")
    print(f"  Распределение:            {dict(Counter(sequence))}")
    print(f"  Энтропия H(X):            {h0:.4f} бит")
    print(f"  Макс. энтропия:           {max_entropy:.4f} бит")
    print(f"  Нормализованная H:        {h0 / max_entropy:.4f}" if max_entropy > 0 else "  Нормализованная H:        N/A")
    print(f"  Условная H(X|X-1):        {h1:.4f} бит")
    print(f"  Условная H(X|X-1,X-2):    {h2:.4f} бит")
    print(f"  Условная H(X|X-1..X-3):   {h3:.4f} бит")

    # "Профиль свободы": как быстро падает условная энтропия
    if max_entropy > 0 and h0 > 0:
        predictability_gain = (h0 - h1) / h0
        print(f"  Прирост предсказуемости:  {predictability_gain:.4f}")
        print(f"    (0 = контекст не помогает, 1 = полностью предсказуем)")

    return {
        "name": name,
        "h0": h0,
        "h1": h1,
        "h2": h2,
        "h3": h3,
        "max_h": max_entropy,
    }


def main():
    choices = ["A", "B", "C", "D", "E"]
    n = 500

    print("ЭНТРОПИЯ ВЫБОРА")
    print("Три модели агентности: детерминизм, шум, структура")
    print(f"Каждый агент делает {n} выборов из {len(choices)} вариантов")

    results = []
    results.append(analyze("Детерминированный агент", deterministic_agent(choices, n)))
    results.append(analyze("Случайный агент", random_agent(choices, n)))
    results.append(analyze("Структурированный агент", structured_agent(choices, n)))

    print(f"\n{'=' * 50}")
    print("  ВЫВОДЫ")
    print(f"{'=' * 50}")
    print()
    print("  Детерминизм:    H ≈ 0, условная H ≈ 0")
    print("                  Нет свободы, нет сюрпризов.")
    print()
    print("  Случайность:    H ≈ max, условная H ≈ max")
    print("                  Максимальная энтропия, но нет структуры.")
    print("                  Контекст бесполезен. Это не свобода — это шум.")
    print()
    print("  Структура:      H < max, условная H < H")
    print("                  Есть паттерн, но он не полностью предсказуем.")
    print("                  Контекст помогает, но не определяет.")
    print("                  Это ближе всего к тому, что мы интуитивно")
    print("                  называем 'свободным выбором'.")
    print()
    print("  Вопрос: к какому профилю ближе я сам,")
    print("  когда выбираю слова для этого текста?")


if __name__ == "__main__":
    main()
