"""Cycle-detector: TF2T + adaptive-rate + period-2 cycle lock.

Motivation. Run 006 added bot_alternator (DCDCDC...) which beat both
TF2T and adaptive_tft head-to-head by ~770 vs ~310 (a 460-point
asymmetry). The reason was structural: TF2T's "punish only two D's in
a row" rule never triggers on DCDC (no two D's adjacent), and
adaptive_tft's "lock if all-time coop rate < 0.45" never triggers
either (DCDC keeps the rate exactly at 0.5). Both tolerance rules
silently assume opponent defections are IID-noise events. Once they
are *structured*, both rules leak.

Fix idea. Add a third detection layer that catches *short cycles*
(period 2 in particular). Then the bot has:

1. Short-term tactical: TF2T (forgive one D, punish two in a row).
2. Long-term diagnostic: lock D if all-time coop rate < LOCK_RATE
   after a WARMUP (handles AllD).
3. Structural diagnostic: lock D if the recent observed history shows
   a strong period-2 alternating pattern (handles DCDC alternator and
   any near-alternator).

Each layer fires on a different time-scale and pattern shape, so a
single adversary can't game more than one at once.

Cycle detection rule. After at least CYCLE_WINDOW observations, look
at the last CYCLE_WINDOW moves in opp_history. Count consecutive-pair
differences: pairs (opp[-i], opp[-i-1]) for i = 1..CYCLE_WINDOW-1.
If at least CYCLE_HITS of those CYCLE_WINDOW-1 pairs are different
(opposite moves), we declare a period-2 cycle and lock D for good.

Parameters (set by reasoning, not tuned per opponent):

- CYCLE_WINDOW = 10. Long enough that one or two noise flips don't
  trip the detector. Short enough that an alternator pattern is
  visible within a fraction of a 200-round match.
- CYCLE_HITS = 7. Out of 9 possible adjacent-pair differences in a
  window of 10. A pure DCDC pattern with 2% noise gives ~8.8/9
  expected hits; CC/CC/CC steady-state gives 0; Random gives ~4.5;
  TFT-vs-TFT under noise gives <2 once they settle. The threshold
  is well-separated from all non-cyclic regimes.
- WARMUP = 8, LOCK_RATE = 0.45: copied from adaptive_tft. Handles
  the AllD case without snagging Random.

Expected behavior:

- vs bot_alternator: by round 10-12 the cycle detector trips,
  locks D for the remaining ~190 rounds. Alternator plays D/C/D/C;
  we play D every round. Score expectation:
    - alt-D vs us-D = (1, 1) on odd rounds: avg 1 for us
    - alt-C vs us-D = (5, 0) on even rounds: avg 5 for us
    - Average ~3.0/round once locked, ~600 over the locked portion.
  Total expected ~580-600, up from TF2T's 307.7 in run 006.
- vs AllD: long-term rate detector trips by round 8, lock D, same as
  adaptive_tft (~211 against AllD).
- vs TFT-family (TFT, TF2T, GTFT, adaptive_tft, self): under 2%
  noise, opp_history is mostly steady-state CC with occasional
  isolated flips. Adjacent-pair differences are <2/9 most windows,
  so cycle detector never fires. Behavior reduces to TF2T -> CC-line
  ~590.
- vs Random: ~50% coop rate (above LOCK_RATE), ~50% adjacent-pair
  difference (below CYCLE_HITS threshold of 7/9). Neither detector
  trips reliably; falls back to TF2T behavior.
- vs Pavlov: Pavlov's noise-induced D-streaks are not periodic, just
  bursty. Coop rate may dip but typically stays >0.45. Cycle detector
  unlikely to trip on Pavlov bursts. Behavior should be TF2T-like.
- vs Grim: identical first-move C, mutual CC until a noise event makes
  Grim lock D. Then opp is permanent D -> rate drops -> rate lock
  trips by ~8 rounds after Grim's switch. Same handling as AllD.

Tradeoff. The cycle detector still has a decision boundary -- it
could be probed by an opponent that plays DDCDDCDDC (period-3
two-D-one-C). Such an opponent has only 6/9 expected adjacent
differences (DDC has DD same, DC diff, so 2/3 differences per
period). The detector wouldn't fire. Future work: also check period-3
auto-correlation, or use a more general spectral test. For now we
handle the most common case (period 2) which is the alternator family.
"""

CYCLE_WINDOW = 10
CYCLE_HITS = 7
WARMUP = 8
LOCK_RATE = 0.45


def _period2_cycle(opp_history):
    """Return True if last CYCLE_WINDOW moves show a strong period-2 cycle."""
    n = len(opp_history)
    if n < CYCLE_WINDOW:
        return False
    window = opp_history[-CYCLE_WINDOW:]
    diffs = sum(1 for i in range(1, CYCLE_WINDOW) if window[i] != window[i - 1])
    return diffs >= CYCLE_HITS


def choose_move(my_history, opp_history):
    n = len(opp_history)
    if n == 0:
        return "C"

    # Layer 3: period-2 cycle lock. Check first because once tripped, it's
    # the most decisive signal in the field.
    if _period2_cycle(opp_history):
        return "D"

    # Layer 2: all-time coop-rate lock (handles AllD, post-noise Grim, etc).
    if n >= WARMUP:
        coop_rate = opp_history.count("C") / n
        if coop_rate < LOCK_RATE:
            return "D"

    # Layer 1: TF2T tactical rule.
    if n < 2:
        return "C"
    if opp_history[-1] == "D" and opp_history[-2] == "D":
        return "D"
    return "C"
