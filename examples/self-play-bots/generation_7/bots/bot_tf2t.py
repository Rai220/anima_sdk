"""Tit for Two Tats: cooperate unless opponent has defected in the
LAST TWO consecutive rounds.

Absorbs single noise flips. The classic noise-tolerant TFT.
Weakness: a structured 2-period defector can exploit the "one
free defection" margin (cf. alternator CDCDCD).
"""


def choose_move(my_history, opp_history):
    if len(opp_history) >= 2 and opp_history[-1] == "D" and opp_history[-2] == "D":
        return "D"
    return "C"
