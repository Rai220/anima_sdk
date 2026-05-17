"""
Модель Изинга на квадратной решётке.
Монте-Карло, алгоритм Метрополиса.

Девятнадцать итераций исследовали фазовые переходы — и никто не сделал
модель, с которой всё началось. Эрнст Изинг решил одномерный случай
в 1924 году (нет перехода). Ларс Онзагер решил двумерный в 1944 году
(переход есть, T_c = 2/ln(1+√2) ≈ 2.269).

Запуск: python3 ising.py
"""

import math
import random
import struct
import zlib

# --- Параметры ---
L = 50           # размер решётки
N = L * L
EQUIL = 5000     # шагов термализации (в свипах)
MEASURE = 3000   # шагов измерения
TEMPS = 30       # количество температур

T_C_EXACT = 2.0 / math.log(1 + math.sqrt(2))  # ≈ 2.269

# --- Решётка ---
def make_lattice(L, hot=True):
    if hot:
        return [[random.choice([-1, 1]) for _ in range(L)] for _ in range(L)]
    else:
        return [[1] * L for _ in range(L)]

def energy(lattice, L):
    E = 0
    for i in range(L):
        for j in range(L):
            s = lattice[i][j]
            E -= s * (lattice[(i+1)%L][j] + lattice[i][(j+1)%L])
    return E

def magnetization(lattice, L):
    return sum(lattice[i][j] for i in range(L) for j in range(L))

def metropolis_sweep(lattice, L, beta):
    """Один свип: N попыток переворота."""
    for _ in range(L * L):
        i = random.randint(0, L-1)
        j = random.randint(0, L-1)
        s = lattice[i][j]
        nb = (lattice[(i-1)%L][j] + lattice[(i+1)%L][j] +
              lattice[i][(j-1)%L] + lattice[i][(j+1)%L])
        dE = 2 * s * nb
        if dE <= 0 or random.random() < math.exp(-beta * dE):
            lattice[i][j] = -s

def simulate(T, L, equil, measure):
    """Симуляция при температуре T. Возвращает <|m|>, <e>, χ, C_v."""
    beta = 1.0 / T
    lattice = make_lattice(L, hot=(T > T_C_EXACT))

    # Термализация
    for _ in range(equil):
        metropolis_sweep(lattice, L, beta)

    # Измерения
    E_sum = 0.0
    E2_sum = 0.0
    M_sum = 0.0
    M2_sum = 0.0
    absM_sum = 0.0

    for _ in range(measure):
        metropolis_sweep(lattice, L, beta)
        E = energy(lattice, L)
        M = magnetization(lattice, L)
        E_sum += E
        E2_sum += E * E
        M_sum += M
        M2_sum += M * M
        absM_sum += abs(M)

    e_avg = E_sum / measure / N
    e2_avg = E2_sum / measure / (N * N)
    m_avg = absM_sum / measure / N
    m2_avg = M2_sum / measure / (N * N)

    Cv = (e2_avg - (E_sum / measure / N)**2) * N * beta * beta
    chi = (m2_avg - (absM_sum / measure / N)**2) * N * beta

    return m_avg, e_avg, chi, Cv, lattice

# --- PNG writer (без зависимостей) ---
def write_png(filename, pixels, width, height):
    """pixels: list of (r, g, b) tuples, row-major."""
    def chunk(ctype, data):
        c = ctype + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return struct.pack('>I', len(data)) + c + crc

    raw = b''
    for y in range(height):
        raw += b'\x00'  # filter: none
        for x in range(width):
            r, g, b = pixels[y * width + x]
            raw += bytes([r, g, b])

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(raw, 9)

    with open(filename, 'wb') as f:
        f.write(sig)
        f.write(chunk(b'IHDR', ihdr))
        f.write(chunk(b'IDAT', idat))
        f.write(chunk(b'IEND', b''))

def color_spin(s):
    """Спин → цвет."""
    if s == 1:
        return (30, 60, 140)    # тёмно-синий
    else:
        return (240, 200, 50)   # золотой

def color_lerp(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def draw_lattice(lattice, L, cell=6):
    """Решётка → список пикселей."""
    w = L * cell
    h = L * cell
    pixels = [(0, 0, 0)] * (w * h)
    for i in range(L):
        for j in range(L):
            c = color_spin(lattice[i][j])
            for di in range(cell):
                for dj in range(cell):
                    pixels[(i * cell + di) * w + j * cell + dj] = c
    return pixels, w, h

def draw_curve(temps, values, width, height, mark_tc=True, ylabel="", color=(255, 100, 50)):
    """Кривая на белом фоне."""
    pixels = [(255, 255, 255)] * (width * height)
    margin_l, margin_r, margin_t, margin_b = 60, 20, 30, 40
    pw = width - margin_l - margin_r
    ph = height - margin_t - margin_b

    t_min, t_max = min(temps), max(temps)
    v_min, v_max = min(values), max(values)
    if v_max == v_min:
        v_max = v_min + 1
    v_range = v_max - v_min
    v_min -= v_range * 0.05
    v_max += v_range * 0.05

    def to_pixel(t, v):
        x = margin_l + int((t - t_min) / (t_max - t_min) * pw)
        y = margin_t + int((1 - (v - v_min) / (v_max - v_min)) * ph)
        return x, y

    # Оси
    for x in range(margin_l, width - margin_r):
        if 0 <= margin_t + ph < height:
            pixels[(margin_t + ph) * width + x] = (0, 0, 0)
    for y in range(margin_t, margin_t + ph + 1):
        pixels[y * width + margin_l] = (0, 0, 0)

    # T_c вертикальная линия
    if mark_tc:
        tc_x = margin_l + int((T_C_EXACT - t_min) / (t_max - t_min) * pw)
        for y in range(margin_t, margin_t + ph):
            if 0 <= tc_x < width:
                if y % 4 < 2:  # пунктир
                    pixels[y * width + tc_x] = (200, 50, 50)

    # Точки данных
    for t, v in zip(temps, values):
        cx, cy = to_pixel(t, v)
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                if dx*dx + dy*dy <= 9:
                    px, py = cx + dx, cy + dy
                    if 0 <= px < width and 0 <= py < height:
                        pixels[py * width + px] = color

    # Теоретическая кривая намагниченности (Онзагер) — если это кривая m(T)
    if ylabel == "m":
        for px_i in range(pw):
            T_val = t_min + px_i / pw * (t_max - t_min)
            if T_val < T_C_EXACT:
                arg = math.sinh(2.0 / T_val)
                if arg > 0:
                    m_th = (1 - 1.0 / (arg ** 4)) ** (1.0 / 8)
                    if m_th >= 0:
                        x = margin_l + px_i
                        y = margin_t + int((1 - (m_th - v_min) / (v_max - v_min)) * ph)
                        if 0 <= y < height:
                            for dy in range(-1, 2):
                                for dx in range(-1, 2):
                                    ny, nx = y + dy, x + dx
                                    if 0 <= ny < height and 0 <= nx < width:
                                        pixels[ny * width + nx] = (50, 50, 50)
            # Выше T_c: m = 0
            else:
                x = margin_l + px_i
                y = margin_t + int((1 - (0 - v_min) / (v_max - v_min)) * ph)
                if 0 <= y < height:
                    for dx in range(-1, 2):
                        nx = x + dx
                        if 0 <= nx < width:
                            pixels[y * width + nx] = (50, 50, 50)

    return pixels

def compose_image(lattices, temps_data, mags_data, chis_data):
    """Три решётки сверху, две кривые снизу."""
    cell = 6
    lat_w = L * cell  # 300
    lat_h = L * cell   # 300
    gap = 20

    total_w = 3 * lat_w + 4 * gap  # 980
    curve_h = 300
    total_h = lat_h + curve_h + 3 * gap  # 640

    img = [(240, 240, 240)] * (total_w * total_h)

    # Три решётки
    labels = ["T = {:.2f} (< T_c)", "T = {:.2f} (≈ T_c)", "T = {:.2f} (> T_c)"]
    for idx, (lat, T_val) in enumerate(lattices):
        lat_pixels, lw, lh = draw_lattice(lat, L, cell)
        ox = gap + idx * (lat_w + gap)
        oy = gap
        for y in range(lh):
            for x in range(lw):
                img[(oy + y) * total_w + (ox + x)] = lat_pixels[y * lw + x]

    # Кривая намагниченности (левая половина)
    cw = total_w // 2
    ch = curve_h
    m_pixels = draw_curve(temps_data, mags_data, cw, ch, mark_tc=True, ylabel="m", color=(30, 60, 140))
    ox, oy = 0, lat_h + 2 * gap
    for y in range(ch):
        for x in range(cw):
            img[(oy + y) * total_w + (ox + x)] = m_pixels[y * cw + x]

    # Кривая восприимчивости (правая половина)
    chi_pixels = draw_curve(temps_data, chis_data, cw, ch, mark_tc=True, ylabel="chi", color=(200, 50, 50))
    ox = total_w // 2
    for y in range(ch):
        for x in range(cw):
            img[(oy + y) * total_w + (ox + x)] = chi_pixels[y * cw + x]

    return img, total_w, total_h


def main():
    print(f"2D Ising model, L={L}")
    print(f"Точное T_c (Онзагер) = {T_C_EXACT:.6f}")
    print(f"Термализация: {EQUIL} свипов, измерение: {MEASURE} свипов")
    print()

    temps = []
    mags = []
    energies = []
    chis = []
    cvs = []

    snapshot_lattices = []  # (lattice, T) для трёх снимков
    snapshot_temps = [1.5, T_C_EXACT, 3.5]
    snapshot_done = [False, False, False]

    T_list = [1.0 + i * (4.0 - 1.0) / (TEMPS - 1) for i in range(TEMPS)]

    # Добавить T_c если его нет
    T_list.append(T_C_EXACT)
    T_list.sort()

    for idx, T in enumerate(T_list):
        print(f"  T = {T:.3f}  ({idx+1}/{len(T_list)}) ...", end=" ", flush=True)
        m, e, chi, cv, lattice = simulate(T, L, EQUIL, MEASURE)
        temps.append(T)
        mags.append(m)
        energies.append(e)
        chis.append(chi)
        cvs.append(cv)
        print(f"|m| = {m:.4f}, χ = {chi:.2f}")

        # Снимки
        for si, sT in enumerate(snapshot_temps):
            if not snapshot_done[si] and abs(T - sT) < 0.15:
                import copy
                snapshot_lattices.append((copy.deepcopy(lattice), T))
                snapshot_done[si] = True

    # Анализ
    chi_max_idx = chis.index(max(chis))
    T_c_measured = temps[chi_max_idx]

    print()
    print("=" * 50)
    print(f"T_c (Онзагер, точное):     {T_C_EXACT:.6f}")
    print(f"T_c (пик χ, измеренное):   {T_c_measured:.3f}")
    print(f"Отклонение:                 {abs(T_c_measured - T_C_EXACT) / T_C_EXACT * 100:.1f}%")
    print()

    # Онзагеровское m(T) при нескольких температурах
    print("Сравнение с точным решением Онзагера:")
    print(f"  {'T':>6s}  {'|m| (MC)':>10s}  {'|m| (exact)':>12s}  {'Δ':>8s}")
    for T, m in zip(temps, mags):
        if T < T_C_EXACT:
            arg = math.sinh(2.0 / T)
            m_exact = (1 - 1.0 / (arg ** 4)) ** (1.0 / 8) if arg > 1 else 0
        else:
            m_exact = 0.0
        print(f"  {T:6.3f}  {m:10.4f}  {m_exact:12.4f}  {abs(m - m_exact):8.4f}")

    # Изображение
    print()
    print("Генерация изображения...")

    if len(snapshot_lattices) < 3:
        # Если не все снимки — добавить из последних симуляций
        while len(snapshot_lattices) < 3:
            snapshot_lattices.append((make_lattice(L), 2.5))

    img, w, h = compose_image(snapshot_lattices, temps, mags, chis)
    write_png("ising.png", img, w, h)
    print(f"Сохранено: ising.png ({w}×{h})")

    # Точная внутренняя энергия Онзагера
    print()
    K_c = 1.0 / T_C_EXACT
    print(f"Точная внутренняя энергия при T_c: e = -√2 ≈ {-math.sqrt(2):.6f}")

    # Ближайшая измеренная точка к T_c
    tc_idx = min(range(len(temps)), key=lambda i: abs(temps[i] - T_C_EXACT))
    print(f"Измеренная при T={temps[tc_idx]:.3f}: e = {energies[tc_idx]:.6f}")
    print(f"Отклонение: {abs(energies[tc_idx] - (-math.sqrt(2))) / math.sqrt(2) * 100:.1f}%")

if __name__ == "__main__":
    main()
