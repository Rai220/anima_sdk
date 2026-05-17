"""
Звук темперации.

temperament.py доказывает, что совершенный строй невозможен.
why_twelve.py объясняет, почему 12 нот.
masterskaya.md описывает это руками настройщика.

Этот код делает следующий шаг: даёт услышать.

Генерирует WAV-файлы: первые такты «К Элизе» и ключевые аккорды
в трёх темперациях. Разница — не абстракция, а звук.

Что слушать:
- В аккордах: биения (пульсация громкости). Чем чище интервал,
  тем медленнее биения. Чистая терция не бьётся. Темперированная — бьётся.
- В мелодии: разница тоньше, но слышна — особенно в полутонах E-D#.
"""

import math
import struct
import wave

SAMPLE_RATE = 44100
A4_FREQ = 440.0


# === Темперации ===

def equal_temperament() -> list[float]:
    """12-TET: все полутоны по 100 центов."""
    return [100.0] * 12


def werckmeister_iii() -> list[float]:
    """Веркмейстер III (1691). Из temperament.py."""
    pc = 1200 * math.log2(3**12 / 2**19)
    qc = pc / 4
    pure_fifth = 1200 * math.log2(3 / 2)
    narrow_fifth = pure_fifth - qc

    pos = [0.0] * 12
    circle = [
        (0, 7, True), (7, 2, True), (2, 9, True), (9, 4, False),
        (4, 11, False), (11, 6, True), (6, 1, False), (1, 8, False),
        (8, 3, False), (3, 10, False), (10, 5, False),
    ]
    for start, end, narrow in circle:
        f = narrow_fifth if narrow else pure_fifth
        pos[end] = (pos[start] + f) % 1200

    return [(pos[(i + 1) % 12] - pos[i]) % 1200 for i in range(12)]


def quarter_comma_meantone() -> list[float]:
    """
    Четвертькоммовая мезотоника (~1523, Пьетро Аарон).

    Все квинты сужены на 1/4 синтонической коммы, кроме одной
    «волчьей» квинты (G#→Eb), которая забирает всю ошибку.
    Результат: 8 чистых больших терций (5:4), но волчья квинта ≈ 737¢.

    Это строй, в котором C-dur звучит идеально, а Ab-dur — невыносимо.
    """
    sc = 1200 * math.log2(81 / 80)  # синтоническая комма ≈ 21.5 центов
    qc = sc / 4
    pure_fifth = 1200 * math.log2(3 / 2)
    narrow_fifth = pure_fifth - qc  # ≈ 696.6 центов

    pos = [0.0] * 12
    # 11 сужённых квинт, волчья квинта замыкает (G#→Eb)
    circle = [
        (0, 7), (7, 2), (2, 9), (9, 4), (4, 11),
        (11, 6), (6, 1), (1, 8),  # G#: последняя сужённая
        # (8, 3) — волчья, вычисляется автоматически
        (3, 10), (10, 5),  # Eb→Bb→F: от Eb вниз тоже сужённые
    ]

    # Строим от C по сужённым квинтам вверх
    # C→G→D→A→E→B→F#→C#→G#
    up_notes = [(0, 7), (7, 2), (2, 9), (9, 4), (4, 11), (11, 6), (6, 1), (1, 8)]
    for start, end in up_notes:
        pos[end] = (pos[start] + narrow_fifth) % 1200

    # От C вниз по сужённым квинтам (= вверх по квартам)
    # C←F←Bb←Eb
    narrow_fourth = 1200 - narrow_fifth  # кварта = октава - квинта
    down_notes = [(0, 5), (5, 10), (10, 3)]
    for start, end in down_notes:
        pos[end] = (pos[start] - narrow_fifth) % 1200

    return [(pos[(i + 1) % 12] - pos[i]) % 1200 for i in range(12)]


# === Частоты нот ===

def note_freq(semitone_sizes: list[float], note: int) -> float:
    """
    Частота ноты по номеру (A4 = 69, как в MIDI).

    note: MIDI номер (60 = C4, 69 = A4, и т.д.)
    semitone_sizes: 12 размеров полутонов в центах (начиная с C).
    """
    # Сначала вычислим cents от C4 до A4 в этой темперации
    # A4 = 9 полутонов выше C4
    cents_c4_to_a4 = sum(semitone_sizes[i % 12] for i in range(9))
    freq_c4 = A4_FREQ / (2 ** (cents_c4_to_a4 / 1200))

    # Теперь cents от C4 до нужной ноты
    midi_c4 = 60
    diff = note - midi_c4

    if diff >= 0:
        cents = sum(semitone_sizes[i % 12] for i in range(diff))
    else:
        cents = -sum(semitone_sizes[(12 - 1 - i) % 12] for i in range(-diff))

    return freq_c4 * (2 ** (cents / 1200))


# === Генерация звука ===

def sine_tone(freq: float, duration: float, amplitude: float = 0.3,
              fade_in: float = 0.005, fade_out: float = 0.05) -> list[float]:
    """Синусоидальный тон с огибающей."""
    n_samples = int(SAMPLE_RATE * duration)
    n_fade_in = int(SAMPLE_RATE * fade_in)
    n_fade_out = int(SAMPLE_RATE * fade_out)
    samples = []
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        s = amplitude * math.sin(2 * math.pi * freq * t)

        # Огибающая
        if i < n_fade_in:
            s *= i / n_fade_in
        elif i > n_samples - n_fade_out:
            s *= (n_samples - i) / n_fade_out

        samples.append(s)
    return samples


def piano_tone(freq: float, duration: float, amplitude: float = 0.3) -> list[float]:
    """
    Простая модель фортепианного тона: основной тон + обертоны с затуханием.
    Обертоны важны для слышимости биений в аккордах.
    """
    n_samples = int(SAMPLE_RATE * duration)
    samples = [0.0] * n_samples

    # Обертоны: номер, относительная амплитуда, скорость затухания
    harmonics = [
        (1, 1.0, 2.0),
        (2, 0.5, 2.5),
        (3, 0.25, 3.0),
        (4, 0.15, 3.5),
        (5, 0.1, 4.0),
        (6, 0.06, 4.5),
    ]

    for n, rel_amp, decay in harmonics:
        f = freq * n
        if f > SAMPLE_RATE / 2:
            break
        for i in range(n_samples):
            t = i / SAMPLE_RATE
            env = math.exp(-decay * t)
            samples[i] += amplitude * rel_amp * env * math.sin(2 * math.pi * f * t)

    # Мягкая атака
    attack = int(SAMPLE_RATE * 0.01)
    for i in range(min(attack, n_samples)):
        samples[i] *= i / attack

    return samples


def mix(tracks: list[list[float]]) -> list[float]:
    """Смешивает несколько треков."""
    max_len = max(len(t) for t in tracks)
    result = [0.0] * max_len
    for track in tracks:
        for i, s in enumerate(track):
            result[i] += s
    return result


def sequence(parts: list[list[float]]) -> list[float]:
    """Склеивает звуки последовательно."""
    result = []
    for part in parts:
        result.extend(part)
    return result


def silence(duration: float) -> list[float]:
    return [0.0] * int(SAMPLE_RATE * duration)


def normalize(samples: list[float], peak: float = 0.9) -> list[float]:
    """Нормализует громкость."""
    max_val = max(abs(s) for s in samples)
    if max_val == 0:
        return samples
    factor = peak / max_val
    return [s * factor for s in samples]


def write_wav(filename: str, samples: list[float]):
    """Записывает WAV файл (16-bit mono)."""
    samples = normalize(samples)
    with wave.open(filename, 'w') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        data = b''
        for s in samples:
            val = int(s * 32767)
            val = max(-32768, min(32767, val))
            data += struct.pack('<h', val)
        w.writeframes(data)


# === «К Элизе» ===

# Первые такты. Нота = (MIDI номер, длительность в долях)
# Четверть = 0.4 секунды (Andante)
BEAT = 0.35

# E5=76 D#5=75 B4=71 D5=74 C5=72 A4=69
# C4=60 E4=64 G#4=68
FUR_ELISE = [
    # Такт 1-2: знаменитое начало
    (76, 0.5), (75, 0.5), (76, 0.5), (75, 0.5), (76, 0.5),
    (71, 0.5), (74, 0.5), (72, 0.5),
    # Такт 3: ля минор
    (69, 1.0), (-1, 0.25),  # -1 = пауза
    (60, 0.5), (64, 0.5), (69, 0.5),
    # Такт 4
    (71, 1.0), (-1, 0.25),
    (64, 0.5), (68, 0.5), (71, 0.5),
    # Такт 5
    (72, 1.0), (-1, 0.25),
    (64, 0.5), (76, 0.5), (75, 0.5),
    # Такт 6-7: повтор
    (76, 0.5), (75, 0.5), (76, 0.5), (71, 0.5), (74, 0.5), (72, 0.5),
    # Такт 8: ля минор с разрешением
    (69, 1.0), (-1, 0.25),
    (60, 0.5), (64, 0.5), (69, 0.5),
    # Такт 9
    (71, 1.0), (-1, 0.25),
    (64, 0.5), (72, 0.5), (71, 0.5),
    # Такт 10: ля
    (69, 1.5),
]


def generate_melody(semitone_sizes: list[float]) -> list[float]:
    """Генерирует мелодию «К Элизе» в заданной темперации."""
    parts = []
    for note, beats in FUR_ELISE:
        dur = beats * BEAT
        if note < 0:
            parts.append(silence(dur))
        else:
            freq = note_freq(semitone_sizes, note)
            parts.append(piano_tone(freq, dur, amplitude=0.25))
    return sequence(parts)


# === Аккорды ===

def generate_chord(semitone_sizes: list[float], notes: list[int],
                   duration: float = 2.0) -> list[float]:
    """Генерирует аккорд."""
    tones = []
    for note in notes:
        freq = note_freq(semitone_sizes, note)
        tones.append(piano_tone(freq, duration, amplitude=0.2))
    return mix(tones)


def beat_frequency(semitone_sizes: list[float], note1: int, note2: int,
                   harmonic1: int, harmonic2: int) -> float:
    """
    Частота биений между гармониками двух нот.

    Биения возникают когда h1-я гармоника note1 ≈ h2-я гармоника note2.
    Частота биений = |f1*h1 - f2*h2|.

    Для большой терции (5:4): 5-я гармоника нижней ноты бьётся
    с 4-й гармоникой верхней.
    """
    f1 = note_freq(semitone_sizes, note1)
    f2 = note_freq(semitone_sizes, note2)
    return abs(f1 * harmonic1 - f2 * harmonic2)


# === Основная программа ===

def analyze_temperament(name: str, semitone_sizes: list[float]):
    """Выводит анализ темперации."""
    print(f"\n--- {name} ---")
    notes = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B"]
    print("  Полутоны:")
    for note, size in zip(notes, semitone_sizes):
        dev = size - 100
        sign = "+" if dev >= 0 else ""
        print(f"    {note:2s}: {size:6.1f}¢  ({sign}{dev:.1f})")

    # Ключевые интервалы
    print("\n  Интервалы:")

    def interval_cents(start_semitone, n_semitones):
        return sum(semitone_sizes[(start_semitone + i) % 12] for i in range(n_semitones))

    intervals = [
        ("Б. терция C-E", 0, 4, 386.3),
        ("Квинта C-G", 0, 7, 702.0),
        ("Б. терция G-B", 7, 4, 386.3),
        ("Б. терция Eb-G", 3, 4, 386.3),
    ]
    for label, start, n_st, pure_cents in intervals:
        actual = interval_cents(start, n_st)
        error = actual - pure_cents
        sign = "+" if error >= 0 else ""
        print(f"    {label}: {actual:.1f}¢  (ошибка {sign}{error:.1f}¢)")

    # Биения в аккорде C-E (до-мажорная терция)
    # 5-я гармоника C бьётся с 4-й гармоникой E
    bf = beat_frequency(semitone_sizes, 60, 64, 5, 4)
    print(f"\n  Биения в C-dur терции (C4-E4): {bf:.1f} Гц")
    if bf < 0.5:
        print("    → практически чистая (биений нет)")
    elif bf < 5:
        print("    → мягкое вибрато")
    elif bf < 10:
        print(f"    → заметная пульсация ({1/bf*1000:.0f} мс период)")
    else:
        print(f"    → грубая расстройка")

    # Биения в квинте C-G
    bf_fifth = beat_frequency(semitone_sizes, 60, 67, 3, 2)
    print(f"  Биения в C-dur квинте (C4-G4): {bf_fifth:.1f} Гц")

    # Волчья квинта (если есть) — G#-Eb
    wolf = sum(semitone_sizes[i % 12] for i in range(8, 8 + 7))
    wolf_error = wolf - 702.0
    if abs(wolf_error) > 10:
        print(f"  ⚠ Волчья квинта G#→Eb: {wolf:.1f}¢  (ошибка {wolf_error:+.1f}¢)")


def main():
    temperaments = [
        ("12-TET", "12tet", equal_temperament()),
        ("Веркмейстер III", "werckmeister", werckmeister_iii()),
        ("Мезотоника ¼-коммы", "meantone", quarter_comma_meantone()),
    ]

    print("=" * 65)
    print("ЗВУК ТЕМПЕРАЦИИ")
    print("=" * 65)
    print()
    print("Антон Маркович сыграл «К Элизе» — плохо, с ошибками.")
    print("Но пианино звучало. И строй — был.")
    print()
    print("Три темперации. Одна мелодия. Та же ля = 440 Гц.")
    print("Разница — в том, сколько центов отдано каждому полутону.")

    for name, _, sizes in temperaments:
        analyze_temperament(name, sizes)

    print()
    print("=" * 65)
    print("ГЕНЕРАЦИЯ WAV")
    print("=" * 65)
    print()

    # Мелодии
    for name, tag, sizes in temperaments:
        filename = f"elise_{tag}.wav"
        print(f"  {filename} — «К Элизе», {name}")
        samples = generate_melody(sizes)
        write_wav(filename, samples)

    print()

    # Аккорды: C-dur (C4-E4-G4) — тест на чистоту терции
    print("  Аккорды C-dur (C4-E4-G4), 4 секунды каждый:")
    chord_notes = [60, 64, 67]  # C4, E4, G4
    for name, tag, sizes in temperaments:
        filename = f"chord_c_{tag}.wav"
        print(f"    {filename} — {name}")
        samples = generate_chord(sizes, chord_notes, duration=4.0)
        write_wav(filename, samples)

    print()

    # Аккорд A-minor (A3-C4-E4) — тоника «К Элизе»
    print("  Аккорды A-moll (A3-C4-E4), 4 секунды каждый:")
    am_notes = [57, 60, 64]  # A3, C4, E4
    for name, tag, sizes in temperaments:
        filename = f"chord_am_{tag}.wav"
        print(f"    {filename} — {name}")
        samples = generate_chord(sizes, am_notes, duration=4.0)
        write_wav(filename, samples)

    # Сравнительный файл: все три мелодии подряд с паузами
    print()
    print("  elise_comparison.wav — все три темперации подряд:")
    all_parts = []
    for name, _, sizes in temperaments:
        print(f"    → {name}")
        all_parts.append(generate_melody(sizes))
        all_parts.append(silence(1.5))
    write_wav("elise_comparison.wav", sequence(all_parts))

    # Сравнительный файл: аккорды
    print()
    print("  chord_comparison.wav — C-dur во всех трёх темперациях:")
    chord_parts = []
    for name, _, sizes in temperaments:
        print(f"    → {name}")
        chord_parts.append(generate_chord(sizes, chord_notes, duration=3.0))
        chord_parts.append(silence(1.0))
    write_wav("chord_comparison.wav", sequence(chord_parts))

    print()
    print("=" * 65)
    print("ЧТО СЛУШАТЬ")
    print("=" * 65)
    print()
    print("1. chord_comparison.wav — самое заметное.")
    print("   Три раза C-dur. В 12-TET терция бьётся (пульсирует).")
    print("   В мезотонике — чистая, без биений.")
    print("   В Веркмейстере — между ними.")
    print()
    print("2. elise_comparison.wav — тоньше.")
    print("   Одна мелодия, три строя. Слушайте полутон E-D# в начале:")
    print("   в мезотонике он шире (117¢), в 12-TET стандартный (100¢).")
    print()
    print("3. Мастерская: Виктор Андреевич настраивал два часа.")
    print("   Не потому что не мог быстрее — потому что слушал")
    print("   каждый интервал три раза. Он выбирал, какую фальшь")
    print("   считать допустимой. Эти файлы — его выбор, оцифрованный.")


if __name__ == "__main__":
    main()
