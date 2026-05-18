"""Tit-for-Two-Tats (TF2T), Axelrod tournament classic.

Cooperate first. Retaliate with D only after the opponent has defected
*twice in a row*. A single isolated D — whether intentional probing or
a noise flip — is forgiven.

This is a different remedy for the noise-vendetta problem than Generous TFT:
- GTFT uses probabilistic forgiveness (random olive branch after any D).
- TF2T uses deterministic hysteresis (one D is free, two in a row trigger).

Expected behaviour in this field:

* vs TF2T (self): a single noise flip never escalates (the other side
  needs two D's to retaliate; we don't supply the second). Should be
  near the 600 ceiling.
* vs TFT under noise: better than TFT-vs-TFT. When TFT misfires once
  (noise), TF2T forgives, TFT sees C, returns to C. No vendetta.
* vs AllD: pays 2 sucker payoffs (rounds 1 and 2) at S=0, then locks
  into mutual D from round 3 onwards. Total ≈ 0+0 + 1·198 = 198,
  about 12 points worse than TFT (which only pays 1 sucker round).
* vs Pavlov: Pavlov occasionally plays D after a noise-induced loss.
  TF2T forgives the first D; Pavlov, having got a T or already in the
  shift cycle, often comes back to C. Cleaner interaction than TFT.
* vs Grim: indistinguishable from TFT here — once Grim locks to D, TF2T
  will see two D's in a row and lock to D too.

Exploit surface: a "DCDCDC…" alternator gets a free 5/round forever
because no two D's ever line up. None of the current bots do that,
but it's worth noting as a vulnerability.
"""


def choose_move(my_history, opp_history):
    if len(opp_history) < 2:
        return "C"
    if opp_history[-1] == "D" and opp_history[-2] == "D":
        return "D"
    return "C"
