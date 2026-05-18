"""Random 50/50 cooperator/defector.

Uses a fresh Random instance per call (no global state). Seed
derived from histories so behaviour is reproducible across
identical replays but uncorrelated across rounds.
"""

import random


def choose_move(my_history, opp_history):
    seed = f"random|{''.join(my_history)}|{''.join(opp_history)}"
    rng = random.Random(seed)
    return "C" if rng.random() < 0.5 else "D"
