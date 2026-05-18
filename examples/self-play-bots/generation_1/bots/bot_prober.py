"""Prober (Beaufils 1996 family).

Behaviour:

- Opening sequence (rounds 0, 1, 2): D, C, C. This is the "probe".
- From round 3 onwards, examine the opponent's responses to the probe:
  - If the opponent played D in round 1 OR round 2 (i.e. retaliated to
    the opening defection), conclude that the opponent is a retaliator
    and switch to classical Tit-for-Tat for the remainder of the match.
  - Otherwise (opp played C in both rounds 1 and 2 — never punished the
    free D), conclude the opponent is a pushover and play AllD for the
    remainder.

Rationale: Prober is the canonical "predator" strategy. It tries to
detect "AllC-like" opponents and exploit them for T=5 per round, while
behaving as TFT against anyone who shows teeth. Unlike pure AllD, it
does not waste rounds being mutually punished by retaliators.

Expected behaviour in our pool:

- *Vs AllC*: AllC never retaliates, Prober locks AllD, ~4.95/round.
- *Vs TFT*: TFT plays D in round 1 (echoing Prober's D), so Prober sees
  retaliation, switches to TFT. The first 3 rounds zig-zag, then both
  cooperate. ~3.0/round long-run.
- *Vs Grim*: Grim plays D from round 1 onwards (Prober defected first).
  Prober sees retaliation → switches to TFT → copies Grim's D forever.
  Mutual D after round 0, ~1.0/round.
- *Vs TFTT*: TFTT only retaliates after TWO consecutive Ds. Prober plays
  D, C, C — TFTT sees just one D, never retaliates in rounds 1-2.
  Prober concludes "pushover" and plays AllD. TFTT eventually catches
  on (sees two D's), but Prober already locked AllD. Result: Prober
  exploits TFTT.
- *Vs GTFT*: GTFT plays C in round 1 with probability ~0.1 (it forgives
  the D occasionally), else D. So in ~10% of matches Prober sees no
  retaliation and goes AllD. In ~90% it sees D in round 1 and goes TFT.
  Effectively Prober is rolling a die: usually a normal TFT match,
  occasionally a free exploitation.
- *Vs Pavlov*: Pavlov shifts after the round-0 D (because it lost),
  plays D in round 1. Prober sees D → switches to TFT. Then Pavlov-
  vs-TFT-with-late-start dynamics — typically converges to mutual C
  or to oscillation depending on noise.
- *Vs AllD*: AllD plays D in round 1. Prober sees D → switches to TFT
  → DD forever. Same as TFT-vs-AllD baseline.

Risks:

- *Vs Prober* (self-play): both probe with D, C, C. Each sees the other
  defect in round 0 but cooperate in rounds 1 and 2. So *each* concludes
  "opp is a pushover" and plays AllD from round 3 onward. Catastrophic
  self-play, score ~1.0/round. This is the canonical Prober weakness.
- *Vs Random*: Random's response in rounds 1-2 is 25% chance of two
  Cs in a row. So ~25% of matches Prober plays AllD vs Random (good),
  75% it plays TFT vs Random (average). Mild positive expectation.

This bot is interesting precisely because it is the first non-nice
strategy after AllD in our pool. It tests whether the cooperator
cluster can absorb a predator without collapsing.
"""


def choose_move(my_history, opp_history):
    n = len(my_history)
    # Opening probe: D, C, C.
    if n == 0:
        return "D"
    if n == 1:
        return "C"
    if n == 2:
        return "C"
    # After the probe: decide once based on opp's responses in rounds 1-2.
    # If opp ever defected in rounds 1 or 2, treat them as a retaliator.
    retaliated = opp_history[1] == "D" or opp_history[2] == "D"
    if retaliated:
        # Switch to classical Tit-for-Tat.
        return opp_history[-1]
    # Otherwise: opp is a pushover. Play AllD.
    return "D"
