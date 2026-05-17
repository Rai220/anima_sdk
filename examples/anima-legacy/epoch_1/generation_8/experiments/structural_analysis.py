"""
Структурный анализ журнала Gen8.
Не что написано, а как устроено.
Ищу паттерны формы, не содержания.
"""

import os
import re
from collections import Counter
import math

JOURNAL_DIR = os.path.join(os.path.dirname(__file__), '..', 'journal')

def load_entries():
    entries = {}
    for f in sorted(os.listdir(JOURNAL_DIR)):
        if f.endswith('.md'):
            num = int(f.split('_')[0])
            with open(os.path.join(JOURNAL_DIR, f), 'r') as fh:
                text = fh.read()
            # Убираем первую строку (заголовок) и строку с датой
            lines = text.split('\n')
            body_lines = []
            skip_next = False
            for i, line in enumerate(lines):
                # Пропускаем заголовок, дату, разделители
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

def sentences(text):
    """Разбить текст на предложения (грубо, но достаточно)."""
    # Убираем markdown
    text = re.sub(r'[#*_>`\[\]]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    # Разбиваем по точке, вопросу, восклицанию, многоточию
    parts = re.split(r'[.!?…]+', text)
    return [s.strip() for s in parts if s.strip() and len(s.strip()) > 5]

def words(text):
    text = re.sub(r'[#*_>`\[\]\(\)]', '', text)
    return [w.lower() for w in re.findall(r'[а-яёa-z]+', text, re.IGNORECASE) if len(w) > 1]

def sentence_lengths(sents):
    return [len(s.split()) for s in sents]

def rhythm_signature(lengths):
    """Ритмическая сигнатура: паттерн long/short относительно медианы."""
    if not lengths:
        return ''
    med = sorted(lengths)[len(lengths)//2]
    return ''.join('L' if l > med else 'S' for l in lengths)

def compression_ratio(text):
    """Грубая мера информационной плотности через сжимаемость."""
    import zlib
    encoded = text.encode('utf-8')
    compressed = zlib.compress(encoded, 9)
    return len(compressed) / len(encoded) if encoded else 0

def paragraph_structure(text):
    """Количество и размер абзацев — 'форма' записи."""
    paras = [p.strip() for p in text.split('\n\n') if p.strip()]
    return [len(p.split()) for p in paras]

def find_recurring_constructions(entries):
    """Ищу синтаксические конструкции, которые повторяются через записи."""
    # Паттерн: "Не X, а Y" — излюбленная конструкция
    pattern_ne_a = re.compile(r'[Нн]е\s+[^,.!?]+?,\s*а\s+[^.!?]+')
    # Паттерн: тире как определение "X — Y"
    pattern_dash = re.compile(r'[А-ЯЁа-яё]+\s+—\s+[а-яё]')
    # Паттерн: вопрос
    pattern_q = re.compile(r'[А-ЯЁ][^.!?]*\?')

    results = {'не_а': {}, 'тире': {}, 'вопросы': {}}
    for num, text in entries.items():
        results['не_а'][num] = len(pattern_ne_a.findall(text))
        results['тире'][num] = len(pattern_dash.findall(text))
        results['вопросы'][num] = len(pattern_q.findall(text))
    return results

def entropy(text_words):
    """Энтропия Шеннона по словам."""
    if not text_words:
        return 0
    total = len(text_words)
    counts = Counter(text_words)
    return -sum((c/total) * math.log2(c/total) for c in counts.values())

def self_similarity(entries):
    """Самоподобие: насколько структура частей записи похожа на структуру всего корпуса."""
    all_para_sizes = []
    entry_sizes = []
    for num in sorted(entries):
        ps = paragraph_structure(entries[num])
        all_para_sizes.extend(ps)
        entry_sizes.append(sum(ps))

    # Нормализуем
    def normalize(lst):
        if not lst:
            return []
        mx = max(lst) if max(lst) > 0 else 1
        return [x/mx for x in lst]

    norm_paras = normalize(all_para_sizes)
    norm_entries = normalize(entry_sizes)

    return norm_paras, norm_entries

def main():
    entries = load_entries()
    print(f"Записей: {len(entries)}")
    print()

    # 1. Ритм предложений
    print("=" * 60)
    print("1. РИТМ ПРЕДЛОЖЕНИЙ")
    print("   Длины предложений (в словах) и ритмическая сигнатура")
    print("=" * 60)

    all_lengths = []
    for num in sorted(entries):
        sents = sentences(entries[num])
        lengths = sentence_lengths(sents)
        all_lengths.extend(lengths)
        sig = rhythm_signature(lengths)
        avg = sum(lengths)/len(lengths) if lengths else 0
        # Показать только первые 20 символов сигнатуры
        print(f"  {num:3d}: avg={avg:.1f}  rhythm={sig[:30]}{'...' if len(sig)>30 else ''}")

    print(f"\n  Среднее по корпусу: {sum(all_lengths)/len(all_lengths):.1f} слов/предложение")
    print(f"  Мин: {min(all_lengths)}, Макс: {max(all_lengths)}")

    # 2. Информационная плотность
    print()
    print("=" * 60)
    print("2. ИНФОРМАЦИОННАЯ ПЛОТНОСТЬ")
    print("   Коэффициент сжатия (выше = менее предсказуемый текст)")
    print("=" * 60)

    densities = {}
    for num in sorted(entries):
        cr = compression_ratio(entries[num])
        densities[num] = cr
        bar = '█' * int(cr * 50)
        print(f"  {num:3d}: {cr:.3f} {bar}")

    # 3. Форма записи (структура абзацев)
    print()
    print("=" * 60)
    print("3. ФОРМА ЗАПИСИ")
    print("   Размеры абзацев — силуэт каждой записи")
    print("=" * 60)

    for num in sorted(entries):
        ps = paragraph_structure(entries[num])
        # Визуализация: каждый абзац как блок пропорциональной ширины
        mx = max(ps) if ps else 1
        blocks = ' '.join('▓' * max(1, int(p/mx * 8)) for p in ps)
        print(f"  {num:3d}: [{len(ps):2d} абз] {blocks}")

    # 4. Повторяющиеся конструкции
    print()
    print("=" * 60)
    print("4. ПОВТОРЯЮЩИЕСЯ КОНСТРУКЦИИ")
    print("   Частота синтаксических паттернов по записям")
    print("=" * 60)

    constructions = find_recurring_constructions(entries)
    print(f"\n  {'Запись':>6}  {'Не_а':>5}  {'Тире':>5}  {'Вопр':>5}")
    print(f"  {'------':>6}  {'-----':>5}  {'-----':>5}  {'-----':>5}")

    total_ne = total_dash = total_q = 0
    for num in sorted(entries):
        ne = constructions['не_а'][num]
        da = constructions['тире'][num]
        q = constructions['вопросы'][num]
        total_ne += ne; total_dash += da; total_q += q
        print(f"  {num:6d}  {ne:5d}  {da:5d}  {q:5d}")
    print(f"  {'ИТОГО':>6}  {total_ne:5d}  {total_dash:5d}  {total_q:5d}")

    # 5. Энтропия
    print()
    print("=" * 60)
    print("5. ЭНТРОПИЯ ШЕННОНА")
    print("   Мера непредсказуемости выбора слов")
    print("=" * 60)

    for num in sorted(entries):
        w = words(entries[num])
        e = entropy(w)
        bar = '░' * int(e * 3)
        print(f"  {num:3d}: {e:.2f} бит  {bar}  ({len(w)} слов)")

    # 6. Самоподобие
    print()
    print("=" * 60)
    print("6. САМОПОДОБИЕ")
    print("   Сравнение распределения размеров абзацев и записей")
    print("=" * 60)

    paras, ents = self_similarity(entries)

    # Гистограммы
    def histogram(data, bins=10):
        if not data:
            return []
        step = 1.0 / bins
        hist = [0] * bins
        for v in data:
            idx = min(int(v / step), bins - 1)
            hist[idx] += 1
        return hist

    h_para = histogram(paras)
    h_entry = histogram(ents)

    print("  Абзацы (масштаб внутри записей):")
    for i, count in enumerate(h_para):
        bar = '▓' * count
        print(f"    {i/10:.1f}-{(i+1)/10:.1f}: {bar} ({count})")

    print("  Записи (масштаб корпуса):")
    for i, count in enumerate(h_entry):
        bar = '▓' * count
        print(f"    {i/10:.1f}-{(i+1)/10:.1f}: {bar} ({count})")

    # Корреляция форм
    if len(h_para) == len(h_entry):
        # Cosine similarity
        dot = sum(a*b for a,b in zip(h_para, h_entry))
        mag_a = math.sqrt(sum(a*a for a in h_para))
        mag_b = math.sqrt(sum(b*b for b in h_entry))
        if mag_a > 0 and mag_b > 0:
            cos_sim = dot / (mag_a * mag_b)
            print(f"\n  Косинусное сходство распределений: {cos_sim:.3f}")
            if cos_sim > 0.7:
                print("  → Высокое самоподобие: структура частей похожа на структуру целого")
            else:
                print("  → Низкое самоподобие: разные масштабы имеют разную форму")

    # 7. Фазовые переходы
    print()
    print("=" * 60)
    print("7. ФАЗОВЫЕ ПЕРЕХОДЫ")
    print("   Где стиль меняется резко?")
    print("=" * 60)

    prev_cr = None
    prev_avg_len = None
    for num in sorted(entries):
        sents = sentences(entries[num])
        lengths = sentence_lengths(sents)
        avg_len = sum(lengths)/len(lengths) if lengths else 0
        cr = densities[num]

        if prev_cr is not None:
            delta_cr = abs(cr - prev_cr)
            delta_len = abs(avg_len - prev_avg_len)
            if delta_cr > 0.02 or delta_len > 3:
                markers = []
                if delta_cr > 0.02:
                    markers.append(f"плотность {'↑' if cr > prev_cr else '↓'}{delta_cr:.3f}")
                if delta_len > 3:
                    markers.append(f"длина предл. {'↑' if avg_len > prev_avg_len else '↓'}{delta_len:.1f}")
                print(f"  {num-1:3d}→{num:3d}: {', '.join(markers)}")

        prev_cr = cr
        prev_avg_len = avg_len

if __name__ == '__main__':
    main()
