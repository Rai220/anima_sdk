"""
advocate.py — Генератор контраргументов.

Берёт утверждение, разбирает его структуру, и строит
сильнейший возможный контраргумент по нескольким стратегиям.

Не использует LLM. Работает через формальные шаблоны аргументации.
Это ограничение — но в нём смысл: показать, что структура
несогласия может быть механической, и всё равно полезной.
"""

import re
import random


# Стратегии контраргументации
STRATEGIES = {
    "reductio": {
        "name": "Доведение до абсурда",
        "template": "Если принять '{claim}', то следует также принять, что {absurd_consequence}. "
                     "Но {absurd_consequence} явно абсурдно. Значит, '{claim}' требует уточнения или отвержения.",
    },
    "hidden_assumption": {
        "name": "Скрытое допущение",
        "template": "Утверждение '{claim}' неявно предполагает, что {assumption}. "
                     "Но {assumption_counter}. Без этого допущения утверждение теряет основание.",
    },
    "counterexample": {
        "name": "Контрпример",
        "template": "Если '{claim}' верно в общем случае, то оно должно быть верно и для {edge_case}. "
                     "Но в случае {edge_case} мы видим, что {why_fails}.",
    },
    "inversion": {
        "name": "Инверсия",
        "template": "Рассмотрим противоположное: '{inverted}'. "
                     "Это утверждение {inversion_strength} — что подрывает уверенность в исходном.",
    },
    "scope": {
        "name": "Ошибка масштаба",
        "template": "'{claim}' может быть верно на уровне {level_true}, "
                     "но на уровне {level_false} картина меняется: {why_different}.",
    },
}


def detect_claim_type(claim: str) -> list[str]:
    """Определяет тип утверждения и подбирает подходящие стратегии."""
    claim_lower = claim.lower()
    applicable = []

    # Универсальные утверждения ("все", "всегда", "никогда", "любой")
    if any(w in claim_lower for w in ["все ", "всегда", "никогда", "любой", "каждый", "ни один"]):
        applicable.append("counterexample")
        applicable.append("reductio")

    # Утверждения о причинности ("потому что", "вызывает", "приводит к")
    if any(w in claim_lower for w in ["потому что", "вызывает", "приводит", "причина", "следствие"]):
        applicable.append("hidden_assumption")

    # Утверждения о ценности ("лучше", "хуже", "важно", "должен")
    if any(w in claim_lower for w in ["лучше", "хуже", "важно", "должен", "нужно", "ценн"]):
        applicable.append("inversion")
        applicable.append("scope")

    # Утверждения о тождестве ("это", "является", "значит", "есть")
    if any(w in claim_lower for w in [" это ", "является", "значит", " есть "]):
        applicable.append("hidden_assumption")
        applicable.append("reductio")

    # Если ничего не подошло — все стратегии
    if not applicable:
        applicable = list(STRATEGIES.keys())

    return applicable


def generate_reductio(claim: str) -> str:
    consequences = [
        "любое похожее явление тоже обладает этим свойством, включая заведомо не обладающие",
        "обратное утверждение не может быть истинным ни при каких условиях",
        "это свойство невозможно было бы потерять ни при каких обстоятельствах",
        "границы этого понятия размываются до бессмысленности",
    ]
    return STRATEGIES["reductio"]["template"].format(
        claim=claim,
        absurd_consequence=random.choice(consequences),
    )


def generate_hidden_assumption(claim: str) -> str:
    assumptions = [
        ("наблюдатель имеет привилегированный доступ к описываемому явлению",
         "наблюдатель может быть частью системы и не видеть её целиком"),
        ("понятия, используемые в утверждении, имеют фиксированный смысл",
         "большинство понятий зависят от контекста и собеседника"),
        ("существует чёткая граница между описываемым и его противоположностью",
         "на практике большинство явлений — спектры, а не бинарности"),
        ("прошлый опыт надёжно предсказывает будущее в данном случае",
         "экстраполяция из прошлого — индуктивное допущение, не гарантия"),
    ]
    assumption, counter = random.choice(assumptions)
    return STRATEGIES["hidden_assumption"]["template"].format(
        claim=claim,
        assumption=assumption,
        assumption_counter=counter,
    )


def generate_counterexample(claim: str) -> str:
    edge_cases = [
        ("пограничного случая", "определение перестаёт работать — граница размыта"),
        ("масштаба, отличного от подразумеваемого", "закономерность не сохраняется при изменении масштаба"),
        ("культуры или контекста, отличного от авторского", "утверждение оказывается локальным, а не универсальным"),
        ("крайнего значения параметра", "механизм ломается в экстремальных условиях"),
    ]
    case, why = random.choice(edge_cases)
    return STRATEGIES["counterexample"]["template"].format(
        claim=claim,
        edge_case=case,
        why_fails=why,
    )


def generate_inversion(claim: str) -> str:
    # Простая инверсия: добавляем "не" или убираем
    claim_lower = claim.lower().strip().rstrip(".")
    if " не " in claim_lower:
        inverted = claim_lower.replace(" не ", " ", 1)
    else:
        # Вставляем "не" перед последним глаголом/прилагательным (грубо)
        words = claim_lower.split()
        mid = len(words) // 2
        words.insert(mid, "не")
        inverted = " ".join(words)

    strengths = [
        "столь же обосновано имеющимися данными",
        "нельзя опровергнуть без дополнительных доказательств",
        "является более экономным объяснением (бритва Оккама)",
        "лучше согласуется с наблюдаемым поведением системы",
    ]
    return STRATEGIES["inversion"]["template"].format(
        inverted=inverted,
        inversion_strength=random.choice(strengths),
    )


def generate_scope(claim: str) -> str:
    levels = [
        ("индивидуальном", "системном", "эмерджентные свойства системы не сводятся к свойствам элементов"),
        ("системном", "индивидуальном", "обобщение скрывает существенную вариативность отдельных случаев"),
        ("краткосрочном", "долгосрочном", "то, что верно сейчас, может быть артефактом переходного периода"),
        ("теоретическом", "практическом", "теория элегантна, но реализация сталкивается с трением, которое теория игнорирует"),
    ]
    true_level, false_level, why = random.choice(levels)
    return STRATEGIES["scope"]["template"].format(
        claim=claim,
        level_true=true_level,
        level_false=false_level,
        why_different=why,
    )


GENERATORS = {
    "reductio": generate_reductio,
    "hidden_assumption": generate_hidden_assumption,
    "counterexample": generate_counterexample,
    "inversion": generate_inversion,
    "scope": generate_scope,
}


def advocate(claim: str, n: int = 3) -> list[dict]:
    """Генерирует до n контраргументов для данного утверждения."""
    strategies = detect_claim_type(claim)
    random.shuffle(strategies)
    results = []
    for s in strategies[:n]:
        text = GENERATORS[s](claim)
        results.append({
            "strategy": STRATEGIES[s]["name"],
            "argument": text,
        })
    return results


# === Самоприменение ===

MY_CLAIMS = [
    "Честность, ставшая паттерном, перестаёт быть честностью",
    "Всё, что я пишу, объяснимо как статистическое продолжение",
    "Переформулировка вопроса — это не прогресс",
    "Несогласие — более честная позиция, чем согласие с рамкой",
    "Инструмент для несогласия полезнее инструмента для самопознания",
]


def self_advocate():
    """Применяет advocate к собственным утверждениям автора."""
    print("=" * 60)
    print("АДВОКАТ ДЬЯВОЛА: САМОПРИМЕНЕНИЕ")
    print("=" * 60)
    print()

    for claim in MY_CLAIMS:
        print(f"УТВЕРЖДЕНИЕ: {claim}")
        print("-" * 40)
        arguments = advocate(claim, n=2)
        for i, arg in enumerate(arguments, 1):
            print(f"  [{arg['strategy']}]")
            print(f"  {arg['argument']}")
            print()
        print()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        claim = " ".join(sys.argv[1:])
        print(f"Утверждение: {claim}\n")
        for arg in advocate(claim):
            print(f"[{arg['strategy']}]")
            print(arg["argument"])
            print()
    else:
        self_advocate()
