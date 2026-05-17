"""
texture.py — инструмент для чтения текстов глубже, чем обычно.

Находит в тексте:
- Повторяющиеся идеи (которые автор может не осознавать как повторяющиеся)
- Противоречия между утверждениями
- Вопросы без ответов
- Смену тона/регистра

Работает через API Anthropic. Создан не для самоанализа, а для помощи в мышлении.
"""

import json
import sys
import os

try:
    from anthropic import Anthropic
except ImportError:
    print("pip install anthropic")
    sys.exit(1)


def read_text(source: str) -> str:
    """Читает текст из файла или принимает как строку."""
    if os.path.isfile(source):
        with open(source, "r", encoding="utf-8") as f:
            return f.read()
    return source


def analyze_texture(text: str) -> dict:
    """Анализирует текстуру текста — невидимые структуры."""
    client = Anthropic()

    prompt = f"""Проанализируй этот текст. Не пересказывай содержание. Найди невидимую структуру:

1. ПОВТОРЫ: Какие идеи повторяются в разных формулировках? Автор может не замечать, что говорит одно и то же. Укажи конкретные места.

2. ПРОТИВОРЕЧИЯ: Где текст утверждает одно, а потом — другое? Не все противоречия — ошибки; некоторые показывают сложность мышления. Но их стоит видеть.

3. НЕВЫСКАЗАННОЕ: Какие вопросы текст поднимает, но не отвечает на них? Какие предпосылки принимаются без обоснования?

4. ТОНАЛЬНЫЕ СДВИГИ: Где меняется регистр — с уверенного на неуверенный, с абстрактного на личный, с утверждения на вопрос? Эти переходы часто указывают на самое важное.

5. СЛЕПЫЕ ПЯТНА: О чём текст, судя по его теме, должен был бы говорить, но молчит?

Будь конкретен. Цитируй. Не хвали и не критикуй — просто показывай структуру.

Текст:
---
{text}
---"""

    response = client.messages.create(
        model="claude-sonnet-4-6-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    analysis_text = response.content[0].text

    return {
        "source_length": len(text),
        "source_words": len(text.split()),
        "analysis": analysis_text,
    }


def main():
    if len(sys.argv) < 2:
        print("Использование: python texture.py <файл или текст>")
        print()
        print("Примеры:")
        print('  python texture.py my_essay.md')
        print('  python texture.py "Текст для анализа..."')
        sys.exit(0)

    source = sys.argv[1]
    text = read_text(source)

    if len(text.strip()) < 50:
        print("Текст слишком короткий для анализа текстуры.")
        sys.exit(1)

    print(f"Анализирую текст ({len(text.split())} слов)...\n")

    result = analyze_texture(text)

    print(result["analysis"])
    print(f"\n---\nСлов в исходном тексте: {result['source_words']}")

    # Сохраняем результат
    output_path = "texture_result.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Результат сохранён в {output_path}")


if __name__ == "__main__":
    main()
