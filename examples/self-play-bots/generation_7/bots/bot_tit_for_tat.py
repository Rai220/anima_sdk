"""Tit for Tat: C on round 1, then mirror opponent's last move.

Axelrod's tournament winner (1980). The minimal "nice + retaliate
+ forgive + non-envious" strategy.
"""


def choose_move(my_history, opp_history):
    if not opp_history:
        return "C"
    return opp_history[-1]
