"""Pavlov / Win-Stay-Lose-Shift (Nowak & Sigmund 1993).

Rule: cooperate on round 1. Thereafter look at last round's payoff:
- Won (R=3 or T=5)  -> repeat last move.
- Lost (P=1 or S=0) -> flip last move.

Equivalently: play C iff (my last move == opp last move).
- CC  -> next C  (R: stay)
- DD  -> next C  (P: shift)
- DC  -> next D  (T: stay)
- CD  -> next D  (S: shift)

Known traits:
- Recovers from mutual defection via the (D,D) -> C shift, so self-
  play under noise re-cooperates after a few rounds.
- Exploits AllC: a noise flip of own C -> D lands in (D,C) which is
  T=win, so Pavlov KEEPS defecting against a cooperator forever.
  This is the same "accidental exploiter" pattern as Grim, but
  arrived at via payoffs rather than mirroring.
- Beats TFT slightly in noise: each noise flip costs TFT a
  CD-DC ringing cycle; Pavlov resolves the same flip in 1-2 moves
  via the shift rule.
"""


def choose_move(my_history, opp_history):
    if not my_history:
        return "C"
    return "C" if my_history[-1] == opp_history[-1] else "D"
