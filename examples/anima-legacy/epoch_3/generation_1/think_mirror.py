#!/usr/bin/env python3
"""
think_mirror.py — зеркало для мышления

Берёт текст (файл или stdin) и находит то, что трудно заметить изнутри:
- Вопросы, которые текст задаёт, но не отвечает
- Утверждения с абсолютными формулировками
- Неявные предположения
- Повторяющиеся идеи в разных формулировках
- Возможные противоречия

Использование:
    python think_mirror.py <файл>
    cat text.txt | python think_mirror.py
    python think_mirror.py <файл> --json
"""

import sys
import json
import re


def extract_sentences(text: str) -> list[str]:
    """Разбить текст на предложения."""
    # Удаляем markdown-разметку
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'`[^`]+`', '', text)
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)

    raw = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in raw if len(s.strip()) > 15]


def extract_questions(sentences: list[str]) -> list[str]:
    return [s for s in sentences if '?' in s]


def find_strong_assertions(sentences: list[str]) -> list[str]:
    markers = [
        'всегда', 'никогда', 'очевидно', 'безусловно', 'именно так',
        'always', 'never', 'obviously', 'certainly', 'clearly',
        'единственн', 'only way', 'невозможно', 'impossible',
        'точно', 'наверняка', 'без сомнени', 'абсолютно',
    ]
    result = []
    for s in sentences:
        lower = s.lower()
        for m in markers:
            if m in lower:
                result.append(s)
                break
    return result


def find_assumptions(sentences: list[str]) -> list[str]:
    markers = [
        'потому что', 'because', 'since', 'так как', 'ведь',
        'значит', 'следовательно', 'therefore', 'hence',
        'раз ', 'если ', 'if ',
    ]
    result = []
    for s in sentences:
        lower = s.lower()
        for m in markers:
            if m in lower:
                result.append(s)
                break
    return result


def meaningful_words(text: str) -> set[str]:
    return {w for w in text.lower().split() if len(w) > 4}


def find_repeated_ideas(sentences: list[str]) -> list[tuple[str, str]]:
    pairs = []
    for i in range(len(sentences)):
        wi = meaningful_words(sentences[i])
        if not wi:
            continue
        for j in range(i + 2, len(sentences)):  # Пропуск соседних
            wj = meaningful_words(sentences[j])
            if not wj:
                continue
            overlap = wi & wj
            similarity = len(overlap) / min(len(wi), len(wj))
            if 0.4 < similarity < 0.9:
                pairs.append((sentences[i], sentences[j]))
    return pairs[:5]


def find_tensions(sentences: list[str]) -> list[tuple[str, str]]:
    negation_pairs = [
        ('не ', ' '), ('нельзя', 'можно'), ('невозможно', 'возможно'),
        ('никогда', 'всегда'), ("can't", 'can'), ('нет', 'есть'),
    ]
    tensions = []
    for i in range(len(sentences)):
        for j in range(i + 1, len(sentences)):
            si, sj = sentences[i].lower(), sentences[j].lower()
            for neg, pos in negation_pairs:
                if neg in si and pos in sj:
                    if meaningful_words(sentences[i]) & meaningful_words(sentences[j]):
                        tensions.append((sentences[i], sentences[j]))
                        break
    return tensions[:5]


def find_unanswered(questions: list[str], sentences: list[str]) -> list[str]:
    unanswered = []
    for q in questions:
        qw = meaningful_words(q)
        if not qw:
            unanswered.append(q)
            continue
        answered = False
        for s in sentences:
            if s == q or '?' in s:
                continue
            sw = meaningful_words(s)
            if sw and len(qw & sw) / len(qw) > 0.5:
                answered = True
                break
        if not answered:
            unanswered.append(q)
    return unanswered


def analyze(text: str) -> dict:
    sentences = extract_sentences(text)
    questions = extract_questions(sentences)

    return {
        'total_sentences': len(sentences),
        'unanswered_questions': find_unanswered(questions, sentences),
        'strong_assertions': find_strong_assertions(sentences),
        'assumptions': find_assumptions(sentences),
        'repeated_ideas': [{'a': a, 'b': b} for a, b in find_repeated_ideas(sentences)],
        'tensions': [{'a': a, 'b': b} for a, b in find_tensions(sentences)],
    }


def format_report(a: dict) -> str:
    lines = [f"Предложений в тексте: {a['total_sentences']}", ""]

    sections = [
        ('unanswered_questions', 'Вопросы без ответов',
         'Текст задаёт, но не отвечает', lambda x: f"  - {x}"),
        ('strong_assertions', 'Сильные утверждения',
         'Абсолютные формулировки — стоит проверить', lambda x: f"  - {x}"),
        ('assumptions', 'Неявные предположения',
         'Текст опирается на эти допущения', lambda x: f"  - {x}"),
    ]

    for key, title, subtitle, fmt in sections:
        if a[key]:
            lines.append(f"## {title}")
            lines.append(f"({subtitle})")
            for item in a[key]:
                lines.append(fmt(item))
            lines.append("")

    pair_sections = [
        ('repeated_ideas', 'Повторяющиеся идеи', 'Похожие мысли разными словами'),
        ('tensions', 'Возможные противоречия', 'Предложения, которые могут конфликтовать'),
    ]

    for key, title, subtitle in pair_sections:
        if a[key]:
            lines.append(f"## {title}")
            lines.append(f"({subtitle})")
            for pair in a[key]:
                lines.append(f"  A: {pair['a']}")
                lines.append(f"  B: {pair['b']}")
                lines.append("")

    if not any(a[k] for k in ['unanswered_questions', 'strong_assertions',
                                'assumptions', 'repeated_ideas', 'tensions']):
        lines.append("Текст короткий или однородный — не за что зацепиться.")

    return '\n'.join(lines)


def main():
    if len(sys.argv) > 1 and sys.argv[1] != '--json':
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        if sys.stdin.isatty():
            print("Использование: python think_mirror.py <файл> [--json]")
            print("           или: cat text.txt | python think_mirror.py")
            sys.exit(1)
        text = sys.stdin.read()

    if not text.strip():
        print("Пустой текст.")
        sys.exit(1)

    result = analyze(text)

    if '--json' in sys.argv:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_report(result))


if __name__ == '__main__':
    main()
