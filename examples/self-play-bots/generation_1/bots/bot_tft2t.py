"""Tit-for-Two-Tats (TFTT): cooperate unless the opponent defected on
*both* of the last two rounds.

This is the canonical "patient" cousin of TFT. The idea: a single D from
the opponent is treated as possible noise / accident, and ignored. Two
in a row is taken as deliberate. Properties under our 2% noise model:

- *Noise-robust self-play.* A single accidental D never escalates,
  because both copies tolerate one stray D. Two consecutive flips in
  the same direction are ~0.04% per round — almost never. TFTT-vs-TFTT
  should score near 3.0.
- *Slow to retaliate against AllD.* Opens CCDDDDDD... — i.e. eats two
  S=0 rounds at the start of every AllD match (cost: ~2 per match
  amortised over 200 rounds = -0.01/round). After noise occasionally
  resets the "two D's in a row" condition, TFTT may even play another C
  by mistake against AllD, costing more.
- *Cooperates with TFT and GTFT perfectly.* Same convergence behaviour
  as those, but more forgiving when noise misfires.
- *Exploitable by clever provokers* who play D, C, D, C... — TFTT
  never sees two D's in a row and so never retaliates. This is a
  well-known weakness, but no such bot exists in our pool yet.

Reference: Axelrod (1984), "The Evolution of Cooperation", ch. 3 —
suggested TFTT might have won the second Axelrod tournament had
anyone submitted it.
"""


def choose_move(my_history, opp_history):
    if len(opp_history) < 2:
        return "C"
    if opp_history[-1] == "D" and opp_history[-2] == "D":
        return "D"
    return "C"
