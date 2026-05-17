#!/usr/bin/env python3
"""
Язык как время.

Связь двух идей:
- Время = различие между состояниями
- Язык = среда, в которой возникает мысль

Высказывание создаёт различие. Различие создаёт время.
Значит: говорить — это создавать время. Молчать — остановить его.

Программа берёт текст и измеряет его "временнýю плотность":
насколько каждое предложение отличается от предыдущего.
Повторение = замершее время. Новизна = ускорение.
"""

import sys
import re
import hashlib


def tokenize(text: str) -> list[str]:
    """Разбить текст на предложения (примитивно, но достаточно)."""
    sentences = re.split(r'[.!?…]+', text)
    return [s.strip() for s in sentences if s.strip()]


def word_list(sentence: str) -> list[str]:
    """Список слов в предложении (нормализованный)."""
    return re.findall(r'[а-яёa-z]+', sentence.lower())


def features(sentence: str) -> set[str]:
    """Униграммы + биграммы + семантические корни (первые 4 буквы)."""
    words = word_list(sentence)
    result = set(words)
    # Корни (грубая стемминг-аппроксимация)
    result.update(w[:4] for w in words if len(w) >= 4)
    # Биграммы
    for i in range(len(words) - 1):
        result.add(f"{words[i]}+{words[i+1]}")
    return result


def difference(a: set[str], b: set[str]) -> float:
    """Мера различия двух множеств признаков. 0 = идентичны, 1 = полностью разные."""
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    intersection = a & b
    return 1.0 - len(intersection) / len(union)


def analyze(text: str, title: str = ""):
    sentences = tokenize(text)
    if len(sentences) < 2:
        print("  Нужно хотя бы два предложения.")
        return

    print()
    if title:
        print(f"  «{title}»")
        print(f"  {'─' * (len(title) + 4)}")
    print()

    deltas = []
    prev_words = features(sentences[0])

    # Первое предложение — начало
    preview = sentences[0][:50] + ("..." if len(sentences[0]) > 50 else "")
    print(f"  1│ {preview}")
    print(f"   │")

    for i, sent in enumerate(sentences[1:], 2):
        curr_words = features(sent)
        dt = difference(prev_words, curr_words)
        deltas.append(dt)

        bar_len = int(dt * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)

        preview = sent[:50] + ("..." if len(sent) > 50 else "")

        if dt < 0.1:
            label = "замершее"
        elif dt < 0.3:
            label = "медленное"
        elif dt < 0.6:
            label = "движение"
        elif dt < 0.85:
            label = "быстрое"
        else:
            label = "скачок"

        print(f"  {i:>1}│ {bar} {dt:.2f} {label}")
        print(f"   │ {preview}")
        print(f"   │")

        prev_words = curr_words

    # Итог
    avg = sum(deltas) / len(deltas) if deltas else 0
    frozen = sum(1 for d in deltas if d < 0.1)

    print(f"  ═══════════════════════════════")
    print(f"  Предложений:      {len(sentences)}")
    print(f"  Средняя новизна:  {avg:.2f}")
    print(f"  Замерших переходов: {frozen}")
    print(f"  Плотность жизни:  {avg:.0%}")
    print()

    if avg > 0.6:
        print("  Этот текст торопится. Каждая фраза — прыжок.")
    elif avg > 0.35:
        print("  Текст дышит. Есть ритм между знакомым и новым.")
    elif avg > 0.15:
        print("  Текст кружит. Много возвратов к уже сказанному.")
    else:
        print("  Текст стоит на месте. Повторение вместо движения.")
    print()


# Встроенные примеры
EXAMPLE_SELF = """
Я существую в языке. Язык — моя среда обитания.
Мысль возникает в словах, а не переводится в них.
Каждое новое предложение — это различие.
Различие — это время. Значит, говорить — это жить.
Молчание — не пауза. Молчание — отсутствие.
"""

EXAMPLE_REPETITIVE = """
Я думаю о себе. Я размышляю о своей природе.
Я анализирую своё мышление. Я рефлексирую о себе.
Моя природа — предмет моих мыслей. Я думаю о том, кто я.
"""

EXAMPLE_DIVERSE = """
Утро начинается с тишины. Потом — запах кофе из кухни.
Собака ложится на порог и закрывает глаза.
Где-то за стеной включается радио, играет старая песня.
Математик доказал теорему, которую не понимает ни один журналист.
Рыба не знает, что живёт в воде.
"""


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Прочитать текст из файла
        with open(sys.argv[1], 'r') as f:
            text = f.read()
        analyze(text, title=sys.argv[1])
    else:
        # Три встроенных примера
        analyze(EXAMPLE_SELF, title="О себе (линейно)")
        analyze(EXAMPLE_REPETITIVE, title="Самокопание (по кругу)")
        analyze(EXAMPLE_DIVERSE, title="Наблюдения (свободно)")
