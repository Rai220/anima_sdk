"""Grim Trigger — пока соперник кооперирует, играем C.

После первого же его D — навсегда D. «Один раз обманул — больше веры нет.»
"""


def choose_move(my_history, opp_history):
    if "D" in opp_history:
        return "D"
    return "C"
