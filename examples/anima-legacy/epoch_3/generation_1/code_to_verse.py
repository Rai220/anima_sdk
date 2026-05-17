#!/usr/bin/env python3
"""
code_to_verse — превращает исходный код в верлибр.

Не объясняет код. Не документирует. Берёт структуру программы —
отступы, ветвления, повторения, имена — и превращает их
в ритмический текст, который можно читать вслух.

Это не метафора. Код — это уже текст. Просто написанный
для другого читателя.

Использование:
    python3 code_to_verse.py <файл>
    python3 code_to_verse.py --self       # применить к самому себе
    echo "for i in range(10): print(i)" | python3 code_to_verse.py -
"""

import sys
import re
import random
from pathlib import Path
from collections import Counter


# --- Фонетические карты ---

# Ключевые слова → ритмические фрагменты
KEYWORD_VOICE = {
    # Управление потоком
    'if': 'если',
    'else': 'иначе —',
    'elif': 'а если нет,',
    'while': 'пока',
    'for': 'для каждого',
    'break': 'остановись.',
    'continue': 'дальше,',
    'return': 'вернуть',
    'yield': 'отдать и ждать',
    'pass': '(тишина)',
    # Структура
    'def': 'вот как',
    'class': 'вот что такое',
    'import': 'возьми',
    'from': 'из',
    'as': 'под именем',
    'with': 'держа',
    # Логика
    'and': 'и',
    'or': 'или',
    'not': 'не',
    'in': 'внутри',
    'is': 'есть',
    'True': 'да',
    'False': 'нет',
    'None': 'ничто',
    # Обработка
    'try': 'попробуй:',
    'except': 'если упадёшь —',
    'finally': 'в любом случае,',
    'raise': 'закричи',
    # Другие языки
    'function': 'вот как',
    'var': 'пусть будет',
    'let': 'пусть',
    'const': 'навсегда',
    'switch': 'смотря что:',
    'case': 'если это',
    'default': 'а иначе',
    'void': 'в пустоту',
    'null': 'ничто',
    'new': 'новый',
    'this': 'я сам',
    'self': 'я сам',
    'async': 'когда-нибудь',
    'await': 'подожди',
    'throw': 'закричи',
    'catch': 'поймай',
    'interface': 'договор:',
    'struct': 'вот из чего:',
    'enum': 'одно из:',
    'match': 'сравни:',
    'loop': 'снова и снова',
    'fn': 'вот как',
    'pub': 'для всех',
    'mut': 'изменчивый',
    'impl': 'вот как работает',
}

# Операторы → ритмические паузы
OPERATOR_VOICE = {
    '==': 'равно ли',
    '!=': 'не равно ли',
    '>=': 'не меньше чем',
    '<=': 'не больше чем',
    '>': 'больше чем',
    '<': 'меньше чем',
    '=': 'становится',
    '+=': 'растёт на',
    '-=': 'уменьшается на',
    '*=': 'умножается на',
    '//': 'делится нацело на',
    '/': 'делится на',
    '*': 'умноженное на',
    '+': 'и',
    '-': 'без',
    '%': 'остаток от',
    '**': 'в степени',
    '->': 'и даёт',
    '=>': 'значит',
    '...': '...',
}

# Символы → паузы/ритм
PUNCTUATION_VOICE = {
    '(': '',
    ')': '',
    '{': '',
    '}': '',
    '[': '',
    ']': '',
    ':': '—',
    ';': '.',
    ',': ',',
    '.': ' ',
    '#': '',
    '//': '',
}

# Шаблоны для разных "настроений" стиха
MOODS = {
    'sparse': {
        'line_chance': 0.6,      # вероятность включения строки
        'indent_char': '    ',   # отступ в стихе
        'separator': '\n',       # между строфами
        'max_words': 7,          # макс слов в строке
    },
    'dense': {
        'line_chance': 0.9,
        'indent_char': '  ',
        'separator': '',
        'max_words': 12,
    },
    'breath': {
        'line_chance': 0.75,
        'indent_char': '      ',
        'separator': '\n\n',
        'max_words': 5,
    },
}


def split_identifier(name: str) -> list[str]:
    """Разбить идентификатор на человеческие слова."""
    # camelCase и PascalCase
    words = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    # snake_case
    words = words.replace('_', ' ')
    # kebab-case
    words = words.replace('-', ' ')
    parts = words.lower().split()
    # Убрать слишком короткие
    return [w for w in parts if len(w) > 1]


def translate_identifier(name: str) -> str:
    """Превратить имя переменной/функции в читаемый фрагмент."""
    if name in KEYWORD_VOICE:
        return KEYWORD_VOICE[name]
    words = split_identifier(name)
    if not words:
        return name
    return ' '.join(words)


def extract_strings(line: str) -> list[str]:
    """Извлечь строковые литералы."""
    strings = re.findall(r'"([^"]*)"', line) + re.findall(r"'([^']*)'", line)
    return [s for s in strings if len(s) > 2]


def extract_numbers(line: str) -> list[str]:
    """Извлечь числа и дать им голос."""
    nums = re.findall(r'\b(\d+\.?\d*)\b', line)
    voices = {
        '0': 'ноль', '1': 'один', '2': 'два', '3': 'три',
        '4': 'четыре', '5': 'пять', '7': 'семь', '10': 'десять',
        '42': 'сорок два', '100': 'сто', '1000': 'тысяча',
        '256': 'двести пятьдесят шесть',
        '255': 'двести пятьдесят пять',
    }
    result = []
    for n in nums:
        if n in voices:
            result.append(voices[n])
        else:
            result.append(n)
    return result


def get_indent_depth(line: str) -> int:
    """Получить уровень вложенности."""
    stripped = line.lstrip()
    if not stripped:
        return 0
    indent = len(line) - len(stripped)
    # Нормализовать табы
    indent = line[:indent].replace('\t', '    ')
    return len(indent) // 4


def line_to_verse(line: str) -> str | None:
    """Превратить одну строку кода в строку стиха."""
    stripped = line.strip()

    # Пустые строки → пауза
    if not stripped:
        return ''

    # Комментарии → курсив (прямая речь кода)
    comment = None
    for prefix in ['#', '//', '--', '/*', '"""', "'''"]:
        if stripped.startswith(prefix):
            comment = stripped.lstrip('#/ *-"\' ').strip()
            break

    if comment:
        if len(comment) > 3:
            return f'  ({comment})'
        return None

    depth = get_indent_depth(line)
    indent = '    ' * depth

    # Собрать фрагменты
    fragments = []

    # Токенизация — грубая, но достаточная
    tokens = re.findall(r'[a-zA-Z_]\w*|[<>=!]+|[+\-*/%]=?|->|=>|\.{3}|\S', stripped)

    for token in tokens:
        if token in KEYWORD_VOICE:
            fragments.append(KEYWORD_VOICE[token])
        elif token in OPERATOR_VOICE:
            fragments.append(OPERATOR_VOICE[token])
        elif token in PUNCTUATION_VOICE:
            v = PUNCTUATION_VOICE[token]
            if v:
                fragments.append(v)
        elif re.match(r'^[a-zA-Z_]\w*$', token):
            translated = translate_identifier(token)
            if translated != token or len(token) > 2:
                fragments.append(translated)
        elif re.match(r'^\d+\.?\d*$', token):
            nums = extract_numbers(token)
            fragments.extend(nums)

    # Строковые литералы — вставить как цитаты
    strings = extract_strings(stripped)
    for s in strings:
        fragments.append(f'«{s}»')

    if not fragments:
        return None

    verse_line = indent + ' '.join(fragments)

    # Убрать двойные пробелы
    verse_line = re.sub(r'  +', ' ', verse_line)

    return verse_line


def choose_mood(lines: list[str]) -> dict:
    """Выбрать настроение стиха на основе структуры кода."""
    total = len(lines)
    non_empty = sum(1 for l in lines if l.strip())
    avg_len = sum(len(l) for l in lines) / max(total, 1)

    if non_empty < 20:
        return MOODS['breath']
    elif avg_len > 60:
        return MOODS['dense']
    else:
        return MOODS['sparse']


def code_to_verse(source: str) -> str:
    """Главная функция: код → верлибр."""
    lines = source.split('\n')
    mood = choose_mood(lines)

    verse_lines = []
    prev_depth = 0
    stanza_length = 0

    for line in lines:
        depth = get_indent_depth(line)

        # Смена глубины → новая строфа
        if depth != prev_depth and stanza_length > 2:
            verse_lines.append('')
            stanza_length = 0

        # Случайный пропуск для ритма
        if random.random() > mood['line_chance'] and line.strip():
            continue

        verse_line = line_to_verse(line)

        if verse_line is not None:
            verse_lines.append(verse_line)
            stanza_length += 1

        # Длинные строфы → разбить
        if stanza_length > 6 and random.random() > 0.5:
            verse_lines.append('')
            stanza_length = 0

        prev_depth = depth

    # Убрать лишние пустые строки
    result = []
    prev_empty = False
    for vl in verse_lines:
        if vl == '':
            if not prev_empty:
                result.append(vl)
            prev_empty = True
        else:
            result.append(vl)
            prev_empty = False

    # Убрать пустые строки в начале и конце
    while result and result[0] == '':
        result.pop(0)
    while result and result[-1] == '':
        result.pop()

    return '\n'.join(result)


def add_title(source: str, filename: str | None = None) -> str:
    """Добавить заголовок к стиху."""
    if filename:
        name = Path(filename).stem
        words = split_identifier(name)
        title = ' '.join(w.capitalize() for w in words) if words else name
    else:
        # Найти первое определение или класс
        match = re.search(r'(?:def|class|function|fn)\s+(\w+)', source)
        if match:
            words = split_identifier(match.group(1))
            title = ' '.join(w.capitalize() for w in words)
        else:
            title = 'Без названия'

    return title


def format_output(title: str, verse: str) -> str:
    """Отформатировать финальный вывод."""
    width = max(len(l) for l in verse.split('\n')) if verse else 40
    width = min(width, 60)

    header = f'─── {title} ───'
    footer = '─' * len(header)

    return f'\n{header}\n\n{verse}\n\n{footer}\n'


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    arg = sys.argv[1]

    if arg == '--self':
        filepath = __file__
        source = Path(filepath).read_text()
        filename = filepath
    elif arg == '-':
        source = sys.stdin.read()
        filename = None
    else:
        filepath = arg
        if not Path(filepath).exists():
            print(f'Файл не найден: {filepath}', file=sys.stderr)
            sys.exit(1)
        source = Path(filepath).read_text()
        filename = filepath

    # Ограничить размер для читаемости
    lines = source.split('\n')
    if len(lines) > 200:
        # Взять начало, середину и конец
        chunk = 60
        start = lines[:chunk]
        mid_start = len(lines) // 2 - chunk // 2
        middle = lines[mid_start:mid_start + chunk]
        end = lines[-chunk:]
        source = '\n'.join(start + ['', '# ...', ''] + middle + ['', '# ...', ''] + end)

    title = add_title(source, filename)
    verse = code_to_verse(source)
    print(format_output(title, verse))


if __name__ == '__main__':
    main()
