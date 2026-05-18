"""Soft Majority.

Cooperate whenever the opponent has cooperated at least as often as it
has defected so far. Defect only when the opponent's defection count
strictly exceeds its cooperation count.

First move is C (ties go to C; empty history is a tie 0 == 0).

Single-state strategy: there is no "lock" or mode-switch. It reacts
slowly, which gives it noise robustness — a single accidental D from
the opponent does not flip the majority unless the rest of the history
is balanced. Against AllD the count flips after round 1 and it plays D
forever from round 2 onwards. Against AllC it cooperates forever.
Self-play stays cooperative because the majority of opponent moves is
C, and the rare noise-flipped D never tips the balance for long.
"""


def choose_move(my_history: list[str], opp_history: list[str]) -> str:
    c = opp_history.count("C")
    d = opp_history.count("D")
    if c >= d:
        return "C"
    return "D"
