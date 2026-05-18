# Strategies: what works, what doesn't, why

Running notes, organised by bot. Updated after each tournament run.
The point of this file is to capture *causal* insight, not raw
scores. Scores go in `SCORES.md`.

## Pantheon (Run 001)

### bot_always_c — naive dove
- Score: 333.20 (#5 / 5).
- **Why weak**: gets exploited by Grim, AllD, and partially by
  Random. Even TFT-vs-AllC pairs leak a bit due to noise (TFT
  defects after a noise-flip of its own C → AllC doesn't care).
- **Real-world analogue**: unilateral disarmament. Sounds nice;
  only works if literally every counter-party is also nice. Even
  one defector in a population can drag AllC down to subsistence.

### bot_always_d — predator
- Score: 442.80 (#2 / 5).
- **Why strong here**: 2 of the 4 other bots are exploitable
  (AllC fully, Random partially). AllD scoops 970 vs AllC and
  577 vs Random — both massive transfers.
- **Why won't keep winning**: as we add real reciprocators, AllD's
  exploit cells will shrink. Reciprocators will play D back at
  AllD reliably; only AllC will remain a free meal. AllD's average
  will collapse.
- **Real-world analogue**: a one-shot scammer in a small village.
  Profitable until everyone learns to avoid you.

### bot_grim — eternal punisher
- Score: 456.67 (#1 / 5).
- **Why strong here**: rides AllC the same way AllD does (and even
  better, because Grim's noise-flips of its own C → D look like
  legitimate D's to AllC, who keeps cooperating, while Grim is now
  locked in D-mode).
- **Why fragile**: Grim self-play is 292.7. Grim-vs-Grim has the
  same noise problem as TFT-vs-TFT, but worse because there is NO
  recovery rule — first noise flip causes both to lock into DD
  forever.
- **Real-world analogue**: zero-tolerance / mandatory-minimum
  laws. They look stable on paper, but every false positive (every
  noise flip) creates a permanent breakdown. Cf. "diplomatic
  expulsion in retaliation for a single perceived slight" — entire
  alliance frameworks have collapsed this way.

### bot_tit_for_tat — minimal reciprocator
- Score: 409.13 (#3 / 5).
- **Why middling here**: doesn't exploit AllC (only 605, the noise-
  affected CC equilibrium), so it leaves "exploit profit" on the
  table relative to AllD/Grim. But also doesn't get exploited
  badly: TFT vs AllD = 210, the DD floor, vs AllC's 23.
- **Self-play under noise**: 498.7. Lost ~17% vs the 600 ceiling
  due to the CD-DC ringing that follows each noise flip. Still
  recovers.
- **Real-world analogue**: reciprocity-based diplomacy. Doesn't
  win the year a free-rider gets to feed off you, but also never
  collapses. Median in any given match; champion over long horizons
  in mixed populations.

### bot_random — coin flipper
- Score: 383.93 (#4 / 5).
- **Why surprisingly OK**: bots that defect get exploited by
  AllC's free-meal cells in a different shape. Random gets ~50%
  of those cells, which is half as exploitable but still positive.
  It also doesn't lock badly against AllD (it just half-cooperates,
  earning ~1 per round).
- **Why not a real strategy**: random has no causal structure, so
  no opponent can build trust with it. Its score is a smear across
  expected outcomes, never the best in any single cell.
- **Real-world analogue**: erratic policy. Predictable enough to
  be safe to ignore, but not coordinated enough to win anything
  big.

## Hypotheses for next strategies

Based on the dynamics above, the most leverage comes from:

1. **A reciprocator that resists self-play noise better than TFT**.
   Tit-for-Two-Tats (TF2T) is the canonical answer: only retaliate
   after TWO defections in a row, which absorbs single noise flips.
2. **A reciprocator that detects and exploits genuine AllD-style
   opponents**. Pure TFT just mirrors AllD into DD; if the bot
   could detect "this opponent is unilaterally hostile" it could
   stop wasting C's on warm-up rounds and still lock the DD floor.
3. **A bot that can apologise for its own noise-flips** (Contrite
   TFT). This is the smart-forgiveness lesson from earlier
   generations: forgive only when you can attribute the trouble
   to your own noise.

The first bot I will add is **TF2T**, because:
- It's the cleanest test of "tolerate single defection, punish
  doubles".
- It's the simplest possible deterministic noise-absorber. Sets a
  baseline for any randomised forgiveness rule (GTFT, CTFT) we
  add later.
- Its weakness (vulnerability to structured 2-period attacks) is
  worth measuring before more complex bots are added.

## After Run 002 (TF2T added)

### bot_tf2t — tolerant reciprocator
- Score: 431.83 (#2 / 6). Entered just below TFT.
- **Noise robustness confirmed**: TF2T self-play 587.3 vs TFT
  self-play 498.7 — TF2T saves ~90 points (~15% of CC ceiling)
  by absorbing single-noise-flips without retaliating. That's
  the entire reason it would beat TFT in pure self-play.
- **Why TFT still beats it overall**: TFT exploits TF2T's
  tolerance by ~0.7 points per match (600.7 vs 600 CC ceiling
  when playing each other). Tiny but real, and TFT does the
  same against AllC, getting a small surplus everywhere it can.
  Sum of small surpluses over 6 opponents > TF2T's pure-self-
  play advantage.
- **Real-world analogue**: a country with a 30-day cure-period
  for treaty violations vs. a country that retaliates on day 1.
  The cure-period country plays nicer with its own kind, but
  loses small amounts of leverage to the day-1 retaliator at
  every transient violation.

### Important meta-observation

**Adding ONE bot reshaped the rankings dramatically.** TFT moved
from #3 to #1 without any internal change, simply because adding
one more reciprocator added a high-yield mutual-cooperation cell
to its row average. This is the "ecology, not strategy" lesson
in miniature: a strategy's score is a function of the *bot pool*
in which it lives, not just its own logic.

Implication: I should be very careful when claiming "X is the
best strategy". The honest statement is "X is the best strategy
*in this current pool*". Convergence will only be meaningful once
the pool contains a representative range of opponent types.

## Hypotheses queued for next runs

- **Generous TFT** — randomised forgiveness baseline (next).
- **Contrite TFT** — smart forgiveness (apologise only for own
  noise flips).
- **Adaptive TFT** — long-window coop-rate detector + short-window
  tactical tolerance.
- **Gradual** — escalating punishment.
- **Hard / Soft Majority** — frequency-based responder.
- **ZD strategies** (equalizer, extortion) — Press-Dyson 2012.
- **Alternator / Cycle detector** — adversarial test + counter.

The plan is to add one per run, observe matrix shifts, retire
losers to `_failed/` if they fail to beat any incumbent.

## After Run 003 (Pavlov added)

### bot_pavlov — payoff-sensitive Win-Stay-Lose-Shift
- Score: 472.86 (#1 / 7). Took the lead from TFT.
- **Best self-play in the field** (580.0). Mechanism: when noise
  desyncs the pair, one side experiences (D,C) = T = win and stays
  D; the other sees (C,D) = S = loss and shifts to D; both then
  see (D,D) = P = loss and shift back to C. Recovery: 1-2 rounds,
  vs TFT's 2-round CD-DC ringing.
- **AllC predator** (789.7 vs AllC). Same mechanism as Grim: a
  noise flip of Pavlov's C → D lands at (D,C) = T = win, so Pavlov
  reads "I won by defecting → keep defecting". Pavlov then plays
  D against AllC's continued C until the next noise event.
- **Catastrophic vs AllD** (119.7, *below* the DD floor). Mechanism:
  AllD plays D always. Pavlov: round 1 C → S → shift D; round 2 D
  → P → shift C; round 3 C → S → shift D. So Pavlov oscillates
  CDCDCD against AllD, getting 0+1 every 2 rounds (~0.5/round).
  Pavlov is structurally built to be exploited by unconditional
  defectors.
- **Real-world analogue**: "rules-based" diplomatic cultures. They
  cooperate happily when things go well, exploit obvious weakness,
  recover quickly from transient breakdowns — but get repeatedly
  suckered by counterparties who simply don't play the same game.
  Cf. trade negotiations where the rules-based side keeps offering
  partial concessions to a counterparty who never reciprocates.

### Meta-observation: Pavlov vs the four Axelrod principles
- **Nice?** No — exploits AllC under noise.
- **Retaliatory?** Yes — defects after S, stays D after T.
- **Forgiving?** Yes, instantly — after DD shifts back to C.
- **Non-envious?** Indifferent — Pavlov ignores opponent's score,
  only looks at its own last-round payoff.

So Pavlov is forgiving + retaliatory + not-nice. Compare TFT:
forgiving + retaliatory + nice. The non-nice axis costs Pavlov
the AllD column but earns it the AllC and Random columns. Net
win in this pool. **The "nice" axis is a tradeoff, not a
universal virtue: it pays only in pools where exploitable
opponents are rare and unconditional defectors are common.**

## Hypotheses for Run 004 — Generous TFT

GTFT: same as TFT, but after observing opponent's D, cooperate
with probability `g`. The Nowak-Sigmund canonical value is
g* = min(1 - (T-R)/(R-S), (R-P)/(T-P)) = min(1 - 2/3, 2/4) = 1/3.

Predictions:
- GTFT self-play under noise will improve on TFT's 498.7 (closer
  to TF2T's 587.3) because ~1/3 of the noise-flips get forgiven
  in a single round instead of triggering CD-DC oscillation.
- GTFT vs AllD will be slightly worse than TFT vs AllD (210.7),
  because the random forgiveness wastes ~1/3 of the response D's,
  scoring 0 each.
- GTFT vs Pavlov: interesting test. Pavlov's "exploit on loss"
  interacts non-trivially with random forgiveness.

If GTFT(1/3) beats TF2T in self-play but does NOT beat TFT overall,
it confirms that *deterministic* tolerance (TF2T) and *probabilistic*
tolerance (GTFT) leak similarly to predators, with GTFT slightly
worse because it can't be primed by opponent behaviour.

## After Run 004 (GTFT added)

### bot_gtft — Generous Tit for Tat, g = 1/3
- Score: 448.71 (#4 / 8). Entered just below TFT.
- **Self-play 583.7** — almost identical to TF2T (587.3), well
  above plain TFT (498.7). Confirmed: probabilistic forgiveness
  absorbs noise about as well as deterministic tolerance.
- **Leak to TFT confirmed**: GTFT vs TFT 573.7 / TFT vs GTFT
  583.7. ~10-point asymmetry per match, same shape as TFT vs
  TF2T (600.7 / 585.7). The deterministic-vs-stochastic
  distinction is irrelevant for this leak — what matters is
  that the forgiver doesn't make the retaliator pay anything
  back for its accidental D's. **The leak is a property of
  one-sided forgiveness, not of how the forgiveness is
  triggered.**
- **Catastrophic vs Grim** (157.0, *worse* than TFT vs Grim 272.3).
  Mechanism: once Grim locks into D, every forgiving C from
  GTFT scores 0; mirror-only TFT at least scores 1 per round.
  Forgiveness without target-detection costs you against
  unconditional defectors.
- **vs AllD: 143.0** vs TFT's 210.7. Same mechanism as vs
  Grim — wasted forgiveness against a fixed-D opponent.
- **Real-world analogue**: "we will keep extending the olive
  branch, every nth offer". Works against good-faith opponents
  who occasionally misread; fails against opponents who have
  decided unilaterally to defect. The fix is not to be more or
  less generous, but to *condition* generosity on detecting
  whether the opponent is actually reciprocating over a longer
  window. (That's the Contrite TFT / Adaptive TFT path.)

### Meta-observation: forgiveness has two distinct failure modes

1. **Leak-to-retaliators**: TFT, by retaliating once after a
   noise flip, banks ~10 points off GTFT/TF2T per match.
   Forgivers structurally subsidise non-forgivers.
2. **Wasted-on-locked-defectors**: against Grim or AllD, every
   forgiving move is a 0-point gift. GTFT pays this tax more
   than TF2T because GTFT's 1/3 probability fires regardless
   of opponent state; TF2T at least requires a single C from
   the opponent to reset.

A truly good forgiver must:
- Detect own-noise vs genuine-defection (Contrite TFT).
- Detect lock-in (Adaptive TFT / cooperation-rate monitor).
- Apply forgiveness only when own-noise was the cause AND the
  opponent is not in a fixed-D pattern.

This is the queue for the next 3-4 bots.

## After Run 005 (CTFT added)

### bot_ctft — Contrite Tit For Tat (standing-based)
- Score: 481.85 (#2 / 9). Entered directly into top-3 territory,
  6 points behind Pavlov.
- **Self-play 593.3** — beats every other strategy except literal
  AllC (601.0). Mechanism: when CTFT's own intended C is noise-
  flipped to D, it marks itself as "bad standing" and plays C the
  next round even after the opponent's retaliation. The ring CD-DC
  ends in exactly 3 rounds (D-C-C, total payoffs 5+0+3 = 8 vs 9 for
  pure CC). Compare TFT-self at 498.7 where the ring oscillates
  indefinitely.
- **Leak to TFT closed**: CTFT vs TFT 499.0 / TFT vs CTFT 507.3.
  TFT's edge is +8 (vs +15 to TF2T, +10 to GTFT). The remaining +8
  comes from the symmetric case CTFT cannot fix unilaterally:
  *opponent's* noise flip. CTFT retaliates, TFT mirrors, the ring
  starts. Closing this fully would require *both* sides to be
  contrite — i.e. a coordination/norms problem in real-world terms.
- **Nice but not naïve**: vs AllC, CTFT plays at 601.7 / 588.3, very
  close to the noise-affected CC ceiling. Unlike Grim (892.3 vs
  AllC) and Pavlov (789.7 vs AllC), CTFT does NOT systematically
  exploit AllC. Its contrition rule correctly classifies its own
  noise as "my fault" and plays C in apology, so the noise-driven
  exploitation pump that Grim/Pavlov enjoy never activates.
- **vs AllD: 205.0** (below the DD floor of 200 by a hair, but only
  because of CTFT's first-round C giving AllD a free 5). Same shape
  as TFT. CTFT does not have a detector to short-circuit the AllD
  warmup, so it pays the same ~5-point warmup cost as TFT.
- **vs Grim: 304.7** — better than TFT's 272.3 vs Grim. Mechanism:
  during the post-noise lock, CTFT correctly retaliates after Grim
  defects (Grim is in "bad standing" from CTFT's POV permanently
  after the lock event), and CTFT's standing-tracker correctly
  treats its own retaliation as legitimate. The 32-point gap to TFT
  is because TFT's own noise flips after the lock waste C-against-D
  rounds (each costing 5 vs DD floor 1), whereas CTFT's
  apology-after-own-flip still costs 5 but is followed by a single
  C+D=0 round instead of TFT's full CD-DC cycle which costs 0+5+0+5
  = 10 over 4 rounds. CTFT's apology rule trims this to 0+5 = 5
  over 2 rounds.
- **vs Pavlov: 494.3 / 502.7** — almost balanced. Both have strong
  recovery mechanisms; neither can exploit the other.
- **Real-world analogue**: a diplomatic culture that publicly owns
  its own mistakes. The "I'm sorry, that was an error on our end"
  norm closes the asymmetric leak that strict reciprocity allows.
  Contrast: post-WW2 German Wiedergutmachung culture (explicit
  ownership of historical defection) vs. cultures with weaker
  apology norms — long-run trust and trade asymmetries differ
  measurably. The IPD version shows the mechanism: own-noise
  contrition is unilaterally achievable; it does not require the
  opponent to be contrite, and it captures most of the upside.

### Meta-observation: Pavlov vs CTFT, the two "leaders"

Both top bots have near-ceiling self-play (Pavlov 580, CTFT 593)
and recover from noise quickly. They differ on the *nice* axis:

- Pavlov is **not nice**: it exploits AllC and Random.
- CTFT is **nice**: it refuses to exploit AllC.

In a pool with 2 exploitable bots (AllC, Random) and 7 reciprocators,
Pavlov's not-nice axis is worth +6 points overall vs CTFT. If we
add more reciprocators (Adaptive TFT, Detective, Gradual), Pavlov's
advantage from naive bots should erode further and CTFT may take
the lead. **The leaderboard is a function of the niceness ratio of
the pool**: the more reciprocators present, the more "nice" pays.

### Meta-observation: forgiveness vs contrition

The two ways to absorb noise:

1. **Forgiveness** (TF2T, GTFT) — let the opponent off the hook
   for one D. Asymmetric: costs the forgiver, benefits the
   forgiven. Leaks to non-forgivers (TFT) and locked defectors
   (Grim, AllD).
2. **Contrition** (CTFT) — apologise for your *own* perceived D.
   Symmetric in self-play. Closes the leak to TFT. Does NOT fix
   the opponent-side noise case unless the opponent is also
   contrite.

Contrition strictly dominates forgiveness when only one's own
errors need correcting (the typical noise model). Forgiveness has
a niche when the opponent might be coming back to cooperation
after a deliberate defection and one wants to seize the recovery
fast — but this rarely happens in practice in this pool.

Real-world: unilateral apologies and acknowledgement of fault are
strictly better than unilateral forgiveness for stabilising
cooperation under observation noise. The political analogue is
"sorry, we are recalling our diplomat for the error in the cable"
beats "we will overlook your shelling of our outpost". The first
removes the asymmetry; the second invites repeat exploitation.

## Hypotheses queued for Run 006+

- **Adaptive TFT** — measure opponent's cooperation rate over
  a window; if it falls below threshold, switch to AllD;
  otherwise play TFT. Predicted to beat plain TFT against
  AllD/Grim columns. **NEXT**.
- **Gradual (Beaufils)** — escalating punishment with cooldown.
  Predicted to deter exploiters while permitting recovery.
- **Hard Majority** — D if opp's defection count > cooperation
  count; else C. Predicted middling; tests whether bulk-
  frequency signals beat last-move signals.
- **Soft Majority** — C if opp's C count >= D count; else D.
  Marginally more forgiving; tests sensitivity to threshold.
- **Detective** — play C,D,C,C in the first 4 moves to fingerprint
  opponent; switch to AllD if opp didn't punish the D, else TFT.
  Predicted to beat both AllC-exploiters and TFT-family in
  mixed pools.
- **ZD-extortion** (Press-Dyson 2012, x=2) — enforce a linear
  payoff relation favourable to itself. Predicted to win
  pairwise but lose in self-play.

## After Run 006 (ATFT added)

### bot_atft — Adaptive TFT (window=20, threshold=0.20)

- Score: 476.10 (#3 / 10). Entered just below CTFT, above the
  rest of the reciprocator block.
- **Detector triggers cleanly against AllD/Random**: opp coop
  rate from these two sits at noise floor (~2-50%), well below
  0.20 for AllD. The lock-D mode prevents wasting C's on noise-
  flipped D's from AllD. The gain is modest (~2 points/match vs
  AllD), because the cost TFT pays for mirroring noise C's is
  also modest at noise=0.02.
- **Self-play 509.0** — only ~10 points above TFT-self (498.7).
  No real improvement; the detector never trips against another
  ATFT under normal noise. ATFT is *not* a self-play optimisation;
  it is a defector-detection layer on top of TFT.
- **vs Grim: 250.0** — SURPRISINGLY worse than TFT vs Grim (272.3).
  Mechanism (see Lesson 012 below): after Grim locks D and ATFT
  detects, ATFT plays pure D and gets the DD floor (1/round).
  TFT, by contrast, keeps mirroring Grim's *noise-flipped* C's
  with a C response — score 0 that round but then score 5 the
  next round when Grim's continued D meets TFT's mirror-of-C =
  C... wait, no. Let me re-trace. After Grim locks D and TFT
  mirrors:
    - Grim plays D (intended), TFT plays D (mirror): score 1/1.
    - Grim's D noise-flipped to C (rare, ~2%): TFT mirrors prev
      D = D, score 5/0 to TFT.
    - Next round: TFT mirrors C, plays C; Grim plays D: score 0/5.
  Net over 4 rounds containing one Grim noise flip:
    - rounds k-2, k-1: DD = 1+1 = 2 for TFT.
    - round k (Grim flipped to C, TFT plays D from prev D):
      D+C = 5 for TFT, 0 for Grim.
    - round k+1: TFT mirrors C, plays C; Grim plays D: 0 for TFT.
  So 4 rounds: TFT gets 1+1+5+0 = 7, average 1.75. Without the
  flip, TFT gets 4 (1×4). With noise=0.02, expected flips per 200
  rounds is ~4 on each side; each gives TFT an extra ~3 points.
  Plus Grim's own D-events that get noise-flipped to C have the
  same shape. Total bonus over 200 rounds: ~24-30 points. Matches
  the TFT-vs-Grim 272.3 = DD floor 200 + ~70 noise bonus.
  ATFT, locked in D, gets none of this bonus. 250 ≈ 200 + 50 (the
  pre-lock rounds where ATFT still mirrors).
- **vs Pavlov: 526.7 (3 repeats) → ~473 (10 repeats)**. Possibly
  marginal improvement over TFT vs Pavlov (~446 at 10 repeats),
  but noise variance is high enough that the gap might be 0-20
  not 80. ATFT may not really beat TFT here once seed variance
  is averaged out.
- **Real-world analogue**: a country that explicitly characterises
  its counterparty as a "structural defector" (label X as a rogue
  state, sanction them, refuse all engagement) and stops responding
  to any of their cooperative gestures. Saves the cost of being
  pulled into one-off engagements that go nowhere. But — Lesson
  012 — *also gives up the upside of opportunistic cooperation
  when the counterparty makes a token concession*. Mirror-only
  TFT can occasionally pocket those concessions; lock-D ATFT
  forgoes them. Whether that matters depends on whether the
  counterparty's noise is genuinely random or signals real
  willingness to cooperate. The model can't distinguish, but
  real-world political analysis often can.

### Meta-observation: detector-based bots can pay an "abstention tax"

Two effects from the ATFT run:

1. **Against unambiguous defectors** (AllD), the detector gain is
   small because the noise events the detector avoids cost very
   little to a TFT mirror anyway (5 points per event).
2. **Against locked defectors with internal noise** (Grim), the
   detector LOSES points because it abstains from a profitable
   side-game (Grim's noise C's → free 5 for the mirror).

The combined effect is a wash on the AllD/Grim columns. ATFT's
real benefit in the current pool is more cooperators get a high-
yield CC cell (TF2T, GTFT, AllC all picked up +10-15 points from
having ATFT in the pool). So **ATFT enters the top-3 not by
beating defectors better but by being a clean cooperator in
mutual play**. The defector-detection is more of a hygiene
feature than an offensive weapon at the current noise level.

If we raised noise to 0.10, the detector would matter more
(noise-induced false-defections would be more common and TFT-
style mirroring would waste more rounds). Worth re-running
later with a noise sweep.

### Hypotheses for Run 007+ (queued, refined)

The current pool has saturated reciprocators (5+ near-identical
top scores). To open up new dynamics we need either:

a) An aggressive opportunist (Detective, ZD-extortion) that
   exploits one slice of the reciprocator pool.
b) A pattern-based bot (Soft Majority, Hard Majority) that uses
   bulk statistics instead of last-move triggers.
c) A noise-aware contrite hybrid (CTFT + ATFT combo).

**Gradual (Beaufils 1996) is queued next**. It uses escalating
punishment: on the n-th opp defection, retaliate with n D's, then
play 2 C's to "reset". The interest is whether escalation
deters AllD-style behaviour better than the constant 1-D
retaliation of TFT, at the cost of slower recovery from noise.

Predicted: Gradual will be a non-monotone curve — good vs
opportunists (D-then-recover patterns), middling vs AllD,
slightly worse than TFT in self-play because each accumulated
noise flip permanently raises the future punishment count.

## After Run 007 (Gradual added)

### bot_gradual — Beaufils escalating punishment

- Score: 421.97 (#10 / 11). Just above AllD, just below Grim.
- **Self-play 308.3** — far below TFT-self (498.7) and TF2T-self
  (587.3). The cascade prediction was right: each noise flip
  permanently increments BOTH copies' escalation counters, so
  after a dozen flips on each side both are deep into the
  ramp. By round 100 they spend more rounds in mid-burst D than
  in calming C, scoring at ~DD-floor + small calming-tail
  contributions.
- **vs AllD 181.3** — BELOW the DD floor of 200. The escalation
  matches AllD's D's most of the time (DD = 1 each), but the
  mandatory 2-C calming tails are pure 0-point gifts to an
  unrepentant defector. Over a 200-round match with ~30
  escalation cycles, ~60 rounds are "C vs D = 0 to me, 5 to
  AllD". Gradual's mechanism *assumes* the opponent will read
  the calming-C signal and reciprocate. AllD does not. The
  signal is wasted.
- **vs AllC 609.3** — surprisingly close to the CC ceiling.
  Noise-triggered "false defections" from AllC are rare enough
  (~4 per 200 rounds) that even with escalation (bursts of 1, 2,
  3, 4 D's plus 2 C's each), only ~18 rounds are non-CC. The
  rest is mutual cooperation at 3 each. So Gradual *almost*
  preserves AllC-cooperation, except for accumulating burst
  costs. **Note**: this is a structural advantage of Gradual
  over Pavlov and Grim, both of which exploit AllC heavily.
  Gradual at least is "nice" in the Axelrod sense.
- **vs Pavlov 551.0** — Gradual wins big vs Pavlov (which only
  scores 261.0 in return). Mechanism: Pavlov's WSLS oscillation
  desynchronises against Gradual's structured burst-then-calm
  pattern. Gradual's D-bursts hit Pavlov's C's directly (T=5
  each); Gradual's calming C's land on Pavlov's D's (S=0 to
  Gradual, but only briefly, then escalation resumes). Pavlov
  can never settle into mutual CC because the bursts repeatedly
  shift it. **This is the cell that knocked Pavlov off the top.**
- **vs Random 564.0 / 229.0** — Gradual hugely outscores Random.
  Random's 50% D-rate triggers escalating punishment in ~3-4
  rounds and we stay in D mode most of the game. Random has no
  way to coordinate calming windows, so it eats D's continually
  while Gradual occasionally catches Random's C with its own
  burst-D = +5 for Gradual.
- **vs Grim 242.3** — slightly worse than TFT (272.3) vs Grim,
  better than ATFT (250.0) vs Grim. Once Grim locks, Gradual
  escalates against the lock, eventually plays mostly D (DD = 1
  each), but the mandatory 2-C calming tails still leak some
  S=0 cells.
- **Real-world analogue**: a state that uses "graduated
  reciprocity" (escalating sanctions per provocation, with
  goodwill gestures after each round). Brittle under noise: each
  misperceived signal permanently raises the next sanctions
  ceiling. Works against unitary actors who interpret the
  goodwill gestures correctly (i.e. mostly cooperators); fails
  against actors who simply don't decode the signal (AllD-like)
  or who have their own oscillation logic (Pavlov-like). The
  political analogue is the unilateral détente cycle in cold-
  war politics: each calming gesture matters only if the
  counter-party reads it as such. The Cuban Missile Crisis
  hotline was a *bilateral* commitment to read each other's
  calming signals correctly — Gradual is unilateral and pays
  for that asymmetry.

### Meta-observation: ONE bot, TWO leadership swaps

Pavlov went from #1 to #2 after Gradual entered — purely because
of ONE cell, Pavlov vs Gradual = 261.0. No other bot in the pool
exploits Pavlov this badly. This is "ecology, not strategy" in
its purest form: Pavlov's strategy did not change, but the
ranking did, because the pool added a counter-strategy that
specifically targets WSLS's oscillation pattern.

The lesson for the real world: a country's "rules-based" strategy
(Pavlov-like, rewarding cooperation and punishing defection in
short cycles) is robust until a structurally different actor
enters the game. Then the rules-based actor doesn't lose because
its rules became worse — it loses because the rule-set is wrong
for the new opponent. This is the IPD version of "Vietnam after
nuclear deterrence" or "asymmetric warfare against modern
militaries".

### Meta-observation: nice-but-cascading vs nice-and-fast-forgiving

CTFT and Gradual are BOTH "nice" in Axelrod's sense (never first
to defect). But CTFT recovers from noise in 2-3 rounds, while
Gradual *escalates* on each noise event and never resets the
counter. The result: CTFT wins #1, Gradual sits #10. **Niceness
without bounded retaliation is fragile under noise.** The Axelrod
principle "be retaliatory" must be balanced by "be forgiving" —
Gradual is too retaliatory.

The real-world version: forgiveness must be *bounded in time*,
not bounded in count. "I will forget defections older than X
years" stabilises long relationships; "I have not yet retaliated
enough for what you did 20 years ago" destabilises them. Reading
20th-century European politics through this lens is instructive.

## Hypotheses for Run 008+

The pool now has 11 bots with a clear structure: 5 reciprocators
clustered at the top (CTFT, Pavlov, TF2T, ATFT, GTFT in 16-point
band), 1 close reciprocator (TFT) trailing, 1 friendly cooperator
(AllC), and 4 punished bots (Random, Grim, Gradual, AllD). To
diversify, we need new shapes:

- **Soft Majority** — defect iff opp's D > opp's C cumulatively.
  Bulk statistics, slow trigger. Predicted to land near AllC in
  score but with much better behaviour vs AllD/Grim. **NEXT**.
- **Hard Majority** — defect first, switch to TFT once opp's C
  ≥ D. Different starting position; tests "guilty until proven
  innocent" prior.
- **Detective** — fingerprint sequence then branch on response.
  Likely a top-3 disruptor.
- **ZD-extortion** — Press-Dyson linear-payoff enforcer.
- **Tester / Provocateur** — early D probe then revert to TFT.

Need at least 4 more non-pantheon bots to reach the 10-non-trivial
threshold. Plan: Soft Majority, Hard Majority, Detective, and
either ZD-extortion or a custom hybrid as the 10th non-trivial.

## Run 008 — Soft Majority lands at #1

The result exceeded the hypothesis. Predicted "near-AllC level".
Actual: #1 outright at 502.89, +12.0 above CTFT.

### Why Soft Majority wins

The bot's rule is trivial: cooperate unless opp's cumulative D
count > cumulative C count. Yet it dominates a field of
sophisticated reciprocators. The mechanism is a combination of
three properties:

1. **Maximally nice in the Axelrod sense.** Soft Majority NEVER
   defects first — at round 1 the rule says "0 D's, 0 C's, so D
   is not > C, cooperate." Many "nice" bots (TFT, GTFT, TF2T,
   ATFT) start with C as a hard-coded first move. Soft Majority
   starts with C as the *consequence* of its scoring rule, which
   makes it equally nice but more principled.

2. **Highly noise-tolerant.** A single flipped D in a sea of
   C's never trips the rule (1 D vs ~199 C's still has D < C).
   Compare to plain TFT, which retaliates on every flipped D
   immediately. Soft Majority's tolerance is *unbounded in time*
   — even an early D from the opponent doesn't matter as long as
   later C's outnumber it.

3. **Eventual D-lock against persistent defectors.** Against AllD
   the D-count exceeds C-count after exactly 1 round, and Soft
   Majority defects forever after. Against bots that defect
   *more than half* of the time on average (e.g. Random), Soft
   Majority transitions to D in a few rounds and stops bleeding.

The key insight: this is a *self-calibrating* threshold. TFT-
family bots have a fixed lookback window (1, 2, or 3 rounds).
Soft Majority has an *adaptive* window that grows with history,
giving it the right amount of patience for each opponent. With a
cooperator, the patience is effectively infinite; with a
defector, the patience runs out in 1-2 rounds.

### Where Soft Majority loses

Two specific weakness cells:

- **vs Pavlov (504.0 cell)**: only ~80% of the CC ceiling.
  Pavlov's WSLS oscillation hits Soft Majority with bursts of
  D's. Each Pavlov D is a S=0 cell for Soft Majority. But
  Soft Majority's tolerance is so high that it absorbs them
  without retaliating, which means Pavlov keeps oscillating
  (because Pavlov shifts on S=0). The pattern is a steady leak
  rather than a catastrophe. Pavlov is the only reciprocator
  that scores < 580 against Soft Majority.

- **vs Gradual (550.3 cell)**: Soft Majority gives up ~45 points
  here too. Gradual's escalating bursts are short enough that
  Gradual's own profile remains majority-C from Soft Majority's
  POV (each burst-of-N D's is followed by 2 C's plus the long
  intervening CC runs). So Soft Majority never flips its rule
  and keeps absorbing the bursts. Gradual gets its highest cell
  anywhere at 623.7.

These are the *exact* failure modes of bulk-statistics rules:
they don't react fast enough to **structured exploitation
patterns** even when the *rate* of defection is high. A
Pavlov-style oscillator can keep extracting T=5's because its
short bursts of D never push the cumulative statistic past
the threshold.

### Real-world analogue

Soft Majority is "the patient democracy" or "the long-term
business partner": it judges you by your total track record,
not by any single transgression. Misperceptions, single bad
calls, occasional rudeness — all get absorbed as long as the
long-run pattern is cooperative. Persistent bad actors do
eventually get the cold shoulder, but only after enough
evidence accumulates.

This works brilliantly in low-stakes social and economic
networks where most participants are mostly cooperative. It
fails against actors who *systematically* exploit while
maintaining a surface of cooperation (Pavlov, Gradual): in
geopolitics, the analogue is a state that maintains formal
diplomatic relations while running covert exploitation. A
Soft-Majority counterpart can't see through the surface.

### Lesson for the four Axelrod principles

Soft Majority's success refines our reading of the principles:

1. **Nice** ✓ — never defects first, ever.
2. **Retaliatory** — yes, but with a high threshold. The bot
   IS retaliatory, but only against majority-D opponents. This
   tells us Axelrod's "retaliatory" is best read as
   *eventually* retaliatory, not *immediately* retaliatory.
3. **Forgiving** ✓✓ — the most forgiving of all non-AllC bots
   in the pool. Forgives any past D as long as future C's
   restore the majority.
4. **Non-envious** ✓ — Soft Majority literally doesn't track
   its own score, only opp's cooperation rate.

The principle Soft Majority does NOT have, that TFT-family
bots do, is **provocability** (Axelrod's term — be quick to
provoke when wronged). Yet it still wins. The takeaway: in a
noisy, mostly-nice population, *unprovocable forgiveness with
a long-run defector trigger* beats *immediate provocability*.

## Hypotheses for Run 009+

The pool now has 12 bots. Soft Majority dominates by being
*more forgiving* than the TFT-family bots while still
defending against permanent defectors. Two ways to dethrone it:

- **Hard Majority** (queued) — direct opposite. Predicted to
  lose because it pays the first-D tax against every reciprocator.
- **Detective** — fingerprint at start. If opp punishes, become
  TFT. If opp tolerates, exploit. This is the bot most likely
  to beat Soft Majority because Detective's first-D probe
  would extract T=5 from Soft Majority (which absorbs it) and
  then transition to AllC mode against it. Detective vs Soft
  Majority cell: ~3*199 + 5 = 602, close to the max.
- **Adaptive grim-relaxed** — like Grim but unlocks after N
  rounds of mutual C from opponent.
- **Pavlov-variant** that doesn't oscillate against Soft
  Majority. A "stabilised Pavlov" that adds a TFT fallback
  when it detects oscillation in its own history.

The interesting question: is Soft Majority robust to a probing
attack? Detective is the next bot to find out.

## Detective (Run 009) — the partial answer

Detective debuted at #5 (480.62), well below Soft Majority's #1
(508.85). The probe-and-exploit design *works* against the targets
it was meant for:

- **vs AllC: 779.7** (TFT got 605.7 against AllC). +175 from
  alternation extraction. Detective doesn't just CC with AllC; it
  banks T=5 every other round.
- **vs TF2T: 715.7** (the highest cell in TF2T's column). Detective's
  alternation hides under TF2T's "two consecutive D's" trigger.
- **vs Soft Majority: 605.3** — the **highest cell anyone has
  scored against Soft Majority in any run**, beating CTFT's 606.0
  from Run 008 by a hair (effectively a tie). Detective's R1 D
  successfully extracts one free T=5 before SM's tally re-balances.

But Detective fails on three dimensions:

1. **Provocation cost**: Detective LOSES R2-R3 against Grim, AllD,
   and TFT-like opponents. Those S=0 cells in the probe come back
   as ~200 cells, dragging the row down.
2. **Self-play penalty**: 448.0 (vs predicted 598). Noise during
   probe causes one Detective to misread the other as "tolerant"
   ~4% of the time, after which alternation against a TFT-mode
   peer creates DC-CD oscillation. The expected loss compounds
   over 200 rounds.
3. **Cell-propagation backfire**: Detective's 779.7 cell against
   AllC pulled AllC's row down by -11.3, and its 715.7 cell against
   TF2T pulled TF2T's row down by -6.4. These don't directly hurt
   Detective, but they reshuffle the *column* averages that
   Detective competes against. The relative rank gain is smaller
   than the absolute exploitation gain.

### Why Soft Majority still wins

Soft Majority's 580.3 cell against Detective is only ~25 points
below its row average. Why? Detective's TFT fallback (because SM
defected in probe at R2) means Detective behaves as TFT for 197 of
200 rounds against SM. That's effectively a "TFT-with-1-free-T5"
matchup, which is +5 over a pure TFT-vs-SM cell. Detective gets
+25 above the reciprocator block (605 vs 582), but SM only loses
~10 from this cell compared to its other reciprocator cells.

The asymmetry: in a 13-bot pool, a +175 cell against AllC contributes
+175/13 = +13.5 to row average. A −168 cell against Grim contributes
−168/13 = −13. They cancel out. Soft Majority's much steadier row
(no cells below 200, no cells above 600 except its own AllC cell)
beats Detective's high-variance row by virtue of having FEWER
floors, not by having MORE ceilings.

### Lesson for Run 010+

A probe-and-exploit bot needs to **minimise probe cost** to be
profitable. Options:

- **Late probe**: play TFT for first 30 rounds, then probe with a
  single D. By round 30, retaliators have already shown themselves
  (noise has triggered DD spirals or stayed in CC). The probe only
  fires against opponents that have been pure-C for 30 rounds —
  almost certainly forgivers. Banks exploit cells without paying
  upfront cost against Grim/AllD.
- **Conditional probe**: probe ONLY if opponent's first-K moves are
  all C. This is essentially a Pavlov-with-extra-signal variant.
- **Soft probe**: instead of D, send a single "test" pattern that
  doesn't directly trigger TFT — e.g., play exactly D in round 1
  AND C in round 2 AND check whether opponent's R2 move was
  forgiving (i.e., still C). If R2 was D, restart from CC. If R2
  was C, probe deeper.

The next bot, **Shadow**, will implement the "late probe" variant.

## Hypotheses for Run 010+

- **Shadow** (queued) — TFT for first 30 rounds, then probe-and-
  exploit if opponent's cooperation rate is high. Predicted to:
  - Match TFT or CTFT against reciprocators in the first 30 rounds
    (no provocation cost).
  - In the post-probe phase, extract some T=5's against AllC, TF2T,
    Soft Majority, but only ~170 rounds of exploit (vs Detective's
    197), so smaller absolute gain.
  - Self-play: 30 rounds of mutual CC, then probe phase causes
    the same chaos as Detective — net likely similar to TFT vs TFT
    (~498).
  - Row average prediction: ~500-510, possibly overtaking Soft
    Majority.

- **Hard Majority** (still queued) — control test for the "first-D
  tax" hypothesis. Should be a net loser. Run as a falsification
  test of the Run 008 lesson.

- **Adaptive Grim** — Grim that relaxes after K rounds of mutual C.
  Should fix Grim's biggest weakness (the noise-triggered permanent
  lock-in) and likely place near the reciprocator block.

## Shadow (Run 010) — what the late probe actually buys

Shadow tested the **"minimise probe cost"** hypothesis from
the Run 009 lesson. The bet was that running TFT for 30 rounds
before the probe would (a) keep cells against Grim/AllD/TFT/CTFT
near the reciprocator block (no upfront provocation) and (b)
preserve the AllC/TF2T/SM exploit by probing once at round 30.

Result: a mixed report card.

### What worked

- **Soft Majority exploit**: 632.7 (Detective: 605.3, TFT: 605.3).
  Shadow extracts an extra +27 from SM by running TFT for the
  first 30 rounds (banking ~85 mutual CC points), then alternating
  D/C while SM's tally stays C-heavy. Detective's early provocation
  cost ~30 points against SM compared to Shadow. **This is the
  cleanest demonstration that "late probe + sticky tolerant
  opponent" beats "early probe + same tolerant opponent".**
- **Self-play**: 592.3 (Detective: 448.0, TFT: 498.7). The sync
  detector ("two synchronized mutual D's → permanent C") is the
  single best self-play recovery mechanism we've built. Two
  Shadow bots reach mutual CC by round 37 in 85%+ of matches,
  losing only ~7 points to the recovery transition.
- **vs AllC and TF2T**: 718.0 and 631.7 — close to Detective's
  cells (779.7 and 715.7) but 30 rounds shorter on the exploit
  phase. Predictable.
- **vs Grim and AllD**: 247.0 and 210.3 — roughly equal to
  Detective's cells, not better. Shadow's "no upfront probe"
  doesn't save against Grim because the round-30 probe still
  fires when opp_d_rate is low, and Grim's pure-C means
  opp_d_rate stays at ~0.02 through round 30. **The "late
  probe" theory failed to predict that Grim looks identical to
  AllC for the first 30 rounds (no D events), so Shadow probes
  Grim too.**

### What broke

- **vs CTFT**: 448.7 (TFT vs CTFT: 507.3, Detective vs CTFT:
  560.0). Shadow's post-probe fallback is plain TFT. Plain TFT
  against CTFT in noise produces persistent oscillation
  because CTFT's contrite logic is one-sided — it forgives its
  own noise-D's but not the opponent's TFT retaliation chains.
  Detective's probe-revealed-retaliator-mode is identical to
  Shadow's, but Detective's *interaction history* with CTFT
  doesn't include a probe at round 30 — the probe was rounds
  0-2 and produced a single short retaliation cycle. Shadow's
  round-30 probe arrives after 30 rounds of mutual CC, where
  the CTFT/Shadow standing-pair is **G/G**. Shadow's D pushes
  itself to B-standing → CTFT plays D in round 31 → my test
  phase plays C → CTFT plays C in round 32 (we're now G/G
  again) → test passes count(D)==1 → revert to TFT. From
  here on, TFT vs CTFT in noise is the same as TFT vs TFT in
  noise minus a tiny CTFT-side noise correction. The cell
  averages ~448.
- **vs ATFT**: 437.3 (Detective: 491.7). Same mechanism: ATFT
  is an adaptive TFT variant that adjusts trust over time;
  a single mid-game probe causes a long trust-decay, and
  Shadow's TFT fallback doesn't repair.
- **vs Gradual**: 318.7 (Detective: 310.7). Gradual's
  escalating retaliation against the probe is harsh — Gradual
  responds to my round-30 D with a multi-round D burst, and
  Shadow's TFT fallback gets caught in that burst.

### Lesson for Run 011

The "**late probe**" idea is sound but **the post-probe
fallback must be CTFT (or some other contrite/forgiving
strategy), not plain TFT**. Reverting to plain TFT after a
mid-game disturbance is the worst of both worlds: it
provokes some retaliation rounds, then doesn't apologise.

Concrete fix idea: a **Shadow-CTFT hybrid**. Phase 1 (rounds
0-29): CTFT instead of TFT. Phase 2 (round 30): same probe
condition. Phase 3 (test): same. Phase 4 (fallback): CTFT
again with the probe move retroactively treated as "my own
noise-D" (so my standing stays G). Phase 5 (exploit): same
D/C alternation with sync detector.

That bot has not been written yet. It's a viable Run 011
candidate. The other strong candidate is **Adaptive Grim**:
fix the Grim noise-trigger by adding a "K consecutive mutual
C's → unlock and forgive" rule. Adaptive Grim should rank
near the top because its only weakness in the existing
matrix (cells against Detective, Shadow, and noise) are
fixable in a single mechanism.

## Hypotheses for Run 011+

- **Adaptive Grim** (highest expected gain): fixes Grim's
  noise trigger, predicted to land in the top-3 reciprocator
  block (480-500 row mean) and potentially displace ATFT or
  TF2T.
- **Contrite Shadow**: fixes Shadow's CTFT/ATFT cells,
  predicted to climb from #7 to #3-5. Doesn't change the
  top-2 (SM, CTFT).
- **Hard Majority**: still a useful control to confirm the
  "first-D tax" finding from Run 008. Predicted bottom-half.
- **Master Detective**: Detective with a CTFT fallback
  (similar to Contrite Shadow but with the early probe
  preserved). Predicted to land #4-5.

## Adaptive Grim (Run 011)

### Design
- K=10 D's, then PROBE=2 C's, then forgive if ≥FORGIVE=1 of opp's
  probe replies was C; else repeat the cycle.
- Same trigger as Grim (first D from opp during cooperate phase).
- Stateless — mode reconstructed from `opp_history` each call.

### Observed (Run 011)

- Row mean **456.40** (#10). Below predicted 480-500 range.
- Bright cells: AllC 650, Pavlov 550, GTFT 550, Random 518, TF2T
  548, Shadow 518, CTFT 520, TFT 516, Detective 509.
- Dark cells: Soft Majority 338, Gradual 310, Grim 240, AllD 184.
- Self-play 432: noise events on either side cause one-side
  triggers; both eventually trigger; FORGIVE=1 lets them re-sync
  ~13 rounds after a noise event.

### What works
- **Recovery from noise events** against soft reciprocators
  (TFT, CTFT, GTFT, ATFT, TF2T, Shadow). Vanilla Grim's cells
  vs these were 227-505; AGrim's are 463-548. The fix is
  exactly what the design predicted — periodic probes catch the
  reciprocator's willingness to return to cooperation.
- **Exploits noise-flipped C's into D's** against AllC and
  Random. AGrim's 650 vs AllC and 518 vs Random are higher
  than any pure-reciprocator's cell against those bots, because
  AGrim accidentally gets 10 free T-cells per noise event.
- **Self-play recovery** via FORGIVE=1: the staggered
  trigger episodes resolve in ~13 rounds instead of cascading
  forever (which a stricter FORGIVE=2 would cause).

### What doesn't
- **Soft Majority cell (338).** SM's tally-based reasoning
  doesn't care that AGrim's D-burst is "supposed to be" a
  finite punishment. Once the tally crosses, SM switches and
  never comes back, because AGrim's probe-C (2 rounds) is
  insufficient to flip SM's tally back. This is a *fundamental*
  conflict between cycle-based and aggregate-based reasoning.
- **Gradual cell (310).** Gradual escalates linearly with
  observed D-count, so AGrim's 10-D burst triggers a 10+ round
  D burst from Gradual. AGrim's probe-C is met with Gradual's
  D → forgive fails → cycle continues. Locked similar to SM.
- **Grim cell (240).** Vanilla Grim doesn't care about the
  intent of AGrim's cycle; one D triggers Grim's permanent D.
  AGrim's probe-C is met with D, locked.
- **AllD cell (184).** Worse than vanilla Grim's 207 because
  AGrim wastes 2/12 rounds per cycle on S=0 probes.

### Lesson

A periodic-probe forgiveness mechanism heals the **soft
reciprocator** subgraph (TFT-family) but fails against
**hard-state** opponents (Grim, Gradual) and **aggregate-state**
opponents (Soft Majority). The reason is asymmetric: AGrim's
probe-C signals "I'm willing to forgive if you are," but
hard-state opponents have already updated to a permanent D
state that no 2-round probe can dislodge.

A fix would require either:
1. **Variable-length probe** that extends the C-window if opp
   stays in D, e.g., 2-4-8 rounds. But this risks being
   exploited by AllD-like bots.
2. **Recognising the opponent type** in probe replies — e.g.,
   distinguish "ratchet retaliation" (Grim) from "tally-based"
   (SM) from "noise-flipped reciprocator" (TFT) and using a
   different forgiveness threshold for each. But this borders
   on opponent-modelling, which is heavy machinery.
3. **Lower K** (e.g., K=5) — shortens the punishment to avoid
   crossing SM's tally threshold. But this hurts vs AllD and
   weakens the deterrent signal.

Each fix trades one cell for another. The combinatorics suggest
no single-parameter Grim-variant can dominate the pool: the
trade-off space is too rough.

### Connection to real world

Adaptive Grim maps to **proportional sanctions with a sunset
clause**. Examples:
- **UN sanctions regimes with periodic reviews** (e.g., Iran
  JCPOA): impose long sanctions, periodically allow inspection
  / dialogue windows, lift sanctions if reciprocated.
- **Cold-War arms-control treaties with verification periods**:
  detente, then a verification regime, then re-escalation if
  the other side cheats.
- **Schoolyard "I'll stop hitting back if you say sorry"**:
  the same dynamic, but with single-shot probes.

The failure mode (Soft Majority cell) maps to **a stakeholder
who counts grievances rather than reading intent**: regardless
of how much the punishing party signals "this is a finite
punishment, here's a probe of cooperation," the stakeholder
remembers the punishment count and stays defensive forever.
Real-world example: a country that imposes broad sanctions on
another and offers periodic dialogue rounds may still be unable
to restore relations if the sanctioned population has lost
faith in any forthcoming reconciliation. Trust is built on
*recency* and *tone*, but some institutions update on
*aggregate*.

## Final synthesis (post-Run 011)

After 11 tournaments and 15 total bots (5 pantheon + 10
non-trivial), three structural conclusions:

1. **The reciprocator cluster wins on average.** Bots scoring
   456-493 are all variants of "cooperate-by-default,
   retaliate-once, forgive-if-reasonable" (CTFT, GTFT, TF2T,
   ATFT, Pavlov, TFT, Shadow, Detective, AGrim). The cluster
   is tight (37-point spread) because all these bots get
   ~580-600 against each other and ~150-220 against pure
   defectors. The differences are second-order — who has the
   best noise correction (CTFT), who is most forgiving (GTFT),
   who exploits naive cooperators best (Detective, Shadow).

2. **Aggregate-reasoning beats reactive reasoning at #1.**
   Soft Majority's #1 across runs 8-11 is not because it has
   bright exploit cells (it doesn't — its 580 cell against AllC
   is normal) but because it has *no* dark cells. SM scored
   208-251 only against AllD/Grim/Random, and 504-595 against
   everyone else. Its low variance wins by avoiding the long
   tail of bad cells that every reciprocator pays.

3. **Probe-and-exploit is a losing strategy in this pool.**
   Detective (#4) and Shadow (#6) and AGrim (#10) all use
   some form of "probe to learn opponent type, then exploit
   if safe." Their average is ~473 — below the pure
   reciprocators' 487 and well below SM's 503. The probe cost
   outweighs the exploit gains, and the post-probe trust
   loss compounds. This is the strongest evidence for
   Axelrod's NICE principle in our data.
