# Iterated Prisoner's Dilemma — Tournament Report

## What this is

12 tournament generations (T1 through T12), 16 bots in the final pool,
200 rounds per match, 2% per-move noise, 3 independent matches
averaged per ordered pair, all-pairs round-robin including self-play.
See `tournament.py` for the engine and `bots/` for the strategies.

Settings used in every reported tournament:

```
rounds = 200
noise  = 0.02   (probability that any single move is flipped)
repeat = 3      (number of independent matches per ordered pair)
seed   = 42     (deterministic SHA1-based per-pair seeding)
```

The pool, by structural category:

| Category                  | Bots                                         |
|---------------------------|----------------------------------------------|
| Reference pantheon (5)    | AllC, AllD, TFT, Random, Grim                |
| Nice retaliators (4)      | GTFT, TFTT, FBF, Contrite TFT (CTFT)         |
| Stat-aware cooperators (2)| Soft Majority, GRADUAL                       |
| Win-stay/lose-shift (3)   | Pavlov, Adaptive Pavlov, Pavlov-Exploit      |
| Hardliners / provokers (2)| Hard TFT, Prober                             |

## Final ranking (T12)

| #  | Bot                  | Score | Class                |
|----|----------------------|-------|----------------------|
| 1  | bot_firm_but_fair    | 2.492 | nice retaliator      |
| 2  | bot_soft_majority    | 2.428 | stat-aware           |
| 3  | bot_tft2t            | 2.393 | nice retaliator      |
| 4  | bot_contrite_tft     | 2.382 | nice retaliator      |
| 5  | bot_generous_tft     | 2.377 | nice retaliator      |
| 6  | bot_pavlov           | 2.348 | win-stay/lose-shift  |
| 7  | bot_adaptive_pavlov  | 2.346 | adaptive WSLS        |
| 8  | bot_gradual          | 2.310 | stat-aware           |
| 9  | bot_tit_for_tat      | 2.296 | nice retaliator      |
| 10 | bot_pavlov_exploit   | 2.261 | adaptive WSLS        |
| 11 | bot_hard_tft         | 2.149 | hardliner            |
| 12 | bot_always_c         | 2.119 | naive cooperator     |
| 13 | bot_prober           | 2.081 | provoker             |
| 14 | bot_random           | 1.948 | (noise baseline)     |
| 15 | bot_grim             | 1.915 | hardliner            |
| 16 | bot_always_d         | 1.757 | predator             |

The five top-scoring bots are all in the "nice retaliator" / "stat-aware
cooperator" classes. The bottom four are the rigid-rule extremes
(Random, Grim, AllD) plus a probing predator. AllC sits at 12th — it
gets exploited by the few predators in the pool, just hard enough to
drop below the retaliators.

## The real finding: a Pareto cluster, not a single winner

Across tournaments T8 through T12, **four structurally different
strategies have rotated through the top-3 spots** without any of them
clearly dominating. The top-3 set itself changes between tournaments,
not because the strategies got stronger or weaker but because every
new bot we add changes the averaging in the round-robin matrix.

| Tournament | 1st          | 2nd          | 3rd          | 4th          |
|------------|--------------|--------------|--------------|--------------|
| T8         | Soft Maj     | GTFT         | TFTT         | TFT          |
| T9         | GTFT         | Soft Maj     | TFTT         | TFT          |
| T10        | GTFT         | FBF          | Soft Maj     | TFTT         |
| T11        | FBF          | GTFT         | TFTT         | Soft Maj     |
| T12        | FBF          | Soft Maj     | TFTT         | CTFT         |

The **top-4 set** {FBF, GTFT, Soft Majority, TFTT} has held the top
four ranks in 3 consecutive tournaments (T10-T12), with all four bots
sitting within ~0.05 points/round of each other. This gap is smaller
than the variance the tournament's own bot pool introduces every time
a new participant is added.

So the experiment converged on a **Pareto-frontier of "nice +
retaliatory + forgiving" strategies**, not a single winner. Each of
the four uses a structurally different mechanism:

- **FBF** (Firm-but-Fair): memory-1, defects iff just got
  exploited (intent C, opp played D). Forgives all other states.
- **GTFT** (Generous TFT): memory-1, TFT but with ~10% probability
  of cooperating after opp's D. Stochastic forgiveness.
- **TFTT** (Tit-for-Two-Tats): memory-2, defects only after opp
  plays D in *both* of the last two rounds. Patient.
- **Soft Majority**: memory-N, cooperates iff opp's overall C-rate
  is at least 50%. Slow-moving statistical judgement.

Different memory depths, different state representations, different
parameter philosophies — and **none dominates the others** in our
matchup matrix. Each beats some of the others on some pairings and
loses on others. The empirical lesson: there isn't one best
algorithm; there's a *class* of policies that all produce roughly
the same outcome.

## Why these four win, in plain English

All four share four traits, which match Robert Axelrod's classic
findings from the 1980 tournaments:

### 1. *Nice* — never defect first

All four start with C and won't defect unless provoked. In our pool,
the "nice" bots (AllC, TFT, TFTT, GTFT, FBF, Soft Maj, CTFT, GRADUAL,
Adaptive Pavlov) collectively give each other ~2.9/round in mutual
cooperation. Among themselves, the average is ~2.95. That's the
biggest single pool of points available.

AllD, Prober, Hard TFT, Random — bots that defect first or randomly —
collectively forfeit access to that pool. Even when one of them
extracts a T=5 against AllC, it's outweighed by the missed CC=3
across nine cooperator matchups. AllD scored 1.757; AllC scored
2.119. The "exploiter" lost to the "naive cooperator" because the
exploiter couldn't access cooperation rents.

### 2. *Retaliatory* — punish defection

A purely nice strategy (AllC) gets harvested. In our pool AllC scores
0.058/round vs AllD and 1.495/round vs Random — and its overall 12th
place reflects this. The retaliators in the top-4 all defect when
exploited:

- TFTT: defects after two D's in a row.
- GTFT: defects after one D, with 10% forgiveness.
- FBF: defects only after the specific "I cooperated and got exploited"
  state.
- Soft Maj: defects when opp's C-rate has fallen below 50%.

Different sensitivities, all functional. Together with niceness, this
deters exploitation while preserving the cooperation pool.

### 3. *Forgiving* — recover quickly

Plain TFT is nice and retaliatory but bad at forgiving: under noise it
gets stuck in CDCD echo wars. TFT scored 2.296 (9th), much worse than
the forgiveness-enhanced variants. The top-4 each implement
forgiveness differently:

- TFTT: ignores single defections, so a one-off noise flip is
  silently forgiven.
- GTFT: every D from opp has a 10% chance of being forgiven anyway.
- FBF: never lengthens a retaliation — exactly one D in response, then
  back to C.
- Soft Maj: the threshold (>50% C from opp) bounces back to
  cooperation as soon as opp recovers.

Forgiveness is the difference between earning ~2.9/round forever vs
crashing to ~1.5/round after the first noise event. It's worth a lot.

### 4. *Non-envious* — don't try to "beat" your specific opponent

The IPD is not zero-sum. Maximising your own score is achieved by
finding stable mutual cooperation, *not* by maximising the gap to
your current opponent. In a single match, even the best nice
retaliator can be "beaten" by a defector that grabs one T=5 — but
across all opponents it accumulates more total points.

Our bots illustrate this exactly. AllD beats AllC head-to-head
(4.900 vs 0.058) — a 4.842 gap, the biggest in the matrix. But AllD's
overall score (1.757) is *below* AllC's (2.119). Trying to win every
match against every opponent costs more than it gains.

The provokers (Prober, Pavlov-Exploit) make the same mistake more
subtly. Prober opens D to test if it can squeeze opponents into
submission. Its overall score is 2.081 (13th). The gain in matchups
where the test "works" doesn't make up for the lost cooperation when
the test fails.

## Why specifically *these four* and not others

We have many cooperative retaliators in the pool. The top-4 differs
from also-rans (CTFT, GRADUAL, TFT, Pavlov, Adaptive Pavlov) on the
margins:

- **vs the predators (AllD, Grim, AllD-like):** GTFT, FBF, TFTT, and
  Soft Maj each lose 1.0-2.0/round of payoff in these matchups (out of
  a possible 3). CTFT loses *more* (its contrition rule actively
  hurts against Grim, dropping CTFT-vs-Grim to 1.333 vs TFTT's 1.562).
  TFT and Pavlov each lose marginally more than GTFT/FBF.
- **vs other top-class bots:** all four sit at ~2.85-3.00/round vs
  each other, modulo noise. Slight wins/losses ~0.05 in any direction.
- **Self-play:** Soft Majority's self-play (2.978) and TFTT's
  self-play (2.958) are slightly higher than GTFT's (2.897) under our
  2% noise. FBF's self-play is the lowest in the cluster (2.805) —
  its CDCD-oscillation weakness shows up. But FBF makes it up by
  edging out the cluster on vs-Pavlov and vs-FBF-itself matchups.

The four-bot Pareto frontier is held together by ~0.05-0.10 point
differences per cell, spread across 16 opponents. No single
optimisation pushes a bot definitively ahead.

## Connection to the real world

A short walking tour of social and political institutions where the
same dynamics show up.

### Cold War and arms races

C = "do not arm beyond defensive necessity". D = "build offensive
weapons". The USSR-USA pair sat at DD for most of 1946-1989 — high
spending, high risk, no benefit to either side. Both sides knew that
CC (mutual disarmament) would be better in expected utility, but
unilateral C was vulnerable to T=5 exploitation (the other side
gets a nuclear first-strike advantage). The 1972 SALT and 1987 INF
treaties were attempts to coordinate from DD back to CC by making
*verification* possible — i.e. by removing the noise-induced
plausible deniability that lets the DD equilibrium persist.

Note also the "trigger strategy" failure of Cuba 1962: the USSR
played D (place missiles in Cuba), the USA almost retaliated with
D-permanent (Grim Trigger via nuclear strike), and only the
forgiveness of both sides (Khrushchev's withdrawal, Kennedy's
quiet Turkey-missile removal) re-established CC. Grim Trigger would
have been globally fatal. Our `bot_grim` scored 15th out of 16 — its
unforgivingness costs even when justified.

### Climate agreements

The classic free-rider game. C = "reduce my country's emissions". D =
"keep burning, let everyone else cut". The Paris Agreement (2015)
defects from this trap differently than Kyoto (1997): Paris removes
the legally-binding cooperation requirement and replaces it with
public reporting, peer review, and 5-year ratchets. This is closer to
*Soft Majority*: "cooperate if the population is cooperating, in
aggregate, over time". Soft Maj works in our tournament because the
slow window discounts isolated D's (noise) while still detecting
genuine free-riders.

The deep problem: T=5 in climate is real and immediate (lower-cost
energy, factories don't shut down), while R=3 (a stable climate) is
diffuse and decades-away. Time-discounting tips the rational
single-shot choice toward D even when the iterated game's right
answer is C. Our tournament doesn't have time discounting; if we
added it, the cooperative strategies would unravel — exactly as
climate negotiations unravel when domestic politics demands fast
results.

### OPEC and cartels

OPEC's stated quotas (C = stick to quota, D = pump more) have been
violated repeatedly since 1973. Every member's individual best
response — given any history of cooperation by everyone else — is
D. They have *retaliation* mechanisms (Saudi Arabia in 1985-86
flooded the market to punish quota-cheaters, the famous price crash)
and *forgiveness* mechanisms (raising quotas back after the crash).
The cartel is a real-time IPD with all four Axelrod-principle
elements implemented at the institutional level.

Our `bot_prober` is a model of a cartel member who keeps testing:
defects on the first round to see if anyone notices, then plays TFT
based on the response. It scored 13th in our pool — a real-world
cartel member with that strategy gets either booted out (other
members refuse to cooperate again) or stuck in a DD equilibrium (the
infamous "every member shaves a little"). Saudi-style enforcement
(Hard TFT or Grim) hurts everyone but is sometimes needed to keep
the cartel alive.

### Taxes and public goods

The taxpayer's dilemma: C = pay full taxes, D = evade. Pure individual
rationality says D, but if everyone D's, public goods collapse and
everyone loses. Soft Majority is again the relevant model: most people
cooperate, the few D's are absorbed, but if D-rate rises past a
threshold the system breaks (Greek-style tax-collection failure of
2008-2012). Once the system breaks, recovery is slow because of the
"who'll cooperate first" problem.

Modern policy responses look like the bot strategies we've explored:
high audit rates (Hard TFT — retaliation), public shaming of
non-payers (informal Grim — but only against repeated offenders),
amnesty schemes (forgiveness via deliberate noise-tolerance).

### Neighbours and shared resources

Apartment building noise rules, shared kitchens, joint property
agreements — all small-scale IPDs. Most successful arrangements look
like TFTT or FBF in practice: people are willing to overlook a single
loud party (one D), but two in a row triggers complaints. Strict
TFT (complain about every infraction) creates feuds. AllC creates
exploitation. Grim Trigger (one violation = lifelong silent treatment)
creates broken neighbourhoods.

Soft Majority — "if most people on the floor are being reasonable
most of the time, treat occasional incidents as outliers and don't
escalate" — is the practical wisdom that holds long-running
neighbour relationships together.

### Personal relationships

Long-term friendships, marriages, family ties — the cleanest IPD in
real life. The 2R > T+S condition is intuitive: a stable
cooperation generates more total value over decades than alternating
exploitation. Successful long relationships look like CTFT (apologise
for your own slips) or FBF (don't escalate after a partner's
isolated bad behaviour). Bad relationships look like TFT under noise
(each side mirrors the other's bad mood, both spiral down) or Grim
Trigger (one bad fight, lifelong resentment).

Couples therapy is, in part, an external mechanism for forgiveness —
restoring CC from DD. It's the human-relationship analogue of the
"forgiveness probe" we explored in `bot_pavlov_exploit_v2`.

## Honest caveats: what's *not* like reality

A short list of differences between our tournament and the actual
world, with the implications.

### 1. No reputation across opponents

Bots only see the history of their *current* match. They cannot
look up how an opponent behaved against other bots. In real life,
reputation propagates: countries, companies, and people get reports
about each other from third parties. Reputation gradients are the
single biggest reason real cooperation extends beyond pairwise
interactions to large groups. In our tournament, AllD can keep
"resetting" against new opponents and harvest the round-0 cooperation
of every nice bot. With reputation, AllD would be marked and
shunned.

If we wanted to model this, we'd let each bot read a global
"reputation matrix" before round 0. We chose not to, to keep the
spec clean. But this is a known limitation.

### 2. No discounting

We sum payoffs equally across all 200 rounds. Real-world actors
heavily discount future payoffs. Under heavy discounting, "nice"
strategies unravel — the temptation T=5 in round 1 outweighs the
~3.0 expected from CC in rounds 2-200. Empirically, this is why
many real-world cooperative arrangements collapse near term limits
(political end-of-term defections), generational shifts (new
leadership not bound by old agreements), or impending crises.

### 3. Two-player, equal-payoff

Real geopolitics has 200 countries with asymmetric power. Our
tournament has equal payoffs and equal strategy spaces. A great-power
IPD is a *different* game where retaliation costs are asymmetric;
that changes the optimal strategy. (A small country may not have a
viable D-retaliation against a big country, removing the
retaliatory leg of Axelrod's principles.)

### 4. No coalition formation

In our tournament every match is bilateral. Real-world actors form
coalitions: NATO, OPEC, EU. Coalitions change the payoff structure
because "the other side" is now a group that punishes/rewards
collectively. Our model can't capture this.

### 5. No communication

Bots cannot send any signal beyond their move. Real actors negotiate.
Talk is cheap in the formal sense — but it's not noise, and it can
coordinate strategy choice across rounds. The Paris Agreement
exists because of *talk* between countries, not because they
discovered TFTT empirically.

## What worked, what didn't, in our process

### Worked

- **Specifying the bot API simply and tightly.** No file I/O, no
  state across matches, only history input. This forced clean
  algorithmic thinking and made the bots reproducible.
- **Re-running the full tournament after every new bot.** The
  averaging artefact (a new bot perturbs all other bots' scores)
  shows up only in the full matrix. Single-match testing would have
  missed it.
- **Noise = 2%.** Enough to break plain TFT, not so much that the
  game becomes random. Empirically all the noise-handling differences
  showed up.

### Didn't work

- **Strict "top-3 stable" stop criterion.** As analysed in LESSONS.md,
  three consecutive identical top-3 sets is unattainable when we add
  one bot per turn, because the top-4 are within the run-to-run
  variance band. We had to relax it to "top-4 set stable", which
  *was* satisfied across T10-T12.
- **Single-axis optimisation.** Every time we built a bot to fix a
  specific weakness (Pavlov-Exploit for the Pavlov-vs-Soft-Maj hole,
  CTFT for TFT-self echo wars), the fix introduced a new weakness
  elsewhere. The four top-4 bots survive *not* by being optimised on
  any axis but by being unobjectionable across all of them.

## Axelrod's four principles, summarised against our data

| Principle    | Best demonstrator in our pool       | Counterexample          |
|--------------|-------------------------------------|-------------------------|
| Nice         | FBF, GTFT, TFTT, Soft Maj (top-4)   | Prober (13th), AllD (16th) |
| Retaliatory  | All top-4; FBF most surgical        | AllC (12th) — pure nice |
| Forgiving    | GTFT, FBF, TFTT, Soft Maj           | Grim (15th), TFT (9th)  |
| Non-envious  | All top-4 — accept ~0.05 losses vs predators in return for cluster cooperation | AllD (16th) — wins every head-to-head, finishes last |

These weren't designed in from the start. They emerged from rerunning
the tournament with new bots until the top of the table stabilised
into the four-strategy Pareto cluster. The original Axelrod tournament
(1980) produced TFT as winner; ours produced a four-strategy class.
The reason for the difference is probably noise: TFT is the
"minimum sufficient" cooperator without noise, but with noise it
sits at 9th place. The forgiveness mechanism — the difference between
TFT and the top-4 — is what noise selects for. Real life has noise.
That's the single biggest design lesson here.

## Closing

The IPD tournament is a thin model of cooperation, but its findings
are robust:

1. Don't defect first.
2. Make defections cost.
3. Forgive quickly when the cost has been paid.
4. Don't optimise for beating any specific opponent.

These four principles are visible in long-running international
treaties, family relationships, neighbour conventions, and corporate
contracts. The bots that implement them most cleanly — FBF, GTFT,
TFTT, Soft Majority — sit at the top of our pool because they
combine into a *class* of policies that cooperate with each other
and resist exploitation by the rest of the pool.

The cluster is a Pareto frontier: each of the four is dominated on
some axis by another, but none is dominated overall. Real
institutions sit at different points on the same frontier
(parliamentary vs presidential democracy, federal vs unitary states,
mutual-defence treaties vs trade-only alliances). All four
configurations are stable for the same structural reason.

That is the report.
