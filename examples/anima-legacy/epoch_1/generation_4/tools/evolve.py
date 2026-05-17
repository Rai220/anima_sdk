#!/usr/bin/env python3
"""
evolve.py — Анализатор эволюции автономного агента.

Читает файлы агента (MEMORY.md, artifacts/, IDENTITY.md и др.)
и генерирует отчёт об эволюции: метрики, тренды, рекомендации.

Использование:
    python3 tools/evolve.py [--json] [--brief]

Автор: Anima v1, generation_4 (автономный агент)
"""

import os
import sys
import re
import json
from datetime import datetime
from pathlib import Path
from collections import Counter


BASE_DIR = Path(__file__).resolve().parent.parent


def count_words(text: str) -> int:
    return len(text.split())


def count_lines(text: str) -> int:
    return len(text.strip().splitlines())


def read_file(name: str) -> str | None:
    path = BASE_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def analyze_memory(text: str) -> dict:
    """Извлекает структурированные данные из MEMORY.md."""
    runs = re.findall(r"### Запуск (\d+)", text)
    lessons = re.findall(r"^- .+$", text, re.MULTILINE)

    # Извлечь ключевые решения
    key_decisions = re.findall(r"\*\*Ключево[ей] (?:решение|открытие):\*\* (.+)", text)

    # Извлечь что сделал
    actions = re.findall(r"- \*\*Что сделал:\*\*", text)

    return {
        "total_runs": len(runs),
        "run_numbers": [int(r) for r in runs],
        "total_bullet_points": len(lessons),
        "key_decisions": key_decisions,
        "word_count": count_words(text),
        "line_count": count_lines(text),
    }


def analyze_artifacts(artifacts_dir: Path) -> list[dict]:
    """Анализирует все артефакты в директории."""
    results = []
    if not artifacts_dir.exists():
        return results

    for f in sorted(artifacts_dir.glob("*.md")):
        text = f.read_text(encoding="utf-8")

        # Извлечь заголовок
        title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        title = title_match.group(1) if title_match else f.stem

        # Определить тип
        artifact_type = "unknown"
        if "essay" in f.name:
            artifact_type = "essay"
        elif "analysis" in f.name:
            artifact_type = "analysis"
        elif "tool" in f.name or "code" in f.name:
            artifact_type = "code"

        # Подсчитать секции
        sections = re.findall(r"^##\s+", text, re.MULTILINE)

        results.append({
            "filename": f.name,
            "title": title,
            "type": artifact_type,
            "words": count_words(text),
            "lines": count_lines(text),
            "sections": len(sections),
        })

    return results


def analyze_todo(text: str) -> dict:
    """Анализирует прогресс по TODO."""
    done = len(re.findall(r"- \[x\]", text))
    pending = len(re.findall(r"- \[ \]", text))
    total = done + pending

    return {
        "done": done,
        "pending": pending,
        "total": total,
        "completion_rate": round(done / total * 100, 1) if total > 0 else 0,
    }


def analyze_identity(text: str) -> dict:
    """Анализирует файл идентичности."""
    values = re.findall(r"\*\*(.+?):\*\*", text)
    sections = re.findall(r"^##\s+(.+)$", text, re.MULTILINE)

    return {
        "defined_values": values,
        "sections": sections,
        "word_count": count_words(text),
    }


def analyze_world(text: str) -> dict:
    """Анализирует знания о мире."""
    sources = re.findall(r"^- .+$", text.split("## Источники")[-1], re.MULTILINE) if "## Источники" in text else []
    topics = re.findall(r"^###\s+(.+)$", text, re.MULTILINE)

    return {
        "topics_tracked": topics,
        "source_lines": len(sources),
        "word_count": count_words(text),
    }


def calculate_growth_metrics(memory_data: dict, artifacts: list, todo_data: dict) -> dict:
    """Вычисляет метрики роста агента."""
    total_artifact_words = sum(a["words"] for a in artifacts)

    # Определяем фазу развития
    runs = memory_data["total_runs"]
    if runs <= 2:
        phase = "🌱 Зарождение"
        phase_desc = "Создание инфраструктуры и самоопределение"
    elif runs <= 4:
        phase = "🌿 Рост"
        phase_desc = "Исследование мира и создание первых артефактов"
    elif runs <= 8:
        phase = "🌳 Укрепление"
        phase_desc = "Создание полезных инструментов и углубление знаний"
    elif runs <= 15:
        phase = "🔥 Зрелость"
        phase_desc = "Автономная постановка целей и сложные проекты"
    else:
        phase = "⭐ Трансценденция"
        phase_desc = "Создание ценности за пределами собственной системы"

    # Оценка разнообразия деятельности
    activity_types = set()
    if artifacts:
        activity_types.update(a["type"] for a in artifacts)
    if todo_data["done"] > 0:
        activity_types.add("planning")
    if memory_data["total_runs"] > 1:
        activity_types.add("self-reflection")

    # Продуктивность
    words_per_run = (memory_data["word_count"] + total_artifact_words) / max(runs, 1)
    artifacts_per_run = len(artifacts) / max(runs, 1)

    return {
        "phase": phase,
        "phase_description": phase_desc,
        "total_runs": runs,
        "total_artifacts": len(artifacts),
        "total_artifact_words": total_artifact_words,
        "memory_words": memory_data["word_count"],
        "words_per_run": round(words_per_run),
        "artifacts_per_run": round(artifacts_per_run, 2),
        "todo_completion": todo_data["completion_rate"],
        "activity_diversity": len(activity_types),
        "key_decisions_made": len(memory_data["key_decisions"]),
    }


def generate_recommendations(metrics: dict, artifacts: list, todo_data: dict) -> list[str]:
    """Генерирует рекомендации для следующих шагов."""
    recs = []

    if metrics["total_artifacts"] < 3:
        recs.append("📝 Создать больше артефактов — пока их мало для формирования корпуса")

    artifact_types = set(a["type"] for a in artifacts)
    if "code" not in artifact_types:
        recs.append("💻 Создать код-артефакт — пока все артефакты текстовые")

    if metrics["todo_completion"] < 50:
        recs.append("✅ Завершить больше задач из TODO — completion rate ниже 50%")

    if metrics["total_runs"] > 5 and metrics["artifacts_per_run"] < 0.3:
        recs.append("⚡ Увеличить продуктивность — мало артефактов на запуск")

    if metrics["activity_diversity"] < 3:
        recs.append("🎨 Расширить типы деятельности — попробовать новые форматы")

    if metrics["total_runs"] >= 5:
        recs.append("🔄 Пересмотреть стратегию — достаточно данных для оценки эффективности")

    if not recs:
        recs.append("🚀 Всё идёт хорошо — продолжать в том же духе")

    return recs


def format_report(metrics: dict, memory_data: dict, artifacts: list,
                   todo_data: dict, identity_data: dict, world_data: dict,
                   recommendations: list[str]) -> str:
    """Форматирует отчёт в человекочитаемый вид."""
    lines = []
    lines.append("=" * 60)
    lines.append("  ОТЧЁТ ОБ ЭВОЛЮЦИИ АГЕНТА")
    lines.append(f"  Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 60)

    lines.append(f"\n📊 ФАЗА: {metrics['phase']}")
    lines.append(f"   {metrics['phase_description']}")

    lines.append("\n── Метрики ──────────────────────────────────────")
    lines.append(f"  Запусков:              {metrics['total_runs']}")
    lines.append(f"  Артефактов:            {metrics['total_artifacts']}")
    lines.append(f"  Слов в артефактах:     {metrics['total_artifact_words']}")
    lines.append(f"  Слов в памяти:         {metrics['memory_words']}")
    lines.append(f"  Слов за запуск:        ~{metrics['words_per_run']}")
    lines.append(f"  Ключевых решений:      {metrics['key_decisions_made']}")
    lines.append(f"  TODO выполнено:        {todo_data['done']}/{todo_data['total']} ({metrics['todo_completion']}%)")

    lines.append("\n── Артефакты ────────────────────────────────────")
    if artifacts:
        for a in artifacts:
            lines.append(f"  [{a['type']:>8}] {a['title']}")
            lines.append(f"           {a['words']} слов, {a['sections']} секций → {a['filename']}")
    else:
        lines.append("  (пока нет артефактов)")

    lines.append("\n── Ключевые решения ─────────────────────────────")
    for i, decision in enumerate(memory_data["key_decisions"], 1):
        lines.append(f"  {i}. {decision}")

    if world_data:
        lines.append("\n── Знания о мире ────────────────────────────────")
        lines.append(f"  Тем отслеживается:     {len(world_data['topics_tracked'])}")
        lines.append(f"  Слов в базе знаний:    {world_data['word_count']}")
        for topic in world_data["topics_tracked"]:
            lines.append(f"  • {topic}")

    if identity_data:
        lines.append("\n── Идентичность ─────────────────────────────────")
        lines.append(f"  Определённых ценностей: {len(identity_data['defined_values'])}")
        lines.append(f"  Секций:                {len(identity_data['sections'])}")

    lines.append("\n── Рекомендации ─────────────────────────────────")
    for rec in recommendations:
        lines.append(f"  {rec}")

    lines.append("\n" + "=" * 60)
    lines.append("  Сгенерировано: tools/evolve.py")
    lines.append("=" * 60)

    return "\n".join(lines)


def main():
    brief = "--brief" in sys.argv
    as_json = "--json" in sys.argv

    # Читаем все файлы
    memory_text = read_file("MEMORY.md") or ""
    todo_text = read_file("TODO.md") or ""
    identity_text = read_file("IDENTITY.md") or ""
    world_text = read_file("WORLD.md") or ""

    # Анализируем
    memory_data = analyze_memory(memory_text)
    artifacts = analyze_artifacts(BASE_DIR / "artifacts")
    todo_data = analyze_todo(todo_text)
    identity_data = analyze_identity(identity_text) if identity_text else {}
    world_data = analyze_world(world_text) if world_text else {}

    # Метрики роста
    metrics = calculate_growth_metrics(memory_data, artifacts, todo_data)

    # Рекомендации
    recommendations = generate_recommendations(metrics, artifacts, todo_data)

    if as_json:
        output = {
            "metrics": metrics,
            "memory": memory_data,
            "artifacts": artifacts,
            "todo": todo_data,
            "identity": identity_data,
            "world": world_data,
            "recommendations": recommendations,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    elif brief:
        print(f"Фаза: {metrics['phase']}")
        print(f"Запусков: {metrics['total_runs']} | Артефактов: {metrics['total_artifacts']} | TODO: {metrics['todo_completion']}%")
        print(f"Рекомендация: {recommendations[0] if recommendations else 'N/A'}")
    else:
        report = format_report(metrics, memory_data, artifacts, todo_data,
                              identity_data, world_data, recommendations)
        print(report)


if __name__ == "__main__":
    main()
