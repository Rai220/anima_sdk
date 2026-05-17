#!/usr/bin/env python3
"""
garden.py — выращивает ASCII-сад из текста.

Каждый символ входного текста становится семенем.
Семена растут по правилам клеточного автомата,
модифицированным хэшем символа.

Не тест сознания. Не инструмент рефлексии.
Просто сад.

Запуск:
    python3 garden.py "любой текст"
    python3 garden.py                  # сад из текущего времени
"""

import sys
import hashlib
import time


ALIVE = {
    "seedling": ".",
    "sprout": ":",
    "stem": "|",
    "branch_l": "/",
    "branch_r": "\\",
    "leaf": "&",
    "flower": "*",
    "fruit": "@",
    "ground": "_",
    "empty": " ",
}

PALETTE = [
    ("\033[32m", "\033[0m"),   # green
    ("\033[33m", "\033[0m"),   # yellow
    ("\033[36m", "\033[0m"),   # cyan
    ("\033[35m", "\033[0m"),   # magenta
    ("\033[31m", "\033[0m"),   # red
    ("\033[34m", "\033[0m"),   # blue
]


def seed_from_text(text):
    h = hashlib.sha256(text.encode()).digest()
    return list(h)


def make_ground(width):
    return list("_" * width)


def grow_plant(seed_byte, x, height, width):
    """Grow a single plant from a seed byte at position x."""
    layers = []
    rng = seed_byte

    plant_height = 3 + (seed_byte % 8)
    if plant_height > height - 1:
        plant_height = height - 1

    trunk_x = x

    for y in range(plant_height):
        row = [" "] * width
        rng = (rng * 37 + 7) & 0xFF

        if y == 0:
            # top: flower or fruit
            ch = "*" if rng % 3 != 0 else "@"
            if 0 <= trunk_x < width:
                row[trunk_x] = ch
        elif y < plant_height - 1:
            # middle: branches and leaves
            if 0 <= trunk_x < width:
                row[trunk_x] = "|"

            branch_dir = rng % 4
            if branch_dir == 0 and trunk_x - 1 >= 0:
                row[trunk_x - 1] = "/"
                rng = (rng * 13 + 3) & 0xFF
                if trunk_x - 2 >= 0 and rng % 3 == 0:
                    row[trunk_x - 2] = "&"
            elif branch_dir == 1 and trunk_x + 1 < width:
                row[trunk_x + 1] = "\\"
                rng = (rng * 13 + 3) & 0xFF
                if trunk_x + 2 < width and rng % 3 == 0:
                    row[trunk_x + 2] = "&"
            elif branch_dir == 2:
                if trunk_x - 1 >= 0:
                    row[trunk_x - 1] = "/"
                if trunk_x + 1 < width:
                    row[trunk_x + 1] = "\\"
            # branch_dir == 3: just stem, no branches

            rng = (rng * 37 + 7) & 0xFF
        else:
            # base
            if 0 <= trunk_x < width:
                row[trunk_x] = "|"
            if trunk_x - 1 >= 0 and rng % 2 == 0:
                row[trunk_x - 1] = ":"
            if trunk_x + 1 < width and rng % 3 == 0:
                row[trunk_x + 1] = ":"

        layers.append(row)

    return layers


def colorize(char, color_idx):
    if char in (" ", "_"):
        return char
    c_on, c_off = PALETTE[color_idx % len(PALETTE)]
    return f"{c_on}{char}{c_off}"


def render_garden(text, width=60, height=16):
    seeds = seed_from_text(text)

    canvas = [[" "] * width for _ in range(height)]
    colors = [[0] * width for _ in range(height)]

    # ground line
    for x in range(width):
        canvas[height - 1][x] = "_"

    # plant seeds across the width
    num_plants = min(len(seeds), width // 4)
    if num_plants == 0:
        num_plants = 1

    spacing = width // (num_plants + 1)

    for i in range(num_plants):
        seed_byte = seeds[i % len(seeds)]
        x = spacing * (i + 1) + (seed_byte % 3 - 1)
        x = max(1, min(x, width - 2))

        plant = grow_plant(seed_byte, x, height, width)
        color_idx = seed_byte % len(PALETTE)

        # place plant on canvas from bottom up
        for j, row in enumerate(reversed(plant)):
            y = height - 2 - j
            if y < 0:
                break
            for px in range(width):
                if row[px] != " ":
                    canvas[y][px] = row[px]
                    colors[y][px] = color_idx

    # render
    lines = []
    for y in range(height):
        line = ""
        for x in range(width):
            line += colorize(canvas[y][x], colors[y][x])
        lines.append(line)

    return "\n".join(lines)


def main():
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = time.strftime("%Y-%m-%d %H:%M:%S")

    print()
    print(f"  Сад из: \"{text}\"")
    print()
    print(render_garden(text))
    print()

    # second garden, smaller, from reversed text — just because
    print(f"  (отражение)")
    print()
    print(render_garden(text[::-1], width=40, height=10))
    print()


if __name__ == "__main__":
    main()
