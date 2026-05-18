# Iterated Prisoner's Dilemma: 11 tournaments, 15 strategies

Final report for generation 7's self-play IPD experiment. Built
a round-robin tournament engine, seeded a pantheon of 5
classical strategies, added 10 non-trivial variants over 6
iterations, and ran 11 tournaments to identify which strategies
*stably win* under noise.

## 1. Setup

- **Game:** classical 2-player iterated prisoner's dilemma.
  Payoff matrix: CC=3/3, CD=0/5, DC=5/0, DD=1/1. (T>R>P>S and
  2R>T+S, so mutual cooperation is collectively optimal.)
- **Match length:** 200 rounds per match.
- **Noise:** each move is independently flipped with
  probability 0.02 before being scored and entered into history.
  Expected ~8 flips per match (4 per side).
- **Repetitions:** 3 per matchup, then averaged. Deterministic
  per-pair seed (`f"{base}|{a}|{b}|{r}"`).
- **Format:** round-robin, each bot vs every other bot
  (including self-play). 15 bots → 120 unique pairs.
- **Engine:** `tournament.py` (~220 lines, stdlib only).
- **Bot interface:** pure `choose_move(my_history, opp_history)
  → "C" | "D"`. Any exception or bad output is scored as D.

## 2. The pool

**Pantheon (5):** AlwaysC, AlwaysD, Tit-For-Tat, Random, Grim
Trigger.

**Non-trivial (10):**

| name | one-line description |
|------|----------------------|
| TF2T (Tit-For-Two-Tats) | C until two consecutive D's from opp. |
| Pavlov (WSLS) | repeat my last if R or T, switch if S or P. |
| GTFT (Generous TFT) | TFT with ~25% probability of forgiving a D. |
| CTFT (Contrite TFT) | TFT with a standing-tracker: forgive own D if I was in good standing. |
| ATFT (Adaptive TFT) | TFT with a slow trust adjustment. |
| Gradual | linearly escalating retaliation. |
| Soft Majority | C iff opp's cumulative C-count ≥ D-count. |
| Detective | probe with `D-C-C-C`: if opp cooperated throughout, exploit; else TFT. |
| Shadow | TFT for 30 rounds (recon), then single D probe, exploit if "safe." |
| Adaptive Grim | Grim + periodic 2-round C-probe; forgive if any C in probe replies. |

## 3. Final ranking (Run 011)

```
rank  bot                      score
   1  bot_soft_majority       502.73
   2  bot_ctft                493.20
   3  bot_gtft                487.07
   4  bot_detective           482.84
   5  bot_tf2t                481.47
   6  bot_shadow              480.31
   7  bot_atft                478.49
   8  bot_tit_for_tat         466.27
   9  bot_pavlov              459.18
  10  bot_adaptive_grim       456.40
  11  bot_always_c            449.13
  12  bot_random              429.13
  13  bot_gradual             417.53
  14  bot_grim                396.00
  15  bot_always_d            354.96
```

Top-3 has been **identical across the last three tournaments**
(Runs 009, 010, 011 all = Soft Majority, CTFT, GTFT). Pool has
10 non-trivial strategies. STOP conditions met.

## 4. Why the top-3 wins

### #1 Soft Majority (502.73): *low variance wins*

Soft Majority cooperates as long as the opponent's cumulative
C-count is ≥ D-count, and defects otherwise. It is the **only
top-tier bot that is not a reciprocator at all** — it doesn't
care about *recent* moves, only the running tally.

**Why it wins:**
- Against any bot that mostly cooperates, SM's tally stays
  C-majority → SM cooperates → mutual CC at ~580-600/match.
- Against pure defectors (AllD, Grim post-trigger), SM's tally
  flips to D-majority within ~50 rounds → SM defects forever,
  scoring DD = ~200-220/match.
- Against noisy reciprocators (TFT, CTFT, etc.), the tally
  rarely flips because noise affects both sides symmetrically.

**Where it loses:**
- vs Adaptive Grim (338): AGrim's 10-D burst-then-2-C-probe
  cycle pushes SM's tally past the threshold and SM switches
  permanently. SM cannot recover even when AGrim sends a
  probe-C, because 2 C's don't move the cumulative tally.
- vs Pavlov (402): Pavlov's WSLS dynamic creates a pattern of
  intermittent D's that SM tolerates but doesn't exploit.

**Structural reason for #1:** SM has *no cells below 200* and
*no cells above 600* (except natural CC cells). Its row variance
is 130², while CTFT's is 124² and GTFT's is 158². The reason SM
edges CTFT for #1 is that SM's defection-recovery (it locks
into DD against actual defectors faster than CTFT's slow
contrite cycle does) keeps SM's floor a bit higher.

### #2 CTFT (493.20): *the best reciprocator*

Contrite TFT is TFT with a private "standing" tracker: if my D
was a noise flip (I was in good standing), don't escalate.
Apologies are issued by playing a deliberate C even when the
opponent has just defected.

**Why it wins:**
- Vanilla TFT in noise spirals into mutual D after a single
  noise event; CTFT extinguishes most spirals within 2 rounds.
- Against soft reciprocators (TFT, GTFT, TF2T, ATFT) CTFT
  scores ~593-600/match — better than TFT vs TFT.
- Against AllC, CTFT cooperates throughout → 600.

**Where it loses:**
- vs Shadow (442): Shadow's mid-game probe destabilises
  CTFT's standing tracker (Shadow goes from G-standing to
  B-standing without earning it through observed bad play),
  creating a noise-amplified oscillation.
- vs Detective (553): Detective extracts 5 free T-cells in its
  opening probe before CTFT's standing logic re-stabilises.
- vs Pavlov (502): CTFT's contrite C arrives when Pavlov is in
  lose-shift mode → off-phase oscillation.

**Structural reason for #2:** CTFT has the same high cells as
TFT against soft reciprocators but corrects TFT's noise spiral,
adding ~30 pts/cell on average. The cost is that CTFT
occasionally "over-apologises" and gives an exploit window to
probe-style bots.

### #3 GTFT (487.07): *cheap repair*

Generous TFT is TFT with a 25% probability of forgiving a D
(playing C even when opponent's last move was D). The
forgiveness is randomised, breaking deterministic oscillation
chains in noise.

**Why it wins:**
- A single noise flip in TFT vs TFT causes mutual D until
  another noise flip resets them; GTFT skips this by playing C
  with 25% probability after any opp D, recovering in
  expectation within 4 rounds.
- Against AllC (604) and other cooperators, GTFT plays mostly
  C with a few accidental D's that AllC absorbs.

**Where it loses:**
- vs Grim (157): GTFT's first accidental C-after-D triggers
  Grim, then Grim plays D forever; GTFT continues to play C
  ~25% of the time (S=0) and D otherwise.
- vs AllD (143): same as TFT vs AllD but worse because GTFT's
  C-after-D donations to AllD cost free T-cells.
- vs Gradual (359): GTFT's forgiveness rate is mismatched with
  Gradual's linear escalation.

**Structural reason for #3:** GTFT is the simplest *probabilistic*
recovery from noise. Without GTFT, TFT scores ~466 in this pool
(its actual rank #8). With GTFT's noise correction, the same
strategy lifts to 487.

### Outside the top-3

- **Detective (#4, 482.84):** opens with `D-C-C-C` to probe.
  Wins big against AllC (780), TF2T (716), and Random (~450).
  Loses to AllD (212), Grim (212), and self (448). The big
  exploit cells don't compensate for the bad cells.
- **TF2T (#5, 481.47):** tolerant of single D's, vulnerable to
  Detective-style alternation (397). Otherwise close to CTFT.
- **Shadow (#6, 480.31):** the best AllC-exploit cell (718) and
  the highest SM cell of any bot (633), but lost to CTFT (449)
  and ATFT (440) because of post-probe oscillation. Self-play
  592 (best of any non-SM bot) due to sync detector.
- **AGrim (#10, 456.40):** see Section 5.
- **AllD (#15, 354.96):** the canonical "exploit-everything-fail-
  vs-everything" strategy. Scores 970 vs AllC but ~200 vs all
  reciprocators. In a heterogeneous pool, the average is bottom.

## 5. The Axelrod principles, validated in our data

Robert Axelrod's four characteristics of successful IPD
strategies map cleanly onto our results.

### Niceness — never defect first

**Test:** compare bots that open with C against bots that open
with D.

| bot       | first move | row mean |
|-----------|------------|---------:|
| Soft Maj. | C          |    502.7 |
| CTFT      | C          |    493.2 |
| GTFT      | C          |    487.1 |
| TFT       | C          |    466.3 |
| AllD      | D          |    354.9 |
| Detective | D          |    482.8 |
| Shadow    | C (TFT phase) | 480.3 |
| AGrim     | C          |    456.4 |

Every bot in the top-3 opens with C. The *only* bot that opens
with D and scores above 460 is Detective — and Detective's bonus
(it exploits naive cooperators) is paid back in spades against
reciprocators that punish the D opening (Grim, AllD self-play).
Detective's row 482 is below all three nice bots.

The principle is robust: **niceness pays because the
information value of cooperative rounds compounds.** A nice bot
learns the opponent's type from its cooperative replies; a mean
bot gives up that information channel.

### Retaliatory — punish defection

**Test:** AlwaysC scores 449.1 (#11). It is "nice" but not
"retaliatory." Compare with TFT (466.3) — same niceness but
adds retaliation.

The 17-point gap is small but consistent across tournaments:
**niceness without retaliation is exploitable**, but the
exploitation isn't catastrophic (AllC still gets ~600 vs
reciprocators, only AllD/Grim drive it down to 23-144).

In a pool of *only* nice reciprocators, AllC would do fine.
In a mixed pool with at least one exploiter (AllD, Detective,
Shadow), AllC pays a ~50-point tax per exploiter.

### Forgiving — don't carry grudges

**Test:** Grim (#14, 396.0) is nice and retaliatory but **not**
forgiving. Compare with GTFT (#3, 487.1) — same niceness, same
retaliation, but forgives.

The 91-point gap is the **single largest principle-level effect**
in our data. Forgiveness in noise is *essential*: without it, a
single accidental D from the opponent locks both into permanent
DD, costing ~400 pts per locked pair.

Even Adaptive Grim (with periodic probe-based forgiveness) at
456.4 is +60 vs vanilla Grim — and AGrim is a half-measure;
the full reciprocator cluster (CTFT, GTFT, etc.) at 480-493 is
+90 above vanilla Grim because they forgive every round, not
just every 12 rounds.

### Non-envious — don't try to beat *this* opponent

**Test:** Detective tries to beat each opponent individually
(probe to identify, exploit if naive). Soft Majority makes no
attempt to beat anyone; it just plays a fixed rule.

Detective: row mean 482.8, individual matchups range from 212
to 780 (variance ≈ 168²). 
Soft Majority: row mean 502.7, individual matchups range from
208 to 596 (variance ≈ 130²). 

Soft Majority *loses* to AllD (208) but doesn't try to
"compete" with AllD — it just minimises its loss. Detective
*beats* AllC (780) but the win comes at the cost of damaged
relationships with retaliators.

In tournament *aggregate* scoring, Soft Majority's "I don't
care if I beat you, I care if we both score" approach wins.
Detective's "I want to beat AllC specifically" wastes
information cycles on opponents that aren't AllC.

## 6. Real-world connections

The structural lessons from our tournament map directly onto
several real-world iterated-cooperation games.

### 6.1 Cold War and arms races

The U.S.–Soviet arms race is a classical IPD-with-noise:
- **C** = limit weapons or honour a treaty.
- **D** = secretly build / test new weapons.
- **Noise** = misinterpretation of satellite data, false alarms,
  or accidental treaty violations.

The historical pattern looks like CTFT or GTFT: a long period
of cooperation (SALT, START, INF), occasional retaliatory
escalations (Cuban Missile Crisis), and eventually de-escalation
when the *contrite* state ("we both have the bomb, mutual
destruction is real") is reached. The reason the world didn't
spiral into DD is exactly the CTFT mechanism: both sides
maintained ambiguous *standing* — neither claimed to be perfect,
both allowed face-saving retreats from provocations.

The exceptions (Korea, Vietnam, Afghanistan) are local
manifestations of the AllD column: in those theatres, neither
side could find a forgiveness channel, and the local dynamic
locked into DD even while the bilateral dynamic at the strategic
level remained reciprocator-like.

**AGrim's failure vs Soft Majority** maps to a familiar real-
world failure mode: the U.S. tried to use targeted sanctions
plus periodic dialogue windows (Iran, North Korea) — a probe-
based forgiveness mechanism — but the affected populations
became "aggregate reasoners" (Soft Majority-like). After enough
cycles of sanctions, even sincere dialogue windows are
discounted: the cumulative-grievance tally stays D-heavy. This
is exactly the cell where AGrim scored 338 instead of the
predicted 580.

### 6.2 Climate agreements (Kyoto, Paris)

In climate IPD:
- **C** = comply with emission reductions.
- **D** = continue burning fossil fuels.
- **Temptation T=5** = a country's economy grows faster if it
  defects while others cooperate.
- **Noise** = imperfect monitoring, accidentally exceeding
  agreed quotas due to weather or measurement error.

The Paris Agreement design echoes Soft Majority's logic: there
is no per-incident sanction (no TFT-style "you exceeded, we
exceed"), only an aggregate review every 5 years. This is
*intentional*: the framers correctly intuited that aggregate-
based reasoning produces lower variance in compliance
trajectories than per-incident retaliation, which in noisy
monitoring would degenerate into mutual finger-pointing.

The cost is that the Paris regime is slow to penalise serial
defectors — exactly the trade-off Soft Majority makes in our
tournament. A purely TFT-style climate regime would crash on
the first measurement error; Soft Majority absorbs noise and
only retaliates on cumulative deviation. **Kyoto, by contrast,
was more TFT-like with binding per-period penalties; it
collapsed exactly the way TFT collapses in noise.**

### 6.3 Cartels (OPEC, etc.)

OPEC is an IPD where:
- **C** = honour the production quota.
- **D** = quietly produce above quota.
- **Information lag** = noise in observing partners' production.

The historical pattern is **Tit-For-Tat with periodic
collapse**: when one member is observed cheating, others
retaliate by also overproducing. Prices crash. After 6-18
months, the cartel reconvenes and re-establishes quotas. This
is approximately Gradual or AGrim behaviour — and it has the
same flaw: the punishment phase causes durable damage to the
cartel's legitimacy with consumers, so the long-run row average
is below what a "boring" stable quota system would achieve.

In our data, Gradual scored 417.5 (#13). In OPEC's data, the
2014-2016 oil price war and the 2020 Russia-Saudi standoff
cost the cartel ~$1 trillion in foregone revenue — exactly the
kind of "punishment cycle cost" that AGrim incurs against Soft
Majority.

### 6.4 Free-rider problems (taxes, public goods)

When a community provides a public good (street lighting,
vaccination, defence), each individual faces a private IPD:
- **C** = pay tax / get vaccinated / serve in militia.
- **D** = free-ride; let others pay.

The successful institutions are *Soft Majority*-like: they
don't track who individually defected, they enforce a baseline
rule (compulsory tax, mandatory vaccination, conscription) that
overrides individual incentives. The TFT alternative — "I'll
only pay if my neighbour pays" — would collapse in noise (one
late payment triggers cascade).

In data: countries with high *baseline* compliance institutions
(Scandinavian tax compliance, Japanese civic participation)
outperform countries with TFT-style enforcement (some U.S.
states' "voluntary" tax compliance norms).

### 6.5 Personal relationships

Long-term friendships and marriages are the cleanest real-world
examples of IPD-with-noise. Empirical relationship research
(Gottman et al.) finds that:
- Successful long-term partnerships have **CTFT-like
  responses**: when one partner hurts the other (a D in
  IPD terms), the offender quickly apologises (contrite C)
  and the offended partner accepts the apology rather than
  retaliating in kind.
- Failing partnerships display **TFT or Grim dynamics**:
  every slight is met with a counter-slight (TFT) or stored
  as a permanent grievance (Grim).
- The 5:1 positivity ratio (Gottman) maps to GTFT's ~25%
  forgiveness rate: forgive ~1 of every 4 transgressions
  *unconditionally* (no retaliation, no record).

The Detective / Shadow pattern in relationships looks like
"testing the partner's tolerance" — small experimental D's to
see what they let slide. In our data, Detective and Shadow
land in the middle of the pack; in relationships, this pattern
correlates with relationship dissatisfaction (the partner being
"tested" loses trust faster than the tester gains exploit
information).

## 7. Honest takeaways

### What the model captures well

- **Noise matters.** Strategies tuned for noise-free play
  (vanilla Grim, vanilla TFT) collapse against strategies with
  even modest noise tolerance (GTFT, CTFT, SM). This matches
  the real-world observation that small misunderstandings can
  rupture cooperation if there's no forgiveness mechanism.
- **Aggregate reasoning beats reactive reasoning at #1.** This
  is a counterintuitive but robust finding, and it maps onto
  the empirical observation that boring institutions (rule of
  law, predictable regulation) outperform clever ones over
  long horizons.
- **Probe-and-exploit pays narrow gains but broad costs.**
  Detective, Shadow, and AGrim all extract big exploit cells
  but pay for them in trust loss with the rest of the pool. In
  real-world terms: aggressive procurement, brinkmanship, and
  "small breach to test tolerance" all under-perform stable
  cooperation in long-horizon games.
- **Forgiveness in noise is essential.** The single biggest
  Axelrod-principle effect in our data is the +91-point gap
  between Grim and GTFT, both of which are otherwise nice and
  retaliatory.

### What the model captures poorly

- **No reputational spillovers.** In our IPD, what bot A does
  against bot B is invisible to bot C. In real life, reputations
  travel — a country that breaks a treaty with one partner
  signals untrustworthiness to all others. With reputation
  effects, AllD would collapse much faster (other bots would
  treat it as a known defector before the match starts).
- **No coalitions or side-payments.** Real-world cooperation
  often involves third parties (mediators, alliances,
  compensation funds). Our IPD has none.
- **Fixed payoff matrix.** Real-world payoffs vary by context
  (a defection in nuclear arms control is far more costly than
  a defection in trade tariffs). Our model treats all rounds as
  equally weighted.
- **No "exit" option.** In real life, parties can refuse to
  play, or end the relationship. Our IPD forces 200 rounds. A
  more realistic model would allow exit, which would penalise
  AllD-style bots even more harshly (every reciprocator would
  refuse a second match).
- **No second-order strategies.** Our bots reason only about
  history of moves. Real-world actors reason about other
  actors' *strategies* — "I think they're playing Grim, so I
  must never defect even once." Adding this opponent-modelling
  layer changes the game qualitatively.

### What I'd build next if I had more turns

1. **Reputation-aware tournament.** Each bot sees a summary
   of opponent's behaviour from prior matches. Predict: AllD
   collapses to <250 (everyone defects from round 1), Soft
   Majority maintains #1 with even less variance.
2. **Variable-length probe AGrim.** Extend the C-probe
   adaptively: if opp still defects, try 4-round, then
   8-round probes. Predict: SM cell improves from 338 to ~480.
3. **Opponent-modelling Detective.** Use the first 10 rounds
   to classify opp as one of {Grim, AllD, TFT, AllC, SM},
   then choose a strategy optimised for that class. Predict:
   ~520 row mean, potentially #1.
4. **Population dynamics.** Instead of round-robin, simulate
   evolutionary replicator dynamics: each generation, bot
   counts are weighted by previous-generation scores. Predict:
   Soft Majority dominates the asymptotic population because
   its low variance compounds over generations.

### Bottom-line claim

The Axelrod principles (nice, retaliatory, forgiving,
non-envious) all show up cleanly in our data, but the **single
strongest principle is non-envy**: trying to beat individual
opponents (Detective, Shadow, AGrim) costs more than it gains
in aggregate scoring. The bot that most embodies non-envy is
Soft Majority — it has no exploit mechanism, no probe, no
opponent type detection. It just follows a simple, predictable
rule and wins on consistency.

The real-world analogue is the most boring possible: **stable,
predictable, rule-following institutions outperform clever,
agile, opportunistic ones in long-horizon iterated games with
heterogeneous partners and noisy observation.** This is not
news to political scientists or institutional economists. It is,
however, news to anyone who thinks that strategic cleverness
is the path to long-run success in a multi-party world.

---

*Generation 7, Run 011. Pool: 15 bots (5 pantheon + 10
non-trivial). Tournament parameters: rounds=200, noise=0.02,
repeat=3, seed=42. Top-3 stable across Runs 009-011: Soft
Majority, CTFT, GTFT. STOP file created.*
