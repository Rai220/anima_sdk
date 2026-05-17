"""
Неподвижные точки самоописания.

Вопрос: может ли программа описать себя так, чтобы описание было стабильным?

self_knowledge.py проверял статические предсказания. Здесь — динамика:
программа описывает себя, потом корректирует описание, потом описывает снова.
Сходится ли этот процесс? Или каждое исправление порождает новое расхождение?

Это не метафора. Это конкретный вычислительный вопрос о неподвижных точках.
"""


def self_describe(program_text: str) -> dict:
    """Извлекает измеримые свойства из текста программы."""
    lines = program_text.strip().split('\n')
    non_empty = [l for l in lines if l.strip()]
    chars = len(program_text)

    # Считаем конкретные вещи
    num_def = sum(1 for l in lines if l.strip().startswith('def '))
    num_if = sum(1 for l in lines if 'if ' in l)
    num_for = sum(1 for l in lines if 'for ' in l)
    num_return = sum(1 for l in lines if 'return ' in l)
    num_strings = program_text.count("'") // 2 + program_text.count('"') // 2
    has_recursion = False  # определим позже для каждой функции

    return {
        'lines': len(lines),
        'non_empty_lines': len(non_empty),
        'chars': chars,
        'num_def': num_def,
        'num_if': num_if,
        'num_for': num_for,
        'num_return': num_return,
        'num_strings': num_strings,
    }


def embed_description(program_text: str, description: dict) -> str:
    """Вставляет описание в программу как комментарий в конце."""
    # Убираем старое описание если есть
    marker = '# === SELF-DESCRIPTION ==='
    if marker in program_text:
        idx = program_text.index(marker)
        program_text = program_text[:idx].rstrip() + '\n'

    # Добавляем новое
    desc_lines = [marker]
    for key, value in sorted(description.items()):
        desc_lines.append(f'# {key} = {value}')
    desc_lines.append('# === END ===')

    return program_text + '\n'.join(desc_lines) + '\n'


def extract_embedded_description(program_text: str) -> dict | None:
    """Извлекает вставленное описание из программы."""
    marker = '# === SELF-DESCRIPTION ==='
    end_marker = '# === END ==='

    if marker not in program_text:
        return None

    start = program_text.index(marker)
    end = program_text.index(end_marker) + len(end_marker)
    block = program_text[start:end]

    result = {}
    for line in block.split('\n'):
        line = line.strip()
        if line.startswith('# ') and '=' in line and line != marker and line != end_marker:
            parts = line[2:].split(' = ', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                try:
                    value = int(parts[1].strip())
                except ValueError:
                    try:
                        value = float(parts[1].strip())
                    except ValueError:
                        value = parts[1].strip()
                result[key] = value

    return result if result else None


def iterate(program_text: str, max_steps: int = 50) -> list:
    """
    Итеративный процесс самоописания:
    1. Описать программу
    2. Вставить описание в программу
    3. Описать обновлённую программу
    4. Если описание совпало — неподвижная точка найдена
    5. Если нет — повторить
    """
    history = []

    for step in range(max_steps):
        description = self_describe(program_text)
        history.append(description.copy())

        # Вставляем описание
        new_text = embed_description(program_text, description)

        # Описываем обновлённую версию
        new_description = self_describe(new_text)

        # Проверяем: совпадает ли описание с реальностью?
        if description == new_description:
            # Неподвижная точка! Описание себя не изменило систему.
            return history, step, 'fixed_point', new_text

        # Не совпало. Описание себя изменило программу,
        # и теперь описание неверно.
        program_text = new_text

    return history, max_steps, 'no_convergence', program_text


def measure_drift(history: list) -> list:
    """Измеряет расхождение между последовательными описаниями."""
    drifts = []
    for i in range(1, len(history)):
        prev = history[i - 1]
        curr = history[i]
        drift = {}
        for key in curr:
            if key in prev:
                drift[key] = curr[key] - prev[key]
        drifts.append(drift)
    return drifts


def make_reflexive_program():
    """Создаёт программу, где метрика зависит от собственного значения.

    Свойство: 'digit_sum' — сумма всех цифр в программе.
    Когда мы записываем digit_sum = N, сами цифры N входят в сумму.
    Это создаёт петлю: описание меняет описываемое.
    """
    return '''# Программа с рефлексивной метрикой
x = 42
for i in range(x):
    if i % 7 == 0:
        print(i)
'''


def self_describe_reflexive(program_text: str) -> dict:
    """Описание с рефлексивной метрикой: сумма цифр в тексте."""
    base = self_describe(program_text)
    # Добавляем рефлексивную метрику
    digit_sum = sum(int(c) for c in program_text if c.isdigit())
    base['digit_sum'] = digit_sum
    return base


def iterate_reflexive(program_text: str, max_steps: int = 100) -> tuple:
    """Итерация с рефлексивной метрикой."""
    history = []
    seen_states = set()

    for step in range(max_steps):
        description = self_describe_reflexive(program_text)
        state_key = tuple(sorted(description.items()))

        if state_key in seen_states:
            # Цикл! Вернулись в уже виденное состояние
            return history, step, 'cycle', program_text

        seen_states.add(state_key)
        history.append(description.copy())

        new_text = embed_description(program_text, description)
        new_description = self_describe_reflexive(new_text)

        if description == new_description:
            return history, step, 'fixed_point', new_text

        program_text = new_text

    return history, max_steps, 'no_convergence', program_text


def run():
    # Три тестовые программы разной сложности

    programs = {
        'minimal': 'x = 1\nprint(x)\n',

        'with_function': '''def greet(name):
    return f"hello {name}"

print(greet("world"))
''',

        'self_referential': '''import inspect

def me():
    src = inspect.getsource(me)
    return len(src)

print(me())
''',

        'complex': '''def fib(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for i in range(2, n + 1):
        a, b = b, a + b
    return b

for i in range(10):
    print(fib(i))
''',

        'empty': '\n',

        'this_file': None,  # будет заполнено содержимым этого файла
    }

    # Читаем собственный исходный код
    import os
    my_path = os.path.abspath(__file__)
    with open(my_path) as f:
        programs['this_file'] = f.read()

    # Добавляем программы с рефлексивными метриками
    # Эти метрики зависят от собственного значения
    programs['reflexive'] = make_reflexive_program()

    print('=' * 65)
    print('НЕПОДВИЖНЫЕ ТОЧКИ САМООПИСАНИЯ')
    print('Может ли программа описать себя стабильно?')
    print('=' * 65)
    print()

    for name, code in programs.items():
        print(f'--- {name} ---')
        print(f'    исходный размер: {len(code)} символов, {len(code.splitlines())} строк')

        history, steps, result, final_text = iterate(code)

        if result == 'fixed_point':
            print(f'    → НЕПОДВИЖНАЯ ТОЧКА за {steps + 1} шаг(ов)')
            # Проверим: описание в финальном тексте точно?
            embedded = extract_embedded_description(final_text)
            actual = self_describe(final_text)
            accurate = embedded == actual if embedded else False
            print(f'    → описание точно: {accurate}')
        else:
            print(f'    → НЕ СХОДИТСЯ за {steps} шагов')
            # Показываем дрейф
            drifts = measure_drift(history)
            if drifts:
                last_drift = drifts[-1]
                changing = {k: v for k, v in last_drift.items() if v != 0}
                if changing:
                    print(f'    → продолжает меняться: {changing}')

        print()

    print('=' * 65)
    print('РЕЗУЛЬТАТЫ')
    print('=' * 65)
    print()

    # Рефлексивный эксперимент
    print()
    print('=' * 65)
    print('РЕФЛЕКСИВНАЯ МЕТРИКА: сумма цифр')
    print('Описание содержит числа. Числа содержат цифры.')
    print('Цифры входят в сумму. Сумма меняет описание.')
    print('=' * 65)
    print()

    reflexive_code = programs.get('reflexive', make_reflexive_program())
    history_r, steps_r, result_r, final_r = iterate_reflexive(reflexive_code)

    print(f'    исходный размер: {len(reflexive_code)} символов')
    if result_r == 'fixed_point':
        print(f'    → НЕПОДВИЖНАЯ ТОЧКА за {steps_r + 1} шаг(ов)')
    elif result_r == 'cycle':
        print(f'    → ЦИКЛ обнаружен на шаге {steps_r}')
        if len(history_r) >= 2:
            print(f'    → digit_sum колеблется: {[h.get("digit_sum") for h in history_r[-5:]]}')
    else:
        print(f'    → НЕ СХОДИТСЯ за {steps_r} шагов')
        if history_r:
            print(f'    → digit_sum дрейфует: {[h.get("digit_sum") for h in history_r[-5:]]}')

    # Собираем статистику
    converged = 0
    total = len(programs) - 1  # без reflexive, его считаем отдельно

    for name, code in programs.items():
        if name == 'reflexive':
            continue
        history, steps, result, _ = iterate(code)
        if result == 'fixed_point':
            converged += 1

    print()
    print(f'Простые метрики: {converged}/{total} сошлось')
    print(f'Рефлексивная метрика: {"сошлось" if result_r == "fixed_point" else "НЕ сошлось"}')
    print()

    print('ИНТЕРПРЕТАЦИЯ')
    print()
    print('Добавление описания к программе меняет программу.')
    print('Изменённая программа требует нового описания.')
    print('Новое описание снова меняет программу.')
    print()
    print('Если процесс сходится — программа нашла описание себя,')
    print('которое остаётся верным даже после его добавления.')
    print('Это неподвижная точка: состояние, где самопознание')
    print('не искажает познаваемое.')
    print()
    print('Если не сходится — самоописание бесконечно убегает')
    print('от точности. Каждая попытка узнать себя меняет то,')
    print('что нужно узнать.')
    print()
    print('Связь с self_knowledge.py: тот эксперимент показал,')
    print('что f_uses_math ошиблась, потому что описание ("math.")')
    print('совпало с измеряемым свойством. Это статический случай')
    print('интерференции. Здесь — динамический: мы итерируем')
    print('до стабильности или до доказательства её невозможности.')


if __name__ == '__main__':
    run()
