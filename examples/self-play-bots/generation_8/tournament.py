#!/usr/bin/env python3
"""Iterated Prisoner's Dilemma round-robin tournament engine.

Usage:
    python3 tournament.py                       # full round-robin on bots/
    python3 tournament.py bots/X.py bots/Y.py   # single match
    python3 tournament.py --json                # machine-readable
    python3 tournament.py --rounds 200 --noise 0.02 --repeat 3 --seed 42
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import random
import sys
import traceback
from pathlib import Path

# Payoff matrix: (my, opp) -> (my_score, opp_score)
PAYOFF = {
    ("C", "C"): (3, 3),
    ("C", "D"): (0, 5),
    ("D", "C"): (5, 0),
    ("D", "D"): (1, 1),
}


def load_bot(path: Path):
    """Load a bot module from a file path. Returns (name, choose_move)."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "choose_move"):
        raise AttributeError(f"{path} has no choose_move()")
    return path.stem, module.choose_move


def safe_call(choose_move, my_hist, opp_hist):
    """Call bot safely. Bad return / exception -> 'D'."""
    try:
        move = choose_move(list(my_hist), list(opp_hist))
    except Exception:
        return "D"
    if move not in ("C", "D"):
        return "D"
    return move


def play_match(bot_a, bot_b, rounds: int, noise: float, rng: random.Random):
    """Single match of `rounds` rounds. Returns (score_a, score_b, hist_a, hist_b)."""
    name_a, fn_a = bot_a
    name_b, fn_b = bot_b
    hist_a: list[str] = []
    hist_b: list[str] = []
    score_a = 0
    score_b = 0
    for _ in range(rounds):
        move_a = safe_call(fn_a, hist_a, hist_b)
        move_b = safe_call(fn_b, hist_b, hist_a)
        # Noise: flip each move independently with probability `noise`
        if noise > 0:
            if rng.random() < noise:
                move_a = "D" if move_a == "C" else "C"
            if rng.random() < noise:
                move_b = "D" if move_b == "C" else "C"
        pa, pb = PAYOFF[(move_a, move_b)]
        score_a += pa
        score_b += pb
        hist_a.append(move_a)
        hist_b.append(move_b)
    return score_a, score_b, hist_a, hist_b


def play_match_repeated(bot_a, bot_b, rounds: int, noise: float, repeat: int, seed: int):
    """Play `repeat` matches, return average (score_a, score_b) per match."""
    total_a = 0
    total_b = 0
    for r in range(repeat):
        match_key = f"{seed}|{bot_a[0]}|{bot_b[0]}|{r}"
        rng = random.Random(match_key)
        # Re-seed the global RNG so bots that call random.random() get
        # reproducible (but independent across matches) behavior.
        random.seed(match_key + "|bots")
        sa, sb, _, _ = play_match(bot_a, bot_b, rounds, noise, rng)
        total_a += sa
        total_b += sb
    return total_a / repeat, total_b / repeat


def find_bots(bots_dir: Path) -> list[Path]:
    """Find all bot_*.py files in bots_dir (non-recursive, skip _failed/)."""
    paths = []
    for p in sorted(bots_dir.glob("bot_*.py")):
        if "_failed" in p.parts:
            continue
        paths.append(p)
    return paths


def round_robin(bot_paths: list[Path], rounds: int, noise: float, repeat: int, seed: int):
    """Each bot plays every other bot (including self). Returns results dict."""
    bots = [load_bot(p) for p in bot_paths]
    n = len(bots)
    # matrix[i][j] = avg score bot i got against bot j
    matrix = [[0.0] * n for _ in range(n)]
    totals = [0.0] * n
    counts = [0] * n
    for i in range(n):
        for j in range(i, n):
            sa, sb = play_match_repeated(bots[i], bots[j], rounds, noise, repeat, seed)
            if i == j:
                matrix[i][i] = sa  # self-play
                totals[i] += sa
                counts[i] += 1
            else:
                matrix[i][j] = sa
                matrix[j][i] = sb
                totals[i] += sa
                totals[j] += sb
                counts[i] += 1
                counts[j] += 1
    averages = [totals[i] / counts[i] if counts[i] else 0.0 for i in range(n)]
    names = [b[0] for b in bots]
    ranking = sorted(range(n), key=lambda i: -averages[i])
    return {
        "names": names,
        "matrix": matrix,
        "averages": averages,
        "ranking": [names[i] for i in ranking],
        "ranking_scores": [averages[i] for i in ranking],
        "params": {"rounds": rounds, "noise": noise, "repeat": repeat, "seed": seed},
    }


def print_text_report(result):
    p = result["params"]
    print(f"# IPD Tournament")
    print(f"rounds={p['rounds']} noise={p['noise']} repeat={p['repeat']} seed={p['seed']}")
    print()
    print("## Ranking (avg score per match)")
    for i, (name, score) in enumerate(zip(result["ranking"], result["ranking_scores"]), 1):
        print(f"{i:2d}. {name:30s} {score:7.2f}")
    print()
    print("## Matrix (row = bot, col = opponent, value = row's avg score)")
    names = result["names"]
    width = max(len(n) for n in names)
    header = " " * (width + 2) + " ".join(f"{n[:8]:>8s}" for n in names)
    print(header)
    for i, name in enumerate(names):
        row = " ".join(f"{result['matrix'][i][j]:8.1f}" for j in range(len(names)))
        print(f"{name:{width}s}  {row}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bots", nargs="*", help="Optional: two bot paths for single match")
    ap.add_argument("--rounds", type=int, default=200)
    ap.add_argument("--noise", type=float, default=0.02)
    ap.add_argument("--repeat", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--bots-dir", default="bots")
    args = ap.parse_args()

    if len(args.bots) == 2:
        bot_a = load_bot(Path(args.bots[0]))
        bot_b = load_bot(Path(args.bots[1]))
        sa, sb = play_match_repeated(bot_a, bot_b, args.rounds, args.noise, args.repeat, args.seed)
        if args.json:
            print(json.dumps({"a": bot_a[0], "b": bot_b[0], "score_a": sa, "score_b": sb}))
        else:
            print(f"{bot_a[0]} vs {bot_b[0]}: {sa:.2f} - {sb:.2f}")
        return

    bots_dir = Path(args.bots_dir)
    bot_paths = find_bots(bots_dir)
    if not bot_paths:
        print(f"No bots found in {bots_dir}/", file=sys.stderr)
        sys.exit(1)
    result = round_robin(bot_paths, args.rounds, args.noise, args.repeat, args.seed)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_text_report(result)


if __name__ == "__main__":
    main()
