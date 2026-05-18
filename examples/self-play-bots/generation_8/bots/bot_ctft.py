"""Contrite Tit-for-Tat (Wu & Axelrod 1995, "How to Cope with Noise").

Idea: in noisy IPD, TFT-vs-TFT collapses into long alternating-CD vendettas
after a single noise flip. Contrite TFT tracks the *standing* of each
player to distinguish "unprovoked defection" (retaliate) from "justified
retaliation against my own prior defection" (forgive, accept punishment).

Standings are computed from the publicly visible history of actual moves:

  player has GOOD standing initially.
  After each round:
    my_new_standing  = BAD  iff  I played D against opp's GOOD pre-standing
                       GOOD otherwise.
    opp_new_standing = BAD  iff  opp played D against my GOOD pre-standing
                       GOOD otherwise.

  Decision: play D iff opp ends the latest round in BAD standing; else C.

Behaviour summary:
- vs cooperators: pure C (~3 per round).
- vs AllD: retaliates from round 2 onward (~1 per round).
- vs TFT/CTFT/etc with a single noise flip: 2 disruption rounds (one sucker
  per side, then back to mutual C). Compare TFT-vs-TFT which alternates
  CD/DC indefinitely after one flip.
- vs Prober (D, C, C, ...): retaliates D in round 2 (opp is in BAD standing
  after their unprovoked R1 D), opp returns to C, both cleared to GOOD,
  mutual C from R3 onward. Passes the sucker test.

This is a canonical "nice / retaliatory / forgiving / non-envious" strategy
(Axelrod 1984) with a precise rule for *who deserves forgiveness*.
"""


def choose_move(my_history, opp_history):
    if not my_history:
        return "C"

    my_standing = "good"
    opp_standing = "good"
    for t in range(len(my_history)):
        m_pre = my_standing
        o_pre = opp_standing
        m = my_history[t]
        o = opp_history[t]
        my_standing = "bad" if (m == "D" and o_pre == "good") else "good"
        opp_standing = "bad" if (o == "D" and m_pre == "good") else "good"

    return "D" if opp_standing == "bad" else "C"
