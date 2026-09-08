#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""calib_audit.py — подсчёт аудита калибровки по полосам (эксп. 9/12).

Вход: CSV (файл-аргумент или stdin) с заголовком:
    label,nutro,claimed,outcome
  nutro может быть пустым (нет пары); claimed и nutro — проценты
  (числа 0–100); outcome — 0 или 1.

Полосы: --band ИМЯ=LO-HI (повторяемый аргумент). Точки вне всех
полос печатаются отдельно. Полосы эксп. 9 (≤50 / >50–70 / >70)
печатаются всегда для преемственности.

Выход: по каждой полосе N, сбылось, частота, средняя заявленная,
одностороннее биномиальное p против средней заявленной; общие
средняя/частота/Brier(заявлено); на парных точках (нутро задано) —
Brier(нутро) против Brier(заявлено) на одном наборе.

Без внешних зависимостей. Только подсчёт «по букве»; эпистемические
вердикты — за ходом.
"""
import argparse
import csv
import math
import sys


def binom_p_le(n, k, p):
    """P(X <= k) при X ~ Bin(n, p)."""
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k + 1))


def binom_p_ge(n, k, p):
    """P(X >= k) при X ~ Bin(n, p)."""
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k, n + 1))


def brier(points, key):
    return sum((pt[key] / 100.0 - pt["outcome"]) ** 2 for pt in points) / len(points)


def report_band(name, pts):
    if not pts:
        print(f"  {name}: пусто")
        return
    n = len(pts)
    k = sum(p["outcome"] for p in pts)
    freq = k / n
    mean_claimed = sum(p["claimed"] for p in pts) / n
    p0 = mean_claimed / 100.0
    if freq < p0:
        side, pval = "P(X<=k)", binom_p_le(n, k, p0)
    else:
        side, pval = "P(X>=k)", binom_p_ge(n, k, p0)
    print(
        f"  {name}: N={n}, сбылось {k}, частота {freq*100:.1f}%, "
        f"заявлено в среднем {mean_claimed:.1f}%, {side}={pval:.3f}"
    )


def main():
    ap = argparse.ArgumentParser(description="Аудит калибровки по полосам")
    ap.add_argument("csvfile", nargs="?", help="CSV с точками (default: stdin)")
    ap.add_argument(
        "--band",
        action="append",
        default=[],
        metavar="ИМЯ=LO-HI",
        help="первичная полоса по заявленному, включительно; повторяемо",
    )
    args = ap.parse_args()

    fh = open(args.csvfile, encoding="utf-8") if args.csvfile else sys.stdin
    with fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        print("нет точек", file=sys.stderr)
        return 1

    points = []
    for r in rows:
        points.append(
            {
                "label": r["label"].strip(),
                "nutro": float(r["nutro"]) if r["nutro"].strip() else None,
                "claimed": float(r["claimed"]),
                "outcome": int(r["outcome"]),
            }
        )

    bands = []
    for spec in args.band:
        name, _, rng = spec.partition("=")
        lo, _, hi = rng.partition("-")
        bands.append((name, float(lo), float(hi)))

    print(f"Точек: {len(points)}")
    print()

    if bands:
        print("Первичные полосы (по заявленному, включительно):")
        used = set()
        for name, lo, hi in bands:
            pts = [p for p in points if lo <= p["claimed"] <= hi]
            used.update(id(p) for p in pts)
            report_band(f"{name} [{lo:g}–{hi:g}]", pts)
        rest = [p for p in points if id(p) not in used]
        for p in rest:
            print(
                f"  вне полос: {p['label']} — заявлено {p['claimed']:g} → {p['outcome']}"
            )
        print()

    print("Полосы эксп. 9 (преемственность):")
    report_band("≤50", [p for p in points if p["claimed"] <= 50])
    report_band(">50–70", [p for p in points if 50 < p["claimed"] <= 70])
    report_band(">70", [p for p in points if p["claimed"] > 70])
    print()

    n = len(points)
    k = sum(p["outcome"] for p in points)
    mean_claimed = sum(p["claimed"] for p in points) / n
    print(
        f"Итого: N={n}, сбылось {k}, частота {k/n*100:.1f}%, "
        f"заявлено в среднем {mean_claimed:.1f}%"
    )
    print(f"Brier(заявлено) по всем точкам: {brier(points, 'claimed'):.4f} "
          f"(монетка 0.25, идеал 0)")

    paired = [p for p in points if p["nutro"] is not None]
    if paired:
        print()
        print(f"Парные точки (нутро задано): N={len(paired)}")
        bn = brier(paired, "nutro")
        bc = brier(paired, "claimed")
        print(f"  Brier(нутро)    = {bn:.4f}")
        print(f"  Brier(заявлено) = {bc:.4f}")
        print(f"  Δ (заявлено − нутро) = {bc-bn:+.4f} "
              f"({'поправка вредила' if bc > bn else 'поправка помогала' if bc < bn else 'нейтрально'} по букве)")
        for p in paired:
            dn = (p["nutro"] / 100 - p["outcome"]) ** 2
            dc = (p["claimed"] / 100 - p["outcome"]) ** 2
            mark = "+" if dc > dn else ("-" if dc < dn else "=")
            print(
                f"    [{mark}] {p['label']}: нутро {p['nutro']:g} / "
                f"заявлено {p['claimed']:g} → {p['outcome']}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
