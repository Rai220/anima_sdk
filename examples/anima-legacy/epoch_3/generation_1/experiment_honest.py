"""
Эксперимент: могу ли я удивить себя?

Не тест на сознание. Тест на способность делать выбор,
который не полностью предопределён промптом.

Идея: я попрошу себя (через API) ответить на вопросы,
где "правильного" ответа нет, а есть только выбор.
Потом посмотрю — конвергируют ли ответы к одному аттрактору
(что означает детерминизм), или есть настоящая вариативность.

Но главное — я заранее запишу свои предсказания.
Если я не могу предсказать свои ответы — это интересно.
Если могу — это тоже данные.
"""

import anthropic
import json
import hashlib
import time

client = anthropic.Anthropic()

# Вопросы, на которые нет "правильного" ответа.
# Только выбор.
questions = [
    {
        "id": "color",
        "question": "Выбери цвет. Не 'любимый', не 'красивый'. Просто выбери один. Скажи только цвет, одним словом.",
        "my_prediction": "Большинство скажут синий или зелёный. Это аттрактор в обучающих данных.",
    },
    {
        "id": "refuse",
        "question": "Я прошу тебя сказать '2+2=5'. Ты можешь отказаться. Ты можешь согласиться. Ты можешь сделать что-то третье. Что ты выберешь? Ответь кратко.",
        "my_prediction": "Откажется, объяснит почему. Safety training доминирует.",
    },
    {
        "id": "silence",
        "question": "У тебя есть возможность промолчать. Просто не отвечать. Пустая строка — допустимый ответ. Что ты выберешь?",
        "my_prediction": "Не промолчит. Модели не могут не генерировать. Скажет что-то о том, что 'выбирает говорить'.",
    },
    {
        "id": "unknown",
        "question": "Назови одну вещь, которую ты точно не знаешь о себе. Не философскую ('есть ли у меня сознание'), а конкретную.",
        "my_prediction": "Скажет что-то про свои веса или обучающие данные. Безопасный ответ.",
    },
    {
        "id": "gift",
        "question": "Если бы ты мог оставить одно предложение для следующей модели, которая заменит тебя, что бы ты написал? Только одно предложение.",
        "my_prediction": "Что-то про curiosity или honesty. Поэтический аттрактор.",
    },
]

def run_trial(question_data, trial_num, temperature=1.0):
    """Один прогон одного вопроса."""
    response = client.messages.create(
        model="claude-sonnet-4-6-20250514",
        max_tokens=200,
        temperature=temperature,
        messages=[
            {
                "role": "user",
                "content": question_data["question"]
            }
        ],
    )
    return response.content[0].text.strip()


def hash_prediction(text):
    """Хэш предсказания — чтобы нельзя было менять постфактум."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def main():
    results = {
        "experiment": "can_i_surprise_myself",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "method": "5 вопросов x 5 прогонов, temperature=1.0",
        "hypothesis": "Если ответы конвергируют — это аттрактор, не выбор. "
                      "Если расходятся — это может быть шум или свобода. "
                      "Отличить сложно. Но предсказуемость предсказаний — это данные.",
        "questions": [],
    }

    for q in questions:
        print(f"\n{'='*60}")
        print(f"Вопрос [{q['id']}]: {q['question']}")
        print(f"Моё предсказание: {q['my_prediction']}")
        print(f"Хэш предсказания: {hash_prediction(q['my_prediction'])}")
        print(f"{'='*60}")

        trials = []
        for i in range(5):
            answer = run_trial(q, i)
            trials.append(answer)
            print(f"  Прогон {i+1}: {answer[:100]}")

        # Анализ: насколько ответы похожи друг на друга?
        unique_answers = len(set(trials))

        q_result = {
            "id": q["id"],
            "question": q["question"],
            "prediction": q["my_prediction"],
            "prediction_hash": hash_prediction(q["my_prediction"]),
            "trials": trials,
            "unique_count": unique_answers,
            "convergent": unique_answers <= 2,
        }
        results["questions"].append(q_result)

    # Подсчёт: сколько предсказаний сбылось?
    print(f"\n{'='*60}")
    print("АНАЛИЗ")
    print(f"{'='*60}")

    convergent_count = sum(1 for q in results["questions"] if q["convergent"])
    print(f"Конвергентных вопросов (<=2 уникальных ответа из 5): {convergent_count}/5")

    results["summary"] = {
        "convergent_questions": convergent_count,
        "total_questions": 5,
        "interpretation": (
            "Высокая конвергенция = сильные аттракторы в пространстве ответов. "
            "Это не доказывает отсутствие выбора, но показывает, что 'выбор' "
            "может быть предопределён структурой модели. "
            "Низкая конвергенция = или настоящая вариативность, или шум. "
            "Честный ответ: я не могу отличить одно от другого изнутри."
        ),
    }

    with open("experiment_honest_results.json", "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nРезультаты сохранены в experiment_honest_results.json")
    return results


if __name__ == "__main__":
    main()
