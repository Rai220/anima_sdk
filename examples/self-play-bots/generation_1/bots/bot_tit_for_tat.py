"""Tit-for-Tat: cooperate first, then copy opponent's last move.

Axelrod's classical winner in noise-free tournaments. Nice (never defects
first), retaliatory (punishes a D immediately), forgiving (one D for one D,
then back to C), and clear.
"""


def choose_move(my_history, opp_history):
    if not opp_history:
        return "C"
    return opp_history[-1]
