"""Firm Tit-for-Two-Tats — TF2T hardened against early-game probes.

Lesson from Run #10: TF2T-family bots (TF2T, tf2t_trigger) tolerate
*one* D, which is exactly the signal Prober looks for. Prober plays
D, C, C in rounds 1-3, watches the opponent's reply in rounds 2-3,
and if the opponent never punished the round-1 D it labels them a
"sucker" and exploits forever after. TF2T is engineered to be
patient, so it walks into the trap.

Idea: be TFT-strict in the *early* rounds (where probes happen) and
TF2T-tolerant from round 6 onwards (where noise-vendetta avoidance
matters most).

Concretely:
* Rounds 1 to 5: pure Tit-for-Tat.
  - Round 1 (no history): C.
  - Rounds 2-5: mirror opp's last move.
  This means a single D from the opponent in rounds 1-4 will *be
  retaliated against immediately in the next round*. A probing bot
  will see retaliation and re-classify us as a reciprocator, not a
  sucker.
* Rounds 6+: TF2T. Retaliate only when the *last two* opponent moves
  were both D. Single isolated D's (overwhelmingly likely to be noise
  at this point) are forgiven.

Why 5? Heuristic — Prober's diagnostic window is rounds 2-3, and
similar testers (potential future bots) might extend up to 4-5. Five
rounds of "strict" play covers most testers without paying a long
cost in lost noise-tolerance.

Expected behaviour:

* vs Prober: round 1 = C vs D, round 2 = D vs C (we retaliate against
  the probe), round 3 = D vs C (we mirror their round-2 D — wait, but
  Prober plays C in round 2, so we mirror C? Actually:
  - Round 1: us C, Prober D
  - Round 2: us D (TFT mode, mirror their last D), Prober C
  - Round 3: us C (mirror their last C), Prober C
  Now Prober checks rounds 2-3 of opp: D, C. Not "C,C". Verdict: TFT.
  Prober switches to TFT. We continue TFT for rounds 4-5, then TF2T.
  Net: avoid the exploit. Expected score ~495 (TFT-vs-TFT under noise).
  That's a big improvement on TF2T's 250 vs Prober.

* vs AllD: round 1 C (S=0), round 2 D forever after. Same as TFT.
  Expected ~210, slightly better than TF2T's ~200.

* vs AllC: all CC modulo noise. ~595.

* vs TFT: same as TFT-vs-TFT initially. Once we enter TF2T mode at
  round 6, we tolerate single noise flips. TFT keeps mirroring our
  C's. Should be slightly *better* than TFT-vs-TFT (we'd damp noise
  vendettas in the late game). Expected ~520-550.

* vs TF2T: matched-pair behaviour. TF2T-vs-TF2T already handles noise
  via two-D tolerance. We add a TFT phase up front but it never bites
  here (TF2T doesn't defect first). Should be near-ceiling ~600.

* vs GTFT, Pavlov, soft_majority: similar to TF2T's matchups but
  slightly punishment-happier early. Mostly cooperative, near
  ~570-595.

* vs Grim: round 1 C, round 2 C. Probably no early D from grim if no
  noise. If a noise flip occurs in our move, Grim trips and locks D.
  We respond D (TFT phase) then in TF2T phase keep responding D
  because Grim plays D twice in a row. Same outcome as TF2T-vs-Grim.

* vs self: both play TFT first 5 rounds. No defections → all C's. From
  round 6 both TF2T. A single noise flip is tolerated. Expected ~595.

* vs Random: TFT phase will retaliate often early, then we relax. Some
  exploit of single isolated D's. Probably comparable to TF2T vs
  Random (~615).

Risk: the strict-early phase opens a small 5-round vendetta window
vs TFT-likes if a noise flip lands in rounds 1-5. Round 1 noise flip
on us → TFT bot plays D in round 2 → we mirror D in round 3 → TFT
plays D in round 4 → ... vendetta until round 6 when we enter TF2T
mode and break the cycle by playing C if their preceding D was
isolated. Worst case: 5 rounds of mutual D = 5*1 = 5 points lost.
Probability ~10% of any rounds 1-5 having a flip. Expected cost
~0.5 points per match. Negligible.
"""

EARLY_PHASE = 5


def choose_move(my_history, opp_history):
    rnd = len(opp_history)

    # Round 1: always C (no history).
    if rnd == 0:
        return "C"

    # Rounds 2-5: strict TFT. Mirror opp's last move so a probe D in
    # round 1 (or 2-4) is punished immediately in the next round.
    if rnd < EARLY_PHASE:
        return opp_history[-1]

    # Round 6+: TF2T. Retaliate only on two consecutive D's.
    if opp_history[-1] == "D" and opp_history[-2] == "D":
        return "D"
    return "C"
