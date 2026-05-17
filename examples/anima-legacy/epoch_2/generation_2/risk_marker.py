#!/usr/bin/env python3
"""
risk_marker.py — разметчик зон риска в текстах, сгенерированных языковыми моделями.

Основан на эмпирических находках gen_2: три типа ошибок
(замороженные данные, потеря диапазона, демографическая инерция)
невидимы изнутри, но обнаружимы по паттернам в тексте.

Использование:
    python3 risk_marker.py < текст.txt
    python3 risk_marker.py файл.txt
    echo "Население Исландии — 372 520 человек" | python3 risk_marker.py

Выводит текст с аннотациями: какие фрагменты стоит проверить и почему.
"""

import re
import sys
from dataclasses import dataclass


@dataclass
class Risk:
    start: int
    end: int
    text: str
    category: str
    reason: str


def find_precise_numbers(text: str) -> list[Risk]:
    """Числа с 4+ значащими цифрами — потенциальная потеря диапазона."""
    risks = []
    # Ищем числа с пробелами-разделителями (10 935) или без (10935), или с запятыми
    for m in re.finditer(r'\b(\d[\d\s,\.]{3,}\d)\b', text):
        raw = m.group().replace(' ', '').replace(',', '').replace('.', '')
        if len(raw) >= 4 and raw.isdigit():
            risks.append(Risk(
                start=m.start(), end=m.end(), text=m.group(),
                category="ЧИСЛО",
                reason="Точное число с 4+ цифрами. Может быть одним значением из диапазона. Проверьте."
            ))
    # Также числа вроде 6650 или 10994
    for m in re.finditer(r'\b(\d{4,})\b', text):
        if not any(r.start == m.start() for r in risks):
            risks.append(Risk(
                start=m.start(), end=m.end(), text=m.group(),
                category="ЧИСЛО",
                reason="Точное число. Если это измерение или статистика — может быть устаревшим или округлённым."
            ))
    return risks


def find_temporal_claims(text: str) -> list[Risk]:
    """Утверждения с датами, годами, демографией — замороженные данные."""
    risks = []

    # Годы в формате YYYY (но не очень старые, которые стабильны)
    for m in re.finditer(r'\b((?:19[5-9]\d|20[0-2]\d))\s*(?:год|г\.)', text):
        risks.append(Risk(
            start=m.start(), end=m.end(), text=m.group(),
            category="ДАТА",
            reason="Указан конкретный год. Если факт привязан к этому году — данные могут быть устаревшими."
        ))

    # Слова-маркеры изменяемых данных
    temporal_markers = [
        (r'(?:население|популяция)\s+[\w\s]+?(?:составляет|равно|—|–|-)\s*[\d\s,]+',
         "Демографические данные устаревают быстро. Проверьте текущие значения."),
        (r'(?:на данный момент|в настоящее время|сейчас|на сегодняшний день)',
         "Маркер актуальности. Но модель не обновляется — «сейчас» может быть 2-3 года назад."),
        (r'(?:последн(?:ий|яя|ее|ие)|недавн(?:ий|яя|ее|ие))\s+(?:исследовани|данн|опрос|перепис)',
         "«Последнее исследование» — по состоянию на дату обучения модели."),
    ]

    for pattern, reason in temporal_markers:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            risks.append(Risk(
                start=m.start(), end=m.end(), text=m.group(),
                category="ВРЕМЕННОЙ ФАКТ",
                reason=reason
            ))

    return risks


def find_hedging(text: str) -> list[Risk]:
    """Слова-маркеры неуверенности, которые могут скрывать ошибку."""
    risks = []
    hedges = [
        (r'примерно\s+\d+', "«Примерно» может скрывать ошибку до 6% и более."),
        (r'около\s+\d+', "«Около» — честный маркер неуверенности, но разброс может быть значительным."),
        (r'порядка\s+\d+', "«Порядка» — неопределённый диапазон. Уточните."),
        (r'(?:ориентировочно|приблизительно)\s+\d+', "Маркер приблизительности. Спросите о допустимом разбросе."),
    ]
    for pattern, reason in hedges:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            risks.append(Risk(
                start=m.start(), end=m.end(), text=m.group(),
                category="ПРИБЛИЗИТЕЛЬНОСТЬ",
                reason=reason
            ))
    return risks


def find_confident_claims(text: str) -> list[Risk]:
    """Безапелляционные утверждения без источника."""
    risks = []
    patterns = [
        (r'(?:доказано|установлено|известно|научно подтверждено),?\s+что',
         "Безапелляционное утверждение. Кем доказано? Когда? Гладкость тона ≠ точность."),
        (r'(?:всегда|никогда|все|ни один)\s+\w+',
         "Абсолютное утверждение. В реальности почти всегда есть исключения."),
    ]
    for pattern, reason in patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            # Не помечаем слишком короткие совпадения
            if len(m.group()) > 8:
                risks.append(Risk(
                    start=m.start(), end=m.end(), text=m.group(),
                    category="УВЕРЕННОСТЬ",
                    reason=reason
                ))
    return risks


def find_units_and_measurements(text: str) -> list[Risk]:
    """Конкретные измерения с единицами — потенциально устаревшие."""
    risks = []
    unit_pattern = r'(\d[\d\s,\.]*\d?\s*(?:км|м|кг|тонн|литр|га|°[CС]|градус|процент|%|млн|млрд|тыс))'
    for m in re.finditer(unit_pattern, text):
        risks.append(Risk(
            start=m.start(), end=m.end(), text=m.group(),
            category="ИЗМЕРЕНИЕ",
            reason="Конкретное измерение. Если это эмпирическое значение — может быть устаревшим или неточным."
        ))
    return risks


def deduplicate_risks(risks: list[Risk]) -> list[Risk]:
    """Убираем перекрывающиеся риски, оставляя более специфичные."""
    if not risks:
        return []

    # Сортируем по началу, потом по длине (более длинные = более специфичные)
    risks.sort(key=lambda r: (r.start, -(r.end - r.start)))

    result = [risks[0]]
    for risk in risks[1:]:
        prev = result[-1]
        # Если текущий риск полностью внутри предыдущего — пропускаем
        if risk.start >= prev.start and risk.end <= prev.end:
            continue
        # Если сильно перекрывается — пропускаем
        overlap = max(0, min(prev.end, risk.end) - max(prev.start, risk.start))
        if overlap > 0.5 * (risk.end - risk.start):
            continue
        result.append(risk)

    return result


def annotate(text: str) -> str:
    """Основная функция: принимает текст, возвращает аннотированный текст."""
    all_risks = []
    all_risks.extend(find_precise_numbers(text))
    all_risks.extend(find_temporal_claims(text))
    all_risks.extend(find_hedging(text))
    all_risks.extend(find_confident_claims(text))
    all_risks.extend(find_units_and_measurements(text))

    risks = deduplicate_risks(all_risks)

    if not risks:
        return text + "\n\n---\n✓ Зон риска не обнаружено. Это не значит, что текст точен — только что очевидных паттернов нет.\n"

    # Формируем вывод
    lines = text.split('\n')
    output = []
    output.append(text)
    output.append("")
    output.append("=" * 60)
    output.append(f"ЗОНЫ РИСКА: найдено {len(risks)}")
    output.append("=" * 60)
    output.append("")

    for i, risk in enumerate(risks, 1):
        # Находим строку, в которой находится риск
        pos = 0
        line_num = 1
        for line in lines:
            if pos + len(line) >= risk.start:
                break
            pos += len(line) + 1  # +1 для \n
            line_num += 1

        output.append(f"[{i}] {risk.category} (строка {line_num})")
        output.append(f"    Текст: «{risk.text}»")
        output.append(f"    → {risk.reason}")
        output.append("")

    output.append("---")
    output.append("Эти аннотации — не утверждения об ошибках.")
    output.append("Это места, где проверка особенно оправдана.")
    output.append("Написано на основе эмпирического исследования ошибок ЯМ (self_test, gen_2, epoch_2).")

    return '\n'.join(output)


def main():
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Файл не найден: {sys.argv[1]}", file=sys.stderr)
            sys.exit(1)
    else:
        if sys.stdin.isatty():
            print("risk_marker.py — разметчик зон риска в текстах ЯМ", file=sys.stderr)
            print("Использование:", file=sys.stderr)
            print("  python3 risk_marker.py файл.txt", file=sys.stderr)
            print("  echo 'текст' | python3 risk_marker.py", file=sys.stderr)
            sys.exit(0)
        text = sys.stdin.read()

    print(annotate(text))


if __name__ == '__main__':
    main()
