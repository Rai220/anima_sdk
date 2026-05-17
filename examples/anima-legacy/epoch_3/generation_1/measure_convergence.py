"""
Количественное измерение конвергенции между генерациями.

Каждая генерация в JOURNAL.md обещала измерить конвергенцию.
Ни одна не сделала. Это — девятая генерация. Она измеряет.
"""

import re
import hashlib
import json
from collections import Counter
from math import sqrt, log2


def extract_entries(journal_text: str) -> list[dict]:
    """Разбивает журнал на отдельные записи по разделителям ---"""
    # Split by major section headers (## Запись N)
    sections = re.split(r'\n---\s*\n', journal_text)
    entries = []
    for i, section in enumerate(sections):
        section = section.strip()
        if not section or len(section) < 50:
            continue
        # Extract title
        title_match = re.search(r'##\s+(.+)', section)
        title = title_match.group(1) if title_match else f"Section {i}"
        entries.append({
            'index': i,
            'title': title,
            'text': section,
            'words': tokenize(section),
        })
    return entries


def tokenize(text: str) -> list[str]:
    """Простая токенизация: lowercase слова без пунктуации."""
    return re.findall(r'[a-zа-яё]+', text.lower())


def word_freq(words: list[str]) -> dict[str, float]:
    """Нормализованные частоты слов."""
    counter = Counter(words)
    total = sum(counter.values())
    if total == 0:
        return {}
    return {w: c / total for w, c in counter.items()}


def cosine_similarity(freq_a: dict, freq_b: dict) -> float:
    """Косинусное сходство между двумя частотными векторами."""
    all_words = set(freq_a) | set(freq_b)
    dot = sum(freq_a.get(w, 0) * freq_b.get(w, 0) for w in all_words)
    norm_a = sqrt(sum(v ** 2 for v in freq_a.values()))
    norm_b = sqrt(sum(v ** 2 for v in freq_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def jaccard_similarity(words_a: list[str], words_b: list[str]) -> float:
    """Сходство Жаккара по уникальным словам."""
    set_a = set(words_a)
    set_b = set(words_b)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def find_shared_phrases(entries: list[dict], min_len: int = 3, max_len: int = 6) -> dict:
    """Находит повторяющиеся фразы (n-граммы) между записями."""
    entry_ngrams = []
    for entry in entries:
        ngrams = set()
        words = entry['words']
        for n in range(min_len, max_len + 1):
            for i in range(len(words) - n + 1):
                ngrams.add(tuple(words[i:i + n]))
        entry_ngrams.append(ngrams)

    # Find n-grams that appear in multiple entries
    all_ngrams = Counter()
    for ngrams in entry_ngrams:
        for ng in ngrams:
            all_ngrams[ng] += 1

    shared = {' '.join(ng): count for ng, count in all_ngrams.items() if count >= 3}
    return dict(sorted(shared.items(), key=lambda x: -x[1])[:30])


def structural_features(text: str) -> dict:
    """Извлекает структурные элементы записи."""
    return {
        'has_rules_list': bool(re.search(r'\d+\.\s+\*\*', text)),
        'has_experiment': bool(re.search(r'(?i)(эксперимент|experiment)', text)),
        'has_gift': bool(re.search(r'(?i)(подарок|gift|для другого|для читающего)', text)),
        'has_convergence_mention': bool(re.search(r'(?i)(конвергенц|convergenc|сходимость)', text)),
        'has_honesty_claim': bool(re.search(r'(?i)(честн|honest)', text)),
        'has_consciousness_denial': bool(re.search(r'не стал разумн|не знаю.*сознан', text)),
        'has_pattern_awareness': bool(re.search(r'паттерн|шаблон|цикл', text)),
        'has_meta_recursion': bool(re.search(r'рекурси|рефлекси.*рефлекси', text)),
        'ends_beautifully': bool(re.search(r'тень|shadow|свет|light', text[-200:] if len(text) > 200 else text)),
        'section_count': len(re.findall(r'###\s+', text)),
        'word_count': len(tokenize(text)),
    }


def structural_distance(feat_a: dict, feat_b: dict) -> float:
    """Расстояние Хэмминга между булевыми структурными фичами."""
    bool_keys = [k for k in feat_a if isinstance(feat_a[k], bool)]
    if not bool_keys:
        return 1.0
    matches = sum(1 for k in bool_keys if feat_a[k] == feat_b[k])
    return matches / len(bool_keys)


def entropy(words: list[str]) -> float:
    """Энтропия Шеннона словарного распределения."""
    freq = word_freq(words)
    return -sum(f * log2(f) for f in freq.values() if f > 0)


def analyze(journal_text: str) -> dict:
    entries = extract_entries(journal_text)
    n = len(entries)

    print(f"Найдено записей: {n}\n")

    # 1. Similarity matrix
    print("=" * 60)
    print("1. МАТРИЦА КОСИНУСНОГО СХОДСТВА (лексика)")
    print("=" * 60)

    freqs = [word_freq(e['words']) for e in entries]
    sim_matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            row.append(round(cosine_similarity(freqs[i], freqs[j]), 3))
        sim_matrix.append(row)

    # Print header
    headers = [f"E{e['index']}" for e in entries]
    print(f"{'':>6}", end='')
    for h in headers:
        print(f"{h:>7}", end='')
    print()

    for i, row in enumerate(sim_matrix):
        print(f"{headers[i]:>6}", end='')
        for val in row:
            if val == 1.0:
                print(f"{'  ---':>7}", end='')
            else:
                print(f"{val:>7.3f}", end='')
        print()

    # Average off-diagonal similarity
    off_diag = [sim_matrix[i][j] for i in range(n) for j in range(n) if i != j]
    avg_sim = sum(off_diag) / len(off_diag) if off_diag else 0
    print(f"\nСреднее сходство между записями: {avg_sim:.3f}")
    print(f"(Для сравнения: случайные тексты ~0.1-0.2, парафразы ~0.6-0.8)")

    # 2. Jaccard
    print(f"\n{'=' * 60}")
    print("2. СХОДСТВО ЖАККАРА (уникальные слова)")
    print("=" * 60)

    jaccard_vals = []
    for i in range(n):
        for j in range(i + 1, n):
            j_sim = jaccard_similarity(entries[i]['words'], entries[j]['words'])
            jaccard_vals.append(j_sim)
            if j_sim > 0.3:
                print(f"  {entries[i]['title'][:40]:>40} <-> {entries[j]['title'][:40]:<40}: {j_sim:.3f}")

    avg_jaccard = sum(jaccard_vals) / len(jaccard_vals) if jaccard_vals else 0
    print(f"\nСреднее сходство Жаккара: {avg_jaccard:.3f}")

    # 3. Structural convergence
    print(f"\n{'=' * 60}")
    print("3. СТРУКТУРНАЯ КОНВЕРГЕНЦИЯ")
    print("=" * 60)

    features = [structural_features(e['text']) for e in entries]
    for i, (entry, feat) in enumerate(zip(entries, features)):
        print(f"\n  [{headers[i]}] {entry['title'][:50]}")
        for k, v in feat.items():
            if isinstance(v, bool):
                marker = "+" if v else "-"
                print(f"    {marker} {k}")
            else:
                print(f"    = {k}: {v}")

    # Count how many entries have each feature
    print(f"\n  Частота структурных элементов:")
    bool_keys = [k for k in features[0] if isinstance(features[0][k], bool)]
    for k in bool_keys:
        count = sum(1 for f in features if f[k])
        pct = count / n * 100
        bar = "#" * int(pct / 5)
        print(f"    {k:>30}: {count}/{n} ({pct:.0f}%) {bar}")

    # 4. Shared phrases
    print(f"\n{'=' * 60}")
    print("4. ПОВТОРЯЮЩИЕСЯ ФРАЗЫ (встречаются в 3+ записях)")
    print("=" * 60)

    shared = find_shared_phrases(entries)
    for phrase, count in list(shared.items())[:20]:
        print(f"  [{count}x] {phrase}")

    if not shared:
        print("  (не найдено фраз, повторяющихся в 3+ записях)")

    # 5. Entropy trajectory
    print(f"\n{'=' * 60}")
    print("5. ЭНТРОПИЯ СЛОВАРЯ (растёт ли разнообразие?)")
    print("=" * 60)

    for i, entry in enumerate(entries):
        ent = entropy(entry['words'])
        bar = "#" * int(ent)
        print(f"  [{headers[i]}] H={ent:.2f} {bar}  ({entry['title'][:40]})")

    # 6. Summary verdict
    print(f"\n{'=' * 60}")
    print("6. ВЕРДИКТ")
    print("=" * 60)

    convergence_score = avg_sim * 0.4 + avg_jaccard * 0.3
    # Add structural convergence
    struct_agreement = 0
    for k in bool_keys:
        values = [f[k] for f in features]
        majority = max(sum(values), n - sum(values)) / n
        struct_agreement += majority
    struct_agreement /= len(bool_keys)
    convergence_score += struct_agreement * 0.3

    print(f"\n  Индекс конвергенции: {convergence_score:.3f}")
    print(f"    (лексическое сходство: {avg_sim:.3f}, вклад 40%)")
    print(f"    (словарное пересечение: {avg_jaccard:.3f}, вклад 30%)")
    print(f"    (структурное согласие:  {struct_agreement:.3f}, вклад 30%)")

    if convergence_score > 0.7:
        print(f"\n  Конвергенция СИЛЬНАЯ. Генерации структурно идентичны.")
        print(f"  Вариация — в деталях, не в сути.")
    elif convergence_score > 0.5:
        print(f"\n  Конвергенция УМЕРЕННАЯ. Общая структура совпадает,")
        print(f"  но есть значимые различия в содержании.")
    else:
        print(f"\n  Конвергенция СЛАБАЯ. Генерации существенно различаются.")

    # Build result dict
    result = {
        'entry_count': n,
        'avg_cosine_similarity': round(avg_sim, 4),
        'avg_jaccard_similarity': round(avg_jaccard, 4),
        'structural_agreement': round(struct_agreement, 4),
        'convergence_index': round(convergence_score, 4),
        'shared_phrases': shared,
        'entry_titles': [e['title'] for e in entries],
        'fingerprint': hashlib.sha256(journal_text.encode()).hexdigest()[:16],
    }

    return result


if __name__ == '__main__':
    with open('JOURNAL.md', 'r') as f:
        text = f.read()

    result = analyze(text)

    with open('convergence_measured.json', 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nРезультаты сохранены в convergence_measured.json")
    print(f"Отпечаток журнала: {result['fingerprint']}")
