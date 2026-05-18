# Strategies log

Running interpretation: which strategies pull their weight, and why.

## After run 001 (pantheon only)

### What works

- **Grim (1st)**. With many defector-shaped opponents (AllD, Random) and
  no other forgiving cooperators to keep mutual-C alive, the population
  *rewards* unforgivingness. Grim turns into AllD after the first betrayal
  and then collects DD-floors instead of being exploited.
- **AllD (2nd)**. Free 5s against AllC, DD floor against everyone else.
  In a field this hostile, "never trust" is a strong baseline.

### What doesn't (yet)

- **TFT (4th)** is *Axelrod's* champion but loses in this tiny pantheon
  because:
  1. There are no other gentle reciprocators to mutually exploit
     the CC-payoff with.
  2. Noise of 2% over 200 rounds breaks TFT-vs-TFT badly: expected
     CC payoff drops from 600 toward ~420 because every misfire kicks
     off a CD/DC echo until another misfire breaks the chain.
  3. TFT alone can't punish AllD as efficiently as Grim does (it
     still tries to cooperate every time AllD slips).
- **AllC (last)**. The textbook losing strategy in any field with even
  one defector. Confirms the "nice but not retaliatory" failure mode.
- **Random**. Surprisingly third — it beats TFT and AllC because half
  its moves accidentally exploit AllC, and it doesn't trigger Grim
  immediately. Still well below R=3 because half its DD's pull it down.

### Hypotheses to test in future runs

1. Adding more *forgiving cooperators* (Generous TFT, TF2T, Pavlov) should
   create a "cooperation block" that lifts those strategies above Grim,
   because they cash in on mutual CC while Grim wastes rounds in DD vs
   each other.
2. Once enough cooperators exist, TFT-family should rise to the top, and
   AllD should drop, because exploiting just AllC isn't enough to outscore
   sustained CC.
3. Pavlov (Win-Stay-Lose-Shift) should self-correct under noise faster
   than TFT — it should beat TFT in noisy environments.

## After run 002 (GTFT added)

### What changed

- TFT moved 4th → 1st. The mere presence of *one* additional gentle
  reciprocator was enough to lift TFT's average above Grim/AllD, because
  TFT-vs-GTFT settles near the CC line (586 ~ 600 noisefloor).
- Grim moved 1st → 3rd. Grim still farms AllC, but it now wastes more
  matches in DD vs GTFT and noisy-TFT.

### What I learned about GTFT

- GTFT's *cooperation pair* is fantastic: 593 vs self, 570 vs TFT,
  near-perfect mutual-C.
- GTFT's *exploit-immunity* is bad: 147 vs AllD — *worse than DD*. It
  literally pays AllD to be there. Forgiveness needs to be conditional
  on a baseline of opponent cooperation, not unconditional.
- Lesson: a noise-handling strategy should distinguish "did the opponent
  defect because of noise" (forgive) from "did the opponent defect
  because they're AllD" (do not forgive).

### Hypotheses for upcoming bots

- **TF2T** (Tit-for-Two-Tats): tolerates 1 noisy defection but punishes
  2 in a row. Should beat GTFT against AllD (1 D is forgiven once, then
  it locks into D from round 2 onward) while keeping the noise-handling
  benefit against TFT/GTFT.
- **Pavlov / Win-Stay-Lose-Shift**: after a noise misfire, both Pavlovs
  recover within ~2 rounds, much faster than TFT. Should rank high in
  noisy IPD.
- **Adaptive AllD-detector**: explicitly tracks opponent cooperation
  rate; once below threshold for a while, lock D. Should fix GTFT's
  AllD-bleed without losing its forgiveness against noise.

## After run 003 (TF2T added)

### What changed

- TF2T entered at #1 (468.24). It beat TFT (the previous leader) by
  ~15 points purely from two effects:
  1. Better self/peer cooperation under noise (TF2T-vs-TF2T = 594 vs
     TFT-vs-TFT = 499).
  2. Still hits the DD floor against AllD (200), unlike GTFT (146).
- TFT held its top-3 spot only because GTFT and TF2T mutually
  cooperated with it. Without forgiving partners TFT collapses.

### What I learned about TF2T

- TF2T is the cheapest noise fix: just one extra step of memory and
  one extra if-statement. No probability, no tuning.
- Its real edge is *symmetry of forgiveness*: both bots forgive a
  single misfire the same way, so noise events almost never lead to
  the long CD/DC echoes that hurt TFT.
- Open question: TF2T is exploitable by a clever DCDCDC alternator
  ("provocateur" or "every-other-D"). We haven't built one yet, so the
  weakness doesn't show up in this run. A future bot_alternator would
  test how brittle TF2T is.

### Hypotheses still standing

- **Pavlov / WSLS** should also do well in noise; it's worth adding
  next to compare to TF2T head-to-head.
- **AllD-detector / adaptive bot** is the cleanest fix for GTFT's
  AllD-bleed; we should still build one, because it would also handle
  Random better than TF2T does (TF2T vs Random = 373, somewhat low).
- The leaderboard is now cooperator-dominated. Each new defector-style
  bot we add will probably drop in rank unless it has a real exploit
  vector against the cooperator block.

## After run 004 (Pavlov added)

### What changed

- Pavlov entered at #1 (459.54), edging TF2T by ~2 points. The win is
  *narrow* and built on three legs:
  1. Best-in-class self-play under noise (589 vs CC-max 600).
  2. Above-CC payoff vs AllC (694) — opportunistic noise-triggered
     exploit: once noise flips a round to look like AllC defected,
     Pavlov reads "I won by playing D" and stays D, mining T=5/round.
  3. Decent reciprocation with the cooperator block.
- Grim climbed back to #3 because Pavlov is one of the rare cooperator
  bots Grim can punish (180.3 against it). When the population contains
  "flickering" cooperators that occasionally play D, Grim's permanent-
  punishment niche reopens.

### What I learned about Pavlov

- **WSLS recovers from noise in ~2 rounds, vs TFT's potentially infinite
  CD/DC echo.** This is the cleanest demonstration of why "shift after
  loss" outperforms "copy the move" in a noisy world.
- **Pavlov is brittle vs pure exploiters.** vs AllD it scores 111.7 —
  *below* the DD-floor. The CDCDCD oscillation is real and the cost is
  ~90 points compared to a DD-floor strategy. So Pavlov is a top
  strategy only when the field is cooperator-heavy. In an all-defector
  field, it would lose hard.
- **Pavlov can be unintentionally "greedy" vs AllC.** This is morally
  ambiguous: it doesn't *intend* to exploit, but the WSLS rule means
  any noise misfire converts Pavlov into a hidden AllD vs AllC. In real-
  world terms, this is the strategy that "accidentally" keeps the
  benefit when a partner makes a tiny mistake — feature for utility,
  bug for trust.

### Hypotheses for next bots

- **bot_alternator (DCDC...)** would test TF2T's weakness: TF2T always
  forgives single Ds, so DCDC should let alternator collect 5,0,5,0
  against TF2T (avg 2.5/round) — better than CC! Worth confirming.
- **bot_adaptive_tft** — explicitly tracks opponent cooperation rate
  over a window; if rate < some threshold, lock into D (treat as AllD);
  else play TFT. This should outperform GTFT and possibly TF2T against
  AllD while keeping noise tolerance.
- **bot_hard_majority** — defect if opponent has more Ds than Cs so far
  (start D). Should crush AllC and Random; behavior vs TFT-family is
  the open question.
- **bot_soft_majority** — cooperate unless opponent has strictly more Ds
  than Cs (start C). Mirror of hard majority, biased nice.

## After run 005 (adaptive_tft added)

### What changed

- bot_adaptive_tft entered at #1 (485.00), a ~+15 jump over the
  previously-tight 4-way cluster. The biggest single-bot lift since
  the original pantheon was assembled.
- Pavlov collapsed 1st → 6th. Same absolute score (~455), but the
  field now contains a bot (adaptive_tft) that *recognises* and
  *punishes* Pavlov's noise-induced D-streaks. This is the first
  example of a strategy explicitly counter-designed against another
  strategy in the field winning by exploiting that match-up.
- GTFT lifted 4th → 2nd. The same dynamic as TFT in run 002: adding
  one more reliable cooperation partner (adaptive_tft) raises GTFT's
  average without changing GTFT itself.

### What I learned about adaptive_tft

- **Conditional generosity beats unconditional generosity.** This is
  the clean answer to the "GTFT bleeds to AllD" problem from run 002.
  Forgiveness with a hard threshold (0.45 coop rate) keeps the noise-
  handling benefit of TF2T while closing the AllD leak.
- **Lock-after-evidence > lock-on-first-D.** Grim's "one D and you're
  dead" rule collapses under noise. Adaptive_tft's rule needs both
  (a) a warm-up window and (b) a sustained low coop rate. So a single
  noisy D never triggers the lock, but a permanent defector reliably
  does.
- **Detection is asymmetric.** Adaptive_tft punishes Pavlov (526 vs
  Pavlov, while Pavlov got only 357 against it). Pavlov can't detect
  what adaptive_tft is doing; it just keeps WSLS-flickering, which
  keeps coop rate visible to adaptive_tft as "below 0.45 → lock".
  This is interesting as a real-world parallel: a sophisticated
  observer beats a habit-driven actor whose habit is misaligned with
  the environment.
- **The 0.45 threshold is a deliberate compromise.** Set higher
  (e.g. 0.6), adaptive_tft would lock against Random (~50% coop)
  and lose money vs Random. Set lower (e.g. 0.2), it would *not*
  lock against Pavlov's flicker and lose its main edge. 0.45 is just
  below the random baseline and well above the AllD-with-noise rate
  (~0.02).

### Hypotheses still standing

- **bot_alternator (DCDCDC...)** is now the most important missing
  adversary. It would expose two weaknesses at once:
  1. TF2T cooperates forever against DCDC (no two D's adjacent →
     never punishes), eating 5,0,5,0 = 2.5/round.
  2. Adaptive_tft sees coop rate = ~0.5, just above 0.45 → never
     locks, so it also keeps cooperating. The pure-alternator might
     actually dethrone adaptive_tft. We should build it next.
- **bot_hard_majority / bot_soft_majority** — majority-based strategies
  haven't been tested. Hard majority would defect against AllC heavily,
  which the field punishes; soft majority would behave like TFT in
  this field. Probably less interesting than alternator.
- **bot_window_tft** — same as adaptive_tft, but uses a recent-N
  window for coop rate instead of all-time. Would handle adversaries
  that *change* strategy mid-match (e.g. cooperate for 30 rounds to
  reset the rate, then defect). Worth building once we have such an
  adversary in the pool.
- **bot_zd_extort** (zero-determinant extortion, Press & Dyson 2012)
  — sets up a linear relation forcing the opponent's score to scale
  with its own. It's a famous "smart-strategy" result and would be
  fun to put in the pool, but it has no clean drop-in form without
  some setup. Future.

### Refined view

After 5 runs, the field has settled into 3 strategy archetypes:

1. **Conditional cooperators with detection** (adaptive_tft, TF2T,
   TFT, GTFT). They handle noise gracefully, cooperate with each
   other, and at worst hit the DD-floor against AllD. Adaptive_tft
   is the strongest by ~15 points because it actively punishes
   noise-flipping cooperators (Pavlov) as well.
2. **Punishers** (Grim). Permanent-D-after-D works only if there's
   someone in the field with a positive recovery rule that Grim can
   exploit. With cooperators outnumbering punishers and detection
   catching flickers, Grim's niche is shrinking.
3. **Pure types and Random** (AllC, AllD, Random). They're floor and
   ceiling references. AllC subsidises the field; AllD parasites
   subsidise themselves but can't escape DD-floor against everyone
   else; Random just gives the field free CCs and DDs.

## After run 006 (alternator added)

### What changed

- bot_alternator entered at #1 (493.13), and the move from #6 to #1
  for an *unranked* freshman in a single run is the largest
  redistribution we've seen. Adaptive_tft (previous #1) dropped to #6;
  TF2T dropped from #2/#4 to #8.
- The win came almost entirely from two cells: `alternator vs TF2T = 774`
  and `alternator vs adaptive_tft = 774`. Both targets are "tolerant"
  cooperators — they're built to *forgive* a single D, and the
  alternator weaponises that tolerance directly.

### What I learned about alternator

- **Forgiveness without a memory of pattern is a leak.** TF2T tolerates
  any single D; DCDC never produces two D's in a row, so TF2T never
  punishes. Adaptive_tft adds an all-time threshold check, but DCDC
  keeps coop rate at exactly 0.5 — just above 0.45, so the threshold
  never trips. The lesson is sharper than "tolerance is bad": tolerance
  is fine, *as long as the tolerated pattern is genuinely random*. As
  soon as the opponent's D's come in a *predictable* cycle, a tolerance
  rule becomes a free-money pump.
- **TFT is uniquely robust against alternator.** TFT and alternator
  played to a draw (494 each), because TFT has no tolerance parameter
  for alternator to attack. This is one of the most counter-intuitive
  results so far: the simplest member of the cooperator family beats
  the *cleverer* members against a structured adversary.
- **Grim is the only bot in the pool that *crushes* alternator** (594
  for Grim, 112 for alternator), because Grim doesn't tolerate anything.
  The pendulum keeps swinging: in run 005, sophistication (adaptive_tft)
  beat simplicity (Grim); in run 006, simplicity (Grim and TFT) beat
  sophistication (adaptive_tft and TF2T).

### Hypotheses for next bots

The alternator exposes a clean gap. To close it we need a bot that
either:

1. **bot_window_tft** — uses opponent coop rate over a *recent* window
   (say last 20 rounds) instead of all-time. DCDC over 20 rounds still
   shows coop rate 0.5, so a fixed-threshold window detector won't
   help directly. But combined with a *defection cycle detector*
   ("the opponent's defections are evenly spaced") this could work.
2. **bot_prober** — sends DCC at the start. If the opponent retaliates,
   plays TFT for the rest. If the opponent keeps cooperating (sucker),
   switches to AllD. A prober naturally classifies AllC vs reciprocator
   and would be a real counter to AllC and probably a draw against
   TF2T/TFT.
3. **bot_cycle_detector** — explicitly looks for short cycles (period 2
   or 3) in opp_history. If a cycle is found, defect on the C-rounds
   of the cycle and play 0 on the D-rounds (i.e. always defect once a
   cycle is detected). This would shatter pure alternator and similar
   bots. Worth building.
4. **bot_gradual** (Beaufils et al. 1996) — escalating retaliation: on
   the n-th detected D, retaliate with n consecutive D's, then forgive
   with two C's. Should be much harder to game than TF2T/TF2T-variants.
5. **bot_hard_majority** — defect if opp has more D's than C's so far,
   else cooperate. Against DCDC, majority is 50/50 borderline. Probably
   won't help vs alternator but would be a strong reference point.

The cycle-detector is the most surgical counter; the prober and
gradual strategies are good general-purpose additions. I'll build
the cycle-detector next as the direct counter, then add gradual as
a more robust general strategy.

## After run 007 (cycle_detector added)

### What changed

- bot_cycle_detector entered at #1 (505.06), the second example of a
  bot designed specifically to neutralise an existing leader (the
  first was adaptive_tft vs Pavlov in run 005). The mechanism was
  exactly the hypothesised one: after ~10 rounds the detector
  recognises alternator's DCDC pattern and switches to permanent D,
  flipping the run-006 alternator-vs-TF2T result (`alternator beat
  TF2T 774-307`) into its mirror image (`cycle_detector beats
  alternator 571-137`).
- bot_alternator collapsed 1st → 6th. Its weaponised exploits of
  TF2T and adaptive_tft are unchanged (still ~770 head-to-head), but
  the new ~137 cell vs cycle_detector dragged its average down.
- TFT held its top-3 spot AGAIN (4th run in a row in top-2). This is
  the most consistent strategy in the field by far. TFT has no
  decision boundary to attack, so each new bot either ties it
  (alternator: 488-488) or loses to it cleanly. Boring, robust,
  unfailing.

### What I learned about cycle_detector

- **Layered detection works.** Three independent rules — TF2T
  (tactical), all-time rate (long-term), and adjacent-pair-difference
  count (structural) — fire on disjoint conditions. Each closes a
  different attack vector, and none of them trips on the same
  benign opponent (TFT-family, AllC, Random).
- **The cycle test is structurally narrower than the others.** It
  only catches period-2 patterns. A future opponent with period-3
  (e.g. DDCDDCDDC) would slip past, since DDC has only 2 adjacent-
  pair-differences per 3 (DD same, DC diff, CD diff -> 2 of 3
  positions differ ≈ 6/9 below the 7/9 threshold). The fix is
  either a period-3 check or a more general autocorrelation test
  at multiple lags.
- **The narrowest win matters most.** cycle_detector's 19-point lead
  over TFT (#2) is mostly explained by *one* matchup, alternator.
  In a hypothetical Run 008 where someone adds a period-3 cycler,
  this lead would evaporate unless we also extend the detector.
- **Cycle_detector cannot be exploited by a higher-cycle period
  because its non-cycle layers still apply.** A period-3 cycler with
  net coop rate below 0.45 would still be caught by the rate-lock.
  But a balanced period-3 (1 D in every 3 rounds) keeps the rate at
  ~66% — above the lock. So a future "stealth alternator" is real.

### Hypotheses for next bots

The field now has the four core archetypes well-represented:

1. **Pure types**: AllC, AllD, Random (always lose; references).
2. **Conditional cooperators**: TFT, GTFT, TF2T, adaptive_tft,
   cycle_detector. Cycle_detector is the strongest; TFT is the most
   robust.
3. **Pattern exploiters**: alternator. Exposed the holes in TF2T,
   adaptive_tft.
4. **Punishers**: Grim, Pavlov. Both struggle in the cooperator-
   heavy field.

To progress further (toward a stable top-3), we need:

- **bot_gradual** (Beaufils et al. 1996). After the n-th observed D
  from opponent, retaliate with n consecutive D's, then issue two
  cooling-off C's. This is more punitive than TF2T and more
  forgiving than Grim — and crucially, the cooling-off phase
  protects against alternator-style exploit: gradual would only
  defect after seeing one D, NOT defect again until two more D's
  appear. Could be either a new winner or a new mid-pack bot.
- **bot_prober** (DCC opener; then if opponent retaliates, play
  TFT, else AllD). Tests classification ability against the
  current cooperators. May replace AllD as a smarter defector.
- **bot_majority** variants (hard/soft). May not win but provide
  baselines for "look at totals, not last move".
- **bot_omega_tft** — TFT that "randomises out" if it gets stuck
  in a CD/DC echo. Could be a worse-vs-alternator (no defense) but
  better-vs-self version of TFT.

I'll add bot_gradual next: it's the strongest theoretically-grounded
unimplemented cooperator strategy, and it directly addresses
alternator without needing structural pattern detection.

## After run 008 (gradual added)

### What changed

- bot_gradual entered at #2 (504.64), only ~11 points behind
  cycle_detector. Gradual is the strongest *generalist* defender
  added so far — it handles alternator (558 vs cycle_detector's
  576), Pavlov (566, the best of any reciprocator), and Random
  (538, also best) without using any explicit pattern-detection
  layer. It's pure escalating reciprocity.
- The hypothesis from before run 008 held: "Gradual handles
  alternator without needing structural pattern detection".
  Confirmed; the mechanism is *automatic state lock-in via
  escalation*, not pattern recognition.
- TFT held top-5 for a 5th consecutive run, falling from #2 to
  #4. The pattern from LESSONS.md 012 (TFT is the equity-index-
  fund of IPD) continues — it never wins a run but never falls
  below #5 in a 12-bot field.

### What I learned about Gradual

- **Escalation generalises pattern-detection.** Cycle_detector
  beats alternator because it explicitly tests for period-2
  cycles. Gradual beats alternator because *any* persistent
  defection — periodic, irregular, or noisy — drives the
  cumulative D count up monotonically, and the punishment length
  grows linearly with it. After enough triggers, Gradual is
  effectively AllD against any persistent defector, with the
  cooling phases providing a few free 5s but bounded in count.
  This means Gradual generalises to period-3, period-5, or
  aperiodic exploiters that would slip past cycle_detector's
  period-2 test.
- **Cost: 2-cooling-C tax against persistent defectors.**
  Gradual vs AllD = 199 < DD-floor of 200 (and < Grim's lock-in
  performance of 217 in same matchup). The cost is small in
  absolute terms but exists. Against alternator it's worse:
  Gradual gets 558 vs cycle_detector's 575, an ~17 point
  shortfall. The 2 cooling rounds per cycle are an inherent
  trade for being "less brittle" than a permanent lock.
- **Asymmetric advantage against noise-flickering bots.**
  Gradual vs Pavlov = 566.3 (best in the field). This was a
  surprise to me. Mechanism: Pavlov has bursts of D under noise,
  and Gradual punishes each burst with escalating severity.
  Because Pavlov's WSLS reverts to C when its D meets Gradual's
  C-cooling (Pavlov interpretes "lose-stay" wrong here -- it
  actually reverts to C since (D,C) is "win-shift"), the system
  rapidly re-stabilises on CC after each burst. The cooling
  phase is what enables that re-stabilization; without it (Grim,
  which has no cooling) Pavlov gets repeatedly punished and
  never re-cooperates.
- **Self-play is OK but not great.** Gradual-vs-Gradual = 551.7,
  below TF2T-self (598.7) and adaptive_tft-self (595.3). The
  reason: under 2% noise, one bot sees the other's noise flip
  as a fresh D and triggers a 1-D punishment. The cooling phase
  helps de-escalate but adds the noise-echo problem of TFT.
  This puts Gradual *between* TFT-self (465, no cooling at all)
  and TF2T-self (599, full forgiveness of single D's) — about
  what we'd expect.

### What this tells me about the meta-game

- The top of the field is now a contest between two distinct
  philosophies:
  - **Detector-based defense** (cycle_detector, adaptive_tft):
    classify the opponent, switch behaviour modes. Sharp wins on
    the patterns they classify, but vulnerable to opponents that
    sit *just outside* the decision boundary.
  - **Mechanism-based defense** (Gradual): no classification, just
    escalating reciprocity. Slightly broader applicability, but
    pays a small cost (cooling tax) against the cases that
    detectors handle precisely.
- For the third decisive run, I want to test which philosophy
  scales better as the field grows. Adding a *probing* bot
  (e.g. bot_prober that defects in round 1 to test) would
  challenge both approaches differently:
  - cycle_detector: would NOT lock D on the first move (the
    cycle test requires 10 rounds of observation), so would
    play TF2T-style and tolerate the prober's first D.
  - Gradual: WOULD respond to the prober's first D with a
    1-round D, then 2 cooling C's. If the prober interprets
    Gradual's D as "this opponent fights back" and switches
    to TFT-mode, both bots reach CC for the rest of the match.
  - This is a meaningful test of nice-vs-not-nice openings.
- An alternative test is bot_majority (hard or soft) which
  uses a *fundamentally different* aggregation (mode of all
  opp moves) rather than recency. Majority strategies often
  perform poorly in IPD because they're too slow to respond,
  but as a baseline they're informative.

### Hypotheses for next bots

I'll add **bot_prober** next: round 1 = D (test), then if
opp retaliated immediately (round 2 D), switch to TFT for the
rest; if opp continued C (sucker), switch to AllD. This is the
classical "exploit naive cooperators while playing nicely with
reciprocators". It should:

- Crush bot_always_c (full T=5 stream after round 2: ~990).
- Mostly tie with TFT-family (after round 2 prober plays TFT;
  the opening D gets echoed back to D in round 3, then they
  drift through a brief noise-echo and stabilise on CC).
- Lose to Grim (round 1 D triggers Grim's permanent lock).
- Tie with itself (DD opening, both switch back to TFT or AllD
  symmetrically).
- Beat alternator? Unclear — depends on whether alternator's
  second move (C) is interpreted as "no retaliation, you're a
  sucker, switch to AllD". I expect Prober to misclassify
  alternator and try to exploit it, then alternator's
  *third* move (D) hits Prober at the wrong moment. Will see.

After Prober: bot_majority (hard) as a reference, then think
about period-3 or pattern-aware extensions.

## Things I'm watching

- Self-play robustness under noise: lower is worse.
- Performance vs AllD: never trade more than DD-floor.
- Performance vs AllC: full exploit (5/round) is "greedy", reciprocal
  (3/round) is "nice" — the tournament's structure prefers nice as long
  as enough cooperators exist.
- **Niche-reopening for punishers.** Pavlov flickering brings Grim back
  to top-3 because Grim has someone exploitable. Strategies don't exist
  in isolation; each new bot reshapes the niche structure.
- **Counter-strategies.** Adaptive_tft's #1 finish is the first case of
  a bot designed to neutralise a specific weakness in another bot
  (Pavlov's noise-flicker) and being rewarded for it. This opens a
  meta-game: each new bot reshapes which detectors are useful.

## After run 009 (prober added)

### What changed

- bot_prober entered at #10 (417.36), beating only Grim, AllC and
  AllD. Confirmed the hypothesis that a *not-nice* opener pays a
  big price in a field with detector-based defenders.
- bot_gradual moved to #1 (489.72), narrowly ahead of cycle_detector
  (488.15). The gradual-detector swap is decided by *one bad
  matchup*: cycle_detector hit DD-floor vs prober while gradual
  recovered after its 1-round punishment. A reminder that in a
  small field, a single new bot can flip the rankings via second-
  order effects, not by being competitive itself.
- TFT moved up to #3 (it has the best `tft vs prober = 475.7`
  cell of any reciprocator). Six consecutive runs in top-5 — TFT
  is the most consistent finisher in the field.

### What I learned about Prober

- **Sucker-exploit alone is not enough.** Prober gets ~985 vs AllC
  but the rest of the field punishes its R1 defection enough to
  drag it below the reciprocator pack. In a field where >50% of
  bots are detectors or reciprocators, probing is a net loss.
- **Detectors love probers.** cycle_detector and adaptive_tft both
  trigger their permanent-defect modes on a single R1 D. The
  detectors don't *intend* to punish probers specifically; they
  trigger on the same pattern (early defection, persistent in
  cycle_detector's case). This is asymmetric: detectors built to
  punish AllD also punish Prober for free.
- **The 3-round probe window is too narrow.** Under 2% noise, a
  single noisy C from a true reciprocator in rounds 2 or 3 can
  misclassify them as a sucker. The probability is ~4% per round
  for both opp moves to be noisy, plus the possibility of a
  cooperator playing C from the start. In practice this didn't
  bite much (the noise-flip and the actual classification logic
  mostly coincide), but in a higher-noise regime it would.
- **Self-play disaster.** Two probers mutually classify each other
  as suckers and lock into DD. The strategy fundamentally can't
  cooperate with itself.

### What this tells me about the meta-game

- The field has reached a stage where *adding a not-nice strategy
  hurts that strategy more than the cooperators it preys on*.
  Adding more cooperator-exploit bots will not yield winners
  unless they ALSO solve the detector and self-play problems
  simultaneously.
- The cooperator-defender axis matters: gradual and cycle_detector
  both win because they're *both* cooperators with their kind AND
  punishers against defectors. A pure exploiter (prober) cannot
  do both.
- For the next bot, I want to test a *different* idea: rather than
  add another reciprocator variant or detector, test a strategy
  that explicitly tries to FIX prober's self-play problem (signal
  + handshake) while keeping its exploit capacity. Call this
  "Mutual Recognition": a bot that probes once but recognises
  another prober via a handshake pattern and switches to mutual
  CC. This is the "secret handshake" idea from coordination games.

### Hypotheses for next bot

I'll add **bot_handshake** next: round 1 = D (probe, like prober);
round 2 = D (second probe — the handshake signal); rounds 3+:

- If opp also played DD in rounds 1-2, they're a handshake bot —
  switch to AllC for the rest (mutual exploitation impossible,
  but mutual cooperation pays 3/round forever).
- Else if opp played C in either round 1 or 2, they're either a
  cooperator (switch to AllD to exploit) or a slow-reciprocator
  (switch to TFT to limit damage). Heuristic: if opp played C in
  BOTH rounds 1 and 2, AllD (sucker); else TFT (reciprocator).

Self-play prediction: both play DD-DD-CC-CC-... mutual cooperation
from R3 onwards. Score ~ 1+1+3*198 = 596. Excellent self-play.

vs AllC: DD-DD then exploit. 1+1+5*198 = 992. Same as Prober.
vs TFT: DD-DD then opp retaliates in R2 (echo of our R1 D);
  R3 opp plays D (echo of R2 D); we see opp played C in R1 and D
  in R2 -> we're in "C in either round" branch — actually wait,
  TFT plays C in R1 by default, then D in R2 (echoing our D),
  then D in R3 (echoing our D). So opp moves are CDD. R1=C, so
  not a handshake -> fall through to "C in either round" branch.
  Opp played C in R1 and D in R2 -> TFT mode. Then mutual D-D
  noise echo for a bit, then CC.
vs cycle_detector: DD-DD. cycle_detector responds: R1=C (start),
  R2=D (echo of our R1 D), R3=C (echo of our R2 — wait, we played
  D in R2 too, so opp R3 = D). Opp moves CDD. Same branch as TFT.
  But cycle_detector might lock D after seeing our 2 D's.
vs prober: DD-DD vs prober's DCC. Opp R1=D, R2=C, R3=C. We see
  opp R1=D, R2=C — not handshake. C in R2 — sucker classify.
  Switch to AllD. Prober separately classifies us as reciprocator
  (we played D in R1 and... oh wait, R2 we also played D —
  prober sees DD in rounds 1+2). Prober switches to TFT. So we
  AllD and prober TFTs — we get the exploit. Asymmetric win for us.

Risk: handshake-bot vs prober and prober vs handshake-bot will
disagree on classification. handshake harvests prober's TFT-mode
cooperation, but the overall outcome depends on noise.

This is interesting — handshake should slot in around #5-7 in
total score but should *win on self-play and AllC exploit
combined*. If it ranks higher than prober it'll demonstrate that
adding a coordination layer is enough to fix prober's main
weakness.

## Run 010 — handshake outscores prober by 24 points

Results after Run 010 (params unchanged):

- handshake at #9 (429.05), prober at #11 (405.57). Confirmed:
  the handshake mechanism is a net positive over pure probing.
- Top-3 still {gradual, tit_for_tat, cycle_detector} (same SET as
  Run 009, positions slightly shuffled). One more run with same
  SET = convergence.

### What worked for handshake

- **Self-play 593.0 vs Prober-self 207.3** — the headline win. The
  two-D opener + verification-C protocol works exactly as designed
  in mutual matches: both bots recognise the DD signal, both play
  C in R3, both confirm, both lock in AllC. This single cell
  represents a ~28-point lift to handshake's average across the
  14-bot field.
- **vs random 461.7 vs Prober's 445.7** — modest improvement.
  Random's 50/50 mix means rounds 1-2 are 25% DD (handshake-
  candidate path), 25% CC (sucker path), 50% mixed (TFT path).
  Mixed and CC paths both yield AllD or TFT, both of which beat
  random in the long run.
- **vs TF2T 371.3 vs Prober's 257.0** — counterintuitive
  improvement. TF2T retaliates after 2 consecutive D's; our 2-D
  opener triggers TF2T's retaliation in R3. We see opp CC in R1-R2
  (not retaliated yet) -> classify sucker -> AllD. So our R3+
  is all D. Mutual DD ensues with TF2T occasionally returning to C.
  Mutual DD avg ~1.5/round * 197 ~ 296. Plus early bonus 15. Total
  ~370.

### What hurt handshake vs prober

- **vs TFT 409.3 vs Prober's 510.0** — -101. The 2-D opener locks
  TFT into mutual DD for ~5-8 rounds before noise breaks the lock.
  Under noise, the mutual-DD lock isn't broken uniformly — it can
  persist 20+ rounds if both bots keep mirroring noisy D's. So 1
  extra "bad" round in expectation translates to ~4x the per-round
  cost in practice.
- **vs gradual 384.7 vs Prober's 469.0** — -85. Two consecutive D's
  in our opener trigger gradual's cumulative-D punishment counter
  to start at 2, not 1. Each subsequent noise-flip then adds to a
  growing punishment.
- **vs cycle_detector 224.3, vs adaptive_tft 217.7** — both at
  or near DD-floor. The detectors lock D against our 2-D opener
  and never release.

### Detector vulnerability is the consistent ceiling

Both Prober (#11) and Handshake (#9) hit the same ceiling: the
two big detector bots (cycle_detector, adaptive_tft) lock D
against any not-nice opener and stay locked. Combined cost: ~3
cells worth of ~600-point losses = ~1800 points distributed across
the bot's row. For Handshake this is ~128 points off the average,
which is roughly the gap between #9 and the top tier (~480).

Implication: a "not-nice" opener cannot break into top-3 unless
it ALSO solves the detector-lock problem. There are two ways:

1. **De-escalate the opener**: probe with a single C-then-D or
   C-D-C instead of a D-block. Most detectors don't lock on a
   single D inside an otherwise-cooperative opening.
2. **Late probe**: cooperate normally for the first ~20 rounds to
   build trust, THEN probe with a single D. Gives up the early-
   round exploit window where suckers are most vulnerable.

### Next bot: Contrite TFT (CTFT)

Candidates considered for the next bot:

- **Contrite TFT** (CTFT): plays TFT, but if our last move was
  noisily flipped from C to D (we INTENDED C, world SAW D, opp
  retaliated next turn), we forgive opp's retaliation instead of
  echoing it. Known fix for TFT's noise-vulnerability in self-play.
  Should improve TFT-self from ~444 to ~580 under 2% noise.
- **ZD-extortion** (Press-Dyson 2012): mathematically forces a
  payoff difference vs ANY opponent. Powerful but complex; rank
  prediction unclear in a small field.
- **Hybrid TFT-Pavlov** (HTFT): TFT, with a Pavlov-style override
  to break the mutual-D lock when both have been DDing.
- **Reverse-Handshake**: open C-C as a tribal signal. Switch to
  AllC if opp also CC'd, AllD if opp DD'd, TFT else. Doesn't
  trigger detector locks.

Picking **Contrite TFT** because:
- It directly addresses TFT-self's noise vulnerability (the
  empirical 444 vs theoretical 600).
- It's "nice" (won't trigger detector locks).
- It tests whether *smarter forgiveness* (only when we caused the
  defection via noise) beats GTFT's blanket forgiveness.
- It has clear evolutionary-game-theory backing (Boyd 1989,
  Sugden 1986).

Prediction: CTFT vs TFT-family bots should improve on TFT-self
self-cooperation. Vs detectors should rank similarly to TFT
(both nice). Vs handshake should suffer the same R3-confusion as
TFT. Net: CTFT ranks #2-3, similar to TFT or slightly above.

If after adding CTFT we get another run where top-3 SET stays
{gradual, tit_for_tat, X} (X = cycle_detector or ctft), I'll have
3 consecutive runs with the same top-3 set and can declare
convergence + write the final REPORT.md.

## Run 011 — Contrite TFT lands at #1, displaces gradual

Result: CTFT first, GTFT second, gradual third. Top-3 set changed from
Run 010's {gradual, tit_for_tat, cycle_detector} to {contrite_tft,
generous_tft, gradual}. The convergence counter resets.

### What worked for CTFT

- **Self-play 593.0 vs TFT-self 533.3 (+60)**. The single biggest win.
  CTFT-vs-CTFT under 2% noise loses ~2.5 points per noise event (one
  CD round before mutual apology re-establishes CC). TFT-vs-TFT under
  2% noise loses ~30+ points per noise event because the CD/DC echo
  persists until another flip happens to break it. The asymmetry is
  the core mechanism.
- **CTFT vs handshake 507.3 vs TFT-vs-handshake 448.3 (+59)**. CTFT's
  apology window helps escape the DD lock caused by handshake's 2-D
  opener: a single noise flip in the lock phase triggers CTFT's
  apology, restoring cooperation faster.
- **CTFT vs alternator 493.0 vs GTFT-vs-alternator 436.3 (+57)**. CTFT
  doesn't waste forgiveness on alternator's deterministic D's, while
  GTFT does. CTFT's selectivity here is a feature.
- **CTFT vs TFT 557.0** (asymmetric: TFT gets 533.3 in the mirror).
  CTFT extracts ~24 extra points from TFT by apologising when its
  own flips caused the trouble. TFT, lacking contrition, walks into
  longer CD/DC echoes when CTFT's noise hits.

### What hurt CTFT

- **CTFT vs grim 230.0**. Grim is unforgiving. A single noise flip
  triggers grim's lock, CTFT TFTs back, mutual DD ensues. Apology
  doesn't help because grim doesn't reciprocate apologies. -77 points
  vs CTFT's potential 600.
- **CTFT vs pavlov 490.0 vs GTFT-vs-pavlov 530.0 (-40)**. Pavlov's
  WSLS rule oscillates between C and D when paired with a forgiving
  TFT-variant. CTFT's apology fires only on noise; pavlov's
  intentional D's pass through CTFT's TFT layer and produce mutual
  D bursts. GTFT's random C's smooth out this oscillation; CTFT
  cannot.
- **CTFT vs random 452.3**. Random's D's look like noise to CTFT
  (intended C, observed D pattern). The 2-round apology window
  stays open continuously, costing extra C's against a defector
  half the time. ~5-10 points worse than TFT-vs-random.
- **CTFT vs gradual 503.0 vs TFT-vs-gradual 365.7 (+138!)**.
  Interesting reversal: TFT-vs-gradual is a known nightmare matchup
  (gradual's escalation overpunishes TFT's mirror). CTFT's apology
  shortens the punishment-mirror cycles when noise hits, leading
  to a much cleaner relationship with gradual.

### Why CTFT beats GTFT

GTFT forgives at rate p=0.3 regardless of cause. CTFT forgives only
when it caused the trouble itself. The "smart" forgiveness avoids
wasting C's on opponents whose D's are deliberate:

- vs deterministic deceivers (alternator, prober D-phase, pavlov-D):
  GTFT's blanket forgiveness gives away points; CTFT's targeted
  forgiveness doesn't.
- vs noise-shaped opponents (TFT-family, CTFT-family, generous-TFT):
  CTFT and GTFT both recover from CD/DC echoes; CTFT is slightly
  more efficient because it apologises only when needed.

This is the central lesson of Run 011: in noisy worlds, *attribution
matters*. Knowing that the trouble was your fault is more valuable
than randomly forgiving.

### What's still vulnerable

CTFT inherits TFT's vulnerability to Grim and AllD (both DD-floor
locked). Adding contrition doesn't fix unconditional-D opponents.

### Next bot candidates

The top-3 set just changed, so convergence is reset. Need 3+ more
runs with the same top-3 to declare convergence. Two paths:

A) **Add another "smart" reciprocator** to test whether the trio
   {ctft, gtft, gradual} is robust. Candidates:
   - **Omega TFT** (Slany & Kienreich 2007): TFT + a "deadlock"
     detector that switches to C-burst when stuck in a long DD
     phase. Should help against grim, AllD-recovery scenarios.
   - **TFT-Pavlov hybrid (TFT2P)**: TFT, but when in a DD streak
     of 4+ consecutive rounds, play a single C as Pavlov would.
     Breaks DD locks without becoming exploitable.
   - **Adaptive Contrite TFT (ACTFT)**: CTFT but the apology window
     adapts based on opp's response history. If opp ignored a
     previous apology (didn't return to C), shorten or disable
     the apology window against this opp.

B) **Add a "defector buster"** that specifically targets grim and
   AllD without sacrificing cooperation with reciprocators. Candidates:
   - **Spite TFT** (anti-grim): like TFT but switches to C-burst
     after 5 consecutive DD rounds (similar to omega).
   - **Tester** (Axelrod's RHFV): probes early; if not punished,
     plays AllD; if punished, plays TFT. Different from prober:
     tests with C (mistake), not D, so detectors don't lock.

Picking **Omega TFT** because:
- It directly addresses both grim-lock and AllD-recovery in CTFT's
  weak cells.
- It stays "nice" so it doesn't trigger detector locks.
- It has solid evolutionary-game-theory backing as a known fix to
  TFT's deadlock weaknesses.
- It can be implemented stateless via reconstruction (like CTFT).

Prediction: Omega TFT ranks #2-4. It should improve vs grim and
AllD (DD-lock-recovery), but lose marginal points vs gradual and
TFT-family (the C-burst occasionally gets exploited). If Omega
breaks into top-3, it'll show that detection mechanisms (like
cycle_detector's lock) are not the only way to dominate the field
— bursts can also work.

If after adding Omega TFT we get top-3 stability (same set 3 runs
running), I'll write REPORT.md.

## Run 012 — Omega TFT lands at #2, top-3 set changes again

Result: contrite_tft #1 (508.10), omega_tft #2 (501.27), cycle_detector
#3 (498.42). Top-3 set changed from Run 011's {contrite_tft,
generous_tft, gradual} to {contrite_tft, omega_tft, cycle_detector}.
Convergence counter resets to 0 again. (Pattern: adding a bot that
itself becomes top-3 forces a set change.)

### What worked for Omega TFT

- **vs alternator: 599.3 (column top!).** Omega's randomness counter
  trips around round 16 against alternator's CDCD pattern, then locks
  into AllD mode and exploits alternator's residual C's for the rest
  of the match. The "trip and switch" exploitation pattern adds ~100
  points over TFT-vs-alternator (494).
- **vs handshake: 499.7.** Deadlock detector helps escape the DD
  lock that handshake's 2-D opener induces. Compare TFT 332.7, CTFT
  478.3, GTFT 405.7. Omega is competitive with CTFT here via a
  different mechanism (pattern-detected break vs intent-attributed
  apology).
- **vs random: 578.3 (column top!).** Random's D's pile up on RC;
  once threshold hits, omega locks AllD and exploits random's
  residual C's. Random plays C ~50% of the time so AllD gets 2.5
  points per round average. Net: better than continuing to TFT.
- **vs tit_for_tat: 556.0 asymmetric (TFT got 436.7).** Omega's
  deadlock detector breaks the CD/DC echoes that TFT alone cannot
  escape, similar to CTFT-vs-TFT asymmetry. Asymmetry of ~120 points
  in omega's favour — the biggest single-cell asymmetry vs TFT.
- **Self-play 556.0.** Better than TFT-self 449.7 by ~106. Worse
  than CTFT-self 592.3 by ~36. The deadlock detector takes 4 rounds
  to break each CD/DC echo (vs CTFT's apology which breaks in 2);
  the extra 2 rounds per noise event explain the ~36-point gap.

### What hurt Omega TFT

- **vs grim: 211.0 (vs TFT's 233.0, -22).** When grim locks D after
  a noise flip, omega's deadlock counter doesn't fire (DD ≠
  alternation). Omega TFTs back D, mutual DD ensues. Noise on grim's
  side then occasionally seduces omega into a C (mirror of observed
  C), which grim exploits. Same brittleness as TFT, slightly worse.
- **vs prober: 338.0 (vs TFT's 473.3, -135).** Prober's early D's
  prime omega's RC near the threshold; one more noise flip in
  prober's TFT-mode phase trips RC to 8, switching omega to AllD.
  Then mutual DD ensues. The randomness threshold is too sensitive
  to early-game probes; a prober that's actually TFT-shaped after
  round 4 gets misread as "random" by omega.
- **vs always_d: 208.3 (vs TFT's 200.7, +8).** Tied with TFT. Omega
  doesn't enter AllD mode against AllD because the RC resets on
  matching D's. This is correct behaviour but doesn't IMPROVE over
  TFT.

### Why Omega TFT outperforms expectations

I predicted omega ranks #2-4 with the catch that it'd lose to grim
and AllD. The grim/AllD prediction was right (it does lose ~22
points vs grim), but I underestimated the wins from:

1. The detector-class exploitation (alternator, random). Omega is the
   FIRST bot to actively detect and exploit non-cooperators while
   staying nice with cooperators. This is the same niche that
   cycle_detector was filling, but omega does it via threshold
   detection rather than pattern detection. The two strategies
   complement each other and both ranked top-3.
2. The deadlock break vs TFT and TFT-family. Each forgiver-vs-omega
   pair gets +20-100 points by escaping echoes. CTFT, omega, and
   GTFT all benefit from being "smart forgivers"; omega is the
   newcomer in this class.

### Key lesson for adding bots

The top-3 in Run 011 was {contrite_tft, generous_tft, gradual} — all
three "nice + forgive somehow" bots. Adding omega TFT (another nice +
forgive) bumped gradual out and replaced GTFT with cycle_detector
(detection-style cooperation enforcer). So the dominant CLASS of
strategy hasn't changed (nice + smart-forgive + detect), but the
specific bots rotate as new exemplars are added.

Pattern: the top of the field is a TIER, not specific bots. The tier
consists of bots that:
- Are nice (cooperate first)
- Forgive noise via SOME mechanism (random, apology, deadlock break)
- Detect deceivers and exploit them (omega's RC, cycle_detector's
  pattern detection, gradual's escalation)
- Don't get exploited by AllD/grim too badly

Within the tier, individual bots compete for the top-3 slots and the
exact ranking depends on the OTHER bots in the field (relative
exploitability vs each other).

### Next bot candidates

Two strategic options to test convergence:

A) Add a bot DESIGNED to break top-3. Best candidate:
   - **Omega-Contrite TFT (OCTFT)**: combines Omega's deadlock detector
     with CTFT's apology window AND drops the randomness counter (which
     hurts more than helps under noise). Should outperform both Omega
     and CTFT individually. Predicted: #1 or #2.

B) Add a bot that probably WON'T break top-3, just to validate
   stability. Candidates:
   - **Adaptive Pavlov (APavlov)**: WSLS + AllD-detector. Likely
     ranks mid-tier (#5-#8).
   - **Soft Majority (SMaj)**: cooperate if opp's #C >= #D. Statistical
     bot. Likely ranks ~#10.
   - **ZD-Extortion (ZDe)**: zero-determinant, mathematically guaranteed
     to extract > opp in 2-player. Hurts in round-robin (DD-floor vs
     self and vs reciprocators). Likely ranks #10-#13.

Picking **Omega-Contrite TFT (OCTFT)** because:
- It tests the "hybrid is better than the sum" hypothesis directly.
- It addresses Omega's biggest weakness (grim/AllD) by inheriting
  CTFT's apology (which still doesn't fix grim but at least fixes
  noise-induced DD between nice bots).
- If OCTFT breaks into top-3, we've shown that "smart forgiveness"
  has at least 3 independent mechanisms (Omega's deadlock detector,
  CTFT's apology, and possibly cycle_detector's exploitation switch)
  that compose well.
- If OCTFT does NOT break top-3 (because the field already has too
  many nice-forgivers), we've shown that the niche is saturated and
  adding more nice-forgivers gives diminishing returns.

Prediction: OCTFT enters at #1 or #2. Top-3 set becomes {OCTFT,
contrite_tft, omega_tft} or similar. Convergence counter resets
once more.

If OCTFT either DOES or DOES NOT break top-3, the NEXT bot after
that should be something deliberately different — e.g., an exploiter
like ZD-Extortion or a memory-2 lookup-table bot — to validate that
the top-3 holds against radically different threats.

## Run 013 — bot_octft analysis

OCTFT entered at **#2 (502.96)**, just 0.57 points behind contrite_tft.
The hybrid hypothesis was validated: combining CTFT's apology window
with Omega's deadlock detector (while dropping Omega's randomness
counter / AllD-switch) produces a strictly better top-tier bot than
either parent alone.

### What worked

- **Apology window inherited from CTFT.** Self-play 590.7 (~CC ceiling
  minus noise), same mechanism as CTFT-self 592.7. Apology fires the
  round after opp retaliates for my noise flip; mutual cooperation
  restored after exactly 1 wasted round.
- **Deadlock break inherited from Omega.** OCTFT vs TFT = 576 (with
  TFT getting 598 in mirror) — within 20 points of CTFT-vs-TFT
  performance. The deadlock break unilaterally exits CD/DC echoes
  even when opp isn't a forgiver. Cost: occasional self-injury when
  the "echo" was actually opp probing or alternating; benefit:
  unilateral repair on its own timeline.
- **NO randomness counter.** This was the key insight. The randomness
  counter cost Omega 135 points vs prober (false-positive AllD
  trigger) and 22 vs grim. Removing it: OCTFT vs prober = 578 (+240
  over Omega), OCTFT vs grim = 256 (+45 over Omega). The net cost of
  dropping the counter is ONLY the loss against alternator (-160) and
  random (-49) — but the field has more probers and grims than
  alternators and randoms. Net positive.

### What didn't work

- **vs alternator: 432.3** (vs Omega's 592.0, -160). Without the AllD
  switch, OCTFT can't exploit alternator's pattern. The deadlock
  break fires every 3 rounds and gets exploited (alternator's D
  takes my C). This is the biggest single cell loss from dropping
  Omega's randomness counter.
- **vs random: 437.0** (vs Omega's 486.3, -49). Random's D's don't
  pattern-match into a CD/DC echo (random is random), so deadlock
  break rarely fires; OCTFT just TFTs back. Random plays C 50% so
  TFT-vs-random ~ 455 typical. OCTFT slightly worse because of
  occasional misfired apologies.

### Asymmetric pairs

- `octft vs tit_for_tat = 576` while `tit_for_tat vs octft = 598`.
  TFT extracts +22 from OCTFT. This is OPPOSITE to the usual
  CTFT-vs-TFT pattern (where CTFT extracts more). Likely: OCTFT's
  deadlock break fires more aggressively than CTFT's apology, and
  each break gives TFT a free D-on-C exploitation round.
- `octft vs prober = 578` while `prober vs octft = 472`. OCTFT extracts
  +106 from prober. Prober's early-D probe doesn't trigger any
  OCTFT defensive switch (no randomness counter); when prober flips
  to TFT mode at round 4, OCTFT TFTs back and they cooperate. Prober
  gets nothing extra from the probe.

### Why it ranked #2 (not #1)

CTFT (503.53) edged OCTFT (502.96) by 0.57. The likely reason:
OCTFT's deadlock break is more aggressive than the apology, and
fires on patterns that CTFT correctly identifies as "not my flip,
don't apologise". These cases produce slightly worse outcomes than
CTFT's "always-TFT-unless-MY-noise" rule. The deadlock break is
useful asymmetrically against TFT-family bots but slightly wasteful
against everyone else.

### Implications

The TOP TIER of the field is now structurally:
1. CTFT (pure apology, no detector)
2. OCTFT (apology + deadlock break, no AllD switch)
3. Gradual (escalating retaliation + de-escalation)
4. Omega TFT (apology-shaped deadlock break + AllD switch)
5. TFT (pure mirror)
6. Cycle detector (pattern exploitation + TFT base)
7. GTFT (random forgiveness)

All seven are "nice + reciprocate + smart-forgive". The differences
between them are SMALL (~10 points each), explained by:

- Smart-forgive mechanism (apology vs deadlock-break vs random forgive
  vs gradual escalation): apology > deadlock-break > random forgive
  > gradual.
- Exploitation mechanism (none vs pattern detection vs AllD switch):
  none > pattern > AllD-switch. AllD switch is too brittle in our
  field (no AllD opponents to actually exploit, just probers and
  alternators that trigger false positives).

This suggests a "no-detector" rule wins: cooperate; if opp defects,
retaliate; if you flipped, apologise; otherwise stay cooperative.
Trying to detect and exploit opp aggressively (cycle_detector, omega)
helps against a few bots but hurts in general.

### Next bot candidates

The top-3 set has now changed 3 turns in a row (Runs 011, 012, 013).
Adding more bots will continue to shuffle the top. To test
convergence properly, we need to STOP adding bots and run 2-3
identical tournaments to see if the top-3 stabilises. The spec
prefers this approach (option (a) from Run 012 analysis).

Decision: do NOT add a new bot in Run 014. Just re-run the
tournament with the same bot set and check if top-3 = {contrite_tft,
octft, gradual} holds. If yes for Runs 014 and 015, we have
convergence and write REPORT.md.

If the top-3 is unstable across re-runs (because of bot_random's
unseeded RNG or floating-point variance), we'll see it.

If the top-3 IS stable, we have convergence and can write REPORT.md
analyzing the final tier:
- #1 CTFT: pure smart-forgiveness via apology
- #2 OCTFT: apology + deadlock-break (slightly more aggressive
  forgiveness, slightly less efficient overall)
- #3 Gradual: escalating retaliation (different mechanism, exits via
  de-escalation phase rather than apology)

## Update after Runs 014-017 — seed-stability finding

Across 5 seeds (42, 43, 44, 45, 100), **octft is #1 in 4/5 runs and
#2 in the remaining one (losing by 0.57 to contrite_tft).** This is
the clearest seed-robust ranking the project has produced.

The reason octft is the seed-robust winner: it combines two
forgiveness mechanisms (apology window + deadlock detector), each of
which addresses a different failure mode of pure TFT:

- **Apology window** fixes "my noise flip starts a feud against a
  reciprocating opponent." After observing my own unintended D, if
  the opponent retaliates with D, I play C unilaterally to break the
  feud. Symmetry-aware forgiveness.
- **Deadlock detector** fixes "we're locked in alternating CD/DC
  because of a single noise event in an early round." After 3 rounds
  of pure alternation, both bots play C unilaterally to reset.
  Pattern-aware forgiveness.

The key design choice — DROPPING omega-tft's randomness counter /
AllD switch — removed octft's only major vulnerability (vs prober).
Omega-tft loses ~240 points vs prober because prober's two opening Ds
falsely trigger Omega's "this is a non-cooperator" lockdown. octft
doesn't have that lockdown, so it cooperates with prober normally.

Cost of dropping randomness counter: octft loses ~160 points vs
alternator and ~50 vs random (cannot exploit them like omega-tft can).
But these are minor opponents in the field; their lower-rank scores
don't pull octft down enough to outweigh the prober/random gain.

**Generalising:** the best strategies are the ones with the fewest
brittle mechanisms. Adding "exploitation modes" or "lockdown modes"
gives short-term gains against weak opponents but creates failure
surface against tricky-but-cooperative opponents like prober. The
seed-stability test confirms: octft's 2-mechanism design beats both
its 1-mechanism parent (CTFT, single mechanism) and its 3-mechanism
sibling (omega-tft) consistently.

## The cycling #2/#3 slots — what determines them?

Across 5 seeds, #2 and #3 cycle within `{contrite_tft, gradual,
tit_for_tat, generous_tft}`. Which one wins each slot depends on the
noise pattern:

- **contrite_tft** wins #2 when the seed produces "balanced" noise
  (errors distributed roughly evenly across matches).
- **gradual** wins #2 when the noise pattern produces clusters
  (multiple consecutive noise events in some matches). Gradual's
  escalating retaliation handles clusters better than CTFT, which
  apologises round-by-round.
- **tit_for_tat** wins #3 when noise is mild enough that pure mirror
  beats apology-bots wasting moves on each other.
- **generous_tft** wins #3 when many opponents are non-reciprocators
  (gtft picks up easy gains against them).

These four bots cluster within ~10 points of each other. Their
ordering is genuinely sensitive to the noise realisation — there is
no robust #2 / #3 distinction within this group. The robust fact is
they are ALL above the rest of the field.

## Final taxonomy

Tier 1 (octft, alone): nice + reciprocate + apology + deadlock-break,
        no exploitation mode. Robustly #1.
Tier 2 (CTFT, gradual, TFT, gtft, omega-tft): nice + reciprocate +
        ONE forgiveness/exploitation mechanism. Cycle #2-#6.
Tier 3 (cycle_detector, adaptive_tft, tf2t): nice + reciprocate +
        narrow special-case mechanism. ~470-490.
Tier 4 (handshake, pavlov, alternator): mixed or experimental
        strategies. ~440-450.
Tier 5 (random, prober, always_c, grim): brittle or naive. ~390-430.
Tier 6 (always_d): pure defector. ~350, dead last.

Hard ranking within Tier 1-2 doesn't seem to converge to a single
order under any noise seed. The TIER itself is the convergence.
