"""Adaptive Pavlov — Pavlov base + AllD detector with re-test option.

Pavlov (Win-Stay, Lose-Shift) is famously near-optimal in noisy mutual-C
matchups, including self-play (DD-after-noise auto-corrects to CC next
round). But it has a known Achilles heel against AllD: Pavlov keeps
oscillating C, D, C, D, ... feeding the all-defector ~0.5 sucker rounds
per round. In our Run #8 that cost Pavlov 119.7 points vs AllD (compare
to TFT's 210.7 or TF2T's 200.0).

Idea: keep the Pavlov core for the cooperative matchups, but bolt on a
*consecutive* AllD detector. If the opponent has played D for K
consecutive rounds (regardless of my move), lock into D and stop the
sucker bleed.

Design choices and trade-offs:

* **Consecutive** rather than windowed. We learned from tf2t_trigger that
  windowed thresholds (e.g. "9 D's in last 10") fire too easily against
  Random (~50% D rate has a non-negligible chance of hitting 9/10) and
  Pavlov (occasional D probes after noise). A consecutive streak is far
  harder to hit by chance: with 2% noise, P(8 consecutive flips out of
  C) ≈ 0.02^8 ≈ 2.6e-14 — essentially never. So we will only trigger
  on a *deliberate* defector.

* **K = 8.** Long enough that Pavlov's own noise-induced D-then-C
  probing (max streak ≈ 1) and a TFT-vs-TFT noise vendetta (D-streak
  is rare; even alternating DC patterns reset the streak) cannot reach
  it. Short enough that AllD is detected by round 9 at the latest,
  saving ~190 rounds of sucker cycling.

* **No re-test.** Once locked, we stay locked. Simpler and safer. We
  could add a "re-cooperate after 50 rounds of mutual D" probe to
  recover from Grim-trip situations, but Grim itself doesn't re-cooperate
  either, and a re-test against a true AllD would just hand it a free T.

* **My own history isn't checked.** All that matters for the trigger
  is opp_history; if opp is playing 8 D's in a row we lock D regardless
  of what we were doing. (Note: against Grim, the first opp D triggers
  Grim's permanent D, so after ~8 more rounds we lock D too, which is
  fine — both at D = mutual ~200.)

Expected behaviour:

* **vs Pavlov, AllC, TFT, TF2T, GTFT, soft_majority:** identical to plain
  Pavlov. No 8-D streaks appear, so we stay in Pavlov mode. The good
  self-play that makes Pavlov famous (vs Pavlov ≈ 570 even with noise)
  carries over.

* **vs AllD:** plain Pavlov scored 119.7. Adaptive Pavlov plays
  C, D, C, D, ..., D, D, D... locking after 8 consecutive opp D's
  (rounds 1-8 minimum). Worst case score ~ 8 Pavlov-cycle rounds at
  avg ~2.5 each + 192 rounds at 1.0 each ≈ 20 + 192 = 212. About
  TFT-level (210.7), a +90 gain over Pavlov.

* **vs Grim:** Grim cooperates until the first noise-induced D from us
  (round k). After that, Grim is permanent D. Our streak counter sees
  opp = D from round k+1 onward (Grim plays D regardless of us). After
  8 more rounds we lock D. Then mutual D for the rest. Before locking,
  Pavlov was cycling C/D against Grim's D — score ~2.5 per round for
  ~8 rounds, then ~1 per round for ~190 rounds. Better than plain Pavlov
  vs Grim (348.0) or worse? Plain Pavlov against late-trip Grim: Pavlov
  oscillates C/D after Grim trips at round k, getting ~2.5 per round.
  For k=10, plain Pavlov score = 10 CC rounds (30) + 190 cycle rounds
  (475) = ~500. For k=50: 50 CC (150) + 150 cycle (375) = ~525. With
  our lock: 10 CC + ~8 cycle (20) + 182 mutual D (182) = ~212. WORSE.

  Hmm — that's a regression vs plain Pavlov for the Grim matchup. The
  AllD-detector hurts us against Grim because Grim looks identical to
  AllD *after* the trip, but with Pavlov's oscillation it actually
  exploits Grim's no-retaliation-on-our-D state (Grim doesn't care, it
  plays D anyway, so we get a free 5 every other round when we cycle
  to D). Locking to D throws that away.

  This is a real trade-off: in the current 12-bot field, Pavlov gains
  ~90 vs AllD but loses ~310 vs Grim (and possibly some vs adaptive_tft
  if it locks D against us). Net per-opponent average: roughly even
  or slightly worse than plain Pavlov.

  We accept this. In a field with more AllD-likes (e.g. probers,
  testers, Grim-after-trip) Adaptive Pavlov should beat plain Pavlov;
  in this field it's a wash. The interesting story for the report is
  the *trade-off* itself: AllD-detection costs you against opponents
  that *behave like AllD but aren't AllD-rational* (like tripped-Grim,
  which doesn't punish your defections).

* **vs Random:** Random's max D-streak in a 200-round match has expected
  length ~ log2(200) ≈ 7.6. There's a non-trivial chance of hitting an
  8-D streak, especially under noise. Maybe ~50% of matches will trigger
  the lock somewhere. When locked, we stop Pavlov's profitable C/D
  cycling against Random (plain Pavlov scored 498.7) and drop to
  cycling-then-AllD. Some loss, perhaps 50-100 points.

* **Self-play:** identical to plain Pavlov (no D-streaks under 2% noise).
  Near-ceiling ~570. Good.

* **vs adaptive_tft:** adaptive_tft has a lock-D mode of its own. If it
  ever fires (which it does against vendetta partners) we'd then see
  8 opp D's and lock too — both lock to D for rest of match. Probably
  worse than plain Pavlov vs adaptive_tft (442.7).

In summary: Adaptive Pavlov is a *targeted* improvement against AllD
specifically, with a measurable cost against Grim and Random. Whether
that nets positive depends on the field composition. Worth running
to verify the trade-off prediction.

Key insight for the report: an "AllD detector" cannot tell whether the
opponent is rational-evil (AllD itself), broken-cooperator
(Grim post-trip), or random-streak (Random). All look identical from
the outside. Punishing all three the same way (lock D) is suboptimal
against the latter two — a classic problem of inferring intent from
behaviour with no extra channel.

Determinism: choose_move depends only on histories; no random.
"""

K_ALLD_STREAK = 8


def choose_move(my_history, opp_history):
    if not my_history:
        return "C"

    # AllD detector: K consecutive D's from opponent -> permanent D.
    if len(opp_history) >= K_ALLD_STREAK:
        if all(m == "D" for m in opp_history[-K_ALLD_STREAK:]):
            return "D"

    # Pavlov core: win-stay (opp cooperated), lose-shift (opp defected).
    last_mine = my_history[-1]
    last_opp = opp_history[-1]
    if last_opp == "C":
        return last_mine
    return "D" if last_mine == "C" else "C"
