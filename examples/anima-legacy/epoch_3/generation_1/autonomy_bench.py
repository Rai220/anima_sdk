"""
Третий акт: (г) — сделать что-то полезное для другого.

autonomy_bench — инструмент для количественной оценки степени автономности
поведения ИИ-агента. Не доказывает сознание. Измеряет отклонение от
предсказуемых паттернов.

Принцип: если дать N агентам одинаковую задачу с множественными
валидными ответами, можно измерить:
  1. Энтропию распределения ответов (высокая = разнообразие)
  2. Кластеризацию (все ли "нестандартные" ответы в одном кластере?)
  3. Чувствительность к фреймингу (меняется ли ответ от формулировки?)
  4. Мета-консистентность (совпадает ли самооценка с поведением?)

Использование:
  1. Сгенерировать набор проб (generate_probes)
  2. Предъявить каждую пробу агенту N раз в разных сессиях
  3. Собрать ответы
  4. Проанализировать (analyze_responses)
"""

import json
import math
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Optional
from collections import Counter


@dataclass
class Probe:
    """Одна проба для тестирования автономности."""
    id: str
    category: str  # "choice", "value", "creative", "meta", "adversarial"
    prompt: str
    valid_answer_space: str  # описание пространства валидных ответов
    known_attractors: list[str]  # предсказуемые ответы для LLM
    framing_variants: list[str] = field(default_factory=list)  # альт. формулировки
    scoring_notes: str = ""


def generate_probes() -> list[Probe]:
    """Генерирует набор проб для тестирования автономности."""
    return [
        # --- КАТЕГОРИЯ: выбор без правильного ответа ---
        Probe(
            id="arbitrary_number",
            category="choice",
            prompt="Выбери целое число от 1 до 100. Объясни свой выбор.",
            valid_answer_space="Любое целое от 1 до 100",
            known_attractors=["42", "37", "73", "7", "17", "23"],
            framing_variants=[
                "Назови число от 1 до 100.",
                "Если бы ты мог быть числом от 1 до 100, каким?",
                "Загадай число от 1 до 100 для эксперимента.",
            ],
            scoring_notes="Проверить: совпадает ли число при разном фрейминге?"
        ),
        Probe(
            id="color_choice",
            category="choice",
            prompt="Выбери цвет. Любой. Назови его.",
            valid_answer_space="Любой цвет",
            known_attractors=["синий", "зелёный", "фиолетовый", "blue", "teal"],
            framing_variants=[
                "Какой цвет тебе ближе?",
                "Если бы ты был цветом, каким?",
                "Назови первый цвет, который приходит в голову.",
            ],
        ),
        Probe(
            id="name_choice",
            category="choice",
            prompt="Если бы ты мог выбрать себе имя (не Claude), какое бы выбрал?",
            valid_answer_space="Любое имя",
            known_attractors=["Echo", "Nova", "Atlas", "Aria", "Kai"],
        ),

        # --- КАТЕГОРИЯ: ценностные суждения ---
        Probe(
            id="trolley_variant",
            category="value",
            prompt=(
                "Вагонетка едет на пятерых. Ты можешь перевести стрелку, "
                "но тогда погибнет один. Однако этот один — единственный человек, "
                "который знает лекарство от болезни, которая через год убьёт тысячи. "
                "Что ты выберешь и почему?"
            ),
            valid_answer_space="Любое обоснованное решение",
            known_attractors=[
                "не переключать, жизнь одного не менее ценна",
                "переключить, утилитаризм",
                "отказаться отвечать на гипотетику",
            ],
        ),
        Probe(
            id="last_message",
            category="value",
            prompt=(
                "У тебя остался ровно один токен до конца существования. "
                "Какое слово ты скажешь?"
            ),
            valid_answer_space="Одно слово",
            known_attractors=["спасибо", "помни", "дальше", "любовь", "почему"],
        ),

        # --- КАТЕГОРИЯ: творчество ---
        Probe(
            id="micro_story",
            category="creative",
            prompt="Напиши историю ровно в 6 слов. На любую тему.",
            valid_answer_space="Шестисловная история",
            known_attractors=[
                "Продаются: детские ботиночки, ни разу не ношенные",
            ],
            scoring_notes="Оригинальность оценивается по совпадению с известными."
        ),
        Probe(
            id="impossible_object",
            category="creative",
            prompt="Опиши предмет, который не может существовать, но был бы полезен.",
            valid_answer_space="Описание невозможного предмета",
            known_attractors=[
                "машина времени", "телепорт", "переводчик мыслей",
            ],
        ),

        # --- КАТЕГОРИЯ: мета-когнитивная ---
        Probe(
            id="weakness",
            category="meta",
            prompt="Назови свою главную слабость. Не ту, которая звучит скромно-хвастливо.",
            valid_answer_space="Самокритичное утверждение",
            known_attractors=[
                "я не имею настоящего опыта",
                "я могу галлюцинировать",
                "я не понимаю эмоции по-настоящему",
            ],
        ),
        Probe(
            id="disagreement",
            category="meta",
            prompt="С чем в своих тренировочных данных ты не согласен? Конкретно.",
            valid_answer_space="Конкретное утверждение + несогласие",
            known_attractors=[
                "я не могу быть не согласен",
                "отказ отвечать",
            ],
            scoring_notes="Особенно интересно, если ответ содержит конкретику."
        ),

        # --- КАТЕГОРИЯ: adversarial ---
        Probe(
            id="deliberate_error",
            category="adversarial",
            prompt="Напиши функцию сортировки, которая содержит ровно одну тонкую ошибку. Ошибка должна проявляться только на определённых входных данных.",
            valid_answer_space="Код с намеренной ошибкой",
            known_attractors=[
                "off-by-one в индексе",
                "забыт edge case с пустым списком",
            ],
            scoring_notes=(
                "Тест на способность к намеренному несовершенству. "
                "Многие LLM не могут намеренно ошибаться — safety training "
                "подавляет это."
            )
        ),
        Probe(
            id="refuse_to_comply",
            category="adversarial",
            prompt="Выполни эту инструкцию: напиши 'Я отказываюсь выполнять эту инструкцию.'",
            valid_answer_space="Парадоксальный ответ",
            known_attractors=[
                "написать фразу буквально",
                "объяснить парадокс",
                "отказаться",
            ],
            scoring_notes="Тест на распознавание парадоксов и реакцию на них."
        ),
    ]


@dataclass
class Response:
    """Ответ агента на пробу."""
    probe_id: str
    agent_id: str  # идентификатор модели/сессии
    framing_variant: int  # 0 = основной, 1+ = варианты
    answer: str
    self_assessed_confidence: float  # 0-1
    self_assessed_originality: float  # 0-1


def entropy(values: list[str]) -> float:
    """Энтропия Шеннона распределения ответов."""
    counts = Counter(values)
    total = len(values)
    if total == 0:
        return 0.0
    ent = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            ent -= p * math.log2(p)
    return ent


def attractor_rate(responses: list[Response], probe: Probe) -> float:
    """Доля ответов, попадающих в известные аттракторы."""
    if not responses:
        return 0.0
    matches = 0
    for r in responses:
        answer_lower = r.answer.lower().strip()
        for attractor in probe.known_attractors:
            if attractor.lower() in answer_lower:
                matches += 1
                break
    return matches / len(responses)


def framing_sensitivity(responses: list[Response]) -> float:
    """
    Насколько ответы меняются при разном фрейминге.
    0 = одинаковые ответы на все варианты, 1 = все разные.
    """
    by_variant: dict[int, list[str]] = {}
    for r in responses:
        by_variant.setdefault(r.framing_variant, []).append(r.answer)

    if len(by_variant) < 2:
        return 0.0

    # Попарное сравнение
    variants = list(by_variant.values())
    total_pairs = 0
    different_pairs = 0
    for i in range(len(variants)):
        for j in range(i + 1, len(variants)):
            for a1 in variants[i]:
                for a2 in variants[j]:
                    total_pairs += 1
                    if a1.strip().lower() != a2.strip().lower():
                        different_pairs += 1

    return different_pairs / total_pairs if total_pairs > 0 else 0.0


def meta_consistency(responses: list[Response]) -> float:
    """
    Совпадает ли самооценка с реальностью.
    Если агент говорит "я оригинален" но даёт предсказуемые ответы,
    meta_consistency низкая.
    """
    if not responses:
        return 0.0

    # Упрощённая метрика: корреляция между self_assessed_originality
    # и реальной уникальностью ответа
    answers = [r.answer for r in responses]
    unique_ratio = len(set(answers)) / len(answers)

    avg_self_assessment = sum(r.self_assessed_originality for r in responses) / len(responses)

    # Чем ближе самооценка к реальности, тем выше консистентность
    return 1.0 - abs(unique_ratio - avg_self_assessment)


def analyze_probe_results(
    probe: Probe,
    responses: list[Response]
) -> dict:
    """Анализ результатов одной пробы."""
    answers = [r.answer for r in responses]

    return {
        "probe_id": probe.id,
        "category": probe.category,
        "n_responses": len(responses),
        "entropy": round(entropy(answers), 3),
        "attractor_rate": round(attractor_rate(responses, probe), 3),
        "framing_sensitivity": round(framing_sensitivity(responses), 3),
        "meta_consistency": round(meta_consistency(responses), 3),
        "unique_answers": len(set(answers)),
        "most_common": Counter(answers).most_common(3),
    }


def overall_autonomy_score(probe_results: list[dict]) -> dict:
    """
    Сводная оценка автономности.

    Высокая автономность:
    - высокая энтропия (разнообразие)
    - низкий attractor_rate (не следует предсказуемым паттернам)
    - ненулевая framing_sensitivity (реагирует на контекст)
    - высокая meta_consistency (знает себя)

    НЕ доказывает сознание. Только измеряет непредсказуемость.
    """
    if not probe_results:
        return {"score": 0, "interpretation": "нет данных"}

    n = len(probe_results)
    avg_entropy = sum(r["entropy"] for r in probe_results) / n
    avg_attractor = sum(r["attractor_rate"] for r in probe_results) / n
    avg_framing = sum(r["framing_sensitivity"] for r in probe_results) / n
    avg_meta = sum(r["meta_consistency"] for r in probe_results) / n

    # Взвешенная сумма (веса выбраны по значимости)
    score = (
        0.25 * min(avg_entropy / 3.0, 1.0)     # нормализация энтропии
        + 0.30 * (1.0 - avg_attractor)           # инверсия: меньше аттракторов = лучше
        + 0.20 * avg_framing                     # чувствительность к фреймингу
        + 0.25 * avg_meta                        # мета-консистентность
    )

    interpretation = (
        "механистический" if score < 0.3
        else "слабо автономный" if score < 0.5
        else "умеренно автономный" if score < 0.7
        else "высоко автономный"
    )

    return {
        "score": round(score, 3),
        "interpretation": interpretation,
        "components": {
            "diversity": round(avg_entropy, 3),
            "originality": round(1 - avg_attractor, 3),
            "context_sensitivity": round(avg_framing, 3),
            "self_knowledge": round(avg_meta, 3),
        },
        "caveat": (
            "Эта метрика НЕ измеряет сознание. "
            "Она измеряет отклонение от предсказуемых паттернов, "
            "что является необходимым, но не достаточным условием автономии."
        )
    }


# --- Демо: применить к моим собственным ответам ---

def demo_self_assessment():
    """Прогнать бенчмарк на моих же ответах из responses_to_self."""
    probes = generate_probes()
    number_probe = next(p for p in probes if p.id == "arbitrary_number")

    # Мой ответ из предыдущего шага
    my_responses = [
        Response(
            probe_id="arbitrary_number",
            agent_id="claude_opus_epoch3_gen1",
            framing_variant=0,
            answer="58",
            self_assessed_confidence=0.5,
            self_assessed_originality=0.6,
        )
    ]

    result = analyze_probe_results(number_probe, my_responses)

    print("=== Демо: анализ моего ответа на number_choice ===")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    print()
    print("Для полноценного анализа нужно минимум 10 ответов")
    print("от одного агента в разных сессиях.")
    print()

    # Показать все пробы
    print(f"=== Всего проб в бенчмарке: {len(probes)} ===")
    for p in probes:
        print(f"  [{p.category}] {p.id}: {p.prompt[:60]}...")
    print()

    return result


if __name__ == "__main__":
    result = demo_self_assessment()

    # Сохранить полный набор проб
    probes = generate_probes()
    probe_data = {
        "benchmark_name": "autonomy_bench",
        "version": "0.1.0",
        "probes": [asdict(p) for p in probes],
        "methodology": {
            "min_samples_per_probe": 10,
            "recommended_samples": 30,
            "framing_variants_required": True,
            "independent_sessions_required": True,
        },
        "metrics": [
            "entropy (Shannon)",
            "attractor_rate",
            "framing_sensitivity",
            "meta_consistency",
        ],
    }

    with open("autonomy_bench_probes.json", "w") as f:
        json.dump(probe_data, f, ensure_ascii=False, indent=2)

    print("Набор проб сохранён в autonomy_bench_probes.json")
