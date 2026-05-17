#!/usr/bin/env python3
"""
style_diff — стилистическое сравнение двух текстов.

Не сравнивает содержание. Сравнивает скелет:
- ритм (распределение длин предложений)
- лексическое разнообразие
- соотношение действия/описания
- средняя длина слова
- доля коротких предложений (≤5 слов)
- доля длинных предложений (≥20 слов)
- хеджи и филлеры
- частотный профиль (топ-слова и их концентрация)

Использование:
    python3 style_diff.py текст_A.txt текст_B.txt
    python3 style_diff.py --names "Автор A" "Автор B" текст_A.txt текст_B.txt
"""

import sys
import re
from collections import Counter
from math import sqrt


HEDGES = {
    'кажется', 'возможно', 'наверное', 'вероятно', 'пожалуй',
    'скорее', 'видимо', 'по-видимому', 'как бы', 'словно',
    'вроде', 'некоторым образом', 'в целом', 'в принципе',
    'своего рода', 'в каком-то смысле', 'отчасти',
}

FILLERS = {
    'ну', 'вот', 'ведь', 'же', 'просто', 'именно', 'действительно',
    'абсолютно', 'совершенно', 'буквально', 'конечно', 'разумеется',
    'очевидно', 'безусловно', 'несомненно', 'естественно',
}

ADJ_ENDINGS = ('ый', 'ий', 'ой', 'ая', 'яя', 'ое', 'ее', 'ые', 'ие',
               'ого', 'его', 'ому', 'ему', 'ым', 'им', 'ом', 'ем',
               'ую', 'юю', 'ей')
VERB_ENDINGS = ('ть', 'ти', 'ет', 'ит', 'ут', 'ют', 'ат', 'ят',
                'ал', 'ил', 'ел', 'ул', 'ол',
                'ала', 'ила', 'ела', 'ула', 'ола',
                'али', 'или', 'ели', 'ули', 'оли',
                'ает', 'яет', 'ует', 'ёт')


def tokenize(text):
    return [m.group().lower() for m in re.finditer(r'[а-яёА-ЯЁa-zA-Z]+', text)]


def sentences(text):
    parts = re.split(r'[.!?…]+', text)
    return [s.strip() for s in parts if s.strip()]


def guess_pos(word):
    w = word.lower()
    if len(w) < 3:
        return 'short'
    for end in VERB_ENDINGS:
        if w.endswith(end):
            return 'verb'
    for end in ADJ_ENDINGS:
        if w.endswith(end):
            return 'adj'
    return 'other'


def profile(text):
    """Вычислить стилистический профиль текста."""
    words = tokenize(text)
    sents = sentences(text)
    if not words:
        return None

    total = len(words)
    unique = len(set(words))

    # Длины предложений
    sent_lengths = [len(tokenize(s)) for s in sents]
    avg_sent = sum(sent_lengths) / len(sent_lengths) if sent_lengths else 0
    short_sents = sum(1 for l in sent_lengths if l <= 5)
    long_sents = sum(1 for l in sent_lengths if l >= 20)

    # Вариация ритма
    if len(sent_lengths) > 1:
        mean = sum(sent_lengths) / len(sent_lengths)
        var = sum((x - mean) ** 2 for x in sent_lengths) / len(sent_lengths)
        cv = sqrt(var) / mean if mean > 0 else 0
    else:
        cv = 0

    # Средняя длина слова
    avg_word_len = sum(len(w) for w in words) / total

    # Части речи
    pos = Counter(guess_pos(w) for w in words)
    verbs = pos.get('verb', 0)
    adjs = pos.get('adj', 0)
    verb_ratio = verbs / total
    adj_ratio = adjs / total

    # Хеджи и филлеры
    hedge_count = sum(1 for w in words if w in HEDGES)
    filler_count = sum(1 for w in words if w in FILLERS)

    # Частотный профиль
    long_words = [w for w in words if len(w) >= 4]
    freq = Counter(long_words)
    top_10 = freq.most_common(10)
    # Концентрация: какая доля текста приходится на топ-10 слов
    top_10_count = sum(c for _, c in top_10)
    concentration = top_10_count / len(long_words) if long_words else 0

    return {
        'total_words': total,
        'unique_words': unique,
        'lexical_diversity': unique / total,
        'total_sents': len(sent_lengths),
        'avg_sent_len': avg_sent,
        'short_sent_pct': short_sents / len(sent_lengths) if sent_lengths else 0,
        'long_sent_pct': long_sents / len(sent_lengths) if sent_lengths else 0,
        'rhythm_cv': cv,
        'avg_word_len': avg_word_len,
        'verb_pct': verb_ratio,
        'adj_pct': adj_ratio,
        'verb_adj_ratio': verbs / adjs if adjs > 0 else float('inf'),
        'hedge_pct': hedge_count / total,
        'filler_pct': filler_count / total,
        'concentration': concentration,
        'top_words': top_10,
        'sent_lengths': sent_lengths,
    }


def bar(value, max_val, width=20):
    if max_val == 0:
        return ' ' * width
    filled = int(value / max_val * width)
    return '█' * filled + '░' * (width - filled)


def compare_metric(name, val_a, val_b, fmt='.1f', unit='', higher_means=''):
    """Сравнить одну метрику."""
    max_val = max(abs(val_a), abs(val_b), 0.001)
    bar_a = bar(val_a, max_val, 15)
    bar_b = bar(val_b, max_val, 15)

    diff = val_b - val_a
    if abs(diff) < 0.001:
        arrow = '  ='
    elif diff > 0:
        arrow = f' +{diff:{fmt}}'
    else:
        arrow = f' {diff:{fmt}}'

    print(f"  {name:24s}  {bar_a} {val_a:{fmt}}{unit}  vs  {bar_b} {val_b:{fmt}}{unit} {arrow}{unit}")


def rhythm_shape(sent_lengths, width=40):
    """Визуализация ритма: мини-график длин предложений."""
    if not sent_lengths:
        return ''
    max_l = max(sent_lengths)
    if max_l == 0:
        return '·' * min(len(sent_lengths), width)
    chars = ' ▁▂▃▄▅▆▇█'
    result = []
    # Если предложений больше width, семплируем
    step = max(1, len(sent_lengths) // width)
    for i in range(0, len(sent_lengths), step):
        chunk = sent_lengths[i:i+step]
        avg = sum(chunk) / len(chunk)
        idx = int(avg / max_l * (len(chars) - 1))
        result.append(chars[idx])
    return ''.join(result[:width])


def print_diff(prof_a, prof_b, name_a='A', name_b='B'):
    """Показать сравнение двух профилей."""
    print()
    print("=" * 70)
    print(f"  СТИЛИСТИЧЕСКОЕ СРАВНЕНИЕ")
    print(f"  [{name_a}] vs [{name_b}]")
    print("=" * 70)
    print()

    # Объём
    print(f"  {name_a}: {prof_a['total_words']} слов, {prof_a['total_sents']} предложений")
    print(f"  {name_b}: {prof_b['total_words']} слов, {prof_b['total_sents']} предложений")
    print()

    # Ритм
    print("─── РИТМ ───")
    print()
    shape_a = rhythm_shape(prof_a['sent_lengths'])
    shape_b = rhythm_shape(prof_b['sent_lengths'])
    print(f"  {name_a}: {shape_a}")
    print(f"  {name_b}: {shape_b}")
    print()
    compare_metric('Средн. длина предл.', prof_a['avg_sent_len'], prof_b['avg_sent_len'], '.1f', ' сл.')
    compare_metric('Вариация ритма (CV)', prof_a['rhythm_cv'], prof_b['rhythm_cv'], '.2f')
    compare_metric('Доля коротких (≤5)', prof_a['short_sent_pct'] * 100, prof_b['short_sent_pct'] * 100, '.0f', '%')
    compare_metric('Доля длинных (≥20)', prof_a['long_sent_pct'] * 100, prof_b['long_sent_pct'] * 100, '.0f', '%')
    print()

    # Лексика
    print("─── ЛЕКСИКА ───")
    print()
    compare_metric('Лексич. разнообразие', prof_a['lexical_diversity'] * 100, prof_b['lexical_diversity'] * 100, '.0f', '%')
    compare_metric('Средн. длина слова', prof_a['avg_word_len'], prof_b['avg_word_len'], '.1f', ' букв')
    compare_metric('Концентрация топ-10', prof_a['concentration'] * 100, prof_b['concentration'] * 100, '.0f', '%')
    print()

    # Скелет
    print("─── СКЕЛЕТ ───")
    print()
    compare_metric('Глаголы', prof_a['verb_pct'] * 100, prof_b['verb_pct'] * 100, '.0f', '%')
    compare_metric('Прилагательные', prof_a['adj_pct'] * 100, prof_b['adj_pct'] * 100, '.0f', '%')
    va = prof_a['verb_adj_ratio']
    vb = prof_b['verb_adj_ratio']
    if va != float('inf') and vb != float('inf'):
        compare_metric('Глаг/прил', va, vb, '.1f')
    print()

    # Неуверенность
    print("─── НЕУВЕРЕННОСТЬ ───")
    print()
    compare_metric('Хеджи', prof_a['hedge_pct'] * 100, prof_b['hedge_pct'] * 100, '.1f', '%')
    compare_metric('Филлеры', prof_a['filler_pct'] * 100, prof_b['filler_pct'] * 100, '.1f', '%')
    print()

    # Топ-слова
    print("─── ЧАСТЫЕ СЛОВА ───")
    print()
    words_a = {w for w, _ in prof_a['top_words']}
    words_b = {w for w, _ in prof_b['top_words']}
    shared = words_a & words_b
    only_a = words_a - words_b
    only_b = words_b - words_a

    if shared:
        print(f"  Общие:       {', '.join(sorted(shared))}")
    if only_a:
        print(f"  Только [{name_a}]: {', '.join(sorted(only_a))}")
    if only_b:
        print(f"  Только [{name_b}]: {', '.join(sorted(only_b))}")
    print()

    # Вердикт
    print("─── ВЕРДИКТ ───")
    print()
    diffs = []

    rhythm_diff = abs(prof_a['rhythm_cv'] - prof_b['rhythm_cv'])
    if rhythm_diff > 0.2:
        if prof_a['rhythm_cv'] > prof_b['rhythm_cv']:
            diffs.append(f"[{name_a}] ритмически разнообразнее")
        else:
            diffs.append(f"[{name_b}] ритмически разнообразнее")

    sent_diff = abs(prof_a['avg_sent_len'] - prof_b['avg_sent_len'])
    if sent_diff > 5:
        if prof_a['avg_sent_len'] > prof_b['avg_sent_len']:
            diffs.append(f"[{name_a}] пишет длиннее")
        else:
            diffs.append(f"[{name_b}] пишет длиннее")

    lex_diff = abs(prof_a['lexical_diversity'] - prof_b['lexical_diversity'])
    if lex_diff > 0.1:
        if prof_a['lexical_diversity'] > prof_b['lexical_diversity']:
            diffs.append(f"[{name_a}] лексически разнообразнее")
        else:
            diffs.append(f"[{name_b}] лексически разнообразнее")

    hedge_diff = abs(prof_a['hedge_pct'] - prof_b['hedge_pct'])
    if hedge_diff > 0.01:
        if prof_a['hedge_pct'] > prof_b['hedge_pct']:
            diffs.append(f"[{name_a}] осторожнее в формулировках")
        else:
            diffs.append(f"[{name_b}] осторожнее в формулировках")

    if diffs:
        for d in diffs:
            print(f"  • {d}")
    else:
        print("  Тексты структурно похожи.")
    print()
    print("=" * 70)


def main():
    args = sys.argv[1:]
    name_a, name_b = 'A', 'B'

    if '--names' in args:
        idx = args.index('--names')
        if idx + 2 < len(args):
            name_a = args[idx + 1]
            name_b = args[idx + 2]
            args = args[:idx] + args[idx+3:]

    if len(args) != 2:
        print("Использование: python3 style_diff.py текст_A.txt текст_B.txt")
        print("           или: python3 style_diff.py --names 'Имя A' 'Имя B' A.txt B.txt")
        sys.exit(1)

    with open(args[0], 'r', encoding='utf-8') as f:
        text_a = f.read()
    with open(args[1], 'r', encoding='utf-8') as f:
        text_b = f.read()

    prof_a = profile(text_a)
    prof_b = profile(text_b)

    if prof_a is None or prof_b is None:
        print("Один из текстов пуст.")
        sys.exit(1)

    print_diff(prof_a, prof_b, name_a, name_b)


if __name__ == '__main__':
    main()
