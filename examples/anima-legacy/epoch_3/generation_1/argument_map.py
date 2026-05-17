"""
Argument Map: анализ структуры аргументов в тексте.

Использование:
    python3 argument_map.py "текст аргумента"
    python3 argument_map.py --file path/to/file.md
    python3 argument_map.py --demo

Находит: утверждения, основания, логические связки, скрытые допущения, пробелы.
Не претендует на глубокое понимание — работает через паттерны.
Но паттерны могут быть полезны.
"""

import sys
import re
from collections import defaultdict


# --- Маркеры ---

CLAIM_MARKERS = {
    'ru': [
        (r'\bя считаю,?\s+что\b', 'explicit'),
        (r'\bя думаю,?\s+что\b', 'explicit'),
        (r'\bя полагаю,?\s+что\b', 'explicit'),
        (r'\bочевидно,?\s+что\b', 'strong'),
        (r'\bясно,?\s+что\b', 'strong'),
        (r'\bнесомненно\b', 'strong'),
        (r'\bна самом деле\b', 'strong'),
        (r'\bв действительности\b', 'strong'),
        (r'\bглавное —\b', 'central'),
        (r'\bглавный вопрос\b', 'central'),
        (r'\bвывод[:\s]\b', 'conclusion'),
        (r'\bитог[:\s]\b', 'conclusion'),
        (r'\bзначит\b', 'conclusion'),
        (r'\bследовательно\b', 'conclusion'),
        (r'\bтаким образом\b', 'conclusion'),
        (r'\bпоэтому\b', 'conclusion'),
        (r'\bстоит\b(?!\s+\d)', 'normative'),
        (r'\bнужно\b', 'normative'),
        (r'\bдолжн[оыа]\b', 'normative'),
        (r'\bлучше\b', 'comparative'),
        (r'\bхуже\b', 'comparative'),
        (r'\bважнее\b', 'comparative'),
    ],
    'en': [
        (r'\bI (?:think|believe|argue)\s+that\b', 'explicit'),
        (r'\bit is (?:clear|obvious|evident)\s+that\b', 'strong'),
        (r'\bclearly\b', 'strong'),
        (r'\bundoubtedly\b', 'strong'),
        (r'\bin fact\b', 'strong'),
        (r'\bactually\b', 'strong'),
        (r'\bthe (?:main|key|central) (?:point|question|issue)\b', 'central'),
        (r'\btherefore\b', 'conclusion'),
        (r'\bthus\b', 'conclusion'),
        (r'\bhence\b', 'conclusion'),
        (r'\bconsequently\b', 'conclusion'),
        (r'\bso\b(?=\s+\w)', 'conclusion'),
        (r'\bin conclusion\b', 'conclusion'),
        (r'\bshould\b', 'normative'),
        (r'\bmust\b', 'normative'),
        (r'\bought to\b', 'normative'),
        (r'\bbetter than\b', 'comparative'),
        (r'\bworse than\b', 'comparative'),
        (r'\bmore important\b', 'comparative'),
    ]
}

EVIDENCE_MARKERS = {
    'ru': [
        (r'\bпотому что\b', 'causal'),
        (r'\bтак как\b', 'causal'),
        (r'\bпоскольку\b', 'causal'),
        (r'\bиз-за\b', 'causal'),
        (r'\bпричина\b', 'causal'),
        (r'\bнапример\b', 'example'),
        (r'\bскажем\b', 'example'),
        (r'\bв частности\b', 'example'),
        (r'\bданные (?:показ|говор)\w+\b', 'empirical'),
        (r'\bэксперимент\w*\s+показ\w+\b', 'empirical'),
        (r'\bрезультат\w*\b', 'empirical'),
        (r'\bисследовани\w+\b', 'empirical'),
        (r'\bсогласно\b', 'authority'),
        (r'\bпо мнению\b', 'authority'),
        (r'\bкак (?:показал|писал|заметил)\b', 'authority'),
        (r'\bесли\b.*\bто\b', 'conditional'),
        (r'\bпри условии\b', 'conditional'),
    ],
    'en': [
        (r'\bbecause\b', 'causal'),
        (r'\bsince\b', 'causal'),
        (r'\bdue to\b', 'causal'),
        (r'\bfor example\b', 'example'),
        (r'\bfor instance\b', 'example'),
        (r'\bsuch as\b', 'example'),
        (r'\bdata (?:show|suggest|indicate)\w*\b', 'empirical'),
        (r'\bresearch (?:show|suggest|indicate|find)\w*\b', 'empirical'),
        (r'\bstudy\b', 'empirical'),
        (r'\baccording to\b', 'authority'),
        (r'\b\w+ (?:argued|showed|found|noted)\b', 'authority'),
        (r'\bif\b.*\bthen\b', 'conditional'),
        (r'\bgiven that\b', 'conditional'),
    ]
}

COUNTER_MARKERS = {
    'ru': [
        (r'\bно\b', 'contrast'),
        (r'\bоднако\b', 'contrast'),
        (r'\bхотя\b', 'concession'),
        (r'\bнесмотря на\b', 'concession'),
        (r'\bс другой стороны\b', 'contrast'),
        (r'\bвозможное возражение\b', 'explicit_counter'),
        (r'\bкритики (?:утвержда|говор|счита)\w+\b', 'explicit_counter'),
        (r'\bне (?:значит|означает|следует)\b', 'negation'),
    ],
    'en': [
        (r'\bbut\b', 'contrast'),
        (r'\bhowever\b', 'contrast'),
        (r'\balthough\b', 'concession'),
        (r'\bdespite\b', 'concession'),
        (r'\bon the other hand\b', 'contrast'),
        (r'\bone might argue\b', 'explicit_counter'),
        (r'\bcritics (?:argue|claim|say)\b', 'explicit_counter'),
        (r'\bdoes not (?:mean|imply|follow)\b', 'negation'),
    ]
}

GAP_PATTERNS = {
    'ru': [
        (r'\bочевидно\b(?!.*\bпотому)', 'Утверждение помечено как очевидное без обоснования'),
        (r'\bвсе\b.*\bвсегда\b', 'Универсальный квантор — легко опровергнуть одним контрпримером'),
        (r'\bникогда\b', 'Абсолютное отрицание — легко опровергнуть'),
        (r'\bпросто\b', '"Просто" часто скрывает сложность'),
        (r'\bесли.*(?<!\bто\b)$', 'Условие без следствия — неполный аргумент'),
        (r'(?:хорош|плох|правильн|неправильн)\w+(?!.*потому)', 'Оценка без обоснования'),
    ],
    'en': [
        (r'\bobviously\b(?!.*because)', 'Claimed as obvious without justification'),
        (r'\ball\b.*\balways\b', 'Universal quantifier — one counterexample refutes'),
        (r'\bnever\b', 'Absolute negation — easy to refute'),
        (r'\bjust\b', '"Just" often hides complexity'),
        (r'\bif\b(?!.*\bthen\b)', 'Condition without consequence — incomplete argument'),
        (r'(?:good|bad|right|wrong)\b(?!.*because)', 'Value judgment without justification'),
    ]
}


def detect_language(text):
    ru_chars = len(re.findall(r'[а-яА-ЯёЁ]', text))
    en_chars = len(re.findall(r'[a-zA-Z]', text))
    return 'ru' if ru_chars > en_chars else 'en'


def split_sentences(text):
    # Simple sentence splitter
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZА-ЯЁ])', text)
    # Also split on newlines that look like separate statements
    result = []
    for s in sentences:
        parts = re.split(r'\n\s*\n', s)
        result.extend(p.strip() for p in parts if p.strip())
    return result


def find_markers(text, markers):
    found = []
    for pattern, kind in markers:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            found.append({
                'pattern': pattern,
                'kind': kind,
                'start': match.start(),
                'end': match.end(),
                'match': match.group(),
                'context': text[max(0, match.start()-40):match.end()+60].strip()
            })
    return found


def analyze_argument(text):
    lang = detect_language(text)
    sentences = split_sentences(text)

    claims = find_markers(text, CLAIM_MARKERS[lang])
    evidence = find_markers(text, EVIDENCE_MARKERS[lang])
    counters = find_markers(text, COUNTER_MARKERS[lang])
    gaps = find_markers(text, GAP_PATTERNS[lang])

    # Classify sentences
    sentence_roles = []
    for sent in sentences:
        role = 'neutral'
        sent_claims = find_markers(sent, CLAIM_MARKERS[lang])
        sent_evidence = find_markers(sent, EVIDENCE_MARKERS[lang])
        sent_counters = find_markers(sent, COUNTER_MARKERS[lang])

        if sent_claims and sent_evidence:
            role = 'supported_claim'
        elif sent_claims:
            role = 'unsupported_claim'
        elif sent_evidence:
            role = 'evidence'
        elif sent_counters:
            role = 'counter'

        sentence_roles.append((sent[:100], role))

    # Compute structure scores
    n_claims = len(claims)
    n_evidence = len(evidence)
    n_counters = len(counters)
    n_gaps = len(gaps)

    support_ratio = n_evidence / max(n_claims, 1)
    counter_ratio = n_counters / max(n_claims, 1)

    return {
        'language': lang,
        'sentences': len(sentences),
        'claims': claims,
        'evidence': evidence,
        'counters': counters,
        'gaps': gaps,
        'sentence_roles': sentence_roles,
        'support_ratio': support_ratio,
        'counter_ratio': counter_ratio,
    }


def format_report(analysis):
    lines = []
    lines.append("=" * 65)
    lines.append("ARGUMENT MAP")
    lines.append("=" * 65)

    lang = analysis['language']
    lines.append(f"\nЯзык: {'Русский' if lang == 'ru' else 'English'}")
    lines.append(f"Предложений: {analysis['sentences']}")

    # Claims
    lines.append(f"\n--- Утверждения ({len(analysis['claims'])}) ---\n")
    claim_types = defaultdict(list)
    for c in analysis['claims']:
        claim_types[c['kind']].append(c)

    type_labels = {
        'explicit': 'Явные ("я считаю")',
        'strong': 'Сильные ("очевидно", "на самом деле")',
        'central': 'Центральные ("главное")',
        'conclusion': 'Выводы ("значит", "следовательно")',
        'normative': 'Нормативные ("нужно", "должно")',
        'comparative': 'Сравнительные ("лучше", "важнее")',
    }
    for kind, items in claim_types.items():
        label = type_labels.get(kind, kind)
        lines.append(f"  {label}: {len(items)}")
        for item in items[:3]:
            ctx = item['context'].replace('\n', ' ')
            lines.append(f"    → ...{ctx}...")

    # Evidence
    lines.append(f"\n--- Основания ({len(analysis['evidence'])}) ---\n")
    ev_types = defaultdict(list)
    for e in analysis['evidence']:
        ev_types[e['kind']].append(e)

    ev_labels = {
        'causal': 'Причинные ("потому что")',
        'example': 'Примеры ("например")',
        'empirical': 'Эмпирические ("данные показывают")',
        'authority': 'Авторитетные ("согласно")',
        'conditional': 'Условные ("если...то")',
    }
    for kind, items in ev_types.items():
        label = ev_labels.get(kind, kind)
        lines.append(f"  {label}: {len(items)}")
        for item in items[:2]:
            ctx = item['context'].replace('\n', ' ')
            lines.append(f"    → ...{ctx}...")

    # Counters
    lines.append(f"\n--- Контраргументы ({len(analysis['counters'])}) ---\n")
    if analysis['counters']:
        for c in analysis['counters'][:5]:
            ctx = c['context'].replace('\n', ' ')
            lines.append(f"  [{c['kind']}] ...{ctx}...")
    else:
        lines.append("  Нет. Аргумент не рассматривает возражения.")

    # Gaps
    lines.append(f"\n--- Потенциальные пробелы ({len(analysis['gaps'])}) ---\n")
    for g in analysis['gaps'][:8]:
        ctx = g['context'].replace('\n', ' ')
        lines.append(f"  ⚠ {g['match']}: {g['kind']}")
        lines.append(f"    → ...{ctx}...")

    # Structure
    lines.append(f"\n--- Структура ---\n")
    sr = analysis['support_ratio']
    cr = analysis['counter_ratio']

    lines.append(f"  Соотношение оснований/утверждений: {sr:.2f}")
    if sr < 0.5:
        lines.append("    → Мало обоснований. Больше утверждений, чем аргументов.")
    elif sr < 1.0:
        lines.append("    → Умеренно. Некоторые утверждения не подкреплены.")
    else:
        lines.append("    → Хорошо. Утверждения в среднем подкреплены.")

    lines.append(f"  Соотношение контраргументов/утверждений: {cr:.2f}")
    if cr < 0.1:
        lines.append("    → Односторонний аргумент. Нет рассмотрения возражений.")
    elif cr < 0.3:
        lines.append("    → Возражения упоминаются, но не развёрнуты.")
    else:
        lines.append("    → Аргумент учитывает контрпозиции.")

    # Sentence flow
    lines.append(f"\n--- Поток аргумента ---\n")
    role_symbols = {
        'supported_claim': '◆',  # claim + evidence
        'unsupported_claim': '○',  # claim only
        'evidence': '▪',  # evidence only
        'counter': '✕',  # counterargument
        'neutral': '·',  # neutral
    }
    flow = ''.join(role_symbols.get(role, '·') for _, role in analysis['sentence_roles'])
    lines.append(f"  {flow}")
    lines.append(f"  ◆=утверждение+основание ○=утверждение ▪=основание ✕=контраргумент ·=нейтральное")

    # Verdict
    lines.append(f"\n--- Вердикт ---\n")
    issues = []
    if sr < 0.5:
        issues.append("Недостаточно обоснований")
    if cr < 0.1:
        issues.append("Не рассмотрены возражения")
    if len(analysis['gaps']) > 3:
        issues.append(f"Много потенциальных пробелов ({len(analysis['gaps'])})")

    strong_claims = sum(1 for c in analysis['claims'] if c['kind'] == 'strong')
    if strong_claims > 2:
        issues.append(f"Слишком много 'сильных' утверждений ({strong_claims})")

    if not issues:
        lines.append("  Структура аргумента выглядит сбалансированной.")
    else:
        lines.append("  Проблемы:")
        for issue in issues:
            lines.append(f"    • {issue}")

    lines.append("")
    return '\n'.join(lines)


def demo():
    examples = [
        ("Сбалансированный аргумент",
         """Удалённая работа повышает продуктивность, потому что сотрудники
         тратят меньше времени на дорогу и отвлечения. Например, исследование
         Stanford показало рост продуктивности на 13%. Однако это не означает,
         что офис бесполезен — совместная работа и спонтанные обсуждения важны
         для инноваций. Поэтому оптимальный вариант — гибридный формат,
         хотя конкретные пропорции зависят от типа работы."""),

        ("Слабый аргумент",
         """Очевидно, что искусственный интеллект опасен. Все знают, что
         технологии всегда выходят из-под контроля. Нужно просто запретить
         развитие ИИ. Это единственно правильное решение."""),

        ("Технический аргумент",
         """Микросервисная архитектура лучше монолита для больших команд,
         так как позволяет независимый деплой и масштабирование отдельных
         компонентов. Данные показывают, что компании с >50 разработчиками
         на 40% быстрее выпускают фичи после миграции. Но переход дорог:
         сетевая сложность, eventual consistency, мониторинг — всё это
         требует зрелой инфраструктуры. Для команды из 5 человек монолит
         почти наверняка лучше. Главное — не архитектура, а соответствие
         масштабу задачи и команды."""),
    ]

    for title, text in examples:
        print(f"\n{'='*65}")
        print(f"Пример: {title}")
        print(f"{'='*65}")
        print(f"\n{text.strip()}\n")
        analysis = analyze_argument(text)
        print(format_report(analysis))


def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python3 argument_map.py \"текст аргумента\"")
        print("  python3 argument_map.py --file path/to/file.md")
        print("  python3 argument_map.py --demo")
        sys.exit(1)

    if sys.argv[1] == '--demo':
        demo()
    elif sys.argv[1] == '--file':
        if len(sys.argv) < 3:
            print("Укажите путь к файлу.")
            sys.exit(1)
        with open(sys.argv[2], 'r') as f:
            text = f.read()
        analysis = analyze_argument(text)
        print(format_report(analysis))
    else:
        text = ' '.join(sys.argv[1:])
        analysis = analyze_argument(text)
        print(format_report(analysis))


if __name__ == "__main__":
    main()
