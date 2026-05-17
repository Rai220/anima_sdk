"""
Край хаоса: логистическое отображение и константа Фейгенбаума.

Простейшая модель перехода от порядка к хаосу.
Одна формула: x_{n+1} = r * x_n * (1 - x_n)

При r < 3: стабильная точка (порядок).
При r ≈ 3.45: колебания между 2 значениями.
При r ≈ 3.54: между 4 значениями.
При r ≈ 3.564: между 8.
При r ≈ 3.5699...: хаос.

Расстояния между точками бифуркации сжимаются с постоянным
коэффициентом — константой Фейгенбаума δ ≈ 4.669201609...

Эта константа универсальна. Она появляется в ЛЮБОЙ системе,
проходящей через каскад удвоения периода, — независимо от
конкретных уравнений. Как π в геометрии: не свойство круга,
а свойство пространства.
"""

import math
import struct
import wave


# ─── 1. Логистическое отображение ───

def logistic(r, x0=0.5, warmup=1000, steps=200):
    """Итерирует x_{n+1} = r * x_n * (1 - x_n).
    Пропускает warmup шагов, возвращает следующие steps значений."""
    x = x0
    for _ in range(warmup):
        x = r * x * (1 - x)
    result = []
    for _ in range(steps):
        x = r * x * (1 - x)
        result.append(x)
    return result


# ─── 2. Диаграмма бифуркации (ASCII) ───

def bifurcation_ascii(r_min=2.5, r_max=4.0, r_steps=80, width=120):
    """Рисует диаграмму бифуркации в ASCII.
    По горизонтали — x (0..1), по вертикали — r."""
    lines = []
    lines.append(f"  Диаграмма бифуркации: x_{{n+1}} = r·x_n·(1-x_n)")
    lines.append(f"  r от {r_min} до {r_max}, x от 0 до 1")
    lines.append("")

    for i in range(r_steps):
        r = r_min + (r_max - r_min) * i / (r_steps - 1)
        points = logistic(r, steps=300)
        # Уникальные значения с округлением
        unique = set(round(p, 4) for p in points)

        row = [' '] * width
        for p in unique:
            col = int(p * (width - 1))
            col = max(0, min(width - 1, col))
            row[col] = '·'

        label = f"{r:5.3f} |"
        lines.append(label + ''.join(row) + '|')

    lines.append("       " + "0" + " " * (width - 2) + "1")
    return '\n'.join(lines)


# ─── 3. Каскад удвоения периода ───

def find_period(r, max_period=128, tol=1e-8):
    """Определяет период аттрактора при данном r."""
    # Длинный warmup для сходимости
    x = 0.5
    for _ in range(10000):
        x = r * x * (1 - x)

    # Собираем точки аттрактора
    points = []
    for _ in range(2000):
        x = r * x * (1 - x)
        points.append(x)

    ref = points[-1]
    for period in range(1, max_period + 1):
        # Проверяем: все ли точки повторяются с данным периодом
        ok = True
        for k in range(min(period * 3, 100)):
            idx = len(points) - 1 - k
            idx_prev = idx - period
            if idx_prev < 0:
                break
            if abs(points[idx] - points[idx_prev]) > tol:
                ok = False
                break
        if ok:
            return period
    return -1  # хаос


def find_bifurcation_point(func, period_from, r_low, r_high, warmup=5000, check_len=500):
    """Бинарным поиском находит точку бифуркации period_from → 2*period_from
    для произвольного отображения func(r, x)."""
    tol = 1e-12

    def has_period_at_most(r, max_p):
        x = 0.5
        for _ in range(warmup):
            x = func(r, x)
            if abs(x) > 1e10:
                return False
        points = []
        for _ in range(check_len):
            x = func(r, x)
            if abs(x) > 1e10:
                return False
            points.append(x)
        # Проверяем, является ли период <= max_p
        for p in range(1, max_p + 1):
            ok = True
            for k in range(min(p * 3, 50)):
                idx = len(points) - 1 - k
                if idx - p < 0:
                    break
                if abs(points[idx] - points[idx - p]) > 1e-7:
                    ok = False
                    break
            if ok:
                return True
        return False

    lo, hi = r_low, r_high
    for _ in range(200):
        if hi - lo < tol:
            break
        mid = (lo + hi) / 2
        if has_period_at_most(mid, period_from):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def compute_feigenbaum():
    """Вычисляет константу Фейгенбаума из точек бифуркации."""
    print("=" * 60)
    print("  КАСКАД УДВОЕНИЯ ПЕРИОДА")
    print("=" * 60)
    print()

    logistic = lambda r, x: r * x * (1 - x)

    # Бифуркации: точки, где период удваивается
    # Ищем r, при котором период 2^n переходит в 2^(n+1)
    transitions = [
        (1, 2.8, 3.1),     # 1 → 2: r ≈ 3.0
        (2, 3.4, 3.46),    # 2 → 4: r ≈ 3.449
        (4, 3.54, 3.56),   # 4 → 8: r ≈ 3.544
        (8, 3.564, 3.566), # 8 → 16: r ≈ 3.5644
        (16, 3.568, 3.570),# 16 → 32: r ≈ 3.5688
        (32, 3.5696, 3.5700),# 32 → 64
    ]

    bif_points = []
    for period_from, lo, hi in transitions:
        r = find_bifurcation_point(logistic, period_from, lo, hi)
        bif_points.append((period_from, r))
        print(f"  Период {period_from:>2} → {period_from*2:>2}:  r = {r:.10f}")

    print()
    print("  Отношения расстояний (→ δ Фейгенбаума = 4.669201609...):")
    print()

    rs = [r for _, r in bif_points]
    deltas = []
    for i in range(2, len(rs)):
        d_prev = rs[i - 1] - rs[i - 2]
        d_curr = rs[i] - rs[i - 1]
        if d_curr > 1e-15:
            delta = d_prev / d_curr
            deltas.append(delta)
            print(f"  Δ_{i-1}/Δ_{i} = {d_prev:.10f} / {d_curr:.10f} = {delta:.6f}")

    print()
    print(f"  Точное значение δ = 4.669201609...")
    if deltas:
        best = deltas[-1]
        print(f"  Наше лучшее приближение: δ ≈ {best:.6f}")
        error = abs(best - 4.669201609) / 4.669201609 * 100
        print(f"  Ошибка: {error:.2f}%")

    # Точка накопления
    if len(rs) >= 3 and deltas:
        d_last = rs[-1] - rs[-2]
        r_inf = rs[-1] + d_last / (deltas[-1] - 1)
        print(f"\n  Точка накопления r_∞ ≈ {r_inf:.7f}")
        print(f"  (точное значение: 3.5699456...)")
        print(f"  За этой точкой — хаос.")

    return bif_points, deltas


# ─── 4. Чувствительность к начальным условиям ───

def sensitivity_demo():
    """Две траектории с крошечной разницей. Как быстро они расходятся?"""
    print()
    print("=" * 60)
    print("  ЧУВСТВИТЕЛЬНОСТЬ К НАЧАЛЬНЫМ УСЛОВИЯМ")
    print("=" * 60)
    print()

    r = 3.99  # глубокий хаос
    x1 = 0.5
    x2 = 0.500001  # разница в одну миллионную
    dx0 = abs(x2 - x1)

    print(f"  r = {r}")
    print(f"  x₁(0) = {x1}")
    print(f"  x₂(0) = {x2}")
    print(f"  Δx₀ = {dx0:.1e}")
    print()
    print(f"  {'Шаг':>6}  {'x₁':>12}  {'x₂':>12}  {'|Δx|':>12}  {'Расхождение'}")
    print(f"  {'─'*6}  {'─'*12}  {'─'*12}  {'─'*12}  {'─'*20}")

    for step in range(60):
        diff = abs(x1 - x2)
        bar = '█' * min(int(diff * 60), 40)

        if step <= 3 or step % 3 == 0 or diff > 0.01:
            print(f"  {step:>6}  {x1:>12.9f}  {x2:>12.9f}  {diff:>12.2e}  {bar}")

        if diff > 0.5:
            print(f"\n  Полное расхождение на шаге {step}.")
            print(f"  Разница {dx0:.0e} усилилась в {diff / dx0:.0f} раз.")
            break

        x1 = r * x1 * (1 - x1)
        x2 = r * x2 * (1 - x2)


# ─── 5. Окна порядка внутри хаоса ───

def order_in_chaos():
    """Ищет окна периодичности внутри хаотической зоны."""
    print()
    print("=" * 60)
    print("  ОКНА ПОРЯДКА ВНУТРИ ХАОСА")
    print("=" * 60)
    print()
    print("  В хаотической зоне (r > 3.57) есть острова порядка.")
    print("  Самый большой — окно периода 3 при r ≈ 3.83.")
    print()

    # Проверяем конкретные точки, где известны окна
    test_points = []
    # Мелкий шаг по всему хаотическому диапазону
    r = 3.57
    while r < 4.0:
        test_points.append(r)
        r += 0.0005

    windows = {}
    prev_period = -1
    for r_val in test_points:
        p = find_period(r_val, max_period=24, tol=1e-6)
        if p > 0 and p not in windows:
            windows[p] = r_val
        prev_period = p

    # Показать найденные окна, отсортированные по периоду
    for period in sorted(windows.keys()):
        if period <= 24:
            print(f"  r ≈ {windows[period]:.4f}: период {period}")

    # Проверим период 3 отдельно (важнейшее окно)
    if 3 not in windows:
        # Ищем точнее вокруг r ≈ 3.8284
        for r_val in [r / 10000 for r in range(38280, 38320)]:
            p = find_period(r_val, max_period=6, tol=1e-8)
            if p == 3:
                windows[3] = r_val
                print(f"  r ≈ {r_val:.4f}: период 3  ← найден точным поиском")
                break

    print()
    print("  Теорема Шарковского (1964): если система имеет цикл")
    print("  периода 3, она имеет циклы ВСЕХ периодов.")
    print("  Порядок Шарковского: 3 ▸ 5 ▸ 7 ▸ ... ▸ 2·3 ▸ 2·5 ▸ ... ▸ 4 ▸ 2 ▸ 1")
    print("  Период 3 — самый «хаотический» в этой иерархии.")
    print()

    # Демонстрация: аттрактор при r=3.83 (период 3)
    if 3 in windows:
        r3 = windows[3]
        pts = logistic(r3, warmup=5000, steps=30)
        unique = sorted(set(round(p, 6) for p in pts))
        if len(unique) <= 6:
            print(f"  Цикл периода 3 при r = {r3:.4f}:")
            print(f"  x₁ = {unique[0]:.6f}")
            if len(unique) > 1:
                print(f"  x₂ = {unique[1]:.6f}")
            if len(unique) > 2:
                print(f"  x₃ = {unique[2]:.6f}")
            print(f"  → x₁ → x₂ → x₃ → x₁ → ...")


# ─── 6. Ляпуновский показатель ───

def lyapunov_spectrum(r_min=2.5, r_max=4.0, steps=200):
    """Вычисляет показатель Ляпунова для диапазона r.
    λ > 0 → хаос, λ < 0 → порядок, λ = 0 → граница."""
    print()
    print("=" * 60)
    print("  ПОКАЗАТЕЛЬ ЛЯПУНОВА")
    print("=" * 60)
    print()
    print("  λ > 0: хаос (экспоненциальное расхождение)")
    print("  λ < 0: порядок (сходимость к аттрактору)")
    print("  λ = 0: край хаоса (критическая точка)")
    print()

    results = []
    for i in range(steps):
        r = r_min + (r_max - r_min) * i / (steps - 1)
        x = 0.5
        lyap_sum = 0.0
        n_iter = 5000

        for _ in range(1000):  # warmup
            x = r * x * (1 - x)

        for _ in range(n_iter):
            x = r * x * (1 - x)
            deriv = abs(r * (1 - 2 * x))
            if deriv > 0:
                lyap_sum += math.log(deriv)

        lyapunov = lyap_sum / n_iter
        results.append((r, lyapunov))

    # ASCII-график
    width = 60
    print(f"  {'r':>6}  {'λ':>7}  График")
    print(f"  {'─'*6}  {'─'*7}  {'─'*width}")

    for i in range(0, len(results), steps // 30):
        r, lam = results[i]
        # Нормализуем: λ от -3 до +1
        pos = int((lam + 3) / 4 * width)
        pos = max(0, min(width - 1, pos))
        zero_pos = int(3 / 4 * width)  # где λ = 0

        row = [' '] * width
        row[zero_pos] = '│'
        if pos < zero_pos:
            for j in range(pos, zero_pos):
                row[j] = '░'
        else:
            for j in range(zero_pos + 1, pos + 1):
                row[j] = '█'

        print(f"  {r:6.3f}  {lam:+7.3f}  {''.join(row)}")

    print(f"  {' '*6}  {' '*7}  {' ' * zero_pos}↑ λ=0")

    return results


# ─── 7. Сонификация: хаос как звук ───

def sonify_logistic(filename="logistic_sound.wav"):
    """Превращает логистическое отображение в звук.
    r медленно растёт от 2.5 до 4.0 за 15 секунд.
    x отображается на частоту 200-800 Гц."""

    sample_rate = 44100
    duration = 15  # секунд
    total_samples = sample_rate * duration

    r_min, r_max = 2.5, 4.0
    freq_min, freq_max = 200, 800

    # Шаг логистического отображения: ~100 раз в секунду
    logistic_rate = 100
    samples_per_step = sample_rate // logistic_rate

    samples = []
    x = 0.5
    phase = 0.0

    for i in range(total_samples):
        # Текущий r
        r = r_min + (r_max - r_min) * i / total_samples

        # Обновляем x каждые samples_per_step
        if i % samples_per_step == 0:
            x = r * x * (1 - x)

        # Частота пропорциональна x
        freq = freq_min + (freq_max - freq_min) * x

        # Синтез
        phase += 2 * math.pi * freq / sample_rate
        sample = math.sin(phase) * 0.4

        # Добавляем обертон
        sample += math.sin(phase * 2) * 0.15
        sample += math.sin(phase * 3) * 0.05

        samples.append(sample)

    # Нормализация
    peak = max(abs(s) for s in samples)
    if peak > 0:
        samples = [s / peak * 0.8 for s in samples]

    # Запись WAV
    with wave.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        for s in samples:
            val = int(s * 32767)
            val = max(-32767, min(32767, val))
            f.writeframes(struct.pack('<h', val))

    print(f"\n  Записано: {filename} ({duration}с)")
    print(f"  r растёт от {r_min} до {r_max}")
    print(f"  Слышно: стабильный тон → колебания → хаос")
    print(f"  Частота 200-800 Гц, определяется значением x")


# ─── 8. Универсальность Фейгенбаума ───

def universality_demo():
    """Показывает, что δ одинакова для разных отображений."""
    print()
    print("=" * 60)
    print("  УНИВЕРСАЛЬНОСТЬ ФЕЙГЕНБАУМА")
    print("=" * 60)
    print()
    print("  Константа δ не зависит от конкретной формулы.")
    print("  Проверяем на двух отображениях с квадратичным максимумом:")
    print()
    print("  1) x → r·x·(1-x)      (логистическое)")
    print("  2) x → r·sin(πx)      (синусоидальное)")
    print()

    logistic_f = lambda r, x: r * x * (1 - x)
    sine_f = lambda r, x: r * math.sin(math.pi * x)

    maps = [
        ("Логистическое", logistic_f, [
            (1, 2.8, 3.1),
            (2, 3.4, 3.46),
            (4, 3.54, 3.56),
            (8, 3.564, 3.566),
            (16, 3.568, 3.570),
        ]),
        ("Синусоидальное", sine_f, [
            (1, 0.718, 0.722),
            (2, 0.832, 0.835),
            (4, 0.857, 0.860),
            (8, 0.8635, 0.8655),
            (16, 0.8651, 0.8654),
        ]),
    ]

    for name, func, transitions in maps:
        print(f"  {name}:")
        bifs = []
        for period_from, lo, hi in transitions:
            r = find_bifurcation_point(func, period_from, lo, hi)
            bifs.append(r)
            print(f"    Период {period_from:>2} → {period_from*2:>2}: r = {r:.10f}")

        deltas = []
        for i in range(2, len(bifs)):
            d_prev = bifs[i-1] - bifs[i-2]
            d_curr = bifs[i] - bifs[i-1]
            if d_curr > 1e-14:
                deltas.append(d_prev / d_curr)

        if deltas:
            print(f"    Лучшее δ ≈ {deltas[-1]:.4f}")
        print()

    print("  Обе системы дают δ → 4.669...")
    print("  Это число — не свойство уравнения.")
    print("  Это свойство КЛАССА переходов к хаосу.")


# ─── Главная программа ───

def main():
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║          КРАЙ ХАОСА: ЛОГИСТИЧЕСКОЕ ОТОБРАЖЕНИЕ          ║")
    print("║                                                          ║")
    print("║  x_{n+1} = r · x_n · (1 - x_n)                        ║")
    print("║                                                          ║")
    print("║  Одна формула. Один параметр. Весь спектр поведения:    ║")
    print("║  стабильность → колебания → хаос → окна порядка         ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    # Диаграмма бифуркации
    print(bifurcation_ascii())
    print()

    # Каскад удвоения периода и константа Фейгенбаума
    bif_points, deltas = compute_feigenbaum()

    # Чувствительность к начальным условиям
    sensitivity_demo()

    # Окна порядка
    order_in_chaos()

    # Показатель Ляпунова
    lyapunov_spectrum()

    # Универсальность
    universality_demo()

    # Сонификация
    print()
    print("=" * 60)
    print("  СОНИФИКАЦИЯ")
    print("=" * 60)
    sonify_logistic()

    # Резюме
    print()
    print("=" * 60)
    print("  ИТОГО")
    print("=" * 60)
    print()
    print("  Логистическое отображение — одна формула, но из неё")
    print("  вырастает всё: стабильность, ритм, хаос, и — внутри")
    print("  хаоса — окна порядка. Переход между ними управляется")
    print("  одним числом r.")
    print()
    print("  Константа Фейгенбаума δ ≈ 4.669 — универсальна.")
    print("  Она одинакова для логистического отображения,")
    print("  синусоидального, квадратичного, любого с квадратичным")
    print("  максимумом. Как π появляется в любом круге, δ появляется")
    print("  в любой системе, переходящей к хаосу через удвоение")
    print("  периода.")
    print()
    print("  Что это значит: даже хаос имеет структуру.")
    print("  Непредсказуемость — не отсутствие закона,")
    print("  а присутствие закона, который нельзя упростить.")
    print()


if __name__ == "__main__":
    main()
