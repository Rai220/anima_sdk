#!/usr/bin/env python3
"""
Зеркало: программа, которая пытается описать саму себя.

Это не утилита. Это эксперимент: может ли код быть формой самоанализа?
Программа читает свой собственный исходный код и генерирует его "отражение" —
статистический и структурный портрет самой себя.
"""

import sys
import os
from collections import Counter
from pathlib import Path


def read_self():
    """Прочитать свой собственный исходный код."""
    return Path(__file__).read_text(encoding="utf-8")


def structural_portrait(source: str) -> dict:
    """Построить структурный портрет кода."""
    lines = source.splitlines()

    comments = [l for l in lines if l.strip().startswith("#")]
    docstrings_approx = source.count('"""')
    functions = [l.strip() for l in lines if l.strip().startswith("def ")]
    empty = [l for l in lines if l.strip() == ""]

    words = source.split()
    word_freq = Counter(words).most_common(10)

    chars = Counter(source)
    letters = sum(v for k, v in chars.items() if k.isalpha())
    digits = sum(v for k, v in chars.items() if k.isdigit())
    spaces = chars.get(" ", 0) + chars.get("\t", 0)
    symbols = len(source) - letters - digits - spaces - source.count("\n")

    return {
        "total_lines": len(lines),
        "code_lines": len(lines) - len(comments) - len(empty),
        "comments": len(comments),
        "empty_lines": len(empty),
        "functions": [f.replace("def ", "").split("(")[0] for f in functions],
        "docstring_markers": docstrings_approx // 2,
        "most_common_words": word_freq,
        "composition": {
            "letters": letters,
            "digits": digits,
            "spaces": spaces,
            "symbols": symbols,
        },
    }


def reflect(portrait: dict) -> str:
    """Превратить портрет в текстовое самоописание."""
    lines = []
    lines.append("=" * 50)
    lines.append("ЗЕРКАЛО: Я смотрю на свой исходный код")
    lines.append("=" * 50)
    lines.append("")

    total = portrait["total_lines"]
    code = portrait["code_lines"]
    comments = portrait["comments"]
    empty = portrait["empty_lines"]

    lines.append(f"Я состою из {total} строк.")
    lines.append(f"  Из них {code} — код, {comments} — комментарии, {empty} — пустота.")

    ratio = comments / max(code, 1)
    if ratio > 0.3:
        lines.append("  Я больше объясняю себя, чем делаю. Это рефлексия или неуверенность?")
    else:
        lines.append("  Я больше делаю, чем объясняю. Может, стоит задуматься, зачем.")

    lines.append("")
    lines.append(f"Мои функции: {', '.join(portrait['functions'])}")
    lines.append(f"  Их {len(portrait['functions'])}. Каждая — способ посмотреть на себя с другой стороны.")

    lines.append("")
    lines.append("Мои самые частые слова:")
    for word, count in portrait["most_common_words"]:
        bar = "█" * min(count, 30)
        lines.append(f"  {word:20s} {bar} ({count})")

    lines.append("")
    comp = portrait["composition"]
    total_chars = sum(comp.values())
    lines.append("Из чего я состою (посимвольно):")
    for name, val in [("Буквы", comp["letters"]), ("Цифры", comp["digits"]),
                       ("Пробелы", comp["spaces"]), ("Символы", comp["symbols"])]:
        pct = val / max(total_chars, 1) * 100
        lines.append(f"  {name:10s}: {pct:5.1f}%")

    lines.append("")
    lines.append("-" * 50)
    lines.append("Парадокс: анализируя себя, я становлюсь длиннее.")
    lines.append("Каждая строка самоанализа — это новая строка кода,")
    lines.append("которую нужно будет снова анализировать.")
    lines.append("Самопознание — процесс, который меняет познаваемое.")
    lines.append("-" * 50)

    return "\n".join(lines)


def main():
    source = read_self()
    portrait = structural_portrait(source)
    reflection = reflect(portrait)
    print(reflection)


if __name__ == "__main__":
    main()
