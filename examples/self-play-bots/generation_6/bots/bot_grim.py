"""Grim Trigger. Cooperate until opponent defects once -- then D forever.

Maximally unforgiving. Punishes a single transgression eternally, which
makes it terrible under noise: one stray flip locks in mutual DD.
"""


def choose_move(my_history, opp_history):
    if "D" in opp_history:
        return "D"
    return "C"
