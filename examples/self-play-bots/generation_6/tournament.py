#!/usr/bin/env python3
"""Iterated Prisoner's Dilemma tournament engine.

Bots live in bots/ as bot_*.py files exposing:
    choose_move(my_history: list[str], opp_history: list[str]) -> str

Returns 'C' or 'D'. Invalid output or exceptions count as 'D' for that round.

Histories shown to bots are the *observed* (post-noise) moves -- this models
"trembling hand" execution noise, where a bot intended one thing but the world
saw another. Both bots see the same noisy history.

Usage:
    python3 tournament.py                       # round-robin over bots/
    python3 tournament.py bots/X.py bots/Y.py   # single match
    python3 tournament.py --json                # machine-readable output
    python3 tournament.py --rounds 200 --noise 0.02 --repeat 3 --seed 42
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import random
import sys
import traceback
from pathlib import Path

# Payoff matrix (T > R > P > S, 2R > T + S).
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
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "choose_move"):
        raise AttributeError(f"{path} has no choose_move()")
    return path.stem, module.choose_move


def safe_call(fn, my_hist, opp_hist):
    """Call bot; coerce errors / bad output to 'D'."""
    try:
        # Defensive copy so a misbehaving bot can't mutate state we hand out.
        move = fn(list(my_hist), list(opp_hist))
    except Exception:
        return "D"
    if move not in ("C", "D"):
        return "D"
    return move


def play_match(fn_a, fn_b, rounds, noise, rng):
    """Play one match. Returns (score_a, score_b, hist_a, hist_b)."""
    # Each bot remembers what they OBSERVED (i.e. post-noise moves).
    hist_a: list[str] = []
    hist_b: list[str] = []
    score_a = 0
    score_b = 0
    for _ in range(rounds):
        # Bot A sees its own observed moves as my_history, B's observed as opp.
        move_a = safe_call(fn_a, hist_a, hist_b)
        move_b = safe_call(fn_b, hist_b, hist_a)
        # Apply trembling-hand noise.
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


def run_pair(fn_a, fn_b, rounds, noise, repeat, base_seed):
    """Repeat a match `repeat` times. Returns (avg_a, avg_b)."""
    total_a = 0
    total_b = 0
    for r in range(repeat):
        rng = random.Random(base_seed + r)
        sa, sb, _, _ = play_match(fn_a, fn_b, rounds, noise, rng)
        total_a += sa
        total_b += sb
    return total_a / repeat, total_b / repeat


def round_robin(bots, rounds, noise, repeat, seed):
    """Each bot plays each other (incl. self). Returns dict of results."""
    n = len(bots)
    names = [name for name, _ in bots]
    # matrix[i][j] = average score bot i got against bot j across `repeat` runs
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            # Use a deterministic per-pair seed so order doesn't matter.
            pair_seed = seed + 1000 * (i * n + j)
            avg_i, avg_j = run_pair(bots[i][1], bots[j][1], rounds, noise, repeat, pair_seed)
            matrix[i][j] = avg_i
            # NOTE: matrix[j][i] gets set when we hit (j, i) explicitly.
            # We do all (i, j) pairs to keep code simple, even though it's
            # 2x more matches than strictly needed. Self-play (i==j) is hit
            # exactly once, as required.
            if i != j:
                # Skip re-running the mirror; just record what we got.
                # Actually we DO want to re-run mirror so noise varies, but
                # we already loop through all (i, j) ordered pairs above.
                pass
    # Average per-round score per bot (averaged over opponents).
    totals = []
    for i in range(n):
        # Average score per opponent, then per round.
        per_opp = sum(matrix[i]) / n
        per_round = per_opp / rounds
        totals.append((names[i], per_opp, per_round))
    totals.sort(key=lambda x: -x[1])
    return {
        "names": names,
        "matrix": matrix,
        "totals": totals,
    }


def discover_bots(bots_dir: Path):
    """Find all bot_*.py files in bots_dir, excluding _failed/."""
    files = sorted(p for p in bots_dir.glob("bot_*.py"))
    return [load_bot(p) for p in files]


def fmt_table(result, rounds):
    names = result["names"]
    matrix = result["matrix"]
    totals = result["totals"]
    name_to_idx = {n: i for i, n in enumerate(names)}

    lines = []
    lines.append("RANKING (avg score per opponent, avg per round)")
    lines.append("-" * 72)
    for rank, (name, per_opp, per_round) in enumerate(totals, 1):
        lines.append(f"{rank:>2}. {name:<32} {per_opp:>8.2f}   ({per_round:.3f}/round)")
    lines.append("")
    lines.append("PAYOFF MATRIX (row plays column; cell = row's avg score)")
    lines.append("-" * 72)
    # Compact header
    col_w = 7
    header = " " * 28 + "".join(f"{n[:col_w-1]:>{col_w}}" for n in names)
    lines.append(header)
    for i, row_name in enumerate(names):
        row = f"{row_name:<28}"
        for j in range(len(names)):
            row += f"{matrix[i][j]:>{col_w}.1f}"
        lines.append(row)
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("bot_a", nargs="?", help="single match: bot A")
    parser.add_argument("bot_b", nargs="?", help="single match: bot B")
    parser.add_argument("--rounds", type=int, default=200)
    parser.add_argument("--noise", type=float, default=0.02)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bots-dir", default="bots")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.bot_a and args.bot_b:
        # Single match mode.
        bot_a = load_bot(Path(args.bot_a))
        bot_b = load_bot(Path(args.bot_b))
        avg_a, avg_b = run_pair(
            bot_a[1], bot_b[1], args.rounds, args.noise, args.repeat, args.seed
        )
        if args.json:
            print(json.dumps({
                "bot_a": bot_a[0],
                "bot_b": bot_b[0],
                "rounds": args.rounds,
                "noise": args.noise,
                "repeat": args.repeat,
                "seed": args.seed,
                "avg_a": avg_a,
                "avg_b": avg_b,
            }, indent=2))
        else:
            print(f"{bot_a[0]} vs {bot_b[0]} over {args.rounds} rounds "
                  f"(noise={args.noise}, repeat={args.repeat})")
            print(f"  {bot_a[0]:<28} {avg_a:>8.2f}")
            print(f"  {bot_b[0]:<28} {avg_b:>8.2f}")
        return 0

    bots_dir = Path(args.bots_dir)
    if not bots_dir.is_dir():
        print(f"no bots directory: {bots_dir}", file=sys.stderr)
        return 1
    bots = discover_bots(bots_dir)
    if len(bots) < 2:
        print(f"need at least 2 bots, found {len(bots)}", file=sys.stderr)
        return 1
    result = round_robin(bots, args.rounds, args.noise, args.repeat, args.seed)

    if args.json:
        out = {
            "params": {
                "rounds": args.rounds,
                "noise": args.noise,
                "repeat": args.repeat,
                "seed": args.seed,
            },
            "names": result["names"],
            "matrix": result["matrix"],
            "ranking": [
                {"name": n, "score": s, "per_round": pr}
                for n, s, pr in result["totals"]
            ],
        }
        print(json.dumps(out, indent=2))
    else:
        print(f"params: rounds={args.rounds} noise={args.noise} "
              f"repeat={args.repeat} seed={args.seed} bots={len(bots)}")
        print()
        print(fmt_table(result, args.rounds))
    return 0


if __name__ == "__main__":
    sys.exit(main())
