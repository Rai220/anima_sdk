"""Pavlov / Win-Stay-Lose-Shift (Nowak & Sigmund, 1993).

The rule, stated by payoff: if last round's payoff was R (3) or T (5),
keep last move; if it was S (0) or P (1), switch. Equivalently, by the
last (my, opp) pair:

    (C, C) -> repeat C   ("we cooperated, it worked, keep going")
    (D, C) -> repeat D   ("I exploited, it paid, keep exploiting")
    (C, D) -> switch  D  ("I was a sucker, stop being one")
    (D, D) -> switch  C  ("mutual punishment is bad, try cooperating")

Two things make Pavlov interesting for this experiment:

1. Noise recovery is fast. If a CC pair gets noise-flipped to CD or DC,
   Pavlov returns to mutual CC within 2-3 rounds, while TFT can spin in
   a long CD/DC echo. So Pavlov should outscore TFT in self-play under
   noise.

2. Pavlov is BAD against AllD. After one D from the opponent it switches
   to D; the next DD makes it switch back to C; AllD then exploits the
   C; Pavlov switches to D... resulting in a CDCDCD oscillation that
   averages ~0.5/round, well below the DD floor of 1.0. This is a known
   weakness and we expect to see it in the matrix.

So Pavlov is a "good among cooperators, bad against pure exploiters"
strategy -- the mirror of GTFT's pattern. Comparing them tells us
whether the population is currently leaning cooperator (Pavlov wins)
or exploiter (Pavlov bleeds).

First move: C (act nice, per Axelrod's principle 1).
"""


def choose_move(my_history, opp_history):
    if not my_history:
        return "C"
    last_mine = my_history[-1]
    last_opp = opp_history[-1]
    # "Win" = got R or T, i.e. opponent played C.
    won = last_opp == "C"
    if won:
        return last_mine
    # "Lose" = got S or P, i.e. opponent played D. Switch.
    return "D" if last_mine == "C" else "C"
