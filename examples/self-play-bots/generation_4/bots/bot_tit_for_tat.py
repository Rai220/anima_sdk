"""Tit for Tat (Аксельрод 1980).

Первый ход — C. Дальше копирует последний ход соперника. Классическая
nice + retaliatory + forgiving (одношаговое прощение) + non-envious.

В шумной среде имеет известную слабость: один шумовой D любого из
участников запускает каскад взаимных наказаний.
"""


def choose_move(my_history, opp_history):
    if not opp_history:
        return "C"
    return opp_history[-1]
