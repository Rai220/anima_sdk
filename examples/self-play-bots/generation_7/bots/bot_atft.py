"""Adaptive Tit For Tat: TFT + sliding-window defector detector.

The motivation comes from Lesson 008: forgiveness/cooperation against
a *locked* defector is pure loss. Plain TFT mirrors AllD into a DD
floor, which is the best one-shot response, but it still wastes a
first-round C and gets pulled into single-round C responses every
time the opponent's D gets noise-flipped to C. A bot that has
identified the opponent as "structurally hostile" should stop
mirroring noise and just stay D.

Rules.

- Round 1: cooperate (we cannot know yet whether the opponent is
  hostile).
- From round 6 onward: compute the opponent's cooperation rate over
  the last `WINDOW` rounds (using whatever portion of history is
  available). If that rate falls below `THRESHOLD`, play D. This
  switch is non-sticky — if the opponent's coop rate climbs back
  above the threshold, we resume TFT.
- Otherwise: mirror the opponent's last move (TFT).

Design choices.

- `WINDOW = 20`, `THRESHOLD = 0.20`. A noise=0.02 environment makes
  even a fully cooperating opponent miss ~2% of intended C's. TFT-
  vs-TFT noise ringing pushes coop rate down further but typically
  stays well above 0.5 in self-play. Threshold 0.20 leaves a wide
  safety margin and triggers reliably against AllD-style opponents
  whose coop rate sits near 2% (their forced noise C's).
- `min_history = 5`. Without this floor, a single early D from the
  opponent (e.g. round-1 noise flip) would push coop_rate to 0/1 =
  0 and we'd defect at round 2. The 5-round floor costs us up to
  4 rounds against AllD (vs full TFT mirror would also waste those
  rounds in slightly different ways) but stops false-positive
  triggers against well-behaved opponents that happen to take a
  noise hit early.
- Non-sticky switch. If the opponent recovers (e.g. Grim's locked
  D is rare in practice; cooperative bots reliably return to C),
  we want to return to mirroring rather than locking into our own
  D forever. This is the difference vs. a hypothetical "Trigger
  TFT" that, once it has decided the opp is hostile, plays D until
  the end.

Predicted behaviour.

- vs AllC: TFT mirror, score ~ noise-affected CC.
- vs AllD: round-1 wasted C, rounds 2-5 TFT-mirror D, from round 6
  onward locked D. Should match or slightly beat plain TFT vs AllD
  (~210) by avoiding occasional noise-driven C responses.
- vs Grim that has locked D: after the lock, coop rate from Grim
  drops to near 0 within `WINDOW` rounds, we switch to permanent D
  and stop responding to Grim's noise-flipped C's. Should beat
  plain TFT vs Grim (272.3).
- vs TFT-family (TFT, TF2T, GTFT, CTFT): coop rate stays high
  even under noise; ATFT behaves like TFT. Should match those
  cells.
- Self-play: identical to TFT-self-play under noise (~498.7).
  No improvement here. Adaptive TFT is *not* a noise-recovery
  strategy; it is a defector-detection strategy.
"""

WINDOW = 20
THRESHOLD = 0.20
MIN_HISTORY = 5


def choose_move(my_history, opp_history):
    if not opp_history:
        return "C"
    if len(opp_history) >= MIN_HISTORY:
        recent = opp_history[-WINDOW:]
        coop_rate = recent.count("C") / len(recent)
        if coop_rate < THRESHOLD:
            return "D"
    return opp_history[-1]
