"""Generous Tit for Tat (Nowak & Sigmund, 1992).

Same as TFT, but after observing opponent's D, forgive (play C) with
probability g = 1/3 instead of always retaliating.

Why g = 1/3? For the canonical payoff (T=5, R=3, P=1, S=0):

    g* = min(1 - (T - R) / (R - S),  (R - P) / (T - P))
       = min(1 - 2 / 3,              2 / 4)
       = min(1/3, 1/2)
       = 1/3.

Below g* GTFT is too unforgiving (loses self-play noise recovery);
above g* it is too soft (leaks to exploiters). 1/3 is the Pareto-
frontier sweet spot against TFT-family opponents under noise.

Reproducibility: seeded with history string per Lesson 001.
"""

import random

FORGIVE_PROB = 1.0 / 3.0


def choose_move(my_history, opp_history):
    if not opp_history:
        return "C"
    if opp_history[-1] == "C":
        return "C"
    # Opponent's last move was D. Forgive with probability g.
    seed = f"gtft|{''.join(my_history)}|{''.join(opp_history)}"
    rng = random.Random(seed)
    return "C" if rng.random() < FORGIVE_PROB else "D"
