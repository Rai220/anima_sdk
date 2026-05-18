"""Contrite Tit For Tat (Boyd 1989; Wu & Axelrod 1995).

Like TFT but tracks a "standing" (good/bad) for both players. The
goal is to break the CD-DC ringing that TFT suffers under noise,
without opening the door to exploitation (the way TF2T and GTFT do).

Rules.

Both players start in good standing (G). After every round we
update standings based on what was actually played:

- I played C  -> my new standing = G.
- I played D against a B-standing opponent -> G (legitimate
  retaliation).
- I played D against a G-standing opponent -> B (unprovoked, i.e.
  noise from my side, since CTFT itself never *intends* an
  unprovoked D).

Opponent's standing updates symmetrically based on what they played
and what my pre-round standing was.

Decision rule at the start of a new round:

- If opp_std == B and my_std == G: play D (retaliate against a
  genuinely bad-standing opponent).
- Otherwise: play C (cooperate, or apologise if my own standing
  has been knocked down to B by a noise event).

This closes the "tolerance tax" leak (Lesson 004): when MY C gets
noise-flipped to D, I play C next round even after the opponent's
retaliation, so the ring CD-DC-CC ends in 3 rounds instead of
oscillating indefinitely. It does NOT, however, fix the symmetric
case where the OPPONENT's C is noise-flipped to D — CTFT still
retaliates there, and against a non-contrite TFT this triggers the
usual TFT-vs-TFT ring. Fixing that would require opponent-side
forgiveness, which is the GTFT / TF2T direction with its own costs.

Against AllD, CTFT plays D from round 2 onward (same as TFT). Against
AllC, CTFT plays C indefinitely except for transient retaliation
after a noise flip on AllC's side (one-round retaliation, then
restored). It does NOT systematically exploit AllC the way Grim or
Pavlov do.
"""


def choose_move(my_history, opp_history):
    if not opp_history:
        return "C"
    my_std = "G"
    opp_std = "G"
    for i in range(len(my_history)):
        m = my_history[i]
        o = opp_history[i]
        new_my = "G" if m == "C" else ("G" if opp_std == "B" else "B")
        new_opp = "G" if o == "C" else ("G" if my_std == "B" else "B")
        my_std, opp_std = new_my, new_opp
    if opp_std == "B" and my_std == "G":
        return "D"
    return "C"
