"""Tit-for-Tat — Anatol Rapoport's classic Axelrod winner.

Start with C. After that, copy the opponent's previous move.
"""


def choose_move(my_history, opp_history):
    if not opp_history:
        return "C"
    return opp_history[-1]
