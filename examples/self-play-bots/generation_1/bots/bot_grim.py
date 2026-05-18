"""Grim Trigger: cooperate until opponent defects once, then defect forever.

Unforgiving. Devastating against pure defectors, but in a noisy world a
single accidental D from a friendly opponent permanently destroys the
relationship.
"""


def choose_move(my_history, opp_history):
    if "D" in opp_history:
        return "D"
    return "C"
