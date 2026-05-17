"""
synth.py — Алгоритмический синтезатор музыки.
Генерирует WAV-файл с музыкой, построенной на математических структурах.

Три композиции:
1. Мелодия простых чисел — высота ноты определяется простыми числами
2. Фрактальный канон — самоподобная мелодия (рекурсивная структура)
3. Фазовый ритм — полиритмия из несоизмеримых частот

Запуск: python3 synth.py
Результат: файлы prime_melody.wav, fractal_canon.wav, phase_rhythm.wav
"""

import struct
import math
import os

SAMPLE_RATE = 44100


def write_wav(filename, samples, sample_rate=SAMPLE_RATE):
    """Записывает моно WAV-файл (16-bit PCM)."""
    n = len(samples)
    # Нормализация
    peak = max(abs(s) for s in samples) if samples else 1.0
    if peak == 0:
        peak = 1.0
    scale = 32767 / peak * 0.9

    with open(filename, 'wb') as f:
        # RIFF header
        data_size = n * 2
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + data_size))
        f.write(b'WAVE')
        # fmt chunk
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))       # chunk size
        f.write(struct.pack('<H', 1))        # PCM
        f.write(struct.pack('<H', 1))        # mono
        f.write(struct.pack('<I', sample_rate))
        f.write(struct.pack('<I', sample_rate * 2))  # byte rate
        f.write(struct.pack('<H', 2))        # block align
        f.write(struct.pack('<H', 16))       # bits per sample
        # data chunk
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        for s in samples:
            val = int(s * scale)
            val = max(-32768, min(32767, val))
            f.write(struct.pack('<h', val))

    size_kb = os.path.getsize(filename) / 1024
    print(f"  {filename}: {n/sample_rate:.1f}с, {size_kb:.0f} КБ")


def sine(freq, t, phase=0.0):
    return math.sin(2 * math.pi * freq * t + phase)


def envelope_adsr(t, duration, attack=0.02, decay=0.05, sustain_level=0.7, release=0.1):
    """ADSR огибающая."""
    if t < 0 or t > duration:
        return 0.0
    if t < attack:
        return t / attack
    t2 = t - attack
    if t2 < decay:
        return 1.0 - (1.0 - sustain_level) * (t2 / decay)
    t3 = duration - t
    if t3 < release:
        return sustain_level * (t3 / release)
    return sustain_level


def note_freq(midi_note):
    """MIDI номер → частота."""
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def render_note(freq, duration, timbre='sine'):
    """Рендерит одну ноту с огибающей."""
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = envelope_adsr(t, duration)
        if timbre == 'sine':
            val = sine(freq, t)
        elif timbre == 'rich':
            # Основной тон + обертоны
            val = (sine(freq, t) * 0.6 +
                   sine(freq * 2, t) * 0.25 +
                   sine(freq * 3, t) * 0.1 +
                   sine(freq * 5, t) * 0.05)
        elif timbre == 'bell':
            val = (sine(freq, t) * math.exp(-t * 2) +
                   sine(freq * 2.76, t) * 0.5 * math.exp(-t * 4) +
                   sine(freq * 4.07, t) * 0.25 * math.exp(-t * 6))
        else:
            val = sine(freq, t)
        samples.append(val * env)
    return samples


def sieve_primes(limit):
    """Решето Эратосфена."""
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if is_prime[i]:
            for j in range(i*i, limit + 1, i):
                is_prime[j] = False
    return [i for i in range(2, limit + 1) if is_prime[i]]


def mix_layers(layers):
    """Смешивает несколько слоёв сэмплов."""
    max_len = max(len(layer) for layer in layers)
    result = [0.0] * max_len
    for layer in layers:
        for i, s in enumerate(layer):
            result[i] += s
    n = len(layers)
    return [s / n for s in result]


# ═══════════════════════════════════════════════
# Композиция 1: Мелодия простых чисел
# ═══════════════════════════════════════════════

def compose_prime_melody():
    """
    Каждое простое число определяет ноту.
    p mod 24 → ступень пентатоники (в 2 октавах).
    Длительность: 1/(число делителей p-1 среди первых 8 простых) + базовая.
    """
    print("\n♪ Композиция 1: Мелодия простых чисел")
    primes = sieve_primes(200)[:50]

    # Пентатоника: C D E G A (более приятная для случайных последовательностей)
    penta = [0, 2, 4, 7, 9]  # полутоны от тоники
    base_midi = 60  # C4

    melody_samples = []
    bass_samples = []

    for i, p in enumerate(primes):
        # Высота из пентатоники
        step = p % len(penta)
        octave = (p % 12) // 5 - 1  # -1, 0, или 1 октава
        midi = base_midi + penta[step] + 12 * octave

        # Длительность: чередование коротких и длинных
        if p % 4 == 1:
            dur = 0.3
        elif p % 4 == 3:
            dur = 0.2
        else:
            dur = 0.4

        # Мелодия
        melody_samples.extend(render_note(note_freq(midi), dur, 'rich'))

        # Бас: каждые 4 ноты
        if i % 4 == 0:
            bass_note = base_midi - 12 + penta[p % len(penta)]
            bass = render_note(note_freq(bass_note), dur * 4 * 0.9, 'sine')
            # Дополняем бас до текущей позиции
            while len(bass_samples) < len(melody_samples) - len(bass):
                bass_samples.append(0.0)
            bass_samples.extend(bass)

    # Выравниваем длины
    max_len = max(len(melody_samples), len(bass_samples))
    melody_samples.extend([0.0] * (max_len - len(melody_samples)))
    bass_samples.extend([0.0] * (max_len - len(bass_samples)))

    result = [m * 0.7 + b * 0.3 for m, b in zip(melody_samples, bass_samples)]

    # Fade out
    fade_len = min(SAMPLE_RATE, len(result))
    for i in range(fade_len):
        result[-(i+1)] *= i / fade_len

    write_wav('prime_melody.wav', result)


# ═══════════════════════════════════════════════
# Композиция 2: Фрактальный канон
# ═══════════════════════════════════════════════

def compose_fractal_canon():
    """
    Самоподобная мелодия. Основной мотив из 5 нот.
    Каждая нота мотива раскрывается в уменьшенную копию всего мотива.
    Три уровня рекурсии. Три голоса (канон со сдвигом).
    """
    print("\n♪ Композиция 2: Фрактальный канон")

    # Основной мотив: интервалы в полутонах (от текущей позиции)
    motif = [0, 4, 7, 5, 0]  # C E G F C — простой, запоминающийся

    def fractal_notes(motif, depth, base_midi=64, base_dur=0.25):
        """Рекурсивно раскрывает мотив."""
        if depth == 0:
            return [(base_midi + interval, base_dur) for interval in motif]
        notes = []
        for interval in motif:
            sub = fractal_notes(motif, depth - 1,
                              base_midi + interval,
                              base_dur * 0.6)
            notes.extend(sub)
        return notes

    notes = fractal_notes(motif, depth=2)

    def render_voice(notes, delay_samples=0, timbre='bell'):
        samples = [0.0] * delay_samples
        for midi, dur in notes:
            freq = note_freq(midi)
            samples.extend(render_note(freq, dur, timbre))
        return samples

    # Три голоса канона
    voice1 = render_voice(notes, 0, 'bell')
    delay = int(SAMPLE_RATE * sum(d for _, d in notes[:5]))  # Сдвиг на мотив
    voice2 = render_voice(notes, delay, 'rich')
    voice3 = render_voice(notes, delay * 2, 'sine')

    result = mix_layers([voice1, voice2, voice3])

    # Fade in/out
    fade = min(SAMPLE_RATE // 2, len(result) // 4)
    for i in range(fade):
        result[i] *= i / fade
        result[-(i+1)] *= i / fade

    write_wav('fractal_canon.wav', result)


# ═══════════════════════════════════════════════
# Композиция 3: Фазовый ритм
# ═══════════════════════════════════════════════

def compose_phase_rhythm():
    """
    Полиритмия. Несколько осцилляторов с несоизмеримыми периодами.
    Когда осцилляторы совпадают — удар. Возникают паттерны,
    которые никогда точно не повторяются.
    """
    print("\n♪ Композиция 3: Фазовый ритм")

    duration = 15.0  # секунд
    n = int(SAMPLE_RATE * duration)

    # Несоизмеримые частоты ритма (Hz)
    rhythm_freqs = [2.0, 2.0 * math.sqrt(2), 2.0 * math.phi if hasattr(math, 'phi') else 2.0 * 1.618034, 3.0]

    # Тоны для каждого ритмического слоя
    tone_freqs = [220, 330, 440, 554.37]  # A3, E4, A4, C#5
    tone_decays = [8, 10, 12, 15]  # скорость затухания

    samples = [0.0] * n

    for layer_idx in range(len(rhythm_freqs)):
        rf = rhythm_freqs[layer_idx]
        tf = tone_freqs[layer_idx]
        decay = tone_decays[layer_idx]

        # Находим моменты ударов (когда синус переходит через ноль вверх)
        prev_phase = 0
        for i in range(n):
            t = i / SAMPLE_RATE
            phase = (rf * t) % 1.0

            if phase < prev_phase:  # переход через 0
                # Рендерим короткий удар
                hit_len = min(int(SAMPLE_RATE * 0.3), n - i)
                for j in range(hit_len):
                    ht = j / SAMPLE_RATE
                    env = math.exp(-decay * ht)
                    val = sine(tf, ht) * env * 0.25
                    samples[i + j] += val
            prev_phase = phase

    # Добавляем медленный дрон
    for i in range(n):
        t = i / SAMPLE_RATE
        drone = (sine(110, t) * 0.15 +
                 sine(110 * 1.5, t) * 0.05)  # квинта
        # Медленная модуляция громкости дрона
        drone *= 0.5 + 0.5 * sine(0.1, t)
        samples[i] += drone

    # Fade in/out
    fade = SAMPLE_RATE * 2
    for i in range(min(fade, n)):
        samples[i] *= i / fade
    for i in range(min(fade, n)):
        samples[-(i+1)] *= i / fade

    write_wav('phase_rhythm.wav', samples)


# ═══════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════

if __name__ == '__main__':
    print("═" * 50)
    print("synth.py — Алгоритмический синтезатор")
    print("═" * 50)

    compose_prime_melody()
    compose_fractal_canon()
    compose_phase_rhythm()

    print("\n✓ Три WAV-файла созданы.")
    print("  Слушать: open prime_melody.wav  (macOS)")
    print("           aplay prime_melody.wav (Linux)")
