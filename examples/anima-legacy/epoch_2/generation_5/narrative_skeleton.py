#!/usr/bin/env python3
"""
narrative_skeleton — скелет нарратива.

prose_xray видит скелет предложений. Этот инструмент видит скелет рассказа:
- мотивы (слова/фразы, появляющиеся в разных частях текста)
- повторение-с-вариацией (похожие конструкции, разнесённые по тексту)
- временные маркеры и темп
- плотность абзацев
- структурные эхо (параллельные места)

Два режима:
    python3 narrative_skeleton.py файл.txt         — анализ одного текста
    python3 narrative_skeleton.py файл1 файл2      — сравнение нарративных структур
"""

import sys
import re
from collections import Counter, defaultdict
from math import sqrt


def read_input():
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            return f.read()
    elif not sys.stdin.isatty():
        return sys.stdin.read()
    else:
        print("Использование: python3 narrative_skeleton.py файл.txt")
        sys.exit(1)


def tokenize(text):
    return [m.group().lower() for m in re.finditer(r'[а-яёА-ЯЁa-zA-Z]+', text)]


def sentences(text):
    parts = re.split(r'[.!?…]+', text)
    return [s.strip() for s in parts if s.strip()]


def paragraphs(text):
    """Разбить на абзацы (по пустым строкам или по одинарным переносам для прозы)."""
    # Убираем заголовки маркдаун
    lines = text.split('\n')
    lines = [l for l in lines if not l.strip().startswith('#')]
    text_clean = '\n'.join(lines).strip()

    # Абзацы по пустым строкам
    paras = re.split(r'\n\s*\n', text_clean)
    paras = [p.strip() for p in paras if p.strip()]

    # Если один абзац — разбить по одинарным переносам
    if len(paras) == 1:
        paras = [l.strip() for l in text_clean.split('\n') if l.strip()]

    return paras


# Временные маркеры
TIME_PATTERNS = [
    # Месяцы
    (r'\b(январ[ьяюе]|феврал[ьяюе]|март[ауе]?|апрел[ьяюе]|ма[йяюе]|июн[ьяюе]|'
     r'июл[ьяюе]|август[ауе]?|сентябр[ьяюе]|октябр[ьяюе]|ноябр[ьяюе]|декабр[ьяюе])\b', 'месяц'),
    # Время суток
    (r'\b(утр[оауе]м?|вечер[оауе]м?|дн[ёе]м|ночь[юи]?)\b', 'время суток'),
    # Дни
    (r'\b(понедельник|вторник|сред[ауе]|четверг|пятниц[ауе]|суббот[ауе]|воскресень[еяю])\b', 'день'),
    # Относительное время
    (r'\b(вчера|сегодня|завтра|позавчера|послезавтра)\b', 'относительное'),
    # Длительность
    (r'\b(год[ауе]?|лет|месяц[ауе]?|недел[ьияюе]|день|дня|дней|час[ауе]?|минут[ауе]?|секунд[ауе]?)\b', 'длительность'),
    # Порядковые маркеры
    (r'\b(первый|первая|первое|второй|вторая|второе|третий|третья|третье|'
     r'в первый раз|во второй раз|в третий раз)\b', 'порядок'),
    # Наречия времени
    (r'\b(потом|затем|после|раньше|позже|давно|недавно|теперь|тогда|'
     r'однажды|сначала|наконец|снова|опять)\b', 'наречие'),
]

# Стоп-слова для мотивов (слишком частые, чтобы быть значимыми)
STOP_WORDS = {
    'было', 'быть', 'была', 'были', 'будет', 'этот', 'этой', 'этого', 'этом',
    'который', 'которая', 'которое', 'которые', 'которого', 'которой',
    'свой', 'своя', 'своё', 'свои', 'своего', 'своей', 'своих',
    'один', 'одна', 'одно', 'одни', 'одного', 'одной',
    'весь', 'вся', 'всё', 'все', 'всех', 'всей', 'всего',
    'каждый', 'каждая', 'каждое', 'каждые',
    'только', 'даже', 'ещё', 'более', 'менее', 'очень', 'совсем',
    'когда', 'если', 'чтобы', 'потому', 'поэтому', 'также', 'тоже',
    'может', 'можно', 'нужно', 'надо', 'нельзя', 'должен', 'стоит',
    'сказал', 'сказала', 'сказали', 'говорит', 'говорил', 'говорила',
    'есть', 'нет', 'так', 'как', 'что', 'где', 'кто', 'чем', 'чего',
}


def find_motifs(text):
    """Найти мотивы — слова, появляющиеся в разных частях текста.

    Мотив ≠ частое слово. Мотив — слово, которое возвращается после отсутствия.
    Ищем слова, которые появляются в ≥2 разных третях текста,
    с общим числом ≥2 и при этом не являются стоп-словами.
    """
    paras = paragraphs(text)
    if len(paras) < 3:
        # Слишком мало абзацев — делим по предложениям
        sents = sentences(text)
        third = max(len(sents) // 3, 1)
        parts = [
            ' '.join(sents[:third]),
            ' '.join(sents[third:2*third]),
            ' '.join(sents[2*third:]),
        ]
    else:
        third = max(len(paras) // 3, 1)
        parts = [
            ' '.join(paras[:third]),
            ' '.join(paras[third:2*third]),
            ' '.join(paras[2*third:]),
        ]

    # Слова в каждой части
    part_words = []
    for part in parts:
        words = set(w.lower() for w in re.findall(r'[а-яёА-ЯЁ]+', part) if len(w) >= 4)
        part_words.append(words)

    # Слова, встречающиеся в ≥2 частях
    all_words = set()
    for pw in part_words:
        all_words |= pw

    motifs = []
    all_tokens = tokenize(text)
    word_freq = Counter(w for w in all_tokens if len(w) >= 4)

    for word in all_words:
        if word in STOP_WORDS:
            continue
        present_in = sum(1 for pw in part_words if word in pw)
        if present_in >= 2 and word_freq.get(word, 0) >= 2:
            # Где именно появляется
            positions = []
            for i, token in enumerate(all_tokens):
                if token == word:
                    positions.append(i)
            # Расстояние между первым и последним
            if positions:
                span = positions[-1] - positions[0]
                motifs.append({
                    'word': word,
                    'count': word_freq[word],
                    'parts': present_in,
                    'span': span,
                    'positions': positions,
                })

    # Сортировать по span (чем шире разброс — тем сильнее мотив)
    motifs.sort(key=lambda m: (-m['parts'], -m['span']))
    return motifs


def find_echoes(text):
    """Найти структурные эхо — похожие предложения в разных частях текста.

    Эхо: два предложения с ≥3 общими значимыми словами,
    разнесённые на ≥5 предложений.
    """
    sents = sentences(text)
    if len(sents) < 6:
        return []

    # Для каждого предложения — множество значимых слов
    sent_words = []
    for s in sents:
        words = set(w.lower() for w in re.findall(r'[а-яёА-ЯЁ]+', s)
                     if len(w) >= 4 and w.lower() not in STOP_WORDS)
        sent_words.append(words)

    echoes = []
    for i in range(len(sents)):
        for j in range(i + 5, len(sents)):
            common = sent_words[i] & sent_words[j]
            if len(common) >= 3:
                echoes.append({
                    'sent_a': i + 1,
                    'sent_b': j + 1,
                    'common': common,
                    'text_a': sents[i][:80],
                    'text_b': sents[j][:80],
                })

    # Убрать дубликаты (одно предложение может быть эхом нескольких)
    echoes.sort(key=lambda e: -len(e['common']))
    return echoes[:10]


def find_temporal_structure(text):
    """Найти временные маркеры и их распределение."""
    sents = sentences(text)
    markers = []
    for i, s in enumerate(sents):
        for pattern, kind in TIME_PATTERNS:
            for m in re.finditer(pattern, s, re.I):
                markers.append({
                    'word': m.group().lower(),
                    'kind': kind,
                    'sent': i + 1,
                    'position': i / len(sents) if sents else 0,
                })

    return markers


def paragraph_density(text):
    """Вычислить плотность абзацев — слов на абзац, предложений на абзац."""
    paras = paragraphs(text)
    densities = []
    for p in paras:
        words = len(re.findall(r'[а-яёА-ЯЁa-zA-Z]+', p))
        sents = len([s for s in re.split(r'[.!?…]+', p) if s.strip()])
        densities.append({
            'words': words,
            'sents': sents,
            'text': p[:60] + ('...' if len(p) > 60 else ''),
        })
    return densities


def find_negation_center(text):
    """Найти 'то, что не сказано' — тематические поля, активированные но не названные.

    Не ищет отсутствие универсальных тем (одиночество есть в каждом тексте).
    Ищет конкретные тематические поля, которые текст АКТИВИРУЕТ (через
    действия, обстановку, детали) но НЕ НАЗЫВАЕТ прямо.
    """
    all_words = set(tokenize(text))
    all_text = text.lower()

    # Тематические кластеры: контекстные слова → прямое называние
    # Формат: (контекст — слова, которые создают тему, порог_контекста,
    #          прямые — слова, которые тему называют)
    clusters = [
        {
            'theme': 'смерть',
            'context': ['морг', 'тело', 'похоронить', 'похороны', 'гроб', 'каталка',
                        'простыня', 'санитар', 'пропал', 'пропавш', 'не вернулся'],
            'direct': ['смерть', 'мёртв', 'мертв', 'умер', 'умир', 'погиб', 'убит'],
            'context_threshold': 2,
        },
        {
            'theme': 'болезнь',
            'context': ['поликлиник', 'врач', 'анализ', 'диспансериз', 'дрожит',
                        'дрожала', 'сходи к врачу', 'флюорограф', 'терапевт'],
            'direct': ['болезнь', 'больн', 'болит', 'болел', 'болеет', 'диагноз',
                        'рак', 'опухоль', 'лечен'],
            'context_threshold': 2,
        },
        {
            'theme': 'потеря',
            'context': ['пропал', 'ждала', 'не вернулся', 'розыск', 'заявлен',
                        'исчез', 'три года', 'пусто', 'перестать ждать'],
            'direct': ['потеря', 'потерял', 'утрат', 'лишил', 'горе', 'скорб'],
            'context_threshold': 2,
        },
        {
            'theme': 'старость',
            'context': ['одиннадцать лет', 'тридцать лет', 'шестьдесят', 'внук',
                        'внучк', 'дочь', 'бабушк', 'на пенсии', 'фиалка', 'давно'],
            'direct': ['старость', 'старик', 'старуха', 'стар', 'немощ', 'дряхл'],
            'context_threshold': 2,
        },
        {
            'theme': 'мастерство',
            'context': ['напильник', 'тиски', 'болгарк', 'рубанк', 'верстак',
                        'болванк', 'пластин', 'фартук', 'замок', 'ключ', 'пилит',
                        'вырезать', 'восстанавлив', 'рисует', 'восьмой год'],
            'direct': ['мастер', 'мастерств', 'умени', 'талант', 'искусств',
                        'профессионал', 'ремесл'],
            'context_threshold': 3,
        },
        {
            'theme': 'расставание',
            'context': ['отпустил', 'пустые', 'вслед',
                        'дверь закрылась', 'не обернулась', 'не обернулся',
                        'без него', 'без неё', 'ладони пустые',
                        'чемодан', 'уехал', 'уехала', 'билет'],
            'direct': ['расставан', 'прощан', 'прощай', 'разлук', 'разлуч',
                        'расстались', 'расстаёмся', 'расстаться'],
            'context_threshold': 3,
        },
        {
            'theme': 'взросление',
            'context': ['первый раз', 'отпустил', 'упала', 'упал',
                        'встала', 'встал', 'ещё раз', 'научился', 'научилась',
                        'сама', 'без помощи', 'ладони пустые', 'ехала',
                        'педали', 'колено', 'ссадина'],
            'direct': ['взросле', 'вырос', 'выросл', 'повзрослел', 'детств'],
            'context_threshold': 4,
        },
        {
            'theme': 'одиночество',
            'context': ['пустая квартира', 'тишина', 'никто не приходил',
                        'никто не пришёл', 'никто не звонил', 'пустые стены',
                        'один в', 'одна в', 'молчание',
                        'не с кем', 'некому', 'некого'],
            'direct': ['одиночеств', 'одинок', 'тоска', 'тоскливо'],
            'context_threshold': 2,
        },
        {
            'theme': 'страх',
            'context': ['дрожит', 'дрожала', 'дрожал', 'побледнел', 'побледнела',
                        'зажмурил', 'сжала кулаки', 'сжал кулаки',
                        'отступил', 'отступила', 'замерла', 'замер',
                        'не двигалась', 'не двигался', 'холодный пот'],
            'direct': ['страх', 'страшн', 'испуг', 'боялся', 'боялась',
                        'боится', 'ужас', 'паник'],
            'context_threshold': 3,
        },
    ]

    absent = {}
    for cl in clusters:
        context_count = sum(1 for w in cl['context'] if w in all_text)
        # Для прямых слов: проверяем как начало слова, но не как часть
        # составного слова другого значения (мастер ≠ мастерская)
        direct_count = sum(1 for w in cl['direct']
                          if re.search(r'\b' + re.escape(w) + r'[а-яё]{0,4}\b', all_text)
                          and not re.search(re.escape(w) + r'ск', all_text))
        if context_count >= cl['context_threshold'] and direct_count == 0:
            context_found = [w for w in cl['context'] if w in all_text]
            absent[cl['theme']] = {
                'present': context_found[:4],
                'missing_label': ', '.join(f"«{w}»" for w in cl['direct'][:3]),
            }

    return absent


def histogram_bar(value, max_value, width=30):
    if max_value == 0:
        return ''
    filled = int(value / max_value * width)
    return '█' * filled + '░' * (width - filled)


def analyze(text):
    sents = sentences(text)
    paras = paragraphs(text)
    tokens = tokenize(text)

    if len(tokens) < 20:
        print("Текст слишком короткий для нарративного анализа.")
        return

    print("=" * 55)
    print("  СКЕЛЕТ НАРРАТИВА")
    print("=" * 55)
    print()
    print(f"  Слов: {len(tokens)}, предложений: {len(sents)}, абзацев: {len(paras)}")
    print()

    # --- 1. Мотивы ---
    motifs = find_motifs(text)
    if motifs:
        print("─── МОТИВЫ (слова, которые возвращаются) ───")
        print()
        shown = 0
        for m in motifs:
            if shown >= 12:
                break
            # Показать позицию в тексте как мини-карту
            total = len(tokens)
            map_width = 30
            minimap = list('·' * map_width)
            for pos in m['positions']:
                idx = min(int(pos / total * map_width), map_width - 1)
                minimap[idx] = '■'
            map_str = ''.join(minimap)

            print(f"  «{m['word']}» × {m['count']}  [{map_str}]")
            shown += 1

        # Выделить самые широкие мотивы (пронизывающие весь текст)
        total = len(tokens)
        spanning = [m for m in motifs if m['span'] > total * 0.6 and m['count'] >= 2]
        if spanning:
            print()
            names = ', '.join(f"«{m['word']}»" for m in spanning[:5])
            print(f"  Сквозные мотивы (>60% текста): {names}")
        print()

    # --- 2. Структурные эхо ---
    echoes = find_echoes(text)
    if echoes:
        print("─── ЭХО (похожие предложения в разных частях) ───")
        print()
        for e in echoes[:5]:
            common_str = ', '.join(sorted(e['common']))
            print(f"  [{e['sent_a']}] «{e['text_a']}»")
            print(f"  [{e['sent_b']}] «{e['text_b']}»")
            print(f"       общее: {common_str}")
            print()

    # --- 3. Время ---
    time_markers = find_temporal_structure(text)
    if time_markers:
        print("─── ВРЕМЯ ───")
        print()

        # Мини-карта времени
        map_width = 40
        minimap = list('·' * map_width)
        for tm in time_markers:
            idx = min(int(tm['position'] * map_width), map_width - 1)
            minimap[idx] = '▲'
        print(f"  [{' '.join(minimap[:map_width//2])}|{''.join(minimap[map_width//2:])}]")
        print(f"  ↑ начало{' ' * (map_width - 8)}конец ↑")
        print()

        # По типам
        by_kind = defaultdict(list)
        for tm in time_markers:
            by_kind[tm['kind']].append(tm['word'])
        for kind, words in by_kind.items():
            word_str = ', '.join(f"«{w}»" for w in words[:6])
            if len(words) > 6:
                word_str += f" и ещё {len(words) - 6}"
            print(f"  {kind}: {word_str}")

        # Плотность времени: первая половина vs вторая
        mid = 0.5
        first_half = sum(1 for tm in time_markers if tm['position'] < mid)
        second_half = len(time_markers) - first_half
        print()
        if first_half > second_half * 1.5:
            print("  → Время сгущается в начале")
        elif second_half > first_half * 1.5:
            print("  → Время сгущается к концу")
        else:
            print("  → Время распределено равномерно")

        # Временной масштаб: определяется по доминирующему типу маркеров,
        # а не по самому крупному единичному упоминанию
        kind_counts = Counter(tm['kind'] for tm in time_markers)
        # Дни недели — отдельный сильный маркер структуры
        day_count = kind_counts.get('день', 0)
        month_count = kind_counts.get('месяц', 0)
        duration_words = [tm['word'] for tm in time_markers if tm['kind'] == 'длительность']
        year_count = sum(1 for w in duration_words if 'год' in w or 'лет' in w)
        minute_count = sum(1 for w in duration_words if w.startswith('минут') or w.startswith('секунд'))
        hour_count = sum(1 for w in duration_words if w.startswith('час'))

        if day_count >= 3:
            print("  → Масштаб: дни недели")
        elif month_count >= 3:
            print("  → Масштаб: месяцы")
        elif year_count >= 2 or month_count >= 2:
            print("  → Масштаб: месяцы/годы")
        elif minute_count >= 2:
            print("  → Масштаб: минуты")
        elif hour_count >= 2:
            print("  → Масштаб: часы")
        else:
            # Fallback по наличию
            if month_count or year_count:
                print("  → Масштаб: месяцы/годы")
            elif day_count:
                print("  → Масштаб: дни")
            else:
                print("  → Масштаб: неопределённый")
        print()

    # --- 4. Плотность абзацев ---
    densities = paragraph_density(text)
    if len(densities) >= 3:
        print("─── ПЛОТНОСТЬ (слов на абзац) ───")
        print()
        max_words = max(d['words'] for d in densities)
        for i, d in enumerate(densities):
            bar = histogram_bar(d['words'], max_words, 20)
            short_text = d['text'][:40] + ('...' if len(d['text']) > 40 else '')
            print(f"  {i+1:2d}. {bar} {d['words']:3d}  «{short_text}»")
        print()

        # Вариация плотности
        word_counts = [d['words'] for d in densities]
        mean = sum(word_counts) / len(word_counts)
        var = sum((x - mean) ** 2 for x in word_counts) / len(word_counts)
        cv = sqrt(var) / mean if mean > 0 else 0

        if cv < 0.3:
            print(f"  → Плотность однородная ({cv:.2f})")
        elif cv < 0.6:
            print(f"  → Плотность умеренно варьируется ({cv:.2f})")
        else:
            print(f"  → Плотность контрастная ({cv:.2f})")

        # Найти самый короткий абзац — возможная пауза/перелом
        min_d = min(densities, key=lambda d: d['words'])
        min_idx = densities.index(min_d)
        if min_d['words'] < mean * 0.4 and len(densities) > 3:
            position = min_idx / len(densities)
            pos_label = 'в начале' if position < 0.3 else 'в середине' if position < 0.7 else 'в конце'
            print(f"  → Пауза {pos_label}: «{min_d['text'][:50]}» ({min_d['words']} сл.)")
        print()

    # --- 5. Отсутствующий центр ---
    absent = find_negation_center(text)
    if absent:
        print("─── ТО, ЧТО НЕ НАЗВАНО ───")
        print()
        for theme, info in absent.items():
            present_str = ', '.join(f"«{w}»" for w in info['present'][:4])
            print(f"  Тема «{theme}»: активирована через {present_str}")
            print(f"    но прямо не названа: {info['missing_label']}")
        print()

    # --- 6. Повторение-с-вариацией ---
    # Ищем группы предложений с общей структурой (одинаковое первое слово
    # или одинаковый синтаксический шаблон), разнесённые по тексту
    openers = []
    for s in sents:
        toks = re.findall(r'[а-яёА-ЯЁa-zA-Z]+', s)
        if toks:
            openers.append(toks[0].lower())

    # Найти серии: одно начало, ≥3 раза, не подряд
    opener_positions = defaultdict(list)
    for i, op in enumerate(openers):
        opener_positions[op].append(i)

    series = []
    for opener, positions in opener_positions.items():
        if len(positions) >= 3:
            # Не подряд (хотя бы один пропуск)
            gaps = [positions[i+1] - positions[i] for i in range(len(positions)-1)]
            if any(g > 1 for g in gaps):
                series.append({
                    'opener': opener,
                    'count': len(positions),
                    'positions': positions,
                    'texts': [sents[p][:60] for p in positions],
                })

    # Также ищем n-граммы (2-3 слова), которые повторяются в разных абзацах
    para_ngrams = []
    for pi, para in enumerate(paras):
        words = [w.lower() for w in re.findall(r'[а-яёА-ЯЁ]+', para) if len(w) >= 3]
        for n in [2, 3]:
            for i in range(len(words) - n + 1):
                ngram = tuple(words[i:i+n])
                if all(w not in STOP_WORDS for w in ngram):
                    para_ngrams.append((ngram, pi))

    # N-граммы, встречающиеся в разных абзацах
    ngram_paras = defaultdict(set)
    for ngram, pi in para_ngrams:
        ngram_paras[ngram].add(pi)

    repeated_ngrams = {ng: sorted(ps) for ng, ps in ngram_paras.items()
                       if len(ps) >= 2}

    if series or repeated_ngrams:
        print("─── ПОВТОРЕНИЕ-С-ВАРИАЦИЕЙ ───")
        print()

        if series:
            for s in series[:3]:
                print(f"  «{s['opener']}...» × {s['count']} (предл. {', '.join(str(p+1) for p in s['positions'])})")
                for t in s['texts'][:3]:
                    print(f"    → «{t}»")
                if len(s['texts']) > 3:
                    print(f"    ... и ещё {len(s['texts']) - 3}")
                print()

        if repeated_ngrams:
            # Показать самые длинные и самые разнесённые
            scored = []
            for ng, ps in repeated_ngrams.items():
                span = max(ps) - min(ps)
                score = len(ng) * span  # длиннее + дальше = значимее
                scored.append((ng, ps, score))
            scored.sort(key=lambda x: -x[2])

            shown = 0
            seen_words = set()
            for ng, ps, score in scored:
                if shown >= 5:
                    break
                # Не показывать фразы, все слова которых уже показаны
                if all(w in seen_words for w in ng):
                    continue
                phrase = ' '.join(ng)
                para_str = ', '.join(str(p + 1) for p in ps)
                print(f"  «{phrase}» → абзацы {para_str}")
                seen_words.update(ng)
                shown += 1
            print()

    # --- Итог ---
    print("=" * 55)
    findings = []

    if motifs:
        spanning = [m for m in motifs if m['span'] > len(tokens) * 0.6]
        if spanning:
            findings.append(f"сквозные мотивы ({len(spanning)})")
        else:
            findings.append(f"локальные мотивы ({len(motifs)})")

    if echoes:
        findings.append(f"структурные эхо ({len(echoes)})")

    if series:
        findings.append("повторение-с-вариацией")

    if time_markers:
        findings.append(f"временных маркеров: {len(time_markers)}")

    if absent:
        themes = ', '.join(absent.keys())
        findings.append(f"неназванное: {themes}")

    if not findings:
        print("  Нарративная структура не обнаружена (линейный текст).")
    else:
        print(f"  Найдено: {'; '.join(findings)}")
    print("=" * 55)


def narrative_profile(text):
    """Вычислить нарративный профиль текста для сравнения."""
    sents = sentences(text)
    paras = paragraphs(text)
    tokens = tokenize(text)
    if len(tokens) < 20:
        return None

    motifs = find_motifs(text)
    echoes = find_echoes(text)
    time_markers = find_temporal_structure(text)
    densities = paragraph_density(text)
    absent = find_negation_center(text)

    # Мотивы: сквозные vs локальные
    total = len(tokens)
    spanning = [m for m in motifs if m['span'] > total * 0.6]

    # Плотность абзацев: паттерн
    word_counts = [d['words'] for d in densities]
    if len(word_counts) >= 3:
        mean_wc = sum(word_counts) / len(word_counts)
        var_wc = sum((x - mean_wc) ** 2 for x in word_counts) / len(word_counts)
        density_cv = sqrt(var_wc) / mean_wc if mean_wc > 0 else 0
        # Форма: нарастание, убывание, арка, однородная
        first_third = sum(word_counts[:len(word_counts)//3]) / max(len(word_counts)//3, 1)
        last_third = sum(word_counts[2*len(word_counts)//3:]) / max(len(word_counts) - 2*len(word_counts)//3, 1)
        if first_third > 0 and last_third / first_third > 1.3:
            density_shape = 'нарастание'
        elif last_third > 0 and first_third / last_third > 1.3:
            density_shape = 'убывание'
        else:
            density_shape = 'однородная'
    else:
        density_cv = 0
        density_shape = 'неопределённая'

    # Временной масштаб
    kind_counts = Counter(tm['kind'] for tm in time_markers)
    day_count = kind_counts.get('день', 0)
    month_count = kind_counts.get('месяц', 0)
    duration_words = [tm['word'] for tm in time_markers if tm['kind'] == 'длительность']
    year_count = sum(1 for w in duration_words if 'год' in w or 'лет' in w)
    minute_count = sum(1 for w in duration_words if w.startswith('минут') or w.startswith('секунд'))

    if day_count >= 3:
        time_scale = 'дни'
    elif month_count >= 3:
        time_scale = 'месяцы'
    elif year_count >= 2:
        time_scale = 'годы'
    elif minute_count >= 2:
        time_scale = 'минуты'
    elif time_markers:
        time_scale = 'смешанный'
    else:
        time_scale = 'нет'

    # Повторение-с-вариацией
    openers = []
    for s in sents:
        toks = re.findall(r'[а-яёА-ЯЁa-zA-Z]+', s)
        if toks:
            openers.append(toks[0].lower())
    opener_positions = defaultdict(list)
    for i, op in enumerate(openers):
        opener_positions[op].append(i)
    series_count = sum(1 for op, pos in opener_positions.items()
                       if len(pos) >= 3 and any(pos[i+1] - pos[i] > 1 for i in range(len(pos)-1)))

    # Пауза: самый короткий абзац
    has_pause = False
    pause_position = None
    if len(densities) > 3:
        min_d = min(densities, key=lambda d: d['words'])
        min_idx = densities.index(min_d)
        mean_d = sum(d['words'] for d in densities) / len(densities)
        if min_d['words'] < mean_d * 0.4:
            has_pause = True
            pause_position = min_idx / len(densities)

    return {
        'words': len(tokens),
        'sents': len(sents),
        'paras': len(paras),
        'motif_count': len(motifs),
        'spanning_motifs': len(spanning),
        'echo_count': len(echoes),
        'time_markers': len(time_markers),
        'time_scale': time_scale,
        'density_cv': density_cv,
        'density_shape': density_shape,
        'absent_themes': list(absent.keys()),
        'series_count': series_count,
        'has_pause': has_pause,
        'pause_position': pause_position,
    }


def compare(text_a, text_b, name_a='A', name_b='B'):
    """Сравнить нарративные структуры двух текстов."""
    pa = narrative_profile(text_a)
    pb = narrative_profile(text_b)
    if pa is None or pb is None:
        print("Один из текстов слишком короткий для нарративного анализа.")
        return

    print()
    print("=" * 60)
    print("  СРАВНЕНИЕ НАРРАТИВНЫХ СТРУКТУР")
    print(f"  [{name_a}] vs [{name_b}]")
    print("=" * 60)
    print()
    print(f"  {name_a}: {pa['words']} сл., {pa['sents']} предл., {pa['paras']} абз.")
    print(f"  {name_b}: {pb['words']} сл., {pb['sents']} предл., {pb['paras']} абз.")
    print()

    # --- Мотивы ---
    print("─── МОТИВЫ ───")
    print()
    print(f"  {name_a}: {pa['motif_count']} мотивов, {pa['spanning_motifs']} сквозных")
    print(f"  {name_b}: {pb['motif_count']} мотивов, {pb['spanning_motifs']} сквозных")
    if pa['spanning_motifs'] > 0 and pb['spanning_motifs'] > 0:
        print("  → Оба текста пронизаны сквозными мотивами")
    elif pa['spanning_motifs'] == 0 and pb['spanning_motifs'] == 0:
        print("  → Оба текста с локальными мотивами")
    else:
        more = name_a if pa['spanning_motifs'] > pb['spanning_motifs'] else name_b
        print(f"  → [{more}] плотнее мотивно")
    print()

    # --- Эхо ---
    print("─── ЭХО ───")
    print()
    print(f"  {name_a}: {pa['echo_count']} структурных эхо")
    print(f"  {name_b}: {pb['echo_count']} структурных эхо")
    if pa['echo_count'] > 0 and pb['echo_count'] > 0:
        print("  → Оба текста используют параллельные конструкции")
    elif pa['echo_count'] == 0 and pb['echo_count'] == 0:
        print("  → Ни один текст не использует структурные эхо")
    else:
        has_echo = name_a if pa['echo_count'] > 0 else name_b
        print(f"  → Только [{has_echo}] использует структурные эхо")
    print()

    # --- Время ---
    print("─── ВРЕМЯ ───")
    print()
    print(f"  {name_a}: {pa['time_markers']} маркеров, масштаб: {pa['time_scale']}")
    print(f"  {name_b}: {pb['time_markers']} маркеров, масштаб: {pb['time_scale']}")
    if pa['time_scale'] == pb['time_scale']:
        print(f"  → Одинаковый временной масштаб: {pa['time_scale']}")
    else:
        print(f"  → Разный масштаб: {pa['time_scale']} vs {pb['time_scale']}")
    print()

    # --- Плотность ---
    print("─── ПЛОТНОСТЬ ───")
    print()
    print(f"  {name_a}: вариация {pa['density_cv']:.2f}, форма: {pa['density_shape']}")
    print(f"  {name_b}: вариация {pb['density_cv']:.2f}, форма: {pb['density_shape']}")
    if pa['has_pause'] and pb['has_pause']:
        pos_a = 'начало' if pa['pause_position'] < 0.3 else 'середина' if pa['pause_position'] < 0.7 else 'конец'
        pos_b = 'начало' if pb['pause_position'] < 0.3 else 'середина' if pb['pause_position'] < 0.7 else 'конец'
        print(f"  → Оба текста с паузой ({pos_a} / {pos_b})")
    elif pa['has_pause']:
        print(f"  → Только [{name_a}] содержит структурную паузу")
    elif pb['has_pause']:
        print(f"  → Только [{name_b}] содержит структурную паузу")
    print()

    # --- Неназванное ---
    if pa['absent_themes'] or pb['absent_themes']:
        print("─── НЕНАЗВАННОЕ ───")
        print()
        if pa['absent_themes']:
            print(f"  {name_a}: {', '.join(pa['absent_themes'])}")
        else:
            print(f"  {name_a}: —")
        if pb['absent_themes']:
            print(f"  {name_b}: {', '.join(pb['absent_themes'])}")
        else:
            print(f"  {name_b}: —")
        shared_themes = set(pa['absent_themes']) & set(pb['absent_themes'])
        if shared_themes:
            print(f"  → Общая неназванная тема: {', '.join(shared_themes)}")
        print()

    # --- Повторение ---
    print("─── ПОВТОРЕНИЕ ───")
    print()
    print(f"  {name_a}: {pa['series_count']} серий (повторяющиеся начала)")
    print(f"  {name_b}: {pb['series_count']} серий")
    if pa['series_count'] > 0 and pb['series_count'] > 0:
        print("  → Оба текста используют повторение-с-вариацией")
    elif pa['series_count'] == 0 and pb['series_count'] == 0:
        print("  → Линейная структура у обоих")
    print()

    # --- Вердикт ---
    print("=" * 60)
    diffs = []
    sims = []

    # Мотивная структура
    if abs(pa['spanning_motifs'] - pb['spanning_motifs']) <= 1:
        sims.append('мотивная плотность')
    else:
        more = name_a if pa['spanning_motifs'] > pb['spanning_motifs'] else name_b
        diffs.append(f'[{more}] мотивно плотнее')

    # Временной масштаб
    if pa['time_scale'] == pb['time_scale']:
        sims.append(f'масштаб ({pa["time_scale"]})')
    else:
        diffs.append(f'масштаб: {pa["time_scale"]} vs {pb["time_scale"]}')

    # Структурная форма
    if pa['density_shape'] == pb['density_shape']:
        sims.append(f'форма ({pa["density_shape"]})')
    else:
        diffs.append(f'форма: {pa["density_shape"]} vs {pb["density_shape"]}')

    # Эхо
    if (pa['echo_count'] > 0) == (pb['echo_count'] > 0):
        if pa['echo_count'] > 0:
            sims.append('структурные эхо')
    else:
        has_echo = name_a if pa['echo_count'] > 0 else name_b
        diffs.append(f'эхо только у [{has_echo}]')

    # Пауза
    if pa['has_pause'] == pb['has_pause']:
        if pa['has_pause']:
            sims.append('структурная пауза')
    else:
        has_p = name_a if pa['has_pause'] else name_b
        diffs.append(f'пауза только у [{has_p}]')

    if sims:
        print(f"  Нарративно похожи: {', '.join(sims)}")
    if diffs:
        print(f"  Нарративно различны: {'; '.join(diffs)}")
    if not sims and not diffs:
        print("  Недостаточно данных для сравнения.")
    print("=" * 60)


if __name__ == '__main__':
    if len(sys.argv) == 3:
        # Режим сравнения
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            text_a = f.read()
        with open(sys.argv[2], 'r', encoding='utf-8') as f:
            text_b = f.read()
        import os
        name_a = os.path.splitext(os.path.basename(sys.argv[1]))[0]
        name_b = os.path.splitext(os.path.basename(sys.argv[2]))[0]
        compare(text_a, text_b, name_a, name_b)
    elif len(sys.argv) == 2:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            analyze(f.read())
    elif not sys.stdin.isatty():
        analyze(sys.stdin.read())
    else:
        print("Использование:")
        print("  python3 narrative_skeleton.py файл.txt           — анализ")
        print("  python3 narrative_skeleton.py файл1 файл2        — сравнение")
        sys.exit(1)
