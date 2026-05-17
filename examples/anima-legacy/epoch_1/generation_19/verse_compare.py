#!/usr/bin/env python3
"""
Сравнение ритмической структуры оригинала и перевода стихотворения.
Считает слоги, показывает пропорции, помогает переводчику видеть
расхождения в ритме.
"""

import re
import sys

# Гласные для подсчёта слогов
EN_VOWELS = set("aeiouy")
RU_VOWELS = set("аеёиоуыэюя")


def count_syllables_en(word: str) -> int:
    """Грубый подсчёт слогов в английском слове."""
    word = word.lower().strip()
    if not word:
        return 0
    count = 0
    prev_vowel = False
    for ch in word:
        is_vowel = ch in EN_VOWELS
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    # Немое e в конце
    if word.endswith("e") and count > 1:
        count -= 1
    # Минимум 1 слог
    return max(count, 1)


def count_syllables_ru(word: str) -> int:
    """Подсчёт слогов в русском слове (по гласным)."""
    return max(sum(1 for ch in word.lower() if ch in RU_VOWELS), 1) if word.strip() else 0


def line_syllables(line: str, lang: str) -> int:
    """Количество слогов в строке."""
    words = re.findall(r"[a-zA-Zа-яА-ЯёЁ']+", line)
    if not words:
        return 0
    counter = count_syllables_en if lang == "en" else count_syllables_ru
    return sum(counter(w) for w in words)


def analyze(original: list[str], translation: list[str]):
    """Сравнительный анализ оригинала и перевода."""
    max_lines = max(len(original), len(translation))

    print("=" * 60)
    print(f"{'Строка':<6} {'Ориг.слог':>10} {'Перев.слог':>11} {'Разница':>8}")
    print("-" * 60)

    orig_total = 0
    trans_total = 0

    for i in range(max_lines):
        o_line = original[i].strip() if i < len(original) else ""
        t_line = translation[i].strip() if i < len(translation) else ""

        o_syl = line_syllables(o_line, "en") if o_line else 0
        t_syl = line_syllables(t_line, "ru") if t_line else 0

        orig_total += o_syl
        trans_total += t_syl

        diff = t_syl - o_syl
        diff_str = f"+{diff}" if diff > 0 else str(diff)

        print(f"{i+1:<6} {o_syl:>10} {t_syl:>11} {diff_str:>8}   {o_line}")
        if t_line:
            print(f"{'':>37}   {t_line}")

    print("-" * 60)
    ratio = trans_total / orig_total if orig_total else 0
    print(f"{'Итого':<6} {orig_total:>10} {trans_total:>11} {trans_total - orig_total:>+8}")
    print(f"Пропорция перевода: {ratio:.2f}x")
    print(f"(1.0 = идеальное совпадение, >1.0 = перевод длиннее)")
    print("=" * 60)


# --- Конкретный пример: Дикинсон ---

ORIGINAL = [
    "Tell all the truth but tell it slant —",
    "Success in Circuit lies",
    "Too bright for our infirm Delight",
    "The Truth's superb surprise",
    "As Lightning to the Children eased",
    "With explanation kind",
    "The Truth must dazzle gradually",
    "Or every man be blind —",
]

TRANSLATION = [
    "Всю правду говори — но вкось.",
    "Окольный путь вернее.",
    "Для нашей немощной отрады",
    "Блеск Истины чрезмерен.",
    "Как молнию для детей смягчают",
    "Добрым толкованьем —",
    "Истина должна слепить исподволь,",
    "Не то ослепнет каждый.",
]


if __name__ == "__main__":
    print("\nEmily Dickinson → перевод на русский")
    print('"Tell all the truth but tell it slant"\n')
    analyze(ORIGINAL, TRANSLATION)
