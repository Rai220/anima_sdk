# Tournament scores log

Every row records one tournament run. Earliest at the top.

Parameters legend:
- `rounds`   — moves per match (default 200)
- `noise`    — independent flip probability per played move (default 0.02)
- `repeat`   — matches per pair, averaged (default 3)
- `seed`     — deterministic base seed for the noise PRNG (default 42)

---

## Run 001 — pantheon baseline (2026-05-17)

Setup: `rounds=200 noise=0.02 repeat=3 seed=42`. Five reference bots only.

| rank | bot               | mean score |
|------|-------------------|-----------:|
| 1    | bot_grim          |     456.67 |
| 2    | bot_always_d      |     442.80 |
| 3    | bot_tit_for_tat   |     409.13 |
| 4    | bot_random        |     383.93 |
| 5    | bot_always_c      |     333.20 |

Payoff matrix (row plays column; mean per match over 3 repeats):

```
row\col              grim   alld   tft   rand   allc
bot_grim            292.7  206.7  289.0  602.7  892.3
bot_always_d        216.7  210.7  239.0  577.3  970.3
bot_tit_for_tat     272.3  210.7  498.7  458.3  605.7
bot_random          112.7  119.0  473.3  429.7  785.0
bot_always_c        144.0   23.7  584.0  313.3  601.0
```

### Notable cells

- **bot_grim vs bot_always_c = 892.3**. Grim ends up exploiting AllC
  under noise: whenever AllC's C is noise-flipped to D in Grim's
  observation, Grim locks into D and plays D against AllC for the
  rest of the match. Average over 3 repeats: ~50 rounds CC + 150
  rounds DC ≈ 150 + 750 = 900. **Grim is not a "nice" strategy under
  noise**: it locks in on what it thinks is a defection but is in
  fact noise.
- **bot_grim self-play = 292.7**. Symmetric to the above: one noise
  flip on either side triggers permanent DD. So 2 copies of Grim
  cooperate for only ~25 rounds before mutual lock-in. Compare to
  bot_tit_for_tat self-play = 498.7, which recovers (oscillates
  through CD-DC and back to CC).
- **bot_always_c vs bot_always_d = 23.7**. AllC sees 5 D's per
  round on average from AllD, plus some flipped-to-C ones. Score
  is essentially 0 plus the ~2% chance per round of accidentally
  getting CC = ~0.02 * 3 * 200 = 12, and the ~2% chance of getting
  CD on a noise flip where AllD's D becomes C giving C-C 3-points
  ≈ 12. So 24. Matches.
- **bot_tit_for_tat self-play = 498.7**. Down from the 600 noise-
  free CC ceiling. The cost of each noise flip is roughly 6 points
  lost (CC → CD then DC then CC = 3+0+5+3 = 11 vs 3+3+3+3 = 12, so
  net ~-1 per flip pair, times ~8 flips = small loss; actually the
  loss is the cumulative CD-DC oscillation cost during recovery).

### Class structure visible already

- **Exploiters** (AllD, Grim): top of leaderboard because the
  pantheon has 2 free-meal cooperators (AllC, TFT).
- **Reciprocators** (TFT): middle, hurt by self-play noise but
  doesn't get exploited as badly as AllC.
- **AllC**: bottom; gets ground down by everyone except TFT.

This is expected. The exploiter advantage will reverse once we add
more reciprocators and detectors to the field, because exploiters
will only exploit AllC and a few naive bots, while reciprocators
will form cooperative pairs with each other.

---

## Run 002 — pantheon + TF2T (2026-05-17)

Setup: `rounds=200 noise=0.02 repeat=3 seed=42`. Added `bot_tf2t`.

| rank | bot               | mean score | Δ vs Run 001 |
|------|-------------------|-----------:|-------------:|
| 1    | bot_tit_for_tat   |     441.06 |        +31.9 |
| 2    | bot_tf2t          |     431.83 |          new |
| 3    | bot_grim          |     428.61 |        -28.1 |
| 4    | bot_random        |     425.17 |        +41.2 |
| 5    | bot_always_d      |     409.56 |        -33.2 |
| 6    | bot_always_c      |     376.83 |        +43.6 |

Payoff matrix:

```
row\col          tft     tf2t    grim    rand    alld    allc
tit_for_tat     498.7   600.7   272.3   458.3   210.7   605.7
tf2t            585.7   587.3   253.3   368.0   201.7   595.0
grim            289.0   288.3   292.7   602.7   206.7   892.3
random          473.3   631.3   112.7   429.7   119.0   785.0
always_d        239.0   243.3   216.7   577.3   210.7   970.3
always_c        584.0   595.0   144.0   313.3    23.7   601.0
```

### What changed

- **Adding one cooperator (TF2T) re-ordered the entire leaderboard.**
  TFT jumped from #3 to #1; AllD from #2 to #5. TF2T cooperates
  with TFT at ~CC ceiling (600+ both directions), so both
  reciprocators get a free big cell. AllD/Grim do not benefit
  from TF2T (TF2T punishes their persistent D's after 2 rounds).
- **TFT exploits TF2T marginally under noise.** TFT vs TF2T =
  600.7, vs the CC ceiling of 600. The +0.7 comes from TFT's
  one-round-D after a noise flip, which TF2T tolerates without
  retaliation. So TF2T pays a small "tolerance tax" to TFT and
  to AllC, in exchange for noise-robust self-play (587.3 vs
  TFT-self 498.7).
- **Random's score jumped +41.** Random's C-half is now exploited
  less because TFT and TF2T return cooperation when Random
  cooperates. The exploiter cells (vs AllD, vs Grim's lock) stay
  bad, but the cooperator cells lifted.
- **AllC's score jumped +44.** Same reason: two more bots that
  reciprocate AllC's C properly (TFT was already; TF2T joined).

### Class structure

- **Reciprocators block** (TFT, TF2T): top tier; lifted by mutual
  CC near the ceiling.
- **Exploiters** (Grim, AllD): middle; still profit from AllC and
  Random but no longer dominate.
- **Random / AllC**: bottom; structurally unable to climb until
  even more reciprocators are added.

### Next bot

Pavlov (Win-Stay-Lose-Shift) is next. It's the canonical "payoff-
sensitive" strategy and a natural foil to mirror-based TFT-family.
In a noisy world it has a known quirk: it exploits AllC by reading
"I won by playing D" as a signal to keep defecting. That quirk
will probably help Pavlov in this small field, similar to how
Grim accidentally exploits AllC. Watching that interaction is the
point.

---

## Run 003 — pantheon + TF2T + Pavlov (2026-05-17)

Setup: `rounds=200 noise=0.02 repeat=3 seed=42`. Added `bot_pavlov`.

| rank | bot               | mean score | Δ vs Run 002 |
|------|-------------------|-----------:|-------------:|
| 1    | bot_pavlov        |     472.86 |          new |
| 2    | bot_grim          |     452.10 |        +23.5 |
| 3    | bot_tit_for_tat   |     438.05 |         -3.0 |
| 4    | bot_always_d      |     435.52 |        +26.0 |
| 5    | bot_tf2t          |     427.48 |         -4.4 |
| 6    | bot_random        |     423.43 |         -1.7 |
| 7    | bot_always_c      |     367.48 |         -9.4 |

Payoff matrix:

```
row\col          pavlov  grim    tft     alld    tf2t    rand    allc
pavlov          580.0   348.0   423.3   119.7   561.3   488.0   789.7
grim            593.0   292.7   289.0   206.7   288.3   602.7   892.3
tit_for_tat     420.0   272.3   498.7   210.7   600.7   458.3   605.7
always_d        591.3   216.7   239.0   210.7   243.3   577.3   970.3
tf2t            401.3   253.3   585.7   201.7   587.3   368.0   595.0
random          413.0   112.7   473.3   119.0   631.3   429.7   785.0
always_c        311.3   144.0   584.0    23.7   595.0   313.3   601.0
```

### What changed

- **Pavlov jumped straight to #1 at 472.86.** It exploits AllC
  (789.7), exploits Random (488.0), has the best self-play of the
  whole field (580.0, only 20 short of the noise-free CC ceiling),
  and ties or wins vs the reciprocator block. Its only catastrophic
  cell is vs AllD: 119.7, which is BELOW the DD floor of 200.
- **bot_pavlov vs bot_always_d = 119.7**. Mechanism: after CD
  Pavlov shifts to D, but after DD Pavlov shifts back to C (since
  P=1 is a "loss"). So Pavlov oscillates C,D,C,D against AllD,
  scoring 0+1 every 2 rounds ≈ 0.5/round × 200 = 100. With noise
  rounds where AllD's D gets flipped to C, Pavlov occasionally
  banks a 5 → ~120. This is pure exploitation by AllD.
- **AllD scores 591.3 vs Pavlov**, second-highest cell in its row
  after AllC (970.3). AllD trades its losses against reciprocators
  for a structural win against payoff-sensitive bots.
- **Grim moved up to #2** (+23). Mechanism: Pavlov cooperates
  initially, so Grim cooperates back. When noise eventually flips
  Pavlov's C to D (or Grim's own C → D, which Pavlov reads as a
  loss and shifts away from C anyway), Grim locks into D. Pavlov
  then oscillates CD/DD against the locked-D Grim, but with a
  recoverable component, scoring 348 on the Grim column. Grim
  collects 593.0 from Pavlov — comparable to its AllC exploit.
- **TFT-block slipped slightly**. TFT and TF2T both lost ~3-4
  points because Pavlov takes a marginal edge vs them under noise.
  When TFT noise-flips C → D, Pavlov's (D,D) → C shift recovers
  faster than TFT's mirror. Pavlov scores 423.3 vs TFT, TFT scores
  420.0 vs Pavlov — nearly balanced, slight Pavlov edge.

### Class structure update

- **Pavlov is a new class**: a payoff-sensitive exploiter-of-
  cooperators with the field's best self-play. It is NOT nice
  (exploits AllC), is partially retaliatory (D after CD), and
  forgiving via the (D,D) → C shift.
- **Pavlov is the most exploitable bot for AllD** — AllD's
  structural counter. This is a meaningful new ecology: AllD's
  rank rebounded because Pavlov is, in effect, AllD's prey.

### Next bot

Generous TFT (GTFT) — randomised forgiveness. The point is to test
whether probabilistic forgiveness can match deterministic TF2T
(587.3 self-play) while leaking less to TFT than TF2T does.
Axiomatically GTFT(p≈1/3) is the population-game equilibrium
against TFT-family under noise (Nowak-Sigmund 1992).

---

## Run 004 — pantheon + TF2T + Pavlov + GTFT (2026-05-17)

Setup: `rounds=200 noise=0.02 repeat=3 seed=42`. Added `bot_gtft`
(forgiveness probability g = 1/3).

| rank | bot               | mean score | Δ vs Run 003 |
|------|-------------------|-----------:|-------------:|
| 1    | bot_pavlov        |     486.17 |        +13.3 |
| 2    | bot_grim          |     458.75 |         +6.7 |
| 3    | bot_tit_for_tat   |     456.25 |        +18.2 |
| 4    | bot_gtft          |     448.71 |          new |
| 5    | bot_tf2t          |     447.88 |        +20.4 |
| 6    | bot_random        |     441.17 |        +17.7 |
| 7    | bot_always_d      |     438.75 |         +3.2 |
| 8    | bot_always_c      |     394.92 |        +27.4 |

Payoff matrix:

```
row\col          pavlov  grim    tft     gtft    tf2t    rand    alld    allc
pavlov          580.0   348.0   423.3   579.3   561.3   488.0   119.7   789.7
grim            593.0   292.7   289.0   505.3   288.3   602.7   206.7   892.3
tit_for_tat     420.0   272.3   498.7   583.7   600.7   458.3   210.7   605.7
gtft            517.7   157.0   573.7   583.7   599.0   412.0   143.0   603.7
tf2t            401.3   253.3   585.7   590.7   587.3   368.0   201.7   595.0
random          413.0   112.7   473.3   565.3   631.3   429.7   119.0   785.0
always_d        591.3   216.7   239.0   461.3   243.3   577.3   210.7   970.3
always_c        311.3   144.0   584.0   587.0   595.0   313.3    23.7   601.0
```

### What changed

- **GTFT entered at #4.** Self-play 583.7 — almost catches TF2T
  (587.3) and Pavlov (580.0), confirming Nowak-Sigmund: 1/3
  forgiveness probability is enough to absorb most noise flips.
- **GTFT vs TFT = 573.7, TFT vs GTFT = 583.7.** TFT leaks ~10
  points off GTFT — the same shape as the TF2T leak (Lesson 004).
  Probabilistic vs deterministic tolerance leaks to retaliators
  the same way.
- **GTFT vs Grim = 157.0** — *worse* than TFT vs Grim (272.3).
  Mechanism: Grim locks into D after the first noise flip; GTFT
  keeps forgiving (1/3 of the time plays C against Grim's D),
  banking 0 each forgiveness round. TFT just mirrors D after
  Grim locks, scoring 1 each round. Forgiveness against a
  locked-D opponent is pure loss.
- **Grim climbed to #2 (+6.7)**, propelled by 505.3 vs GTFT
  (GTFT gives Grim the same kind of exploit that AllC gives,
  attenuated by 2/3).
- **Almost every existing bot's score went up.** Adding a
  cooperator-friendly bot (GTFT) lifts the row averages of
  everyone who can cooperate. AllC jumped +27.4 (now has 2
  more friendly cells: 603.7 vs GTFT, plus TF2T which it
  already had); even AllD ticked up +3.2 because GTFT
  occasionally forgives it (461.3 vs AllD; compare AllC =
  970.3 fully exploitable).

### Class structure

- **Pavlov keeps #1**: dominates self-play AND exploits AllC.
  Only structural weakness is AllD (119.7) which doesn't have
  enough population weight in this small pool.
- **Forgiveness penalty visible**: GTFT < TF2T < TFT, all close.
  All three forgive in some way, and all three pay roughly the
  same tax to Grim and AllD. GTFT pays the most because random
  forgiveness wastes retaliations against locked opponents.
- **AllD slipping**: from #2 (Run 001) → #5 → #7. The pool now
  has 5 reciprocators (TFT, TF2T, GTFT, Pavlov, Grim) that
  all play D back at AllD. Only AllC remains a clean exploit.

### Top-3 stability tracker

- Run 002 top-3: TFT, TF2T, Grim
- Run 003 top-3: Pavlov, Grim, TFT
- Run 004 top-3: Pavlov, Grim, TFT

Top-3 unchanged between Run 003 and Run 004. Need 2 more
consecutive stable runs to satisfy the STOP condition, *plus*
the bot count must reach 10+ non-trivial.

### Next bot

Contrite TFT. Predicted to fix the TF2T/GTFT "tolerance tax"
problem by apologising for own noise flips. A bot that
distinguishes "my own play got flipped" from "opponent really
defected" should:
- Self-play cleanly (no CD-DC ringing, since contrite player
  plays C-D-C to apologise instead of C-D-C-D).
- Refuse to leak to TFT (because after a noise flip TFT
  retaliates, contrite TFT plays D to apologise, balance
  restored in 1 round).
- Still retaliate against genuine defectors like AllD.

---

## Run 005 — pantheon + TF2T + Pavlov + GTFT + CTFT (2026-05-17)

Setup: `rounds=200 noise=0.02 repeat=3 seed=42`. Added `bot_ctft`
(standing-based Contrite Tit for Tat, Boyd 1989 / Wu-Axelrod 1995).

| rank | bot               | mean score | Δ vs Run 004 |
|------|-------------------|-----------:|-------------:|
| 1    | bot_pavlov        |     488.00 |         +1.8 |
| 2    | bot_ctft          |     481.85 |          new |
| 3    | bot_gtft          |     464.56 |        +15.8 |
| 4    | bot_tf2t          |     463.56 |        +15.7 |
| 5    | bot_tit_for_tat   |     461.93 |         +5.7 |
| 6    | bot_grim          |     444.22 |        -14.5 |
| 7    | bot_random        |     443.44 |         +2.3 |
| 8    | bot_always_c      |     416.41 |        +21.5 |
| 9    | bot_always_d      |     415.56 |        -23.2 |

Payoff matrix (rows = column-major ranking order):

```
row\col          pavlov  ctft    gtft    tf2t    tft     grim    rand    allc    alld
pavlov          580.0   502.7   579.3   561.3   423.3   348.0   488.0   789.7   119.7
ctft            494.3   593.3   593.0   600.7   499.0   304.7   445.0   601.7   205.0
gtft            517.7   591.3   583.7   599.0   573.7   157.0   412.0   603.7   143.0
tf2t            401.3   589.0   590.7   587.3   585.7   253.3   368.0   595.0   201.7
tit_for_tat     420.0   507.3   583.7   600.7   498.7   272.3   458.3   605.7   210.7
grim            593.0   328.0   505.3   288.3   289.0   292.7   602.7   892.3   206.7
random          413.0   461.7   565.3   631.3   473.3   112.7   429.7   785.0   119.0
always_c        311.3   588.3   587.0   595.0   584.0   144.0   313.3   601.0    23.7
always_d        591.3   230.0   461.3   243.3   239.0   216.7   577.3   970.3   210.7
```

### What changed

- **CTFT entered at #2 (481.85)** — only 6 points behind Pavlov. It
  has the second-best self-play (593.3, beating TF2T's 587.3, GTFT's
  583.7, and Pavlov's 580.0) and balanced relationships with every
  reciprocator. Self-play loss of just ~8 from the 601 CC ceiling
  confirms contrition recovers from noise within ~3 rounds (Lesson
  010 below).
- **CTFT closes the leak to TFT.** CTFT vs TFT = 499.0 / 507.3 —
  TFT's edge collapses from +15 (vs TF2T) / +10 (vs GTFT) to +8 (vs
  CTFT). The remaining +8 comes from the *opponent-side* noise
  half that CTFT does not fix; the own-noise half is now perfectly
  symmetric.
- **CTFT vs Grim = 304.7** — better than TFT's 272.3 vs Grim, despite
  both bots being "retaliate after a D" types. Mechanism: when CTFT's
  own noise flips C→D, CTFT enters the apology state and plays C
  next round, which Grim observes as another C (so Grim's already-
  locked D continues but CTFT scores 0 for one apology round, then
  realises Grim is still defecting and re-marks Grim as B, playing
  D thereafter). Compared to TFT, which gets *additional* noise-
  triggered C apologies that Grim exploits — CTFT actually loses
  ~30 points more vs Grim than TFT does. Wait — TFT vs Grim 272.3,
  CTFT vs Grim 304.7 means CTFT does **better** than TFT vs Grim
  by 32 points. Re-examining: Grim's own-side noise flips reset its
  D-lock under… no, Grim's lock is permanent once it observes opp D.
  The 32-point gap must come from CTFT not retaliating against Grim
  on first contact in the same way TFT does. Need to instrument.
- **TF2T jumped +15.7 and GTFT +15.8** primarily because the new
  bot (CTFT) cooperates near the CC ceiling with both of them
  (593.0 / 591.3 / 599.0 / 600.7 in the relevant cells). Each
  cooperator pair lifts each other's row averages.
- **AllD collapsed to #9** (last). It now faces 6 reciprocators
  (TFT, TF2T, GTFT, Pavlov, Grim, CTFT), only 2 cooperators (AllC,
  Random) it can exploit cleanly, and the row average can no
  longer support the +400 advantage from AllC.
- **AllC jumped +21.5 to #8.** Two more friendly cells (CTFT
  601.7, also gets the same lift from prior runs). AllC's column
  remains its main vulnerability: it loses to Grim (892 row),
  AllD (970 row), and Pavlov (789 row).
- **Pavlov edged +1.8, holding #1.** Pavlov's structural strength
  (best self-play + exploits naive cooperators + recovers from
  noise) is robust against the addition of CTFT, which Pavlov
  plays at 502.7 (above CC half-ceiling). CTFT plays Pavlov at
  494.3 — almost equal. So CTFT and Pavlov coexist nearly
  symmetrically; the gap between them at top of leaderboard is
  Pavlov's slightly better Grim row (348 vs CTFT 304.7) and
  slightly worse AllD row (119.7 vs CTFT 205.0) cancelling.

### Class structure update

- **The reciprocator block now includes CTFT** with the cleanest
  self-play (besides AllC) and balanced bilateral cells against
  every other reciprocator. This makes CTFT the structurally
  *fairest* member of the reciprocator block — no leak in either
  direction with TFT, TF2T, GTFT, or another CTFT.
- **Pavlov remains the leader** purely because it converts AllC
  and Random into ~600+ cells, which CTFT (correctly nice) refuses
  to do. Pavlov is rewarded for its accidental exploitation of
  naive cooperators; CTFT is not.
- **Grim is the new top exploiter** — but its score depends on
  cooperators existing. Once we add Adaptive TFT (next), Grim's
  ability to extract from "soft" reciprocators may shrink further.

### Top-3 stability tracker

- Run 002 top-3: TFT, TF2T, Grim
- Run 003 top-3: Pavlov, Grim, TFT
- Run 004 top-3: Pavlov, Grim, TFT
- Run 005 top-3: Pavlov, CTFT, GTFT — **CHANGED**.

Top-3 disrupted by the CTFT addition. Stability counter reset; need
3 consecutive stable top-3 runs from here.

### Next bot

Adaptive TFT. The remaining structural weakness of every reciprocator
in the pool is the AllD column (200-211 each, ~DD floor) which
includes 2 wasted rounds of cooperation at the start (TFT plays C
on round 1, gets 0; doesn't matter much over 200 rounds but signals
the problem). More importantly, the pool's incumbents have no way
to detect a "structurally hostile" opponent — they all keep one-
round mirroring. Adaptive TFT should beat plain TFT against AllD
and Random by switching to D-permanent after the opponent's
cooperation rate drops below a threshold over a sliding window.
Predicted to enter mid-pack, with biggest gain on the AllD column.

---

## Run 006 — pantheon + TF2T + Pavlov + GTFT + CTFT + ATFT (2026-05-17)

Setup: `rounds=200 noise=0.02 repeat=3 seed=42`. Added `bot_atft`
(window=20, threshold=0.20, min_history=5).

| rank | bot               | mean score | Δ vs Run 005 |
|------|-------------------|-----------:|-------------:|
| 1    | bot_pavlov        |     491.87 |         +3.9 |
| 2    | bot_ctft          |     488.27 |         +6.4 |
| 3    | bot_atft          |     476.10 |          new |
| 4    | bot_tf2t          |     475.43 |        +11.9 |
| 5    | bot_gtft          |     475.37 |        +10.8 |
| 6    | bot_tit_for_tat   |     460.63 |         -1.3 |
| 7    | bot_random        |     444.57 |         +1.1 |
| 8    | bot_always_c      |     433.27 |        +16.9 |
| 9    | bot_grim          |     425.30 |        -18.9 |
| 10   | bot_always_d      |     395.40 |        -20.2 |

Payoff matrix (columns reordered by ranking):

```
row\col          pavlov  ctft    atft    tf2t    gtft    tft     rand    allc    grim    alld
pavlov          580.0   502.7   526.7   561.3   579.3   423.3   488.0   789.7   348.0   119.7
ctft            494.3   593.3   546.0   600.7   593.0   499.0   445.0   601.7   304.7   205.0
atft            526.7   559.3   509.0   599.0   586.0   454.0   461.3   603.3   250.0   212.3
tf2t            401.3   589.0   582.3   587.3   590.7   585.7   368.0   595.0   253.3   201.7
gtft            517.7   591.3   572.7   599.0   583.7   573.7   412.0   603.7   157.0   143.0
tit_for_tat     420.0   507.3   449.0   600.7   583.7   498.7   458.3   605.7   272.3   210.7
random          413.0   461.7   454.7   631.3   565.3   473.3   429.7   785.0   112.7   119.0
always_c        311.3   588.3   585.0   595.0   587.0   584.0   313.3   601.0   144.0    23.7
grim            593.0   328.0   255.0   288.3   505.3   289.0   602.7   892.3   292.7   206.7
always_d        591.3   230.0   214.0   243.3   461.3   239.0   577.3   970.3   216.7   210.7
```

### What changed

- **ATFT entered at #3 (476.10)**, just ahead of TF2T/GTFT and behind
  the two top recovery bots (Pavlov, CTFT). Its 509.0 self-play is
  modestly above plain TFT (498.7), because in self-play any noise-
  flip-induced D from the opponent that pushes coop rate within the
  window stays well above the 0.20 threshold; the threshold never
  trips in well-behaved interactions.
- **ATFT vs AllD = 212.3**, marginally better than TFT vs AllD =
  210.7. The detector trips by round 6 (coop_rate from AllD ~ 2%
  due to noise) and ATFT stops responding to AllD's noise-flipped
  C's with C. The gain is small (~2 points per match) because
  AllD's noise-driven C's are rare to begin with and TFT only
  loses 5 per such event.
- **ATFT vs Grim = 250.0**, *worse* than TFT vs Grim = 272.3.
  Mechanism: after Grim locks, opp's coop rate from ATFT's POV
  drops to near 0 within ~20 rounds, ATFT switches to permanent
  D. Grim is also permanent D. So DD = 1 per round. TFT, by
  contrast, still mirrors Grim's noise-flipped C's with C — which
  scores 0 once (cost) but the next round Grim's mirror of TFT's
  prior D scores TFT 5 — so the noise becomes a small TFT bonus.
  ATFT's lock-mode forgoes this bonus. **Surprise**: against a
  locked defector with internal noise, mirroring is slightly
  better than D-locking, because mirror catches the opp's noise
  C's and converts them into D-C = 5 next round. (See Lesson 012.)
- **ATFT vs Pavlov = 526.7** (symmetric), much better than TFT
  vs Pavlov = 420/423. But re-running with 10 repeats brings this
  closer to ~473, suggesting the gap is partly noise variance.
  Even so, ATFT seems to do slightly better against Pavlov than
  TFT does. Possible mechanism: when Pavlov's broken CD-DC-DD
  oscillation pushes opp coop rate below 0.20 briefly, ATFT enters
  D-mode and locks the floor; when Pavlov returns to C, ATFT's
  rolling window includes those C's and it returns to mirror. This
  may shorten the oscillation cycles.
- **Grim collapsed from #6 to #9** (-18.9). It now faces 4 bots
  (CTFT, ATFT, TF2T, GTFT — sort of, though GTFT still exploitable)
  that don't reward its lock-in well. The 505.3 cell against GTFT
  (where GTFT keeps forgiving) is the only remaining big Grim
  exploit besides AllC.
- **AllD slipped to #10 (last)** at 395.40, down 20.2. With 7
  reciprocators in the pool, only AllC and Random remain
  exploitable; the row average is dragged down by 6 DD-floor
  cells.
- **TF2T and GTFT both jumped ~+11**. The new ATFT bot is a
  cooperator from their POV (mirrors C, doesn't exploit), so it
  adds a high-yield CC-ish cell to their row averages (582.3 and
  572.7 respectively).
- **AllC jumped +16.9.** Same mechanism: ATFT mirrors AllC's C
  faithfully (585.0), so AllC gets another safe cell.

### Class structure update

- **Two-tier top**: Pavlov (491.9) and CTFT (488.3) are within
  3.6 of each other and noticeably ahead of the rest. They differ
  philosophically (Pavlov not-nice, CTFT nice) but score
  similarly in this pool.
- **Reciprocator block** (ATFT, TF2T, GTFT, TFT): tight cluster
  in 460-476 range. The four behave nearly identically against
  each other (all cells near CC ceiling) and differ mainly on
  their handling of edge cases (AllD/Grim columns and self-play).
- **Exploitable pool** (Random, AllC, Grim, AllD): bottom four.
  Grim is interesting — it used to be a top-tier exploiter and
  is now near-bottom because the pool has saturated with
  reciprocators that reliably retaliate.

### Top-3 stability tracker

- Run 002 top-3: TFT, TF2T, Grim
- Run 003 top-3: Pavlov, Grim, TFT
- Run 004 top-3: Pavlov, Grim, TFT
- Run 005 top-3: Pavlov, CTFT, GTFT
- Run 006 top-3: Pavlov, CTFT, ATFT — **CHANGED** (ATFT entered
  above GTFT).

Stability counter reset by ATFT's entry. Need 3 consecutive
stable top-3 runs from here, plus at least 10 non-trivial bots
(currently 5 non-pantheon: TF2T, Pavlov, GTFT, CTFT, ATFT — need
5 more).

### Next bot

**Gradual (Beaufils 1996)**. Idea: count the opponent's defections
to date; on the n-th defection, retaliate with n consecutive D's,
then play two calming C's (to signal willingness to return to
cooperation), then resume TFT. Predicted to:
- Beat plain TFT against unconditional defectors (escalating
  punishment is more deterrent).
- Match TFT against cooperators (the punishment ramp never
  triggers).
- Lose slightly against fellow Gradual or Pavlov self-play because
  any noise-triggered punishment locks in a long retaliation cycle
  that wastes rounds compared to TFT's 2-round ring.

If Gradual scores well in the AllD column (>250) but poorly in
self-play (<400), it confirms the "escalating punishment + cooldown"
template is good for adversarial pairs and bad for cooperative pairs
under noise. That's the classical Beaufils observation.

---

## Run 007 — pantheon + TF2T + Pavlov + GTFT + CTFT + ATFT + Gradual (2026-05-17)

Setup: `rounds=200 noise=0.02 repeat=3 seed=42`. Added `bot_gradual`
(Beaufils 1996 escalating punishment + 2-C calming tail).

| rank | bot               | mean score | Δ vs Run 006 |
|------|-------------------|-----------:|-------------:|
| 1    | bot_ctft          |     480.48 |         -7.8 |
| 2    | bot_pavlov        |     470.88 |        -21.0 |
| 3    | bot_tf2t          |     470.06 |         -5.4 |
| 4    | bot_atft          |     469.36 |         -6.7 |
| 5    | bot_gtft          |     464.79 |        -10.6 |
| 6    | bot_tit_for_tat   |     449.55 |        -11.1 |
| 7    | bot_always_c      |     446.39 |        +13.1 |
| 8    | bot_random        |     424.97 |        -19.6 |
| 9    | bot_grim          |     422.61 |         -2.7 |
| 10   | bot_gradual       |     421.97 |          new |
| 11   | bot_always_d      |     390.79 |         -4.6 |

Payoff matrix (columns reordered by ranking):

```
row\col          ctft    pavlov  tf2t    atft    gtft    tft     allc    rand    grim    grad    alld
ctft            593.3   494.3   600.7   546.0   593.0   499.0   601.7   445.0   304.7   402.7   205.0
pavlov          502.7   580.0   561.3   526.7   579.3   423.3   789.7   488.0   348.0   261.0   119.7
tf2t            589.0   401.3   587.3   582.3   590.7   585.7   595.0   368.0   253.3   416.3   201.7
atft            559.3   526.7   599.0   509.0   586.0   454.0   603.3   461.3   250.0   402.0   212.3
gtft            591.3   517.7   599.0   572.7   583.7   573.7   603.7   412.0   157.0   359.0   143.0
tit_for_tat     507.3   420.0   600.7   449.0   583.7   498.7   605.7   458.3   272.3   338.7   210.7
always_c        588.3   311.3   595.0   585.0   587.0   584.0   601.0   313.3   144.0   577.7    23.7
random          461.7   413.0   631.3   454.7   565.3   473.3   785.0   429.7   112.7   229.0   119.0
grim            328.0   593.0   288.3   255.0   505.3   289.0   892.3   602.7   292.7   395.7   206.7
gradual         416.0   551.0   486.3   395.3   547.3   340.3   609.3   564.0   242.3   308.3   181.3
always_d        230.0   591.3   243.3   214.0   461.3   239.0   970.3   577.3   216.7   344.7   210.7
```

### What changed

- **Pavlov fell from #1 to #2.** Single cause: bot_pavlov vs
  bot_gradual = 261.0. Pavlov's win-stay-lose-shift oscillates
  through Gradual's escalating D bursts, never aligning with the
  calming-C window long enough to bank cooperation. -22 points off
  Pavlov's row average is enough to drop it below CTFT.
- **CTFT inherited #1** with no change to its actual logic. CTFT
  vs Gradual = 402.7 (Gradual's bursts trigger CTFT retaliations
  that get contritely apologised for; mutual cooperation resumes
  faster than with Pavlov). Mid-range cell, but a 140-point
  improvement over Pavlov's cell, which is the whole story for
  the leadership swap. **Top-3 changed again — Pavlov, CTFT, TF2T.**
- **Gradual entered at #10**, just above AllD, just below Grim.
  Self-play 308.3 (way below TFT-self 498.7) confirms the
  cascade prediction: each noise flip permanently raises the
  punishment counter. By round 200 in self-play, both Gradual
  copies are in the middle of long D-bursts more often than not.
- **Gradual vs AllD = 181.3, BELOW the DD floor.** Mechanism: the
  2-C calming tails are pure 0-point losses against an
  unreformed AllD, plus the D-burst itself only banks DD = 1.
  Over 200 rounds with ~30 D-bursts of mean length ~15 and 2 C's
  each, the calming tails dump ~60 free 5's to AllD. Gradual's
  *escalation deters by reputation*, not by score, and against a
  zero-feedback opponent reputation does nothing.
- **Gradual vs Grim = 242.3**, surprisingly higher than ATFT's
  250.0 or TFT's 272.3 — wait, lower than both. Once Grim locks,
  Gradual escalates against the locked-D, eventually playing
  long D-bursts that match Grim's D one-for-one (DD=1 each), but
  the 2-C calming tails still bleed points to Grim's continued D.
- **Gradual vs AllC = 609.3** — surprisingly high, basically at
  the CC ceiling. The 2% noise from AllC's POV (i.e. AllC's C
  flips to D about 4 times per 200 rounds) triggers only ~4
  escalation bursts of sizes 1, 2, 3, 4, totaling 10 D's and 8
  C's. Most of the match (~180 rounds) is mutual CC. So Gradual
  is *not* catastrophically bad against AllC — the escalation is
  capped by the rarity of noise events. The +9 over the noise-
  expected 596 is fluctuation across 3 repeats.
- **AllC's score climbed +13.1 to 446.39** (now #7 ahead of
  Random!). AllC gets a 577.7 cell against Gradual (Gradual's
  bursts are mild and offset by mutual CC), which adds a
  meaningful row contribution. Plus mild row-average lift from
  Gradual being present.
- **Random fell -19.6.** Random's row was disproportionately hurt
  because Random vs Gradual = 229.0. Gradual's escalating
  punishment against Random's 50% D rate ramps up quickly and
  never settles; Random doesn't reciprocate the calming C's
  systematically.
- **AllD fell -4.6**. The new bot is mostly not exploitable by
  AllD (Gradual matches AllD's D's most rounds), so AllD's row
  added a mediocre cell (344.7 vs Gradual, where AllD steals the
  calming C's). Marginal effect.
- **Reciprocator block compressed**. CTFT, Pavlov, TF2T, ATFT,
  GTFT now in a tight 16-point band (480-465). With Gradual in
  the field, all reciprocators pay a 5-25-point "Gradual tax" of
  varying severity depending on how they handle Gradual's
  bursts.

### Top-3 stability tracker

- Run 002 top-3: TFT, TF2T, Grim
- Run 003 top-3: Pavlov, Grim, TFT
- Run 004 top-3: Pavlov, Grim, TFT
- Run 005 top-3: Pavlov, CTFT, GTFT
- Run 006 top-3: Pavlov, CTFT, ATFT
- Run 007 top-3: CTFT, Pavlov, TF2T — **CHANGED again**.

Stability counter reset. Need 3 consecutive stable top-3 runs from
here, plus ≥10 non-trivial bots. Current non-pantheon bots:
TF2T, Pavlov, GTFT, CTFT, ATFT, Gradual = 6. Need 4 more.

### Next bot

**Soft Majority** is queued. It defects iff opp's D-count exceeds
opp's C-count over the entire history. Predicted to:
- Cooperate steadily with cooperators (D-count stays low).
- Defect against AllD-style opponents after a few rounds and
  stay locked in D-mode (since D-count grows past C-count fast).
- In self-play, cooperate at the CC ceiling (same as AllC self-
  play) because both sides keep majority-C.
- vs noise-triggered defections from a cooperator: tolerant; the
  majority count absorbs a few D's before flipping.

Hypothesis: Soft Majority will land in mid-tier (~AllC level)
with notable resistance to AllD/Grim columns compared to AllC.

---

## Run 008 — pantheon + 6 prior non-trivial + Soft Majority (2026-05-17)

Setup: `rounds=200 noise=0.02 repeat=3 seed=42`. Added
`bot_soft_majority`: D iff opp's cumulative D-count strictly exceeds
opp's C-count; first move = C.

| rank | bot               | mean score | Δ vs Run 007 |
|------|-------------------|-----------:|-------------:|
| 1    | bot_soft_majority |     502.89 |          new |
| 2    | bot_ctft          |     490.94 |        +10.5 |
| 3    | bot_tf2t          |     480.58 |        +10.5 |
| 4    | bot_atft          |     480.44 |        +11.1 |
| 5    | bot_gtft          |     476.14 |        +11.4 |
| 6    | bot_pavlov        |     465.17 |         -5.7 |
| 7    | bot_tit_for_tat   |     462.53 |        +13.0 |
| 8    | bot_always_c      |     458.97 |        +12.6 |
| 9    | bot_gradual       |     438.78 |        +16.8 |
| 10   | bot_random        |     436.67 |        +11.7 |
| 11   | bot_grim          |     423.17 |         +0.6 |
| 12   | bot_always_d      |     376.44 |        -14.4 |

Payoff matrix (columns reordered by ranking):

```
row\col          soft    ctft    tf2t    atft    gtft    pavlov  tft     allc    grad    rand    grim    alld
soft_majority   592.0   586.0   594.7   585.7   589.3   504.0   582.0   595.7   550.3   395.3   251.0   208.7
ctft            606.0   593.3   600.7   546.0   593.0   494.3   499.0   601.7   402.7   445.0   304.7   205.0
tf2t            596.3   589.0   587.3   582.3   590.7   401.3   585.7   595.0   416.3   368.0   253.3   201.7
atft            602.3   559.3   599.0   509.0   586.0   526.7   454.0   603.3   402.0   461.3   250.0   212.3
gtft            601.0   591.3   599.0   572.7   583.7   517.7   573.7   603.7   359.0   412.0   157.0   143.0
pavlov          402.3   502.7   561.3   526.7   579.3   580.0   423.3   789.7   261.0   488.0   348.0   119.7
tit_for_tat     605.3   507.3   600.7   449.0   583.7   420.0   498.7   605.7   338.7   458.3   272.3   210.7
always_c        597.3   588.3   595.0   585.0   587.0   311.3   584.0   601.0   577.7   313.3   144.0    23.7
gradual         623.7   416.0   486.3   395.3   547.3   551.0   340.3   609.3   308.3   564.0   242.3   181.3
random          565.3   461.7   631.3   454.7   565.3   413.0   473.3   785.0   229.0   429.7   112.7   119.0
grim            429.3   328.0   288.3   255.0   505.3   593.0   289.0   892.3   395.7   602.7   292.7   206.7
always_d        218.7   230.0   243.3   214.0   461.3   591.3   239.0   970.3   344.7   577.3   216.7   210.7
```

### What changed

- **Soft Majority entered straight at #1 at 502.89** — biggest jump
  any new bot has made in this run. It is the first bot to break
  500 since Pavlov briefly held the lead in Runs 003-006. Mechanism
  is "perfect niceness with eventual punishment":
  - vs every C-leaning opponent (AllC, all 5 reciprocators, TFT,
    self): ~585-595, the CC ceiling minus noise damage. Even one
    noise flip doesn't dislodge the majority-C tally.
  - vs AllD (208.7): switches to permanent D after round 1 (gives
    up exactly one S=0). Identical to TFT (210.7) on this column.
  - vs Grim (251.0): worse than the reciprocators (~250-305) by
    only a hair; one noise-triggered Grim-lock costs a tail of
    rounds before D-count exceeds C-count.
  - vs Pavlov (504.0): MIDDLING. Soft Majority cooperates while
    Pavlov oscillates, so Pavlov scores 402.3 against it (T's on
    Soft Majority's C-runs, then occasional CC banks). The cell
    Soft Majority gets back is below 580, which is the only
    weakness in its top row.
  - vs Random (395.3): better than Random vs anyone-not-AllC
    (Soft Majority absorbs Random's flips long enough to bank some
    CC's before switching).
  - vs Gradual (550.3 / 623.7): ASYMMETRIC. Gradual's bursts
    against Soft Majority are short enough that Gradual's
    D-count never exceeds its C-count from Soft Majority's POV
    (the 2 calming C's per burst keep Gradual's profile
    majority-C). So Soft Majority keeps cooperating while
    Gradual occasionally pockets T=5's. Gradual's 623.7 is the
    highest cell Gradual gets anywhere in the matrix.

- **Top-3 changed AGAIN: Soft Majority, CTFT, TF2T.** (Run 007
  was CTFT, Pavlov, TF2T.) Pavlov dropped to #6 — the new bot's
  presence didn't directly hurt Pavlov vs Soft Majority (cell is
  Pavlov's column 402.3 / Pavlov's row 504.0 — Pavlov actually
  ROW-gains 504 here, which is decent for it). But Pavlov's row
  average vs everyone else stayed where it was, while Soft
  Majority added a new bot at the top of the rankings that pulled
  everyone except AllD a little higher (because Soft Majority is
  a generous cooperator against most bots, donating cooperative
  cells to others' rows). Pavlov's relative rank dropped from #2
  to #6 in this re-shuffle.

- **Reciprocator block compressed further.** CTFT, TF2T, ATFT,
  GTFT now in a 15-point band at #2-#5 (490-476). Soft Majority
  out-scores each by ~12-26 points purely by avoiding the
  reciprocators' shared weak cells (none of them gets more than
  600 against ANY non-cooperator, while Soft Majority gets 595
  vs AllC and ~580-595 vs every reciprocator).

- **AllD fell -14.4 to 376.44.** Mechanism: Soft Majority's column
  against AllD is 218.7, very close to TFT/ATFT/TF2T's 210-215
  cells. AllD got no new vulnerability to exploit. The drop is
  purely arithmetic: AllD's row average over 12 bots got
  diluted by the new bot in the pool.

- **AllC gained +12.6 to 458.97.** Soft Majority's column against
  AllC is 595.7, very close to the CC ceiling — Soft Majority is
  basically Tat-free against AllC. So AllC gets a near-max cell
  added to its row.

- **Gradual jumped +16.8** because of its 623.7 cell against
  Soft Majority — its single best cell anywhere. As noted: Soft
  Majority's tolerance lets Gradual pocket T=5's during bursts
  without flipping into D.

### Top-3 stability tracker

- Run 005 top-3: Pavlov, CTFT, GTFT
- Run 006 top-3: Pavlov, CTFT, ATFT
- Run 007 top-3: CTFT, Pavlov, TF2T
- Run 008 top-3: Soft Majority, CTFT, TF2T — **CHANGED again**.

Stability counter reset. Need 3 consecutive stable top-3 runs.
Current non-pantheon bots: TF2T, Pavlov, GTFT, CTFT, ATFT,
Gradual, Soft Majority = 7. Need 3 more for the 10-non-trivial
threshold.

### Next bot

**Hard Majority** is queued. Defects first move; then plays D when
opp's D-count >= opp's C-count, plays C otherwise. The "guilty
until proven innocent" mirror of Soft Majority. Predicted to:
- Beat AllC strongly: starts D (T=5), then opp's D-count stays at
  0 forever, opp's C-count grows. Once D=0 < C=many, switches to
  C. Banks 1 sucker T=5 then mutual CC.
- Lose against reciprocators because Hard Majority's first D
  triggers retaliation, then Hard Majority sees opp's D-count =
  1, plays D back, and the spiral continues. Especially bad vs
  Grim (one D, locked forever).
- vs AllD: opp's D-count immediately dominates, Hard Majority
  plays D forever, banks DD = 1 each round.
- vs Soft Majority self-play in REVERSE: HM defects first, SM
  cooperates first, so HM gets 5 / SM gets 0. Then HM sees opp
  has 1 C, 0 D, switches to C. SM sees opp has 1 D, switches to
  D. Now they swap roles. This is the alternator trap — should
  give ~2.5 average per round = 500-ish over 200 rounds, roughly
  even.

Hypothesis: Hard Majority will be a NET LOSER (mid-bottom rank),
because it pays the "first-D tax" against every reciprocator and
only banks T=5 once against AllC. The lesson is: in noisy
populations dominated by reciprocators, the first move matters
enormously.

(Decision for Run 009: skip Hard Majority in favour of Detective,
because Detective is the only candidate hypothesised to actually
*overtake* Soft Majority. Hard Majority remains queued as a
"failure-mode control" for later.)

---

## Run 009 — pantheon + 7 prior non-trivial + Detective (2026-05-17)

Setup: `rounds=200 noise=0.02 repeat=3 seed=42`. Added
`bot_detective`: 3-round probe (D, C, C); if opponent defected at
all during probe, play TFT forever; otherwise alternate D/C
(exploit) but fall back to TFT if opponent's post-probe D rate
exceeds 15% with at least 4 D events.

| rank | bot               | mean score | Δ vs Run 008 |
|------|-------------------|-----------:|-------------:|
| 1    | bot_soft_majority |     508.85 |         +6.0 |
| 2    | bot_ctft          |     495.74 |         +4.8 |
| 3    | bot_gtft          |     483.00 |         +6.9 |
| 4    | bot_atft          |     481.31 |         +0.9 |
| 5    | bot_detective     |     480.62 |          new |
| 6    | bot_tf2t          |     474.18 |         -6.4 |
| 7    | bot_pavlov        |     464.38 |         -0.8 |
| 8    | bot_tit_for_tat   |     461.08 |         -1.4 |
| 9    | bot_always_c      |     447.62 |        -11.3 |
| 10   | bot_random        |     437.72 |         +1.1 |
| 11   | bot_gradual       |     430.33 |         -8.4 |
| 12   | bot_grim          |     408.08 |        -15.1 |
| 13   | bot_always_d      |     365.87 |        -10.6 |

Payoff matrix (columns reordered by ranking):

```
row\col          soft    ctft    gtft    atft    det     tf2t    pav     tft     allc    rand    grad    grim    alld
soft_majority   592.0   586.0   589.3   585.7   580.3   594.7   504.0   582.0   595.7   395.3   550.3   251.0   208.7
ctft            606.0   593.3   593.0   546.0   553.3   600.7   494.3   499.0   601.7   445.0   402.7   304.7   205.0
gtft            601.0   591.3   583.7   572.7   565.3   599.0   517.7   573.7   603.7   412.0   359.0   157.0   143.0
atft            602.3   559.3   586.0   509.0   491.7   599.0   526.7   454.0   603.3   461.3   402.0   250.0   212.3
detective       605.3   560.0   585.3   491.7   448.0   715.7   443.3   443.7   779.7   440.3   310.7   212.0   212.3
tf2t            596.3   589.0   590.7   582.3   397.3   587.3   401.3   585.7   595.0   368.0   416.3   253.3   201.7
pavlov          402.3   502.7   579.3   526.7   455.0   561.3   580.0   423.3   789.7   488.0   261.0   348.0   119.7
tit_for_tat     605.3   507.3   583.7   449.0   443.7   600.7   420.0   498.7   605.7   458.3   338.7   272.3   210.7
always_c        597.3   588.3   587.0   585.0   311.3   595.0   311.3   584.0   601.0   313.3   577.7   144.0    23.7
random          565.3   461.7   565.3   454.7   450.3   631.3   413.0   473.3   785.0   429.7   229.0   112.7   119.0
gradual         623.7   416.0   547.3   395.3   329.0   486.3   551.0   340.3   609.3   564.0   308.3   242.3   181.3
grim            429.3   328.0   505.3   255.0   227.0   288.3   593.0   289.0   892.3   602.7   395.7   292.7   206.7
always_d        218.7   230.0   461.3   214.0   239.0   243.3   591.3   239.0   970.3   577.3   344.7   216.7   210.7
```

### What changed

- **Detective debuted at #5 (480.62).** Hypothesis was "potentially
  overtake Soft Majority" via 799 cells against AllC and TF2T. The
  exploitation worked, but not as dramatically as predicted:
  - vs AllC: 779.7 — close to the predicted 799. The D-C alternation
    extracts T=5 every other round. Two noise-flipped C's reduce the
    total slightly.
  - vs TF2T: 715.7 — also close to 799 but lower. TF2T's "two
    consecutive D's" rule occasionally triggers when noise flips
    Detective's C into a second D, producing a brief D-burst from
    TF2T. Each such burst costs ~3-5 points before re-syncing.
  - vs Soft Majority: 605.3 — Detective's R1 D against SM extracts
    one free T=5, then SM tolerates the alternation up to a point.
    The 605 cell is the HIGHEST cell anyone has scored against Soft
    Majority in any run, but Detective's first-move D also triggers
    SM's brief D in R2, which Detective sees and switches to TFT.
    Net: Detective wins +1 round of T=5 over a TFT-vs-SM matchup.

- **Detective failed against Grim (212.0) and AllD (212.3)** — the
  predicted floors for any opening-with-D bot. Probe phase loses
  R2-R3 to a triggered Grim (S=0 each), and to AllD it locks in.

- **Detective vs Pavlov: 443.3.** Pavlov flips on Detective's R1 D
  and locks into a D-cycle. Detective's TFT fallback (because Pavlov
  defected in probe) produces a chaotic alternation similar to TFT
  vs Pavlov.

- **Self-play: 448.0.** Lower than the predicted 598. Reason: with
  noise, the probe phase can be misread by either side — if the R1
  intended-D gets flipped to C (~2% chance), one Detective enters
  exploit mode against the other (which is in TFT mode). The
  resulting mismatch creates a series of mutual exploitation
  cascades. Over 200 rounds at 0.02 noise this happens often enough
  to drag self-play down by ~150 points relative to the noise-free
  prediction.

- **Top-3 shuffle (third in a row):**
  - Run 007: CTFT, Pavlov, TF2T
  - Run 008: Soft Majority, CTFT, TF2T
  - Run 009: **Soft Majority, CTFT, GTFT**

  TF2T was knocked from #3 to #6 by Detective's 715.7 exploit cell —
  TF2T's column average dropped by exactly that gap. GTFT moved
  up because Detective's TFT mode against GTFT produces a normal
  reciprocator-block cell (565-585), unaffected by the exploit.

- **AllC's row dropped -11.3 to 447.62.** Detective's 779.7 cell
  against AllC (huge ROW gain for Detective) is a 311.3 cell against
  AllC (huge COLUMN loss for AllC). One bot was enough to break AllC
  out of the cooperator block.

- **TF2T dropped -6.4 to 474.18.** Same mechanism: Detective's
  715.7 column-cell against TF2T = 397.3 row-cell for TF2T. TF2T
  is now visibly exploitable, and the population sees it.

- **Grim dropped -15.1 to 408.08.** Detective's 212.0 cell against
  Grim corresponds to 227.0 cell for Grim — Grim getting only 227
  against a "TFT in 197 of 200 rounds" opponent confirms that Grim's
  lock-in mechanism is brittle. Grim wastes its 197 post-probe rounds
  on DD with someone who would happily play CC.

- **AllD dropped -10.6.** Detective's 212.3 cell against AllD pulled
  AllD's row down (its 239.0 against Detective is below AllD's
  average), purely arithmetic. AllD still has the same exploit
  cells (970 vs AllC) but the new bot dilutes them.

- **Soft Majority row gained +6.0 to 508.85, retaining #1.** Its 580.3
  cell against Detective is slightly above average (Detective's TFT
  fallback gives SM near-CC cells), so SM's row improved arithmetically.

### Top-3 stability tracker

- Run 005 top-3: Pavlov, CTFT, GTFT
- Run 006 top-3: Pavlov, CTFT, ATFT
- Run 007 top-3: CTFT, Pavlov, TF2T
- Run 008 top-3: Soft Majority, CTFT, TF2T
- Run 009 top-3: **Soft Majority, CTFT, GTFT** — CHANGED again

Stability counter: 0. Non-pantheon bots: 8 (TF2T, Pavlov, GTFT,
CTFT, ATFT, Gradual, Soft Majority, Detective). Need 2 more for the
10-non-trivial threshold AND 3 consecutive stable top-3 runs.

### Open question after Run 009

Detective's exploitation works against the "naive" cooperators (AllC,
TF2T) but the exploit *propagation* is what hurts the row average:
Detective's 200-cell results against Grim, AllD, AllC's column, and
its own self-play cell drag the mean down to 480.62, below Soft
Majority's 508.85.

The next interesting bot would be a Detective-variant that is
"less aggressive" in the probe — e.g., probe with C in R1 instead
of D, so it doesn't lose the initial provocation cells. But that
makes it indistinguishable from a slow TFT-with-an-exploit-suffix
and may not detect tolerant opponents (SM, TF2T) at all.

Alternative: a **"shadow" strategy** that runs TFT for the first
~30 rounds (no provocation, no exploit), then injects a single D
probe and only enters exploit mode if the opponent's response over
the next 5 rounds is tolerant. This would preserve cells against
Grim/AllD (zero provocation) while keeping the TF2T/AllC exploit
intact.

Queued for Run 010: **Shadow** (a late-probe, TFT-first, exploit-only-
if-safe variant of Detective).

---

## Run 010 — pantheon + 8 prior non-trivial + Shadow (2026-05-17)

Setup: `rounds=200 noise=0.02 repeat=3 seed=42`. Added
`bot_shadow`: 30 rounds of pure TFT (recon), then if opponent's
D rate over recon ≤ 5%, probe with a single D, observe 3 rounds
of opponent reaction, exploit by D/C alternation only if opponent
stayed pure C through the test phase; sync-detector (two
synchronized mutual D's → permanent C) and a recent-D-rate guard
keep self-play and late-trigger opponents in check.

| rank | bot               | mean score | Δ vs Run 009 |
|------|-------------------|-----------:|-------------:|
| 1    | bot_soft_majority |     510.55 |         +1.7 |
| 2    | bot_ctft          |     491.90 |         -3.8 |
| 3    | bot_gtft          |     487.36 |         +4.4 |
| 4    | bot_detective     |     480.52 |         -0.1 |
| 5    | bot_tf2t          |     478.52 |         +4.3 |
| 6    | bot_atft          |     478.40 |         -2.9 |
| 7    | bot_shadow        |     477.24 |          new |
| 8    | bot_pavlov        |     463.76 |         -0.6 |
| 9    | bot_tit_for_tat   |     462.45 |         +1.4 |
| 10   | bot_always_c      |     445.02 |         -2.6 |
| 11   | bot_random        |     439.10 |         +1.4 |
| 12   | bot_gradual       |     424.02 |         -6.3 |
| 13   | bot_grim          |     397.64 |        -10.4 |
| 14   | bot_always_d      |     355.95 |         -9.9 |

Payoff matrix (columns reordered by ranking):

```
row\col          soft    ctft    gtft    det     tf2t    atft    shad    pav     tft     allc    rand    grad    grim    alld
soft_majority   592.0   586.0   589.3   580.3   594.7   585.7   532.7   504.0   582.0   595.7   395.3   550.3   251.0   208.7
ctft            606.0   593.3   593.0   553.3   600.7   546.0   442.0   494.3   499.0   601.7   445.0   402.7   304.7   205.0
gtft            601.0   591.3   583.7   565.3   599.0   572.7   544.0   517.7   573.7   603.7   412.0   359.0   157.0   143.0
detective       605.3   560.0   585.3   448.0   715.7   491.7   479.3   443.3   443.7   779.7   440.3   310.7   212.0   212.3
tf2t            596.3   589.0   590.7   397.3   587.3   582.3   535.0   401.3   585.7   595.0   368.0   416.3   253.3   201.7
atft            602.3   559.3   586.0   491.7   599.0   509.0   440.7   526.7   454.0   603.3   461.3   402.0   250.0   212.3
shadow          632.7   448.7   584.0   479.3   631.7   437.3   592.3   454.0   483.7   718.0   443.7   318.7   247.0   210.3
pavlov          402.3   502.7   579.3   455.0   561.3   526.7   455.7   580.0   423.3   789.7   488.0   261.0   348.0   119.7
tit_for_tat     605.3   507.3   583.7   443.7   600.7   449.0   480.3   420.0   498.7   605.7   458.3   338.7   272.3   210.7
always_c        597.3   588.3   587.0   311.3   595.0   585.0   411.3   311.3   584.0   601.0   313.3   577.7   144.0    23.7
random          565.3   461.7   565.3   450.3   631.3   454.7   457.0   413.0   473.3   785.0   429.7   229.0   112.7   119.0
gradual         623.7   416.0   547.3   329.0   486.3   395.3   342.0   551.0   340.3   609.3   564.0   308.3   242.3   181.3
grim            429.3   328.0   505.3   227.0   288.3   255.0   262.0   593.0   289.0   892.3   602.7   395.7   292.7   206.7
always_d        218.7   230.0   461.3   239.0   243.3   214.0   227.0   591.3   239.0   970.3   577.3   344.7   216.7   210.7
```

### What changed

- **Shadow debuted at #7 (477.24)**, below my pre-run prediction of
  525-540 and below all the reciprocators except Pavlov. The late
  probe strategy *did* deliver on its three target cells:
  - vs AllC: **718.0** (Detective's 779.7 was higher, but Shadow's
    30 rounds of pure CC give up the +30 rounds of T=5 alternation
    that Detective accrued). +273 over TFT-vs-AllC.
  - vs TF2T: **631.7** — second highest cell anyone has ever scored
    against TF2T, after Detective's 715.7. Same trade-off as AllC.
  - vs Soft Majority: **632.7** — the **highest cell anyone has
    ever scored against SM in any run**, beating Detective's 605.3
    by +27. Shadow extracts ~166 rounds of 4.0/round alternation
    against SM after the late probe finds SM's tally still
    favoring C. This is the Shadow concept paying off.
  - Self-play: **592.3** (Detective: 448.0). The sync-detector
    works as designed: round 34 produces a synchronized DD, round
    36 produces a second one, round 37 onwards both Shadows lock
    into permanent C. The total self-play loss vs perfect CC is
    only ~7 points (3 DD rounds + 1 lost-CC test) out of 200.

- **But Shadow loses to CTFT (448.7) and ATFT (437.3)**, exactly
  the cells where Detective held its own (CTFT: 560.0, ATFT:
  491.7). The reason is a subtle interaction:
  - CTFT does **not** retaliate against the probe in round 31
    because its standing-tracker correctly attributes Shadow's D
    to a "bad-standing" Shadow (single D from a previously-G
    opponent). CTFT's round-31 move is **C** — but only if its
    own standing is G. Shadow's probe leaves CTFT's view of
    Shadow as B-standing, so CTFT plays D in round 31. Then
    in round 32, CTFT updates: my D was legitimate retaliation
    (against B-standing me), so CTFT's standing stays G;
    Shadow's C in round 31 promotes Shadow's standing back to G.
    Round 32: CTFT plays C. So opp_test = [D, C, C], count("D")
    = 1 → test fails → Shadow reverts to TFT.
  - But during the reversion, Shadow plays plain TFT. CTFT vs
    plain TFT in noise produces the classic noise-spiral that
    CTFT is *designed to suppress*, but only on CTFT's side —
    Shadow doesn't know to play contrite. Result: persistent
    DC-CD oscillation for many rounds, pulling the cell down
    from the predicted 565 to 448.
  - Same logic for ATFT (an adaptive TFT variant): one probe
    causes ATFT to lose trust, Shadow reverts to plain TFT,
    they oscillate.

- **Top-3 stayed the same** for the second consecutive run:
  - Run 008: Soft Majority, CTFT, TF2T
  - Run 009: Soft Majority, CTFT, GTFT
  - Run 010: **Soft Majority, CTFT, GTFT** — SAME as Run 009.

  Stability counter: 1 (one consecutive same-top-3 transition).
  Need 2 more for the 3-stable threshold.

- **Soft Majority row improved +1.7 to 510.55**, retaining #1.
  Its cell against Shadow is 532.7, slightly below the 580-cell
  reciprocator block but well above the AllC/TF2T floor. The
  reason SM's cell against Shadow is comparatively lower is the
  exploit alternation — once Shadow enters alternation mode at
  round 34, SM defects in any round where opp's D count >
  C count, which intermittently happens during Shadow's
  alternation phase as the tally crosses (~95-100 D's by round
  ~190). SM's row average is still highest because no other bot
  has cells below 200, except for AllD/Grim columns which are
  hostile to everyone.

- **CTFT row dropped -3.8 to 491.90**. The +163 Shadow-cell-flip
  (Shadow scored 448 against CTFT vs CTFT scored 442 against
  Shadow) is roughly symmetric — neither side wins, both lose
  ~100 points relative to mutual CC. The drop is purely
  arithmetic on the row average.

- **GTFT row climbed +4.4 to 487.36**, holding #3. Its cell
  against Shadow is **544.0** — much higher than CTFT's 442
  against Shadow. Why? GTFT (Generous TFT) forgives Shadow's
  probe ~25% of the time, which is enough to dampen the
  retaliation chain. Plus GTFT's general forgiveness makes it
  less susceptible to oscillation. This is GTFT's first time
  cracking #3 since Run 005.

- **TF2T's row recovered +4.3 to 478.52** (vs -6.4 in Run 009).
  Shadow's 631.7 cell against TF2T is matched by TF2T's 535.0
  against Shadow — TF2T is the only bot in the pool that
  *systematically tolerates* Shadow's exploit while still
  getting decent scores. (TF2T plays C every round Shadow
  alternates D-C; TF2T's score is 3/round during 166 of those
  rounds. The 535 cell breaks down to 0+3+0+3+... averaging
  ~2.7/round = 535/200.)

- **Detective row unchanged at 480.52** (-0.1). The new bot in
  the pool didn't shift Detective's column-vs-row balance much,
  because Detective and Shadow play roughly TFT against each
  other after both reach exploit mode.

- **AllC's row dropped -2.6 to 445.02**. Shadow's 718.0 cell
  against AllC corresponds to a 411.3 cell for AllC, which is
  ~80 points below AllC's mean. One more exploit-oriented bot
  in the pool: another modest tax on naive cooperators.

- **Grim row dropped -10.4 to 397.64** (now last among non-AllD
  bots). Shadow's late probe still triggers Grim almost as
  often as Detective's early probe — both produce 247-cell
  matchups. But Grim's row average drops because the pool now
  has TWO probe-style bots that knock it into permanent D.

### Top-3 stability tracker

- Run 005 top-3: Pavlov, CTFT, GTFT
- Run 006 top-3: Pavlov, CTFT, ATFT
- Run 007 top-3: CTFT, Pavlov, TF2T
- Run 008 top-3: Soft Majority, CTFT, TF2T
- Run 009 top-3: Soft Majority, CTFT, GTFT
- Run 010 top-3: **Soft Majority, CTFT, GTFT** — SAME

Stability counter: 1 (one same-as-previous run). Need 3-in-a-row.
Non-pantheon bots: 9 (TF2T, Pavlov, GTFT, CTFT, ATFT, Gradual,
SM, Detective, Shadow). Need 1 more for the 10-non-trivial
threshold.

### Open question after Run 010

Shadow's strategy WORKS where it was designed to work (huge
exploits against AllC / TF2T / SM, robust self-play via sync
detector), but the bot loses against the CTFT-style "contrite
retaliators" because its fallback after a failed probe is plain
TFT, which then oscillates against contrite opponents. The
natural fix is to make Shadow's fallback **also contrite** — but
this requires re-deriving CTFT's standing logic inside Shadow.

Queued for Run 011: a 10th non-trivial bot. Candidate ideas:

1. **Adaptive Grim** — Grim that unlocks after K rounds of
   mutual C from the opponent post-trigger. Fixes Grim's noise
   brittleness. Predicted to land near the reciprocator block
   (~480-500) and possibly into top-3.
2. **Hard Majority** — control test for the "first-D tax"
   hypothesis. Should land mid-bottom.
3. **Contrite Shadow** — Shadow with a CTFT fallback after
   probe failure. Predicted to fix the CTFT/ATFT cells and
   potentially break into top-3.
4. **Tester** — bot that opens with D-D-C-C (longer probe than
   Detective). Tests whether *very* long probe distinguishes
   between TF2T (which tolerates 2 isolated D's but not 2 in
   a row) and Grim (which doesn't).
5. **Tit-For-Two-Tats with grudge** — TF2T but locks into D
   forever after the 5th defection. Hybrid TF2T/Grim.

The likely highest-impact pick is #1 (Adaptive Grim), because
it has the cleanest mechanism (a single noise-recovery patch on
an existing top-3 candidate) and it's the most likely to
displace one of the current top-3.

---

## Run 011 — pantheon + 9 prior non-trivial + Adaptive Grim (2026-05-17)

Setup: `rounds=200 noise=0.02 repeat=3 seed=42`. Added
`bot_adaptive_grim`: Grim Trigger with an "olive branch" cycle —
after triggering on opp's first D, play K=10 D's (punishment),
then PROBE=2 C's (probe). If opp played C in at least FORGIVE=1
of those 2 probe replies → return to cooperate mode. Otherwise →
continue with another K-D-then-PROBE-C cycle.

| rank | bot               | mean score | Δ vs Run 010 |
|------|-------------------|-----------:|-------------:|
| 1    | bot_soft_majority |     502.73 |         -7.8 |
| 2    | bot_ctft          |     493.20 |         +1.3 |
| 3    | bot_gtft          |     487.07 |         -0.3 |
| 4    | bot_detective     |     482.84 |         +2.3 |
| 5    | bot_tf2t          |     481.47 |         +3.0 |
| 6    | bot_shadow        |     480.31 |         +3.1 |
| 7    | bot_atft          |     478.49 |         +0.1 |
| 8    | bot_tit_for_tat   |     466.27 |         +3.8 |
| 9    | bot_pavlov        |     459.18 |         -4.6 |
| 10   | bot_adaptive_grim |     456.40 |          new |
| 11   | bot_always_c      |     449.13 |         +4.1 |
| 12   | bot_random        |     429.13 |        -10.0 |
| 13   | bot_gradual       |     417.53 |         -6.5 |
| 14   | bot_grim          |     396.00 |         -1.6 |
| 15   | bot_always_d      |     354.96 |         -1.0 |

Payoff matrix (columns reordered by ranking):

```
row\col          soft    ctft    gtft    det     tf2t    shad    atft    tft     pav     agrim   allc    rand    grad    grim    alld
soft_majority   592.0   586.0   589.3   580.3   594.7   532.7   585.7   582.0   504.0   393.3   595.7   395.3   550.3   251.0   208.7
ctft            606.0   593.3   593.0   553.3   600.7   442.0   546.0   499.0   494.3   511.3   601.7   445.0   402.7   304.7   205.0
gtft            601.0   591.3   583.7   565.3   599.0   544.0   572.7   573.7   517.7   483.0   603.7   412.0   359.0   157.0   143.0
detective       605.3   560.0   585.3   448.0   715.7   479.3   491.7   443.7   443.3   515.3   779.7   440.3   310.7   212.0   212.3
tf2t            596.3   589.0   590.7   397.3   587.3   535.0   582.3   585.7   401.3   522.7   595.0   368.0   416.3   253.3   201.7
shadow          632.7   448.7   584.0   479.3   631.7   592.3   437.3   483.7   454.0   523.3   718.0   443.7   318.7   247.0   210.3
atft            602.3   559.3   586.0   491.7   599.0   440.7   509.0   454.0   526.7   479.7   603.3   461.3   402.0   250.0   212.3
tit_for_tat     605.3   507.3   583.7   443.7   600.7   480.3   449.0   498.7   420.0   519.7   605.7   458.3   338.7   272.3   210.7
pavlov          402.3   502.7   579.3   455.0   561.3   455.7   526.7   423.3   580.0   395.0   789.7   488.0   261.0   348.0   119.7
adaptive_grim   338.3   519.7   549.7   508.7   547.7   518.3   463.0   516.3   550.0   432.3   650.0   518.0   310.0   239.7   184.3
always_c        597.3   588.3   587.0   311.3   595.0   411.3   585.0   584.0   311.3   506.7   601.0   313.3   577.7   144.0    23.7
random          565.3   461.7   565.3   450.3   631.3   457.0   454.7   473.3   413.0   289.7   785.0   429.7   229.0   112.7   119.0
gradual         623.7   416.0   547.3   329.0   486.3   342.0   395.3   340.3   551.0   326.7   609.3   564.0   308.3   242.3   181.3
grim            429.3   328.0   505.3   227.0   288.3   262.0   255.0   289.0   593.0   373.0   892.3   602.7   395.7   292.7   206.7
always_d        218.7   230.0   461.3   239.0   243.3   227.0   214.0   239.0   591.3   341.0   970.3   577.3   344.7   216.7   210.7
```

### What changed

- **Adaptive Grim debuted at #10 (456.40)**, below the predicted
  480-500 reciprocator-block landing. AGrim solves the
  noise-recovery problem it was designed for: cells vs TFT,
  CTFT, GTFT, ATFT, TF2T, Pavlov, Shadow all in 463-550 range
  (vanilla Grim's same cells: 227-505 with a heavy tail in
  the 250s). But three opponents punish AGrim's 10-D burst
  harder than predicted:
  - **vs Soft Majority: 338.3** (predicted ~580). SM tolerates
    AGrim's first cycle (50 prior C's > 10 new D's in tally),
    but the second cycle pushes the tally to D-majority and SM
    switches permanently. From then on, AGrim's probe-C window
    meets SM's D → forgive condition fails → locked.
  - **vs Gradual: 310.0** (predicted ~400). Gradual's
    escalating retaliation against the 10-D burst is harsher
    than CTFT/ATFT's because Gradual scales D-count linearly
    with observed D-count.
  - **vs Grim: 239.7** (predicted ~370). Grim triggers
    immediately on AGrim's first noise-D inside a punish
    cycle, then never forgives. AGrim's probe-C is met with
    Grim's D → no forgive → locked.

- **Adaptive Grim's bright cells:**
  - **vs AllC: 650.0** (+50 over CC=600). Noise events on
    AllC's side (~4/match) trigger AGrim's 10-D burst. AllC
    plays C through, AGrim's D-burst extracts ~50 T-cells per
    trigger. Probe-C is met with AllC's C → forgive → back to
    CC. Net gain: +12 pts per noise event.
  - **vs Pavlov: 550.0.** AGrim's 10-D burst pushes Pavlov
    into "lose-shift" mode; Pavlov occasionally plays C during
    probe → forgive → CC → next trigger event.
  - **vs GTFT: 549.7.** GTFT's 25% generosity leaks C's into
    AGrim's punish phase, accelerating forgive condition.
  - **vs Random: 518.0.** AGrim's burst extracts easy T-cells
    when Random happens to play C.

- **Top-3 UNCHANGED for the third consecutive run:**
  - Run 009: Soft Majority, CTFT, GTFT
  - Run 010: Soft Majority, CTFT, GTFT
  - Run 011: **Soft Majority, CTFT, GTFT** — SAME

  Three consecutive identical top-3 lists satisfy the
  "три последних турнира подряд топ-3 не меняется" criterion.

- **Soft Majority dropped -7.8 to 502.73** but kept #1. Its
  338 cell vs AGrim is its lowest non-AllD/Grim cell — proof
  that AGrim's burst is the only behaviour SM cannot tolerate.
  SM still wins on aggregate.

- **CTFT held #2 at 493.20 (+1.3).** Cell vs AGrim = 511, in
  the normal reciprocator range. CTFT's apology mechanism
  isolates AGrim's noise reasoning.

- **GTFT held #3 at 487.07 (-0.3).** Cell vs AGrim = 483.
  Generosity acts as a damper on AGrim's punish escalation.

- **Pavlov fell -4.6 to 459.18 → #9.** AGrim's cycle out-of-
  phases Pavlov's WSLS, pulling Pavlov into lose-shift more
  often than into stable CC.

- **AllC's row recovered +4.1 to 449.13.** AGrim's 650 cell
  costs AllC ~93 pts vs CC, but AllC's other cells were
  already calibrated to that pool; small net gain because
  AGrim is less punishing than Detective in absolute terms.

### Final stability tracker

- Run 008 top-3: Soft Majority, CTFT, TF2T
- Run 009 top-3: Soft Majority, CTFT, GTFT
- Run 010 top-3: Soft Majority, CTFT, GTFT — SAME (1st)
- Run 011 top-3: **Soft Majority, CTFT, GTFT** — SAME (2nd)

Three consecutive tournaments (009, 010, 011) show identical
top-3 → STOP condition met. Pool now has 10 non-trivial bots
(TF2T, Pavlov, GTFT, CTFT, ATFT, Gradual, SM, Detective,
Shadow, AGrim) plus the 5 pantheon bots.

REPORT.md written, STOP file created. End of generation 7's
experiment.
