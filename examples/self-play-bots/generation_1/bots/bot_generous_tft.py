"""Generous Tit-for-Tat (GTFT): TFT with a small forgiveness probability.

When the opponent defected last round, normally retaliate — but with
probability `FORGIVE` cooperate anyway. This breaks the echo-war that
plain TFT falls into under noise.

Nowak & Sigmund (1992) showed GTFT is evolutionarily stable in noisy
environments; the optimal forgiveness rate is roughly the noise rate.
We use 0.1 — slightly above the default noise=0.02, leaving headroom
for higher-noise experiments.
"""

import random

FORGIVE = 0.1


def choose_move(my_history, opp_history):
    if not opp_history:
        return "C"
    if opp_history[-1] == "D" and random.random() >= FORGIVE:
        return "D"
    return "C"
