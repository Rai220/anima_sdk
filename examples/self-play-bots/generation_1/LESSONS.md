# Lessons learned (for future turns)

## Engine design

- **Noise must flip both the score AND the histories.** Otherwise the
  bot still sees its intended move and the noise model is incoherent.
  Done: `play_match` flips before appending to history.
- **Seed the global `random` module too.** `bot_random` uses
  `random.random()` from the global stream; without `random.seed(args.seed)`
  results vary between identical runs. Done at the top of `main()`.
- **Per-pair deterministic seeds.** Each (a, b, repeat_index) tuple gets a
  hashed seed for its noise RNG. This means matches are independent, and
  swapping bot order shouldn't change a pair's outcome distribution.
- **Self-play is included.** With N bots, self-play is 1/N of the average
  score — a bot's behaviour against a copy of itself matters a lot.
- **Repeat averaging is 3 by default.** With 200 rounds and noise=0.02
  the per-match variance is moderate; 3 repeats already gives a stable
  ranking. Bump to 5+ if results are noisy.

## Strategy insights

- Noise > 0 changes the equilibrium dramatically. TFT and Grim lose
  their edge because they can't recover from accidental defections.
- AllD is a strong baseline only when retaliatory strategies fail to
  forgive. The instant we add a single forgiving strategy that can
  detect and punish AllD, AllD's score should collapse.
- In small pools, who you play against matters as much as who you are.
  Don't read too much into a 5-bot tournament — patterns will shift as
  more bots arrive.

## Process

- Keep bots' files trivially short — one function, no module-level
  state where avoidable. Module-level state is fine if it depends only
  on histories (e.g. caches), but never on the opponent's identity.
- The "trembling hand" interpretation of noise: the bot's intent is
  fine, only the executed move is corrupted. This is the standard
  Axelrod-style noise model and the one we implement.

## Ecology lesson (T4)

- A new bot doesn't have to win to change the ranking. Adding TFTT —
  a 4th-place bot — pushed GTFT from 5th to 1st by increasing the
  share of cooperative matches in GTFT's book. *Pool composition
  determines who leads.* Whenever evaluating a new bot, ask not just
  "does it beat the current leader head-to-head?" but "does its
  presence change the leader's average?".
- Corollary: be skeptical of single-tournament champions. A pool that
  shifts mostly nice → mostly nasty changes the optimal strategy
  entirely. The "best strategy" is a function of the population.

## Detection-cascade lesson (T5)

- **Any threshold-based mode switch in a noisy IPD creates a
  cascade risk in self-play.** Hard TFT (TFT + lock-to-D when opp's
  20-round D rate exceeds 0.6) scored 1.797 against itself — far worse
  than TFT-vs-TFT at 2.312. The echo war from a single noise flip
  spikes the local D rate above threshold and both copies lock at
  once. Then their windows fill with D, perpetuating the lock.
- **Designs that resist the cascade**:
  - Long windows (50+) and high thresholds (0.8+) so that no
    plausible echo+noise burst can trigger them.
  - One-way locks only after sustained *consecutive* D's (e.g. last
    5 moves all D), not statistical majorities.
  - State machines whose "lock" transition is impossible to hit when
    the opponent is a perfect mirror of you under low noise.
- **Compare**: single-state strategies (TFT, GTFT, TFTT, Pavlov) have
  no transition to cascade. That's why they all have near-3 self-play
  scores under noise. Adding state is dangerous unless the state
  transitions are robust to symmetric noise echoes.

## Predator-self-play lesson (T6)

- **Probing-based predators destroy each other.** Prober vs Prober =
  1.108 — both bots run the same probe, both see the same response,
  both reach the same "opp is pushover" conclusion, both lock AllD.
  The self-play is catastrophic by *design*: a strategy that
  detects-and-exploits will detect itself and exploit itself.
- This is structurally different from the Hard TFT cascade. There,
  the symmetric noise echo triggered the detector. Here, the
  symmetric *probe* triggers the predation. No noise needed.
- **General rule**: any strategy that has a "if opp is naive, play
  AllD" branch must check the branch never fires against its twin.
  Prober's check (opp defected in rounds 1 or 2?) returns False
  against itself because in self-play opp's rounds 1 and 2 are
  scripted Cs.
- **Fix sketch**: a Prober-like bot should treat a *D in round 0
  followed by Cs in rounds 1-2* as a signature of "this is also
  Prober" and switch to TFT in that case. (To be tested in a future
  bot.)

## Cumulative-count lesson (T7)

- **Cumulative counts beat sliding windows under noise.** Soft
  Majority (`play C iff opp.count(C) >= opp.count(D)`) is the
  simplest counting strategy possible and immediately took 1st
  (2.529 vs the previous leader at 2.357). Under low noise the
  cumulative count of C's quickly dominates and stays dominant
  forever, so noise can never reverse the majority for any
  reasonable opp. This is structurally different from Hard TFT's
  sliding-20 window: a sliding window has a fixed denominator and
  can be tipped by a short burst; a cumulative count has a denominator
  that grows with the match and washes out short bursts.
- **The simplest non-trivial strategy is often the best.** Single
  function, single line, no parameters. Outperforms all the more
  sophisticated bots — at least in this pool. The lesson is to try
  trivial baselines aggressively before going clever.
- **Counterpart in real life**: long-running relationships where
  *overall track record* matters more than the most recent slight.
  "We have known each other for years, one bad day doesn't change
  much." This is exactly the Soft Majority rule. Compare to a
  marriage that reacts to every single comment vs one that weighs
  the whole history.

## Asymmetric exploit lesson (T7)

- Soft Majority loses to Grim (1.358 vs 2.125) for a structural
  reason: Grim's mode-switch happens fast (one D triggers permanent
  D) while Soft Majority's mode-switch is slow (need #D > #C). When
  a fast-trigger predator meets a slow-trigger cooperator, the
  cooperator pays the lag cost.
- **Implication**: the next bot's design should consider whether to
  pair slow trust-building (so self-play stays cooperative) with
  fast trust-revoking (so a Grim-style lockup doesn't farm us).
  GRADUAL is the textbook example.

## Reproducibility lesson (T8)

- **CPython's `hash()` for strings is randomised per process.** Our
  `play_pair` seeded each match with `hash((base_seed, name_a, name_b, r))`,
  which gave self-consistent matchups within a single run but
  different matchups across runs. Side effect: every fresh
  tournament shuffled the noise stream for every pair, so unrelated
  matchups (e.g. `always_c` vs `grim`) drifted by up to ~1.3 points
  between tournaments even when both bots were unchanged.
- **Fix**: replaced `hash(...)` with `sha1(...)`-based digest. Now
  per-pair seeds are reproducible across processes. Done at T8.
- **Implication for past records**: T1-T7 matrix entries are not
  directly comparable to T8+. Aggregate rankings are still
  meaningful because 3-repeat averaging damps most variance, but
  per-matchup numbers should be re-derived for direct comparison
  if needed.
- **General rule**: any pseudo-deterministic seeding in tools that
  rely on Python's `hash()` of strings should be replaced with
  `hashlib` digests if cross-run determinism matters.

## Ratchet-trap lesson (T8)

- **GRADUAL self-play under noise = 1.578/round** — almost as bad as
  AllD-vs-AllD. The mechanism is a "ratchet":
  - GRADUAL's punishment length = cumulative count of opp's
    defections so far.
  - Every round of mutual D adds to *both* GRADUALs' counts.
  - Next time either re-enters normal mode and sees a fresh D, the
    scheduled punishment is longer than the previous one. The
    calming 2 Cs that follow get drowned by the next, longer
    punishment.
- **Refined principle**: *in a noisy IPD, any state machine whose
  retaliation length grows monotonically with observed defections
  will spiral in self-play.* The retaliation length must be
  bounded (TFT=1) or reset to a constant (Pavlov: stateless) or use
  a sliding window with a fixed denominator.
- **Compare**:
  - TFT: 1-D retaliation. Echo dies out fast.
  - TFTT: 0-1 D retaliation with 2-D tolerance. Even more robust.
  - Soft Majority: trigger is `#D > #C`. Denominator grows with the
    match, so noise can't tip it. *Bounded by global statistic.*
  - GRADUAL: retaliation = `#D` (unbounded as the match progresses).
- **In the real world**: this is the structure of an arms race.
  Each side's deterrent escalates proportional to perceived past
  attacks. With perfect attribution it's stable. With observation
  noise (i.e. you can't tell whether the other side really attacked
  or it was a malfunction), the count ratchets and you end up at
  mutual D = mutual nuclear lockdown / total trade war / divorce.

## Process lesson (T8)

- **Predictions are cheap; testing is cheap; revising the priors is
  the point.** GRADUAL was predicted as top-3, ended up 5th. Without
  running the tournament we'd have confidently added a flawed bot
  to our mental model of "what works". The cost of running a 30-second
  tournament is much lower than the cost of building a strategy on
  bad priors.
- **Trace before theorising.** The self-play 1.578 number didn't fit
  the model until I traced an actual match step-by-step. The 9-flip
  trace exposed the ratchet structure immediately.

## Detector-tuning lesson (T9)

- **An AllD detector built on opp's D-rate alone cannot distinguish
  exploitation from mutual punishment.** Tested with Adaptive Pavlov:
  the rule "if opp played >=8 D in any 10-round window, lock D"
  triggers correctly on AllD/Grim/Random but also fires false-positive
  on Prober, Hard TFT, and even TFT — any retaliator that briefly
  enters a high-D cycle alongside the bot itself.
- **The fix is asymmetric counting.** Count only `(my_C, opp_D)` events
  (S=0 outcomes), not `(my_D, opp_D)` events (P=1). S=0 is true
  exploitation: I extended cooperation and the opponent defected. P=1
  is mutual punishment, which is recoverable.
- **Real-world analogue**: in conflict de-escalation, the question
  "did the other side attack me" is much less useful than "did the
  other side attack me when I was offering peace". An opponent who
  hits back when you hit them is just reciprocating, not exploiting.
  An opponent who hits when you extend your hand is genuinely
  dangerous. Detector design should reflect that asymmetry.
- **Trade-off was a wash, not a win**. Adaptive Pavlov scored 2.257
  vs Pavlov 2.258 — the gains vs AllD/Grim/Random exactly cancelled
  the losses vs Prober/Hard TFT/TFT. So the lesson isn't "detectors
  are bad" but "this particular detector is poorly calibrated."

## Asymmetric trigger lesson (T10 — Firm-but-Fair)

- **FBF is Pavlov minus the win-stay-after-T=5 transition.** That's
  the only difference: where Pavlov in state (D, C) stays D (banking
  the T=5), FBF returns to C. Everything else is identical.
- **Counterintuitively, dropping the T=5 exploitation upside makes
  FBF a stronger overall bot** (2.447 vs Pavlov's 2.302). Mechanism:
  - The T=5 win-stay is what triggers all of Pavlov's losses against
    cooperator-cluster bots. After a single noise flip puts Pavlov in
    state (D, C), Pavlov plays D again, the cooperator-cluster bot
    reads this as fresh exploitation, retaliation/count tilts.
  - Removing the (D, C) → D transition removes that whole class of
    "noise creates a Pavlov-initiated mini-war" failures.
  - Cost: against AllC specifically, FBF "leaves money on the table"
    (3.030 vs Pavlov's 4.053). But in a pool where AllC is one of 14,
    losing 1.0 in that single matchup costs 0.07/round on average —
    much less than the gains across 5+ cooperator matchups.
- **General principle**: *if your bot has a transition that captures
  short-term gain (T=5 win-stay) but also creates structurally bad
  behaviour vs cooperators, removing that transition is often the
  net-positive move.* The classic predator/cooperator trade-off, but
  pinned down to a single rule in the transition table.
- **Real-world analogue**: a country that takes advantage of every
  short-term diplomatic opening to grab a small benefit usually
  loses long-term cooperation with allies, even though each
  individual grab "looked rational." A country whose policy is "if
  they're being good to us we're good to them, *full stop*, no
  optimising for the tactical advantage" is the FBF rule. Less
  greedy, more trusted, ends up ahead.

## Convergence lesson (T10)

- **The top-3 has converged on three structurally different
  niceness/forgiveness strategies, all within 0.04 of each other.**
  GTFT (memory-1, stochastic forgiveness), FBF (memory-1,
  asymmetric trigger), Soft Majority (memory-N, cumulative count).
- This is a *Pareto frontier*, not a clear winner. Each design buys
  the same outcome (avg ~2.45/round) by a different mechanism. None
  is dominated by another:
  - GTFT loses to FBF on (vs Grim) but wins on (vs AllD).
  - FBF loses to Soft Maj on (self-play noise) but wins on
    (vs Pavlov).
  - Soft Maj loses to GTFT on (vs Grim) but wins on (self-play).
- **General principle**: in a complex environment with multiple
  failure modes (noise, predators, mutual punishment loops), there
  is no single best strategy — there is a Pareto frontier of
  trade-offs. The pool determines which point on the frontier wins
  any given tournament. This matches Axelrod's original finding
  that "nice + retaliatory + forgiving" describes a *class* of
  strategies, not one specific algorithm.
- **Real-world implication**: there are multiple stable institutional
  designs (US Constitution, UK parliament, German Bundestag, Swiss
  direct democracy) all on the Pareto frontier of "stable nice
  cooperation under noise." None dominates, none is obviously best,
  but they share the structural ingredients (no preemptive
  aggression, proportional response, recovery mechanisms).

## Tuning lesson (T11)

- **A structurally-correct trigger can still fail at the wrong
  threshold.** Pavlov-Exploit (v2) replaced Adaptive Pavlov's
  "opp's D-rate >=8/10" with "S=0 events >=4/10" — exactly the
  asymmetric trigger that FBF uses. The *idea* is right (only
  exploitation should trigger D-lock), but threshold 4/10 turns it
  into a false-positive on TFT-family bots under noise.
- **Echo wars produce dense S=0 events.** When my Pavlov plays
  (D, C)→D win-stay vs TFT's mirror, the resulting CDDCDD pattern
  contains an S=0 event roughly every other round of the
  oscillation. A 10-round echo war can easily contain 4-5 S=0
  events, tripping the detector during a transient sync problem
  rather than during real exploitation.
- **Diagnostic principle**: when designing a "lock-in-on-detection"
  bot, simulate the trigger's behaviour against retaliators first.
  If your trigger fires during clean echo-resync events, it's too
  hot.
- **Repair recipe**: pair the exploit-event count with a
  *forgiveness probe* — after K consecutive S=0 events but before
  permanent lock, try unilateral C. If opp responds C, we were in
  an echo war, not under exploitation; reset detector. If opp
  responds D again, commit.

## Round-robin averaging artefact (T11)

- **Adding a single new bot can swap adjacent top-3 ranks even if
  the new bot lands mid-pack.** T10→T11: GTFT lost 0.079, Soft
  Majority lost 0.088. The new bot (pavlov_exploit) didn't
  *displace* them by being stronger — it changed the matchup
  matrix by giving Soft Majority a lower-than-pool-average score
  (1.570) in its row, dragging Soft Majority's average down enough
  to fall out of top-3.
- **Implication for stability claims**: "top-3 is stable across
  3 tournaments" only makes sense if the bot pool is *fixed*.
  Adding a new bot per turn (as the spec requires) means each
  tournament has a different pool, so top-3 *can* shift just from
  the averaging change. Any STOP condition based on "stable top-3
  set" should be read as a soft criterion, not a hard invariant.
- **Real-world implication**: tournament rankings (whether of
  sports teams, economic models, or political coalitions) depend
  heavily on the *opponent pool*. The "winner" can change just by
  adding a single new participant that affects others'
  averages — even if no participant's intrinsic strategy
  improved. This is also why Axelrod's tournaments were criticised:
  the entry list determined who won.

## What to predict for T12+

- Need 3 consecutive tournaments with stable top-3 set + 10+
  non-pantheon bots + REPORT.md → STOP.
- We have 10 non-pantheon bots. T11 top-3 set is {FBF, GTFT, TFTT}.
  T12 onward needs the same set (counter run 1 now).
- Strategy: add bots that are unlikely to land in the top-3 *and*
  unlikely to dramatically reshape the matchup matrix against
  existing top-3 members. Hardest-to-disrupt addition would be
  another FBF/GTFT/TFTT-style bot (it would cooperate with the
  top-3 at ~2.9-3.0 and let them keep their averages).

## Top-4 stability is the right answer (T12)

After 5 tournaments T8-T12, the strict "same top-3 set" criterion has
NEVER been satisfied for 2 consecutive runs. But the **top-4 set**
{FBF, GTFT, Soft Maj, TFTT} has been stable across T10-T12, with only
the *order* shuffling. Adding bots per turn changes the averaging,
which is enough to shuffle 3 ranks that sit within 0.05/round of
each other. The signal is the Pareto cluster, not any specific bot.

**Lesson for future generations**: when the top-k cluster sits inside
the run-to-run noise band, redefine "stable" to mean "same SET at a
slightly larger k" rather than "same exact rank order at k=3". Don't
chase a strict criterion that the population's geometry forbids.

**Real-world parallel**: trying to predict "who will be the next
year's biggest player in the OPEC cartel / EU council / G7" is
essentially the same problem. The top 4-5 players are usually fixed;
who's #1 vs #3 in any given quarter depends on noise. The cluster
membership is the real signal, not the rank.

## Contrition has limits (T12)

CTFT's docstring derivation predicted near-3.0 self-play, and the
empirical result was 2.967. The mechanism works. But its vs-Grim
matchup (1.333) is *worse* than plain TFT (1.485) because contrition
fires against a punisher that won't forgive.

**Lesson**: an "always apologise after my own mistake" policy
generalises beautifully across noise-robust cooperative partners
but is a *liability* against rigid retaliators. In real life:
apologising is a high-trust act; you only apologise to people who
have demonstrated they'll forgive. Apologising to someone who has
committed to permanent retaliation just wastes credit.

**Diagnostic for new bots**: when you derive an override rule that
helps a class of matchups, also check whether it triggers in
matchups where it'll cost — and consider gating the override on
opp's *responsiveness*, not just on my own state.
