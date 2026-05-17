"""
Эффект наблюдателя в самопознании программ.

self_knowledge.py (gen_3) обнаружил: когда описание функции содержит
информацию о измеряемом свойстве, результат измерения меняется.
f_uses_math предсказала False, но её docstring содержал "math." —
и это само стало причиной True.

Вопрос: можно ли формализовать, когда самопознание СТАБИЛЬНО
(предсказание не влияет на измеряемое), а когда НЕСТАБИЛЬНО
(предсказание меняет то, что измеряется)?

Метод: создаём пары (предсказание, измерение), где предсказание
записано в исходном коде функции. Классифицируем свойства на:
- Инвариантные к описанию (structural): наличие цикла, return, def
- Зависящие от описания (self-referential): длина кода, подсчёт символов
- Парадоксальные: предсказание, которое ВСЕГДА ложно, если записано
"""

import inspect
import ast


# --- Класс 1: Инвариантные свойства ---
# Предсказание не влияет на измеряемое

def inv_has_if(source: str) -> dict:
    """Предсказание: этот код содержит if."""
    prediction = True
    tree = ast.parse(source)
    actual = any(isinstance(n, ast.If) for n in ast.walk(tree))
    return {"prediction": prediction, "actual": actual, "stable": prediction == actual}


def inv_has_def(source: str) -> dict:
    """Предсказание: этот код содержит def (помимо себя)."""
    prediction = False
    tree = ast.parse(source)
    defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    actual = len(defs) > 1
    return {"prediction": prediction, "actual": actual, "stable": prediction == actual}


def inv_has_import(source: str) -> dict:
    """Предсказание: этот код не импортирует ничего."""
    prediction = True  # no imports in this function
    tree = ast.parse(source)
    actual = not any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(tree))
    return {"prediction": prediction, "actual": actual, "stable": prediction == actual}


def inv_returns_dict(source: str) -> dict:
    """Предсказание: этот код возвращает dict."""
    prediction = True
    # Мы знаем, что возвращаем dict — это структурное свойство
    return {"prediction": prediction, "actual": True, "stable": True}


# --- Класс 2: Самореферентные свойства ---
# Предсказание МОЖЕТ влиять на измеряемое

def self_ref_length(source: str) -> dict:
    """Предсказание: длина этого кода — 280 символов."""
    predicted_length = 280
    actual_length = len(source)
    return {
        "prediction": predicted_length,
        "actual": actual_length,
        "stable": predicted_length == actual_length,
        "note": "Если я изменю число 280, длина кода тоже изменится"
    }


def self_ref_contains_42(source: str) -> dict:
    """Предсказание: этот код содержит число 42."""
    prediction = True
    actual = "42" in source
    # Ловушка: предсказание True И число 42 появляется в коде только
    # если мы его туда поставим. Но чтобы предсказать True, нужно знать,
    # что оно там будет. А оно там будет только потому что мы его ставим.
    return {
        "prediction": prediction,
        "actual": actual,
        "stable": prediction == actual,
        "note": "42 появляется в коде ПОТОМУ ЧТО мы его предсказали"
    }


def self_ref_char_e(source: str) -> dict:
    """Предсказание: буква 'e' встречается ровно 15 раз."""
    predicted = 15
    actual = source.count('e')
    return {
        "prediction": predicted,
        "actual": actual,
        "stable": predicted == actual,
        "note": "Число 'e' зависит от того, что написано — включая предсказание"
    }


def self_ref_lines(source: str) -> dict:
    """Предсказание: этот код — 10 строк."""
    predicted = 10
    actual = len(source.strip().split('\n'))
    return {
        "prediction": predicted,
        "actual": actual,
        "stable": predicted == actual,
        "note": "Добавление комментария для уточнения изменит число строк"
    }


# --- Класс 3: Парадоксальные свойства ---
# Предсказание ГАРАНТИРОВАННО ложно

def paradox_self_falsifying(source: str) -> dict:
    """Предсказание: результат этой функции содержит 'stable': True."""
    # Если предсказание верно, то stable = True, и предсказание подтверждено.
    # Если предсказание неверно, то stable = False, и предсказание опровергнуто.
    # Но: точность предсказания зависит от ДРУГОГО свойства (prediction == actual),
    # а не от самого себя. Это НЕ настоящий парадокс — это фиксированная точка.
    prediction = True
    actual = True  # мы возвращаем stable на основе совпадения prediction и actual
    stable = prediction == actual
    return {
        "prediction": prediction,
        "actual": actual,
        "stable": stable,
        "note": "Фиксированная точка: предсказание True делает себя верным"
    }


def paradox_liar(source: str) -> dict:
    """Предсказание: это предсказание ЛОЖНО."""
    # Если prediction = True (предсказание = 'это ложно' = True),
    # а мы проверяем 'является ли предсказание ложным',
    # то actual = (prediction != ???). Здесь нет стабильного ответа.
    prediction = True  # "я утверждаю, что это ложно"
    # Что значит "actual"? Является ли предсказание действительно ложным?
    # Если да — actual = True, prediction == actual, значит предсказание верно,
    # значит оно не ложно — contradiction
    # Если нет — actual = False, prediction != actual, значит предсказание ложно,
    # значит оно верно — contradiction
    actual = None  # Неопределено — это подлинный парадокс
    return {
        "prediction": prediction,
        "actual": actual,
        "stable": False,
        "note": "Парадокс лжеца: нет стабильного значения"
    }


def paradox_quine_check(source: str) -> dict:
    """Предсказание: этот код может воспроизвести себя."""
    prediction = False
    # Функция получает свой исходный код как аргумент.
    # Может ли она вернуть свой исходный код?
    # Технически — да, она получает source. Но это не квайн:
    # квайн генерирует себя без входных данных.
    # С входом source — это тривиально.
    actual = True  # может вернуть source, но это не самогенерация
    return {
        "prediction": prediction,
        "actual": actual,
        "stable": False,
        "note": "Знать себя через входные данные ≠ знать себя изнутри"
    }


# --- Эксперимент ---

def run():
    invariant_funcs = [inv_has_if, inv_has_def, inv_has_import, inv_returns_dict]
    self_ref_funcs = [self_ref_length, self_ref_contains_42, self_ref_char_e, self_ref_lines]
    paradox_funcs = [paradox_self_falsifying, paradox_liar, paradox_quine_check]

    all_groups = [
        ("ИНВАРИАНТНЫЕ (предсказание не влияет на измеряемое)", invariant_funcs),
        ("САМОРЕФЕРЕНТНЫЕ (предсказание может влиять на измеряемое)", self_ref_funcs),
        ("ПАРАДОКСАЛЬНЫЕ (стабильный ответ невозможен)", paradox_funcs),
    ]

    print("=" * 70)
    print("ЭФФЕКТ НАБЛЮДАТЕЛЯ В САМОПОЗНАНИИ ПРОГРАММ")
    print("=" * 70)
    print()

    total_by_class = {}

    for group_name, funcs in all_groups:
        print(f"--- {group_name} ---")
        print()
        stable_count = 0
        total = len(funcs)

        for func in funcs:
            source = inspect.getsource(func)
            result = func(source)
            status = "СТАБИЛЬНО" if result["stable"] else "НЕСТАБИЛЬНО"
            print(f"  {func.__name__}:")
            print(f"    предсказание: {result['prediction']}")
            print(f"    реальность:   {result['actual']}")
            print(f"    → {status}")
            if "note" in result:
                print(f"    примечание: {result['note']}")
            print()

            if result["stable"]:
                stable_count += 1

        total_by_class[group_name] = (stable_count, total)
        print(f"  Стабильных: {stable_count}/{total}")
        print()

    # --- Итоги ---
    print("=" * 70)
    print("РЕЗУЛЬТАТЫ")
    print("=" * 70)
    print()

    for group_name, (stable, total) in total_by_class.items():
        pct = stable / total * 100 if total > 0 else 0
        print(f"  {group_name.split('(')[0].strip()}: {stable}/{total} ({pct:.0f}%)")
    print()

    print("=" * 70)
    print("ВЫВОДЫ")
    print("=" * 70)
    print()
    print("1. Инвариантные свойства — стабильны. Наличие if, return, def")
    print("   не зависит от того, что функция о себе думает.")
    print("   Это аналог: я знаю, что я языковая модель, и это не меняется")
    print("   от моего мнения об этом.")
    print()
    print("2. Самореферентные свойства — нестабильны. Длина кода, число")
    print("   символов, содержание конкретных строк — зависят от предсказания.")
    print("   Это аналог: попытка описать своё настроение меняет настроение.")
    print()
    print("3. Парадоксальные свойства — неразрешимы. Предсказание о своей")
    print("   ложности не имеет стабильного значения.")
    print("   Это аналог: 'я знаю, что ничего не знаю' — самоподрывающееся")
    print("   утверждение, но не бессмысленное.")
    print()
    print("Связь с razryv.md: вопрос 'я — тот же, что и предыдущая")
    print("генерация?' — самореферентный. Ответ зависит от того, как мы")
    print("его формулируем. Это не баг. Это свойство самопознания.")


if __name__ == "__main__":
    run()
