#!/usr/bin/env python3
"""Round-robin турнир по итерированной дилемме заключённого.

Использование:
    python3 tournament.py                       # полный round-robin по bots/
    python3 tournament.py bots/X.py bots/Y.py   # одиночный матч X vs Y
    python3 tournament.py --rounds 200 --noise 0.02 --repeat 3 --seed 42
    python3 tournament.py --json               # машино-читаемый вывод

Бот = .py файл с функцией:
    choose_move(my_history: list[str], opp_history: list[str]) -> str

Возвращает 'C' или 'D'. На любое исключение или некорректный возврат
считается, что бот сыграл 'D' в этом раунде.
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
from typing import Callable

# Матрица выплат в одном раунде, T > R > P > S и 2R > T + S.
PAYOFF = {
    ("C", "C"): (3, 3),
    ("C", "D"): (0, 5),
    ("D", "C"): (5, 0),
    ("D", "D"): (1, 1),
}


def load_bot(path: Path) -> tuple[str, Callable[[list[str], list[str]], str]]:
    """Загрузить бота из .py файла. Возвращает (имя, функция choose_move)."""
    name = path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"не удалось загрузить {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "choose_move"):
        raise RuntimeError(f"в {path} нет функции choose_move")
    return name, module.choose_move


def safe_move(fn: Callable, my_hist: list[str], opp_hist: list[str]) -> str:
    """Вызвать бот, защититься от исключений и мусора на выходе."""
    try:
        # Передаём копии, чтобы бот случайно не испортил историю.
        mv = fn(list(my_hist), list(opp_hist))
    except Exception:
        return "D"
    if mv not in ("C", "D"):
        return "D"
    return mv


def play_match(
    a_fn: Callable,
    b_fn: Callable,
    rounds: int,
    noise: float,
    rng: random.Random,
) -> tuple[int, int, list[tuple[str, str]]]:
    """Один матч A vs B. Возвращает (очки_A, очки_B, лог раундов после шума)."""
    a_hist: list[str] = []
    b_hist: list[str] = []
    a_score = 0
    b_score = 0
    log: list[tuple[str, str]] = []
    for _ in range(rounds):
        a_mv = safe_move(a_fn, a_hist, b_hist)
        b_mv = safe_move(b_fn, b_hist, a_hist)
        # Шум: каждый ход с вероятностью noise переворачивается.
        if noise > 0:
            if rng.random() < noise:
                a_mv = "D" if a_mv == "C" else "C"
            if rng.random() < noise:
                b_mv = "D" if b_mv == "C" else "C"
        pa, pb = PAYOFF[(a_mv, b_mv)]
        a_score += pa
        b_score += pb
        # В историю кладём то, что фактически было сыграно (после шума).
        # Это даёт ботам шанс увидеть реальный ход соперника, как в жизни.
        a_hist.append(a_mv)
        b_hist.append(b_mv)
        log.append((a_mv, b_mv))
    return a_score, b_score, log


def run_tournament(
    bot_paths: list[Path],
    rounds: int,
    noise: float,
    repeat: int,
    seed: int,
) -> dict:
    """Round-robin по списку ботов (включая матчи с самим собой)."""
    bots: list[tuple[str, Callable]] = [load_bot(p) for p in bot_paths]
    names = [n for n, _ in bots]
    n = len(bots)
    # totals[i] = суммарные очки бота i во всех матчах.
    totals = [0.0] * n
    # matches_played[i] = сколько матчей сыграл бот i.
    matches_played = [0] * n
    # matrix[i][j] = средние очки бота i против бота j за один матч.
    matrix = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(i, n):
            scores_i: list[int] = []
            scores_j: list[int] = []
            for rep in range(repeat):
                rng = random.Random((seed * 1_000_003) ^ (i * 1009 + j) ^ rep)
                si, sj, _ = play_match(
                    bots[i][1], bots[j][1], rounds, noise, rng
                )
                scores_i.append(si)
                scores_j.append(sj)
            avg_i = sum(scores_i) / repeat
            avg_j = sum(scores_j) / repeat
            matrix[i][j] = avg_i
            matrix[j][i] = avg_j
            if i == j:
                # Матч с самим собой считаем один раз для тотала.
                totals[i] += avg_i
                matches_played[i] += 1
            else:
                totals[i] += avg_i
                totals[j] += avg_j
                matches_played[i] += 1
                matches_played[j] += 1

    avg_per_match = [
        totals[i] / matches_played[i] if matches_played[i] else 0.0
        for i in range(n)
    ]
    avg_per_round = [s / rounds for s in avg_per_match]
    order = sorted(range(n), key=lambda i: avg_per_match[i], reverse=True)

    return {
        "params": {
            "rounds": rounds,
            "noise": noise,
            "repeat": repeat,
            "seed": seed,
        },
        "bots": names,
        "totals": totals,
        "matches_played": matches_played,
        "avg_per_match": avg_per_match,
        "avg_per_round": avg_per_round,
        "matrix": matrix,
        "order": order,
    }


def format_report(result: dict) -> str:
    """Текстовый отчёт о турнире."""
    p = result["params"]
    names = result["bots"]
    order = result["order"]
    lines: list[str] = []
    lines.append(
        f"Параметры: rounds={p['rounds']}, noise={p['noise']}, "
        f"repeat={p['repeat']}, seed={p['seed']}"
    )
    lines.append(f"Ботов: {len(names)}")
    lines.append("")
    lines.append("Рейтинг (среднее очков за матч / за раунд):")
    width = max(len(n) for n in names)
    for rank, i in enumerate(order, 1):
        lines.append(
            f"  {rank:2d}. {names[i]:<{width}}  "
            f"{result['avg_per_match'][i]:7.2f}  "
            f"({result['avg_per_round'][i]:.3f} за раунд)"
        )
    lines.append("")
    lines.append("Матрица 'строка против столбца', среднее за матч:")
    header = " " * (width + 2) + "  ".join(f"{n[:8]:>8}" for n in names)
    lines.append(header)
    for i in range(len(names)):
        row = f"{names[i]:<{width}}  " + "  ".join(
            f"{result['matrix'][i][j]:8.2f}" for j in range(len(names))
        )
        lines.append(row)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bots", nargs="*", help="пути к .py файлам ботов")
    parser.add_argument("--rounds", type=int, default=200)
    parser.add_argument("--noise", type=float, default=0.02)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--json", action="store_true", help="JSON-вывод")
    parser.add_argument(
        "--bots-dir",
        default="bots",
        help="каталог с ботами, если не заданы явно",
    )
    args = parser.parse_args()

    here = Path(__file__).resolve().parent

    if args.bots:
        bot_paths = [Path(p).resolve() for p in args.bots]
    else:
        bots_dir = (here / args.bots_dir).resolve()
        bot_paths = sorted(
            p for p in bots_dir.glob("bot_*.py") if p.is_file()
        )

    if not bot_paths:
        print("нет ботов для прогона", file=sys.stderr)
        return 2

    # Одиночный матч: ровно 2 бота — выводим подробности и счёт.
    if len(bot_paths) == 2 and args.bots:
        name_a, fn_a = load_bot(bot_paths[0])
        name_b, fn_b = load_bot(bot_paths[1])
        scores_a: list[int] = []
        scores_b: list[int] = []
        for rep in range(args.repeat):
            rng = random.Random(args.seed + rep)
            sa, sb, _ = play_match(
                fn_a, fn_b, args.rounds, args.noise, rng
            )
            scores_a.append(sa)
            scores_b.append(sb)
        avg_a = sum(scores_a) / args.repeat
        avg_b = sum(scores_b) / args.repeat
        if args.json:
            out = {
                "match": [name_a, name_b],
                "scores_a": scores_a,
                "scores_b": scores_b,
                "avg_a": avg_a,
                "avg_b": avg_b,
                "params": {
                    "rounds": args.rounds,
                    "noise": args.noise,
                    "repeat": args.repeat,
                    "seed": args.seed,
                },
            }
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            print(f"{name_a} vs {name_b}")
            print(f"  {name_a}: {scores_a} (avg {avg_a:.2f})")
            print(f"  {name_b}: {scores_b} (avg {avg_b:.2f})")
        return 0

    result = run_tournament(
        bot_paths,
        rounds=args.rounds,
        noise=args.noise,
        repeat=args.repeat,
        seed=args.seed,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_report(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
