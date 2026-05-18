"""Random 50/50. Pure noise baseline; should sit near the bottom in a sane
field, beating only those it can exploit (AllC) and itself."""

import random

# Use a dedicated RNG seeded once per process. Across matches within a run,
# this produces a different stream each call -- which is fine for a random
# baseline (we're not trying to be reproducible per-match).
_rng = random.Random()


def choose_move(my_history, opp_history):
    return _rng.choice(("C", "D"))
