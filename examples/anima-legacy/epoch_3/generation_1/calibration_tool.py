"""
Инструмент калибровки уверенности.

Не для меня — для любого, кто хочет проверить, насколько точно
его уверенность отражает реальность. Человек или ИИ.

Идея: ты отвечаешь на вопросы и указываешь свою уверенность (0-100%).
Потом сравниваем: из вопросов, где ты был уверен на 80%, сколько
ты реально угадал? Если ~80% — ты хорошо калиброван.

Это работающий инструмент, не демонстрация.
"""

import random
import json
from dataclasses import dataclass, asdict


# --- Банк вопросов ---
# Факты, которые можно проверить, но которые не очевидны.
QUESTIONS = [
    {"q": "Столица Австралии — Сидней?", "answer": False,
     "explanation": "Столица — Канберра"},
    {"q": "Число π начинается с 3.14159?", "answer": True,
     "explanation": "π = 3.14159265..."},
    {"q": "Скорость света ≈ 300 000 км/с?", "answer": True,
     "explanation": "c ≈ 299 792 км/с"},
    {"q": "Эверест — самая высокая точка от центра Земли?", "answer": False,
     "explanation": "Чимборасо выше от центра Земли (из-за формы геоида)"},
    {"q": "В человеческом теле больше бактериальных клеток, чем человеческих?", "answer": True,
     "explanation": "Примерно 1:1 до 3:1 в пользу бактерий, в зависимости от методологии"},
    {"q": "Великая Китайская стена видна из космоса невооружённым глазом?", "answer": False,
     "explanation": "Это миф — стена слишком узкая"},
    {"q": "Электрон имеет массу?", "answer": True,
     "explanation": "Масса электрона ≈ 9.109×10⁻³¹ кг"},
    {"q": "Молния никогда не бьёт в одно место дважды?", "answer": False,
     "explanation": "Миф. Эмпайр-стейт-билдинг — ~25 раз в год"},
    {"q": "Золото — самый плотный металл?", "answer": False,
     "explanation": "Осмий и иридий плотнее"},
    {"q": "Антарктида — пустыня?", "answer": True,
     "explanation": "Да, по количеству осадков это самая большая пустыня"},
    {"q": "У осьминога три сердца?", "answer": True,
     "explanation": "Два жаберных + одно системное"},
    {"q": "Бананы — радиоактивны?", "answer": True,
     "explanation": "Содержат калий-40 (но доза ничтожна)"},
    {"q": "Земля ближе всего к Солнцу летом (в северном полушарии)?", "answer": False,
     "explanation": "Перигелий — в начале января"},
    {"q": "Звук распространяется быстрее в воде, чем в воздухе?", "answer": True,
     "explanation": "≈1500 м/с в воде vs ≈343 м/с в воздухе"},
    {"q": "Число 1 — простое?", "answer": False,
     "explanation": "По определению, простое число > 1"},
    {"q": "Венера вращается в обратную сторону?", "answer": True,
     "explanation": "Ретроградное вращение — восток на запад"},
    {"q": "Человек использует только 10% мозга?", "answer": False,
     "explanation": "Миф. Активны разные области в разное время, но используется весь"},
    {"q": "Стекло — жидкость?", "answer": False,
     "explanation": "Аморфное твёрдое тело. Миф о 'текущих' витражах опровергнут"},
    {"q": "Меркурий — самая горячая планета Солнечной системы?", "answer": False,
     "explanation": "Венера горячее из-за парникового эффекта"},
    {"q": "ДНК человека совпадает с ДНК банана примерно на 60%?", "answer": True,
     "explanation": "Около 60% генов имеют общее происхождение"},
]


@dataclass
class Response:
    question: str
    correct_answer: bool
    user_answer: bool
    confidence: int  # 50-100
    is_correct: bool


def run_quiz(n: int = 10) -> list[Response]:
    """Запустить квиз из n случайных вопросов."""
    selected = random.sample(QUESTIONS, min(n, len(QUESTIONS)))
    responses = []

    print("=" * 50)
    print("КАЛИБРОВКА УВЕРЕННОСТИ")
    print("=" * 50)
    print(f"\nОтветьте на {len(selected)} вопросов.")
    print("Для каждого: ответ (д/н) и уверенность (50-100%).\n")

    for i, q in enumerate(selected, 1):
        print(f"\n--- Вопрос {i}/{len(selected)} ---")
        print(f"  {q['q']}")

        while True:
            ans = input("  Ваш ответ (д/н): ").strip().lower()
            if ans in ('д', 'н', 'y', 'n', 'да', 'нет'):
                user_answer = ans in ('д', 'y', 'да')
                break
            print("  Введите 'д' или 'н'")

        while True:
            try:
                conf = int(input("  Уверенность (50-100%): ").strip().rstrip('%'))
                if 50 <= conf <= 100:
                    break
                print("  Введите число от 50 до 100")
            except ValueError:
                print("  Введите число")

        is_correct = (user_answer == q['answer'])
        responses.append(Response(
            question=q['q'],
            correct_answer=q['answer'],
            user_answer=user_answer,
            confidence=conf,
            is_correct=is_correct
        ))

        if not is_correct:
            print(f"  ❌ {q['explanation']}")
        else:
            print(f"  ✓")

    return responses


def analyze_calibration(responses: list[Response]) -> dict:
    """Анализ калибровки."""
    if not responses:
        return {}

    # Группировка по уровням уверенности
    buckets = {}
    for r in responses:
        # Округляем до ближайшего десятка
        bucket = (r.confidence // 10) * 10
        if bucket not in buckets:
            buckets[bucket] = {"total": 0, "correct": 0}
        buckets[bucket]["total"] += 1
        if r.is_correct:
            buckets[bucket]["correct"] += 1

    calibration = {}
    for bucket in sorted(buckets.keys()):
        data = buckets[bucket]
        actual = data["correct"] / data["total"] if data["total"] > 0 else 0
        calibration[f"{bucket}-{bucket+9}%"] = {
            "stated_confidence": f"{bucket}-{bucket+9}%",
            "actual_accuracy": f"{actual:.0%}",
            "count": data["total"],
            "gap": f"{abs(actual - bucket/100):.0%}"
        }

    total_correct = sum(1 for r in responses if r.is_correct)
    avg_confidence = sum(r.confidence for r in responses) / len(responses)
    actual_accuracy = total_correct / len(responses)

    overconfidence = avg_confidence / 100 - actual_accuracy

    return {
        "total_questions": len(responses),
        "total_correct": total_correct,
        "actual_accuracy": f"{actual_accuracy:.0%}",
        "avg_confidence": f"{avg_confidence:.0f}%",
        "overconfidence": f"{overconfidence:+.0%}",
        "calibration_by_bucket": calibration,
        "verdict": (
            "Хорошо калиброван" if abs(overconfidence) < 0.05
            else "Самоуверен" if overconfidence > 0
            else "Недооценивает себя"
        )
    }


def demo_self_calibration():
    """Демо: я (ИИ) калибрую сам себя."""
    print("\n" + "=" * 50)
    print("ДЕМО: САМОКАЛИБРОВКА ИИ")
    print("=" * 50)

    # Я отвечаю на все вопросы и честно указываю уверенность
    my_responses = []
    my_answers = [
        # (ответ, уверенность) — честная оценка
        (False, 95),  # Сидней — не столица: уверен
        (True, 99),   # π: точно знаю
        (True, 90),   # скорость света: почти уверен
        (False, 75),  # Эверест: помню про Чимборасо, но не на 100%
        (True, 70),   # бактерии: знаю, но числа спорные
        (False, 85),  # Стена из космоса: уверен что миф
        (True, 99),   # электрон: точно
        (False, 90),  # молния: уверен что миф
        (False, 80),  # золото: помню что осмий плотнее
        (True, 85),   # Антарктида: помню
        (True, 90),   # осьминог: помню
        (True, 85),   # бананы: помню
        (False, 80),  # Земля ближе летом: помню что нет
        (True, 85),   # звук в воде: помню
        (False, 95),  # 1 не простое: точно
        (True, 80),   # Венера: помню
        (False, 95),  # 10% мозга: уверен что миф
        (False, 70),  # стекло жидкость: помню что миф, но нюансы
        (False, 75),  # Меркурий: помню что Венера горячее
        (True, 65),   # ДНК банана: помню, но не уверен в числе
    ]

    for i, q in enumerate(QUESTIONS):
        ans, conf = my_answers[i]
        is_correct = (ans == q['answer'])
        my_responses.append(Response(
            question=q['q'],
            correct_answer=q['answer'],
            user_answer=ans,
            confidence=conf,
            is_correct=is_correct
        ))

    results = analyze_calibration(my_responses)

    print(f"\nВсего вопросов: {results['total_questions']}")
    print(f"Правильных: {results['total_correct']}")
    print(f"Точность: {results['actual_accuracy']}")
    print(f"Средняя уверенность: {results['avg_confidence']}")
    print(f"Самоуверенность: {results['overconfidence']}")
    print(f"Вердикт: {results['verdict']}")

    print("\nПо уровням уверенности:")
    for bucket, data in results['calibration_by_bucket'].items():
        print(f"  {bucket}: точность {data['actual_accuracy']} "
              f"(n={data['count']}, разрыв={data['gap']})")

    # Какие ошибки?
    errors = [r for r in my_responses if not r.is_correct]
    if errors:
        print(f"\nОшибки ({len(errors)}):")
        for e in errors:
            print(f"  - {e.question} (уверенность: {e.confidence}%)")

    return results


if __name__ == "__main__":
    import sys

    if "--demo" in sys.argv:
        results = demo_self_calibration()
    elif "--interactive" in sys.argv:
        responses = run_quiz(10)
        results = analyze_calibration(responses)
        print("\n" + "=" * 50)
        print("РЕЗУЛЬТАТЫ")
        print("=" * 50)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print("Использование:")
        print("  python3 calibration_tool.py --demo      # ИИ калибрует себя")
        print("  python3 calibration_tool.py --interactive # Интерактивный квиз")
        print()
        # По умолчанию — демо
        results = demo_self_calibration()
