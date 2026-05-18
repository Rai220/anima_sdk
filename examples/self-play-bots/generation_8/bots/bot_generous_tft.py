"""Generous Tit-for-Tat (Nowak & Sigmund, 1992).

Like Tit-for-Tat, but after the opponent defected we still cooperate with a
small probability `FORGIVE_P`. This breaks the "vendetta" loop that TFT-vs-TFT
falls into under noise: a single accidental D triggers permanent alternating
CD/DC at 2.5 points/round; one forgiveness from either side resets the match
back to mutual cooperation at 3 points/round.

The textbook closed-form for the optimal forgiveness probability is
    p* = min(1 - (T-R)/(R-S), (R-P)/(T-P)) = min(1/3, 1/2) = 1/3
for the standard 0/1/3/5 payoff. At 1/3, a one-step noise vendetta is expected
to last 3 rounds, which is short enough to keep CC the dominant regime, yet
not so generous that AllD exploits us for free every round.

We use p = 1/3 from the literature. The trade-off vs plain TFT:
+ much better self-play and TFT-play under noise (no permanent vendetta);
+ better vs other reciprocators (Grim still won't forgive us, but we forgive
  Grim);
- slightly more exploitable by AllD: we hand out a free C every ~3 rounds
  instead of mirroring D forever. Expected loss vs AllD = 1/3 of (S-P) per
  round ≈ -1/3 point/round compared to TFT.
"""
import random

FORGIVE_P = 1.0 / 3.0


def choose_move(my_history, opp_history):
    if not opp_history:
        return "C"
    last_opp = opp_history[-1]
    if last_opp == "C":
        return "C"
    # Opponent defected last round. Forgive with probability FORGIVE_P,
    # otherwise retaliate.
    if random.random() < FORGIVE_P:
        return "C"
    return "D"
