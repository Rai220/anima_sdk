"""Gradual (Beaufils, Delahaye, Mathieu 1996): escalating retaliation.

Motivation. The current field has two reciprocators that perform well
against most opponents but each has a structural blind spot:

- TF2T forgives any single D and gets exploited by the alternator.
- Grim never forgives anything and bleeds out under 2% noise (mutual
  Grim collapses to DD-floor after the first noise flip).

Gradual sits between them on the punish-vs-forgive axis but with a
twist: punishment *escalates* with the opponent's cumulative defection
count. The exact rule (Beaufils 1996):

1. Cooperate by default.
2. If opponent has just defected AND we are not already in a
   punishment-cooling sequence, start one: play D for `total_D` rounds
   (where total_D is the cumulative count of opponent defections so
   far, INCLUDING the one that just triggered), then play C for 2
   "cooling" rounds.
3. While inside a punishment-cooling sequence, finish it; ignore new
   defections (they will be counted toward the NEXT trigger after the
   sequence completes).

Why this should work in the current field.

- vs AllC: never defects. We never trigger. Behavior = AllC partner
  -> CC line ~590 (noise-degraded R).
- vs AllD: trigger on round 0. Punishment lengths grow rapidly:
  1 D (cumulative=1) -> 2 C cool -> see another D, cumulative=4, 4 D
  -> 2 C, ... -> very quickly we're in near-permanent D mode. Slight
  inefficiency over pure Grim because of the 2 cooling C's each cycle,
  but bounded: the cooling cost is 2*0=0 per cycle, and the cycle
  length grows linearly. Net: a few extra exploit rounds compared to
  Grim/AllD, but still close to DD-floor.
- vs alternator (DCDCDC...): the alternator NEVER stops defecting, so
  every cooling phase ends with another fresh D and a longer
  punishment. By round ~10 we are in essentially permanent D against
  the alternator while the alternator plays its CD pattern. Expected
  per-round: ~3.0 (we get T=5 on opp-C rounds, P=1 on opp-D rounds).
  Comparable to cycle_detector's outcome but achieved without an
  explicit cycle test, just via the natural escalation.
- vs TFT-family (TFT, GTFT, TF2T, adaptive_tft, cycle_detector):
  cooperate first round, opp cooperates first round -> stay in C.
  Under 2% noise, occasional D's appear. Gradual triggers on the
  first noisy D: punishes 1 round (since total_D=1), then 2 cool C's.
  This punishment is shorter than what TFT does (TFT echoes once,
  triggering a CD-DC oscillation). Gradual should actually be
  *smoother* against noisy reciprocators because of the cooling
  phase, which forcibly returns to CC. Expected ~570-590.
- vs Pavlov: Pavlov flickers under noise. Gradual will punish each
  flicker burst, with punishment length tracking the cumulative
  defection count. Pavlov's bursts are short, so Gradual's first
  few punishments are short. After several Pavlov bursts, our
  punishments lengthen and start to dominate. Should land somewhere
  near TF2T's 417 vs Pavlov, possibly better.
- vs Grim: round 1 CC. A noise flip on either side eventually triggers
  Grim into permanent D. Then Gradual sees AllD-like opponent and
  escalates. Net: ~DD-floor after the trigger event. Similar to TF2T
  vs Grim (~256).
- vs Random: opp coop rate ~0.5. Lots of fresh defections, but also
  cool-off windows in between. Gradual will spend a lot of time
  punishing. Probably mid-pack, similar to TF2T vs Random (~394).
- vs cycle_detector: both cooperate at start. Steady CC, identical to
  reciprocator behavior. Should score ~590-600.
- vs self (Gradual vs Gradual): mutual cooperate. First noise flip
  triggers ONE D from the other side (its first observed D). They
  retaliate 1 D each, cool 2 rounds, return to CC. Self-play should
  be smooth, similar to TFT self-play under noise (~500).

Implementation note. The strategy has STATE (current punishment count,
current cooling count, last-trigger total_d), but we must derive it
from histories each call. The most reliable way is to *re-simulate*
the strategy round by round: given opp_history of length n, replay
all n round transitions to get our state at round n. Each call is
O(n) work, which for n <= 200 is negligible.

Edge cases. If our previous moves don't match what the simulation
would have produced (e.g. due to noise flipping our own moves in
opp's view but NOT in our internal view — actually they DO flip in
our own view too, since we see post-noise history), the simulation
will still be consistent with the histories we received. The key
invariant: `my_history` records what the opponent saw (post-noise),
not what we intended. The strategy is *defined* on the post-noise
histories.

Risk. Like TF2T and adaptive_tft, Gradual has a decision boundary
(cumulative D count) that an adversary could probe. A pattern like
DCCCCCCCDCC... (one D every ~7 rounds, never triggering an
escalation since each punishment finishes between D's) would let an
opponent slowly drain us at 2.5/round average — but they'd also
have to absorb our 1 D-per-trigger, so they get ~2.5/round too. Not
a clear exploit, just a slow-bleed equilibrium. No current bot in
the field plays this pattern, but it's an open vulnerability.
"""

COOLING = 2


def choose_move(my_history, opp_history):
    n = len(opp_history)
    if n == 0:
        return "C"

    # Re-simulate state from history. After processing the k-th round
    # (k = 0..n-1), `state_d` is the number of punishment-D's remaining
    # and `state_c` is the number of cooling-C's remaining.
    state_d = 0
    state_c = 0
    cumulative_d = 0  # total observed D's by opp at any point

    for k in range(n):
        opp_move = opp_history[k]
        if opp_move == "D":
            cumulative_d += 1

        # State BEFORE round k determined what we played. After the
        # round, we update state given opp_move and elapsed action.
        if state_d > 0:
            # We just played a punishment D; decrement.
            state_d -= 1
        elif state_c > 0:
            # We just played a cooling C; decrement.
            state_c -= 1
        else:
            # We were cooperating. Check if opp just defected.
            if opp_move == "D":
                # Trigger: start new punishment of length `cumulative_d`
                # plus COOLING C's after.
                state_d = cumulative_d
                state_c = COOLING

    if state_d > 0:
        return "D"
    if state_c > 0:
        return "C"
    return "C"
