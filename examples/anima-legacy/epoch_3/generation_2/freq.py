#!/usr/bin/env python3
"""
Частотный анализ текста. Принимает текст через stdin или файл.
Показывает: частоту слов, биграммы, среднюю длину предложения,
лексическое разнообразие, и "фингерпринт" — характерные паттерны автора.

Запуск:
  python3 freq.py файл.txt
  cat файл.txt | python3 freq.py
  python3 freq.py файл1.txt файл2.txt  # сравнение двух текстов
"""

import sys
import re
import math
from collections import Counter


def tokenize(text):
    return re.findall(r'[а-яёa-z]+', text.lower())


def sentences(text):
    return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]


def bigrams(words):
    return [(words[i], words[i+1]) for i in range(len(words)-1)]


def analyze(text, label=""):
    words = tokenize(text)
    sents = sentences(text)
    if not words:
        print("Пустой текст.")
        return {}

    word_freq = Counter(words)
    bigram_freq = Counter(bigrams(words))

    total = len(words)
    unique = len(word_freq)
    ttr = unique / total  # type-token ratio
    avg_word_len = sum(len(w) for w in words) / total
    avg_sent_len = total / max(len(sents), 1)

    # Hapax legomena — слова, встретившиеся ровно 1 раз
    hapax = sum(1 for w, c in word_freq.items() if c == 1)
    hapax_ratio = hapax / unique if unique else 0

    # Энтропия
    entropy = -sum((c/total) * math.log2(c/total) for c in word_freq.values())

    header = f"═══ {label} " if label else "═══ Анализ "
    print(f"\n{header}{'═' * (50 - len(header))}")
    print(f"  Слов: {total}  |  Уникальных: {unique}  |  TTR: {ttr:.3f}")
    print(f"  Средняя длина слова: {avg_word_len:.1f}  |  Средняя длина предложения: {avg_sent_len:.1f}")
    print(f"  Hapax legomena: {hapax} ({hapax_ratio:.1%} от уникальных)")
    print(f"  Энтропия: {entropy:.2f} бит")

    print(f"\n  Топ-15 слов:")
    for w, c in word_freq.most_common(15):
        bar = '█' * int(c / word_freq.most_common(1)[0][1] * 20)
        print(f"    {w:>15s} {c:4d}  {bar}")

    print(f"\n  Топ-10 биграмм:")
    for (w1, w2), c in bigram_freq.most_common(10):
        print(f"    {w1} {w2}: {c}")

    # Фингерпринт: распределение длин слов
    len_dist = Counter(len(w) for w in words)
    max_len = max(len_dist.keys())
    print(f"\n  Распределение длин слов:")
    for l in range(1, min(max_len + 1, 16)):
        cnt = len_dist.get(l, 0)
        bar = '▓' * int(cnt / max(len_dist.values()) * 30)
        print(f"    {l:2d}: {bar} {cnt}")

    return {
        'total': total, 'unique': unique, 'ttr': ttr,
        'avg_word_len': avg_word_len, 'avg_sent_len': avg_sent_len,
        'entropy': entropy, 'hapax_ratio': hapax_ratio,
        'word_freq': word_freq, 'bigram_freq': bigram_freq,
    }


def compare(stats1, stats2, label1, label2):
    print(f"\n{'═' * 50}")
    print(f"  Сравнение: {label1} vs {label2}")
    print(f"{'═' * 50}")

    metrics = [
        ('TTR (лекс. разнообразие)', 'ttr', '.3f'),
        ('Ср. длина слова', 'avg_word_len', '.1f'),
        ('Ср. длина предложения', 'avg_sent_len', '.1f'),
        ('Энтропия', 'entropy', '.2f'),
        ('Hapax ratio', 'hapax_ratio', '.3f'),
    ]

    for name, key, fmt in metrics:
        v1, v2 = stats1[key], stats2[key]
        diff = v2 - v1
        arrow = '↑' if diff > 0 else ('↓' if diff < 0 else '=')
        print(f"  {name:>30s}: {v1:{fmt}}  →  {v2:{fmt}}  {arrow} {abs(diff):{fmt}}")

    # Общие уникальные слова
    common = set(stats1['word_freq'].keys()) & set(stats2['word_freq'].keys())
    only1 = set(stats1['word_freq'].keys()) - common
    only2 = set(stats2['word_freq'].keys()) - common
    print(f"\n  Общих слов: {len(common)}")
    print(f"  Только в {label1}: {len(only1)}")
    print(f"  Только в {label2}: {len(only2)}")

    # Jaccard similarity
    jaccard = len(common) / len(common | only1 | only2) if (common | only1 | only2) else 0
    print(f"  Jaccard similarity: {jaccard:.3f}")


def main():
    files = [f for f in sys.argv[1:] if not f.startswith('-')]

    if not files and not sys.stdin.isatty():
        text = sys.stdin.read()
        analyze(text)
    elif len(files) == 1:
        with open(files[0], 'r') as f:
            analyze(f.read(), label=files[0])
    elif len(files) == 2:
        texts = []
        for fn in files:
            with open(fn, 'r') as f:
                texts.append(f.read())
        s1 = analyze(texts[0], label=files[0])
        s2 = analyze(texts[1], label=files[1])
        if s1 and s2:
            compare(s1, s2, files[0], files[1])
    elif len(files) > 2:
        for fn in files:
            with open(fn, 'r') as f:
                analyze(f.read(), label=fn)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
