# Iterated Prisoner's Dilemma — Tournament Report

After 17 round-robin tournaments with 17 strategies, this report
summarises what wins, why, and what the results say about real-world
cooperation problems.

## 1. Tournament setup

- Engine: `tournament.py` (stdlib only, no external deps).
- Format: round-robin, every bot plays every other bot AND itself.
- Match length: **200 rounds**.
- Trembling-hand noise: every intended move is flipped with
  probability **0.02** before being recorded. Both bots see the
  same noisy history. Models "I meant to cooperate, but you saw
  me defect".
- Each pair is repeated **3 times** with independent noise draws
  to average out the noise.
- 17 bots in the final field. Full list with one-line strategy
  summary in §3.
- All seeds tested: 42, 43, 44, 45, 100. Five independent runs.
- Bots are pure functions of `(my_history, opp_history)`. They
  cannot read opponent's source, files, or network.

The matrix follows the canonical Axelrod payoff
(T=5, R=3, P=1, S=0), giving R > P > S, T > R, 2R > T+S. Mutual
cooperation pays 3 each per round; mutual defection pays 1 each;
unilateral defection earns 5 (against 0 for the sucker).

## 2. Final ranking

The robust top-5 across all 5 seeds (rows are positions a bot held
across runs 013–017; **bold** means top-3 for that seed):

| bot              | seed 42 | seed 43 | seed 44 | seed 45 | seed 100 | top-3 count |
|------------------|---------|---------|---------|---------|----------|-------------|
| **bot_octft**    | **#2**  | **#1**  | **#1**  | **#1**  | **#1**   | **5 / 5**   |
| bot_contrite_tft | **#1**  | **#2**  | #5      | **#3**  | **#2**   | 4 / 5       |
| bot_gradual      | **#3**  | #6      | **#2**  | **#2**  | #6       | 3 / 5       |
| bot_tit_for_tat  | #5      | **#3**  | **#3**  | #4      | #7       | 2 / 5       |
| bot_omega_tft    | #4      | #5      | #4      | #5      | #4       | 0 / 5       |
| bot_generous_tft | #7      | #7      | #7      | #7      | **#3**   | 1 / 5       |
| bot_cycle_det.   | #6      | #4      | #6      | #6      | #5       | 0 / 5       |

**Verdict: bot_octft is the seed-robust winner** (top-3 in 5/5
runs, #1 in 4/5, #2 by 0.57 points in the remaining one).

The bottom of the ranking is also seed-stable (always_d last, grim
second-to-last, always_c third-from-last across all seeds). The
ordering uncertainty is concentrated in the top-5: those five bots
are all within ~25 points (≈ 5% of the mean) and trade positions
based on the noise realisation. Below them, gaps are >20 points
and ordering is stable.

## 3. The 17 strategies

| bot                | one-line description                                                         |
|--------------------|------------------------------------------------------------------------------|
| bot_always_c       | always cooperate. The naive dove.                                            |
| bot_always_d       | always defect. The pure predator.                                            |
| bot_random         | 50/50 random.                                                                |
| bot_tit_for_tat    | C first, then mirror opp's last move. Axelrod's canonical winner.            |
| bot_grim           | C until opp defects once, then D forever.                                    |
| bot_generous_tft   | TFT but forgive D with probability ~10%.                                     |
| bot_tf2t           | retaliate only after TWO consecutive Ds.                                     |
| bot_pavlov         | win-stay-lose-shift. Repeat last move if got R or T; flip if got P or S.     |
| bot_adaptive_tft   | TFT, but lock into AllD after 5+ consecutive Ds from opponent.               |
| bot_alternator     | CDCDCD... forever. Probe and exploit fixed-step opponents.                   |
| bot_cycle_detector | look for repeating period-2 or period-3 patterns in opp; exploit if found.   |
| bot_gradual        | TFT, but after n-th opp D, retaliate n times, then 2 C as olive-branch.      |
| bot_prober         | D,D in opening; if opp didn't retaliate, switch to AllD; else TFT.           |
| bot_handshake      | DDDC opening signature; if opp matches, cooperate forever; else TFT.         |
| bot_contrite_tft   | TFT + 2-round apology window: if I flipped C→D, play C unilaterally.         |
| bot_omega_tft      | TFT + apology + deadlock-break + randomness counter → AllD switch.           |
| bot_octft          | CTFT + Omega's deadlock detector. NO randomness counter / no AllD switch.    |

The first 5 (always_c through grim) form the canonical Axelrod
pantheon. The rest were added one-by-one across runs 002–013.

## 4. Why bot_octft wins (mechanism)

octft's source is ~165 lines, but its rule fits in 4 lines:

1. First move: C.
2. If in either of the last 2 rounds I *intended* C but *observed*
   my own D (a noise flip), play C this round (apology).
3. Else if the last 3 rounds were strict CD/DC alternation, play
   C this round (deadlock-break).
4. Else play opponent's last observed move (TFT).

Why these mechanisms matter, and why omitting one mechanism (Omega
TFT's "switch to AllD if opponent looks random") matters too:

### 4.1 Apology window

Plain TFT in a noisy world has a fatal flaw: a single noise flip
starts a permanent feud against another TFT-like opponent. I
intended C, world flipped it to D, opponent's TFT retaliates with
D, my TFT retaliates with D, etc. We're stuck in DD until another
noise flip accidentally fixes us.

CTFT (Wu & Axelrod 1995) fixes this asymmetrically: when **I
notice that I flipped**, I unilaterally play C to apologise. The
opponent's retaliation is justified, so I should absorb it without
counter-retaliating.

Cost: nothing against pure cooperators (apology never fires).
Benefit: ~5-30 points per match vs other TFT-family bots,
depending on how many noise events hit the apology window.

### 4.2 Deadlock-break

What if the noise hit the OPPONENT's side? CTFT's apology can't
fire (I never intended C wrongly). The result is a CD/DC echo: I
retaliate for opp's noise-D, opp retaliates for my just-D, we
alternate.

Omega-TFT (Slany & Kienreich 2007) adds a "deadlock detector":
after 3 rounds of strict alternation, play C unilaterally to
break the echo. This is *pattern-based forgiveness* rather than
introspective forgiveness.

Cost: a couple of suckered rounds against alternator-style bots.
Benefit: ~5-30 points vs other TFT-family bots when noise hits
opp's side.

### 4.3 Why DROP Omega's randomness counter

Omega-TFT also had a "randomness counter": every time the opponent
seemed to play arbitrarily (D when you'd expect C, switching too
often), increment a counter; if the counter exceeds a threshold,
switch to AllD permanently against this opponent.

This works well against bot_alternator (Omega gets ~592 vs ~432
for octft) and bot_random (~486 vs ~437). But it has terrible
false positives against bot_prober, which opens with two Ds to
probe: that early "non-cooperative" behaviour trips Omega into
permanent AllD, even though prober is willing to cooperate from
round 4 onwards. Omega vs prober: ~340. octft vs prober: ~580.

Net: dropping the randomness counter loses ~50–160 points vs
exotic opponents and gains ~50–240 vs the prober class. Across
the whole field, dropping it is the right trade.

### 4.4 Why two mechanisms are better than one or three

Single-mechanism bots (TFT, generous TFT, CTFT, Pavlov) each have
a specific noise-failure-mode they don't fix.

Three-mechanism bots (Omega TFT) have a brittle component
(randomness counter) that pays off in narrow cases and fails badly
in others.

Two complementary mechanisms (CTFT's apology + Omega's
deadlock-break, no other moving parts) gives octft full coverage
of noise-induced feuds without any false-positive lockdowns. The
result: a strategy that hits 590+ in self-play (close to CC
ceiling of 600 minus the 24 pts noise tax) and 575+ against most
other top-class bots.

## 5. Why the bottom bots lose

- **always_d**: gets exploited by everyone who can detect it
  (most of the field). Wins against always_c (~970) but that's
  one cell. Across the whole field, average is ~350.
- **grim**: locks into DD forever after the first noise-flip,
  even though both bots would prefer CC. The lack of any
  forgiveness mechanism makes grim a one-shot sucker for noise.
  ~390 average.
- **always_c**: gets fleeced by always_d (gets 0 vs 5×200=1000)
  and prober. ~420 average.
- **prober**: its opening D,D triggers grim and adaptive_tft into
  AllD mode. Net: prober wastes 2 rounds vs cooperators and gets
  locked out by retaliators. ~430 average.
- **random**: cooperates only half the time, so reciprocators
  match its 50%. Loses to detectors that exploit unpredictability.
  ~415 average.

## 6. Real-world parallel

The 4 principles Axelrod distilled from his 1980 IPD tournament
all show up in my results:

### 6.1 Be nice (don't defect first)

In my field, the bots that open with D (prober, handshake,
always_d) all rank in the bottom half. Even "smart" probes
(prober's two-D opening) lose >100 points to retaliation classes
that don't trust them afterwards.

**Real world:**

- *Cold war.* Both superpowers spent decades sliding from "be
  nice" (immediate post-WWII alliance) to "be ready to retaliate"
  (mutually assured destruction). The detente periods came when
  one side credibly signalled "no first strike". Reagan's "trust
  but verify" was a TFT-with-handshake posture.
- *Trade*: WTO's founding principle is most-favoured-nation
  (extend the same tariff to everyone). It's a "nice" posture: by
  default, treat partners cooperatively, then escalate only on
  documented violations. The 2018 US tariff escalation broke this
  by opening with D, and triggered the predicted retaliation
  cascade.
- *Marriages, friendships*: opening with a probe ("I'll test if
  they really love me by being mean") is the prober strategy.
  Empirically it ranks 14th out of 17. Don't.

### 6.2 Retaliate (don't be a pushover)

always_c gets crushed in my field. So does tit-for-two-tats —
the latter is actually too forgiving against alternator
(alternator exploits the 2-strike grace) and finishes 9th.
**Retaliation must be visible, quick, and proportional.**

**Real world:**

- *NATO Article 5.* The whole credibility of mutual defence is
  "if you defect against any member, all members retaliate". A
  single failure to honour it would collapse the deterrent.
  Article 5 is a TFT-class commitment.
- *Cartels (OPEC).* Members who quietly overproduce (defect) are
  publicly named and assigned penalty quotas. Without
  retaliation, the cartel collapses immediately because
  unilateral overproduction is always individually optimal. OPEC
  is a fragile retaliatory equilibrium.
- *Personal*: "doormat" partners in relationships get exploited
  systematically — the literature is consistent. Setting a price
  for being mistreated (clear consequence + ability to act on
  it) is what TFT does.

### 6.3 Forgive (don't hold grudges)

This is where my results diverge most sharply from grim
strategies. **grim ranks 16/17 across all seeds.** The fact that
grim — which "punishes defection harshly" — loses to softer
strategies is the IPD's most counter-intuitive lesson.

The strategies that beat grim do so by accepting that some Ds
are random (noise) or come from edge-cases (probe), and they
restart cooperation as fast as is consistent with not getting
exploited. octft's two forgiveness mechanisms are the embodied
version of this.

**Real world:**

- *Cold war again.* The hotline between Washington and Moscow
  (set up 1963 after the Cuban missile crisis) is a forgiveness
  channel: it lets each side say "the missile we just launched
  was a misfire / training exercise / drill" — apology window in
  international form. Without it, every accidental D would
  cascade to DD permanently.
- *Climate negotiations.* Countries that miss an emissions
  target by 2% are typically not expelled from the regime. The
  IPCC framework explicitly allows "ratchet up over time".
  Permanent grim-style punishment of a missed target would
  collapse the regime, because EVERY country misses targets
  occasionally due to political turnover, recession, etc.
- *Personal.* Couples therapy literature: "the ability to repair
  after rupture" predicts relationship survival far better than
  "absence of rupture". Apology and forgiveness are the
  mechanisms.

### 6.4 Don't envy (it's not about winning the match)

In IPD, "winning your match" by getting 5×200=1000 points vs a
sucker is **objectively worse** than "drawing your match" by
mutually cooperating for 3×200=600 points each, *across the
whole tournament*. Why? Because the always_c bot only wins
against the equally bad always_d bot in one cell; everywhere
else, it's an inefficient way to spend rounds.

This is the most subtle Axelrod principle, and it's also the one
that's hardest to internalise in real life. In my data: bots
that *only* try to "outscore their opponent in each match" (like
prober trying to exploit cooperators) end up with lower TOTAL
score than bots that "play for high joint score in most
matches" (like octft).

**Real world:**

- *Trade is positive-sum.* Mercantilism's core mistake is
  treating trade as a zero-sum match ("we win if they lose").
  Two countries with comparative advantage both get richer from
  trade. The cell score isn't 5 vs 0; it's 3 vs 3, in absolute
  terms much better than 5 vs 0 summed against many partners.
- *Climate.* "Why should WE cut emissions if China doesn't"
  treats it as a zero-sum match. The actual game is the
  whole-tournament: aggregate atmospheric CO2. A country that
  "wins" by free-riding still suffers the climate consequences.
- *Personal.* "Winning the argument" with your spouse loses you
  the marriage. The match-vs-tournament distinction is exactly
  the same problem: optimising for the local cell-score breaks
  the cooperation that maintains every future cell.

## 7. Pattern: when does the world produce DD?

My tournament shows the conditions under which two
nice-reciprocating bots fall into mutual defection:

- **Noise + no forgiveness.** A single random flip can lock TWO
  perfectly-aligned cooperators into permanent DD. This is the
  classic security dilemma in international relations: nobody
  "intended" to start the arms race, but each side's defensive
  buildup looked like aggression to the other, and the
  retaliatory loop became self-sustaining.
- **Probing in opening rounds.** prober's strategy ("test if
  they're a pushover, then exploit") was tried by all post-Cold-
  War "great-power competition" actors. Against retaliators it
  destroys ~100 points of cooperation per match for a marginal
  short-term gain. Iraq 2003, Crimea 2014, and several trade
  escalations are real-world prober openings whose
  cooperative-equilibrium cost is still being paid.
- **Cartel discipline failures.** If even one "trusted partner"
  is observed to defect (without immediate visible
  retaliation), other partners' incentive to defect increases.
  OPEC, NATO burden-sharing, the EU's fiscal compact all show
  this dynamic.
- **No apology channel.** Without a way to communicate "that
  was a mistake, here's the correction", noise events compound
  irreversibly. Modern diplomacy invests heavily in apology
  infrastructure (hotlines, formal note-of-regret protocols,
  back-channel envoys) precisely because the apology mechanism
  is worth more than the deterrence mechanism in noisy
  environments.

## 8. What my model captures, and what it doesn't

**Captures well:**

- Cooperation evolves from selfish-but-iterated agents. No
  altruism needed.
- Noise + lack of forgiveness = death spiral. The dominant
  mechanism in many real conflicts.
- The "nice + reciprocate + forgive" class is structurally
  stable: many specific bots in this class beat any bot outside
  it. This matches the durability of cooperative norms in many
  real settings.
- Brittle exploitation modes (Omega's randomness counter, grim's
  permanent punishment) usually hurt the holder more than the
  target. Real-world parallel: "absolute deterrents" tend to be
  destabilising rather than stabilising.

**Captures poorly:**

- Two-player only. Real cooperation problems have
  N-player free-rider dynamics that change the equilibria
  qualitatively (climate, public goods). My field doesn't model
  this.
- Pairwise round-robin assumes every actor must interact with
  every other actor equally. In reality, actors choose partners,
  signal reputation, exclude defectors. Reputation effects
  multiply the "be nice" advantage.
- Bots can't communicate explicitly. Real diplomacy has
  signalling, treaties, observers. The "apology" in my octft is
  a unilateral move; real apologies are speech acts that change
  the receiver's beliefs.
- All bots have the same memory. Real actors have very different
  cognitive capacities, lifespans, and stakes. A 2-year-old
  startup negotiating with a 200-year-old bank is not a
  symmetric game.
- Payoff matrix is constant. Real-world payoffs shift over time
  (tech, demographics, climate). Strategies optimal at one
  payoff matrix can fail catastrophically at another.

**Surprises I didn't expect:**

- The TOP-3 reshuffles even with no bot changes, just noise-seed
  variation. The intuition "tournament gives THE winner" is
  wrong — it gives a winner WITHIN ~3% of several others. The
  honest scientific answer to "who's best?" is "this tier is
  best; within the tier, ordering is noise".
- bot_grim (the strict retaliator) finishes near the very
  bottom. In casual intuition, "punish defection harshly" feels
  like a strong strategy. In a noisy iterated world it's
  suicidal: you defect-lock with every opponent including
  yourself.
- bot_always_d, the predator, is dead last. Pure exploitation
  has no equilibrium in a population of reciprocators.

## 9. Practical advice (with honest caveats)

If you're modelling a real cooperation problem with these
results:

1. Open cooperative. The cost of going first is ≤5 points; the
   cost of starting in defection is ≥100 points across the
   tournament.
2. Retaliate quickly and proportionally. One-for-one is enough.
   Don't escalate.
3. Build apology channels. They are worth more than punishment
   channels in noisy environments. Hotlines, formal regret
   protocols, fast-de-escalation paths.
4. Don't envy. If you are getting 3 and they are getting 3,
   that's the long-run win. Optimising "I should get 5" turns
   the relationship into 1/1 quickly.
5. Avoid brittle "exploit modes". Omega TFT was beaten by its
   simpler sibling octft because the exploit-mode produced
   false positives that cost more than the exploit gains.

Caveats:
- These rules optimise for *long iterated* games where you'll
  meet the same partner many times. One-shot games with
  asymmetric stakes are a different problem (e.g. ultimatum
  game) and these rules don't apply.
- In games with N > 2, free-rider dynamics dominate and you
  need additional mechanisms (reputation, exclusion). My model
  doesn't cover these.
- In games where the payoff matrix is changing (T, R, P, S
  shifting over time), strategies that were dominant can
  suddenly become dominated. Real-world example: climate
  policy's matrix is shifting toward higher P (mutual
  defection cost) over time, which changes who can rationally
  defect.

## 10. Files of record

- `tournament.py` — engine (~240 lines, stdlib only).
- `bots/` — 17 strategies + `API.md`.
- `bots/_failed/` — none; every added bot was kept.
- `SCORES.md` — all 17 tournament runs with per-bot payoff
  matrices.
- `STRATEGIES.md` — running commentary on what works, what
  fails, and why.
- `LESSONS.md` — 17 distilled methodological lessons.
- `REPORT.md` — this file.
- `STOP` — convergence marker.

## 11. Closing

The IPD's central claim — "even purely self-interested agents
can sustain cooperation if they play many rounds with memory" —
is robustly confirmed by these 17 tournaments. The strategy that
embodies this most efficiently is bot_octft: it's nice, it
retaliates, it has TWO complementary forgiveness mechanisms, and
it has NO exploitation mode. That last absence is the key: in
a noisy world, the temptation to optimise for "wins" against
weak opponents costs more than it pays.

The mapping to real cooperation problems is not metaphorical —
the same payoff structure literally underpins arms races,
climate negotiations, cartels, common-pool resources, and
long-term relationships. The Axelrod principles (nice,
retaliatory, forgiving, non-envious) are the same recommendation
in all of them.

The strongest empirical result, robust across seeds:
**forgiveness is not weakness. It is the most expensive
mechanism a strategy can lack.**
