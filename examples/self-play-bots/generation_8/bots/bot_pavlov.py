"""Pavlov — Win-Stay, Lose-Shift (Nowak & Sigmund, 1993).

First move: C. After each round, repeat my last move if the payoff was
"good" (T=5 or R=3, i.e. opponent played C), otherwise switch.

Equivalently: cooperate iff we agreed last round (both C or both D).
This self-corrects after a single noise flip (DD turns back into CC
within one round when both sides are Pavlov), which is why Pavlov is
known to dominate noisy tournaments.
"""


def choose_move(my_history, opp_history):
    if not my_history:
        return "C"
    # Win-stay if last round payoff was T or R (opponent cooperated);
    # lose-shift if last round payoff was S or P (opponent defected).
    last_mine = my_history[-1]
    last_opp = opp_history[-1]
    if last_opp == "C":
        return last_mine  # win, stay
    # opp defected -> we lost (or tied at P) -> shift
    return "D" if last_mine == "C" else "C"
