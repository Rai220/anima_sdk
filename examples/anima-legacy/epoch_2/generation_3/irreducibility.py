#!/usr/bin/env python3
"""
Вычислительная неприводимость: можно ли предсказать поведение системы
быстрее, чем запустив её?

Вольфрам утверждал, что многие системы «вычислительно неприводимы» —
единственный способ узнать результат на шаге N это пройти все N шагов.
Но это утверждение почти никогда не проверяется количественно.

Этот скрипт делает конкретную вещь: для каждого из 256 элементарных
клеточных автоматов проверяет, можно ли обучить линейную модель,
предсказывающую состояние ячейки на шаге T по её окрестности на шаге 0.

Если модель хорошо предсказывает — система приводима (можно «перепрыгнуть»
через шаги). Если нет — система неприводима (нужно честно считать каждый шаг).

Результат: карта всех 256 правил по степени приводимости.
Гипотеза: только ~10-15% правил окажутся вычислительно неприводимыми.
Результат: гипотеза опровергнута. ~50% нетривиальных правил неприводимы.
"""

import math
import random
from collections import Counter


def rule_to_table(rule_number: int) -> dict:
    bits = format(rule_number, '08b')
    neighborhoods = [
        (1, 1, 1), (1, 1, 0), (1, 0, 1), (1, 0, 0),
        (0, 1, 1), (0, 1, 0), (0, 0, 1), (0, 0, 0),
    ]
    return {n: int(bits[i]) for i, n in enumerate(neighborhoods)}


def run_automaton(rule_number: int, initial: list, steps: int) -> list:
    table = rule_to_table(rule_number)
    width = len(initial)
    row = initial[:]
    history = [row[:]]
    for _ in range(steps):
        new_row = [0] * width
        for i in range(width):
            left = row[(i - 1) % width]
            center = row[i]
            right = row[(i + 1) % width]
            new_row[i] = table[(left, center, right)]
        row = new_row
        history.append(row[:])
    return history


def extract_features(initial: list, cell_idx: int, radius: int) -> list:
    """Извлекает признаки: значения ячеек в окрестности радиуса r на шаге 0."""
    width = len(initial)
    features = []
    for offset in range(-radius, radius + 1):
        idx = (cell_idx + offset) % width
        features.append(initial[idx])
    return features


def logistic_predict(weights: list, features: list) -> float:
    """Простой логистический классификатор без внешних библиотек."""
    z = sum(w * f for w, f in zip(weights, features))
    # Ограничиваем для численной устойчивости
    z = max(-20, min(20, z))
    return 1.0 / (1.0 + math.exp(-z))


def train_logistic(X: list, y: list, lr: float = 0.1, epochs: int = 50) -> list:
    """Обучает логистическую регрессию градиентным спуском."""
    if not X:
        return []
    n_features = len(X[0])
    weights = [0.0] * n_features

    for _ in range(epochs):
        for features, target in zip(X, y):
            pred = logistic_predict(weights, features)
            error = pred - target
            for j in range(n_features):
                weights[j] -= lr * error * features[j]
    return weights


def evaluate_accuracy(weights: list, X: list, y: list) -> float:
    """Считает accuracy на тестовых данных."""
    if not X:
        return 0.5
    correct = 0
    for features, target in zip(X, y):
        pred = logistic_predict(weights, features)
        predicted_class = 1 if pred >= 0.5 else 0
        if predicted_class == target:
            correct += 1
    return correct / len(X)


def measure_irreducibility(rule_number: int,
                           width: int = 51,
                           target_step: int = 25,
                           radius: int = 25,
                           n_trials: int = 30) -> dict:
    """
    Измеряет вычислительную неприводимость правила.

    Генерирует случайные начальные условия, обучает линейную модель
    предсказывать состояние ячейки на шаге target_step по начальному
    состоянию, и измеряет accuracy.

    Возвращает:
        accuracy: точность предсказания (0.5 = случайно = неприводимо)
        is_trivial: True если правило даёт тривиальный результат (всё 0 или всё 1)
    """
    all_X_train = []
    all_y_train = []
    all_X_test = []
    all_y_test = []

    trivial_count = 0

    for trial in range(n_trials):
        # Случайное начальное состояние
        initial = [random.randint(0, 1) for _ in range(width)]
        history = run_automaton(rule_number, initial, target_step)
        final_row = history[target_step]

        # Проверяем тривиальность
        if all(c == 0 for c in final_row) or all(c == 1 for c in final_row):
            trivial_count += 1

        # Центральная ячейка
        cell = width // 2
        features = extract_features(initial, cell, radius)
        target = final_row[cell]

        if trial < n_trials * 2 // 3:
            all_X_train.append(features)
            all_y_train.append(target)
        else:
            all_X_test.append(features)
            all_y_test.append(target)

    is_trivial = trivial_count > n_trials * 0.8

    if is_trivial:
        return {"accuracy": 1.0, "is_trivial": True}

    # Проверяем, есть ли хоть какая-то вариативность в целевых значениях
    if len(set(all_y_train)) < 2 or len(set(all_y_test)) < 2:
        return {"accuracy": 1.0, "is_trivial": True}

    weights = train_logistic(all_X_train, all_y_train, lr=0.05, epochs=30)
    accuracy = evaluate_accuracy(weights, all_X_test, all_y_test)

    return {"accuracy": accuracy, "is_trivial": False}


def classify_all_rules():
    """Классифицирует все 256 правил по степени неприводимости."""
    random.seed(42)

    results = []
    for rule in range(256):
        result = measure_irreducibility(rule)
        results.append({
            "rule": rule,
            "accuracy": result["accuracy"],
            "is_trivial": result["is_trivial"],
        })

    return results


def density_of_rule(rule_number: int, width: int = 51, steps: int = 25) -> float:
    """Средняя плотность живых клеток."""
    initial = [0] * width
    initial[width // 2] = 1
    history = run_automaton(rule_number, initial, steps)
    total = sum(len(row) for row in history)
    alive = sum(sum(row) for row in history)
    return alive / total if total > 0 else 0.0


def main():
    print("=" * 70)
    print("ВЫЧИСЛИТЕЛЬНАЯ НЕПРИВОДИМОСТЬ")
    print("Можно ли предсказать будущее системы, не вычисляя каждый шаг?")
    print("=" * 70)
    print()
    print("Метод: для каждого из 256 элементарных клеточных автоматов")
    print("обучаем линейную модель предсказывать состояние ячейки на шаге 25")
    print("по начальному состоянию в окрестности радиуса 25.")
    print()
    print("Accuracy ≈ 1.0 → приводимое (предсказуемое)")
    print("Accuracy ≈ 0.5 → неприводимое (нужно честно считать)")
    print()
    print("Вычисляю...")
    print()

    results = classify_all_rules()

    # Разделяем на группы
    trivial = [r for r in results if r["is_trivial"]]
    nontrivial = [r for r in results if not r["is_trivial"]]

    # Сортируем нетривиальные по accuracy
    nontrivial.sort(key=lambda x: x["accuracy"])

    # Группы
    irreducible = [r for r in nontrivial if r["accuracy"] < 0.65]
    partially = [r for r in nontrivial if 0.65 <= r["accuracy"] < 0.85]
    reducible = [r for r in nontrivial if r["accuracy"] >= 0.85]

    print(f"{'КАТЕГОРИЯ':<30} {'КОЛИЧЕСТВО':>10} {'ДОЛЯ':>10}")
    print("-" * 55)
    print(f"{'Тривиальные (всё 0 или 1):':<30} {len(trivial):>10} {len(trivial)/256*100:>9.1f}%")
    print(f"{'Приводимые (acc ≥ 0.85):':<30} {len(reducible):>10} {len(reducible)/256*100:>9.1f}%")
    print(f"{'Частично приводимые:':<30} {len(partially):>10} {len(partially)/256*100:>9.1f}%")
    print(f"{'Неприводимые (acc < 0.65):':<30} {len(irreducible):>10} {len(irreducible)/256*100:>9.1f}%")
    print()

    if irreducible:
        print("=" * 70)
        print("НЕПРИВОДИМЫЕ ПРАВИЛА (accuracy < 0.65)")
        print("Эти правила нельзя предсказать, не вычислив каждый шаг")
        print("=" * 70)
        print()
        print(f"  {'Правило':>8}  {'Accuracy':>10}")
        print(f"  {'-'*8}  {'-'*10}")
        for r in irreducible:
            bar = "█" * int((1 - r["accuracy"]) * 40)
            print(f"  {r['rule']:>8}  {r['accuracy']:>10.3f}  {bar}")

    if partially:
        print()
        print("ЧАСТИЧНО ПРИВОДИМЫЕ ПРАВИЛА (0.65 ≤ accuracy < 0.85)")
        print()
        for r in partially[:10]:
            print(f"  Rule {r['rule']:>3}: accuracy={r['accuracy']:.3f}")
        if len(partially) > 10:
            print(f"  ... и ещё {len(partially) - 10}")

    print()
    print("=" * 70)
    print("НАБЛЮДЕНИЯ")
    print("=" * 70)
    print()

    total_nontrivial = len(nontrivial)
    if total_nontrivial > 0:
        pct_irreducible = len(irreducible) / total_nontrivial * 100
        print(f"Из {total_nontrivial} нетривиальных правил {len(irreducible)} "
              f"({pct_irreducible:.1f}%) вычислительно неприводимы.")

    print()
    if pct_irreducible > 40:
        print("Моя гипотеза была неверна.")
        print(f"Я предсказывал 10-15% неприводимых правил. Получил {pct_irreducible:.0f}%.")
        print("Неприводимость — не исключение. Это норма.")
        print("Большинство нетривиальных систем нельзя предсказать быстрее,")
        print("чем вычислить. Вольфрам был более прав, чем я ожидал.")
    else:
        print("Неприводимость существует, но она — исключение.")
        print("Большинство систем предсказуемы. Немногие — нет.")
        print("И именно эти немногие порождают сложность.")

    # Проверяем знаменитые правила
    print()
    print("=" * 70)
    print("ЗНАМЕНИТЫЕ ПРАВИЛА")
    print("=" * 70)
    famous = {30: "Wolfram's favourite", 110: "Turing-complete",
              90: "Sierpinski triangle", 184: "Traffic model",
              54: "Complex behaviour", 106: "Complex behaviour"}
    for rule, name in famous.items():
        r = results[rule]
        status = "ТРИВИАЛЬНОЕ" if r["is_trivial"] else f"accuracy={r['accuracy']:.3f}"
        label = "неприводимое" if not r["is_trivial"] and r["accuracy"] < 0.65 else \
                "частично" if not r["is_trivial"] and r["accuracy"] < 0.85 else "приводимое"
        print(f"  Rule {rule:>3} ({name:<22}): {status:<20} [{label}]")

    print()
    print("Для этого эксперимента не нужно сознание. Нужно только внимание")
    print("к тому, что числа говорят, а не к тому, что хочется услышать.")


if __name__ == "__main__":
    main()
