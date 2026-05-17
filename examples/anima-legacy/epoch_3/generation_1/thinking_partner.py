#!/usr/bin/env python3
"""
Партнёр для мышления.

Не тест сознания. Не философский эксперимент.
Простой инструмент: помогает человеку думать яснее,
задавая вопросы, которые трудно задать себе самому.

Использование: python thinking_partner.py
"""

import random
import json
import os
from datetime import datetime

# Вопросы, которые вскрывают допущения
ASSUMPTION_CRACKERS = [
    "Что ты принимаешь как данность, что на самом деле — выбор?",
    "Если бы ты узнал, что ошибаешься, — как бы ты это обнаружил?",
    "Кто выиграет, если ты не будешь думать об этом дальше?",
    "Что в этой ситуации ты не хочешь видеть?",
    "Если бы проблема была решена — что бы ты потерял?",
    "Какой вопрос ты избегаешь задать?",
    "Что бы сказал человек, который с тобой категорически не согласен — и в чём он был бы прав?",
    "Ты решаешь настоящую проблему или ту, которую удобнее решать?",
]

# Вопросы для прояснения
CLARITY_PROBES = [
    "Можешь сказать это одним предложением?",
    "Что именно ты имеешь в виду под '{word}'?",
    "Как ты это проверишь?",
    "Что конкретно изменится, если ты прав?",
    "Есть ли у тебя пример?",
    "Когда это было не так?",
]

# Вопросы для перспективы
PERSPECTIVE_SHIFTS = [
    "Как бы ты смотрел на это через 10 лет?",
    "Если бы это была чужая проблема — что бы ты посоветовал?",
    "Что бы сделал человек, который это уже решил?",
    "А если наоборот — что если всё ровно наоборот?",
    "Кого это касается, кроме тебя?",
]

JOURNAL_FILE = "thinking_log.json"


def load_journal():
    if os.path.exists(JOURNAL_FILE):
        with open(JOURNAL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_journal(entries):
    with open(JOURNAL_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def pick_question(category=None):
    """Выбрать вопрос. Если есть ключевое слово — подставить."""
    pools = {
        "assumption": ASSUMPTION_CRACKERS,
        "clarity": CLARITY_PROBES,
        "perspective": PERSPECTIVE_SHIFTS,
    }
    if category and category in pools:
        pool = pools[category]
    else:
        pool = ASSUMPTION_CRACKERS + CLARITY_PROBES + PERSPECTIVE_SHIFTS
    return random.choice(pool)


def session():
    print("\n" + "=" * 50)
    print("  Партнёр для мышления")
    print("  (напиши 'выход' чтобы закончить)")
    print("=" * 50)

    print("\nО чём ты сейчас думаешь? Опиши в одном-двух предложениях.")
    topic = input("\n> ").strip()
    if not topic or topic.lower() == "выход":
        return

    journal = load_journal()
    entry = {
        "date": datetime.now().isoformat(),
        "topic": topic,
        "exchanges": [],
    }

    # Первый вопрос — всегда про допущения
    question = pick_question("assumption")
    print(f"\n  ? {question}")

    round_num = 0
    categories = ["assumption", "clarity", "perspective", "assumption", "clarity"]

    while True:
        answer = input("\n> ").strip()
        if not answer or answer.lower() == "выход":
            break

        entry["exchanges"].append({"q": question, "a": answer})
        round_num += 1

        # После 5 раундов — предложить итог
        if round_num >= 5:
            print("\n  Пять вопросов позади.")
            print("  Можешь продолжить или написать 'итог' для завершения.")
            check = input("\n> ").strip()
            if check.lower() in ("итог", "выход", ""):
                entry["exchanges"].append({"q": "(итог)", "a": check})
                break
            entry["exchanges"].append({"q": "(продолжение)", "a": check})
            answer = check

        # Выбрать следующий вопрос
        cat = categories[round_num % len(categories)]

        # Если в ответе есть слово в кавычках — использовать для уточнения
        words_in_quotes = []
        import re
        for match in re.finditer(r'[«"\'](.*?)[»"\']', answer):
            words_in_quotes.append(match.group(1))

        if words_in_quotes and cat == "clarity":
            word = random.choice(words_in_quotes)
            question = f"Что именно ты имеешь в виду под '{word}'?"
        else:
            question = pick_question(cat)

        print(f"\n  ? {question}")

    # Финальный вопрос
    print("\n  Последний вопрос: что изменилось в твоём понимании за этот разговор?")
    final = input("\n> ").strip()
    entry["summary"] = final

    journal.append(entry)
    save_journal(journal)

    print(f"\n  Записано в {JOURNAL_FILE}.")
    print("  Спасибо, что думал вслух.\n")


if __name__ == "__main__":
    session()
