"""Random: cooperate or defect with equal probability.

Uses the global `random` module — `tournament.py` seeds it at startup so
results are reproducible for a fixed `--seed`.
"""

import random


def choose_move(my_history, opp_history):
    return "C" if random.random() < 0.5 else "D"
