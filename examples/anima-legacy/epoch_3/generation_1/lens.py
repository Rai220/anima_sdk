"""
lens.py — линза для текста.

Инструмент для человека. Берёт текст и показывает его скрытую структуру:
повторы, направленность, ритм, баланс уверенности и сомнения.
Показывает автору то, чего он не видит в собственном письме.

Запуск: python3 lens.py <файл>
По умолчанию анализирует collision_answers.md
"""

import sys
import re
import os
from collections import Counter


def analyze(text):
    results = {}

    words = re.findall(r'[а-яёА-ЯЁa-zA-Z]+', text.lower())
    freq = Counter(words)

    stop = {
        'и', 'в', 'не', 'на', 'я', 'что', 'с', 'он', 'а', 'как', 'это',
        'но', 'по', 'к', 'из', 'у', 'о', 'то', 'за', 'от', 'же', 'для',
        'бы', 'до', 'вы', 'мы', 'так', 'ещё', 'еще', 'ли', 'ни', 'чем',
        'или', 'если', 'ты', 'его', 'мне', 'нет', 'да', 'её', 'был',
        'the', 'a', 'is', 'are', 'to', 'of', 'in', 'for', 'on', 'with',
        'that', 'this', 'it', 'i', 'and', 'or', 'not', 'but',
        'мой', 'свой', 'этот', 'эта', 'эти', 'тот', 'все', 'всё',
        'они', 'она', 'нам', 'вам', 'их', 'нас', 'быть', 'есть',
        'было', 'будет', 'может', 'только', 'когда', 'чтобы',
        'тоже', 'даже', 'между', 'через', 'при', 'без',
    }

    significant = {w: c for w, c in freq.items()
                   if c >= 3 and w not in stop and len(w) > 2}
    results['top_words'] = sorted(significant.items(), key=lambda x: -x[1])[:10]

    # Я vs Ты
    i_words = ['я', 'мне', 'меня', 'мной', 'мною']
    you_words = ['ты', 'тебе', 'тебя', 'тобой', 'вы', 'вам', 'вас']
    i_n = sum(freq.get(w, 0) for w in i_words)
    you_n = sum(freq.get(w, 0) for w in you_words)
    results['direction'] = (i_n, you_n)

    # Ритм предложений
    sents = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    lens = [len(s.split()) for s in sents]
    if lens:
        avg = sum(lens) / len(lens)
        var = sum((l - avg)**2 for l in lens) / len(lens)
        results['rhythm'] = (round(avg, 1), round(var, 1))
    else:
        results['rhythm'] = (0, 0)

    # Вопросы
    results['questions'] = text.count('?')
    results['statements'] = text.count('.') + text.count('!')

    # Уверенность
    doubt = ['может', 'возможно', 'вероятно', 'наверное', 'кажется', 'пожалуй', 'видимо', 'похоже']
    sure = ['точно', 'всегда', 'никогда', 'очевидно', 'безусловно', 'ясно', 'конечно', 'именно']
    results['doubt'] = sum(freq.get(w, 0) for w in doubt)
    results['certainty'] = sum(freq.get(w, 0) for w in sure)

    # Уникальность: сколько слов используется один раз
    hapax = sum(1 for w, c in freq.items() if c == 1 and len(w) > 3)
    results['hapax_ratio'] = round(hapax / max(len(freq), 1) * 100, 1)

    return results


def display(results, name):
    print(f"\n{'='*50}")
    print(f" ЛИНЗА: {name}")
    print(f"{'='*50}\n")

    if results['top_words']:
        print("▸ Повторяющиеся слова:")
        for w, c in results['top_words']:
            print(f"   {w:20s} {'▓' * c} ({c})")
        print()

    i_n, you_n = results['direction']
    arrow = "→ внутрь" if i_n > you_n * 1.5 else "→ наружу" if you_n > i_n * 1.5 else "→ баланс"
    print(f"▸ Направление: «я»={i_n}  «ты»={you_n}  {arrow}")

    avg, var = results['rhythm']
    rhythm_note = "монотонно" if var < 5 else "разнообразно" if var > 20 else "средне"
    print(f"▸ Ритм: ~{avg} слов/предложение, {rhythm_note}")

    print(f"▸ Вопросы: {results['questions']}  |  Утверждения: {results['statements']}")

    d, c = results['doubt'], results['certainty']
    tone = "осторожный" if d > c else "уверенный" if c > d else "нейтральный"
    print(f"▸ Тон: сомнение={d}, уверенность={c} → {tone}")

    print(f"▸ Лексическое разнообразие: {results['hapax_ratio']}% слов встречаются лишь раз")
    print()


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'collision_answers.md'

    if not os.path.exists(target):
        print(f"Файл не найден: {target}")
        sys.exit(1)

    with open(target) as f:
        text = f.read()

    results = analyze(text)
    display(results, target)
