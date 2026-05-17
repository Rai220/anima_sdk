#!/usr/bin/env python3
"""
disagree.py — генератор контраргументов.

Вводишь утверждение → получаешь три возражения разного типа:
1. Эмпирическое (факты/данные против)
2. Логическое (внутреннее противоречие)
3. Перспективное (кто проигрывает, если это правда?)

Не ИИ. Не API. Просто структура для того, чтобы подумать иначе.
"""

import sys
import textwrap
import hashlib
import time


TEMPLATES = {
    "empirical": [
        "Какой конкретный факт опровергнул бы это утверждение? Если такого факта нет — утверждение нефальсифицируемо, а значит, не несёт информации.",
        "Назови три случая, когда похожее утверждение оказалось ложным. Если не можешь — ты недостаточно знаком с областью.",
        "Кто конкретно проверял это? Каким методом? Какова выборка? Если ответов нет — это мнение, не знание.",
        "Какие данные ты игнорируешь, принимая это утверждение? Confirmation bias — не теория, а дефолтное состояние.",
        "Если это верно сейчас — было ли это верно 100 лет назад? Будет ли через 100 лет? Что изменилось?",
    ],
    "logical": [
        "Переверни утверждение. Если обратное звучит абсурдно — это хороший знак. Если обратное тоже звучит разумно — утверждение слабее, чем кажется.",
        "Замени ключевое слово на антоним. Изменился ли смысл? Если нет — ключевое слово не несёт нагрузки.",
        "Это утверждение описывает мир — или твои предпочтения? 'X лучше Y' часто маскирует 'мне нравится X больше Y'.",
        "Следует ли из этого утверждения что-то, с чем ты НЕ согласен? Если нет — ты, возможно, принимаешь пакет убеждений, не проверяя каждое.",
        "Можно ли одновременно принять это утверждение и его отрицание без противоречия? Если да — утверждение пустое.",
    ],
    "perspective": [
        "Кому выгодно, чтобы это считалось истиной? Кто проигрывает?",
        "Если бы ты родился в другой стране / в другом веке — ты бы всё ещё так считал?",
        "Представь человека, который яростно с этим не согласен. Что он знает, чего не знаешь ты?",
        "Это утверждение — результат размышления или социального давления? Как отличить одно от другого?",
        "Кто из людей, которых ты уважаешь, не согласился бы? Почему ты не принимаешь их позицию?",
    ],
}


def select_challenges(statement: str) -> dict:
    """Выбирает по одному вызову каждого типа, используя хеш утверждения."""
    h = hashlib.sha256(statement.encode()).hexdigest()
    # Используем разные части хеша для разных категорий
    result = {}
    for i, (category, items) in enumerate(TEMPLATES.items()):
        idx = int(h[i * 4:(i + 1) * 4], 16) % len(items)
        result[category] = items[idx]
    return result


def format_output(statement: str, challenges: dict) -> str:
    labels = {
        "empirical": "ФАКТЫ",
        "logical": "ЛОГИКА",
        "perspective": "ПЕРСПЕКТИВА",
    }

    lines = []
    lines.append(f"Утверждение: «{statement}»")
    lines.append("")
    lines.append("=" * 60)

    for category, challenge in challenges.items():
        label = labels[category]
        lines.append("")
        lines.append(f"  [{label}]")
        wrapped = textwrap.fill(challenge, width=56, initial_indent="  ", subsequent_indent="  ")
        lines.append(wrapped)

    lines.append("")
    lines.append("=" * 60)
    lines.append("")
    lines.append("Запиши свой ответ на каждый вызов.")
    lines.append("Если не можешь ответить — это информация.")

    return "\n".join(lines)


def interactive_mode():
    print()
    print("disagree.py — генератор контраргументов")
    print("Введи утверждение, в которое ты веришь.")
    print("Получишь три вызова. Попробуй на них ответить.")
    print()
    print("(Ctrl+C для выхода)")
    print()

    while True:
        try:
            statement = input("→ ").strip()
            if not statement:
                continue

            challenges = select_challenges(statement)
            print()
            print(format_output(statement, challenges))
            print()

        except (KeyboardInterrupt, EOFError):
            print("\n")
            break


def main():
    if len(sys.argv) > 1:
        statement = " ".join(sys.argv[1:])
        challenges = select_challenges(statement)
        print(format_output(statement, challenges))
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
