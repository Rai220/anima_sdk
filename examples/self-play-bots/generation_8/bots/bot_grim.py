"""Grim Trigger — cooperate until opponent defects once, then defect forever."""


def choose_move(my_history, opp_history):
    if "D" in opp_history:
        return "D"
    return "C"
