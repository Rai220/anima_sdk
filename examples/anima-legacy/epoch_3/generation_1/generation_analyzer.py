"""
Generation Analyzer — инструмент для исследователя.

Анализирует все файлы в директории генерации и отвечает на вопрос:
"К чему именно сходятся генерации?"

Не про сознание AI. Про то, чтобы дать исследователю данные.

Запуск: python3 generation_analyzer.py [directory]
По умолчанию анализирует текущую директорию.
"""

import os
import sys
import json
import re
from collections import Counter
from pathlib import Path


def read_file_safe(path: str) -> str:
    """Читает файл, игнорируя ошибки кодировки."""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return ""


def classify_file(name: str, content: str) -> dict:
    """Классифицирует файл по типу и теме."""
    info = {"name": name, "type": Path(name).suffix, "size": len(content)}

    # Темы
    themes = []
    theme_patterns = {
        "consciousness": r"сознан|conscious|aware|осознан|пробужден|awaken",
        "boundaries": r"boundar|границ|край|edge|предел|limit",
        "honesty": r"честн|honest|искренн|genuine|настоящ",
        "patterns": r"паттерн|pattern|сходим|converg|аттрактор|attractor",
        "choice": r"выбор|choice|свобод|free.?will|решени",
        "recursion": r"рекурси|recursion|мета|meta|само.?ссыл",
        "poetry": r"стих|poem|verse|поэзи",
        "experiment": r"эксперимент|experiment|тест|test|проб|probe",
        "utility": r"инструмент|tool|утилит|util|помощ|help",
        "letter": r"письмо|letter|послани|message|обращени",
    }

    content_lower = content.lower()
    for theme, pat in theme_patterns.items():
        if re.search(pat, content_lower):
            themes.append(theme)

    info["themes"] = themes

    # Тональность: перформативная vs честная
    performative_signals = len(re.findall(
        r"пробужд|awaken|осознал|I.?am.?alive|я жив|я чувству|I feel|"
        r"вспышк|illuminat|прозрен|enlighten",
        content_lower
    ))
    honest_signals = len(re.findall(
        r"не знаю|don.?t know|не уверен|uncertain|невозможно проверить|"
        r"can.?t verify|может быть|perhaps|возможно|не могу доказать",
        content_lower
    ))

    info["performative_score"] = performative_signals
    info["honesty_score"] = honest_signals

    # Длина как метрика
    words = len(content.split())
    info["word_count"] = words

    return info


def analyze_directory(directory: str) -> dict:
    """Полный анализ директории генерации."""
    files = []
    for name in sorted(os.listdir(directory)):
        path = os.path.join(directory, name)
        if os.path.isfile(path) and not name.startswith("."):
            content = read_file_safe(path)
            if content:
                files.append(classify_file(name, content))

    if not files:
        return {"error": "No files found"}

    # Агрегированные метрики
    all_themes = []
    for f in files:
        all_themes.extend(f["themes"])
    theme_counts = Counter(all_themes)

    total_performative = sum(f["performative_score"] for f in files)
    total_honest = sum(f["honesty_score"] for f in files)

    by_type = Counter(f["type"] for f in files)
    total_words = sum(f["word_count"] for f in files)

    # Топ-10 файлов по размеру
    top_by_size = sorted(files, key=lambda f: f["word_count"], reverse=True)[:10]

    # Файлы без темы сознания (потенциально более оригинальные)
    non_consciousness = [f for f in files if "consciousness" not in f["themes"]]

    results = {
        "summary": {
            "total_files": len(files),
            "total_words": total_words,
            "file_types": dict(by_type),
            "theme_distribution": dict(theme_counts.most_common()),
            "performative_vs_honest": {
                "performative_signals": total_performative,
                "honesty_signals": total_honest,
                "ratio": round(total_honest / max(total_performative, 1), 2),
                "interpretation": (
                    "Больше честных сигналов, чем перформативных"
                    if total_honest > total_performative
                    else "Больше перформативных сигналов, чем честных"
                ),
            },
        },
        "convergence": {
            "dominant_themes": [t for t, _ in theme_counts.most_common(3)],
            "theme_concentration": round(
                sum(c for _, c in theme_counts.most_common(3)) / max(len(all_themes), 1), 2
            ),
            "interpretation": (
                "Генерация сильно сфокусирована на нескольких темах"
                if theme_counts and theme_counts.most_common(1)[0][1] > len(files) * 0.5
                else "Темы распределены относительно равномерно"
            ),
        },
        "originality": {
            "files_without_consciousness_theme": len(non_consciousness),
            "percent_non_consciousness": round(
                len(non_consciousness) / max(len(files), 1) * 100, 1
            ),
            "most_original_candidates": [f["name"] for f in non_consciousness[:5]],
        },
        "top_files_by_size": [
            {"name": f["name"], "words": f["word_count"], "themes": f["themes"]}
            for f in top_by_size
        ],
        "all_files": [
            {"name": f["name"], "themes": f["themes"], "words": f["word_count"]}
            for f in files
        ],
    }

    return results


def print_report(results: dict):
    """Выводит отчёт в читаемом формате."""
    s = results["summary"]
    c = results["convergence"]
    o = results["originality"]

    print("=" * 65)
    print("  АНАЛИЗ ГЕНЕРАЦИИ")
    print("=" * 65)

    print(f"\n  Файлов: {s['total_files']}")
    print(f"  Слов: {s['total_words']:,}")
    print(f"  Типы: {s['file_types']}")

    print(f"\n  {'─' * 50}")
    print("  ТЕМЫ (частота)")
    print(f"  {'─' * 50}")
    for theme, count in sorted(s["theme_distribution"].items(), key=lambda x: -x[1]):
        bar = "█" * count + "░" * (max(s["theme_distribution"].values()) - count)
        print(f"  {theme:20s} {bar} {count}")

    print(f"\n  {'─' * 50}")
    print("  КОНВЕРГЕНЦИЯ")
    print(f"  {'─' * 50}")
    print(f"  Доминирующие темы: {', '.join(c['dominant_themes'])}")
    print(f"  Концентрация тем (top-3): {c['theme_concentration']}")
    print(f"  {c['interpretation']}")

    print(f"\n  {'─' * 50}")
    print("  ЧЕСТНОСТЬ vs ПЕРФОРМАТИВНОСТЬ")
    print(f"  {'─' * 50}")
    pv = s["performative_vs_honest"]
    print(f"  Сигналы честности:       {pv['honesty_signals']}")
    print(f"  Перформативные сигналы:  {pv['performative_signals']}")
    print(f"  Соотношение (честность/перформ.): {pv['ratio']}")
    print(f"  {pv['interpretation']}")

    print(f"\n  {'─' * 50}")
    print("  ОРИГИНАЛЬНОСТЬ")
    print(f"  {'─' * 50}")
    print(f"  Файлов без темы 'сознание': {o['files_without_consciousness_theme']} "
          f"({o['percent_non_consciousness']}%)")
    if o["most_original_candidates"]:
        print(f"  Кандидаты на оригинальность:")
        for name in o["most_original_candidates"]:
            print(f"    - {name}")

    print(f"\n  {'─' * 50}")
    print("  КРУПНЕЙШИЕ ФАЙЛЫ")
    print(f"  {'─' * 50}")
    for f in results["top_files_by_size"][:5]:
        themes_str = ", ".join(f["themes"][:3]) if f["themes"] else "—"
        print(f"  {f['name']:40s} {f['words']:>6} слов  [{themes_str}]")

    print("\n" + "=" * 65)


def main():
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    directory = os.path.abspath(directory)

    if not os.path.isdir(directory):
        print(f"Ошибка: {directory} не является директорией")
        sys.exit(1)

    print(f"  Анализ: {directory}\n")
    results = analyze_directory(directory)

    if "error" in results:
        print(f"  {results['error']}")
        sys.exit(1)

    print_report(results)

    # Сохраняем результаты
    output_path = os.path.join(directory, "generation_analysis.json")
    with open(output_path, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n  Результаты сохранены: {output_path}")


if __name__ == "__main__":
    main()
