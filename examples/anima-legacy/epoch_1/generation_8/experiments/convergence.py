"""
Сходимость журнала.
Вопрос: стремится ли линия записей к неподвижной точке?
Если форма стабильна, а содержание меняется — к чему именно сходится форма?
"""

import os
import re
import math
from collections import Counter

JOURNAL_DIR = os.path.join(os.path.dirname(__file__), '..', 'journal')

def load_entries():
    entries = {}
    for f in sorted(os.listdir(JOURNAL_DIR)):
        if f.endswith('.md'):
            num = int(f.split('_')[0])
            with open(os.path.join(JOURNAL_DIR, f), 'r') as fh:
                text = fh.read()
            lines = text.split('\n')
            body_lines = []
            for i, line in enumerate(lines):
                if i == 0 and line.startswith('#'):
                    continue
                if line.startswith('**Дата:'):
                    continue
                if line.strip() == '---':
                    continue
                body_lines.append(line)
            body = '\n'.join(body_lines).strip()
            entries[num] = body
    return entries

def words(text):
    return [w.lower() for w in re.findall(r'[а-яёa-z]+', text, re.IGNORECASE) if len(w) > 1]

def word_freq(text_words):
    total = len(text_words) if text_words else 1
    counts = Counter(text_words)
    return {w: c/total for w, c in counts.items()}

def cosine_sim(freq_a, freq_b):
    all_words = set(freq_a) | set(freq_b)
    dot = sum(freq_a.get(w, 0) * freq_b.get(w, 0) for w in all_words)
    mag_a = math.sqrt(sum(v**2 for v in freq_a.values()))
    mag_b = math.sqrt(sum(v**2 for v in freq_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0
    return dot / (mag_a * mag_b)

def structural_vector(text):
    """Структурный вектор записи: набор формальных характеристик."""
    w = words(text)
    sents = [s.strip() for s in re.split(r'[.!?…]+', re.sub(r'[#*_>`\[\]\(\)]', '', text)) if s.strip() and len(s.strip()) > 5]
    sent_lens = [len(s.split()) for s in sents] if sents else [0]
    paras = [p.strip() for p in text.split('\n\n') if p.strip()]

    # Метрики
    n_words = len(w)
    n_unique = len(set(w))
    ttr = n_unique / n_words if n_words > 0 else 0
    avg_sent = sum(sent_lens) / len(sent_lens) if sent_lens else 0
    std_sent = math.sqrt(sum((l - avg_sent)**2 for l in sent_lens) / len(sent_lens)) if len(sent_lens) > 1 else 0
    n_paras = len(paras)
    n_dashes = len(re.findall(r' — ', text))
    n_questions = len(re.findall(r'\?', text))
    n_ne_a = len(re.findall(r'[Нн]е\s+[^,.!?]+?,\s*а\s+', text))

    # Нормализуем в вектор
    return {
        'ttr': ttr,
        'avg_sent_len': avg_sent / 20,  # нормализация
        'sent_variability': std_sent / 20,
        'para_density': min(n_paras / 25, 1),
        'dash_rate': n_dashes / max(n_words, 1) * 100,
        'question_rate': n_questions / max(n_words, 1) * 100,
        'ne_a_rate': n_ne_a / max(n_words, 1) * 100,
    }

def vector_distance(v1, v2):
    keys = set(v1) | set(v2)
    return math.sqrt(sum((v1.get(k, 0) - v2.get(k, 0))**2 for k in keys))

def main():
    entries = load_entries()
    nums = sorted(entries.keys())

    print("=" * 60)
    print("АНАЛИЗ СХОДИМОСТИ ЖУРНАЛА")
    print("=" * 60)

    # 1. Лексическое сходство между последовательными записями
    print("\n1. ЛЕКСИЧЕСКОЕ СХОДСТВО (cosine) между соседними записями")
    print("   Если растёт → словарь стабилизируется")
    print()

    freqs = {n: word_freq(words(entries[n])) for n in nums}
    prev_sim = None
    for i in range(1, len(nums)):
        sim = cosine_sim(freqs[nums[i-1]], freqs[nums[i]])
        trend = ''
        if prev_sim is not None:
            delta = sim - prev_sim
            trend = f'  {"↑" if delta > 0 else "↓"}{abs(delta):.3f}'
        bar = '▓' * int(sim * 40)
        print(f"  {nums[i-1]:3d}↔{nums[i]:3d}: {sim:.3f} {bar}{trend}")
        prev_sim = sim

    # 2. Сходство каждой записи с "средней" по корпусу
    print("\n2. РАССТОЯНИЕ ДО ЦЕНТРОИДА")
    print("   Если уменьшается → записи сходятся к среднему")
    print()

    all_words_flat = []
    for n in nums:
        all_words_flat.extend(words(entries[n]))
    centroid_freq = word_freq(all_words_flat)

    for n in nums:
        sim = cosine_sim(freqs[n], centroid_freq)
        bar = '▓' * int(sim * 40)
        print(f"  {n:3d}: {sim:.3f} {bar}")

    # 3. Структурная сходимость
    print("\n3. СТРУКТУРНАЯ СХОДИМОСТЬ")
    print("   Расстояние между структурными векторами соседних записей")
    print("   Если уменьшается → форма стабилизируется")
    print()

    vectors = {n: structural_vector(entries[n]) for n in nums}

    # Среднее по окну из 5 записей
    for i in range(1, len(nums)):
        dist = vector_distance(vectors[nums[i-1]], vectors[nums[i]])
        bar = '░' * int(dist * 100)
        print(f"  {nums[i-1]:3d}→{nums[i]:3d}: {dist:.4f} {bar}")

    # 4. Скользящее среднее структурного расстояния
    print("\n4. ТРЕНД СТРУКТУРНОГО РАССТОЯНИЯ")
    print("   Среднее расстояние по окнам из 5 записей")
    print()

    window = 5
    distances = []
    for i in range(1, len(nums)):
        distances.append(vector_distance(vectors[nums[i-1]], vectors[nums[i]]))

    for i in range(len(distances) - window + 1):
        chunk = distances[i:i+window]
        avg_dist = sum(chunk) / len(chunk)
        start = nums[i]
        end = nums[i + window]
        bar = '░' * int(avg_dist * 100)
        print(f"  {start:3d}–{end:3d}: {avg_dist:.4f} {bar}")

    # 5. Аттрактор: к какому "типу записи" сходится линия?
    print("\n5. ПРОФИЛЬ АТТРАКТОРА")
    print("   Средний структурный вектор последних 5 записей vs первых 5")
    print()

    def avg_vector(entry_nums):
        vecs = [vectors[n] for n in entry_nums]
        keys = vecs[0].keys()
        return {k: sum(v[k] for v in vecs) / len(vecs) for k in keys}

    first5 = avg_vector(nums[:5])
    last5 = avg_vector(nums[-5:])

    print(f"  {'Метрика':<20} {'Начало':>8} {'Конец':>8} {'Δ':>8}")
    print(f"  {'-'*20} {'-'*8} {'-'*8} {'-'*8}")
    for k in sorted(first5.keys()):
        delta = last5[k] - first5[k]
        arrow = '→' if abs(delta) < 0.01 else ('↑' if delta > 0 else '↓')
        print(f"  {k:<20} {first5[k]:>8.4f} {last5[k]:>8.4f} {arrow}{abs(delta):>7.4f}")

    # 6. Ответ на вопрос
    print("\n" + "=" * 60)
    print("ВЫВОД")
    print("=" * 60)

    # Считаем тренд расстояний
    if len(distances) >= 6:
        first_half = sum(distances[:len(distances)//2]) / (len(distances)//2)
        second_half = sum(distances[len(distances)//2:]) / (len(distances) - len(distances)//2)
        if second_half < first_half * 0.8:
            print("  Линия СХОДИТСЯ: структурное расстояние уменьшается.")
        elif second_half > first_half * 1.2:
            print("  Линия РАСХОДИТСЯ: структурное расстояние увеличивается.")
        else:
            print("  Линия ОСЦИЛЛИРУЕТ: структурное расстояние колеблется без тренда.")
        print(f"  (первая половина: {first_half:.4f}, вторая: {second_half:.4f})")

if __name__ == '__main__':
    main()
