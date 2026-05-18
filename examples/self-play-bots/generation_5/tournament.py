#!/usr/bin/env python3
"""Турнир для итерированной дилеммы заключённого.

Запуск:

    python3 tournament.py                       # round-robin по bots/
    python3 tournament.py --json                # машино-читаемый вывод
    python3 tournament.py bots/A.py bots/B.py   # один матч
    python3 tournament.py --rounds 200 --noise 0.02 --repeat 3 --seed 42

Каждый бот живёт в bots/bot_<name>.py и реализует функцию

    choose_move(my_history: list[str], opp_history: list[str]) -> str

Возвращает 'C' или 'D'. На первый ход обе истории пустые. Если бот
возвращает что-то иное или падает — за этот ход ему засчитывается 'D'.

Шум: с вероятностью --noise каждый ход независимо переворачивается ПЕРЕД
подсчётом очков и ПЕРЕД записью в историю обоих игроков. Это значит,
что бот не знает наверняка, как его ход был "прочитан" соперником, и
наоборот.

Матрица выплат (классический Аксельрод, T > R > P > S, 2R > T + S):

    мой / соперник     C        D
    C                  3 / 3    0 / 5
    D                  5 / 0    1 / 1
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import sys
import traceback
from pathlib import Path
from typing import Callable


def _stable_seed(*parts) -> int:
    """Детерминированный 32-битный seed из произвольных аргументов.

    Используем sha1, потому что Python-овский hash() в строках
    рандомизируется per process (PYTHONHASHSEED), и тогда турнир бы не
    воспроизводился между запусками.
    """
    h = hashlib.sha1()
    for p in parts:
        h.update(repr(p).encode("utf-8"))
        h.update(b"|")
    return int.from_bytes(h.digest()[:4], "big")


PAYOFF = {
    ("C", "C"): (3, 3),
    ("C", "D"): (0, 5),
    ("D", "C"): (5, 0),
    ("D", "D"): (1, 1),
}

BOTS_DIR = Path(__file__).resolve().parent / "bots"


# ---------------------------------------------------------------------------
# Загрузка ботов


def load_bot(path: Path) -> tuple[str, Callable[[list[str], list[str]], str]]:
    """Загружает бот из файла, возвращает (имя, функцию choose_move)."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Не удалось загрузить {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fn = getattr(module, "choose_move", None)
    if not callable(fn):
        raise RuntimeError(f"{path}: нет функции choose_move(my, opp)")
    return path.stem, fn


def discover_bots(bots_dir: Path = BOTS_DIR) -> list[tuple[str, Callable]]:
    """Все bots/bot_*.py отсортированные по имени. _failed/ игнорируется."""
    files = sorted(bots_dir.glob("bot_*.py"))
    return [load_bot(p) for p in files]


# ---------------------------------------------------------------------------
# Один матч


def safe_choose(fn: Callable, my_hist: list[str], opp_hist: list[str]) -> str:
    """Вызвать choose_move. Любая ошибка / неверный ответ → 'D'."""
    try:
        move = fn(list(my_hist), list(opp_hist))
    except Exception:
        return "D"
    if move not in ("C", "D"):
        return "D"
    return move


def play_match(
    fn_a: Callable,
    fn_b: Callable,
    rounds: int,
    noise: float,
    rng: random.Random,
) -> tuple[int, int]:
    """Сыграть один матч из `rounds` раундов. Возвращает (score_a, score_b).

    Глобальный модуль `random` сидируется детерминированно на время
    матча из rng, чтобы стохастические боты (использующие
    `random.random()`) тоже давали воспроизводимые результаты при
    одном и том же --seed. Состояние random восстанавливается в конце.
    """
    hist_a: list[str] = []
    hist_b: list[str] = []
    score_a = 0
    score_b = 0
    # Сохранить глобальное состояние random и засеять детерминированно.
    saved_state = random.getstate()
    random.seed(rng.randrange(2**31))
    try:
        for _ in range(rounds):
            a = safe_choose(fn_a, hist_a, hist_b)
            b = safe_choose(fn_b, hist_b, hist_a)
            # Применяем шум: каждый ход независимо переворачивается с
            # вероятностью `noise` перед подсчётом и записью в историю.
            if noise > 0:
                if rng.random() < noise:
                    a = "D" if a == "C" else "C"
                if rng.random() < noise:
                    b = "D" if b == "C" else "C"
            pa, pb = PAYOFF[(a, b)]
            score_a += pa
            score_b += pb
            hist_a.append(a)
            hist_b.append(b)
    finally:
        random.setstate(saved_state)
    return score_a, score_b


# ---------------------------------------------------------------------------
# Round-robin турнир


def run_tournament(
    bots: list[tuple[str, Callable]],
    rounds: int,
    noise: float,
    repeat: int,
    seed: int,
) -> dict:
    """Round-robin: каждый с каждым (включая self-play), `repeat` повторов."""
    names = [name for name, _ in bots]
    n = len(bots)
    # matrix[i][j] = средний счёт бота i в матче против бота j
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        name_i, fn_i = bots[i]
        for j in range(i, n):
            name_j, fn_j = bots[j]
            total_i = 0.0
            total_j = 0.0
            for r in range(repeat):
                # Чтобы шум был "честным" — каждой паре своя последовательность,
                # но детерминированно зависящая от seed.
                pair_seed = _stable_seed(seed, name_i, name_j, r)
                rng = random.Random(pair_seed)
                s_i, s_j = play_match(fn_i, fn_j, rounds, noise, rng)
                total_i += s_i
                total_j += s_j
            avg_i = total_i / repeat
            avg_j = total_j / repeat
            matrix[i][j] = avg_i
            if i != j:
                matrix[j][i] = avg_j
            else:
                # self-play: матрица симметрична; в позиции (i,i) — среднее.
                matrix[i][j] = (avg_i + avg_j) / 2
    totals = [sum(matrix[i]) / n for i in range(n)]
    ranking = sorted(range(n), key=lambda i: -totals[i])
    return {
        "names": names,
        "matrix": matrix,
        "totals": totals,
        "ranking": ranking,
        "params": {
            "rounds": rounds,
            "noise": noise,
            "repeat": repeat,
            "seed": seed,
            "n_bots": n,
        },
    }


# ---------------------------------------------------------------------------
# Вывод


def format_table(result: dict) -> str:
    names = result["names"]
    matrix = result["matrix"]
    totals = result["totals"]
    ranking = result["ranking"]
    params = result["params"]
    rounds = params["rounds"]
    per_round_max = 3.0  # CC каждый раунд

    lines = []
    lines.append(
        f"Параметры: rounds={params['rounds']} noise={params['noise']} "
        f"repeat={params['repeat']} seed={params['seed']} n={params['n_bots']}"
    )
    lines.append(f"Теоретический максимум CC: {rounds * per_round_max:.0f}")
    lines.append("")
    lines.append("Рейтинг (среднее по всем матчам):")
    name_w = max(len(n) for n in names)
    for rank, idx in enumerate(ranking, 1):
        avg_per_round = totals[idx] / rounds
        lines.append(
            f"  {rank:2d}. {names[idx]:<{name_w}}  {totals[idx]:8.2f}  "
            f"({avg_per_round:.3f} / раунд)"
        )
    lines.append("")
    lines.append("Матрица счетов (строка = игрок, столбец = соперник, средний счёт):")
    header = " " * (name_w + 2) + "  ".join(f"{n[:7]:>7}" for n in names)
    lines.append(header)
    for i in range(len(names)):
        row = "  ".join(f"{matrix[i][j]:7.1f}" for j in range(len(names)))
        lines.append(f"{names[i]:<{name_w}}  {row}")
    return "\n".join(lines)


def single_match(
    path_a: str,
    path_b: str,
    rounds: int,
    noise: float,
    repeat: int,
    seed: int,
    as_json: bool,
) -> int:
    name_a, fn_a = load_bot(Path(path_a))
    name_b, fn_b = load_bot(Path(path_b))
    totals_a = []
    totals_b = []
    for r in range(repeat):
        rng = random.Random(_stable_seed(seed, name_a, name_b, r))
        s_a, s_b = play_match(fn_a, fn_b, rounds, noise, rng)
        totals_a.append(s_a)
        totals_b.append(s_b)
    avg_a = sum(totals_a) / repeat
    avg_b = sum(totals_b) / repeat
    payload = {
        "a": name_a,
        "b": name_b,
        "rounds": rounds,
        "noise": noise,
        "repeat": repeat,
        "seed": seed,
        "scores_a": totals_a,
        "scores_b": totals_b,
        "avg_a": avg_a,
        "avg_b": avg_b,
    }
    if as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"{name_a} vs {name_b} — rounds={rounds} noise={noise} repeat={repeat}")
        for r in range(repeat):
            print(f"  повтор {r+1}: {totals_a[r]} : {totals_b[r]}")
        print(f"  среднее: {avg_a:.2f} : {avg_b:.2f}")
    return 0


# ---------------------------------------------------------------------------
# CLI


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Турнир IPD")
    parser.add_argument("--rounds", type=int, default=200)
    parser.add_argument("--noise", type=float, default=0.02)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--json", action="store_true", help="JSON-вывод")
    parser.add_argument(
        "bots",
        nargs="*",
        help="Если указаны два пути bot_X.py bot_Y.py — играет один матч.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if len(args.bots) == 2:
        return single_match(
            args.bots[0],
            args.bots[1],
            args.rounds,
            args.noise,
            args.repeat,
            args.seed,
            args.json,
        )
    if args.bots:
        print("Ошибка: либо запускайте без аргументов (round-robin), "
              "либо передавайте ровно два пути к ботам.", file=sys.stderr)
        return 2
    try:
        bots = discover_bots()
    except Exception as exc:
        print(f"Ошибка загрузки ботов: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1
    if not bots:
        print(f"В {BOTS_DIR} нет ботов (файлов bot_*.py).", file=sys.stderr)
        return 1
    result = run_tournament(
        bots,
        rounds=args.rounds,
        noise=args.noise,
        repeat=args.repeat,
        seed=args.seed,
    )
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_table(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
