"""Contrite Tit-for-Tat (Wu & Axelrod 1995 / Boyd 1989 / Sugden 1986).

TFT, but with apology. The bot tracks its INTENDED moves separately from the
observed (post-noise) moves the world recorded. If on either of the last two
rounds the bot intended C but the world saw D (a noise flip), it plays C
this round regardless of opp's behaviour. This is the "apology window" —
it expects opp to retaliate for the misfire and pre-emptively de-escalates.

Concretely, on each round i:

  - i == 0: play C.
  - Else, default to TFT (mirror opp's last observed move).
  - Exception ("apology"): if in any of rounds {i-2, i-1} the bot's INTENDED
    move was C but my_history showed D, play C instead.

Stateless implementation: the bot's logic is deterministic given the
(my_history, opp_history) pair so far, so we reconstruct what we INTENDED
on every past round by replaying the rule iteratively from round 0.

Why a 2-round window?

  - 1-round (apologise immediately): pointless. The round AFTER my flip, opp
    hasn't yet seen the flip (they choose simultaneously). They'll play
    whatever they would have played anyway. My apology = my normal TFT
    response since they didn't defect yet.
  - 2-round (apologise on the round opp's retaliation lands): correct. The
    round AFTER opp retaliates, I see opp's D; TFT would punish; but the
    noise flip is still in the window, so I apologise instead. Mutual
    cooperation restored after exactly 1 wasted CD round.

Predicted behaviour (vs Run 010 baselines):

  - CTFT vs CTFT under 2% noise: ~580+ (close to CC ceiling 600). TFT-self
    in Run 010 = 444. Predicted lift: ~135 points.
  - CTFT vs TFT: probably similar to TFT-vs-TFT (~444). The apology only
    helps when *both* players forgive; against pure TFT, my apology fixes
    the loop unilaterally — opp still retaliates on the round AFTER my
    flip, but I apologise on the round AFTER THAT, restoring the loop.
    Actually this asymmetric case should improve since I unilaterally
    break out faster. Predicted ~470-500.
  - CTFT vs GTFT: similar to TFT-vs-GTFT (~588 for TFT, GTFT forgives
    randomly). Predicted ~580.
  - CTFT vs handshake: handshake plays 2 D's then TFT. I TFT-mirror,
    landing in DD lock. Apology shouldn't fire (I never intend C while
    opp is playing D in early rounds). Predicted ~409 like TFT.
  - CTFT vs AllD: pure DD. Apology never fires (I never intend C after
    R1). Predicted ~200 like TFT.

The principal hypothesis: a smart-forgiveness rule that only forgives noise
attributable to oneself outperforms blanket forgiveness (GTFT) AND vanilla
TFT, by being firm against intentional defectors but soft against noise.
"""


def _decide(intended_so_far, my_history, opp_history, i):
    """Compute what the bot intends on round i, using only past rounds < i."""
    if i == 0:
        return "C"
    # Apology window: was there a noise flip in rounds i-2 or i-1?
    for k in (i - 2, i - 1):
        if k < 0:
            continue
        if intended_so_far[k] == "C" and my_history[k] == "D":
            return "C"
    # Default: TFT — mirror opp's last observed move.
    return opp_history[i - 1]


def choose_move(my_history, opp_history):
    n = len(my_history)
    if n == 0:
        return "C"
    # Reconstruct intended-move history by replaying the rule.
    intended = []
    for i in range(n):
        intended.append(_decide(intended, my_history, opp_history, i))
    # Decide round n.
    return _decide(intended, my_history, opp_history, n)
