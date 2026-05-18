"""Tit for Tat — классика Аксельрода.

Первый ход — C. Дальше копируем последний ход соперника.
"""


def choose_move(my_history, opp_history):
    if not opp_history:
        return "C"
    return opp_history[-1]
