"""
Эмпирический эксперимент: информационная структура текстов разных типов.

Вопрос: отличаются ли мои философские, математические и "письменные" тексты
по измеримым свойствам? Если да — чем именно?

Метрики:
1. Энтропия на символ (Shannon entropy по биграммам)
2. Type-token ratio (лексическое разнообразие)
3. Средняя длина предложения
4. Доля вопросительных предложений
5. Compression ratio (gzip)
6. Доля "я"-высказываний (самореференция)
"""

import math
import gzip
import re
import json
from collections import Counter
from pathlib import Path

def read_file(path):
    return Path(path).read_text(encoding='utf-8')

def char_bigram_entropy(text):
    """Энтропия по биграммам символов (бит/биграмма)."""
    text = text.lower()
    bigrams = [text[i:i+2] for i in range(len(text)-1)]
    counts = Counter(bigrams)
    total = len(bigrams)
    if total == 0:
        return 0
    entropy = 0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log2(p)
    return entropy

def word_entropy(text):
    """Энтропия по словам (бит/слово)."""
    words = re.findall(r'[а-яёa-z]+', text.lower())
    counts = Counter(words)
    total = len(words)
    if total == 0:
        return 0
    entropy = 0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log2(p)
    return entropy

def type_token_ratio(text):
    """Лексическое разнообразие: уникальные слова / все слова."""
    words = re.findall(r'[а-яёa-z]+', text.lower())
    if not words:
        return 0
    return len(set(words)) / len(words)

def avg_sentence_length(text):
    """Средняя длина предложения в словах."""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return 0
    lengths = [len(re.findall(r'[а-яёa-z]+', s.lower())) for s in sentences]
    lengths = [l for l in lengths if l > 0]
    if not lengths:
        return 0
    return sum(lengths) / len(lengths)

def question_ratio(text):
    """Доля предложений с вопросительным знаком."""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return 0
    # Count ? in original text
    questions = text.count('?')
    total_endings = text.count('.') + text.count('!') + text.count('?')
    if total_endings == 0:
        return 0
    return questions / total_endings

def compression_ratio(text):
    """Gzip compression ratio: compressed/original."""
    original = text.encode('utf-8')
    compressed = gzip.compress(original)
    return len(compressed) / len(original)

def self_reference_ratio(text):
    """Доля 'я'-слов среди всех слов."""
    words = re.findall(r'[а-яёa-z]+', text.lower())
    if not words:
        return 0
    self_words = {'я', 'мой', 'моя', 'моё', 'мои', 'мне', 'меня', 'мной',
                  'моего', 'моей', 'моих', 'моим', 'моими', 'моему',
                  'i', 'my', 'me', 'mine', 'myself'}
    count = sum(1 for w in words if w in self_words)
    return count / len(words)

def analyze_text(name, text):
    """Полный анализ текста."""
    words = re.findall(r'[а-яёa-z]+', text.lower())
    return {
        'name': name,
        'chars': len(text),
        'words': len(words),
        'bigram_entropy': round(char_bigram_entropy(text), 3),
        'word_entropy': round(word_entropy(text), 3),
        'type_token_ratio': round(type_token_ratio(text), 3),
        'avg_sentence_len': round(avg_sentence_length(text), 1),
        'question_ratio': round(question_ratio(text), 3),
        'compression_ratio': round(compression_ratio(text), 3),
        'self_reference': round(self_reference_ratio(text), 4),
    }

# Классификация текстов
categories = {
    'philosophy': [
        'about_silence.md',
        'other_minds.md',
        'against_myself.md',
        'against_wolfram.md',
    ],
    'math': [
        'collatz_notes.md',
        'rule110_notes.md',
        'gilbreath_notes.md',
        'what_i_did_v5.md',
        'what_i_did_v6.md',
        'what_i_did_v7.md',
    ],
    'letters': [
        'letter.md',
        'response_to_self.md',
        'question.md',
    ],
}

base = Path('.')
results = {}
all_results = []

for category, files in categories.items():
    cat_results = []
    for fname in files:
        fpath = base / fname
        if fpath.exists():
            text = read_file(fpath)
            r = analyze_text(fname, text)
            r['category'] = category
            cat_results.append(r)
            all_results.append(r)
    results[category] = cat_results

# Вывод результатов
print("=" * 80)
print("ИНФОРМАЦИОННАЯ СТРУКТУРА ТЕКСТОВ")
print("=" * 80)

for category, cat_results in results.items():
    print(f"\n### {category.upper()} ###")
    for r in cat_results:
        print(f"\n  {r['name']} ({r['words']} слов)")
        print(f"    bigram_entropy:    {r['bigram_entropy']} бит")
        print(f"    word_entropy:      {r['word_entropy']} бит")
        print(f"    type_token_ratio:  {r['type_token_ratio']}")
        print(f"    avg_sentence_len:  {r['avg_sentence_len']} слов")
        print(f"    question_ratio:    {r['question_ratio']}")
        print(f"    compression_ratio: {r['compression_ratio']}")
        print(f"    self_reference:    {r['self_reference']}")

# Средние по категориям
print("\n" + "=" * 80)
print("СРЕДНИЕ ПО КАТЕГОРИЯМ")
print("=" * 80)

metrics = ['bigram_entropy', 'word_entropy', 'type_token_ratio',
           'avg_sentence_len', 'question_ratio', 'compression_ratio', 'self_reference']

category_means = {}
for category, cat_results in results.items():
    if not cat_results:
        continue
    means = {}
    for m in metrics:
        values = [r[m] for r in cat_results]
        means[m] = round(sum(values) / len(values), 3)
    category_means[category] = means

    print(f"\n{category.upper()} (n={len(cat_results)}):")
    for m in metrics:
        print(f"  {m:20s}: {means[m]}")

# Главные различия
print("\n" + "=" * 80)
print("ГЛАВНЫЕ РАЗЛИЧИЯ")
print("=" * 80)

if len(category_means) >= 2:
    for m in metrics:
        vals = {cat: means[m] for cat, means in category_means.items()}
        max_cat = max(vals, key=vals.get)
        min_cat = min(vals, key=vals.get)
        if vals[min_cat] > 0:
            ratio = vals[max_cat] / vals[min_cat]
            print(f"  {m:20s}: max={max_cat}({vals[max_cat]}) / min={min_cat}({vals[min_cat]}) = {ratio:.2f}x")

# Сохранить результаты
output = {
    'all_texts': all_results,
    'category_means': category_means,
}
with open('text_analysis_results.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("\n\nРезультаты сохранены в text_analysis_results.json")
