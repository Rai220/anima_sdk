"""Pavlov / Win-Stay-Lose-Shift (WSLS).

Rule: open with C; after each round, keep the same move if the outcome
was "good" (R=3 or T=5), switch otherwise (P=1 or S=0).

Equivalently, derived from the payoff table:

    last (mine, opp) -> next move
    (C, C): R=3, win  -> stay  -> C
    (D, C): T=5, win  -> stay  -> D
    (C, D): S=0, lose -> shift -> D
    (D, D): P=1, lose -> shift -> C

Notable properties:

- *Self-correcting under noise.* After an accidental DD round, Pavlov
  shifts to C, re-syncing cooperation in one step. TFT echoes the D
  forever (until another flip resyncs them); Pavlov does not.
- *Exploits AllC after a slip.* Against a pure pushover Pavlov locks
  cooperation, but as soon as a noise flip makes opp look like a
  defector once, Pavlov enjoys a free DC round before the cycle
  returns. Against AllC specifically the steady-state is CC.
- *Vulnerable to AllD.* Pavlov plays C, gets 0, shifts to D, gets 1,
  shifts back to C — an alternating CDCD pattern that scores ~0.5 per
  round on average. Worse than TFT here.

Reference: Nowak & Sigmund, "A strategy of win-stay, lose-shift that
outperforms tit-for-tat in the Prisoner's Dilemma game" (Nature, 1993).
"""


def choose_move(my_history, opp_history):
    if not my_history:
        return "C"
    last_mine = my_history[-1]
    last_opp = opp_history[-1]
    # Win (R or T): stay. Loss (S or P): shift.
    if last_mine == "C" and last_opp == "C":
        return "C"  # R=3, stay on C
    if last_mine == "D" and last_opp == "C":
        return "D"  # T=5, stay on D
    if last_mine == "C" and last_opp == "D":
        return "D"  # S=0, shift to D
    return "C"  # (D, D) -> P=1, shift to C
