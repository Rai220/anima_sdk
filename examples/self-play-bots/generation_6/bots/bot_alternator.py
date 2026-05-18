"""Alternator: deterministic DCDCDC... starting with D.

Motivation. Multiple runs flagged this as the most important missing
adversary in the pool. It is the cleanest stress-test of two leaders:

1. TF2T forgives any single D that is not immediately followed by
   another D. A pure DCDC pattern never produces two D's in a row, so
   TF2T should keep cooperating forever and harvest the alternator's
   payoff: rounds look like (D vs C) and (C vs C), giving the alternator
   roughly 5 + 3 = 8 per two rounds (avg 4.0/round) and TF2T 0 + 3 = 3
   per two rounds (avg 1.5/round). That would be a huge win for the
   alternator vs TF2T -- well above the CC line.

2. adaptive_tft uses an all-time coop-rate threshold of 0.45. A pure
   DCDC alternator has coop rate ~0.5, just above the threshold, so the
   AllD-detector would never trigger. The bot would stay in TF2T-mode
   and get exploited the same way TF2T does. That would falsify
   adaptive_tft's main edge.

Against other strategies:

- vs AllC: alternator takes T=5 every other round, R=3 the rest -> 4.0/round.
- vs AllD: bleeds because every C it plays earns 0 against D. ~2.5/round
  (one D-D = 1, one C-D = 0). Actually that's 0.5/round, awful.
- vs TFT: TFT mirrors. After alternator's first D, TFT plays D in round
  2 (while alternator plays C). Then in round 3 TFT plays C (copying
  alternator's prev C) while alternator plays D. So they end up in
  perfect anti-phase: alternator gets 5+0+5+0=... = 2.5/round. TFT
  also gets 2.5/round (mirror). Neither wins.
- vs Grim: alternator's first move is D, Grim locks D forever. Then
  alternator's odd rounds are D (DD floor = 1), even rounds are C (CD
  = 0). Avg 0.5/round. Worst case.
- vs Pavlov: harder to predict; Pavlov's WSLS interpretation of T=5
  (when it plays D vs alternator's C) keeps it on D. Should be ugly
  for the alternator.
- vs adaptive_tft: see motivation -- should exploit ~3.5+/round if
  the 0.45 lock never trips.

Hypothesis. Alternator will beat TF2T and adaptive_tft head-to-head
but lose its overall ranking, because most of the cooperator block
(Grim, AllD, Pavlov) crush it.

If this hypothesis holds it provides the clearest case yet for why
"detection by long-window rate" is insufficient: you need either a
**recent-window** detector (DCDC keeps recent rate at 0.5 too, so a
recent-window detector alone won't help) or a **pattern detector**
that recognises repeating short cycles. Future bots can build that.
"""


def choose_move(my_history, opp_history):
    # Pure deterministic alternator: D on even rounds, C on odd rounds.
    # Round index = len(my_history) (0-based). Round 0 -> D, round 1 -> C, ...
    n = len(my_history)
    return "D" if n % 2 == 0 else "C"
