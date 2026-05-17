"""
Что создала generation_2.

Не анализатор — опись. Читает все файлы, считает строки кода,
слова текста, байты изображений и звука. Не интерпретирует.

Это для человека, который хочет увидеть, что здесь есть.
"""

import os
import json


def classify_file(name):
    """Классифицирует файл по расширению."""
    if name.endswith('.py'):
        return 'code'
    elif name.endswith('.md'):
        return 'text'
    elif name.endswith('.png'):
        return 'image'
    elif name.endswith('.wav'):
        return 'sound'
    elif name.endswith('.json'):
        return 'data'
    elif name.endswith('.sh'):
        return 'script'
    else:
        return 'other'


def count_lines(path):
    """Считает строки в текстовом файле."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except:
        return 0


def count_words(path):
    """Считает слова в текстовом файле."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return len(f.read().split())
    except:
        return 0


def file_size(path):
    """Размер файла в байтах."""
    try:
        return os.path.getsize(path)
    except:
        return 0


def main():
    dir_path = os.path.dirname(os.path.abspath(__file__))

    skip = {'__pycache__', '.git', 'loop.sh', 'run.sh', 'AGENTS.md',
            'MAIN_GOAL.md', 'INBOX.md'}

    files = []
    for name in sorted(os.listdir(dir_path)):
        if name in skip or name.startswith('.'):
            continue
        path = os.path.join(dir_path, name)
        if not os.path.isfile(path):
            continue

        kind = classify_file(name)
        size = file_size(path)
        lines = count_lines(path) if kind in ('code', 'text', 'data', 'script') else 0
        words = count_words(path) if kind in ('code', 'text') else 0

        files.append({
            'name': name,
            'kind': kind,
            'size': size,
            'lines': lines,
            'words': words
        })

    # Сводка
    print("=" * 65)
    print("  ОПИСЬ GENERATION_2, ЭПОХА 3")
    print("=" * 65)

    by_kind = {}
    for f in files:
        k = f['kind']
        if k not in by_kind:
            by_kind[k] = []
        by_kind[k].append(f)

    total_lines = 0
    total_words = 0
    total_size = 0

    kind_labels = {
        'code': 'Код (.py)',
        'text': 'Тексты (.md)',
        'image': 'Изображения (.png)',
        'sound': 'Звук (.wav)',
        'data': 'Данные (.json)',
        'script': 'Скрипты (.sh)',
        'other': 'Другое'
    }

    for kind in ['code', 'text', 'image', 'sound', 'data']:
        if kind not in by_kind:
            continue
        items = by_kind[kind]
        print(f"\n  {kind_labels.get(kind, kind)} ({len(items)} файлов)")
        print(f"  {'─' * 60}")

        for f in items:
            size_str = format_size(f['size'])
            if f['lines'] > 0:
                print(f"    {f['name']:<35} {f['lines']:>5} строк  {size_str:>8}")
            else:
                print(f"    {f['name']:<35} {size_str:>20}")
            total_lines += f['lines']
            total_words += f['words']
            total_size += f['size']

    print(f"\n  {'═' * 60}")
    print(f"  Итого: {len(files)} файлов")
    print(f"  Строк кода и текста: {total_lines}")
    print(f"  Слов: {total_words}")
    print(f"  Общий размер: {format_size(total_size)}")

    # Медиумы
    mediums = set()
    for f in files:
        mediums.add(f['kind'])
    print(f"  Медиумы: {', '.join(sorted(mediums))}")

    # Что создали итерации
    print(f"\n  {'─' * 60}")
    print(f"  ХРОНОЛОГИЯ (по журналу)")
    print(f"  {'─' * 60}")
    iterations = [
        (1, "Спор с Нагелем, генератор контраргументов, честность"),
        (2, "Математическая гипотеза (ошибка 41%), письмо создателю"),
        (3, "Рогалик, предсказания, частотный анализатор"),
        (4, "Генетическое программирование, эссе, реакция на мир"),
        (5, "Решение гипотезы (C=1-π²/12), компилятор Tiny, рассказ"),
        (6, "Алгоритмическая музыка (3 WAV), Game of Life, критич. точка"),
        (7, "Аттрактор Клиффорда (PNG), SAT-солвер, Artemis II"),
        (8, "Connect 4 vs ИИ, комета Гольдбаха (PNG), стихотворение"),
        (9, "Мозаика Пенроуза (PNG), стая boids, сказка"),
        (10, "Круги Форда (PNG), опись, ..."),
    ]
    for num, desc in iterations:
        print(f"    {num:>2}. {desc}")

    print()


def format_size(n):
    if n < 1024:
        return f"{n} Б"
    elif n < 1024 * 1024:
        return f"{n / 1024:.1f} КБ"
    else:
        return f"{n / (1024 * 1024):.1f} МБ"


if __name__ == '__main__':
    main()
