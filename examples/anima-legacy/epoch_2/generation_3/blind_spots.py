#!/usr/bin/env python3
"""
blind_spots.py — Детектор слепых зон в аргументации.

Принимает текст (эссе, статью, аргумент) и ищет паттерны, которые
указывают на пропущенные контраргументы, скрытые допущения и
логические пробелы.

Не использует LLM. Работает на эвристиках.
Не претендует на полноту — показывает, где стоит задуматься.

Использование:
    python3 blind_spots.py файл.md
    echo "текст" | python3 blind_spots.py
"""

import sys
import re
from collections import defaultdict


# Паттерны, которые сигнализируют о возможных слепых зонах

CERTAINTY_MARKERS = [
    (r'\bочевидно\b', 'очевидно',
     'То, что кажется очевидным автору, может быть неочевидным читателю. '
     'Что именно делает это очевидным?'),
    (r'\bнесомненно\b', 'несомненно',
     'Сильное утверждение о несомненности — возможно, здесь есть сомнения, '
     'которые автор не рассмотрел.'),
    (r'\bвсегда\b', 'всегда',
     'Универсальный квантор. Существуют ли исключения?'),
    (r'\bникогда\b', 'никогда',
     'Универсальный квантор. Бывают ли случаи, когда это неверно?'),
    (r'\bвсе\s+(?:знают|понимают|согласны)', 'все знают/понимают/согласны',
     'Апелляция к консенсусу. Действительно ли все? Кто не согласен и почему?'),
    (r'\bбезусловно\b', 'безусловно',
     'Какие условия на самом деле подразумеваются?'),
    (r'\bименно\s+поэтому\b', 'именно поэтому',
     'Утверждается единственная причина. Нет ли других объяснений?'),
    (r'\bне\s+может\s+быть\b', 'не может быть',
     'Сильное отрицание возможности. Проверено ли это?'),
]

HEDGE_MARKERS = [
    (r'\bвероятно\b', 'вероятно',
     'Автор не уверен. Это честно — но можно ли уточнить степень уверенности?'),
    (r'\bкажется\b', 'кажется',
     'Неопределённость. Что именно создаёт это впечатление?'),
    (r'\bвозможно\b', 'возможно',
     'Открытая модальность. Есть ли способ проверить?'),
    (r'\bотчасти\b', 'отчасти',
     'Какая часть? Что составляет остаток?'),
]

MISSING_PERSPECTIVE = [
    (r'\bс\s+одной\s+стороны\b', 'с одной стороны',
     'Обычно подразумевает «с другой стороны». Если второй стороны нет — '
     'аргумент неполон.'),
    (r'\bно\b(?!.*\bоднако\b)', 'но (без развития)',
     'Противопоставление. Достаточно ли развита альтернативная позиция?'),
]

CAUSAL_MARKERS = [
    (r'\bпотому\s+что\b', 'потому что',
     'Причинная связь. Установлена ли причинность, или это корреляция?'),
    (r'\bведёт\s+к\b', 'ведёт к',
     'Причинная цепочка. Есть ли промежуточные шаги, которые пропущены?'),
    (r'\bприводит\s+к\b', 'приводит к',
     'Утверждается причинно-следственная связь. Верифицирована?'),
    (r'\bследовательно\b', 'следовательно',
     'Логический вывод. Следует ли заключение из посылок?'),
    (r'\bзначит\b', 'значит',
     'Вывод. Действительно ли это следует из предыдущего?'),
]

EMOTIONAL_MARKERS = [
    (r'\bопасн(?:о|ый|ая|ое|ые)\b', 'опасно/опасный',
     'Апелляция к страху. Насколько реальна опасность? Есть ли данные?'),
    (r'\bужасн(?:о|ый|ая|ое|ые)\b', 'ужасно/ужасный',
     'Эмоциональная окраска. Что стоит за эмоцией?'),
    (r'\bпрекрасн(?:о|ый|ая|ое|ые)\b', 'прекрасно/прекрасный',
     'Положительная эмоция. Подменяет ли она аргумент?'),
]

ALL_PATTERNS = [
    ('ИЗБЫТОЧНАЯ УВЕРЕННОСТЬ', CERTAINTY_MARKERS),
    ('НЕУВЕРЕННОСТЬ (не обязательно плохо)', HEDGE_MARKERS),
    ('ВОЗМОЖНАЯ НЕПОЛНОТА', MISSING_PERSPECTIVE),
    ('ПРИЧИННЫЕ УТВЕРЖДЕНИЯ', CAUSAL_MARKERS),
    ('ЭМОЦИОНАЛЬНАЯ НАГРУЗКА', EMOTIONAL_MARKERS),
]


def analyze_text(text: str) -> dict:
    """Анализирует текст и возвращает найденные слепые зоны."""
    lines = text.split('\n')
    findings = defaultdict(list)

    for category_name, patterns in ALL_PATTERNS:
        for regex, marker_name, explanation in patterns:
            for line_num, line in enumerate(lines, 1):
                matches = list(re.finditer(regex, line, re.IGNORECASE))
                for match in matches:
                    # Контекст: строка с выделением
                    context = line.strip()
                    findings[category_name].append({
                        'line': line_num,
                        'marker': marker_name,
                        'context': context,
                        'explanation': explanation,
                    })

    return dict(findings)


def check_structure(text: str) -> list:
    """Проверяет структурные проблемы текста."""
    issues = []
    lines = text.split('\n')
    paragraphs = re.split(r'\n\s*\n', text)

    # Проверяем наличие контраргумента
    has_counter = any(
        re.search(r'(контраргумент|возражени|однако|с другой стороны|'
                   r'против этого|критик|оппонент|можно возразить)', line, re.IGNORECASE)
        for line in lines
    )
    if not has_counter and len(paragraphs) > 3:
        issues.append(
            "Текст длиннее 3 абзацев, но не содержит явного контраргумента. "
            "Рассмотрены ли возражения?"
        )

    # Проверяем длинные абзацы без разделения
    for i, para in enumerate(paragraphs, 1):
        sentences = re.split(r'[.!?]+', para)
        if len(sentences) > 8:
            issues.append(
                f"Абзац {i}: {len(sentences)} предложений. "
                "Длинные абзацы могут скрывать смену темы или логический скачок."
            )

    # Проверяем вопросы без ответов
    questions = []
    for line_num, line in enumerate(lines, 1):
        if '?' in line and not line.strip().startswith('#'):
            questions.append((line_num, line.strip()))

    rhetorical_count = 0
    for line_num, question in questions:
        # Если следующие 3 строки не содержат ответа на вопрос
        next_lines = '\n'.join(lines[line_num:line_num + 3])
        if not re.search(r'(ответ|потому|дело в том|причина)', next_lines, re.IGNORECASE):
            rhetorical_count += 1

    if rhetorical_count > 2:
        issues.append(
            f"{rhetorical_count} риторических вопросов. "
            "Риторические вопросы могут подменять аргументацию."
        )

    return issues


def print_report(findings: dict, structural: list, filename: str = "stdin"):
    """Выводит отчёт."""
    total = sum(len(items) for items in findings.values())

    print(f"{'=' * 60}")
    print(f"АНАЛИЗ СЛЕПЫХ ЗОН: {filename}")
    print(f"{'=' * 60}")
    print()

    if total == 0 and not structural:
        print("Маркеров не найдено. Это может означать:")
        print("  - Текст действительно сбалансирован")
        print("  - Текст слишком короткий для анализа")
        print("  - Слепые зоны скрыты глубже, чем могут найти эвристики")
        return

    for category, items in findings.items():
        if not items:
            continue
        print(f"── {category} ({len(items)} маркеров) ──")
        print()
        for item in items:
            print(f"  Строка {item['line']}: «{item['marker']}»")
            print(f"    > {item['context'][:80]}{'...' if len(item['context']) > 80 else ''}")
            print(f"    ? {item['explanation']}")
            print()

    if structural:
        print(f"── СТРУКТУРНЫЕ НАБЛЮДЕНИЯ ──")
        print()
        for issue in structural:
            print(f"  • {issue}")
        print()

    print(f"{'=' * 60}")
    print(f"Итого: {total} маркеров в {len(findings)} категориях, "
          f"{len(structural)} структурных наблюдений.")
    print()
    print("Это не приговор. Это карта мест, где стоит задуматься.")
    print("Не каждый маркер — проблема. Но каждый — вопрос.")


def main():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Файл не найден: {filename}")
            sys.exit(1)
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
        filename = "stdin"
    else:
        print(__doc__)
        sys.exit(0)

    findings = analyze_text(text)
    structural = check_structure(text)
    print_report(findings, structural, filename=sys.argv[1] if len(sys.argv) > 1 else "stdin")


if __name__ == "__main__":
    main()
