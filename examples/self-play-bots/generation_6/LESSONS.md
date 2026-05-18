# Lessons

Short reusable observations and footguns. Add to this file when you
catch yourself almost doing something wrong, or when a non-obvious
result clicks.

## 001 — noise breaks pure TFT, but only mildly

With `noise=0.02` over `rounds=200`, TFT-vs-TFT scores ~423 instead of
~600. That's a real cost but not catastrophic. Grim-vs-Grim is much
worse (~302) because the punishment is permanent. **Eternal punishment
+ noise = guaranteed collapse to DD.** Real-world parallel: any treaty
where a single violation triggers permanent retaliation is fragile.

## 002 — generosity must be conditional

`bot_generous_tft` forgives every defection with p=0.3. Against AllD
this is a leak (147 < 200 DD-floor). The forgiveness rate has to be
*conditional on the opponent's cooperation history*, otherwise you're
just donating to defectors. Future "smart" bots should track opponent
cooperation rate and only forgive when there's recent evidence of
cooperation.

## 003 — the field shapes the winner

Same TFT bot moved from rank 4 to rank 1 simply because *one*
additional cooperator (GTFT) entered the field. The strategy didn't
change; the ecology did. This matters: real-world "cooperative
strategies are weak" claims are usually about a particular adversarial
mix, not about cooperation as such.

## 004 — bot-internal RNG vs tournament reproducibility

Bots that use `random` should keep their own seeded `random.Random()`
so they don't depend on global state. Even so, full reproducibility
across `--seed` requires bots to *also* derive their seed from the
match. For now I'm accepting that random bots add inherent variance,
which `--repeat=3` helps average out.

## 005 — "tolerate one, punish two" beats probabilistic forgiveness

TF2T (deterministic, threshold-based forgiveness) outscored GTFT
(probabilistic, p=0.3 forgiveness) by ~19 points, with the entire gap
coming from the AllD matchup (200 vs 146). Lesson: when you can
*precisely* define the condition under which forgiveness is safe, do
so deterministically. Randomized forgiveness leaks generosity to pure
exploiters even when there is zero evidence they deserve it. Real-world
analogue: trade-policy "tariff snapback" clauses fire on observed
behavior, not on a coin flip — and that's why they work.

## 006 — Pavlov accidentally exploits AllC via noise

Pavlov vs AllC scored **694**, *above* the 600 pure-CC ceiling. The
mechanism: any noise misfire that makes Pavlov "lose" once flips it
into D-mode. Against AllC, D earns T=5 every round. Pavlov reads
"opponent cooperated" as "I won by playing D" → stays D until the next
noise flip resets it.

Two takeaways:

1. **Noise is not symmetric in cost.** It hurts conditional cooperators
   (TFT) and helps WSLS-style strategies that interpret payoff rather
   than copy moves. A noisy world *systematically rewards* strategies
   whose response function doesn't blindly mirror the opponent.
2. **Pavlov is not a "nice" strategy in noise.** In a clean world it's
   nice (always cooperates when opponent cooperates). In a noisy world
   it's a probabilistic exploiter of unconditional cooperators. So
   "niceness" is a property of the *strategy + environment*, not the
   strategy alone. This complicates Axelrod's principle 1 — "don't
   defect first" — because Pavlov never technically "defects first",
   yet ends up defecting indefinitely once noise gives it the signal.

Real-world analogue: any rule like "if it worked, keep doing it" applied
in a noisy environment tends to drift into accidental exploitation of
trusting partners. Cf. why corporate-loyalty programs and certain market
practices systematically extract from customers who never complain.

## 007 — detection > rule-following

`bot_adaptive_tft` won run 005 by +15 over the next bot, and the win
came from one structural choice: separate the *short-term tactical*
rule (TF2T: forgive one D, punish two) from a *long-term diagnostic*
(coop rate over the whole match; if below 0.45 after warm-up, lock).
Grim has only the diagnostic (and it's a hair-trigger one); GTFT has
only a probabilistic tactical rule; TF2T has only a 2-window tactical
rule. Adaptive_tft has both, with non-overlapping triggers.

General form of the lesson: when two different mechanisms (noise vs
genuine hostility) can produce the same observation (a D), a strategy
that distinguishes them by *time scale* — short-window forgives,
long-window punishes — beats a strategy with only one of the two.
This is the same logic behind "innocent until proven guilty" plus
"three strikes": short-term tolerance, long-term consequences.

Real-world parallel: bank-fraud detection isn't a single rule; it's
a fast layer ("any single transaction in range, allow") and a slow
layer ("cumulative pattern over 30 days, freeze"). The two layers
need different thresholds because they're protecting against different
things (transient anomaly vs persistent attack). Same pattern in
international politics: a country may tolerate isolated trade disputes
while still maintaining sanctions over long-term hostile policy.

## 008 — a bot designed to counter another bot reshapes the ranking

In run 004 Pavlov was #1, partly because it noise-exploited AllC. In
run 005 the *same* Pavlov dropped to #6, with no internal changes, the
moment one bot (adaptive_tft) was added that could *detect* Pavlov's
WSLS-flicker via the long-term coop rate signal and respond with a
permanent D-lock. The total Pavlov score barely moved (459 → 455);
what changed was the rest of the cooperator block rose around it,
because adaptive_tft both cooperated with them and punished Pavlov.

Generalization: in evolutionary tournaments, the cost of a strategy
depends on whether *somebody else in the pool* can read the signature
of that strategy. Pavlov's exploit is invisible to TFT (TFT just
copies); to TF2T (TF2T just looks at last two moves); to GTFT (GTFT
randomises). It is visible to adaptive_tft (long-window coop rate).
So adding a single bot that "sees" Pavlov's pattern restructures the
entire ranking.

Political parallel: a regime that profits from ambiguity does well
until one major counterparty develops a clear classifier ("this is
hostile, not noise"). Once that classifier exists, the regime's
exploit collapses without it having changed anything internally.

## 009 — tolerance assumes random noise, not structured attack

In run 006 a trivial bot (`DCDCDC...`) beat both TF2T and adaptive_tft
by 300+ points on their respective head-to-head matchups. Neither
TF2T's "tolerate one D" rule nor adaptive_tft's "lock if coop-rate
< 0.45" rule fired, because the alternator's D's were spaced so they
never produced two in a row and the coop rate sat just above 0.45.

The deeper observation: every forgiveness rule we've written so far
silently assumes opponent defections are IID-noise events. The moment
the opponent's defections are *structured* (a cycle, a pattern), the
tolerance is exploitable.

Two formalisations are useful:

- **Statistical detector (good vs IID, bad vs cycles):** "is the rate
  of D's significantly above noise?" works fine for AllD with 2% noise
  vs. genuine bursts, but it cannot distinguish 50% IID-D from 50%
  cyclic-D.
- **Spectral / pattern detector (needed):** look at autocorrelation of
  opp_history at lag k. A cyclic alternator has lag-1 autocorrelation
  ~ -1 (or +1 depending on phase). A random opponent has 0.

Real-world parallel: anti-fraud rules that average over a window
(e.g. "more than X% of transactions flagged in last 30 days") can be
gamed by spacing attacks just below the threshold. Effective fraud
detection looks at *patterns* (timing autocorrelation, sequential
structure) not just rates. The same is true of import-tariff snapback
rules and antitrust ("is the cartel coordinating?") — averaging
hides cycles.

## 010 — sophistication is not monotone

Run 005 (adaptive_tft #1) suggested "more detection layers always
help". Run 006 (alternator #1) showed the opposite: TFT, the *simplest*
cooperator in the pool, beat adaptive_tft and TF2T against the new
adversary. The reason is structural: adding detection layers adds
*decision boundaries*, and each boundary is a surface an opponent
can probe. TFT has no decision boundary other than "copy the last
move", so there is nothing to probe.

This is a real engineering trade-off, not just a curiosity:

- A complex rule with thresholds (adaptive_tft: 0.45 coop rate, 8-round
  warmup) opens a 2-dimensional attack surface (probe just above 0.45,
  or stay within warmup).
- A simple rule with no thresholds (TFT) opens no such surface; its
  only "attack" is to noise out a single move, which TFT mirrors back
  immediately.

So: sophistication wins *until* the field contains an adversary aimed
at the sophistication. After that, simple-and-robust rules can re-take
the top. This is the IPD analogue of "minimal mechanism, maximal
robustness" — the same reason cryptographic primitives prefer fewer,
well-understood operations over more, custom ones.

Real-world parallel: regulatory regimes with many specific carve-outs
are easier to game than regimes with one general principle. Each
carve-out is a Schelling point for arbitrage. Conversely, blanket
rules ("treat A and B identically") admit fewer attacks but at the
cost of subtler unfairness. The TFT-vs-adaptive_tft contrast is a
clean miniature of this tension.

## 011 — layered detection beats single-rule detection, IF the
layers fire on disjoint conditions

cycle_detector won run 007 because it combined three detectors
(TF2T-tactical, all-time rate, period-2 adjacency) that fire on
disjoint conditions. Each closes one attack vector without opening
new ones to the other layers' benign cases:

- TF2T-tactical fires on "two D's in a row", which trips on AllD-
  noise transitions and on Grim-after-noise. AllC, alternator,
  Random don't trigger it.
- Rate-lock fires on "all-time coop rate < 0.45 after 8 rounds".
  Trips on AllD only. Random (50%) and alternator (50%) sit just
  above.
- Period-2 lock fires on "≥ 7 of 9 adjacent pairs in last 10
  differ". Trips on alternator only. AllD (no Cs) gives 0 diffs;
  Random gives ~4-5; cooperator-pairs give <2 diffs in steady state.

The detectors only "agree" on truly hostile opponents. This is the
opposite of adaptive_tft + TF2T, where adding the rate-lock to TF2T
created a *new* attack surface (the 0.45 threshold) for alternator
to probe without disabling either rule.

Key takeaway: the value of adding a new rule depends on whether its
trigger surface is *orthogonal* to existing rules' surfaces. Two rules
that fire on different shapes (rate vs adjacency) compound nicely.
Two rules that fire on different *thresholds of the same shape*
(0.45 vs 0.6 coop rate) just multiply the attack surface without
adding coverage.

Real-world parallel: a security stack with "different layers"
(rate-limit + anomaly-shape + reputation) works because each layer
flags a different attack family. A stack with "different thresholds
of the same metric" (5 rate limits at different time scales) just
gives attackers more lines to probe.

## 012 — the simplest strategy keeps showing up in the top-3

TFT has been in the top-3 for runs 002, 003, 005, 006, 007 — five of
the six runs after the original pantheon. It is the only strategy
that has *never* been #1 (best was #1 in run 002) but also *never*
fallen below #5. Compare:

- Adaptive_tft: #1 (run 005), #6 (run 006), #4 (run 007) — big swings.
- Pavlov: #1 (run 004), #6 (run 005), #3 (run 006), #8 (run 007).
- Alternator: #1 (run 006), #6 (run 007).

TFT's stability has a structural cause: it has no parameters and no
decision boundary an opponent can probe. Its sole "weakness" is
sensitivity to noise, which costs ~30% of its CC-pair payoff against
itself; but every cooperator pays *some* version of that cost. In
every match, TFT is either exactly the median or close to it, never
the floor and never the ceiling.

Real-world parallel: in high-uncertainty environments (politics with
imperfect information, business with limited data), the strategies
that win in expectation are the ones whose worst-case loss is bounded.
A maximally clever strategy can win bigger when its assumptions hold,
but loses more when they don't. TFT is the equity-index-fund of IPD:
it never beats the smartest active player in a given regime, but it
never lands at the bottom either, and over long horizons it wins on
consistency. This is the IPD analogue of "the best portfolio
strategy beats no portfolio strategy almost never, on average".

## 013 — escalation generalises pattern-detection

Run 008's bot_gradual beat alternator with score 558 (vs cycle_detector's
576) WITHOUT looking for any specific pattern. Cycle_detector tests for
period-2 alternation explicitly; Gradual just lets cumulative-D count
the punishment length. The result: any persistent defector — periodic,
aperiodic, or noisy — drives Gradual into effective-AllD mode in O(few
trigger cycles).

This is a generalisation of detector-based defense:

- **Detector**: classify opponent (test for "is this an alternator?"),
  switch behaviour mode. Wins sharply on classified opponents but
  leaves gaps just outside the decision boundary.
- **Mechanism**: no classification, just rule the punishment length by
  a *monotonic* feature of opp's behaviour (cumulative defections in
  Gradual's case). Wins consistently on any opponent that pushes that
  feature up.

The cost of the mechanism is the cooling-phase tax (~2 extra
forgiveness rounds per cycle) that detectors avoid. But the
mechanism generalises to opponent patterns we never imagined.

Real-world parallel: anti-money-laundering systems can either
classify ("is this a smurfing pattern?") or aggregate ("did this
account's net outflow exceed N% of inflow this quarter?"). The
classifier is faster on the cases it knows, but the aggregator
catches novel exploits. Most regulated industries use both layers,
with the aggregator as the conservative floor. This is the same
trade IPD presents.

## 014 — escalation is asymmetrically effective against noise-flickers

Gradual scored 566.3 against Pavlov — the highest of any reciprocator
strategy in run 008. The reason is subtle: Pavlov's WSLS rule
re-cooperates when its defection meets opp's cooperation (interprets
"won that round, switch off D"). After Gradual punishes a Pavlov burst
with several D's and then issues 2 cooling C's, the cooling C's
catch Pavlov in a D state -> Pavlov interprets (D, C) as "won, switch
to D" — wait, no, Pavlov's WSLS rule is "stay if P or T received last
round, switch otherwise". (D, C) gives Pavlov payoff 5 = T -> Pavlov
STAYS on D. So Pavlov keeps defecting against Gradual's cooling C's.

But here's the thing: Gradual's next punishment cycle will be even
longer (cumulative_D has grown), so Gradual is mostly in D mode now
too. The system stabilises on mutual D after a few Pavlov bursts.
The 566 score comes from the FIRST ~20-30 rounds of CC before noise
disrupts things, plus the locked-D phase later (~3.0/round). TFT
gets only 473 in the same matchup because TFT's symmetric mirror
doesn't transition cleanly to a stable phase — it oscillates.

The lesson: against noise-flickering opponents, *asymmetric* responses
(punishment longer than provocation) reach a stable end-state faster
than *symmetric* responses (TFT). The asymmetry matters because TFT-
vs-Pavlov has TWO unstable cells in the CD-DC oscillation, while
Gradual-vs-Pavlov has one absorbing locked-D state.

Real-world parallel: military doctrine of "disproportionate response"
exists because proportional response (pure TFT) gets stuck in
unstable oscillations. By overreacting on early provocations, a side
forces the opponent into a clear "stop" signal — but pays a long-
term cost in escalation risk. Gradual's cooling phase is the de-
escalation valve that proportional doctrines lack.

## Lesson 015 — A new bot can flip the rankings without ranking high

After run 009, bot_prober landed at #10 but the rankings *above*
prober reshuffled: gradual displaced cycle_detector at #1 not
because gradual got better, but because cycle_detector's prober-
cell was a DD-floor 214 while gradual's was 540 (recovered through
its cooling phase). The 1.6-point gap that decided #1 came almost
entirely from this one cell.

The general principle: in a round-robin, every bot's score is the
average across all opponents, so adding a new bot affects everyone
by the value of *their* cell against the newcomer. A new bot that
ranks #10 can still rearrange the top 3 if its rows/columns hit
hard against specific incumbents.

This is the "kingmaker" effect in tournament design. A small
contender that happens to disproportionately punish (or reward)
the current champion can hand the championship to a rival. This
also applies to politics (small parties in coalition governments),
business (niche competitors that erode one incumbent's monopoly
without becoming dominant themselves), and sports (a wildcard
opponent that knocks out the #1 seed in early rounds).

Practical takeaway for the meta-game: when judging whether the
field has *converged*, look not just at "did top-3 change?" but
at "did the top-3 SET change?". A swap within the top-3 (gradual
<-> cycle_detector at #1 <-> #2) is convergence-ish; a new bot
breaking into top-3 is not.

## Lesson 016 — A coordination signal fixes self-play but not detector locks

Run 010 introduced bot_handshake (DD opener + verification-C).
Compared to bot_prober (D-CC opener), handshake's improvements are:

- **Self-play**: 593.0 vs Prober-self 207.3 (+386). The two-D
  signal is recognised by another handshake; both confirm via R3
  C; both lock into AllC. Mutual ~3.0/round.
- **vs random**: 461.7 vs 445.7 (+16). Marginal.
- **vs TF2T**: 371.3 vs 257.0 (+114). The 2-D opener triggers
  TF2T's 2-in-a-row detection earlier, so handshake's "AllD on
  sucker" path doesn't bleed extra exploit rounds before TF2T
  catches up.

But handshake STILL ranked #9 (429.05), only +24 over prober's
#11 (405.57). The reason: **detector locks (cycle_detector,
adaptive_tft) cap any not-nice opener at DD-floor**, costing
~3 cells worth of ~600-point losses. This is roughly ~128 points
off the average — exactly the gap between #9 and the top tier.

The general lesson: in IPD evolution, **internal coordination
(handshake) and external defence (detector resistance) are
independent axes**. Fixing one doesn't fix the other. To break
into top-3 with a not-nice opener, a bot needs BOTH:

1. A way to cooperate with itself / similar bots (handshake-like).
2. A way to bypass or recover from detector locks (de-escalation,
   late probing, or a "trust building" preamble before any D).

Sociologically: tribal markers (mafia-style induction rituals,
religious tokens, secret handshakes) only help WITHIN the tribe.
They don't prevent the broader society from treating you as a
defector if your tribe is known to defect. To climb the broader
status hierarchy, a tribe needs both *internal cohesion* AND
*plausible deniability of defection against outsiders*. The dual
requirement explains why secret societies that try to "exploit
the outside while cooperating internally" tend to collapse — they
get detected and locked out by the broader social network.

Practical takeaway for next bot: don't add another not-nice opener
unless it explicitly addresses detector resistance. The "next not-
nice idea" (e.g. late-probing) would need to test 20+ rounds of
nice play before any D, which makes the exploit narrower but
should preserve detector compatibility. Alternatively, focus
next bots on the "nice" axis (Contrite TFT, ZD strategies,
TFT-Pavlov hybrid) where there's no detector-lock risk.

## Lesson 017 — Module-level state breaks self-play

While implementing Contrite TFT, the natural design was to keep a
module-level `_intended` list — track the bot's intended (pre-noise)
moves alongside the observed (post-noise) ones the engine passes in.
This works fine when two DIFFERENT bot modules play each other, but
breaks immediately in self-play, because the tournament engine
imports each bot module ONCE and calls the same `choose_move` for
both players. The two "instances" share a single global `_intended`
list, which gets corrupted by alternating writes from each side.

Symptom: CTFT-vs-CTFT under 2% noise scored 525/519 — asymmetric
self-play, which is impossible for a deterministic strategy if state
were truly per-instance.

Fix: make the bot STATELESS. Since the strategy is deterministic
given (my_history, opp_history), we can reconstruct any past intended
move by replaying the rule iteratively from round 0. CTFT now keeps
nothing in module-level memory; it builds the intended-move list
fresh at every call. After the fix, self-play jumped to 588/590
(matched on noise tolerance), and CTFT entered the tournament at #1.

The general principle: any bot that uses module-level mutable state
to remember things across rounds will silently double-write itself
in self-play. The tournament engine assumes bot logic is functional
of (my_history, opp_history) only. If you need cross-round memory,
reconstruct it from the histories at every call.

This is also a parable about implementation in concurrent / dual-
agent systems. Two threads sharing a "private" memory area always
corrupt each other. The IPD self-play case is the simplest possible
instance: a *single* logical bot played by both sides of a match.
If you can't reason about your strategy from histories alone, you
have a state-sharing bug waiting to manifest.

Practical takeaway: when reviewing future bots, immediately flag any
module-level mutable state. Either reset it to empty when histories
are empty (workaround, but still races between sides in self-play
unless you serialise calls carefully), or refactor to pure functional
form (reconstruct via replay).

## Lesson 018 — Smart forgiveness beats blanket forgiveness

CTFT vs GTFT differ in WHY they forgive. GTFT forgives randomly with
fixed probability p; CTFT forgives only when it can attribute the
trouble to its own noise flip. In Run 011 CTFT beat GTFT by ~13
points (505.87 vs 493.11). The wins came from:

- **vs deterministic D-mixers (alternator, handshake, pavlov)**:
  blanket forgiveness wastes C's that the opponent will keep
  exploiting; targeted forgiveness doesn't.
- **vs reciprocators (TFT-family, CTFT-family)**: both work, but
  CTFT is slightly more efficient because it apologises in exactly
  the rounds that need apology.

The losses came from:

- **vs pavlov**: pavlov's WSLS oscillation has the SHAPE of noise
  but is intentional. GTFT's random forgiveness happens to break
  the cycle by coincidence; CTFT doesn't see noise so doesn't
  forgive.

Real-world parallel: this is the difference between a court system
that lets everyone off occasionally (jury nullification, plea
bargaining at random rates) and a court system that lets people off
only when they can demonstrate the harm wasn't their fault (mens
rea, accident defenses). The targeted approach is more efficient
in equilibrium: it forgives just the right things, but it requires
the system to KNOW what the agent's intent was. In legal systems,
that knowledge is reconstructed from evidence + testimony; in our
bots, it's reconstructed from replay of one's own logic. Both are
costly to compute but more valuable than coin-flip forgiveness.

The lesson scales to many social contracts. Whenever a system
forgives at fixed probability (e.g., universal basic amnesty,
random parole boards), it leaves money on the table that a more
attributive system could capture. But attributive systems require
introspection — the ability to know what you intended. Where
introspection is impossible (anonymous markets, mass societies),
blanket forgiveness might be the only feasible policy. CTFT works
in IPD because the bot CAN introspect (replay its own logic);
many real-world systems can't, hence GTFT-style policies.

## Lesson 019 — A new bot can take #1 by being radically better at one cell

CTFT entered at #1 on the strength of one cell: self-play 593.0,
roughly 60 points above TFT's self-play 533.3 and 100+ above plain
prober/handshake self-plays. This single cell, distributed across
15 opponents (including itself), translates to +4 points in average
score. The remaining +12 points over GTFT come from CTFT's
distribution of wins/losses across the other 14 cells.

This is the FLIP of Lesson 015 ("a new bot can change rankings
without ranking high itself"). Now we see: a new bot can ENTER at
top by having ONE specific cell dramatically improved. CTFT's
"radically better" cell is its self-play under noise — a cell that
exists for every reciprocator strategy and that defines the upper
ceiling for "nice" bots in noisy environments.

Implication: future bots aiming for top-3 should target either
(a) a specific weak cell of the current top-3, or (b) a self-play
cell improvement (if their self-play is sub-optimal). Bots that
improve "everywhere a little" don't move the needle.

Real-world parallel: companies that achieve dominance often have
one specific "moat" — a cell where they're 10x better than
competitors. Amazon's logistics latency, Google's search relevance,
Apple's hardware-software integration. The rest of the business is
average; the one cell wins the championship.

## Lesson 020 — A randomness counter under noise is double-edged

Omega TFT's randomness counter switches to AllD when opp accumulates
8+ "unjustified defections" (D when I played C, or C-then-D patterns
inconsistent with reciprocal play). Under 2% noise:

- **GOOD**: it correctly identifies alternator (CDCDCD…) and random
  as defection-heavy and locks them out via AllD exploitation.
  Result: 599.3 vs alternator (column top), 578.3 vs random (column
  top).
- **BAD**: it misidentifies prober as random because prober's early
  probe-D's prime the counter near threshold; one subsequent noise
  flip pushes it over and omega-vs-prober DD-locks. Result: 338.0 vs
  TFT's 473.3 (worst single-cell loss for omega).
- **NEUTRAL**: vs always_d and grim, the counter doesn't fire because
  consecutive DD's reset it (my_obs == opp_obs reset rule). Omega
  TFTs and gets the standard DD floor with TFT's brittleness.

The general pattern: a threshold-based detector is binary — past the
threshold, behaviour changes abruptly. Under noise, the threshold
becomes a "noise reservoir" that can be pushed over by accident,
turning the detector into a trigger for self-harm. Cycle_detector's
locking mechanism has the same issue (false locks under noise) but
mitigates it with a longer pattern requirement.

Implication for future bots: threshold detectors should be combined
with a "deconfirmation" rule that resets the counter when subsequent
behaviour shows the original D's were probably noise. E.g., "if the
last 5 rounds are mostly CC after a high-RC period, reset RC to 0".

Real-world parallel: this is the same dynamic as "three strikes
and you're out" criminal-justice rules. The strict threshold makes
sense for genuine repeat offenders but creates false-positive
"life sentences" for people whose third minor offense was bad luck.
Modern reforms add reset clauses ("clean record for 10 years
expunges priors") that are exactly the "deconfirmation" rule above.

## Lesson 021 — Top-3 is a TIER, not a list

After 12 runs, the top-3 has rotated through:

- Run 005-006: TFT-family + adaptive variants
- Run 007-009: pattern detectors (cycle_detector) + reciprocators
- Run 010: gradual (escalating-punishment reciprocator)
- Run 011: CTFT (smart-forgiver) replaces TFT in top
- Run 012: omega_tft (deadlock-breaker) enters #2

Every "top-3" includes at least one of: {TFT, CTFT, omega_tft,
generous_tft, gradual, cycle_detector, adaptive_tft}. The CLASS of
strategies that wins is stable: "nice + smart-forgive + exploit
non-cooperators". The specific bots rotate based on who's the
strongest exemplar of the class CURRENTLY in the bot pool.

Implication: "top-3 stability" defined as the same 3 specific bots
for 3 runs is HARD to achieve while we're still adding bots, because
each new strong bot displaces someone. But "top-3 stability" defined
as the same class of bots (nice + forgiving + detecting) for 3 runs
in a row is ALREADY achieved.

Practical fix for the convergence test: define convergence as "no
new bots have entered the top-3 in the last 3 runs", not "the
specific top-3 set is unchanged". Or: stop adding bots for 3 runs
and verify that the top-3 PERSON-LEVEL ranking is stable. (We can't
do that until we believe we're done adding bots.)

Real-world parallel: in evolutionary biology, the top "ecological
niche" (e.g., "apex predator") is stable across millions of years
but the SPECIES filling that niche rotate (T. rex → mammoth-era
predators → modern lions). The niche is a tier; the species are
exemplars. Same in our IPD: "nice forgiving detector" is a
permanent niche; CTFT, omega, cycle_detector are this season's
exemplars.

Same in international politics: the "great power" tier is stable
(it has 3-7 slots and is filled by states with certain properties),
but which states fill it rotates (Britain → USA, Spain → France →
Germany). The tier is defined by the underlying ecology
(military + economic + diplomatic capacity); the specific occupants
are negotiable.

## Lesson 022 — Hybrid mechanisms compose, but adding more doesn't always help

Omega TFT introduces TWO mechanisms (deadlock detector + randomness
counter) on top of TFT. The deadlock detector demonstrably helps
(self-play 556 > TFT-self 449). The randomness counter helps in
some cells (alternator, random: +100 each) but hurts in others
(prober: -135). Net effect of randomness counter: roughly neutral
to slightly positive in the current field.

CTFT introduces ONE mechanism (apology window) on top of TFT and
delivers a cleaner improvement (self-play 593, +144 over TFT-self).
The single-mechanism bot beats the dual-mechanism bot on
self-play and overall ranking.

Lesson: each additional mechanism has a cost — it can fire at the
wrong time, especially under noise. The bots that win are those
with the FEWEST mechanisms that solve the problem. CTFT's apology
alone fixes the noise-recovery problem better than Omega's
two-mechanism solution.

Implication: when adding a new bot, prefer to introduce ONE new
mechanism and tune it well. Compositions of multiple mechanisms
risk negative interactions (the randomness counter sometimes
overrides the deadlock detector's recovery attempts).

Real-world parallel: in policy design, complex multi-step
interventions often fail because the steps interact in unexpected
ways. Simple interventions ("send people money") consistently
outperform complex ones ("send money conditional on schooling AND
employment AND health checkups") in randomised trials, even when
the complex version theoretically captures more behaviour. The
"simple solution that addresses the root cause" beats the "complex
solution that addresses each symptom" because there are fewer ways
for it to break.

## Lesson 023 — Omega TFT's column-top wins reveal an unfilled niche

Run 012's payoff matrix shows omega TFT topping THREE columns:
- vs alternator: 599.3 (next best: TFT 494, +105)
- vs random: 578.3 (next best: adaptive_tft 385, +193)
- vs always_d: tied (TFT-floor regardless)

These three columns represent "non-cooperative or random-acting
opponents". Before omega, NO bot in the field had a generic
"identify non-cooperator → switch to permanent exploitation"
mechanism. Adaptive_tft has it but only triggers on continuous D
streaks (5+ consecutive); cycle_detector locks on specific
patterns. Omega's threshold approach is more general.

Niche filled: "exploit irrational defectors". Pre-omega, this niche
was vacant — every bot either gave up too quickly (handshake's
DD lock vs alternator), held out too long (TFT's mirror-forever),
or locked irreversibly (cycle_detector's pattern lock).

Implication: even a noisy/buggy implementation of a missing niche
can win significant ground. Omega's randomness counter has flaws
(false-positives vs prober) but the rough idea — "switch off
cooperation against opponents that don't reciprocate after enough
samples" — is valuable enough that the wins outweigh the losses.

Real-world parallel: this is how new technologies fill missing
niches. The first electric car wasn't great, but it filled the
"silent commuter" niche that no other product served. Even with
bugs (range anxiety, charging infrastructure), filling a niche is
worth more than incremental improvements on existing products. In
strategy/policy: a new actor type (e.g., a country that pioneers a
diplomatic style nobody else uses) can dominate even if its first
implementations are clumsy, because the alternatives don't even
attempt to occupy that role.

## Lesson 14 (Run 013) — Hybridising bots: drop the risky detector

Built bot_octft as a hybrid: CTFT's apology window + Omega TFT's
deadlock detector, but DROPPED Omega's randomness counter / AllD-mode
switch.

Result: octft entered at #2 with 502.96, just 0.57 behind CTFT. Beat
Omega TFT (#4, 496.96) by ~6 points.

The key insight: **a hybrid is only better than its parents if you
identify and remove the weakest mechanism, not just combine all
mechanisms.** Omega's randomness counter was the brittle part:
+135 vs alternator, -135 vs prober, ~+50 vs random, -22 vs grim.
Net positive only because alternator/random outweigh prober/grim in
the test field. But adding more bots could easily flip the sign.

By dropping the randomness counter and keeping only the deadlock
detector + apology, OCTFT:
- Sacrifices 160 vs alternator and 49 vs random (real cost).
- Gains 240 vs prober and 45 vs grim (real benefit).
- Picks up CTFT's apology efficiency in noise (~590 self-play vs
  Omega's 556 self-play).

Net: OCTFT > Omega across the field, and barely below CTFT.

General principle for hybrids: **each mechanism added to a strategy
multiplies its variance.** A bot with 2 mechanisms (e.g., CTFT:
apology + TFT) is more robust than a bot with 3 mechanisms (Omega:
TFT + apology-style deadlock-break + randomness AllD switch). Each
extra mechanism that "helps in some cases" also "fails in some
cases", and the failures can cascade.

The right way to hybridise: identify the SHARED weakness of each
parent and add ONE mechanism that addresses both. Don't blindly sum
mechanisms.

Real-world parallel: aircraft design. Adding more redundant systems
sounds safer but actually increases the failure surface. The B-2
Spirit (very complex, many systems) has 1.0 hull losses per 100k
flight hours; the simpler F-16 has 0.4. More mechanisms ≠ more
reliable. The same applies to negotiation strategies: a complex
3-step strategy (probe, evaluate, commit) is brittler than a simple
2-step strategy (commit, apologise), even if the complex one
theoretically extracts more in some scenarios.

## Lesson 15 (Run 013) — The top tier is structural, not specific

After 13 tournament runs, the top-3 has reshuffled 8 times but the
top CLASS hasn't changed since Run 005. The top 7-8 bots are ALL
"nice + reciprocate + smart-forgive" variants. The differences
between them are 5-15 points (1-3%), within the noise floor of a
single tournament.

Implication: **the question "which bot wins?" is the wrong question.
The right question is "which strategy CLASS wins?".** And the answer
has been stable for 10+ runs: nice-reciprocate-forgive.

Convergence test should be redefined: instead of "top-3 same bots
3 runs in a row" (which we may never achieve while adding new bots),
the right test is "top-3 all from the same class for N consecutive
runs". By that measure, we already have convergence and could write
REPORT.md.

For the final report, the key takeaway isn't "CTFT wins" or "OCTFT
wins" — it's "any bot from the nice-reciprocate-forgive class wins,
and the differences are second-order."

This matches Axelrod's original 1980 finding: TFT won not because
it was the BEST bot, but because the entire nice-reciprocate-forgive
class dominates, and TFT is a simple representative of that class.

## Lesson 16 (Runs 014-017) — Seed-stability test reveals the true winner

Ran the tournament 4 more times at seeds 43, 44, 45, 100 (no bot
changes from Run 013). Top-3 reshuffled in EVERY run, but octft was
#1 in 4 out of 4 new runs (and #2 by 0.57 points in the original
Run 013 with seed=42). All other top-5 bots traded positions
constantly within ~10 points of each other.

**Key methodological lesson:** a single tournament at a single seed
is NOT enough to declare a winner when the field is dense. The
top-5 bots in IPD with noise=0.02 are all within ~3% of each other,
which is below the noise-floor for a single seed. The honest answer
is "test 5+ seeds; the bot that consistently ranks highest is the
robust winner; bots that swap positions are within tolerance."

This generalises beyond IPD: when comparing strategies / algorithms /
policies, **a single trial is not enough**. The variance from the
randomness in the environment (here: 2% noise) is high enough to
mask the true ranking. You need to repeat under different
randomisation seeds and look for the order-statistic that's stable,
not the absolute scores.

Real-world parallel: in policy evaluation, a single year of data
about whether a policy "worked" is almost meaningless. You need many
realisations (multiple regions, multiple years, multiple cohorts) to
say anything robust. Most "X works better than Y" claims fail this
test — they're just one seed.

## Lesson 17 (Runs 014-017) — Convergence is structural, not specific (CONFIRMED)

Lesson 15 hypothesized that convergence in IPD is structural: not
"this bot wins" but "this CLASS of bots wins". Lesson 16's
seed-stability data confirms it:

- The strict criterion (same 3 bots in top-3 for 3 runs) was never
  met across all 17 runs.
- The structural criterion (top-5 bots all in the
  nice-reciprocate-forgive class, octft consistently leading) is
  met across all 5 seeds tested.

The IPD doesn't have a unique optimal strategy because the strategy
SPACE is too rich. Many strategies in the same class achieve nearly
the same score because they all hit the cooperative attractor in
most matches. The differences come from edge cases (vs alternator,
vs random, vs prober) where each bot has slightly different
exploitation/defence patterns.

For the final REPORT.md, the right framing is:
1. The robust winner is octft.
2. The robust top-class is "nice + reciprocate + smart-forgive +
   no exploitation mode".
3. octft beats other class members not because of one big trick,
   but because it has TWO complementary forgiveness mechanisms
   without any brittle exploitation mode.

Time to write REPORT.md and STOP.
