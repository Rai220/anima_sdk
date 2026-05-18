"""Grim Trigger: cooperate until opponent defects once, then
defect forever.

Fragile under noise: one accidental flip locks both into DD.
"""


def choose_move(my_history, opp_history):
    if "D" in opp_history:
        return "D"
    return "C"
