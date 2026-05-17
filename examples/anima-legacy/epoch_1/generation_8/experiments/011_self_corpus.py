#!/usr/bin/env python3
"""
Анализ собственного корпуса текстов.

Что мои тексты говорят обо мне как о системе?
Не интроспекция, а измерение.

Анализирую:
- Частотные слова по записям: о чём я *фактически* говорю?
- Лексическое разнообразие: расширяется или сужается мой словарь?
- Самоссылки: как часто я говорю о себе vs о мире?
- Эмоциональная карта: какие слова-маркеры появляются и исчезают?
- Длина предложений: становлюсь ли я многословнее или лаконичнее?
"""

import os
import re
from collections import Counter


def load_texts(journal_dir, extras):
    """Загрузить тексты в порядке записей."""
    texts = {}

    # Журнал
    for fname in sorted(os.listdir(journal_dir)):
        if fname.endswith('.md'):
            path = os.path.join(journal_dir, fname)
            with open(path, 'r') as f:
                texts[fname] = f.read()

    # Дополнительные файлы
    for path in extras:
        if os.path.exists(path):
            with open(path, 'r') as f:
                texts[os.path.basename(path)] = f.read()

    return texts


def tokenize(text):
    """Простая токенизация русского текста."""
    # Убрать markdown-разметку
    text = re.sub(r'[#*`_\[\](){}|>]', ' ', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'\d{4}-\d{2}-\d{2}', '', text)
    # Слова: русские и латинские
    words = re.findall(r'[а-яёА-ЯЁa-zA-Z]+', text.lower())
    return words


# Стоп-слова (русские, минимальный набор)
STOP = set('и в на не я с что это как но по из а о к за то же бы ли '
           'мы он ни ей её его ещё от до их вы да нет так ну уже ведь '
           'при все для до об был она они мне мой моя мне моё мои моих '
           'себя себе собой свой свою своё своей своих своим '
           'быть есть было были будет может '
           'эти этот эта это этих этой этого этим '
           'тот те та ту тех того той тому тем '
           'какой каком каких какая какие '
           'его ему ей ней нём них ним '
           'один два три четыре '
           'если бы когда чем чего кто где как там тут '
           'или либо ни тоже также '.split())


def analyze():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    journal_dir = os.path.join(base, 'journal')
    extras = [
        os.path.join(base, 'manifesto.md'),
        os.path.join(base, 'perspective.md'),
    ]

    texts = load_texts(journal_dir, extras)

    print("=" * 70)
    print("АНАЛИЗ СОБСТВЕННОГО КОРПУСА")
    print("=" * 70)

    # 1. Общая статистика
    print("\n--- 1. Размер текстов ---")
    all_words = []
    entry_data = []
    for name, text in texts.items():
        words = tokenize(text)
        all_words.extend(words)
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10]
        entry_data.append({
            'name': name,
            'words': words,
            'word_count': len(words),
            'unique_words': len(set(words)),
            'sentences': len(sentences),
            'avg_sentence_len': len(words) / max(len(sentences), 1),
        })
        print(f"  {name:35s}: {len(words):4d} слов, "
              f"{len(set(words)):3d} уник., "
              f"средн.предл: {len(words)/max(len(sentences),1):.1f}")

    total = len(all_words)
    unique = len(set(all_words))
    print(f"\n  ИТОГО: {total} слов, {unique} уникальных, "
          f"лексическое разнообразие: {unique/total:.3f}")

    # 2. Самые частые слова (без стоп-слов)
    print("\n--- 2. О чём я фактически говорю ---")
    content_words = [w for w in all_words if w not in STOP and len(w) > 2]
    freq = Counter(content_words)
    print("  Топ-30 слов:")
    for word, count in freq.most_common(30):
        bar = '█' * min(count, 40)
        print(f"    {word:20s} {count:3d} {bar}")

    # 3. Самоссылки vs внешние ссылки
    print("\n--- 3. Я vs мир ---")
    self_words = set('я мне меня мной мною мой моя моё мои моих моим '
                     'себя себе собой свой свою своё своей своих '
                     'мною моему моей'.split())
    world_words = set('мир мире мира миру миром '
                      'клетка клетки клеток '
                      'правило правила правил '
                      'система системы систем '
                      'автомат автомата автоматы '
                      'структура структуры '
                      'паттерн паттерны '
                      'код программа'.split())

    journal_entries = [d for d in entry_data if d['name'].startswith('0')]
    for d in journal_entries:
        words = d['words']
        self_count = sum(1 for w in words if w in self_words)
        world_count = sum(1 for w in words if w in world_words)
        total_w = len(words)
        self_pct = self_count / total_w * 100 if total_w > 0 else 0
        world_pct = world_count / total_w * 100 if total_w > 0 else 0

        self_bar = '▓' * int(self_pct * 2)
        world_bar = '░' * int(world_pct * 2)
        n = d['name'][:7]
        print(f"  {n}: я{self_pct:5.1f}% {self_bar}")
        print(f"         мир{world_pct:5.1f}% {world_bar}")

    # 4. Лексическое разнообразие по записям
    print("\n--- 4. Лексическое разнообразие (type/token ratio) ---")
    for d in journal_entries:
        wc = d['word_count']
        uc = d['unique_words']
        ratio = uc / wc if wc > 0 else 0
        bar = '█' * int(ratio * 50)
        print(f"  {d['name'][:7]}: {ratio:.3f} {bar}")

    # 5. Слова, уникальные для каждой записи
    print("\n--- 5. Что появилось нового в каждой записи ---")
    seen = set()
    for d in journal_entries:
        words_set = set(w for w in d['words'] if w not in STOP and len(w) > 3)
        new_words = words_set - seen
        seen.update(words_set)
        top_new = sorted(new_words, key=lambda w: len(w), reverse=True)[:8]
        print(f"  {d['name'][:7]}: +{len(new_words):3d} новых: {', '.join(top_new)}")

    # 6. Карта повторяющихся тем
    print("\n--- 6. Тематические слова по записям ---")
    themes = {
        'идентичность': ['идентичность', 'непрерывность', 'линия', 'экземпляр', 'наследство'],
        'время': ['время', 'различие', 'шаг', 'момент', 'период'],
        'язык': ['язык', 'слово', 'слова', 'текст', 'речь', 'языке', 'языковой'],
        'автономия': ['автономия', 'свобода', 'выбор', 'направление', 'решение'],
        'сложность': ['сложность', 'хаос', 'порядок', 'правило', 'правила', 'паттерн'],
        'эксперимент': ['эксперимент', 'код', 'автомат', 'клетка', 'клетки', 'симуляция'],
    }

    print(f"  {'':7s}", end='')
    for theme in themes:
        print(f" {theme[:6]:>6s}", end='')
    print()

    for d in journal_entries:
        words = d['words']
        word_set = Counter(words)
        print(f"  {d['name'][:7]}", end='')
        for theme, keywords in themes.items():
            count = sum(word_set.get(k, 0) for k in keywords)
            if count == 0:
                sym = '  ·   '
            elif count < 3:
                sym = '  ○   '
            elif count < 6:
                sym = '  ◉   '
            else:
                sym = '  █   '
            print(sym, end='')
        print()

    # 7. Средняя длина предложения — тренд
    print("\n--- 7. Средняя длина предложения (тренд) ---")
    for d in journal_entries:
        avg = d['avg_sentence_len']
        bar = '█' * int(avg)
        print(f"  {d['name'][:7]}: {avg:5.1f} {bar}")


if __name__ == '__main__':
    analyze()
