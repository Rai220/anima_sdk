#!/usr/bin/env python3
"""Iterated Prisoner's Dilemma tournament engine.

Usage:
    python3 tournament.py                       # full round-robin over bots/
    python3 tournament.py bots/A.py bots/B.py   # single match between two bots
    python3 tournament.py --rounds 200 --noise 0.02 --repeat 3 --seed 42
    python3 tournament.py --json                # machine-readable output

A bot is any *.py file in bots/ (filename starting with "bot_" by convention,
files starting with "_" are skipped) exposing:

    def choose_move(my_history: list[str], opp_history: list[str]) -> str:
        '''Return 'C' or 'D'. First call: both lists are empty.'''

Rules:
- If a bot returns anything other than 'C'/'D' or raises, its move that
  round is recorded as 'D'.
- Noise: with probability --noise the actual played move is flipped before
  scoring AND before being appended to history (both players see the flipped
  move). This models "trembling hand" mistakes.
- Each ordered pair plays `--repeat` independent matches; final pairwise
  score is the average per-round payoff over all repeats.
- Self-play is included.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import random
import sys
import traceback
from pathlib import Path
from typing import Callable

PAYOFF = {
    ("C", "C"): (3, 3),
    ("C", "D"): (0, 5),
    ("D", "C"): (5, 0),
    ("D", "D"): (1, 1),
}

ChooseMove = Callable[[list, list], str]


def load_bot(path: Path) -> tuple[str, ChooseMove]:
    """Load a bot module from a .py file. Returns (name, choose_move)."""
    name = path.stem
    spec = importlib.util.spec_from_file_location(f"bot_module_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "choose_move"):
        raise RuntimeError(f"{path} has no choose_move()")
    return name, module.choose_move


def discover_bots(bots_dir: Path) -> list[tuple[str, ChooseMove]]:
    bots = []
    for path in sorted(bots_dir.glob("*.py")):
        if path.name.startswith("_"):
            continue
        bots.append(load_bot(path))
    return bots


def safe_call(fn: ChooseMove, my_hist: list, opp_hist: list) -> str:
    """Call bot; coerce errors / bad outputs to 'D'."""
    try:
        move = fn(list(my_hist), list(opp_hist))
    except Exception:
        return "D"
    if move not in ("C", "D"):
        return "D"
    return move


def play_match(
    fn_a: ChooseMove,
    fn_b: ChooseMove,
    rounds: int,
    noise: float,
    rng: random.Random,
) -> tuple[float, float, list, list]:
    """Play one match. Returns (avg_a, avg_b, hist_a, hist_b).

    Histories are the moves *as observed* (post-noise) by both players.
    """
    hist_a: list = []
    hist_b: list = []
    score_a = 0
    score_b = 0
    for _ in range(rounds):
        move_a = safe_call(fn_a, hist_a, hist_b)
        move_b = safe_call(fn_b, hist_b, hist_a)
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
    return score_a / rounds, score_b / rounds, hist_a, hist_b


def play_pair(
    name_a: str,
    fn_a: ChooseMove,
    name_b: str,
    fn_b: ChooseMove,
    rounds: int,
    noise: float,
    repeat: int,
    base_seed: int,
) -> tuple[float, float]:
    """Average over `repeat` matches with deterministic per-pair seeds."""
    tot_a = 0.0
    tot_b = 0.0
    for r in range(repeat):
        # Cross-process-deterministic seed (Python's hash() randomises strings
        # per process by default, which would change pair seeds between runs).
        key = f"{base_seed}|{name_a}|{name_b}|{r}".encode("utf-8")
        seed = int.from_bytes(hashlib.sha1(key).digest()[:4], "big")
        rng = random.Random(seed)
        a, b, _, _ = play_match(fn_a, fn_b, rounds, noise, rng)
        tot_a += a
        tot_b += b
    return tot_a / repeat, tot_b / repeat


def run_tournament(
    bots: list[tuple[str, ChooseMove]],
    rounds: int,
    noise: float,
    repeat: int,
    seed: int,
) -> dict:
    names = [n for n, _ in bots]
    n = len(bots)
    # matrix[i][j] = average per-round score that bot i gets when playing bot j.
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i, n):
            ni, fi = bots[i]
            nj, fj = bots[j]
            si, sj = play_pair(ni, fi, nj, fj, rounds, noise, repeat, seed)
            matrix[i][j] = si
            if i != j:
                matrix[j][i] = sj
    totals = []
    for i, name in enumerate(names):
        # Average across all opponents (including self).
        avg = sum(matrix[i]) / n
        totals.append((name, avg))
    totals.sort(key=lambda x: -x[1])
    return {
        "names": names,
        "matrix": matrix,
        "ranking": totals,
        "params": {
            "rounds": rounds,
            "noise": noise,
            "repeat": repeat,
            "seed": seed,
            "n_bots": n,
        },
    }


def format_report(result: dict) -> str:
    names = result["names"]
    matrix = result["matrix"]
    ranking = result["ranking"]
    params = result["params"]
    lines = []
    lines.append(
        f"Tournament: rounds={params['rounds']} noise={params['noise']} "
        f"repeat={params['repeat']} seed={params['seed']} n={params['n_bots']}"
    )
    lines.append("")
    lines.append("Ranking (avg per-round score across all opponents):")
    for i, (name, avg) in enumerate(ranking, 1):
        lines.append(f"  {i:>2}. {name:<28} {avg:6.3f}")
    lines.append("")
    lines.append("Pairwise matrix (row = bot, col = opponent, value = avg/round):")
    col_w = max(8, max(len(n) for n in names) + 1)
    header = " " * (col_w + 2) + "  ".join(f"{n[:8]:>8}" for n in names)
    lines.append(header)
    for i, row_name in enumerate(names):
        cells = "  ".join(f"{matrix[i][j]:8.3f}" for j in range(len(names)))
        lines.append(f"{row_name:<{col_w}}  {cells}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Iterated Prisoner's Dilemma tournament")
    ap.add_argument("positional", nargs="*", help="Optional: two bot paths for single match")
    ap.add_argument("--rounds", type=int, default=200)
    ap.add_argument("--noise", type=float, default=0.02)
    ap.add_argument("--repeat", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--bots-dir", default="bots")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    # Seed the global random module so stochastic bots (e.g. bot_random)
    # produce reproducible output for a given --seed.
    random.seed(args.seed)

    if len(args.positional) == 2:
        bots = [load_bot(Path(p)) for p in args.positional]
    elif len(args.positional) == 0:
        bots_dir = Path(args.bots_dir)
        if not bots_dir.is_dir():
            print(f"No bots dir: {bots_dir}", file=sys.stderr)
            return 2
        bots = discover_bots(bots_dir)
        if len(bots) < 2:
            print(f"Need at least 2 bots, found {len(bots)}", file=sys.stderr)
            return 2
    else:
        print("Pass either 0 or 2 bot paths", file=sys.stderr)
        return 2

    result = run_tournament(bots, args.rounds, args.noise, args.repeat, args.seed)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
