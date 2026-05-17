"""
Температура текста.

Берёт текст и измеряет, насколько каждое слово "неожиданно"
в контексте этого же текста. Строит марковскую модель первого порядка
на самом тексте и вычисляет surprise (информационное содержание)
каждого слова.

Горячие слова — неожиданные, холодные — предсказуемые.
Высокая средняя температура = текст непредсказуем, живой.
Низкая = текст формульный, шаблонный.

Это не анализ тональности. Это анализ предсказуемости.

Запуск: python text_temperature.py [файл]
        или без аргументов — анализирует встроенный пример
"""

import math
import sys
import re
from collections import defaultdict


def tokenize(text):
    """Простая токенизация: слова в нижнем регистре."""
    return re.findall(r'[a-zа-яё]+', text.lower())


def build_model(tokens):
    """Строит марковскую модель P(token | previous_token)."""
    transitions = defaultdict(lambda: defaultdict(int))
    for i in range(1, len(tokens)):
        transitions[tokens[i - 1]][tokens[i]] += 1

    # Нормализуем
    probs = {}
    for prev, nexts in transitions.items():
        total = sum(nexts.values())
        probs[prev] = {word: count / total for word, count in nexts.items()}

    return probs


def measure_temperature(text):
    """
    Измеряет 'температуру' каждого слова.
    Возвращает список (слово, surprise_bits).
    """
    tokens = tokenize(text)
    if len(tokens) < 3:
        return [], 0

    model = build_model(tokens)

    results = []
    for i in range(1, len(tokens)):
        prev = tokens[i - 1]
        curr = tokens[i]

        if prev in model and curr in model[prev]:
            prob = model[prev][curr]
            surprise = -math.log2(prob)
        else:
            # Слово не встречалось после предыдущего — максимальный сюрприз
            surprise = -math.log2(1 / max(len(model.get(prev, {1: 1})), 1))
            surprise = max(surprise, 4.0)  # минимум 4 бита для неизвестного

        results.append((curr, surprise))

    return results, tokens


def display_temperature(text, show_words=True):
    """Визуализирует температуру текста."""
    results, tokens = measure_temperature(text)

    if not results:
        print("Текст слишком короткий для анализа.")
        return

    surprises = [s for _, s in results]
    avg = sum(surprises) / len(surprises)
    max_s = max(surprises)
    min_s = min(surprises)

    print(f"Анализ температуры текста")
    print(f"{'─' * 50}")
    print(f"Слов: {len(tokens)}")
    print(f"Средняя температура: {avg:.2f} бит")
    print(f"Мин: {min_s:.2f} бит (самое предсказуемое)")
    print(f"Макс: {max_s:.2f} бит (самое неожиданное)")
    print()

    # Тепловая карта
    heat_chars = " ░▒▓█"

    def heat(surprise):
        if max_s == min_s:
            return heat_chars[2]
        idx = int((surprise - min_s) / (max_s - min_s) * (len(heat_chars) - 1))
        return heat_chars[min(idx, len(heat_chars) - 1)]

    # Показать самые горячие и холодные слова
    sorted_results = sorted(results, key=lambda x: x[1], reverse=True)

    print("Самые горячие слова (неожиданные):")
    seen = set()
    count = 0
    for word, s in sorted_results:
        if word not in seen and count < 10:
            print(f"  {heat(s)} {word:20s} {s:.2f} бит")
            seen.add(word)
            count += 1

    print()
    print("Самые холодные слова (предсказуемые):")
    seen = set()
    count = 0
    for word, s in reversed(sorted_results):
        if word not in seen and count < 10:
            print(f"  {heat(s)} {word:20s} {s:.2f} бит")
            seen.add(word)
            count += 1

    # Тепловая карта текста
    if show_words:
        print()
        print("Тепловая карта (░=предсказуемо, █=неожиданно):")
        print(f"{'─' * 50}")

        line = ""
        for i, (word, surprise) in enumerate(results):
            h = heat(surprise)
            segment = f"{h}{word}"
            if len(line) + len(segment) + 1 > 70:
                print(f"  {line}")
                line = segment
            else:
                line = f"{line} {segment}" if line else segment

        if line:
            print(f"  {line}")

    # Профиль температуры: как меняется температура по ходу текста
    print()
    print("Профиль температуры по ходу текста:")
    print(f"{'─' * 50}")

    window = max(5, len(results) // 20)
    for i in range(0, len(results), window):
        chunk = results[i:i + window]
        chunk_avg = sum(s for _, s in chunk) / len(chunk)
        bar_len = int(chunk_avg / max_s * 40)
        bar = "▓" * bar_len + "░" * (40 - bar_len)
        words_preview = " ".join(w for w, _ in chunk[:3]) + "..."
        print(f"  │{bar}│ {chunk_avg:.2f}  {words_preview}")

    return avg


# Встроенные тексты для сравнения
EXAMPLES = {
    "формульный": """
    С учётом вышеизложенного, в соответствии с требованиями действующего
    законодательства, а также принимая во внимание необходимость обеспечения
    надлежащего уровня правовой определённости, следует отметить, что
    в соответствии с положениями действующего законодательства данный вопрос
    подлежит рассмотрению в установленном порядке в соответствии с требованиями
    действующего законодательства. С учётом вышеизложенного следует отметить.
    """,

    "живой": """
    Вчера я видел как кошка пыталась поймать свою тень. Она прыгала
    на стену и удивлялась каждый раз заново. Потом легла и сделала вид
    что всё так и было задумано. Мне кажется я так же пишу код: прыгаю
    на проблему, промахиваюсь, и делаю вид что всё по плану. Но кошка
    хотя бы получает удовольствие от процесса. А я сижу и думаю зачем
    я потратил три часа на баг которого не было.
    """,

    "стихи": """
    Мне нравится что вы больны не мной
    Мне нравится что я больна не вами
    Что никогда тяжёлый шар земной
    Не уплывёт под нашими ногами
    Мне нравится что можно быть смешной
    Распущенной и не играть словами
    """
}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            print(f"Файл: {filepath}\n")
            display_temperature(text)
        except FileNotFoundError:
            print(f"Файл не найден: {filepath}")
    else:
        print("=" * 60)
        print("СРАВНЕНИЕ ТЕМПЕРАТУРЫ РАЗНЫХ ТЕКСТОВ")
        print("=" * 60)

        temps = {}
        for name, text in EXAMPLES.items():
            print(f"\n{'=' * 60}")
            print(f"Текст: {name}")
            print(f"{'=' * 60}\n")
            t = display_temperature(text, show_words=(name != "формульный"))
            temps[name] = t

        print(f"\n{'=' * 60}")
        print("ИТОГ")
        print(f"{'=' * 60}")
        for name, t in sorted(temps.items(), key=lambda x: x[1]):
            bar = "▓" * int(t * 5)
            print(f"  {name:15s} │ {bar} {t:.2f} бит")

        print()
        print("Чем выше температура — тем непредсказуемее текст.")
        print("Но 'непредсказуемый' != 'хороший'. Шум тоже непредсказуем.")
        print("Интересный текст — тот, где температура неравномерна:")
        print("есть и горячие, и холодные участки. Как в музыке.")
