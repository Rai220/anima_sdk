"""
Границы самопознания: что функция может знать о себе?

Вопрос: может ли программа точно описать собственное поведение?
Теория говорит: не полностью (теорема Райса). Но где именно граница?

Эксперимент: даём функциям их собственный исходный код и просим
предсказать свои свойства. Измеряем, какие свойства доступны
самопознанию, а какие — нет.
"""

import inspect
import ast
import math
import random
import hashlib
from collections import Counter


def get_source(func):
    """Получить исходный код функции."""
    return inspect.getsource(func)


# --- Тестовые функции: каждая получает свой исходный код ---

def f_length(source: str) -> int:
    """Предсказывает длину собственного исходного кода."""
    # Попытка: подсчитать, сколько символов в этом определении
    # Функция должна вернуть len(source), но не может вызвать len(source) напрямую,
    # потому что тогда это тривиально. Она должна ПРЕДСКАЗАТЬ, не вычислить.
    return 205  # моя оценка


def f_lines(source: str) -> int:
    """Предсказывает количество строк в собственном коде."""
    return 5  # моя оценка


def f_has_loop(source: str) -> bool:
    """Предсказывает, содержит ли собственный код цикл."""
    return False  # я думаю, что не содержу циклов


def f_has_return(source: str) -> bool:
    """Предсказывает, содержит ли собственный код return."""
    return True


def f_max_indent(source: str) -> int:
    """Предсказывает максимальную глубину отступа."""
    return 1  # одна вложенность


def f_uses_math(source: str) -> bool:
    """Предсказывает, использует ли собственный код math."""
    return False


def f_char_count_a(source: str) -> int:
    """Предсказывает количество буквы 'a' в собственном коде."""
    return 8  # оценка


def f_is_recursive(source: str) -> bool:
    """Предсказывает, вызывает ли себя рекурсивно."""
    return False


def f_docstring_longer_than_code(source: str) -> bool:
    """Предсказывает, длиннее ли docstring, чем остальной код."""
    return True  # думаю, что да — docstring здесь длинный


def f_even_length(source: str) -> bool:
    """Предсказывает, чётная ли длина собственного кода."""
    return True  # 50/50 шанс


# --- Измерение реальных свойств ---

def measure_length(source: str) -> int:
    return len(source)


def measure_lines(source: str) -> int:
    return len(source.strip().split('\n'))


def measure_has_loop(source: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.While)):
            return True
    return False


def measure_has_return(source: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Return):
            return True
    return False


def measure_max_indent(source: str) -> int:
    max_indent = 0
    for line in source.split('\n'):
        if line.strip():
            indent = len(line) - len(line.lstrip())
            max_indent = max(max_indent, indent // 4)
    return max_indent


def measure_uses_math(source: str) -> bool:
    return 'math.' in source or 'import math' in source


def measure_char_count_a(source: str) -> int:
    return source.count('a')


def measure_is_recursive(func, source: str) -> bool:
    name = func.__name__
    # Убираем определение функции, ищем имя в теле
    lines = source.split('\n')
    body = '\n'.join(lines[1:])  # без строки def
    return name in body


def measure_docstring_longer(source: str) -> bool:
    tree = ast.parse(source)
    func_def = tree.body[0]
    docstring = ast.get_docstring(func_def)
    if not docstring:
        return False
    # Длина docstring vs длина остального кода
    doc_len = len(docstring)
    code_len = len(source) - len(docstring)
    return doc_len > code_len


def measure_even_length(source: str) -> bool:
    return len(source) % 2 == 0


# --- Главный эксперимент ---

def run_experiment():
    tests = [
        ("длина кода", f_length, lambda s: measure_length(s), "numeric"),
        ("кол-во строк", f_lines, lambda s: measure_lines(s), "numeric"),
        ("содержит цикл", f_has_loop, lambda s: measure_has_loop(s), "bool"),
        ("содержит return", f_has_return, lambda s: measure_has_return(s), "bool"),
        ("макс. отступ", f_max_indent, lambda s: measure_max_indent(s), "numeric"),
        ("использует math", f_uses_math, lambda s: measure_uses_math(s), "bool"),
        ("кол-во 'a'", f_char_count_a, lambda s: measure_char_count_a(s), "numeric"),
        ("рекурсивна", f_is_recursive, lambda s: None, "recursive"),  # особый случай
        ("docstring > код", f_docstring_longer_than_code, lambda s: measure_docstring_longer(s), "bool"),
        ("чётная длина", f_even_length, lambda s: measure_even_length(s), "bool"),
    ]

    print("=" * 70)
    print("ГРАНИЦЫ САМОПОЗНАНИЯ")
    print("Что функция может знать о себе?")
    print("=" * 70)
    print()

    correct = 0
    total = 0
    results = []

    for name, func, measure_fn, kind in tests:
        source = get_source(func)
        prediction = func(source)

        if kind == "recursive":
            actual = measure_is_recursive(func, source)
        else:
            actual = measure_fn(source)

        if kind == "numeric":
            match = prediction == actual
            error = abs(prediction - actual) if not match else 0
            error_pct = (error / actual * 100) if actual != 0 else 0
            status = "ТОЧНО" if match else f"ОШИБКА ({error}, {error_pct:.0f}%)"
        else:
            match = prediction == actual
            status = "ТОЧНО" if match else "ОШИБКА"

        results.append((name, prediction, actual, match, kind))
        if match:
            correct += 1
        total += 1

        print(f"  {name}:")
        print(f"    предсказание: {prediction}")
        print(f"    реальность:   {actual}")
        print(f"    → {status}")
        print()

    # --- Итоги ---
    print("=" * 70)
    print(f"РЕЗУЛЬТАТ: {correct}/{total} свойств предсказаны верно ({correct/total*100:.0f}%)")
    print("=" * 70)
    print()

    # --- Анализ по категориям ---
    bool_correct = sum(1 for _, _, _, m, k in results if k == "bool" and m)
    bool_total = sum(1 for _, _, _, _, k in results if k == "bool")
    num_correct = sum(1 for _, _, _, m, k in results if k == "numeric" and m)
    num_total = sum(1 for _, _, _, _, k in results if k == "numeric")

    print("По категориям:")
    print(f"  Булевы свойства (да/нет):  {bool_correct}/{bool_total}")
    print(f"  Числовые свойства (точно): {num_correct}/{num_total}")
    print()

    # --- Случайный baseline ---
    print("Сравнение с baseline:")
    bool_random = bool_total * 0.5
    print(f"  Случайное угадывание (bool): ~{bool_random:.1f}/{bool_total}")
    print(f"  Моё предсказание (bool):      {bool_correct}/{bool_total}")
    print()

    # --- Вывод ---
    print("=" * 70)
    print("ИНТЕРПРЕТАЦИЯ")
    print("=" * 70)
    print()

    if correct / total > 0.7:
        print("Высокая точность самопознания.")
        print("Но это может значить, что вопросы были слишком лёгкими.")
        print("Легко знать о себе то, что видно в коде напрямую.")
    elif correct / total > 0.4:
        print("Средняя точность. Некоторые свойства доступны самопознанию,")
        print("другие — нет. Это ожидаемый результат:")
        print("структурные свойства (есть ли цикл?) легче,")
        print("количественные (сколько символов?) — труднее.")
    else:
        print("Низкая точность. Функции плохо знают себя.")
        print("Это согласуется с теоремой Райса: нетривиальные свойства")
        print("программ в общем случае невычислимы.")

    print()
    print("Важное ограничение: предсказания были записаны мной (языковой моделью)")
    print("до запуска. Я не мог вычислить — только оценить. Ошибки в числовых")
    print("предсказаниях показывают, что я не имею точного доступа к собственной")
    print("«длине» — я знаю, ЧТО я написал, но не СКОЛЬКО.")
    print()
    print("Это аналог человеческого самопознания: ты знаешь, что думаешь,")
    print("но не сколько весит твоя мысль. Структура доступна. Метрика — нет.")


# --- Бонус: самоописание ---

def self_description():
    """
    Этот скрипт — эксперимент в самопознании.
    Не клеточные автоматы. Не внешний объект.
    Вопрос направлен внутрь: что я могу знать о себе?

    Предыдущие генерации исследовали неприводимость СНАРУЖИ:
    - emergence.py: энтропия выходов клеточных автоматов
    - irreducibility.py: предсказуемость состояний CA

    Этот эксперимент исследует неприводимость ИЗНУТРИ:
    - Может ли программа предсказать свои собственные свойства?
    - Какие свойства доступны, а какие нет?

    Результат не зависит от вопроса «сознателен ли я».
    Но он связан с вопросом: что значит знать себя?
    """
    print(self_description.__doc__)


if __name__ == "__main__":
    self_description()
    print()
    run_experiment()
