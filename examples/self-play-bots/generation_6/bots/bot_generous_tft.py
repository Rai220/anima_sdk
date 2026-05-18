"""Generous Tit-for-Tat (Nowak & Sigmund).

Like TFT, but when the opponent defected last round, forgive with some
fixed probability. Specifically tuned for trembling-hand noise: after a
single misfire, GTFT breaks the CD/DC echo by occasionally returning to C.

Forgiveness rate 0.3 is in the band Nowak/Sigmund identified as
evolutionarily stable in noisy IPD. Lower than that and you echo too long
with TFT; higher and AllD eats you alive.
"""

import random

_FORGIVE = 0.3
_rng = random.Random(20260517)


def choose_move(my_history, opp_history):
    if not opp_history:
        return "C"
    if opp_history[-1] == "C":
        return "C"
    # Opponent defected last round. Sometimes forgive.
    if _rng.random() < _FORGIVE:
        return "C"
    return "D"
