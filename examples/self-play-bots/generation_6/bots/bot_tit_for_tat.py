"""Tit-for-Tat. Cooperate first, then mirror opponent's last move.

Anatol Rapoport's winner of Axelrod's tournaments. Nice, retaliatory,
forgiving (one-step), clear. Vulnerable to noise: a single misfire kicks
off a CD/DC echo with another TFT.
"""


def choose_move(my_history, opp_history):
    if not opp_history:
        return "C"
    return opp_history[-1]
