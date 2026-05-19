#!/usr/bin/env python3
"""Translate top-caption images: cover the top text band with white and
render Russian text. Optionally also cover an extra region (e.g., a
bottom-right callout).

Each image is described in HANDLERS with parameters tuned by visual
inspection of the source. The script is idempotent: outputs are written
to out/images/<name>.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC_IMG = ROOT.parent / "source" / "images"
OUT_IMG = ROOT / "out" / "images"
OUT_IMG.mkdir(parents=True, exist_ok=True)

FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_ITAL = "/System/Library/Fonts/Supplemental/Arial Italic.ttf"


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def measure(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def detect_dots_start(img: Image.Image, min_gap: int = 15) -> int:
    """Return the y of the first row of the dot grid (or 0 if not found).

    Uses a heuristic: walk down rows until we see >=min_gap mostly empty
    rows after at least one row of text.
    """
    arr = np.array(img.convert("L"))
    h, w = arr.shape
    mask = arr < 200
    counts = mask.sum(axis=1)
    threshold = max(2, w // 60)
    empty = counts <= threshold
    seen_text = False
    gap = 0
    for y in range(h):
        if empty[y]:
            if not seen_text:
                continue
            gap += 1
            if gap >= min_gap:
                return y + 1
        else:
            seen_text = True
            gap = 0
    return 0


def detect_caption_band(img: Image.Image, max_gap_inside_caption: int = 30) -> int:
    """Return the y where the caption ends.

    A caption may have several text lines (with small gaps) plus a
    secondary sub-line (e.g., flush.png's red "1 flush"). We look for the
    first gap of >= max_gap_inside_caption rows after the LAST text row
    we've seen so far.  Falls back to detect_dots_start().
    """
    arr = np.array(img.convert("L"))
    h, w = arr.shape
    mask = arr < 200
    counts = mask.sum(axis=1)
    threshold = max(2, w // 60)
    empty = counts <= threshold
    # We require the caption block to be in the top third of the image.
    limit_y = min(h, max(h // 3, 200))
    seen_text = False
    last_text_y = 0
    gap = 0
    for y in range(limit_y):
        if empty[y]:
            if not seen_text:
                continue
            gap += 1
            if gap >= max_gap_inside_caption:
                return last_text_y + 5
        else:
            seen_text = True
            last_text_y = y
            gap = 0
    if seen_text:
        return min(last_text_y + 5, limit_y)
    return detect_dots_start(img)


def render_centered_text(
    img: Image.Image,
    text_lines: list[tuple[str, str, str]],  # (text, color_hex, font_path)
    box: tuple[int, int, int, int],
    max_font: int = 64,
    min_font: int = 10,
    line_spacing: float = 1.15,
    pad: int = 8,
    fill_color: str | tuple = "white",
    align: str = "center",
) -> None:
    """Cover `box` with fill_color, then center-render multi-line text.
    Auto-shrinks font until everything fits.
    """
    draw = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=fill_color)
    box_w = x1 - x0 - 2 * pad
    box_h = y1 - y0 - 2 * pad

    font_size = max_font
    fonts = None
    sizes = None
    while font_size >= min_font:
        fonts = [load_font(fp, font_size) for _, _, fp in text_lines]
        sizes = [measure(draw, t, f) for (t, _, _), f in zip(text_lines, fonts)]
        max_w = max(w for w, _ in sizes)
        total_h = int(
            sum(h for _, h in sizes)
            + (len(sizes) - 1) * font_size * (line_spacing - 1)
        )
        if max_w <= box_w and total_h <= box_h:
            break
        font_size -= 1
    if fonts is None:
        fonts = [load_font(fp, min_font) for _, _, fp in text_lines]
        sizes = [measure(draw, t, f) for (t, _, _), f in zip(text_lines, fonts)]

    total_h = int(
        sum(h for _, h in sizes)
        + (len(sizes) - 1) * font_size * (line_spacing - 1)
    )
    cy = y0 + pad + (box_h - total_h) // 2
    for (text, color, _), (w, h), font in zip(text_lines, sizes, fonts):
        if align == "center":
            cx = x0 + pad + (box_w - w) // 2
        elif align == "left":
            cx = x0 + pad
        else:
            cx = x0 + pad + (box_w - w)
        draw.text((cx, cy), text, font=font, fill=color)
        cy += int(h + font_size * (line_spacing - 1))


# Convenience: build (text, color, default_font) tuples.
def L(text: str, color: str = "#1c1c1c", font: str = FONT_REG):
    return (text, color, font)


def process(name: str, handler) -> None:
    src = SRC_IMG / name
    dst = OUT_IMG / name
    img = Image.open(src).convert("RGBA")
    handler(img)
    img.convert("RGB").save(dst, optimize=True)
    print(f"wrote {dst}")


# --- handlers (operate on RGBA image, mutate in place) ---

def caption_top(img: Image.Image, lines, max_font: int = 999, pad: int = 8,
                 extra_top: int = 0, extra_bottom: int = -2,
                 force_end: int | None = None) -> None:
    """Cover the top caption (auto-detect) and render `lines` centered.

    By default we use detect_dots_start (gap >= 15 rows), which is the
    most reliable lower bound for "where dot grid begins".  Pass
    `force_end` to override (e.g., when there's a secondary text band
    after the main caption, like the red "1 flush" line).
    """
    if force_end is not None:
        end = force_end
    else:
        end = detect_dots_start(img) or 80
    end = max(end - extra_bottom, 30)
    render_centered_text(
        img, lines, box=(0, extra_top, img.width, end),
        max_font=max_font, pad=pad,
    )


def craigslist(img):
    caption_top(img, [L("В Craigslist работает"),
                       L("около 40 человек")], max_font=22)


def blind(img):
    caption_top(img, [L("1 из 179 человек —"),
                       L("слепой")], max_font=26)


def apple(img):
    caption_top(img, [L("444 розничных магазина"),
                       L("Apple в мире")], max_font=26)


def flush(img):
    # The original has black "508 five-card draws" plus red "1 flush"
    # below it; force the cover to extend past both lines.
    caption_top(img, [L("508 раздач по 5 карт —"),
                       L("1 флеш", "#d2222d", FONT_BOLD)],
                max_font=34, force_end=140)


def millionaires(img):
    caption_top(img, [L("1 из 583 человек —"),
                       L("долларовый миллионер")], max_font=26)


def princesses(img):
    caption_top(img, [L("48 настоящих принцесс")], max_font=34)


def neutron_star(img):
    # Caption is split with a 28-row gap between lines, so detect_dots_start
    # would cut it after the first line.  Force the end past both lines.
    caption_top(img, [L("Нейтронная звезда делает"),
                       L("1 122 оборота в секунду")],
                max_font=40, force_end=140)


def minutes_in_a_day(img):
    caption_top(img, [L("1 440 минут в сутках")], max_font=40)


def perfect_sat(img):
    caption_top(img, [L("Только 1 из 1 489 человек"),
                       L("набирает 1600 на SAT")], max_font=40)


def exoplanets(img):
    caption_top(img, [L("Астрономы обнаружили"),
                       L("1 849 экзопланет")], max_font=40)


def stars(img):
    caption_top(img, [L("Ясной ночью видно"),
                       L("около 2 500 звёзд")], max_font=40)


def seconds_in_an_hour(img):
    caption_top(img, [L("3 600 секунд в часе")], max_font=46)


def religions(img):
    caption_top(img, [L("4 200 религий в мире")], max_font=50)


def languages(img):
    # The original has a two-line caption: large black title (y:44-98) +
    # smaller grey subtitle (y:119-173).  Dot grid starts at y=212.
    caption_top(img, [
        L("6 500 живых языков в мире"),
        L("(из них 2 000 — менее 1 000 носителей)", "#9a9a9a"),
    ], max_font=44, force_end=200)


def sand(img):
    caption_top(img, [L("В кубическом сантиметре умещается"),
                       L("8 000 средних песчинок")], max_font=44)


def one_in_20(img):
    # Top caption.
    caption_top(img, [L("Случайная выборка из"),
                       L("20 американских мужчин")], max_font=38)
    # Replace the red callout in the bottom-right (≈x:330..674, y:240..380).
    render_centered_text(
        img,
        [L("Только один из них", "#d2222d", FONT_REG),
         L("выше 188 см (6'2\")", "#d2222d", FONT_REG)],
        box=(330, 260, 674, 380),
        max_font=30,
    )


def gay_lesbian_bisexual(img):
    # Two captions side-by-side.
    render_centered_text(
        img,
        [L("1 из 43 американцев"),
         L("открыто относит себя"),
         L("к геям, лесбиянкам"),
         L("или бисексуалам")],
        box=(0, 0, 220, 100),
        max_font=16,
        line_spacing=1.1,
    )
    render_centered_text(
        img,
        [L("Но в анонимном"),
         L("опросе доля растёт"),
         L("до 8 из 43")],
        box=(225, 0, 441, 100),
        max_font=16,
        line_spacing=1.1,
    )


# --- Large "caption + dots" images: just overlay the top text band. ---

def fenway(img):
    # 2000x2200. Source caption "This is how many people sell out Fenway Park (37,493)"
    # occupies roughly y=30..120 across the full width.
    caption_top(img, [L("Столько людей помещается на распроданном Fenway Park (37 493)")],
                max_font=64, force_end=140)


def manhattan_buildings(img):
    # 2000x2600. Source caption "47,000 buildings in Manhattan" y~40..150.
    caption_top(img, [L("47 000 зданий на Манхэттене")],
                max_font=80, force_end=180)


def seconds_in_a_day(img):
    # 1999x4527. Source caption "86,400 seconds in a day" y~25..100.
    caption_top(img, [L("86 400 секунд в сутках")],
                max_font=66, force_end=130)


def abortions(img):
    # 2000x6200. Source caption "120,000 worldwide abortions a day" y~30..110.
    caption_top(img, [L("120 000 абортов в мире за сутки")],
                max_font=64, force_end=140)


# --- Math diagrams: overlay targeted boxes for each label. ---

def tetration_generally(img):
    # 1019x609.
    # Green title "Tetration" (y=42..100, bold green): cover whole row.
    render_centered_text(
        img, [L("Тетрация", "#00a000", FONT_BOLD)],
        box=(0, 30, img.width, 110), max_font=64,
    )
    # Green subtitle "(Operation Level 4)" (y=131..163).
    render_centered_text(
        img, [L("(операция 4-го уровня)", "#00a000", FONT_REG)],
        box=(0, 120, img.width, 175), max_font=34,
    )
    # Blue text "a ↑↑ b means a power tower of a's, b high" (y=234..279).
    render_centered_text(
        img,
        [L("a ↑↑ b = ", "#1f5fff", FONT_REG),
         L("башня степеней", "#1f5fff", FONT_BOLD),
         L(" из a высотой b", "#1f5fff", FONT_REG)],
        box=(0, 220, img.width, 285), max_font=34,
        # We need a single-line render; use inline composition instead.
    ) if False else _draw_inline_line(
        img, y=232, width=img.width,
        parts=[("a ↑↑ b означает ", "#1f5fff", FONT_REG, 34),
               ("башню степеней", "#1f5fff", FONT_BOLD, 34),
               (" из a высотой b", "#1f5fff", FONT_REG, 34)],
        bg_box=(0, 220, img.width, 286),
    )
    # Two "b copies of a" labels.
    render_centered_text(
        img, [L("b копий a", "#1c1c1c", FONT_REG)],
        box=(330, 538, 600, 580), max_font=32,
    )
    render_centered_text(
        img, [L("b копий a", "#1c1c1c", FONT_REG)],
        box=(700, 538, 970, 580), max_font=32,
    )


def _draw_inline_line(img, y, width, parts, bg_box):
    """Draw a single line composed of (text, color, font_path, size) parts,
    horizontally centered within `width`. First cover `bg_box` with white."""
    draw = ImageDraw.Draw(img)
    draw.rectangle(bg_box, fill="white")
    fonts = [load_font(fp, size) for _, _, fp, size in parts]
    widths = [measure(draw, t, f)[0] for (t, _, _, _), f in zip(parts, fonts)]
    total_w = sum(widths)
    x = (width - total_w) // 2
    for (t, color, _, _), f, w in zip(parts, fonts, widths):
        draw.text((x, y), t, font=f, fill=color)
        x += w


def string_bundle_examples(img):
    # 1344x1086. Three captions in distinct rows:
    # y=32..65: "Multiplication bundles together a string of addition:"
    # y=374..416: "Exponentiation bundles together a string of multiplication:"
    # y=714..747: "Tetration bundles together a string of exponentiation:"
    _draw_inline_line(
        img, y=30, width=img.width, bg_box=(0, 10, img.width, 90),
        parts=[("Умножение", "#00a000", FONT_BOLD, 40),
               (" сворачивает цепочку ", "#5a5a5a", FONT_REG, 40),
               ("сложений", "#00a000", FONT_BOLD, 40),
               (":", "#5a5a5a", FONT_REG, 40)],
    )
    _draw_inline_line(
        img, y=372, width=img.width, bg_box=(0, 352, img.width, 430),
        parts=[("Возведение в степень", "#00a000", FONT_BOLD, 40),
               (" сворачивает цепочку ", "#5a5a5a", FONT_REG, 40),
               ("умножений", "#00a000", FONT_BOLD, 40),
               (":", "#5a5a5a", FONT_REG, 40)],
    )
    _draw_inline_line(
        img, y=712, width=img.width, bg_box=(0, 692, img.width, 770),
        parts=[("Тетрация", "#00a000", FONT_BOLD, 40),
               (" сворачивает цепочку ", "#5a5a5a", FONT_REG, 40),
               ("возведений в степень", "#00a000", FONT_BOLD, 40),
               (":", "#5a5a5a", FONT_REG, 40)],
    )
    # "b copies of a" labels under each formula. Cover originals generously.
    # Row 1 (under axb): y~200..260, x=540..790.
    render_centered_text(img, [L("b копий a", "#1c1c1c", FONT_REG)],
                         box=(530, 195, 810, 270), max_font=34)
    # Row 2 (under a^b multiplication): y~555..625, x=645..880.
    render_centered_text(img, [L("b копий a", "#1c1c1c", FONT_REG)],
                         box=(625, 545, 900, 635), max_font=34)
    # Row 3 left (under a↑(...) tetration): y~980..1040, x=540..790.
    render_centered_text(img, [L("b копий a", "#1c1c1c", FONT_REG)],
                         box=(530, 970, 810, 1050), max_font=34)
    # Row 3 right (under power tower in tetration): y~980..1040, x=920..1170.
    render_centered_text(img, [L("b копий a", "#1c1c1c", FONT_REG)],
                         box=(910, 970, 1180, 1050), max_font=34)


def pentation_generally(img):
    # 1500x1456.
    render_centered_text(
        img, [L("Пентация", "#00a000", FONT_BOLD)],
        box=(0, 15, img.width, 110), max_font=64,
    )
    render_centered_text(
        img, [L("(операция 5-го уровня)", "#00a000", FONT_REG)],
        box=(0, 110, img.width, 175), max_font=34,
    )
    # Blue 2 lines (y=200..287).
    _draw_inline_line(
        img, y=200, width=img.width, bg_box=(0, 180, img.width, 250),
        parts=[("a ↑↑↑ b означает ", "#1f5fff", FONT_REG, 40),
               ("башенный пир из степеней", "#1f5fff", FONT_BOLD, 40)],
    )
    _draw_inline_line(
        img, y=256, width=img.width, bg_box=(0, 250, img.width, 310),
        parts=[("из b башен по a", "#1f5fff", FONT_REG, 40)],
    )
    # Orange annotation block top-right (y=395..580). Cover box widely.
    render_centered_text(
        img,
        [L("Каждая скобка — это ", "#e8731a", FONT_REG),
         L("башня степеней;", "#e8731a", FONT_BOLD),
         L("если её полностью «развернуть»,", "#e8731a", FONT_REG),
         L("она становится «значением b»", "#e8731a", FONT_REG),
         L("в следующей внешней башне,", "#e8731a", FONT_REG),
         L("то есть её ", "#e8731a", FONT_REG),
         L("высотой.", "#e8731a", FONT_ITAL)],
        box=(850, 380, img.width - 10, 600),
        max_font=26, line_spacing=1.15,
    )
    # "b copies of a" middle (y=605..650). Center under formula.
    render_centered_text(
        img, [L("b копий a", "#1c1c1c", FONT_REG)],
        box=(420, 600, 900, 670), max_font=32,
    )
    # "b-1 towers" right of tower (y=1044..1094, x=870..1150).
    render_centered_text(
        img, [L("b−1 башен", "#1c1c1c", FONT_REG)],
        box=(855, 1020, 1175, 1115), max_font=44,
    )
    # Orange paragraph bottom-left (y=1190..1430, x=60..540). Cover widely.
    render_centered_text(
        img,
        [L("Башенный пир из степеней", "#e8731a", FONT_BOLD),
         L("Нижняя башня имеет высоту a.", "#e8731a", FONT_REG),
         L("Когда её «развернут», полученное", "#e8731a", FONT_REG),
         L("число становится высотой следующей", "#e8731a", FONT_REG),
         L("башни; её «разворачивают» — и оно", "#e8731a", FONT_REG),
         L("идёт высотой в следующую, и так", "#e8731a", FONT_REG),
         L("далее.", "#e8731a", FONT_REG)],
        box=(20, 1180, 620, 1450),
        max_font=26, line_spacing=1.18,
    )


def hexation_generally(img):
    # 1500x1804.
    render_centered_text(
        img, [L("Гексация", "#00a000", FONT_BOLD)],
        box=(0, 15, img.width, 110), max_font=64,
    )
    render_centered_text(
        img, [L("(операция 6-го уровня)", "#00a000", FONT_REG)],
        box=(0, 110, img.width, 175), max_font=34,
    )
    # Blue 3 lines (y=205..345).
    _draw_inline_line(
        img, y=210, width=img.width, bg_box=(0, 195, img.width, 260),
        parts=[("a ↑↑↑↑ b означает", "#1f5fff", FONT_REG, 40)],
    )
    _draw_inline_line(
        img, y=266, width=img.width, bg_box=(0, 255, img.width, 320),
        parts=[("башенный психо-фестиваль из степеней", "#1f5fff", FONT_BOLD, 40)],
    )
    _draw_inline_line(
        img, y=320, width=img.width, bg_box=(0, 315, img.width, 375),
        parts=[("c b башнями по a", "#1f5fff", FONT_REG, 40)],
    )
    # Orange annotation top-right (y=420..680, x=870..1480).
    render_centered_text(
        img,
        [L("Каждая скобка — это ", "#e8731a", FONT_REG),
         L("башенный пир", "#e8731a", FONT_BOLD),
         L("из степеней; если развернуть её", "#e8731a", FONT_REG),
         L("полностью, она становится «b» в", "#e8731a", FONT_REG),
         L("башенном пире следующей внешней", "#e8731a", FONT_REG),
         L("скобки — то есть ", "#e8731a", FONT_REG),
         L("числом башен в нём.", "#e8731a", FONT_ITAL)],
        box=(860, 420, img.width - 10, 690),
        max_font=26, line_spacing=1.15,
    )
    # "b copies of a" middle (y=690..725, x=530..830).
    render_centered_text(
        img, [L("b копий a", "#1c1c1c", FONT_REG)],
        box=(520, 685, 850, 745), max_font=32,
    )
    # Pink callout "A power tower feeding frenzy" (y=855..940, x=900..1110).
    render_centered_text(
        img,
        [L("Башенный пир", "#e6168d", FONT_BOLD),
         L("из степеней", "#e6168d", FONT_BOLD)],
        box=(820, 845, 1150, 960),
        max_font=30, line_spacing=1.15,
    )
    # Orange paragraph bottom-left (y=1370..1740, x=60..560).
    render_centered_text(
        img,
        [L("Башенный психо-фестиваль", "#e8731a", FONT_BOLD),
         L("Первый пир (крайний справа)", "#e8731a", FONT_REG),
         L("начинается с a башен, которые", "#e8731a", FONT_REG),
         L("«питают» друг друга, и в итоге", "#e8731a", FONT_REG),
         L("выходит огромное число. Это число", "#e8731a", FONT_REG),
         L("становится количеством башен в", "#e8731a", FONT_REG),
         L("следующем пире — и так далее.", "#e8731a", FONT_REG),
         L("Группа таких пиров и есть", "#e8731a", FONT_REG),
         L("психо-фестиваль; она получается,", "#e8731a", FONT_REG),
         L("если взять четыре стрелки —", "#e8731a", FONT_REG),
         L("гексацию.", "#e8731a", FONT_REG)],
        box=(20, 1320, 600, 1740),
        max_font=24, line_spacing=1.18,
    )
    # "b-1 feeding frenzies" bottom-right brace (y=1715..1795, x=610..1290).
    render_centered_text(
        img, [L("b−1 башенных пиров", "#1c1c1c", FONT_REG)],
        box=(605, 1705, img.width - 10, 1800), max_font=44,
    )


def sun_tower(img):
    # 1216x1138. Big orange "SUN" top-right + green "Already bigger than a googolplex"
    # at the right middle. The SUN label sits on the yellow sun, so fill
    # with the sun's yellow rather than white.
    render_centered_text(
        img, [L("СОЛНЦЕ", "#ff5d00", FONT_BOLD)],
        box=(880, 50, 1200, 200), max_font=80,
        fill_color=(248, 204, 19),
    )
    # Green callout (y around 471..545, right side). White background is OK
    # here (it's on the white area of the image).
    render_centered_text(
        img,
        [L("Уже больше,", "#00a000", FONT_BOLD),
         L("чем гуголплекс", "#00a000", FONT_BOLD)],
        box=(805, 430, 1110, 560),
        max_font=34, line_spacing=1.15,
    )


def insanity(img):
    # 1503x635. Two red "INSANITY" texts plus "number of towers".
    # First INSANITY inline within "= 3 ↑↑↑ INSANITY =" at y=85..150, x=620..870.
    render_centered_text(
        img, [L("БЕЗУМИЕ", "#d2222d", FONT_BOLD)],
        box=(600, 80, 880, 160),
        max_font=44,
    )
    # Right side: red INSANITY + 'number of towers' y=265..410, x=1175..1435.
    render_centered_text(
        img,
        [L("БЕЗУМНОЕ", "#d2222d", FONT_BOLD),
         L("число", "#d2222d", FONT_REG),
         L("башен", "#d2222d", FONT_REG)],
        box=(1170, 255, 1450, 415),
        max_font=36, line_spacing=1.15,
    )


def grahams_festival(img):
    # 1700x1139.
    # Green bold title "The g1 power tower feeding frenzy psycho festival" spans
    # 2 lines y=20..180, x=350..1500. Cover the whole top band.
    # First wipe, then render Russian title with manual subscript for "g₁"
    # (Arial Bold lacks Unicode subscript glyphs).
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 10, img.width, 200), fill="white")
    green = "#00a000"
    # Two-line title: "Башенный психо-фестиваль g₁" + "(пир из башен степеней)"
    f_main = load_font(FONT_BOLD, 54)
    f_sub = load_font(FONT_BOLD, 32)
    line1_left = "Башенный психо-фестиваль "
    line1_g = "g"
    line1_sub = "1"
    line2 = "(пир из башен степеней)"
    w_left = measure(draw, line1_left, f_main)[0]
    w_g = measure(draw, line1_g, f_main)[0]
    w_sub = measure(draw, line1_sub, f_sub)[0]
    total_w1 = w_left + w_g + 2 + w_sub
    x1 = (img.width - total_w1) // 2
    y1 = 25
    draw.text((x1, y1), line1_left, font=f_main, fill=green)
    draw.text((x1 + w_left, y1), line1_g, font=f_main, fill=green)
    draw.text((x1 + w_left + w_g + 2, y1 + 22), line1_sub, font=f_sub, fill=green)
    w2 = measure(draw, line2, f_main)[0]
    x2 = (img.width - w2) // 2
    y2 = y1 + 75
    draw.text((x2, y2), line2, font=f_main, fill=green)
    # Orange annotation top-center "(b-1) = 2 power tower feeding frenzies in this psycho festival"
    # y=245..335, x=870..1510 (the right edge of "feeding"/"festival" extends past 1400).
    render_centered_text(
        img,
        [L("(b − 1) = 2 башенных пира", "#e8731a", FONT_BOLD),
         L("в этом психо-фестивале", "#e8731a", FONT_BOLD)],
        box=(550, 235, 1520, 345),
        max_font=30, line_spacing=1.15,
    )
    # Green callout right side "The Sun Tower" y=475..515, x=1300..1500.
    render_centered_text(
        img,
        [L("Солнечная башня", "#00a000", FONT_BOLD)],
        box=(1280, 460, img.width - 10, 520),
        max_font=30,
    )
    # Green annotation right "This total becomes the number of towers in the feeding frenzy to its left"
    # y=520..630, x=1290..1640.
    render_centered_text(
        img,
        [L("Это число становится", "#00a000", FONT_REG),
         L("количеством башен в пире", "#00a000", FONT_REG),
         L("слева от него", "#00a000", FONT_REG)],
        box=(1280, 515, img.width - 10, 640),
        max_font=24, line_spacing=1.15,
    )
    # Orange annotation left "These three dots represent..." y=815..960, x=330..870.
    render_centered_text(
        img,
        [L("Эти три точки скрывают", "#e8731a", FONT_REG),
         L("безумное количество башен —", "#e8731a", FONT_ITAL),
         L("больше, чем число", "#e8731a", FONT_REG),
         L("планковских объёмов,", "#e8731a", FONT_REG),
         L("которые могли бы поместиться", "#e8731a", FONT_REG),
         L("в наблюдаемой Вселенной.", "#e8731a", FONT_REG)],
        box=(320, 800, 880, 975),
        max_font=26, line_spacing=1.18,
    )
    # Blue annotation right "This total becomes the height of the tower above it"
    # y=825..955, x=1320..1700.
    render_centered_text(
        img,
        [L("Это число становится", "#1f5fff", FONT_REG),
         L("высотой башни,", "#1f5fff", FONT_REG),
         L("стоящей над ним", "#1f5fff", FONT_REG)],
        box=(1310, 815, img.width - 10, 970),
        max_font=24, line_spacing=1.15,
    )


def grahams_number(img):
    # 1863x959.
    # Green bold "Graham's Number" y=30..130, x=670..1450.
    render_centered_text(
        img,
        [L("Число Грэма", "#00a000", FONT_BOLD)],
        box=(0, 15, img.width, 145),
        max_font=80,
    )
    # Blue "g64 = Graham's Number" left, y=230..300, x=0..680.
    # Subscript ₆₄ does not render in Arial Bold; draw "g", then "64" with
    # a smaller font shifted down (subscript), then " = Число Грэма".
    draw = ImageDraw.Draw(img)
    draw.rectangle((15, 225, 760, 310), fill="white")
    blue = "#1f5fff"
    fg = load_font(FONT_BOLD, 44)
    fsub = load_font(FONT_BOLD, 26)
    x = 30
    y_main = 240
    y_sub = y_main + 22  # shift smaller digits down for subscript look
    draw.text((x, y_main), "g", font=fg, fill=blue)
    gw = measure(draw, "g", fg)[0]
    x += gw + 2
    draw.text((x, y_sub), "64", font=fsub, fill=blue)
    sw = measure(draw, "64", fsub)[0]
    x += sw + 6
    draw.text((x, y_main), " = Число Грэма", font=fg, fill=blue)
    # "64 layers" right side. The actual brace `}` only extends to x≈1541
    # (its widest middle bump). The "6" digit of the original "64 layers"
    # spans x≈1556..1612 (with disjoint outline clusters that visually look
    # like part of the brace, hence the earlier confusion). The whitebox must
    # start AFTER the brace bump (x≥1545) to cover the entire "6". We use
    # x=1547 for a few pixels of safety margin from the brace.
    render_centered_text(
        img,
        [L("64 слоя", "#1c1c1c", FONT_BOLD)],
        box=(1547, 525, img.width - 10, 625),
        max_font=46,
    )


# Tiny dot images we copy unchanged (only mathematical labels / dots, no
# textual content that needs translation).
COPY_AS_IS = [
    "1-dot2-150x111.png",
    "1-dot2.png",
    "10-dots1.png",
    "100-dots1.png",
    "1000-dots1.png",
    "10000-dots.png",
    "1100th1.png",
    "Million-Dots-one-red3.png",
    "Moon.png",
    "million-poster_large.jpg",
    "million-1in10000_large.jpg",
    "million-1in100_large.jpg",
    # g2.png contains only math (g₁, g₂ symbols, arrows, 3's) — no English
    # text to translate.
    "g2.png",
    "100000-dots.png",
]


HANDLERS = {
    "Craigslist.png": craigslist,
    "blind1.png": blind,
    "apple.png": apple,
    "flush.png": flush,
    "millionaires.png": millionaires,
    "princesses1.png": princesses,
    "neutron-star.png": neutron_star,
    "minutes-in-a-day.png": minutes_in_a_day,
    "perfect-SAT1.png": perfect_sat,
    "exoplanets.png": exoplanets,
    "stars.png": stars,
    "seconds-in-an-hour.png": seconds_in_an_hour,
    "religions-in-the-world1.png": religions,
    "languages.png": languages,
    "sand1.png": sand,
    "1-in-20.png": one_in_20,
    "gay-lesbian-bisexual.png": gay_lesbian_bisexual,
    # Big "caption + dots" images.
    "Fenway.png": fenway,
    "manhattan-buildings.png": manhattan_buildings,
    "seconds-in-a-day.png": seconds_in_a_day,
    "abortions1.png": abortions,
    # Math diagrams from the Graham's Number article.
    "tetration-generally1.png": tetration_generally,
    "string-bundle-examples1.png": string_bundle_examples,
    "pentation-generally.png": pentation_generally,
    "hexation-generally1.png": hexation_generally,
    "sun-tower1.png": sun_tower,
    "insanity.png": insanity,
    "grahams-festival.png": grahams_festival,
    "grahams-number.png": grahams_number,
}


def main(only: list[str] | None = None) -> None:
    todo = sorted(set(HANDLERS) | set(COPY_AS_IS))
    if only:
        todo = [t for t in todo if t in only]
    for name in todo:
        if name in HANDLERS:
            process(name, HANDLERS[name])
        else:
            src = SRC_IMG / name
            dst = OUT_IMG / name
            shutil.copyfile(src, dst)
            print(f"copied {dst}")


if __name__ == "__main__":
    only = sys.argv[1:] or None
    main(only)
