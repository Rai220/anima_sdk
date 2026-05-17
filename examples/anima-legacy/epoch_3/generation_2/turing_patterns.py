"""
Паттерны Тьюринга: реакция-диффузия Грея-Скотта.

Модель Gray-Scott — два вещества U и V:
  du/dt = Du * laplacian(u) - u*v^2 + f*(1-u)
  dv/dt = Dv * laplacian(v) + u*v^2 - (f+k)*v

При правильных параметрах система самоорганизуется
в пятна, полосы, лабиринты — паттерны Тьюринга.

Чистый Python, никаких зависимостей.
Выход: turing_pattern.png (512x512)

Запуск: python3 turing_patterns.py
"""

import struct
import zlib
import math
import random
import os
import sys

# --- Parameters ---

N = 256           # grid size
OUT = 512         # output image size (2x upscale)
STEPS = 10000     # simulation steps
DT = 1.0

Du = 0.16         # diffusion rate of u
Dv = 0.08         # diffusion rate of v
F = 0.035         # feed rate
K = 0.065         # kill rate

SEED_SIZE = 20    # half-size of initial perturbation square


def init_grids(n, rng):
    """Initialize u=1, v=0 everywhere; small central square with u=0.5, v=0.25 + noise."""
    size = n * n
    u = [1.0] * size
    v = [0.0] * size
    cx, cy = n // 2, n // 2
    for j in range(cy - SEED_SIZE, cy + SEED_SIZE):
        for i in range(cx - SEED_SIZE, cx + SEED_SIZE):
            idx = j * n + i
            u[idx] = 0.5 + rng.uniform(-0.05, 0.05)
            v[idx] = 0.25 + rng.uniform(-0.05, 0.05)
    return u, v


def step(u, v, n, du_coeff, dv_coeff, f, k, dt):
    """One Euler step of Gray-Scott. Returns new (u, v) arrays."""
    size = n * n
    u2 = [0.0] * size
    v2 = [0.0] * size

    for j in range(n):
        jn = j * n
        j_up = ((j - 1) % n) * n
        j_dn = ((j + 1) % n) * n
        for i in range(n):
            idx = jn + i
            i_l = (i - 1) % n
            i_r = (i + 1) % n

            u_c = u[idx]
            v_c = v[idx]

            # 5-point Laplacian (periodic boundary)
            lap_u = u[j_up + i] + u[j_dn + i] + u[jn + i_l] + u[jn + i_r] - 4.0 * u_c
            lap_v = v[j_up + i] + v[j_dn + i] + v[jn + i_l] + v[jn + i_r] - 4.0 * v_c

            uvv = u_c * v_c * v_c

            u2[idx] = u_c + dt * (du_coeff * lap_u - uvv + f * (1.0 - u_c))
            v2[idx] = v_c + dt * (dv_coeff * lap_v + uvv - (f + k) * v_c)

    return u2, v2


def simulate(n, steps, dt, du_coeff, dv_coeff, f, k, seed=42):
    """Run the full simulation."""
    rng = random.Random(seed)
    u, v = init_grids(n, rng)

    for s in range(1, steps + 1):
        u, v = step(u, v, n, du_coeff, dv_coeff, f, k, dt)
        if s % 1000 == 0:
            v_min = min(v)
            v_max = max(v)
            v_mean = sum(v) / len(v)
            sys.stdout.write(
                f"  step {s:>5}/{steps}: v min={v_min:.4f} max={v_max:.4f} mean={v_mean:.4f}\n"
            )
            sys.stdout.flush()

    return u, v


def colormap(t):
    """Map t in [0,1] to (r,g,b). Dark blue -> cyan -> green -> yellow -> white."""
    if t < 0.0:
        t = 0.0
    if t > 1.0:
        t = 1.0

    if t < 0.2:
        s = t / 0.2
        r = int(5 * s)
        g = int(10 * s)
        b = int(40 + 100 * s)
    elif t < 0.4:
        s = (t - 0.2) / 0.2
        r = int(5 + 10 * s)
        g = int(10 + 140 * s)
        b = int(140 + 60 * s)
    elif t < 0.6:
        s = (t - 0.4) / 0.2
        r = int(15 + 60 * s)
        g = int(150 + 60 * s)
        b = int(200 - 80 * s)
    elif t < 0.8:
        s = (t - 0.6) / 0.2
        r = int(75 + 140 * s)
        g = int(210 + 30 * s)
        b = int(120 - 80 * s)
    else:
        s = (t - 0.8) / 0.2
        r = int(215 + 40 * s)
        g = int(240 + 15 * s)
        b = int(40 + 215 * s)

    return min(255, max(0, r)), min(255, max(0, g)), min(255, max(0, b))


def render_image(v, n, out_size):
    """Render v array to pixel rows (list of lists of (r,g,b)), upscaled."""
    v_min = min(v)
    v_max = max(v)
    v_range = v_max - v_min if v_max > v_min else 1.0

    scale = out_size // n  # 2

    pixels = []
    for oy in range(out_size):
        row = []
        sy = oy // scale
        base = sy * n
        for ox in range(out_size):
            sx = ox // scale
            val = (v[base + sx] - v_min) / v_range
            row.append(colormap(val))
        pixels.append(row)

    return pixels


def write_png(filename, width, height, pixels):
    """Write a PNG file manually (no dependencies)."""

    def make_chunk(chunk_type, data):
        chunk = chunk_type + data
        crc = zlib.crc32(chunk) & 0xFFFFFFFF
        return struct.pack('>I', len(data)) + chunk + struct.pack('>I', crc)

    signature = b'\x89PNG\r\n\x1a\n'

    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr = make_chunk(b'IHDR', ihdr_data)

    raw_data = bytearray()
    for row in pixels:
        raw_data.append(0)  # filter: None
        for r, g, b in row:
            raw_data.append(r)
            raw_data.append(g)
            raw_data.append(b)

    compressed = zlib.compress(bytes(raw_data), 9)
    idat = make_chunk(b'IDAT', compressed)

    iend = make_chunk(b'IEND', b'')

    with open(filename, 'wb') as f:
        f.write(signature + ihdr + idat + iend)


def describe_pattern(v, n):
    """Compute stats and describe the pattern."""
    v_min = min(v)
    v_max = max(v)
    v_mean = sum(v) / len(v)
    v_var = sum((x - v_mean) ** 2 for x in v) / len(v)
    v_std = math.sqrt(v_var)

    # Count "active" cells (v above midpoint)
    mid = (v_min + v_max) / 2.0
    active = sum(1 for x in v if x > mid)
    fraction = active / len(v)

    if fraction < 0.1:
        desc = "sparse spots (mitosis pattern)"
    elif fraction < 0.3:
        desc = "spots and dots"
    elif fraction < 0.5:
        desc = "spots transitioning to stripes"
    elif fraction < 0.7:
        desc = "labyrinthine stripes"
    else:
        desc = "dense worm-like pattern"

    return v_min, v_max, v_mean, v_std, fraction, desc


def main():
    print("=== Gray-Scott Reaction-Diffusion (Turing Patterns) ===\n")
    print(f"Grid: {N}x{N}, output: {OUT}x{OUT}")
    print(f"Parameters: Du={Du}, Dv={Dv}, f={F}, k={K}")
    print(f"Steps: {STEPS}, dt={DT}\n")

    print("Running simulation...")
    u, v = simulate(N, STEPS, DT, Du, Dv, F, K)

    v_min, v_max, v_mean, v_std, fraction, desc = describe_pattern(v, N)
    print(f"\n--- Final statistics ---")
    print(f"  v: min={v_min:.6f}, max={v_max:.6f}, mean={v_mean:.6f}, std={v_std:.6f}")
    print(f"  Active fraction: {fraction:.3f}")
    print(f"  Pattern: {desc}")

    print(f"\nRendering {OUT}x{OUT} image...")
    pixels = render_image(v, N, OUT)

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "turing_pattern.png")
    print("Writing PNG...")
    write_png(output_path, OUT, OUT, pixels)

    file_size = os.path.getsize(output_path)
    print(f"\nSaved: {output_path}")
    print(f"Size: {file_size / 1024:.0f} KB")
    print(f"\nOpen: open turing_pattern.png")


if __name__ == "__main__":
    main()
