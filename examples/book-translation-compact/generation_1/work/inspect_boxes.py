#!/usr/bin/env python3
"""Overlay text-detection bounding boxes on source images for visual
inspection. Helps tune handler coordinates in translate_image_caption.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC_IMG = ROOT.parent / "source" / "images"
OUT_DIR = ROOT / "work"


def find_text_regions(arr: np.ndarray, min_w: int = 30, min_h: int = 10):
    """Find connected text regions (dark pixel clusters)."""
    h, w = arr.shape
    # Dark pixels (text/lines)
    mask = arr < 200
    # Row-level density
    counts_row = mask.sum(axis=1)
    return mask, counts_row


def inspect(name: str):
    src = SRC_IMG / name
    img = Image.open(src).convert("RGB")
    arr = np.array(img.convert("L"))
    draw = ImageDraw.Draw(img)
    h, w = arr.shape
    print(f"{name}: {w}x{h}")
    # Draw grid lines every 100 px with labels
    for x in range(0, w, 100):
        draw.line([(x, 0), (x, h)], fill=(255, 200, 200), width=1)
        draw.text((x + 2, 5), str(x), fill=(255, 0, 0))
    for y in range(0, h, 100):
        draw.line([(0, y), (w, y)], fill=(200, 255, 200), width=1)
        draw.text((5, y + 2), str(y), fill=(0, 128, 0))
    dst = OUT_DIR / f"inspect_{name}"
    img.save(dst)
    print(f"  wrote {dst}")


def main(names: list[str]) -> None:
    for n in names:
        inspect(n)


if __name__ == "__main__":
    main(sys.argv[1:] or [
        "pentation-generally.png",
        "hexation-generally1.png",
        "grahams-festival.png",
        "insanity.png",
        "grahams-number.png",
        "string-bundle-examples1.png",
    ])
