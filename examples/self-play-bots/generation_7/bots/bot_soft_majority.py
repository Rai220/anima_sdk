"""Soft Majority: cooperate when opponent has cooperated at least as
much as defected; defect when opponent's D-count strictly exceeds
their C-count over the entire observed history.

First move = C (a tie at 0-0 counts as "at least as many C's").

Compared to TFT, this is a *bulk-statistics* rule with very slow
trigger: a single noise-flipped D doesn't move the inequality (one D
vs many C's still satisfies C >= D). Compared to AllC, it is not
exploitable indefinitely — against AllD the D-count quickly outweighs
C-count and Soft Majority switches to permanent D.

Predicted behaviour:
- vs AllC, TFT, reciprocators: stable mutual CC (noise rarely flips
  the running tally).
- vs AllD: cooperates for the FIRST round (sucker payoff), then
  D-count = 1 > C-count = 0, switches to D forever. So vs AllD it
  gives up exactly 1 sucker (0 points) and then plays DD (1 point
  each round) — roughly TFT-like in that column.
- vs Random: opponent's expected D-rate = 0.5 + noise effect on us;
  cumulative tally hovers near zero, so Soft Majority will flip-flop
  based on which side the tally lands on. Expect mid-range cell.
- self-play: starts CC, stays CC; noise events resolve themselves
  because both sides keep majority-C tallies.
"""


def choose_move(my_history, opp_history):
    if not opp_history:
        return "C"
    c_count = opp_history.count("C")
    d_count = len(opp_history) - c_count
    if d_count > c_count:
        return "D"
    return "C"
