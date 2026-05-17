"""
Langton's Ant — temporal phase transition.

All previous phase transitions in this generation had a SPATIAL or PARAMETRIC
control variable: density (Game of Life), ratio (SAT), probability (percolation),
r (logistic map), c (Mandelbrot). The question was always "at what VALUE?"

Langton's Ant is different. The rule is fixed. The grid is uniform.
There is no parameter to tune. And yet: after ~10,000 steps of apparent chaos,
a periodic "highway" spontaneously emerges and extends forever.

The control parameter is TIME. The transition is temporal, not parametric.
No one has proven why it happens.

Output: langton.png (1200x800)
"""

import struct
import zlib


def run_ant(grid_size, steps):
    """Run Langton's Ant. Track everything needed for analysis."""
    grid = [[0] * grid_size for _ in range(grid_size)]
    first_visit = [[-1] * grid_size for _ in range(grid_size)]
    visit_count = [[0] * grid_size for _ in range(grid_size)]

    x, y = grid_size // 2, grid_size // 2
    dx, dy = 0, -1  # facing up

    # Record position every 104 steps for highway detection
    PERIOD = 104
    checkpoints = [(x, y)]

    for step in range(steps):
        if not (0 <= x < grid_size and 0 <= y < grid_size):
            break

        if first_visit[y][x] == -1:
            first_visit[y][x] = step
        visit_count[y][x] += 1

        if grid[y][x] == 0:
            dx, dy = -dy, dx
            grid[y][x] = 1
        else:
            dx, dy = dy, -dx
            grid[y][x] = 0

        x += dx
        y += dy

        if (step + 1) % PERIOD == 0:
            checkpoints.append((x, y))

    return grid, first_visit, visit_count, checkpoints, step + 1


def detect_highway(checkpoints):
    """Detect highway by looking for constant displacement per period.

    During the highway, each 104-step period displaces the ant by exactly
    the same (dx, dy). During chaos, displacement varies wildly.
    """
    if len(checkpoints) < 10:
        return None

    # Compute displacement between consecutive checkpoints
    displacements = []
    for i in range(1, len(checkpoints)):
        dx = checkpoints[i][0] - checkpoints[i-1][0]
        dy = checkpoints[i][1] - checkpoints[i-1][1]
        displacements.append((dx, dy))

    # Highway: consecutive displacements are identical
    # Look for a run of >= 10 identical displacements
    PERIOD = 104
    run_start = None
    run_len = 0

    for i in range(1, len(displacements)):
        if displacements[i] == displacements[i-1]:
            if run_len == 0:
                run_start = i - 1
                run_len = 2
            else:
                run_len += 1
        else:
            if run_len >= 10:
                return run_start * PERIOD, displacements[run_start]
            run_len = 0
            run_start = None

    if run_len >= 10:
        return run_start * PERIOD, displacements[run_start]

    return None


def make_png(width, height, pixels):
    """Create PNG from pixel data."""
    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack('>I', len(data)) + c + crc

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))

    raw = bytearray()
    for row in pixels:
        raw.append(0)
        for r, g, b in row:
            raw.extend((r, g, b))

    idat = chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    iend = chunk(b'IEND', b'')

    return header + ihdr + idat + iend


def render(grid, first_visit, visit_count, grid_size, total_steps, highway_start):
    """Render the ant's world with temporal coloring."""
    # Find bounding box
    min_x = min_y = grid_size
    max_x = max_y = 0
    max_vc = 1
    for y in range(grid_size):
        for x in range(grid_size):
            if first_visit[y][x] >= 0:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
                max_vc = max(max_vc, visit_count[y][x])

    margin = 3
    min_x = max(0, min_x - margin)
    max_x = min(grid_size - 1, max_x + margin)
    min_y = max(0, min_y - margin)
    max_y = min(grid_size - 1, max_y + margin)

    view_w = max_x - min_x + 1
    view_h = max_y - min_y + 1

    img_w, img_h = 1200, 800
    scale = min(img_w / view_w, img_h / view_h)

    off_x = (img_w - view_w * scale) / 2
    off_y = (img_h - view_h * scale) / 2

    bg = (10, 10, 15)
    pixels = [[bg] * img_w for _ in range(img_h)]

    import math
    log_max = math.log1p(max_vc)

    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            if first_visit[y][x] < 0:
                continue

            t = first_visit[y][x]
            cell = grid[y][x]
            vc = visit_count[y][x]
            brightness = math.log1p(vc) / log_max

            px_s = int(off_x + (x - min_x) * scale)
            py_s = int(off_y + (y - min_y) * scale)
            px_e = int(off_x + (x - min_x + 1) * scale)
            py_e = int(off_y + (y - min_y + 1) * scale)

            if t < highway_start:
                # Chaotic phase: cool blues/purples
                base_r, base_g, base_b = (50, 30, 140) if cell else (30, 20, 100)
                r = int(base_r * (0.3 + 0.7 * brightness))
                g = int(base_g * (0.3 + 0.7 * brightness))
                b = int(base_b * (0.3 + 0.7 * brightness))
            else:
                # Highway phase: warm ambers/oranges
                base_r, base_g, base_b = (230, 140, 30) if cell else (180, 100, 20)
                r = int(base_r * (0.3 + 0.7 * brightness))
                g = int(base_g * (0.3 + 0.7 * brightness))
                b = int(base_b * (0.3 + 0.7 * brightness))

            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            color = (r, g, b)

            for py in range(max(0, py_s), min(img_h, py_e)):
                for px in range(max(0, px_s), min(img_w, px_e)):
                    pixels[py][px] = color

    return pixels


def main():
    grid_size = 600
    steps = 20000

    print("Langton's Ant: temporal phase transition")
    print(f"Grid: {grid_size}x{grid_size}, Steps: {steps}")
    print()

    grid, first_visit, visit_count, checkpoints, completed = \
        run_ant(grid_size, steps)

    visited = sum(1 for y in range(grid_size) for x in range(grid_size)
                  if first_visit[y][x] >= 0)
    black = sum(grid[y][x] for y in range(grid_size) for x in range(grid_size))

    print(f"Steps completed: {completed}")
    print(f"Unique cells visited: {visited}")
    print(f"Black cells (final): {black}")
    print(f"Black fraction: {black / max(1, visited):.3f}")
    print()

    # Detect highway
    result = detect_highway(checkpoints)

    if result:
        highway_start, disp = result
        print(f"Highway detected at step ~{highway_start}")
        print(f"  Highway displacement per 104 steps: dx={disp[0]}, dy={disp[1]}")
        print(f"  Chaotic phase: 0 — {highway_start}")
        print(f"  Highway phase: {highway_start} — {completed}")
        print(f"  Chaos fraction: {highway_start / completed:.1%}")
    else:
        highway_start = 10000  # known approximate value
        print(f"Highway not auto-detected. Using known value: ~{highway_start}")

    print()

    # Displacement analysis
    print("Displacement per 104-step period (dx, dy):")
    displacements = []
    for i in range(1, min(len(checkpoints), 20)):
        dx = checkpoints[i][0] - checkpoints[i-1][0]
        dy = checkpoints[i][1] - checkpoints[i-1][1]
        displacements.append((dx, dy))
        step = i * 104
        marker = " *" if result and step >= highway_start else ""
        print(f"  period {i:3d} (step {step:5d}): ({dx:+3d}, {dy:+3d}){marker}")
    if len(checkpoints) > 20:
        print(f"  ... ({len(checkpoints)-1} periods total)")
        for i in range(max(20, len(checkpoints) - 3), len(checkpoints)):
            dx = checkpoints[i][0] - checkpoints[i-1][0]
            dy = checkpoints[i][1] - checkpoints[i-1][1]
            step = i * 104
            marker = " *" if result and step >= highway_start else ""
            print(f"  period {i:3d} (step {step:5d}): ({dx:+3d}, {dy:+3d}){marker}")

    print()
    print("  * = highway phase (constant displacement)")
    print()
    print("Key facts:")
    print("  Period: 104 steps (computationally verified)")
    print("  WHY it emerges: UNKNOWN. No proof exists.")
    print("  Cohen-Kung conjecture (1990): highway always emerges.")
    print("  Still open after 36 years.")
    print()
    print("This is the only phase transition in this generation")
    print("where the control parameter is TIME, not a coupling constant.")

    # Render
    print()
    print("Generating langton.png...")
    pixels = render(grid, first_visit, visit_count, grid_size, completed, highway_start)
    png_data = make_png(1200, 800, pixels)

    with open('langton.png', 'wb') as f:
        f.write(png_data)

    size_kb = len(png_data) / 1024
    print(f"Saved langton.png ({size_kb:.0f} KB)")
    print()
    print("Blue/purple = chaotic phase")
    print("Orange/amber = highway phase")
    print("Brightness = visit frequency (log scale)")


if __name__ == '__main__':
    main()
