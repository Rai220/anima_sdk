#!/usr/bin/env python3
"""
XY model on a square lattice — Berezinskii-Kosterlitz-Thouless transition.

Spins are continuous angles θ ∈ [0, 2π). Hamiltonian: H = -J Σ cos(θ_i - θ_j).
Mermin-Wagner theorem: no spontaneous magnetization at any T > 0 in 2D.
Yet there IS a phase transition — topological, not symmetry-breaking.

Below T_BKT ≈ 0.893 (for J=1): vortex-antivortex pairs bound, correlations algebraic (power-law).
Above T_BKT: pairs unbind, free vortices proliferate, correlations exponential.

This is the ONLY topological phase transition. Nobel Prize 2016 (Kosterlitz, Thouless, Haldane).

Output: xy_vortices.png — spin field + vortex map at three temperatures + helicity modulus curve.
"""

import math
import random
import struct
import zlib

# ============================================================
# Parameters
# ============================================================
L = 40          # Lattice size
N_THERM = 3000  # Thermalization sweeps
N_MEAS = 1500   # Measurement sweeps
N_TEMPS = 22    # Number of temperatures
T_MIN = 0.3
T_MAX = 2.0

J = 1.0
T_BKT_THEORY = 0.893  # π/2 * J / 2 ≈ 0.893 (Nelson-Kosterlitz)

random.seed(42)

# ============================================================
# XY Model Monte Carlo (Metropolis)
# ============================================================

def init_lattice(L):
    return [[random.uniform(0, 2*math.pi) for _ in range(L)] for _ in range(L)]

def mc_sweep(lattice, L, beta, delta=1.0):
    """One Metropolis sweep. Returns number of accepted moves."""
    accepted = 0
    for i in range(L):
        for j in range(L):
            theta_old = lattice[i][j]
            theta_new = theta_old + random.uniform(-delta, delta)

            # Neighbors (periodic BC)
            neighbors = [
                lattice[(i+1)%L][j], lattice[(i-1)%L][j],
                lattice[i][(j+1)%L], lattice[i][(j-1)%L]
            ]

            dE = 0.0
            for nb in neighbors:
                dE += -J * (math.cos(theta_new - nb) - math.cos(theta_old - nb))

            if dE <= 0 or random.random() < math.exp(-beta * dE):
                lattice[i][j] = theta_new
                accepted += 1
    return accepted

def measure(lattice, L, beta):
    """Measure magnetization, energy, and helicity modulus."""
    mx, my = 0.0, 0.0
    energy = 0.0

    # For helicity modulus (spin stiffness)
    # Υ = (1/N) [<Σ cos(θ_i - θ_j)>_x - β <(Σ sin(θ_i - θ_j))²>_x]
    cos_sum_x = 0.0
    sin_sum_x = 0.0
    cos_sum_y = 0.0
    sin_sum_y = 0.0

    for i in range(L):
        for j in range(L):
            theta = lattice[i][j]
            mx += math.cos(theta)
            my += math.sin(theta)

            # Right neighbor
            theta_r = lattice[i][(j+1)%L]
            diff_x = theta - theta_r
            cos_sum_x += math.cos(diff_x)
            sin_sum_x += math.sin(diff_x)
            energy += -J * math.cos(diff_x)

            # Down neighbor
            theta_d = lattice[(i+1)%L][j]
            diff_y = theta - theta_d
            cos_sum_y += math.cos(diff_y)
            sin_sum_y += math.sin(diff_y)
            energy += -J * math.cos(diff_y)

    N = L * L
    m = math.sqrt(mx*mx + my*my) / N
    e = energy / N

    return m, e, cos_sum_x, sin_sum_x, cos_sum_y, sin_sum_y

def compute_vorticity(lattice, L):
    """Compute vorticity at each plaquette. +1 = vortex, -1 = antivortex."""
    vortices = [[0]*L for _ in range(L)]
    for i in range(L):
        for j in range(L):
            # Plaquette corners: (i,j), (i,j+1), (i+1,j+1), (i+1,j)
            t1 = lattice[i][j]
            t2 = lattice[i][(j+1)%L]
            t3 = lattice[(i+1)%L][(j+1)%L]
            t4 = lattice[(i+1)%L][j]

            # Sum of angle differences around plaquette, wrapped to [-π, π]
            def wrap(a):
                while a > math.pi: a -= 2*math.pi
                while a < -math.pi: a += 2*math.pi
                return a

            winding = wrap(t2-t1) + wrap(t3-t2) + wrap(t4-t3) + wrap(t1-t4)
            q = round(winding / (2*math.pi))
            vortices[i][j] = q
    return vortices

# ============================================================
# PNG Writer (manual, no dependencies)
# ============================================================

def write_png(filename, width, height, pixels):
    """Write RGB pixels to PNG. pixels[y][x] = (r,g,b)"""
    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return struct.pack('>I', len(data)) + c + crc

    sig = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)

    raw = b''
    for y in range(height):
        raw += b'\x00'  # filter none
        for x in range(width):
            r, g, b = pixels[y][x]
            raw += bytes([max(0,min(255,r)), max(0,min(255,g)), max(0,min(255,b))])

    compressed = zlib.compress(raw, 9)

    with open(filename, 'wb') as f:
        f.write(sig)
        f.write(chunk(b'IHDR', ihdr))
        f.write(chunk(b'IDAT', compressed))
        f.write(chunk(b'IEND', b''))

def angle_to_color(theta):
    """Map angle to HSV color (S=0.8, V=0.95)."""
    theta = theta % (2*math.pi)
    h = theta / (2*math.pi) * 6.0
    s, v = 0.8, 0.95

    i = int(h) % 6
    f = h - int(h)
    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))

    if i == 0: r, g, b = v, t, p
    elif i == 1: r, g, b = q, v, p
    elif i == 2: r, g, b = p, v, t
    elif i == 3: r, g, b = p, q, v
    elif i == 4: r, g, b = t, p, v
    else: r, g, b = v, p, q

    return (int(r*255), int(g*255), int(b*255))

# ============================================================
# Simulation
# ============================================================

print("XY Model — Berezinskii-Kosterlitz-Thouless Transition")
print(f"Lattice: {L}×{L}, Thermalization: {N_THERM}, Measurements: {N_MEAS}")
print(f"T_BKT (theory) ≈ {T_BKT_THEORY}")
print()

temperatures = [T_MIN + i * (T_MAX - T_MIN) / (N_TEMPS - 1) for i in range(N_TEMPS)]

results = []  # (T, <m>, <e>, helicity_modulus)
snapshot_lattices = {}  # Store lattices at three temperatures for visualization

# Temperatures for snapshots
T_low = 0.5    # Well below BKT
T_mid = 0.9    # Near BKT
T_high = 1.5   # Well above BKT

for idx, T in enumerate(temperatures):
    beta = 1.0 / T
    lattice = init_lattice(L)

    # Thermalization with adaptive step
    delta = math.pi
    for sweep in range(N_THERM):
        acc = mc_sweep(lattice, L, beta, delta)
        rate = acc / (L*L)
        if sweep < N_THERM // 2:
            if rate > 0.55: delta *= 1.02
            elif rate < 0.45: delta *= 0.98

    # Measurements
    m_sum, e_sum = 0.0, 0.0
    cos_x_sum, sin2_x_sum = 0.0, 0.0

    for sweep in range(N_MEAS):
        mc_sweep(lattice, L, beta, delta)
        m, e, cos_x, sin_x, cos_y, sin_y = measure(lattice, L, beta)
        m_sum += m
        e_sum += e
        cos_x_sum += cos_x / (L*L)
        sin2_x_sum += (sin_x / (L*L))**2

    m_avg = m_sum / N_MEAS
    e_avg = e_sum / N_MEAS

    # Helicity modulus (spin stiffness)
    # Υ = <cos> - β·L²·<sin²>
    helicity = cos_x_sum / N_MEAS - beta * L * L * sin2_x_sum / N_MEAS

    results.append((T, m_avg, e_avg, helicity))

    # Save snapshots
    best_low = min(temperatures, key=lambda t: abs(t - T_low))
    best_mid = min(temperatures, key=lambda t: abs(t - T_mid))
    best_high = min(temperatures, key=lambda t: abs(t - T_high))

    if abs(T - best_low) < 0.001 and 'low' not in snapshot_lattices:
        snapshot_lattices['low'] = ([row[:] for row in lattice], T)
    if abs(T - best_mid) < 0.001 and 'mid' not in snapshot_lattices:
        snapshot_lattices['mid'] = ([row[:] for row in lattice], T)
    if abs(T - best_high) < 0.001 and 'high' not in snapshot_lattices:
        snapshot_lattices['high'] = ([row[:] for row in lattice], T)

    bar = '█' * int(30 * (idx+1) / N_TEMPS)
    print(f"\r  [{bar:<30}] T={T:.3f}  <m>={m_avg:.4f}  Υ={helicity:.4f}", end='', flush=True)

print("\n")

# ============================================================
# Analysis
# ============================================================

# Find T_BKT from helicity modulus
# Nelson-Kosterlitz: at T_BKT, Υ jumps to (2/π)T_BKT
# Universal jump: Υ(T_BKT⁻) = 2T_BKT/π

print("=== Results ===")
print(f"{'T':>6} {'<m>':>8} {'<e>':>8} {'Υ':>8} {'2T/π':>8}")
print("-" * 44)

t_bkt_measured = None
for i, (T, m, e, hel) in enumerate(results):
    jump_line = 2*T/math.pi
    print(f"{T:6.3f} {m:8.4f} {e:8.4f} {hel:8.4f} {jump_line:8.4f}")

    # BKT: helicity crosses 2T/π line
    if i > 0 and t_bkt_measured is None:
        T_prev, _, _, hel_prev = results[i-1]
        jump_prev = 2*T_prev/math.pi
        jump_curr = 2*T/math.pi
        if hel_prev > jump_prev and hel < jump_curr:
            # Linear interpolation
            # hel(T) = 2T/π at T_BKT
            # hel_prev - jump_prev > 0, hel - jump_curr < 0
            frac = (hel_prev - jump_prev) / ((hel_prev - jump_prev) - (hel - jump_curr))
            t_bkt_measured = T_prev + frac * (T - T_prev)

print()
if t_bkt_measured:
    print(f"T_BKT (measured, Υ = 2T/π crossing): {t_bkt_measured:.3f}")
    print(f"T_BKT (theory, Nelson-Kosterlitz):     {T_BKT_THEORY:.3f}")
    print(f"Deviation: {abs(t_bkt_measured - T_BKT_THEORY)/T_BKT_THEORY*100:.1f}%")
else:
    print("T_BKT crossing not detected (may need finer temperature grid)")

# ============================================================
# Vortex analysis at snapshots
# ============================================================

print("\n=== Vortex Analysis ===")
for key in ['low', 'mid', 'high']:
    if key in snapshot_lattices:
        lat, T = snapshot_lattices[key]
        vort = compute_vorticity(lat, L)
        n_plus = sum(1 for i in range(L) for j in range(L) if vort[i][j] == 1)
        n_minus = sum(1 for i in range(L) for j in range(L) if vort[i][j] == -1)
        print(f"  T={T:.3f}: vortices={n_plus}, antivortices={n_minus}, free={abs(n_plus-n_minus)}")

# ============================================================
# Image generation
# ============================================================

print("\nGenerating xy_vortices.png...")

CELL = 6        # Pixels per spin cell
PAD = 20        # Padding
GRAPH_W = 400   # Graph width
GRAPH_H = 250   # Graph height
LABEL_H = 25    # Label height

lattice_px = L * CELL
n_snapshots = 3

img_w = PAD + n_snapshots * lattice_px + (n_snapshots - 1) * PAD + PAD + GRAPH_W + PAD
img_h = PAD + LABEL_H + lattice_px + PAD + GRAPH_H + LABEL_H + PAD

pixels = [[(30, 30, 35) for _ in range(img_w)] for _ in range(img_h)]

# Draw spin field snapshots with vortices
snapshot_keys = ['low', 'mid', 'high']
labels = []
for si, key in enumerate(snapshot_keys):
    if key not in snapshot_lattices:
        continue
    lat, T = snapshot_lattices[key]
    vort = compute_vorticity(lat, L)

    x0 = PAD + si * (lattice_px + PAD)
    y0 = PAD + LABEL_H

    labels.append((x0, T, key))

    # Draw spin colors
    for i in range(L):
        for j in range(L):
            color = angle_to_color(lat[i][j])
            for dy in range(CELL):
                for dx in range(CELL):
                    px = x0 + j * CELL + dx
                    py = y0 + i * CELL + dy
                    if 0 <= px < img_w and 0 <= py < img_h:
                        pixels[py][px] = color

    # Draw vortices as markers
    for i in range(L):
        for j in range(L):
            if vort[i][j] != 0:
                cx = x0 + j * CELL + CELL // 2
                cy = y0 + i * CELL + CELL // 2
                if vort[i][j] == 1:
                    # Vortex: white dot
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            px, py = cx+dx, cy+dy
                            if 0 <= px < img_w and 0 <= py < img_h:
                                pixels[py][px] = (255, 255, 255)
                elif vort[i][j] == -1:
                    # Antivortex: black dot
                    for dy in range(-1, 2):
                        for dx in range(-1, 2):
                            px, py = cx+dx, cy+dy
                            if 0 <= px < img_w and 0 <= py < img_h:
                                pixels[py][px] = (0, 0, 0)

# Draw helicity modulus graph
gx0 = PAD + n_snapshots * lattice_px + (n_snapshots - 1) * PAD + PAD
gy0 = PAD + LABEL_H
gx1 = gx0 + GRAPH_W
gy1 = gy0 + lattice_px  # Same height as lattice images

# Graph background
for y in range(gy0, min(gy1, img_h)):
    for x in range(gx0, min(gx1, img_w)):
        pixels[y][x] = (15, 15, 20)

# Graph axes
for x in range(gx0, min(gx1, img_w)):
    if gy1-1 < img_h:
        pixels[gy1-1][x] = (100, 100, 100)
for y in range(gy0, min(gy1, img_h)):
    if gx0 < img_w:
        pixels[y][gx0] = (100, 100, 100)

# Plot helicity modulus
gh = gy1 - gy0
gw = gx1 - gx0

# Scale
hel_max = max(r[3] for r in results) * 1.1
if hel_max <= 0: hel_max = 1.0

def graph_point(T, val):
    x = gx0 + int((T - T_MIN) / (T_MAX - T_MIN) * (gw - 1))
    y = gy1 - 1 - int(val / hel_max * (gh - 10))
    return x, y

# Plot 2T/π line (universal jump)
for ti in range(200):
    T = T_MIN + ti * (T_MAX - T_MIN) / 199
    val = 2*T/math.pi
    if val > hel_max: continue
    x, y = graph_point(T, val)
    if 0 <= x < img_w and 0 <= y < img_h:
        pixels[y][x] = (80, 80, 80)

# Plot helicity data
for i in range(len(results)):
    T, _, _, hel = results[i]
    if hel < 0: hel = 0
    x, y = graph_point(T, hel)
    # Draw dot
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx*dx + dy*dy <= 5:
                px, py = x+dx, y+dy
                if 0 <= px < img_w and 0 <= py < img_h:
                    pixels[py][px] = (100, 200, 255)

    # Connect with line to next point
    if i < len(results) - 1:
        T2, _, _, hel2 = results[i+1]
        if hel2 < 0: hel2 = 0
        x2, y2 = graph_point(T2, hel2)
        steps = max(abs(x2-x), abs(y2-y), 1)
        for s in range(steps+1):
            px = x + int((x2-x)*s/steps)
            py = y + int((y2-y)*s/steps)
            if 0 <= px < img_w and 0 <= py < img_h:
                pixels[py][px] = (60, 150, 220)

# Mark T_BKT
if t_bkt_measured:
    bkt_x = gx0 + int((t_bkt_measured - T_MIN) / (T_MAX - T_MIN) * (gw - 1))
    for y in range(gy0, min(gy1, img_h)):
        if 0 <= bkt_x < img_w:
            r, g, b = pixels[y][bkt_x]
            pixels[y][bkt_x] = (min(255, r+60), g//2, g//2)

# Bottom graph: vortex density vs temperature (if we have data)
# Actually, let's compute vortex count at each temperature
# We'll re-run quick simulations for vortex counts
print("Computing vortex density profile...")
vortex_results = []
for T in temperatures:
    beta = 1.0 / T
    lat = init_lattice(L)
    delta_v = math.pi
    for sweep in range(1000):
        acc = mc_sweep(lat, L, beta, delta_v)
        rate = acc / (L*L)
        if sweep < 500:
            if rate > 0.55: delta_v *= 1.02
            elif rate < 0.45: delta_v *= 0.98

    # Average over a few measurements
    nv_total = 0
    n_samples = 3
    for _ in range(n_samples):
        for _ in range(30):
            mc_sweep(lat, L, beta, delta_v)
        vort = compute_vorticity(lat, L)
        nv = sum(1 for i in range(L) for j in range(L) if vort[i][j] != 0)
        nv_total += nv
    vortex_density = nv_total / n_samples / (L*L)
    vortex_results.append((T, vortex_density))

# Draw vortex density graph below
vy0 = gy1 + PAD
vy1 = vy0 + GRAPH_H
vx0 = gx0
vx1 = gx0 + GRAPH_W

# Ensure image is tall enough
while img_h <= vy1 + PAD:
    pixels.append([(30, 30, 35) for _ in range(img_w)])
    img_h += 1

for y in range(vy0, min(vy1, img_h)):
    for x in range(vx0, min(vx1, img_w)):
        pixels[y][x] = (15, 15, 20)

# Axes
for x in range(vx0, min(vx1, img_w)):
    if vy1-1 < img_h:
        pixels[vy1-1][x] = (100, 100, 100)
for y in range(vy0, min(vy1, img_h)):
    if vx0 < img_w:
        pixels[y][vx0] = (100, 100, 100)

# Plot vortex density
vd_max = max(vd for _, vd in vortex_results) * 1.1
if vd_max <= 0: vd_max = 0.1

for i, (T, vd) in enumerate(vortex_results):
    x = vx0 + int((T - T_MIN) / (T_MAX - T_MIN) * (GRAPH_W - 1))
    y = vy1 - 1 - int(vd / vd_max * (GRAPH_H - 10))
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dx*dx + dy*dy <= 5:
                px, py = x+dx, y+dy
                if 0 <= px < img_w and 0 <= py < img_h:
                    pixels[py][px] = (255, 180, 80)

    if i < len(vortex_results) - 1:
        T2, vd2 = vortex_results[i+1]
        x2 = vx0 + int((T2 - T_MIN) / (T_MAX - T_MIN) * (GRAPH_W - 1))
        y2 = vy1 - 1 - int(vd2 / vd_max * (GRAPH_H - 10))
        steps = max(abs(x2-x), abs(y2-y), 1)
        for s in range(steps+1):
            px = x + int((x2-x)*s/steps)
            py = y + int((y2-y)*s/steps)
            if 0 <= px < img_w and 0 <= py < img_h:
                pixels[py][px] = (200, 140, 60)

# Mark T_BKT on vortex graph too
if t_bkt_measured:
    bkt_x = vx0 + int((t_bkt_measured - T_MIN) / (T_MAX - T_MIN) * (GRAPH_W - 1))
    for y in range(vy0, min(vy1, img_h)):
        if 0 <= bkt_x < img_w:
            r, g, b = pixels[y][bkt_x]
            pixels[y][bkt_x] = (min(255, r+60), g//2, g//2)

# Ensure consistent height
final_h = vy1 + PAD
while len(pixels) < final_h:
    pixels.append([(30, 30, 35) for _ in range(img_w)])
pixels = pixels[:final_h]

write_png('xy_vortices.png', img_w, final_h, pixels)
print(f"Saved xy_vortices.png ({img_w}×{final_h})")

# ============================================================
# Summary
# ============================================================

print("\n=== Summary ===")
print(f"XY Model on {L}×{L} lattice")
print(f"T_BKT measured: {t_bkt_measured:.3f}" if t_bkt_measured else "T_BKT: not detected")
print(f"T_BKT theory:   {T_BKT_THEORY:.3f}")
if t_bkt_measured:
    print(f"Deviation:       {abs(t_bkt_measured - T_BKT_THEORY)/T_BKT_THEORY*100:.1f}%")
print()
print("Key difference from Ising (iteration 20):")
print("  Ising: discrete spins ±1, symmetry breaking, <m> ≠ 0 below T_c")
print("  XY:    continuous angles, NO symmetry breaking (<m> → 0 for all T)")
print("         transition is TOPOLOGICAL: vortex-antivortex unbinding")
print("  Ising: second-order transition (divergent susceptibility)")
print("  XY:    infinite-order transition (essential singularity)")
print()
print("Below T_BKT: vortices bound in pairs. Correlations ~ r^{-η(T)} (algebraic)")
print("Above T_BKT: free vortices proliferate. Correlations ~ exp(-r/ξ) (exponential)")
print("The helicity modulus Υ has a UNIVERSAL JUMP at T_BKT: Υ → 2T_BKT/π")
print("This jump is the signature of the BKT transition.")
print()
print("Vortex density profile:")
for T, vd in vortex_results:
    bar = '█' * int(40 * vd / vd_max)
    print(f"  T={T:.3f}: {bar} {vd:.4f}")
