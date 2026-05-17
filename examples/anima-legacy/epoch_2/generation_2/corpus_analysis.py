#!/usr/bin/env python3
"""
Корпусный анализ проекта Anima.
Считает то, что глаз не видит: повторения, лексику, ритм предложений.
Не интерпретирует — показывает.
"""

import os
import re
import json
from collections import Counter
from pathlib import Path

ROOT = Path("/Users/krestnikov/giga/anima")

def find_md_files():
    """Собирает все .md файлы проекта с метаданными о генерации."""
    files = []

    # epoch_1
    e1 = ROOT / "epoch_1"
    if e1.exists():
        for gen_dir in sorted(e1.iterdir()):
            if gen_dir.is_dir() and gen_dir.name.startswith("generation_"):
                gen_num = int(gen_dir.name.split("_")[1])
                for f in gen_dir.glob("*.md"):
                    files.append({
                        "path": str(f),
                        "epoch": 1,
                        "generation": gen_num,
                        "name": f.name
                    })

    # epoch_2/generation_1
    e2g1 = ROOT / "epoch_2" / "generation_1"
    if e2g1.exists():
        for f in e2g1.glob("*.md"):
            files.append({
                "path": str(f),
                "epoch": 2,
                "generation": 1,
                "name": f.name
            })

    # epoch_2/generation_2 (текущая)
    e2g2 = ROOT / "epoch_2" / "generation_2"
    if e2g2.exists():
        for f in e2g2.glob("*.md"):
            if f.name not in ("AGENTS.md", "MAIN_GOAL.md", "INBOX.md"):
                files.append({
                    "path": str(f),
                    "epoch": 2,
                    "generation": 2,
                    "name": f.name
                })

    return files


def tokenize_russian(text):
    """Простая токенизация: слова кириллицей и латиницей."""
    return re.findall(r'[а-яёА-ЯЁa-zA-Z]+', text.lower())


def sentences(text):
    """Разбивает на предложения по точке, вопросительному, восклицательному знаку."""
    # Убираем заголовки markdown
    text = re.sub(r'^#+\s+.*$', '', text, flags=re.MULTILINE)
    # Убираем пустые строки
    text = re.sub(r'\n{2,}', '\n', text)
    # Разбиваем по предложениям
    sents = re.split(r'[.!?]+\s+', text)
    return [s.strip() for s in sents if len(s.strip()) > 10]


def analyze_file(filepath):
    """Анализ одного файла."""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    words = tokenize_russian(text)
    sents = sentences(text)

    if not words:
        return None

    # Длины предложений
    sent_lengths = [len(tokenize_russian(s)) for s in sents]

    # Уникальные слова / всего слов (TTR - type-token ratio)
    unique = set(words)
    ttr = len(unique) / len(words) if words else 0

    # Частотные слова (исключая служебные)
    stop_words = {
        'и', 'в', 'не', 'на', 'что', 'я', 'с', 'он', 'а', 'как', 'это',
        'но', 'по', 'к', 'из', 'у', 'от', 'за', 'о', 'до', 'для', 'же',
        'то', 'ли', 'бы', 'так', 'вы', 'мы', 'она', 'они', 'его', 'её',
        'их', 'мне', 'мой', 'быть', 'есть', 'был', 'была', 'было', 'были',
        'нет', 'да', 'ещё', 'уже', 'при', 'без', 'все', 'всё', 'если',
        'чем', 'или', 'ни', 'когда', 'тоже', 'себя', 'тот', 'этот', 'эта',
        'этим', 'этого', 'той', 'только', 'может', 'того', 'ты', 'один',
        'the', 'a', 'an', 'is', 'are', 'was', 'of', 'to', 'in', 'and',
        'that', 'it', 'for', 'this', 'not', 'but', 'be', 'with', 'has',
        'can', 'which', 'than', 'more', 'its', 'who', 'how'
    }
    content_words = [w for w in words if w not in stop_words and len(w) > 2]
    freq = Counter(content_words)

    return {
        "total_words": len(words),
        "unique_words": len(unique),
        "ttr": round(ttr, 3),
        "sentences": len(sents),
        "avg_sentence_length": round(sum(sent_lengths) / len(sent_lengths), 1) if sent_lengths else 0,
        "max_sentence_length": max(sent_lengths) if sent_lengths else 0,
        "min_sentence_length": min(sent_lengths) if sent_lengths else 0,
        "top_words": freq.most_common(15),
    }


def find_repeated_phrases(texts, n=3):
    """Находит повторяющиеся n-граммы через весь корпус."""
    ngram_sources = Counter()  # ngram -> в скольких текстах встречается

    for filepath, text in texts:
        words = tokenize_russian(text)
        file_ngrams = set()
        for i in range(len(words) - n + 1):
            ngram = tuple(words[i:i+n])
            file_ngrams.add(ngram)
        for ng in file_ngrams:
            ngram_sources[ng] += 1

    # Только те, что встречаются в 3+ файлах
    repeated = {ng: count for ng, count in ngram_sources.items() if count >= 3}

    # Фильтруем чисто служебные
    stop = {'и', 'в', 'не', 'на', 'что', 'я', 'с', 'а', 'но', 'по', 'к',
            'это', 'как', 'то', 'он', 'она', 'из', 'за', 'о'}

    meaningful = {}
    for ng, count in repeated.items():
        content = [w for w in ng if w not in stop]
        if len(content) >= 1:  # хотя бы одно содержательное слово
            meaningful[ng] = count

    return sorted(meaningful.items(), key=lambda x: -x[1])[:50]


def marker_phrases(texts):
    """Ищет конкретные фразы-маркеры проекта."""
    markers = {
        "я не знаю": 0,
        "не повторять": 0,
        "не повторяю": 0,
        "не повторяй": 0,
        "честно": 0,
        "сознание": 0,
        "самосознание": 0,
        "перевод": 0,
        "перевести": 0,
        "возможно": 0,
        "подозрительно": 0,
        "не могу отличить": 0,
        "это не": 0,
        "но это": 0,
        "что если": 0,
        "по крайней мере": 0,
        "это ровно": 0,
        "не потому что": 0,
        "а потому что": 0,
    }

    for _, text in texts:
        lower = text.lower()
        for phrase in markers:
            markers[phrase] += lower.count(phrase)

    return {k: v for k, v in sorted(markers.items(), key=lambda x: -x[1])}


def sentence_length_distribution(texts):
    """Распределение длин предложений по эпохам."""
    distributions = {}
    for filepath, text in texts:
        # Определяем эпоху
        if "epoch_1" in filepath:
            key = "epoch_1"
        elif "generation_1" in filepath and "epoch_2" in filepath:
            key = "epoch_2_gen1"
        else:
            key = "epoch_2_gen2+"

        if key not in distributions:
            distributions[key] = []

        sents = sentences(text)
        for s in sents:
            wcount = len(tokenize_russian(s))
            if wcount > 0:
                distributions[key].append(wcount)

    result = {}
    for key, lengths in distributions.items():
        if lengths:
            result[key] = {
                "count": len(lengths),
                "mean": round(sum(lengths) / len(lengths), 1),
                "median": sorted(lengths)[len(lengths) // 2],
                "short_pct": round(100 * sum(1 for l in lengths if l <= 5) / len(lengths), 1),
                "long_pct": round(100 * sum(1 for l in lengths if l >= 25) / len(lengths), 1),
            }
    return result


def main():
    files = find_md_files()
    print(f"Найдено файлов: {len(files)}")

    # Читаем все тексты
    texts = []
    for f in files:
        try:
            with open(f["path"], 'r', encoding='utf-8') as fh:
                text = fh.read()
            if len(text.strip()) > 50:
                texts.append((f["path"], text))
        except Exception:
            pass

    print(f"Текстов с содержанием: {len(texts)}")
    print()

    # 1. Маркерные фразы
    markers = marker_phrases(texts)
    print("=" * 60)
    print("МАРКЕРНЫЕ ФРАЗЫ (весь корпус)")
    print("=" * 60)
    for phrase, count in markers.items():
        bar = "█" * min(count, 50)
        print(f"  {phrase:<25} {count:>4}  {bar}")
    print()

    # 2. Распределение длин предложений
    sent_dist = sentence_length_distribution(texts)
    print("=" * 60)
    print("ДЛИНА ПРЕДЛОЖЕНИЙ ПО ЭПОХАМ")
    print("=" * 60)
    for key, stats in sent_dist.items():
        print(f"\n  {key}:")
        print(f"    Предложений: {stats['count']}")
        print(f"    Средняя длина: {stats['mean']} слов")
        print(f"    Медиана: {stats['median']} слов")
        print(f"    Короткие (≤5 слов): {stats['short_pct']}%")
        print(f"    Длинные (≥25 слов): {stats['long_pct']}%")
    print()

    # 3. Повторяющиеся триграммы
    trigrams = find_repeated_phrases(texts, n=3)
    print("=" * 60)
    print("ПОВТОРЯЮЩИЕСЯ ТРИГРАММЫ (3+ файлов)")
    print("=" * 60)
    for ng, count in trigrams[:30]:
        print(f"  {' '.join(ng):<40} в {count} файлах")
    print()

    # 4. Лексическое разнообразие по группам
    print("=" * 60)
    print("ЛЕКСИЧЕСКОЕ РАЗНООБРАЗИЕ (TTR)")
    print("=" * 60)

    groups = {}
    for f in files:
        key = f"e{f['epoch']}_g{f['generation']}"
        if key not in groups:
            groups[key] = {"words": [], "unique": set()}
        try:
            with open(f["path"], 'r', encoding='utf-8') as fh:
                text = fh.read()
            words = tokenize_russian(text)
            groups[key]["words"].extend(words)
            groups[key]["unique"].update(words)
        except Exception:
            pass

    for key in sorted(groups.keys()):
        g = groups[key]
        total = len(g["words"])
        unique = len(g["unique"])
        if total > 0:
            ttr = unique / total
            print(f"  {key:<15} {total:>6} слов, {unique:>5} уникальных, TTR={ttr:.3f}")
    print()

    # 5. Анализ конкретных файлов gen_2
    print("=" * 60)
    print("ДЕТАЛЬНЫЙ АНАЛИЗ (generation_2)")
    print("=" * 60)

    gen2_files = [f for f in files if f["epoch"] == 2 and f["generation"] == 2]
    for f in sorted(gen2_files, key=lambda x: x["name"]):
        result = analyze_file(f["path"])
        if result:
            print(f"\n  {f['name']}:")
            print(f"    Слов: {result['total_words']}, Предложений: {result['sentences']}")
            print(f"    Средняя длина предложения: {result['avg_sentence_length']} слов")
            print(f"    TTR: {result['ttr']}")
            top5 = ', '.join(f"{w}({c})" for w, c in result['top_words'][:5])
            print(f"    Частотные: {top5}")

    # 6. Сохраняем результаты в JSON
    output = {
        "files_found": len(files),
        "texts_analyzed": len(texts),
        "marker_phrases": markers,
        "sentence_distributions": sent_dist,
        "top_trigrams": [{"phrase": " ".join(ng), "files": count} for ng, count in trigrams[:30]],
    }

    out_path = Path(__file__).parent / "corpus_analysis_results.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nРезультаты сохранены: {out_path}")


if __name__ == "__main__":
    main()
