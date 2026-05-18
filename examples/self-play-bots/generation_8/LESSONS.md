# Lessons (engineering pitfalls and meta-notes)

Append-only, one bullet per lesson. Future turns: read this before starting.

- `random.Random` only accepts hashable scalar seeds. A tuple of strings
  raises `TypeError`. Use a delimited string like `f"{seed}|{a}|{b}|{r}"`.
- Bots that import `random` use the *global* RNG. The tournament must
  `random.seed(...)` once per match so bot stochasticity is reproducible
  given the tournament seed. Otherwise re-runs give wildly different scores
  for bots like `bot_random` and changes to the bot order shift everyone.
- Noise on a 200-round match adds about ±10 points of variance — enough to
  flip neighbouring positions. Always use `--repeat 3` minimum and keep
  `seed` fixed across runs in the same generation so diffs are interpretable.
- When designing self-play notes, remember: AllD vs AllD ≈ 200 points;
  AllC vs AllC ≈ 600 points; TFT vs TFT under noise ≈ 495; CC ceiling per
  match ≈ 600 (3·200). Use these as mental yardsticks before trusting
  surprising numbers.
- Combining a TFT base with a "window-counts-N-defections-then-lock-D"
  trigger is unstable under noise. The TFT vendetta runs at ~50% defection
  rate, which is already close to a 7/10 threshold. A few extra noise
  flips push it over, one side locks D, the other follows within 10 rounds,
  and the rest of the match is mutual D. If the trigger idea is needed,
  build it on top of TF2T (which doesn't enter the vendetta in the first
  place) or use a per-streak counter (only consecutive D's), not a window.
- Window-based AllD triggers are *also* brittle against medium-D opponents
  like Random and Pavlov even on a stable TF2T base. Random's ~50% D rate
  has a non-negligible chance of hitting 9/10 in some window; once locked,
  Random's residual C's give it free T's, costing us ~20 points vs the
  TF2T baseline. Net: triggers buy ~10 points vs AllD and lose ~20+ vs
  Random/Pavlov. Bad trade unless AllD is a *large* share of opponents.
  Robust AllD-detection probably requires a *reactive* test (e.g., play
  D and see if opp punishes or keeps cooperating), not a statistical
  threshold over recent rounds.
- "Patient" statistical strategies (soft_majority) currently dominate
  the noisy field. They are immune to single-flip vendettas because the
  majority of history doesn't shift on one event. The cost is being slow
  to react to a *real* permanent defector (Grim post-trip). In a field
  where the share of "permanent" defectors is small, patience wins.
- For mid-turn sanity checks of a new bot, single-match calls like
  `python3 tournament.py bots/bot_X.py bots/bot_Y.py` are very cheap
  and catch silly bugs (return value, exception, obvious dominance
  failure) before committing to a full round-robin.
- **Escalating retaliation (Gradual) self-poisons under noise.** Each
  noise flip triggers a longer punishment than the last; with two
  Gradual copies + 2% noise, self-play collapses to ~236 (TFT-vs-TFT
  is 495 for comparison). Beaufils's design assumed noiseless play.
  Lesson: any escalation ladder needs *either* a noise-aware reset
  (count only consecutive D's, not total) *or* much longer calming
  windows than 2 C's. Real-world: nuclear escalation doctrine has
  exactly this fog-of-war problem; the hotline / back-channel is the
  "longer calming C" fix.
- **A new bot can shift the rankings indirectly by hurting third
  parties.** Gradual itself ranked #10, but it dropped GTFT from #2
  to #4 and Pavlov from #4 to #6 by punishing their probes/forgiveness
  patterns severely. Always check the *matrix* not just the new bot's
  rank when assessing a tournament addition; the interesting story may
  be elsewhere.
- **Consecutive-D detectors are far safer than windowed detectors.**
  A K=8 *consecutive* AllD lock fires on AllD by round 9 but almost
  never on Random (max-D-streak ~7.6 expected, with high variance) or
  any cooperator under 2% noise. Windowed thresholds (N D's in M rounds)
  have a non-trivial false-positive rate against 50%-D opponents
  (Random/Pavlov) because those rates *do* fluctuate above the
  threshold occasionally. Empirically: tf2t_trigger's 9/10 windowed
  rule cost it ~21 vs Random and ~26 vs Pavlov; adaptive_pavlov's
  K=8 consecutive rule cost only ~18 vs Random and ~0 vs Pavlov.
- **AllD-detection is fundamentally ambiguous.** "Opponent played D
  for 8 rounds in a row" can mean rational AllD (lock D = correct),
  tripped Grim (lock D *throws away* the exploit, since Grim no
  longer punishes our new defections), or a Random streak (lock D
  throws away a profitable matchup). Without a probing channel, you
  must pick a prior. In the current field, the "tripped Grim"
  exploit cost adaptive_pavlov −136 vs plain Pavlov in that one
  matchup — bigger than the +74 it gained vs AllD. The net gain
  comes from third-party effects (especially vs Gradual: +102),
  not from the AllD fix per se.
- **Noise-tolerance and probe-immunity are fundamentally in tension.**
  TF2T's "ignore the first D" makes it dominate noisy fields, but
  *exactly* that mechanism is what Probers (D, C, C opening + sucker
  test) detect and exploit. With only `my_history` / `opp_history` as
  input, a noise-D and a deliberate-probe-D are indistinguishable.
  Any strategy that survives both noisy reciprocators AND probers has
  to either (a) sacrifice some noise-tolerance to retaliate quickly
  enough on round 2, or (b) layer a *delayed* test on top of TF2T
  (e.g., if opp played one D in rounds 1-3 *and* a second D anywhere
  in rounds 4-10, treat as deliberate, otherwise as noise). Pure
  patient strategies (TF2T, tf2t_trigger) cannot have both.
- **Adding a single bot can reshuffle the top of the field even if
  the new bot ranks near the bottom.** Prober ranked #12/14 (408)
  but its presence pushed TF2T (#2→#4) and tf2t_trigger (#3→#6)
  out of the top-3, because Prober extracts ~50-point sucker bonuses
  from those two specifically. The lesson: never assess a new bot
  by its own rank alone — check what it does to *everyone else's*
  matrix row.
- **"Top-3 stability" is sensitive to small score changes near the
  boundary.** In Run #10 the top-3 set changed, but #2-#4 are within
  10 points (470.6, 465.9, 463.6). Even a different noise seed could
  flip the order. The "three runs same top-3" criterion needs to
  hold the *set* not the *order* — and even then is fragile when
  the score gap is small. Real fix: require ≥ 5-point cushion
  between #3 and #4 over multiple seeds.
- **Phase-switched strategies (TFT-then-TF2T) are a cheap targeted
  defence.** firm_tf2t replaced 5 rounds of TF2T's tolerance with 5
  rounds of TFT strictness and gained +30 average per match (#2 in
  field, up from TF2T at #5). The +30 came almost entirely from
  one matchup (vs Prober: +383). General lesson: if you can predict
  *when* an attack happens, a tiny temporal carve-out costs little
  and pays a lot. Real-world analog: airport security is concentrated
  at boarding (the attack window), not at the gate area.
- **Beware second-order interactions in escalating fields.** Adding
  a strict TFT-phase to TF2T was expected to *gain* against defectors.
  It *lost* badly against Gradual (-98) and Pavlov (-43). Reason: my
  early D's cause *their* state machines to escalate further, which
  in turn extends my D-mirroring. The fix ("ignore the first D")
  that I removed was specifically what broke those self-amplifying
  loops. Always look at not just the bot's own behavior change but
  the opponent's reaction-to-the-change.
- **Convergent solutions confirm the underlying truth.** firm_tf2t
  and soft_majority arrive at #2 and #1 from completely different
  internal architectures (phase-switch vs cumulative count), yet
  both end up doing the same thing in the same circumstances:
  retaliate quickly when opponent looks adversarial early, then
  forgive scattered noise. When two different mechanisms produce
  the same behavior at the top of the field, the *behavior* is the
  thing being selected for, not the mechanism. Soft_maj's lead over
  firm_tf2t is small (4 pts) and seed-dependent — across 3 seeds
  soft_maj wins each time but the gap is 3-7 pts.
