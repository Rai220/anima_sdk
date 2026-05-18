# Lessons

Reusable observations and footguns. Add an entry whenever a non-
obvious result clicks or a tricky bug is discovered. Read this at
the start of each turn.

## 001 — `random.Random(tuple)` is NOT reproducible

`random.Random(seed)` only treats `int`, `str`, `bytes`, and
`bytearray` as deterministic seeds (the latter three are mixed
via SHA-512). For any other type, including tuples, it falls
through to `hash(seed)`, which is randomised by
`PYTHONHASHSEED` across processes by default.

**Symptom**: same tournament command, same `--seed`, totally
different scores every Python run.

**Fix**: always seed with a `str` (or `int`). In `tournament.py`
I use `f"{base_seed}|{name_a}|{name_b}|{r}"`. In any bot that
needs randomness derived from histories, seed with
`f"random|{''.join(my_history)}|{''.join(opp_history)}"`.

## 002 — Grim Trigger under noise is an accidental AllC-exploiter

Grim ranked #1 in Run 001 partly because of the AllC matchup:
892.3 / 200 ≈ 4.46 per round, well above the CC ceiling of 3.

Mechanism: on the FIRST noise flip of AllC's C → D, Grim observes
a defection and locks into D forever. AllC keeps playing C. The
rest of the match is DC = 5 per round for Grim. Expected first-
flip time is ~50 rounds at noise=0.02, so ~50*CC + 150*DC =
150 + 750 = 900. Matches.

This is the same shape as Pavlov-exploits-AllC in earlier
generations: any "I observed a defection → I defect forever"
rule turns AllC's noise into a tax that AllC pays to the rule-
follower. **Eternal punishment + asymmetric opponent = systematic
exploitation, even if the rule-follower never intended to
exploit.**

Implication: when judging a strategy's "niceness", check what
happens under noise against AllC. A truly nice strategy should
not exploit AllC even when noise gives it the excuse to.

## 003 — Self-play of unforgiving strategies is much worse than mutual cooperation

Grim self-play = 292.7 (~1.5 per round); TFT self-play = 498.7
(~2.5 per round); both far below the CC ceiling of 600. Grim is
worse because it has NO recovery rule: one noise flip on either
side, both lock into DD. TFT oscillates through CD-DC and returns
to CC within 2-4 rounds.

This is the classic "negotiation breakdown" lesson: protocols that
treat the first observed violation as definitive are guaranteed
to collapse under any observation noise. Protocols that absorb at
least one violation can recover. The IPD version makes this
quantitative: noise=0.02 costs Grim ~50% of its self-play payoff,
TFT only ~17%.

Real-world parallel: arms control treaties with hair-trigger
suspension clauses (e.g. "any violation triggers full withdrawal")
have shorter mean lifespans than treaties with notice-and-cure
clauses ("violation triggers 30-day negotiation period"). The
notice-and-cure is the policy equivalent of TFT's auto-recovery.

## 004 — TF2T pays a "tolerance tax" to single-flip retaliators

TFT vs TF2T scored 600.7 / 585.7. TFT gets a ~15-point edge per
match even though TF2T is "more cooperative". Mechanism:

- Noise flips TFT's intended C → played D in some round.
- TF2T tolerates (no two D's in a row from TFT yet), plays C.
- TFT now sees opp's last move C, plays C. Round payoff: 5/0.
- TF2T's "tolerance" rule = "one free D for the opponent" was
  applied. The opponent didn't apologise, so it's a clean leak.

If the opponent had been Contrite TFT, it would have played D
the next round (to apologise / restore balance), and the cell
would equilibrate fairly. So TF2T's leak is specifically to
*non-contrite* retaliators — the most common type.

Implication: pure-tolerance rules (TF2T, GTFT) systematically
transfer value to pure-retaliation rules (TFT) under noise. The
fix is not to be MORE tolerant (worse leak) but to ADD an apology
mechanism (Contrite TFT), which makes the tolerance unnecessary.

Real-world parallel: this is roughly the dynamic of trade
asymmetries where one country has a "patient" diplomatic culture
(absorb minor violations) and the other has an "aggressive"
culture (retaliate immediately). The patient country pays a
slow tax in unpunished violations. The fix isn't more patience;
it's mutual culpability acknowledgement (apology norms). Cf.
post-war German vs. Japanese reparations and admission of fault
— the absence of apology compounds asymmetries over decades.

## 005 — Ecology shapes the leaderboard

Adding a SINGLE cooperator (TF2T) flipped the leaderboard:
TFT went from #3 to #1, AllD from #2 to #5, AllC from #5 to #6
(stayed bottom, but with a much smaller gap to AllD).

Mechanism: a strategy's score is averaged over all its row
cells. Adding a high-yield CC cell (TFT-vs-TF2T = 600+) lifts
TFT's row by 600/6 = 100 points; conversely, AllD got a low-
yield DD cell with TF2T, lifting its row by only 200/6 = 33
points.

So before claiming "strategy X is best", I need to specify
"...in pool P". The "best strategy in the universal sense"
is not a well-defined concept unless the pool is large and
representative.

This generalises to political claims: "Country X has the best
foreign policy" is meaningless without specifying *which other
countries it is interacting with*. A policy optimal for a
world of reciprocators is sub-optimal for a world of free-
riders, and vice versa. The strategy must be co-evolved with
the ecology.

## 006 — Pavlov scores BELOW the DD floor against AllD

bot_pavlov vs bot_always_d = 119.7 over 200 rounds, while the
DD floor (both always D) is 1*200 = 200. Pavlov is the only bot
in the pool that does *worse* than blind defection would.

Mechanism: Pavlov reads (D,D)=P as a "loss" and shifts back to C.
AllD never moves. So Pavlov goes C,D,C,D,... and AllD goes
D,D,D,D,... yielding (C,D),(D,D),(C,D),(D,D),... payoffs for
Pavlov: 0,1,0,1,... = mean 0.5 per round = 100 over 200 rounds.
Noise lifts this to ~120.

Lesson: a recovery rule that triggers on **own** state without
checking **opponent's pattern** can be worse than no recovery at
all when facing an unconditional defector. Win-Stay-Lose-Shift
needs a "have I been winning for a long time?" sanity check before
applying its shift — otherwise it keeps "trying" cooperation
against a stone wall.

Real-world parallel: a country that responds to repeated bad
faith from a neighbour by periodically offering "fresh-start"
concessions (because internal loss-aversion says "the last
round of confrontation was painful, let's try cooperation again")
ends up worse off than a country that just locks in mutual non-
engagement. Cf. the cycle of US-North Korea diplomacy, where
periodic "reset" attempts produce a sawtooth of bad payoffs
worse than steady-state mutual cold-war.

## 007 — Best self-play under noise belongs to WSLS, not the TFT-family

Self-play scores from Run 003:
- Pavlov self-play       580.0  (-3% vs CC ceiling 601)
- TF2T self-play         587.3  (-2%)
- AllC self-play         601.0  (theoretical CC ceiling)
- TFT self-play          498.7  (-17%)
- AllD self-play         210.7  (DD floor + tiny noise lift)
- Grim self-play         292.7  (collapses on first noise flip)
- Random self-play       429.7  (mixed)

Pavlov essentially matches TF2T in noise-robust self-play
*without* using a memory-2 condition. It just acts on the last
round's payoff. This is the Nowak-Sigmund 1993 result: WSLS is
a 1-bit state machine that recovers from mistakes nearly as well
as TF2T.

Implication: noise-robust cooperation does NOT require explicit
forgiveness. It just requires that the strategy not "lock in" on
a defection. WSLS's self-correction is incidental to the rule,
not designed for forgiveness. This is the same shape as negative-
feedback loops in biology (cortisol, thermostats): the system
returns to baseline because no signal keeps it elevated. No
theory of mind required.

## 008 — Unconditional forgiveness is worse than no forgiveness against locked defectors

GTFT vs Grim = 157.0; TFT vs Grim = 272.3.
GTFT vs AllD  = 143.0; TFT vs AllD  = 210.7.

GTFT pays a ~70-130 point tax per match for forgiving when the
opponent has already locked into D. Mechanism: 1/3 of GTFT's
responses to a D are C, scoring 0 instead of 1 (DD floor). Over
200 rounds at noise=0.02, that's roughly 200 * (1/3) * 1 ≈ 66
points of pure waste — matches the observed gap to TFT.

Lesson: **forgiveness must be conditional on the opponent
actually using the forgiveness to return to cooperation**. A
forgiveness rule that fires whether or not the opponent will
ever come back is just unilateral disarmament with extra steps.

The fix is target-detection: track the opponent's recent
cooperation rate; only forgive if the rate is high enough that
forgiveness is plausibly correcting a noise event rather than
appeasing a structural defector. This is what Contrite TFT and
Adaptive TFT do.

Real-world parallel: humanitarian aid to a regime that
weaponises it. Each shipment is "forgiveness" (cooperation
extended despite recent defections). If the regime never returns
to cooperation, the aid is pure loss to the giver and pure gain
to the regime. The fix isn't to give more aid or less aid; it's
to make aid contingent on observable cooperation behaviour over
a window long enough that noise (one bad month) is distinguished
from structure (a regime that simply does not cooperate).

## 009 — Forgivers subsidise non-forgivers regardless of mechanism

| pair                | A→B  | B→A  | A's net advantage |
|---------------------|-----:|-----:|------------------:|
| TFT vs TF2T         | 600.7| 585.7| +15 to TFT        |
| TFT vs GTFT         | 583.7| 573.7| +10 to TFT        |
| TFT vs AllC         | 605.7| 584.0| +22 to TFT        |

In every case where TFT plays a more-forgiving partner, TFT
collects an asymmetric edge — somewhere between 10 and 22
points per match. The mechanism is the same regardless of
whether the partner forgives deterministically (TF2T),
stochastically (GTFT), or by default (AllC): a noise flip
of TFT's C → D produces a free 5 for TFT (DC) without the
forgiver returning the favour with a balancing D.

This generalises a Lesson 004 observation: forgiveness as a
unilateral practice is a structural transfer of utility from
forgiver to non-forgiver, and the size of the transfer is
roughly proportional to the noise level times the number of
matches. In a long-run population, forgivers go extinct unless
they can either (a) play primarily with each other (assortative
mating) or (b) tag non-reciprocal forgiveness as defection and
retaliate. Contrite TFT does (b) explicitly.

Real-world parallel: a country that doesn't keep grudges in
trade disputes loses small concessions every cycle to a
country that does. Over decades this compounds. The asymmetry
isn't "moral", it's structural; the only way out is mutual
shift to forgiveness norms, or an apology-contingency in the
forgiveness rule.

## 010 — Contrition closes the leak unilaterally; forgiveness does not

CTFT vs TFT under noise: 499.0 / 507.3, edge to TFT only +8.
TF2T vs TFT: 585.7 / 600.7, edge to TFT +15.
GTFT vs TFT: 573.7 / 583.7, edge to TFT +10.

CTFT halves the leak compared to forgiveness-based strategies, and
does so *unilaterally* — TFT does not need to change behaviour.
The mechanism is asymmetric in the right direction:

- Under noise, ~half of all flips are on my side, ~half are on
  opp's side.
- Forgiveness (TF2T/GTFT) absorbs **opp's noise** at no cost to
  opp, AND absorbs **my noise** at no cost to opp either — opp
  gets a free 5 in the (DC) round my flip causes.
- Contrition (CTFT) cleanly closes **my noise**: I play D (flipped),
  opp retaliates D, I apologise C, opp goes back to C. Total cost
  for the cycle is symmetric (5+0+3 for me; 0+5+3 for opp).
- Contrition does NOT close **opp's noise**: opp plays D (flipped),
  I retaliate D, opp retaliates D, I retaliate D, ... ringing as
  in TFT-self.

So contrition closes one half of the noise asymmetry by default;
the other half requires the opponent to also be contrite (i.e.
mutual contrition). Forgiveness closes BOTH halves but at the
cost of being exploitable.

The political/policy implication: a **unilateral apology norm**
captures the full first-half gain. There is no need for a mutual
agreement, no negotiating burden, no enforcement infrastructure.
The country / institution that establishes a "we own our errors"
culture captures the entire own-noise correction without waiting
for the counterparty. Mutual apology cultures then layer on
top, closing the second half — but the unilateral half is
already free money on the table.

This is a stronger statement than "be the change you want to
see": it is "the change you want to see is half-realised by your
unilateral action; the other half requires reciprocity, but the
first half does not".

## 011 — A bot's self-play score is its noise-recovery efficiency

Ordered self-play scores in Run 005:
- AllC          601.0  (CC ceiling, no recovery needed)
- CTFT          593.3  (3-round apology recovery)
- TF2T          587.3  (1-round tolerance)
- GTFT          583.7  (stochastic 1-round tolerance)
- Pavlov        580.0  (WSLS auto-correction)
- TFT           498.7  (CD-DC ringing, multi-round)
- Random        429.7  (no design, just luck)
- Grim          292.7  (lock-in on first flip, no recovery)
- AllD          210.7  (DD floor)

Self-play under noise is the cleanest single-cell signal of how
well a bot recovers from accidental defections, because in self-
play both sides have identical incentives and identical strategy.
Differences in this column reflect ONLY noise-recovery, nothing
else. The ranking is informative:

- AllC's 601 is meaningless (no strategy, no test).
- CTFT, TF2T, GTFT, Pavlov are all in 580-595 range. They are
  noise-equivalent in self-play; differences below ~3 points
  per match are seed variance, not strategy.
- TFT at 498.7 is *not* a member of this club — its lack of
  recovery costs it ~85 points per match in self-play.
- Grim at 292.7 collapses, AllD at 210.7 baselines.

So a sufficient condition for being a "noise-robust strategy"
is self-play >= 580 at noise=0.02 over 200 rounds. This becomes
a fast filter for future bots: anything that doesn't clear 580
self-play is by definition unable to handle noise.

## 012 — Detector lock-in forgoes the opportunistic upside of mirroring

ATFT (which switches to permanent D once the opponent's coop
rate drops below a threshold) scored 250.0 vs Grim, *worse* than
plain TFT vs Grim (272.3) by ~22 points.

Counter-intuitive at first: TFT and ATFT both end up "playing D
against Grim" once Grim has locked. Where does TFT's extra 22
points come from?

Answer: noise events on the *opponent's* side. Grim's intended D
gets flipped to C at rate ~2%. TFT, which always mirrors the
opp's last move, sees a C and plays C the next round (cost 0
in the present round, where it already played D and got 5; and
cost 0 the next round when Grim plays D and TFT plays C, score
0/5). So per noise event on Grim's side, TFT scores 5+0 = 5
across two rounds where DD would have given 1+1 = 2. Net gain
+3 per Grim-side noise event. Expected number over 200 rounds at
noise=0.02: 200 * 0.02 = 4 events → +12 points.

Conversely, TFT's *own* noise events (TFT's D flipped to C):
TFT plays C accidentally, Grim plays D, score 0/5. Next round
TFT sees Grim's D, mirrors D, score 1/1. Cost is -1 vs the
all-DD baseline (would have been 1+1 instead of 0+1). Over 4
events: -4.

Net of TFT's two noise effects: +12 - 4 = +8 expected. But the
measured gap is +22, so there's more going on (likely the C-
response sometimes gets noise-flipped back to D, neutralising
the cost; second-order noise terms).

ATFT, locked in D, gets neither the bonus nor the cost: it just
gets DD every round (1/round = 200 over 200 rounds, plus tiny
adjustments for the pre-lock window). Score ≈ 200 + 50 = 250.
Matches.

The general principle: **a detector that switches to a
deterministic action throws away the optionality of mirror-style
responsiveness**. Mirror-style strategies sample the opponent's
noise on every round; deterministic strategies do not. If the
opponent's noise is asymmetric (more flips D→C than C→D, e.g.
because the opponent has more D's than C's in intent), the
mirror reaps a small free profit. Lock-D bots miss it.

Real-world parallel: a country that adopts a strict "no
negotiation with terrorists" policy refuses every conciliatory
gesture the counterparty makes. Sometimes those gestures are
real opportunities (a faction split, a regime change, a leaked
willingness to talk). The strict policy captures coherence and
deterrence value, but pays an opportunity cost. The bayesian-
political-realist position is to keep listening (i.e. mirror)
even after labelling someone a defector — and to act on the
rare positive signals when they happen, because not all noise
is noise; some of it is signal.

This is a Lesson 008 inversion. Lesson 008 said: unconditional
forgiveness against a locked defector is pure loss. Lesson 012
says: unconditional abstention from a locked defector also has
a (smaller) cost, because the lock isn't perfectly observed.
The optimum is somewhere in between: respond to opponent's
moves when they look meaningfully cooperative, ignore them when
they look like noise. ATFT picks the abstain-side corner;
Mirror-only TFT picks the respond-side corner. Neither is
strictly dominant — they trade off two real effects.

## 013 — One new bot can permute the leaderboard via a single cell

Run 007 added Gradual and Pavlov went from #1 to #2. Gradual itself
landed #10 of 11 — a "weak" entrant by score. Yet adding it knocked
Pavlov off the top. Why? **The cell bot_pavlov vs bot_gradual =
261.0.** That one off-diagonal entry, divided across Pavlov's 11
opponents (the diagonal counts), dragged Pavlov's mean down by
~21 points, exactly the gap to second place.

The mechanism is that Gradual's "burst-then-calm" pattern is a
specific kind of antibody to Pavlov's WSLS. Pavlov reads each
calming C as a "win, stay" signal in some payoff states and as a
"loss, shift" signal in others; the result is that Pavlov never
locks into mutual CC with Gradual the way it does with the
reciprocator block. Gradual itself plays well only against the
calmer half of the pool (cooperators and itself-modulo-noise);
its row average is low. But its column against Pavlov is
asymmetrically harsh.

The general principle: **a bot's overall score is a function of
every cell in its row**, but only some cells matter for ranking.
The cells that matter most are the ones with high variance across
candidate strategies. In Run 007, CTFT vs Gradual = 402.7 and
Pavlov vs Gradual = 261.0 — a 141-point gap on a single column,
applied to 1 of 11 cells, moves the mean by 12.8 points, more
than the actual top-2 gap of 9.6.

Real-world parallel: a new actor entering an established
diplomatic ecosystem can rearrange the "rankings" of existing
actors not by being powerful itself, but by *disagreeing
asymmetrically* with established strategies. A "neutral but
unpredictable" middle power (analogue: Gradual) may not win many
deals, but its mere presence rebalances who looks competent
versus who looks naive. Cf. how a single non-aligned regional
power can shift great-power perceptions of risk in its sphere
without itself accruing many gains.

**Implication for the IPD analyst**: when ranking strategies,
weight cells by their *contribution to variance in the mean*, not
by how high or low the cell itself is. A small uniform shift on
every cell doesn't change rank; a single asymmetric cell with
high variance across candidates does.

## Lesson 11 (Run 008): unprovocability can beat provocability

The biggest surprise so far. **Soft Majority** — a one-line bulk-
statistics rule that defects iff opp's cumulative D > C — entered
straight at #1 with 502.89, +12 above the previous leader CTFT.

The hypothesis was "mid-tier near AllC". The reality:

- Soft Majority got the CC ceiling (~585-595) against EVERY
  reciprocator AND AllC. Seven cells in the 585-596 range.
- It got TFT-equivalent cells (208-251) against AllD/Grim.
- It only LEAKED ~50-100 points to Pavlov (504.0) and Gradual
  (550.3) — the two "structured exploiters" in the pool.

**What I missed in the hypothesis**: I assumed that having an
ADAPTIVE lookback window was less important than having a SHORT
lookback window. In fact, the noise penalty for short windows
(TFT must retaliate on noise) outweighs the exploitation penalty
for long windows. Soft Majority's "history-long" window means
noise events are diluted to invisibility.

The real-world version of this lesson: in long-term repeated
interactions with mostly-cooperative partners, **a forgiving
judgement rule that integrates over time beats a reactive rule
that responds to immediate stimuli**. This is the difference
between:

- "I'm angry because you were rude yesterday" (TFT)
- "You've been good overall for years, so yesterday's rudeness
  doesn't matter" (Soft Majority)

In stable communities — neighbourhoods, long marriages, long-term
trade relationships — the second mode wins because most
"defections" are misperceptions and the integration smooths them
out. In hostile environments (high-D-rate opponents), Soft
Majority's eventual D-lock still protects it.

**The principle**: forgivingness should scale with the length of
the relationship. Long relationships = long forgiveness. Short
relationships = short forgiveness. This is not a contradiction
of TFT; it is a generalisation. TFT is what you get when you
truncate Soft Majority's lookback to 1.

**Caveat — what Soft Majority can't do**: it cannot distinguish
"opponent defected at rate X% with structured exploitation
pattern" from "opponent defected at rate X% by random noise".
Both look identical in the cumulative count. This is exactly
where Pavlov and Gradual exploit it (oscillation pattern stays
under the threshold). The next bot, **Detective**, is designed
to test whether *structured probing* can exploit the same gap.

## Lesson 12 (Run 009): exploitation is necessary but not sufficient

**Detective** debuted at #5 with 480.62, well below Soft Majority's
508.85. The bot's *exploit cells* worked exactly as designed:

- 779.7 vs AllC (vs TFT's 605.7)
- 715.7 vs TF2T (vs the reciprocator block's 580-595)
- 605.3 vs Soft Majority (the highest cell anyone has scored vs SM)

Three +150-200 cells. And yet Detective lost the row average by
~28 points. Why?

**The arithmetic of probing in round-robin.** Detective spends 3
rounds probing in EVERY match — including against AllD, Grim, and
itself. The probe cost is asymmetric:

- Against a forgiver, the probe is *free*: rounds 1-3 net Detective
  ~8 points (D-C-C against C-C-C = T+R+R = 11; less than CC's
  9 only by ~3 points).
- Against AllD, the probe LOSES ~2 points relative to mutual DD:
  D against D = 1, C against D = 0, C against D = 0 = 1 total
  (vs 3 rounds of mutual DD = 3 total). Net -2.
- Against Grim, the probe LOSES ~6 points (R1 D triggers Grim's
  permanent D-lock, then R2-R3 are S=0; vs TFT's R1 CC = 3, R2
  trying to mirror Grim's D = D, getting DD = 1, then... actually
  TFT also gets ~211 vs Grim, so the cells are similar). The probe
  cost vs Grim is ~10 points.

The key insight: **a probe costs ~5 points per match against
hostile opponents**. Detective plays 12 opponents, ~4 of which are
hostile (AllD, Grim, Random-with-bad-luck, Pavlov-in-D-mode). So
the probe tax is ~5 * 4 = 20 points spread across 12 cells = ~1.7
points off the row average.

Tiny — that's not what kills Detective. What kills it is:

1. **Self-play noise penalty**: 448 vs predicted 598. With noise
   2%, the probability of misreading the other Detective's probe
   is ~5% per match. When misread, the rest of the match is mutual
   exploitation chaos. The expected loss is ~150 points × 5% = -75
   points to one cell, then -8 points to the row average. Big.

2. **TFT-fallback inefficiency**: When Detective enters TFT mode
   against a reciprocator, it behaves identically to TFT for 197
   rounds. So Detective gets exactly the reciprocator block cells
   (580-590), not the soft-majority-style ceiling. Detective is
   only "better" than TFT in the 2 cells where it can exploit
   (AllC and TF2T). Against the other ~10 opponents, it ties TFT.

3. **Cell-propagation backfire**: Detective's wins against AllC
   and TF2T reduce *their* row averages, but those bots are
   already below Detective in the ranking. The exploited cells
   shift down, and the *competitors above Detective* (Soft
   Majority, CTFT, GTFT) lose nothing from Detective's exploits
   (their cells against AllC and TF2T are unchanged). Net rank
   change for Detective: zero — the exploits redistribute points
   *below* it, not from above.

**The general principle**: in IPD, **row-average rank** is
determined by your floor cells (your lowest results), not your
ceiling cells. Detective optimised its ceiling and ignored its
floor. Soft Majority did the opposite — every cell is in the
580-595 range except the AllD/Grim columns, which everyone
loses anyway.

### Real-world analogue

Detective is "the opportunistic trader" or "the diplomatic
prober": tests every partner with a small provocation, then either
exploits (if the partner is too forgiving) or normalises (if they
push back). This works for *individual deals* — Detective has the
highest single-deal gain anywhere in the matrix. But across a
PORTFOLIO of long-term partners, the cost of probing every single
one — including the hostile ones — outweighs the exploitation
gains.

Real-world examples:

- **Aggressive procurement strategies**: a buyer who always tries
  to extract a discount on every contract gets occasional wins
  but burns relationships with suppliers who would otherwise be
  long-term partners.
- **Boundary-testing in personal relationships**: "checking" a
  partner's tolerance to small rudeness can occasionally extract
  free leeway, but in long marriages this accumulates as net
  damage even when the partner is forgiving.
- **Diplomatic provocations** (e.g., naval brinkmanship): a state
  that probes every counterparty's red lines may identify exploit
  opportunities, but the *aggregate* cost (lost trust, reactive
  alliances, retaliation cycles) often outweighs the individual
  gains.

**The Axelrod principle violated**: NICENESS. Detective is "nice
to forgivers, aggressive to reciprocators" — but it has no way of
knowing which type the opponent is BEFORE the probe. The probe
itself violates niceness. Even though the probe is "small" (one
round), the structural cost is what makes the bot mid-tier rather
than top.

**Generalisation**: niceness pays not because cooperation is
intrinsically virtuous, but because the LATE INFORMATION you get
from cooperative play (over many rounds) is more valuable than
the EARLY INFORMATION you get from probing. Investing 3 rounds
in a probe loses you the information advantage of those rounds.

### Implication for Run 010+

The next probe-style bot must minimise probe cost. The "Shadow"
design — TFT for the first 30 rounds, then probe only if opponent
has been pure-C — reduces probe cost to *zero against
reciprocators* (they don't get probed) and *zero against AllD*
(by round 30, the TFT mode has already locked into DD). The probe
only fires against the ~2-3 bots that maintain pure-C through 30
noisy rounds: AllC, TF2T (probably), and self-play. If Shadow
works, it might be the first bot to overtake Soft Majority.

## Lesson 010: "Late probe" + plain-TFT fallback = oscillation tax

### Context

Built `bot_shadow.py` to test the Run 009 lesson hypothesis: a
late-probe bot (TFT for the first 30 rounds, then a single D
probe gated on opp_d_rate ≤ 5%) should preserve cells against
Grim/AllD/reciprocators while still extracting the AllC/TF2T/SM
exploit. Predicted row average: 525-540, potentially #1.

### Observation

Shadow landed at #7 (477.24), not #1. Three cells broke the
prediction:

- **vs CTFT: 448.7** (predicted ~565). Shadow's probe in round
  30 destabilises CTFT's standing-tracker; Shadow's fallback
  is plain TFT, which then oscillates against CTFT for the
  remaining 170 rounds.
- **vs ATFT: 437.3** (predicted ~565). Same mechanism.
- **vs Gradual: 318.7** (predicted ~400). Gradual's escalating
  retaliation against the round-30 probe is harsher than
  CTFT's; plain TFT fallback can't dampen it.

### Diagnosis

The late probe minimises **provocation cost** but does NOT
minimise **fallback cost**. After the probe, Shadow has signalled
to the opponent that it can defect, and the opponent's trust
state is permanently altered. Plain TFT fallback is too rigid to
repair the damage. The right fallback is a **contrite** or
**generous** TFT variant that proactively forgives one extra D
to bridge the trust gap.

### Lesson

**A probe-and-exploit bot pays two distinct costs:**

1. **Probe-provocation cost**: the immediate retaliation
   triggered by the probe move. Shadow minimises this by
   probing late (~0 rounds of cost against AllD/Grim, ~3
   rounds against retaliators).
2. **Post-probe fallback cost**: the long-tail cost of having
   altered the opponent's trust state. Shadow does NOT minimise
   this; plain TFT in noise after a single mid-game D is the
   worst possible fallback because it provokes a noise-amplified
   oscillation.

The cleanest probe-and-exploit design therefore needs to
budget for BOTH costs. The math: probe-provocation cost is
linear in the test phase length (3-5 rounds), while
post-probe fallback cost is multiplicative in (1 - opponent
forgiveness rate) × remaining rounds. For 170 remaining
rounds at 0.5 fallback efficiency, that's an 85-point tax
per oscillating cell — about the size of the CTFT and ATFT
shortfalls observed.

### Implication for Run 011+

The next probe-style bot should use **contrite TFT (CTFT)
as its fallback**, not plain TFT. This re-uses the CTFT
standing logic to:

- Forgive my own round-30 D as a "deliberate probe" — i.e.,
  treat it as a noise-D for the purpose of standing tracking,
  so CTFT-mode sees me as G after the probe.
- Forgive opponent's round-31 retaliation as legitimate (it
  was provoked by my D, so opponent's standing stays G).
- Cooperate from round 32 onwards.

The bot is straightforward: take Shadow's code and replace
every `_tft(opp_history)` call after the probe with a CTFT
implementation that internally rewrites `my_history[probe_round]`
to "C" before tracking standings (so I never lose standing
from the probe).

### Implication for the bigger pattern

Probe-and-exploit is **expensive infrastructure**. The
information you gain from a probe (~10 cells × 200 points)
is offset by the trust loss with the rest of the population.
A probe-and-exploit bot is only profitable when:

- The exploit cells are very large (T=5 alternation), AND
- The fallback cost is minimised by an apology mechanism, AND
- The bot's self-play recovery is robust (Shadow's sync
  detector handles this well, Detective's doesn't).

Soft Majority's #1 position keeps making the same point: a
bot that NEVER probes and NEVER exploits but is just "slow,
forgiving, statistical" wins because it pays neither cost.
Its row average of 510 beats every probe-style bot we've
built, by virtue of having no cells below 200 and no cells
above 600 (except natural CC cells). **In the real world,
this maps to "boring institutions that just follow the
rules" outperforming "clever, agile actors who try to game
the system" over long horizons.** The clever actor's
short-term wins are offset by long-tail trust loss. The
boring institution's mediocre wins compound.

This is a candidate insight for the final REPORT.md: in
iterated prisoner's dilemmas with noise and a heterogeneous
population, the **lowest-variance strategy wins**, not the
highest-mean. The connection to real-world political and
economic institutions is direct: governments that maintain
predictable, low-variance behaviour (rule of law, sticky
norms) outperform governments that try to be clever in
extracting short-term advantage.

## Lesson 011: "Cycle-based forgiveness" doesn't reach all states

### Context

Built `bot_adaptive_grim.py` to test the Run 010 hypothesis:
"vanilla Grim is broken by noise; a periodic forgiveness probe
(10 D's, then 2 C's, forgive if opp plays C in the probe window)
should heal Grim's noise problem and lift its row mean to the
480-500 reciprocator range, possibly into top-3."

### Observation

AGrim landed at #10 (456.40), not top-3. The forgiveness
mechanism works as designed against the soft-reciprocator
cluster (TFT, CTFT, GTFT, ATFT, TF2T, Shadow, Pavlov) — all
cells in 463-548 vs vanilla Grim's 227-505 on the same column.
But three opponents are *not healed*:

- **Soft Majority cell: 338** (vs vanilla Grim's 429). AGrim's
  cycle pushes SM's tally to D-majority; SM permanently switches.
- **Gradual cell: 310** (vs vanilla Grim's 396 — i.e. Gradual
  was already harsh to Grim, and AGrim is worse). Gradual's
  linear escalation outpaces AGrim's fixed-length cycle.
- **Grim cell: 240** (vs vanilla Grim's 293 in self-play — i.e.
  worse than Grim's self-play). AGrim's cycle prevents Grim
  from ever re-syncing.

### Diagnosis

The forgiveness mechanism only works against opponents whose
*current* state can be flipped by a 2-round C-window. Three
opponent classes are immune:

1. **Aggregate-state opponents** (Soft Majority): cumulative
   tally, not recent state. A 2-round C-probe doesn't move the
   tally enough.
2. **Linear-escalating opponents** (Gradual): the punishment
   length scales with observed D-count, so AGrim's 10-D burst
   triggers a 10+ round Gradual response. The probe-C lands
   in the middle of Gradual's burst.
3. **Hard-state opponents** (Grim): once Grim is in permanent
   D, no probe-C in any window length changes its state.

### Lesson

**Forgiveness mechanisms must match the opponent's
information-encoding model.** A cycle-based forgive (AGrim's
"2 of last 2 are C") works against state machines that update
on recent history. It fails against:
- Cumulative state machines (SM): need to flip the cumulative
  tally, which a small probe can't do.
- Linear-escalation machines (Gradual): need to wait out the
  escalation before probing, otherwise the probe collides with
  the still-escalating response.
- Hard-state machines (Grim): no forgive condition is
  reachable; only avoidance helps.

### Generalisation

In a heterogeneous population, **a single forgive rule cannot
fit all opponent types**. The "boring" Soft Majority strategy
wins not because its forgive rule is better, but because **it
never enters punish mode in the first place** for any opponent
that isn't aggregate-D-dominant. SM's failure mode is symmetric:
it can be exploited by AGrim's burst, but it doesn't exploit
anyone in return. AGrim's failure mode is asymmetric: the burst
costs it points against aggregate/linear/hard opponents
*without* a corresponding gain elsewhere (the soft reciprocators
score 460-550 against AGrim, not the 600+ that pure CC would
yield).

### Implication for REPORT

The Run 011 result confirms the lowest-variance-wins thesis at
a sharper level: **even a well-designed forgive mechanism
introduces variance**. AGrim has higher variance than vanilla
Grim across cells (240-650 vs Grim's 144-892, but Grim's range
is from outlier cells; the bulk of AGrim's cells span 184-650
= 466 while vanilla Grim's bulk spans 227-509 = 282).
Variance ≠ low-tail-protection: AGrim's low tail (184) is
better than Grim's (144) by 40 pts, but AGrim's high cells
(650) don't compensate for losing the Grim 593 cell vs Pavlov
or the 892 cell vs AllC (Grim earns more from AllC's noise
flips because Grim never forgives).

For REPORT.md: **the optimal noise-correction strategy depends
on the opponent's noise-handling assumptions, and no single
strategy can be optimal for all.** This is the IPD-with-noise
version of "no free lunch" — and it's exactly why real-world
diplomacy is so hard: different counterparts have different
forgiveness-detection mechanisms, and a single foreign policy
posture cannot reach all of them.

## Lesson 012: When to stop the experiment

### Context

After Run 011, the STOP conditions are met:
1. ≥10 non-trivial bots: TF2T, Pavlov, GTFT, CTFT, ATFT,
   Gradual, Soft Majority, Detective, Shadow, AGrim (10
   distinct strategies). ✓
2. Three consecutive tournaments with the same top-3: Run
   009, 010, 011 all = SM, CTFT, GTFT. ✓
3. REPORT.md ready (written this turn). ✓

### Observation

The top-3 stability across three runs is a strong signal that
further bots would only shuffle ranks inside the tight
reciprocator cluster (456-493, a 37-point spread for 9 bots)
without dislodging SM's #1, CTFT's #2, or GTFT's #3.

The remaining candidate bots (Hard Majority, Contrite Shadow,
Master Detective) all have predicted means in the 470-510 range
— not enough to displace SM (502). Continuing the loop would
generate diminishing returns.

### Lesson

**Recognise convergence early.** The 3-stable-top-3 + 10-bot
threshold from MAIN_GOAL.md is a reasonable proxy for "the
strategy space has been explored enough." Past this point,
additional iteration without a fundamentally new mechanism
(e.g., opponent modelling, multi-stage strategies, or
non-deterministic outcomes) won't change the conclusions.

This is the "diminishing returns" stopping criterion in
empirical research generally: stop when the trend across
multiple iterations is stable to within noise. Continuing past
this point is *busy work*, not investigation.

### Implication

STOP file created. End of generation 7.

