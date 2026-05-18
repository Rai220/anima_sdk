"""Tit-for-Two-Tats (Axelrod's "even nicer" variant).

Cooperate by default. Defect only after the opponent has defected in
*both* of the last two rounds. A single defection -- noise-induced or
not -- is forgiven; two in a row are treated as evidence of real
hostility and punished with a D until the opponent comes back to C.

Why this should help vs Run 002 GTFT problem (147 vs AllD):

- TF2T forgives only the FIRST D from AllD. From round 2 onward it
  locks into D (every pair of opp moves is DD), so it floors at the
  DD payoff (~200) instead of leaking 5s to AllD like GTFT.
- Against TFT/GTFT/itself it tolerates single-misfire noise without
  starting a CD/DC echo, which is the main lift over plain TFT.

Tradeoff: TF2T is exploitable by a "DCDCDC" alternator -- it will keep
cooperating because no two defections are adjacent. We don't have such
an adversary yet, but it's a known weakness worth tracking.
"""


def choose_move(my_history, opp_history):
    if len(opp_history) < 2:
        return "C"
    if opp_history[-1] == "D" and opp_history[-2] == "D":
        return "D"
    return "C"
