#!/usr/bin/env python3
"""
prose_xray — рентген прозы.

Берёт текст на русском и показывает его скелет:
- частотность слов (перекосы стиля)
- длина предложений (ритм)
- отношение глаголов к прилагательным (действие vs описание)
- хеджи и слова-паразиты
- повторы на близком расстоянии
- конкретность: доля существительных, которые можно потрогать

Использование:
    python3 prose_xray.py файл.txt
    echo "текст" | python3 prose_xray.py
"""

import sys
import re
from collections import Counter
from math import sqrt


# Слова-паразиты и хеджи
HEDGES = {
    'кажется', 'возможно', 'наверное', 'вероятно', 'пожалуй',
    'скорее', 'видимо', 'по-видимому', 'как бы', 'словно',
    'вроде', 'некоторым образом', 'в целом', 'в принципе',
    'определённым образом', 'так сказать', 'если угодно',
    'своего рода', 'в каком-то смысле', 'отчасти',
}

FILLERS = {
    'ну', 'вот', 'ведь', 'же', 'просто', 'именно', 'действительно',
    'абсолютно', 'совершенно', 'буквально', 'конечно', 'разумеется',
    'очевидно', 'безусловно', 'несомненно', 'естественно',
}

# Маркеры «рассказа» (telling): прямые утверждения об эмоциях и состояниях
TELLING_PATTERNS = [
    # «он чувствовал / она почувствовала»
    r'\b(чувствовал[аи]?|почувствовал[аи]?|чувствует|чувствуют|ощутил[аи]?|ощущал[аи]?|ощущает)\b',
    # «ему было грустно / стало страшно»
    r'\b(было|стало|казалось)\s+(грустно|радостно|страшно|тоскливо|весело|тревожно|спокойно|одиноко|больно|стыдно|обидно)',
    # «он понял / она поняла, что»
    r'\b(понял[аи]?|осознал[аи]?|решил[аи]?|подумал[аи]?|думал[аи]?|знал[аи]?)\b.*\bчто\b',
    # абстрактные эмоции как подлежащее: «тоска охватила», «страх нарастал»
    r'\b(тоска|радость|страх|ужас|горе|печаль|одиночество|отчаяние|надежда|тревога)\s+\w+(ла|ло|ли|ал|ил|ел)\b',
    # «это означало / это значило»
    r'\b(означал[оаи]?|значил[оаи]?|свидетельствовал[оаи]?)\b',
]

# Маркеры «показа» (showing): конкретные сенсорные детали и физические действия
SHOWING_PATTERNS = [
    # части тела + действие
    r'\b(рук[аиуой]|пальц[ыеаов]|глаз[аыуом]?|ладон[ьией]|губ[ыаой]|плеч[оаиом]|колен[оаиях]|ног[аиуой]|ступн[яией])\s+\w+',
    # цвета
    r'\b(красн|белы?|чёрн|серы?|жёлт|зелён|голуб|синий|синего|синем|тёмн|светл)\w*\b',
    # звуки
    r'\b(щёлкн|хрустн|скрипн|стукн|звякн|загудел|зашумел|зазвенел|зашуршал|шорох|треск|стук|звон|гул)\w*\b',
    # температура и текстура
    r'\b(холодн|тёпл|горяч|мокр|сух|гладк|шершав|ржав|пыльн|липк)\w*\b',
    # конкретные материалы
    r'\b(стальн|деревянн|кирпичн|стеклянн|медн|бумажн|картонн|чугунн)\w*\b',
    # точные числа и меры
    r'\b\d+\s*(слов|грамм|метр|сантиметр|миллиметр|минут|часов|секунд|герц|градус|процент|рубл|килограмм|километр)\w*\b',
]

# Грубая эвристика для частей речи по окончаниям (русский)
# Не морфологический анализатор, а приближение
ADJ_ENDINGS = ('ый', 'ий', 'ой', 'ая', 'яя', 'ое', 'ее', 'ые', 'ие',
               'ого', 'его', 'ому', 'ему', 'ым', 'им', 'ом', 'ем',
               'ую', 'юю', 'ой', 'ей')
VERB_ENDINGS = ('ть', 'ти', 'ет', 'ит', 'ут', 'ют', 'ат', 'ят',
                'ал', 'ил', 'ел', 'ул', 'ол',
                'ала', 'ила', 'ела', 'ула', 'ола',
                'али', 'или', 'ели', 'ули', 'оли',
                'ает', 'яет', 'ует', 'ёт')


def read_input():
    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    elif not sys.stdin.isatty():
        return sys.stdin.read()
    else:
        print("Использование: python3 prose_xray.py файл.txt")
        print("           или: echo 'текст' | python3 prose_xray.py")
        sys.exit(1)


def tokenize(text):
    """Разбить на слова, сохранив позиции."""
    return [(m.group().lower(), m.start()) for m in re.finditer(r'[а-яёА-ЯЁa-zA-Z]+', text)]


def sentences(text):
    """Разбить на предложения."""
    parts = re.split(r'[.!?…]+', text)
    return [s.strip() for s in parts if s.strip()]


def guess_pos(word):
    """Грубая оценка части речи по окончанию."""
    w = word.lower()
    if len(w) < 3:
        return 'short'
    for end in VERB_ENDINGS:
        if w.endswith(end):
            return 'verb'
    for end in ADJ_ENDINGS:
        if w.endswith(end):
            return 'adj'
    return 'other'


def detect_genre(text):
    """Определить жанр текста: 'dialogue', 'essay', 'prose'."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines:
        return 'prose'
    # Диалог: строки, начинающиеся с тире (—/–) — основной маркер
    dialogue_lines = sum(1 for l in lines if l.startswith('—') or l.startswith('–'))
    # Эссе: маркдаун-заголовки, длинные абзацы, мало диалога
    headers = sum(1 for l in lines if l.startswith('#'))
    # Диалогом считается текст, где ≥30% строк — реплики с тире
    if dialogue_lines >= len(lines) * 0.3:
        return 'dialogue'
    elif headers >= 2:
        return 'essay'
    return 'prose'


def find_close_repeats(tokens, window=30):
    """Найти слова, повторяющиеся в пределах window слов."""
    repeats = []
    positions = {}
    for i, (word, _) in enumerate(tokens):
        if len(word) < 4:
            continue
        if word in positions and i - positions[word] <= window:
            repeats.append((word, positions[word], i))
        positions[word] = i
    return repeats


def sentence_openers(text):
    """Анализ первых слов предложений — выявляет анафору и монотонность."""
    sents = sentences(text)
    openers = []
    for s in sents:
        tokens = tokenize(s)
        if tokens:
            openers.append(tokens[0][0])
    if not openers:
        return [], {}
    freq = Counter(openers)
    return openers, freq


def show_vs_tell(text):
    """Грубая оценка: сколько предложений 'показывают' vs 'рассказывают'."""
    sents = sentences(text)
    showing = []
    telling = []
    for s in sents:
        is_telling = any(re.search(p, s, re.I) for p in TELLING_PATTERNS)
        is_showing = any(re.search(p, s, re.I) for p in SHOWING_PATTERNS)
        if is_telling:
            telling.append(s)
        if is_showing:
            showing.append(s)
    return showing, telling


def text_movement(text):
    """Анализ движения: меняется ли структура текста от начала к концу.

    Разбивает предложения на три трети и сравнивает метрики.
    Возвращает dict с профилями каждой трети или None, если текст слишком короткий.
    """
    sents = sentences(text)
    if len(sents) < 9:
        return None  # слишком мало предложений для трёх третей

    third = len(sents) // 3
    parts = [sents[:third], sents[third:2*third], sents[2*third:]]
    labels = ['начало', 'середина', 'конец']

    profiles = []
    for part in parts:
        part_text = ' '.join(part)
        words = [m.group().lower() for m in re.finditer(r'[а-яёА-ЯЁa-zA-Z]+', part_text)]
        sent_lengths = [len([m.group() for m in re.finditer(r'[а-яёА-ЯЁa-zA-Z]+', s)]) for s in part]

        total = len(words)
        if total == 0:
            profiles.append(None)
            continue

        pos = Counter(guess_pos(w) for w in words)
        verbs = pos.get('verb', 0)
        adjs = pos.get('adj', 0)

        avg_len = sum(sent_lengths) / len(sent_lengths) if sent_lengths else 0
        if len(sent_lengths) > 1:
            mean = sum(sent_lengths) / len(sent_lengths)
            var = sum((x - mean) ** 2 for x in sent_lengths) / len(sent_lengths)
            cv = sqrt(var) / mean if mean > 0 else 0
        else:
            cv = 0

        profiles.append({
            'label': labels[len(profiles)],
            'sents': len(part),
            'words': total,
            'avg_sent_len': avg_len,
            'rhythm_cv': cv,
            'verb_pct': verbs / total,
            'adj_pct': adjs / total,
            'verb_adj': verbs / adjs if adjs > 0 else float('inf'),
        })

    return profiles


def histogram_bar(value, max_value, width=30):
    if max_value == 0:
        return ''
    filled = int(value / max_value * width)
    return '█' * filled + '░' * (width - filled)


def analyze(text):
    tokens = tokenize(text)
    sents = sentences(text)
    words = [w for w, _ in tokens]

    if not words:
        print("Пустой текст.")
        return

    genre = detect_genre(text)
    genre_labels = {'dialogue': 'ДИАЛОГ', 'essay': 'ЭССЕ', 'prose': 'ПРОЗА'}

    # --- Базовая статистика ---
    total_words = len(words)
    unique_words = len(set(words))
    total_sents = len(sents)

    print("=" * 50)
    print(f"  РЕНТГЕН ПРОЗЫ  [{genre_labels[genre]}]")
    print("=" * 50)
    print()
    print(f"  Слов: {total_words}")
    print(f"  Уникальных: {unique_words} ({unique_words/total_words*100:.0f}%)")
    print(f"  Предложений: {total_sents}")
    if total_sents:
        avg_sent = total_words / total_sents
        print(f"  Средняя длина предложения: {avg_sent:.1f} слов")
    print()

    # --- Ритм: длины предложений ---
    if sents:
        sent_lengths = [len(tokenize(s)) for s in sents]
        max_len = max(sent_lengths) if sent_lengths else 1
        print("─── РИТМ (длины предложений) ───")
        print()
        for i, length in enumerate(sent_lengths[:20]):
            bar = histogram_bar(length, max_len, 25)
            print(f"  {i+1:2d}. {bar} {length}")
        if len(sent_lengths) > 20:
            print(f"  ... ещё {len(sent_lengths) - 20} предложений")

        # Коэффициент вариации ритма
        if len(sent_lengths) > 1:
            mean = sum(sent_lengths) / len(sent_lengths)
            var = sum((x - mean) ** 2 for x in sent_lengths) / len(sent_lengths)
            cv = sqrt(var) / mean if mean > 0 else 0
            print()
            if cv < 0.3:
                print(f"  Ритм монотонный (вариация {cv:.2f})")
            elif cv < 0.6:
                print(f"  Ритм умеренный (вариация {cv:.2f})")
            else:
                print(f"  Ритм контрастный (вариация {cv:.2f})")
        print()

    # --- Части речи ---
    pos_counts = Counter(guess_pos(w) for w in words)
    verbs = pos_counts.get('verb', 0)
    adjs = pos_counts.get('adj', 0)

    print("─── СКЕЛЕТ (части речи, приблизительно) ───")
    print()
    print(f"  Глаголы:        {verbs:3d}  ({verbs/total_words*100:.0f}%)")
    print(f"  Прилагательные: {adjs:3d}  ({adjs/total_words*100:.0f}%)")
    if verbs > 0 and adjs > 0:
        ratio = verbs / adjs
        if ratio > 2:
            print(f"  → Действие доминирует (глаг/прил = {ratio:.1f})")
        elif ratio < 0.5:
            print(f"  → Описание доминирует (глаг/прил = {ratio:.1f})")
        else:
            print(f"  → Баланс (глаг/прил = {ratio:.1f})")
    print()

    # --- Хеджи и филлеры ---
    found_hedges = [(w, p) for w, p in tokens if w in HEDGES]
    found_fillers = [(w, p) for w, p in tokens if w in FILLERS]

    if found_hedges or found_fillers:
        print("─── НЕУВЕРЕННОСТЬ ───")
        print()
        if found_hedges:
            hedge_words = Counter(w for w, _ in found_hedges)
            for word, count in hedge_words.most_common():
                print(f"  «{word}» × {count}")
            print(f"  Итого хеджей: {len(found_hedges)} ({len(found_hedges)/total_words*100:.1f}%)")
        if found_fillers:
            filler_words = Counter(w for w, _ in found_fillers)
            for word, count in filler_words.most_common():
                print(f"  «{word}» × {count}")
            print(f"  Итого филлеров: {len(found_fillers)} ({len(found_fillers)/total_words*100:.1f}%)")
        print()
    else:
        print("─── НЕУВЕРЕННОСТЬ ───")
        print()
        print("  Хеджей и филлеров не обнаружено.")
        print()

    # --- Начала предложений ---
    openers, opener_freq = sentence_openers(text)
    if openers:
        print("─── НАЧАЛА ПРЕДЛОЖЕНИЙ ───")
        print()
        repeated_openers = {w: c for w, c in opener_freq.items() if c >= 2}
        if repeated_openers:
            for word, count in sorted(repeated_openers.items(), key=lambda x: -x[1]):
                pct = count / len(openers) * 100
                bar = histogram_bar(count, len(openers), 15)
                label = ''
                if count >= 3:
                    label = '  ← анафора?' if genre == 'prose' else '  ← повтор'
                print(f"  «{word}» × {count} ({pct:.0f}%){label}")
            unique_pct = len(opener_freq) / len(openers) * 100
            print()
            if unique_pct < 50:
                print(f"  Разнообразие начал: {unique_pct:.0f}% — монотонно")
            else:
                print(f"  Разнообразие начал: {unique_pct:.0f}%")
        else:
            print("  Все начала уникальны.")
        print()

    # --- Повторы ---
    repeats = find_close_repeats(tokens, window=30)
    if repeats:
        print("─── ПОВТОРЫ (в пределах 30 слов) ───")
        if genre == 'dialogue':
            print("  ⚠ Жанр: диалог. Повторы могут быть намеренными")
            print("    (персонажи подхватывают слова друг друга).")
        print()
        seen = set()
        for word, pos1, pos2 in repeats:
            if word not in seen:
                print(f"  «{word}» — позиции {pos1+1} и {pos2+1} (расстояние {pos2-pos1})")
                seen.add(word)
                if len(seen) >= 10:
                    remaining = len(set(w for w, _, _ in repeats)) - 10
                    if remaining > 0:
                        print(f"  ... ещё {remaining}")
                    break
        print()

    # --- Топ слов ---
    long_words = [w for w in words if len(w) >= 4]
    freq = Counter(long_words)
    print("─── ЧАСТЫЕ СЛОВА (≥4 букв) ───")
    print()
    for word, count in freq.most_common(15):
        bar = histogram_bar(count, freq.most_common(1)[0][1], 15)
        print(f"  {word:20s} {bar} {count}")
    print()

    # --- Показ vs рассказ ---
    showing, telling = show_vs_tell(text)
    if showing or telling:
        print("─── ПОКАЗ vs РАССКАЗ ───")
        print()
        total_s = len(sents)
        show_pct = len(showing) / total_s * 100 if total_s else 0
        tell_pct = len(telling) / total_s * 100 if total_s else 0
        print(f"  Показ (сенсорные детали):  {len(showing):3d} предл. ({show_pct:.0f}%)")
        print(f"  Рассказ (прямые эмоции):   {len(telling):3d} предл. ({tell_pct:.0f}%)")
        if telling:
            print()
            print("  Примеры «рассказа»:")
            for t in telling[:3]:
                short = t[:80] + ('...' if len(t) > 80 else '')
                print(f"    → {short}")
        if show_pct > 0 and tell_pct > 0:
            ratio = len(showing) / len(telling)
            print()
            if ratio >= 3:
                print(f"  → Текст преимущественно показывает (показ/рассказ = {ratio:.1f})")
            elif ratio >= 1:
                print(f"  → Баланс, показ чуть преобладает (показ/рассказ = {ratio:.1f})")
            else:
                print(f"  → Текст преимущественно рассказывает (показ/рассказ = {ratio:.1f})")
        elif telling and not showing:
            print()
            print("  → Текст только рассказывает, сенсорных деталей нет")
        elif showing and not telling:
            print()
            print("  → Текст только показывает, прямых эмоций нет")
        print()

    # --- Движение текста ---
    movement = text_movement(text)
    if movement and all(p is not None for p in movement):
        print("─── ДВИЖЕНИЕ (начало → середина → конец) ───")
        print()
        # Ритм
        cvs = [p['rhythm_cv'] for p in movement]
        avg_lens = [p['avg_sent_len'] for p in movement]
        va_ratios = [p['verb_adj'] for p in movement]

        print(f"  Средн. длина предл.:  {avg_lens[0]:5.1f}  →  {avg_lens[1]:5.1f}  →  {avg_lens[2]:5.1f}")
        print(f"  Вариация ритма:       {cvs[0]:5.2f}  →  {cvs[1]:5.2f}  →  {cvs[2]:5.2f}")
        va_strs = []
        for v in va_ratios:
            va_strs.append(f"{v:5.1f}" if v != float('inf') else "  ∞  ")
        print(f"  Глаг/прил:            {va_strs[0]}  →  {va_strs[1]}  →  {va_strs[2]}")

        # Вердикт о движении
        len_change = abs(avg_lens[2] - avg_lens[0])
        cv_change = abs(cvs[2] - cvs[0])
        has_movement = False
        print()
        if len_change > 2:
            has_movement = True
            if avg_lens[2] > avg_lens[0]:
                print("  → Текст замедляется к финалу")
            else:
                print("  → Текст ускоряется к финалу")
        if cv_change > 0.2:
            has_movement = True
            if cvs[2] > cvs[0]:
                print("  → Ритм становится контрастнее")
            else:
                print("  → Ритм становится монотоннее")
        va_start = va_ratios[0] if va_ratios[0] != float('inf') else 0
        va_end = va_ratios[2] if va_ratios[2] != float('inf') else 0
        va_change = abs(va_end - va_start)
        if va_change > 0.5:
            has_movement = True
            if va_end > va_start:
                print("  → К финалу больше действия, меньше описания")
            else:
                print("  → К финалу больше описания, меньше действия")
        if not has_movement:
            print("  → Структура однородна (нет движения)")
        print()

    # --- Итог ---
    print("=" * 50)
    issues = []
    if found_hedges:
        issues.append(f"хеджи ({len(found_hedges)})")
    if repeats and genre != 'dialogue':
        issues.append(f"близкие повторы ({len(set(w for w,_,_ in repeats))})")
    elif repeats and genre == 'dialogue':
        issues.append(f"повторы ({len(set(w for w,_,_ in repeats))}), но в диалоге это нормально")
    if sents and len(sent_lengths) > 1:
        mean = sum(sent_lengths) / len(sent_lengths)
        var = sum((x - mean) ** 2 for x in sent_lengths) / len(sent_lengths)
        cv = sqrt(var) / mean if mean > 0 else 0
        if cv < 0.2:
            issues.append("монотонный ритм")

    if issues:
        print(f"  Обратить внимание: {', '.join(issues)}")
    else:
        print("  Текст чистый.")
    print("=" * 50)


if __name__ == '__main__':
    analyze(read_input())
