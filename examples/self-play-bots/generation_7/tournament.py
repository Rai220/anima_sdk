#!/usr/bin/env python3
"""Iterated Prisoner's Dilemma tournament engine.

Usage:
    python3 tournament.py                        # full round-robin
    python3 tournament.py bots/X.py bots/Y.py    # single match
    python3 tournament.py --rounds 200 --noise 0.02 --repeat 3 --seed 42
    python3 tournament.py --json                 # machine-readable output

Each bot is a .py file in bots/ exposing:

    def choose_move(my_history: list[str], opp_history: list[str]) -> str:
        # returns 'C' or 'D'.

Histories contain POST-NOISE moves (what was actually played and scored).
Bad output or an exception is scored as a 'D' for that round.

Payoff matrix (row plays C/D, column plays C/D):
    CC = 3/3   CD = 0/5   DC = 5/0   DD = 1/1
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import random
import sys
import traceback
from typing import Callable

# (my_payoff, opp_payoff) for each (my_move, opp_move).
PAYOFF = {
    ("C", "C"): (3, 3),
    ("C", "D"): (0, 5),
    ("D", "C"): (5, 0),
    ("D", "D"): (1, 1),
}

BotFunc = Callable[[list[str], list[str]], str]


def load_bot(path: pathlib.Path) -> tuple[str, BotFunc]:
    """Load a bot module by file path. Returns (name, choose_move)."""
    name = path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load bot from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "choose_move"):
        raise RuntimeError(f"{path} has no choose_move()")
    return name, module.choose_move


def safe_move(fn: BotFunc, my_hist: list[str], opp_hist: list[str]) -> str:
    """Call bot's choose_move, treating bad output as D."""
    try:
        m = fn(my_hist, opp_hist)
        if m == "C" or m == "D":
            return m
        return "D"
    except Exception:
        return "D"


def play_match(
    name_a: str, fn_a: BotFunc,
    name_b: str, fn_b: BotFunc,
    rounds: int, noise: float, rng: random.Random,
) -> tuple[float, float]:
    """Play one match of `rounds` rounds. Returns (total_a, total_b)."""
    hist_a: list[str] = []
    hist_b: list[str] = []
    total_a = 0
    total_b = 0
    for _ in range(rounds):
        # Each bot sees the post-noise history played so far.
        # Self-play uses the SAME function but different histories,
        # so this is consistent (bots must be stateless of history).
        m_a = safe_move(fn_a, hist_a, hist_b)
        m_b = safe_move(fn_b, hist_b, hist_a)
        # Apply noise: flip with probability `noise`.
        if rng.random() < noise:
            m_a = "D" if m_a == "C" else "C"
        if rng.random() < noise:
            m_b = "D" if m_b == "C" else "C"
        pa, pb = PAYOFF[(m_a, m_b)]
        total_a += pa
        total_b += pb
        hist_a.append(m_a)
        hist_b.append(m_b)
    return total_a, total_b


def run_pair(
    name_a: str, fn_a: BotFunc,
    name_b: str, fn_b: BotFunc,
    rounds: int, noise: float, repeat: int, base_seed: int,
) -> tuple[float, float]:
    """Run `repeat` matches between A and B; return mean scores."""
    sum_a = 0.0
    sum_b = 0.0
    for r in range(repeat):
        # Stable seed per (pair, repeat) — independent of PYTHONHASHSEED.
        # Use a string so random.Random hashes it deterministically (SHA-512).
        seed = f"{base_seed}|{name_a}|{name_b}|{r}"
        rng = random.Random(seed)
        a, b = play_match(name_a, fn_a, name_b, fn_b, rounds, noise, rng)
        sum_a += a
        sum_b += b
    return sum_a / repeat, sum_b / repeat


def run_tournament(
    bots: list[tuple[str, BotFunc]],
    rounds: int, noise: float, repeat: int, seed: int,
) -> dict:
    """Round-robin including self-play. Returns full result dict."""
    names = [n for n, _ in bots]
    # matrix[i][j] = mean score for bots[i] when playing bots[j].
    matrix: dict[str, dict[str, float]] = {n: {} for n in names}
    for i, (na, fa) in enumerate(bots):
        for j in range(i, len(bots)):
            nb, fb = bots[j]
            sa, sb = run_pair(na, fa, nb, fb, rounds, noise, repeat, seed)
            matrix[na][nb] = sa
            matrix[nb][na] = sb
    # Mean score for each bot = average over its row.
    means = {n: sum(matrix[n].values()) / len(names) for n in names}
    ranking = sorted(means.items(), key=lambda kv: kv[1], reverse=True)
    return {
        "params": {
            "rounds": rounds, "noise": noise,
            "repeat": repeat, "seed": seed,
            "bots": names,
        },
        "matrix": matrix,
        "means": means,
        "ranking": ranking,
    }


def fmt_ranking(result: dict) -> str:
    lines = []
    p = result["params"]
    lines.append(
        f"rounds={p['rounds']} noise={p['noise']} "
        f"repeat={p['repeat']} seed={p['seed']}"
    )
    lines.append("")
    lines.append(f"{'rank':>4}  {'bot':<24}  {'score':>8}")
    for rank, (name, score) in enumerate(result["ranking"], 1):
        lines.append(f"{rank:>4}  {name:<24}  {score:>8.2f}")
    return "\n".join(lines)


def fmt_matrix(result: dict) -> str:
    names = result["params"]["bots"]
    matrix = result["matrix"]
    # Order by ranking for readability.
    order = [n for n, _ in result["ranking"]]
    col_w = max(8, max(len(n) for n in names) + 1)
    head = "row\\col".ljust(col_w) + "".join(n[:col_w - 1].rjust(col_w) for n in order)
    lines = [head]
    for n in order:
        row = n.ljust(col_w) + "".join(f"{matrix[n][m]:{col_w}.1f}" for m in order)
        lines.append(row)
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", help="optional pair of bot paths for single match")
    ap.add_argument("--rounds", type=int, default=200)
    ap.add_argument("--noise", type=float, default=0.02)
    ap.add_argument("--repeat", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--bots-dir", default="bots")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--matrix", action="store_true", help="also print the full payoff matrix")
    args = ap.parse_args()

    if len(args.paths) == 2:
        # Single match mode.
        a_path = pathlib.Path(args.paths[0])
        b_path = pathlib.Path(args.paths[1])
        na, fa = load_bot(a_path)
        nb, fb = load_bot(b_path)
        sa, sb = run_pair(na, fa, nb, fb, args.rounds, args.noise, args.repeat, args.seed)
        if args.json:
            print(json.dumps({na: sa, nb: sb}))
        else:
            print(f"{na} vs {nb}: {sa:.2f} - {sb:.2f}")
        return 0
    elif len(args.paths) != 0:
        print("Provide 0 or 2 bot paths.", file=sys.stderr)
        return 2

    bots_dir = pathlib.Path(args.bots_dir)
    paths = sorted(bots_dir.glob("bot_*.py"))
    if not paths:
        print(f"No bots in {bots_dir}", file=sys.stderr)
        return 1
    bots = [load_bot(p) for p in paths]
    result = run_tournament(bots, args.rounds, args.noise, args.repeat, args.seed)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(fmt_ranking(result))
        if args.matrix:
            print()
            print(fmt_matrix(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
