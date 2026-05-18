"""Gradual (Beaufils 1996): escalating punishment with calming tail.

Rules.

- Round 1: cooperate.
- Otherwise: maintain (statelessly, by replaying history) a queue of
  punishment-sequences. When the opponent defects for the k-th time
  (k = 1, 2, 3, ...), enqueue a sequence of k consecutive D's followed
  by 2 consecutive C's, scheduled to play AFTER any earlier sequence
  finishes. Each turn, play the current scheduled move; if no sequence
  is currently active, play C.

This implements the canonical Beaufils Gradual without the ambiguous
"reset" behaviour that some descriptions add: a new opp defection that
arrives during an existing punishment burst does NOT restart or extend
the current burst — it gets its own burst, queued behind.

Predicted behaviour in this pool.

- vs AllC: each ~2% noise-induced D from AllC counts as an opp
  defection, triggering an escalating punishment. Over 200 rounds we
  see ~4 noise-D's, queueing punishments of 1+2+3+4 = 10 D's and 8
  C's. Most of the match is cooperative (3 per round) but ~18 rounds
  are wasted, reducing the cell from ~600 (TFT vs AllC) to roughly
  ~500. So Gradual under-performs TFT vs AllC. This is the canonical
  Gradual weakness under noise.
- vs AllD: by round 2 we see 1 D and play 1 D + 2 C; by round 5 we
  see another D and play 2 D + 2 C; etc. The escalation gradually
  raises our D-rate towards 1.0, but the 2-C calming tails leak
  free 5's to AllD periodically. Net score should sit BELOW pure
  TFT vs AllD (~210), because the calming C's against an unreformed
  AllD are pure losses. Possibly 150-180.
- vs Grim: Grim observes our 1 D in round 2 (in response to whatever
  Grim did in round 1; if Grim played C and noise didn't flip, we'd
  also play C in round 1 ourselves, so Grim wouldn't lock). Under
  noise, Grim is likely to lock D early due to a noise event, after
  which we ramp punishments against a locked-D opponent. Score
  likely similar to TFT vs Grim or slightly below.
- vs TFT-family: very dependent on noise. Each noise flip of opp's C
  to D counts as a defection and triggers a permanent escalating
  ramp. Over 200 rounds with noise=0.02 we expect ~4 opp-side flips,
  triggering 1+2+3+4 = 10 D's and 8 calming C's. Our 10 D's against
  TFT will themselves trigger TFT retaliations, which then trigger
  more Gradual punishments → cascade. Self-play is likely much
  WORSE than TFT-self-play despite the calming mechanism, because
  each noise event permanently raises the escalation counter.
- Self-play: same cascade as vs TFT, except both sides do it. Should
  be substantially below TFT-self (498.7), possibly near or below
  the DD floor of 200 after enough cascades.

This is precisely the test from Lesson 002 ("ecology, not strategy"):
escalating punishment looks deterring on paper, but in a noisy world
it punishes its own kind. Predicted entry: mid-pack at best, possibly
bottom if self-play cascade is bad.
"""


def choose_move(my_history, opp_history):
    n = len(my_history)
    if n == 0:
        return "C"

    # Re-derive the schedule of punishment sequences from opp_history.
    next_available = 0
    schedule: list[tuple[int, int, list[str]]] = []
    opp_d_count = 0
    for i, opp in enumerate(opp_history):
        if opp == "D":
            opp_d_count += 1
            k = opp_d_count
            start = max(i + 1, next_available)
            seq = ["D"] * k + ["C", "C"]
            end = start + len(seq)
            schedule.append((start, end, seq))
            next_available = end

    # If round n falls inside any active sequence, play that move.
    for start, end, seq in schedule:
        if start <= n < end:
            return seq[n - start]

    # No active punishment — cooperate.
    return "C"
