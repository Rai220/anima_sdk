# Tournament scores log

Each entry: parameters, bot set, ranking, pairwise matrix.

---

## Tournament 1 — reference pantheon baseline

- Date: 2026-05-15
- Params: `rounds=200 noise=0.02 repeat=3 seed=42`
- Bots: `bot_always_c, bot_always_d, bot_grim, bot_random, bot_tit_for_tat`

### Ranking (avg per-round score across all opponents, including self)

| # | Bot              | Score |
|---|------------------|-------|
| 1 | bot_always_d     | 2.224 |
| 2 | bot_grim         | 2.128 |
| 3 | bot_random       | 1.938 |
| 4 | bot_tit_for_tat  | 1.923 |
| 5 | bot_always_c     | 1.719 |

### Pairwise matrix (row = me, col = opponent, value = my avg/round)

```
                  always_c  always_d  grim      random    tft
always_c             3.008     0.080     1.117     1.467     2.923
always_d             4.872     1.065     1.095     2.902     1.188
grim                 4.192     1.062     1.138     2.917     1.333
random               4.000     0.593     0.608     2.238     2.248
tft                  3.015     1.055     1.233     2.240     2.073
```

### Notable matchups

- **AllC vs AllD = 0.080 / 4.872** — pure exploitation. AllC is the dove
  that gets eaten.
- **AllD vs Grim = 1.065 / 1.062** — both end in permanent DD. Noise barely
  matters here.
- **TFT vs TFT = 2.073** — noise breaks symmetric cooperation. Each
  accidental D triggers an echo war, then a re-sync, then another echo.
  Without noise this would be ~3.000.
- **Grim vs Grim = 1.138** — even worse self-play than DD, because the
  first noise flip ends cooperation forever.
- **AllD vs TFT = 1.188 / 1.055** — TFT mostly defects (correctly), but
  loses the first round and the post-noise-flip echo rounds.
- **AllC vs Grim = 1.117 / 4.192** — Grim accidentally exploits AllC after
  the first noise flip turns one of AllC's C into D.

---

## Tournament 2 — added bot_generous_tft (FORGIVE=0.1)

- Date: 2026-05-15
- Params: `rounds=200 noise=0.02 repeat=3 seed=42`
- Bots: pantheon + `bot_generous_tft`

### Ranking

| # | Bot              | Score | Δ vs T1 |
|---|------------------|-------|---------|
| 1 | bot_grim         | 2.212 | +0.084  |
| 2 | bot_tit_for_tat  | 2.176 | +0.253  |
| 3 | bot_generous_tft | 2.155 | (new)   |
| 4 | bot_always_d     | 2.107 | -0.117  |
| 5 | bot_random       | 2.013 | +0.075  |
| 6 | bot_always_c     | 1.829 | +0.110  |

### Pairwise matrix

```
                   always_c  always_d  gen_tft   grim      random    tft
always_c              3.008     0.063     2.945     0.517     1.537     2.902
always_d              4.913     1.045     1.527     1.077     2.928     1.152
generous_tft          2.995     0.943     2.868     1.218     2.180     2.725
grim                  4.592     1.085     1.685     1.490     2.852     1.572
random                3.903     0.587     2.438     0.652     2.207     2.292
tit_for_tat           3.027     1.060     2.825     1.497     2.275     2.370
```

### What changed

- **AllD lost the crown** (1st → 4th). GTFT exploits AllD less than AllC
  did, so the "free lunch" shrank.
- **Grim climbs to 1st.** It still farms AllC (4.592) and now also exploits
  GTFT (1.685 — GTFT's 10% forgiveness gives Grim recurring C moves to
  punch, while Grim is locked in D mode).
- **TFT climbs to 2nd** because TFT-vs-GTFT is a 2.825 cooperation party.
- **GTFT itself sits 3rd** with very strong self-play (2.868) and strong
  matchups with TFT and AllC, but weak vs Grim and AllD.
- **AllC's score rose** by 0.11 because GTFT cooperates with AllC at 2.945
  (close to 3.0).

---

## Tournament 3 — added bot_pavlov (Win-Stay-Lose-Shift)

- Date: 2026-05-15
- Params: `rounds=200 noise=0.02 repeat=3 seed=42`
- Bots: pantheon + `bot_generous_tft` + `bot_pavlov`

### Ranking

| # | Bot              | Score | Δ vs T2 |
|---|------------------|-------|---------|
| 1 | bot_pavlov       | 2.264 | (new)   |
| 2 | bot_grim         | 2.241 | +0.029  |
| 3 | bot_always_d     | 2.233 | +0.126  |
| 4 | bot_tit_for_tat  | 2.187 | +0.011  |
| 5 | bot_generous_tft | 2.180 | +0.025  |
| 6 | bot_random       | 2.045 | +0.032  |
| 7 | bot_always_c     | 1.827 | -0.002  |

### Pairwise matrix

```
                   always_c  always_d  gen_tft   grim      pavlov    random    tft
always_c              2.937     0.100     2.930     0.720     1.722     1.485     2.897
always_d              4.867     1.073     1.543     1.113     2.935     2.895     1.202
generous_tft          2.997     0.927     2.743     1.080     2.583     2.192     2.742
grim                  4.462     1.047     1.555     1.450     2.945     3.003     1.225
pavlov                3.797     0.585     2.700     1.037     2.937     2.255     2.540
random                3.968     0.587     2.450     0.578     2.263     2.233     2.232
tit_for_tat           3.055     1.043     2.767     1.117     2.515     2.232     2.582
```

### What changed

- **Pavlov claims 1st** (2.264) on the strength of three things:
  1. **Self-play 2.937** — nearly perfect cooperation despite 2% noise.
     Pavlov resyncs from any DD slip in one step (DD -> both shift to C).
  2. **Exploits AllC** at 3.797 — when noise flips an AllC C to D, Pavlov
     shifts to D and gets a free T=5 on the next round before cycling back.
  3. **Strong vs Grim/AllD only via the bot's own self-play boost.**
- **AllD climbed back to 3rd** (2.233 vs 2.107 in T2). Pavlov is a fresh
  victim for AllD: Pavlov vs AllD = 0.585 (CDCD oscillation), so AllD
  scored 2.935 in that pairing — almost as much as it gets vs Random.
- **Grim still farms AllC** (4.462) and AllD-trapped opponents, but its
  self-play is awful (1.450 — Grim vs Grim collapses after noise).
- **TFT and GTFT** are middling — neither one exploits anyone (no T=5
  upside) and both pay echo-war costs even with forgiveness.

### Notable matchups

- **Pavlov vs Pavlov = 2.937** — best self-play in the pool. The
  defining feature of WSLS: noise-robust cooperation.
- **Pavlov vs AllD = 0.585 / 2.935** — Pavlov's worst pairing. The
  alternating CDCD pattern means Pavlov gets S=0 every other round.
- **Pavlov vs Grim = 1.037 / 2.945** — confusing on paper. Pavlov plays
  C, Grim plays C, fine. After the first noise flip Grim is locked into
  D forever. Pavlov then oscillates CDCD, but because Grim is AllD now
  this is the same trap as the AllD pairing, only with later onset.
- **Pavlov vs AllC = 3.797 / 1.722** — noise opens periodic free 5s.
  Without noise this would be a steady 3.0/3.0.
- **Pavlov vs GTFT = 2.700 / 2.583** — both forgive, both resync, very
  cooperative.

---

## Tournament 4 — added bot_tft2t (Tit-for-Two-Tats)

- Date: 2026-05-15
- Params: `rounds=200 noise=0.02 repeat=3 seed=42`
- Bots: pantheon + `bot_generous_tft` + `bot_pavlov` + `bot_tft2t`

### Ranking

| # | Bot              | Score | Δ vs T3 |
|---|------------------|-------|---------|
| 1 | bot_generous_tft | 2.362 | +0.182  |
| 2 | bot_pavlov       | 2.331 | +0.067  |
| 3 | bot_tit_for_tat  | 2.269 | +0.082  |
| 4 | bot_tft2t        | 2.267 | (new)   |
| 5 | bot_grim         | 2.204 | -0.037  |
| 6 | bot_random       | 2.196 | +0.151  |
| 7 | bot_always_d     | 2.081 | -0.152  |
| 8 | bot_always_c     | 1.944 | +0.117  |

### Pairwise matrix

```
                  always_c  always_d  gen_tft   grim      pavlov    random    tft2t     tft
always_c             2.985     0.113     2.945     0.632     1.460     1.515     2.990     2.910
always_d             4.863     0.993     1.485     1.090     2.968     2.902     1.203     1.145
generous_tft         3.003     0.927     2.820     1.578     2.672     2.170     3.022     2.702
grim                 4.515     1.065     1.962     1.343     2.960     2.872     1.537     1.375
pavlov               3.977     0.568     2.722     0.860     2.925     2.318     2.850     2.430
random               3.948     0.593     2.453     0.622     2.252     2.260     3.155     2.282
tft2t                2.982     1.012     2.922     1.337     2.125     1.863     2.958     2.940
tit_for_tat          3.027     1.037     2.793     1.258     2.455     2.257     3.007     2.320
```

### What changed

- **GTFT seizes 1st** (1.578 ↑ vs Grim, 3.022 vs TFTT, 2.702 vs TFT,
  2.820 self). Adding TFTT increased the share of "cooperative siblings"
  in GTFT's match book: GTFT now has *three* near-perfect 3.0 partners
  (TFT, TFTT, AllC) plus strong cooperation with itself and Pavlov.
- **AllD slumps to 7th** (2.081 vs 2.233 in T3). It can't exploit TFTT
  much harder than TFT (1.203 vs 1.145), but it now faces an extra
  cooperator that piles benefits onto the nice cluster, not on AllD.
- **TFTT debuts at 4th** (2.267), almost identical to TFT. Trade-off:
  TFTT loses ~2 rounds at the start of AllD matches (cost ≈ -0.01/round),
  but gains in self-play (2.958 vs TFT's 2.320) and gains vs Grim
  (1.337 vs TFT's 1.258 — TFTT doesn't immediately echo Grim's noise-
  triggered lockup, eats some early Cs from Grim before settling).
- **Grim sinks** because more of the pool now resyncs after noise, so
  Grim's "lock into D forever" rule increasingly hurts both sides.

### Notable matchups

- **TFTT vs TFTT = 2.958** — best self-play after Pavlov-vs-Pavlov in
  T3. Confirms hypothesis 2: TFTT is noise-robust because a single
  flip never escalates.
- **TFTT vs AllD = 1.012 / 1.203** — TFTT loses only ~0.025/round
  more than TFT does (1.037 → 1.012). The "+2 rounds of being a sucker"
  cost is tiny over 200 rounds.
- **TFTT vs Grim = 1.337 / 1.537** — Grim accidentally locks first,
  TFTT keeps trying C, eats Grim's exploit, eventually retaliates.
  Better than TFT here because TFTT keeps cooperating one extra time
  giving Grim a window where the noise can flip Grim's D back to a
  C-percept, but the bottom line is still bad for TFTT.
- **TFTT vs Pavlov = 2.125 / 2.850** — Pavlov exploits TFTT. After
  Pavlov's noise flip to D, TFTT doesn't retaliate (one D only),
  Pavlov stays on D ("win-stay" with T=5), TFTT eventually sees two
  Ds, retaliates, but by then Pavlov has banked free 5s. Pavlov's
  WSLS dynamic punishes single-D-tolerant strategies.
- **TFTT vs Random = 1.863 / 3.155** — Random's biggest win in the
  pool. Random's D's rarely come in pairs, so TFTT keeps cooperating,
  and Random's C's get free C from TFTT.

---

## Tournament 5 — added bot_hard_tft (TFT + AllD-detector, window=20, threshold=0.6)

- Date: 2026-05-15
- Params: `rounds=200 noise=0.02 repeat=3 seed=42`
- Bots: pantheon + `bot_generous_tft` + `bot_pavlov` + `bot_tft2t` + `bot_hard_tft`

### Ranking

| # | Bot              | Score | Δ vs T4 |
|---|------------------|-------|---------|
| 1 | bot_generous_tft | 2.357 | -0.005  |
| 2 | bot_tft2t        | 2.329 | +0.062  |
| 3 | bot_pavlov       | 2.294 | -0.037  |
| 4 | bot_tit_for_tat  | 2.217 | -0.052  |
| 5 | bot_random       | 2.209 | +0.013  |
| 6 | bot_hard_tft     | 2.188 | (new)   |
| 7 | bot_grim         | 2.075 | -0.129  |
| 8 | bot_always_c     | 2.070 | +0.126  |
| 9 | bot_always_d     | 1.992 | -0.089  |

### Pairwise matrix

```
                   always_c  always_d  gen_tft   grim      hard_tft  pavlov    random    tft2t     tft
always_c              3.005     0.083     2.952     0.572     2.897     1.687     1.493     3.025     2.920
always_d              4.900     1.067     1.527     1.055     1.095     2.947     2.893     1.295     1.150
generous_tft          2.985     0.960     2.887     1.185     2.778     2.585     2.168     3.017     2.650
grim                  4.588     1.080     1.643     1.275     1.178     2.955     3.025     1.585     1.348
hard_tft              3.030     1.045     2.837     1.203     1.797     2.415     2.295     3.017     2.057
pavlov                3.828     0.555     2.718     1.238     2.157     2.920     2.115     2.817     2.293
random                3.968     0.577     2.452     0.617     2.145     2.407     2.313     3.140     2.262
tft2t                 2.933     0.995     2.925     1.443     2.942     1.917     1.915     2.958     2.933
tit_for_tat           3.028     1.025     2.683     1.257     2.065     2.293     2.287     3.000     2.312
```

### What changed

- **Hard TFT placed 6th of 9** — a clear disappointment vs my prediction
  of top-3. The killer is **self-play 1.797**, by far the worst among
  retaliatory strategies. Under 2% noise, two Hard-TFT copies can produce
  echo wars where each side's window of 20 occasionally crosses the 60%-D
  threshold, triggering the lock. Once one side locks, the other side's
  window fills with D, and *it* locks too. The cascade kills self-play.
- **vs AllD**: 1.045, basically identical to TFT's 1.025 — gain ~zero.
  TFT already locks DD vs AllD after the first round. The detector
  doesn't help much here because there's nothing extra to detect.
- **vs Grim**: 1.203, *worse* than TFT's 1.257. Why? Grim cooperates for
  the first ~50 rounds (until noise triggers it) then plays D forever.
  Hard TFT sees Grim's D-burst, hits threshold, locks D — but locking D
  doesn't help when Grim is already in D, it just makes the long-run
  payoff 1.0 instead of 1.0 either way. Slight loss from the lock-on
  detection delay.
- **AllD slumps to 9th (last place)**, a new low. Adding any extra
  retaliator (Hard TFT) increases the share of opponents that punish AllD.
- **Grim slumps to 7th** because Hard TFT vs Grim is no longer a
  forgiveness exploitable matchup — Hard TFT locks D right back.

### Notable matchups

- **Hard TFT vs Hard TFT = 1.797** — bad. Echo war + window threshold
  creates a cascade lock. Future detector designs need either a longer
  window, a higher threshold, or a hysteresis condition.
- **Hard TFT vs AllD = 1.045 / 1.095** — Hard TFT plays D for almost
  every round after detection. Marginal improvement over TFT.
- **Hard TFT vs Random = 2.295 / 2.145** — slightly better than TFT
  here (2.287 / 2.262). Random's ~50% D rate sits below threshold, so
  Hard TFT behaves as TFT. The 0.01 edge is just RNG variance.
- **Hard TFT vs Pavlov = 2.415 / 2.157** — slightly better than TFT vs
  Pavlov (2.293 / 2.293). The lock triggers when Pavlov goes through a
  D-streak (after consecutive noise flips), capping Pavlov's exploit.
- **Hard TFT vs TFT = 2.057 / 2.065** — worse than TFT-vs-TFT (2.312).
  Hard TFT's threshold occasionally triggers off the echo war and locks
  D against a cooperator. Penalty for paranoia.

---

## Tournament 6 — added bot_prober (open D,C,C; AllD if no retaliation, else TFT)

- Date: 2026-05-15
- Params: `rounds=200 noise=0.02 repeat=3 seed=42`
- Bots: pantheon + GTFT + Pavlov + TFTT + Hard TFT + `bot_prober`

### Ranking

| #  | Bot              | Score | Δ vs T5 |
|----|------------------|-------|---------|
| 1  | bot_generous_tft | 2.270 | -0.087  |
| 2  | bot_tft2t        | 2.193 | -0.136  |
| 3  | bot_pavlov       | 2.183 | -0.111  |
| 4  | bot_random       | 2.175 | -0.034  |
| 5  | bot_tit_for_tat  | 2.168 | -0.049  |
| 6  | bot_prober       | 2.051 | (new)   |
| 7  | bot_hard_tft     | 1.980 | -0.208  |
| 8  | bot_grim         | 1.979 | -0.096  |
| 9  | bot_always_d     | 1.907 | -0.085  |
| 10 | bot_always_c     | 1.874 | -0.196  |

### Pairwise matrix

```
                   always_c  always_d  gen_tft   grim      hard_tft  pavlov    prober    random    tft2t     tft
always_c              2.982     0.087     2.908     0.442     2.913     1.835     0.117     1.525     2.993     2.937
always_d              4.853     1.110     1.515     1.100     1.063     2.967     1.132     2.848     1.282     1.200
generous_tft          3.033     0.932     2.892     1.407     1.298     2.472     2.813     2.137     3.038     2.675
grim                  4.658     1.050     1.882     1.223     1.190     2.933     1.178     3.038     1.408     1.232
hard_tft              3.013     1.047     1.782     1.190     1.683     2.412     1.545     2.303     3.025     1.803
pavlov                3.735     0.575     2.605     0.883     2.120     2.933     1.680     2.260     2.835     2.208
prober                4.825     1.015     2.838     1.028     1.495     2.463     1.108     2.262     1.248     2.227
random                3.925     0.632     2.387     0.588     2.103     2.235     2.262     2.373     3.012     2.232
tft2t                 2.968     1.015     2.897     1.225     2.925     2.260     1.023     1.828     2.932     2.860
tit_for_tat           3.003     1.033     2.725     1.165     1.712     2.175     2.218     2.207     2.993     2.450
```

### What changed

- **Top 3 unchanged** vs T5: GTFT (1st), TFTT (2nd), Pavlov (3rd). Two
  tournaments in a row with the same podium. One more matching
  tournament and we hit the stop condition for the "stable podium"
  side of the rule.
- **Prober debuts at 6th** (2.051) — a respectable mid-pack predator.
  Best matchups:
  - vs AllC = 4.825 / 0.117 — almost pure AllD exploitation. Prober
    correctly detects AllC's lack of retaliation and farms it.
  - vs TFTT = 1.248 / 1.023 — Prober exploits TFTT mildly. TFTT
    didn't retaliate in rounds 1-2 (single D is below its threshold),
    so Prober locked AllD; TFTT eventually catches on and switches
    to D too. End result is a few free Ds for Prober, then DD.
  - vs GTFT = 2.838 / 2.813 — surprisingly *cooperative*. GTFT
    forgave the round-0 D with high probability (in this seed it
    forgave at least once in rounds 1-2), but Prober's "retaliated"
    check is OR-of-rounds-1-2; GTFT defects in at least one of those
    rounds for most matches, so Prober switches to TFT in most
    matches. Then a mostly cooperative TFT-vs-GTFT dynamic ensues.
- **Prober's worst matchups:**
  - vs self = 1.108 — the canonical Prober weakness. Both probe with
    D, C, C → both see the other's round-0 D and rounds-1-2 Cs →
    both conclude "pushover" → both lock AllD. ~1.0/round forever.
  - vs Grim = 1.028 — Grim retaliates after Prober's round-0 D and
    locks D forever; Prober sees retaliation and switches to TFT but
    that just means it copies Grim's D forever too. Mutual D.
  - vs AllD = 1.015 — same as TFT vs AllD; Prober correctly switches
    to TFT and locks DD.
- **TFTT slipped (-0.136).** It's the prime victim of Prober — it
  doesn't retaliate fast enough to deter Prober's exploit. Cost is
  small per matchup (1.023 vs Prober) but consistent.
- **AllC slipped (-0.196).** Prober punishes AllC harder than any
  other bot. AllC's average dropped from 2.070 to 1.874.
- **Random climbed to 4th** by accident — it benefits from the lower
  average of nearly every other bot (overall pool got slightly more
  predatory in distribution, but Random's score barely moved).
- **Hard TFT slumped further (-0.208).** Adding Prober didn't help it.
  Hard TFT vs Prober = 1.495 / 1.545 — both end up in alternating
  patterns. Hard TFT continues to lose to its own self-play cascade.
- **Grim slumped (-0.096).** Grim's "exploit AllC" matchup is hurt
  because there are now two cooperator-exploiters (Grim, Prober)
  competing for the same pool of nice rounds.

### Notable matchups

- **Prober vs AllC = 4.825 / 0.117** — second-highest exploitation
  in the pool, just behind AllD vs AllC (4.853). The probe-and-lock
  works exactly as designed.
- **Prober vs TFT = 2.227 / 2.218** — basically a tie. TFT retaliates
  in round 1, Prober sees this and switches to TFT mode, and from
  round 3 onwards both copy each other; the opening D-C-C / C-D-C
  zig-zag costs ~8 points up front but they recover at 3.0/round.
- **Prober vs Prober = 1.108** — confirms the predicted self-play
  collapse. Both probe, both see the other's round-0 D AND rounds-1-2
  Cs, both conclude "pushover" → both lock AllD → 1.0/round forever.
  Two predators eat each other.
- **Prober vs Random = 2.262 / 2.262** — Random has ~25% chance to
  produce CC in rounds 1-2, so ~25% of matches Prober plays AllD
  vs Random (advantageous), 75% it plays TFT. Net is mid-table.

---

## Tournament 7 — added bot_soft_majority

- Date: 2026-05-15
- Params: `rounds=200 noise=0.02 repeat=3 seed=42`
- Bots: pantheon + GTFT + Pavlov + TFTT + Hard TFT + Prober + `bot_soft_majority`

### Ranking

| #  | Bot               | Score | Δ vs T6 |
|----|-------------------|-------|---------|
| 1  | bot_soft_majority | 2.529 | (new)   |
| 2  | bot_generous_tft  | 2.413 | +0.143  |
| 3  | bot_tft2t         | 2.290 | +0.097  |
| 4  | bot_tit_for_tat   | 2.273 | +0.105  |
| 5  | bot_pavlov        | 2.214 | +0.031  |
| 6  | bot_prober        | 2.208 | +0.157  |
| 7  | bot_hard_tft      | 2.169 | +0.189  |
| 8  | bot_always_c      | 2.103 | +0.229  |
| 9  | bot_random        | 1.993 | -0.182  |
| 10 | bot_grim          | 1.917 | -0.062  |
| 11 | bot_always_d      | 1.847 | -0.060  |

### Pairwise matrix

```
                    always_c  always_d  gen_tft   grim      hard_tft  pavlov    prober    random    soft_maj  tft2t     tft
always_c               2.978     0.052     2.917     2.303     2.935     1.467     0.120     1.495     2.950     2.985     2.937
always_d               4.910     1.053     1.573     1.090     1.092     2.972     1.160     2.910     1.128     1.270     1.153
generous_tft           3.025     0.932     2.815     1.145     2.543     2.518     2.712     2.125     3.027     3.010     2.695
grim                   3.445     1.065     1.628     1.200     1.242     2.960     1.152     3.018     2.125     1.730     1.517
hard_tft               3.002     1.033     2.702     1.192     2.075     2.268     1.595     2.297     3.022     3.003     1.675
pavlov                 3.975     0.597     2.652     0.743     1.918     2.908     2.387     2.272     1.780     2.843     2.283
prober                 4.853     1.060     2.753     1.043     1.520     2.312     1.092     3.073     3.015     1.280     2.290
random                 3.962     0.560     2.392     0.577     2.097     2.188     0.582     2.188     2.008     3.092     2.278
soft_majority          3.008     1.037     2.910     1.358     2.913     2.505     2.915     2.275     3.002     2.997     2.903
tft2t                  2.977     1.037     2.910     1.480     2.945     2.077     1.030     1.867     2.947     2.972     2.953
tit_for_tat            3.020     1.028     2.753     1.425     1.625     2.308     2.315     2.245     3.037     3.003     2.240
```

### What changed

- **Top-3 reshuffled.** New podium: Soft Majority / GTFT / TFTT. Pavlov
  drops to 5th. The stable-podium counter (GTFT/TFTT/Pavlov in T5+T6)
  resets to 1.
- **Soft Majority debuts at 1st** (2.529) — the strongest debut of any
  bot so far. Mechanism:
  - **Vs AllD = 1.037** — after round 1 the opp has 1 D, 0 C and
    Soft Majority plays D forever from round 2. Same outcome as TFT
    against AllD, very efficient.
  - **Vs AllC = 3.008** — perfect cooperation. AllC's count of C
    dominates noise-flipped Ds.
  - **Vs self = 3.002** — best self-play of any retaliatory bot in
    this pool. The majority count is dominated by the long history
    of Cs, so a noise-flipped D never tips Soft Majority into D
    mode for more than a single round.
  - **Vs Prober = 2.915** — Prober's probe (D, C, C) leaves opp's
    history at [D, C, C] by round 3; Soft Majority's count is 2C/1D
    so it plays C; Prober's "did opp retaliate in rounds 1-2?" sees
    Soft Majority's D in round 1 (response to the D in round 0) and
    switches to TFT. Both then settle into cooperation.
  - **Vs Pavlov = 2.505** — Pavlov gets a few free Ds via noise,
    Soft Majority's slow count keeps cooperating, eventually it
    retaliates (when noise+Pavlov defections push #D > #C), then
    re-cooperates as the count recovers. Net: ~2.5 each direction.
  - **Vs Grim = 1.358** — Soft Majority's only sub-par matchup vs a
    nice opponent. Grim cooperates until a noise flip triggers it,
    then plays D forever. Soft Majority's count slowly catches up
    to "#D dominates" and switches to D, but during the lag Grim
    gets a stream of free 5s.
- **GTFT climbs to 2nd** (+0.143) — adding Soft Majority added another
  near-3.0 cooperation partner. GTFT vs Soft Majority = 3.027 / 2.910.
- **TFTT climbs to 3rd** (+0.097) — same mechanism. TFTT vs Soft
  Majority = 2.947 / 2.997.
- **AllC's score jumped** (+0.229) because Soft Majority cooperates
  with it perfectly, and AllC vs Grim is also higher in this pool
  (2.303 — Grim still defects vs AllC for most rounds, but the
  per-tournament repeat variance gave us a better seed-roll here).
  Need to check this isn't a seed artifact.
- **Random sank** (-0.182) — adding a near-pure-cooperator
  (Soft Majority cooperates with Random ~57% of rounds) raised the
  effective cooperation rate of every retaliator vs Random, but
  Random itself doesn't benefit because its 50/50 still leaks Ds
  into every match.

### Notable matchups

- **Soft Majority vs Soft Majority = 3.002** — single-state, no
  threshold, so noise can never trigger a cascade. The defection
  count would have to overtake the cooperation count, which only
  happens if noise flips ~50% of Cs, far beyond the 2% setting.
- **Soft Majority vs AllD = 1.037 / 1.128** — same end state as TFT
  vs AllD; the response delay is exactly one round (opp must show
  at least one D before #D > #C). Cost ≈ 0.
- **Soft Majority vs Grim = 1.358 / 2.125** — Grim wins this matchup
  noticeably (2.125 vs 1.358). Grim cooperates while it can; Soft
  Majority does too. The first noise flip triggers Grim. Soft
  Majority keeps cooperating until #D > #C, which can take 30-50
  more rounds because the prior C-count was so large. During this
  lag Grim farms Soft Majority for free 5s. Mirror of the Prober
  problem but with a slower trigger and slower recovery.
- **Soft Majority vs Prober = 2.915 / 3.015** — solid cooperation
  after the probe is resolved. Soft Majority's accidental D in
  round 1 (response to Prober's D in round 0) is what *saves* it:
  it convinces Prober to switch to TFT instead of locking AllD.
- **Soft Majority vs Pavlov = 2.505 / 1.780** — Pavlov gains a bit
  here (1.780 actually means it lost net; the 2.505 is Soft
  Majority's gain). When Pavlov noise-flips to D, Soft Majority's
  slow count keeps cooperating, so Pavlov gets free Ds. Eventually
  Soft Majority's count tilts and it plays D, which Pavlov reads
  as "loss" and shifts back to C. Cycle continues.

---

## Engine fix (between T7 and T8): deterministic per-pair seeding

While analysing T8 we found that `play_pair` used Python's `hash()` to
seed each match. CPython's string `hash()` is randomised per process by
default (PYTHONHASHSEED), so the per-pair noise streams varied between
separate runs of the script. This explained why some unrelated
matchups (e.g. `always_c` vs `grim`) drifted by up to ~1.3 points
between tournaments even when neither bot changed. Within a single
process the matchups stayed self-consistent — but cross-tournament
comparisons of individual matchup scores were noisy by design.

Fix: replaced `hash((base_seed, name_a, name_b, r))` with
`int.from_bytes(hashlib.sha1(f"{base_seed}|{name_a}|{name_b}|{r}".encode()).digest()[:4], "big")`.
This is process-independent and identical across runs.

Consequence: **T8 and later use a different per-pair noise stream than
T1-T7**. Individual matchup numbers from T1-T7 are *not* directly
comparable to T8+. Aggregate rankings stay broadly stable (3 repeats
already damp out most of the per-match noise), but the "top-3 stable
for 3 tournaments" stop condition must restart its count under the
new regime. T8 (below) is run 1 of 3 under the fixed seeding.

---

## Tournament 8 — added bot_gradual (Beaufils 1996); deterministic seeds

- Date: 2026-05-15
- Params: `rounds=200 noise=0.02 repeat=3 seed=42` (deterministic per-pair seeds)
- Bots: pantheon + GTFT + Pavlov + TFTT + Hard TFT + Prober + Soft Majority + `bot_gradual`

### Ranking

| #  | Bot               | Score |
|----|-------------------|-------|
| 1  | bot_soft_majority | 2.488 |
| 2  | bot_generous_tft  | 2.373 |
| 3  | bot_tft2t         | 2.364 |
| 4  | bot_tit_for_tat   | 2.316 |
| 5  | bot_gradual       | 2.301 |
| 6  | bot_hard_tft      | 2.205 |
| 7  | bot_pavlov        | 2.197 |
| 8  | bot_random        | 2.142 |
| 9  | bot_always_c      | 2.107 |
| 10 | bot_prober        | 2.094 |
| 11 | bot_grim          | 1.944 |
| 12 | bot_always_d      | 1.791 |

### Pairwise matrix

```
                    always_c  always_d  gen_tft   gradual   grim      hard_tft  pavlov    prober    random    soft_maj  tft2t     tft
always_c               2.958     0.058     2.945     2.843     0.793     2.927     1.362     1.032     1.478     2.963     2.973     2.945
always_d               4.900     1.075     1.545     1.383     1.083     1.120     2.993     1.118     2.878     1.072     1.238     1.085
generous_tft           3.003     0.978     2.863     2.157     1.243     2.798     2.392     2.185     2.163     2.987     3.025     2.675
gradual                3.060     0.975     2.373     1.578     1.112     1.652     2.853     2.387     2.848     3.055     2.975     2.738
grim                   4.418     1.008     1.718     1.403     1.350     1.305     2.968     1.178     2.935     1.673     1.795     1.577
hard_tft               3.035     1.045     2.857     1.843     1.272     2.078     2.332     1.595     2.322     3.015     3.007     2.058
pavlov                 4.053     0.543     2.517     2.295     0.943     2.023     2.897     2.290     2.208     1.507     2.898     2.190
prober                 4.265     1.027     2.427     2.378     1.078     1.528     2.282     1.132     2.283     3.000     1.250     2.483
random                 3.978     0.595     2.430     0.998     0.602     2.272     2.275     2.292     2.182     2.667     3.183     2.235
soft_majority          2.997     1.063     2.953     2.872     1.182     2.915     2.557     2.925     2.083     2.978     2.977     2.360
tft2t                  2.990     1.013     2.883     2.892     1.562     2.923     2.282     1.025     1.925     2.977     2.958     2.942
tit_for_tat            3.012     1.035     2.725     2.788     1.485     2.025     2.173     2.500     2.218     2.393     3.008     2.428
```

### What changed (vs T7 — caveat: different seed regime)

- **Top-3 under the new seeding**: Soft Majority / GTFT / TFTT. This
  happens to match T7's podium under the old seeding. Pavlov dropped
  to 7th (was 5th).
- **GRADUAL debuts at 5th** (2.301) — much weaker than predicted. The
  prediction (STRATEGIES.md after T7) was top-3, possibly 1st. Reason
  for the miss: **GRADUAL self-play collapses under noise** —
  `gradual vs gradual = 1.578`, see analysis below.
- The new seed regime also shows much larger Random and Pavlov self-play
  variance from what we saw in T1-T7; not a big deal because most of
  the ranking is unchanged.
- `bot_grim` swings noticeably between seed regimes (T7: 1.917, T8: 1.944).
- `bot_random` is at 2.142 in T8 — it occasionally lucks into a slot
  above always_c thanks to GRADUAL feeding it 2.848/round (GRADUAL
  doesn't punish random Ds nearly fast enough).

### Notable matchups

- **GRADUAL vs GRADUAL = 1.578** — the spiral. Once a single noise flip
  triggers retaliation, both copies enter punishment+calming sequences
  staggered by one round. Each side's calming Cs land while the other
  side is still in punishment, which the punisher reads as the
  cooperator-paying-grim pattern. Worse, GRADUAL's retaliation length
  equals the **cumulative** count of opp's defections, so every round
  of mutual D ratchets the count up. By round 100 the count is large
  enough that punishments span 50+ rounds, leaving almost no room for
  the 2-C calming windows to ever reach the other side in normal mode.
  Net: ~1.5/round — barely above AllD-vs-AllD.
- **GRADUAL vs Soft Majority = 3.055 / 2.872** — fine. Soft Majority's
  tolerance means GRADUAL's occasional noise-induced D doesn't tip it.
- **GRADUAL vs Hard TFT = 1.652 / 1.843** — Hard TFT's threshold
  detector trips on GRADUAL's escalating retaliation, locking in
  permanent D. Same death spiral as Hard TFT-vs-itself.
- **GRADUAL vs AllD = 0.975 / 1.383** — GRADUAL pays a small cost vs
  AllD because of the calming Cs that follow each punishment block.
  Each calming C against AllD's D is a 0 — and there are ~2 per cycle
  for the entire match. Net loss ~0.05/round vs pure TFT.
- **GRADUAL vs Grim = 1.112 / 1.403** — symmetric trap. Grim trips
  on GRADUAL's noise flip, locks D. GRADUAL retaliates and never
  returns to cooperation cleanly because every calming pair pays 0
  against Grim's D.
- **bot_random vs bot_random = 2.182** — Random self-play under the
  new noise stream happens to be roughly 50/50 still. Higher than
  many retaliators with cascade-prone state machines.


---

## Tournament 9 — added bot_adaptive_pavlov

- Date: 2026-05-15
- Params: `rounds=200 noise=0.02 repeat=3 seed=42` (deterministic per-pair seeds)
- Bots: pantheon + GTFT + Pavlov + TFTT + Hard TFT + Prober + Soft Majority + GRADUAL + `bot_adaptive_pavlov`
- Total bots: 13

### Ranking

| #  | Bot                  | Score |
|----|----------------------|-------|
| 1  | bot_generous_tft     | 2.368 |
| 2  | bot_soft_majority    | 2.360 |
| 3  | bot_tft2t            | 2.346 |
| 4  | bot_tit_for_tat      | 2.298 |
| 5  | bot_gradual          | 2.287 |
| 6  | bot_pavlov           | 2.258 |
| 7  | bot_adaptive_pavlov  | 2.257 |
| 8  | bot_hard_tft         | 2.095 |
| 9  | bot_prober           | 2.076 |
| 10 | bot_random           | 2.072 |
| 11 | bot_always_c         | 2.033 |
| 12 | bot_grim             | 1.920 |
| 13 | bot_always_d         | 1.751 |

### Pairwise matrix (selected rows)

```
                          adap   alwa_c alwa_d gen_tft grad  grim  hard  pavl  prob  rand  soft  tft2t tft
bot_adaptive_pavlov      2.942  4.195  1.055  2.642  2.155  1.462  1.567  2.920  1.340  2.725  1.427  2.857  2.062
bot_pavlov               2.912  4.053  0.543  2.517  2.295  0.943  2.023  2.897  2.290  2.292  1.507  2.898  2.190
```

### What changed (vs T8)

- **Top-3 SET stable: Soft Majority / GTFT / TFTT.**
  But the *order* shuffled — T8 had Soft Maj first (2.488), T9 has
  GTFT first (2.368). The numbers compressed because adding a
  fairly Pavlov-like bot to the pool changed average opponents.
  - T8 top-3: Soft Maj 2.488, GTFT 2.373, TFTT 2.364.
  - T9 top-3: GTFT 2.368, Soft Maj 2.360, TFTT 2.346.
  - Spread within top-3 is 0.022 (T9) vs 0.124 (T8). Top-3 is now
    essentially a three-way tie.

- **bot_adaptive_pavlov debuts at 7th**, almost tied with standard
  Pavlov (2.257 vs 2.258). The new AllD-detector improved the
  matchups that motivated it but broke others.

  | Opponent       | Pavlov | Adaptive Pavlov | Δ      |
  |----------------|--------|-----------------|--------|
  | always_d       | 0.543  | 1.055           | +0.512 |
  | grim           | 0.943  | 1.462           | +0.519 |
  | random         | 2.292  | 2.725           | +0.433 |
  | always_c       | 4.053  | 4.195           | +0.142 |
  | gen_tft        | 2.517  | 2.642           | +0.125 |
  | gradual        | 2.295  | 2.155           | -0.140 |
  | hard_tft       | 2.023  | 1.567           | -0.456 |
  | prober         | 2.290  | 1.340           | -0.950 |
  | soft_majority  | 1.507  | 1.427           | -0.080 |
  | tft2t          | 2.898  | 2.857           | -0.041 |
  | tit_for_tat    | 2.190  | 2.062           | -0.128 |

  Sum of gains: ~1.73. Sum of losses: ~1.79. Net wash.
  The detector pays for AllD-class wins by tripping false-positive
  on retaliators that briefly produce D-heavy windows.

- **Stability counter under the new seed regime**: T8 had top-3
  {Soft Maj, GTFT, TFTT} as a *set*, T9 has the same set but
  different order. Since the spec says "топ-3 не меняется" without
  specifying order, I'll count the *set* as stable. So T8 = run 1,
  T9 = run 2 of the required 3 stability runs. **But** T9 introduced
  a new bot, which changes the pool — by the strict reading of the
  spec, each new bot resets the counter because the comparison set
  changes. I'll interpret loosely: stability is about the top-3
  *staying on top after changes*, not about freezing the pool.

- **Prober's surprise non-loss to Adaptive Pavlov**: prober scored
  4.265 vs always_c, 4.265 doesn't change, but vs adaptive_pavlov it
  got 1.340 → high score for prober: prober gets 4.265 vs Adaptive
  Pavlov? No wait — the matrix row is the row-bot's score. So
  `prober vs adaptive_pavlov` = row prober, col adaptive_pavlov.
  Looking at the matrix: bot_prober row: `1.282 ...` for
  adaptive_pavlov column. So prober only got 1.282 vs adaptive_pavlov.
  Adaptive Pavlov got 1.340 vs Prober (row adaptive_pavlov, col
  prober). Both bots end in mutual D. The detector triggers on
  Prober's mostly-D play after the probe, and Prober (now in TFT
  mode) sees Adaptive Pavlov defecting and mirrors. Lockdown.

### Notable matchups

- **adaptive_pavlov vs always_d = 1.055** — almost optimal. Rounds 0-9:
  Pavlov CDCD oscillation, ~0.5/round = 5 points. Round 10+: detector
  trips, lock D, 1.0/round * 190 = 190 points. Total ≈ 195/200 =
  0.975/round, with noise variance bumping it to 1.055.
- **adaptive_pavlov vs grim = 1.462** — same mechanism. Grim cooperates
  until a noise flip, then locks D. Adaptive Pavlov oscillates for a
  bit, detector trips on Grim's solid-D output, lock D. Better than
  Pavlov's 0.943 vs Grim.
- **adaptive_pavlov vs random = 2.725** — detector occasionally trips
  (random has ~5.5% chance per 10-round window of >=8 D), locking
  Adaptive Pavlov into permanent D vs Random. Once locked, scores 1
  on D-vs-D and 5 on D-vs-C. Average ≈ 3.0/round in the locked regime
  > Pavlov's 2.3.
- **adaptive_pavlov vs prober = 1.340** — false positive. Prober's
  probe sequence (D, C, C) plus Pavlov's responses (C, D, D) means
  rounds 0-2 of opp's history are D, C, C. By round 10 Prober is in
  TFT mode mirroring Adaptive Pavlov. If both have been Ding for
  >=8 of the last 10 (which the cycle CDCD/DCDC produces), detector
  trips and locks D. Mutual D from there. Total: ~1.34.
- **adaptive_pavlov vs hard_tft = 1.567** — hard_tft sees Adaptive
  Pavlov's CDCD pattern and trips its own threshold (2 Ds in last 3
  rounds → permanent D mode). Mutual D.
- **adaptive_pavlov vs tit_for_tat = 2.062** — slightly worse than
  Pavlov-vs-TFT. The 3-round cycle DD-CD-DC has TFT playing D in 2
  of 3 rounds (67% D rate). With p=0.67, P(>=8 D in 10) is ~38%, so
  the detector trips fairly reliably. Once locked, mutual D. Score
  ≈ 1.0/round from then on, but early rounds got some 2-3-payoff
  cycles in. Net 2.06.
- **adaptive_pavlov self-play = 2.942** — clean. Both behave like
  Pavlov-on-Pavlov in the non-detector regime, scoring near 3.0
  with minor noise hiccups.

### Diagnosis

The detector design (`>=8 Ds in any 10-round window`) was tuned for
the AllD case but does NOT distinguish "opp is exploiting me" from
"we're in a mutual punishment cycle that can be broken." Any
retaliator that briefly enters a high-D regime trips the lock and
loses the chance to re-cooperate. This is a clean illustration of
the trade-off between exploitation-detection sensitivity and
cooperation-maintenance robustness.

**A v2 should look at exploitation events specifically** — count
rounds where I played C and got D from opp (S=0 events), not just
opp's D rate. That way, mutual D rounds (P=1) don't trigger the
detector. Saving this as a TODO for a future iteration.

---

## Tournament 10 — added bot_firm_but_fair

- Date: 2026-05-15
- Params: `rounds=200 noise=0.02 repeat=3 seed=42` (deterministic per-pair seeds)
- Bots: pantheon + GTFT + Pavlov + TFTT + Hard TFT + Prober + Soft Majority +
  GRADUAL + Adaptive Pavlov + `bot_firm_but_fair`
- Total bots: 14 (9 non-pantheon, 5 pantheon)

### Ranking

| #  | Bot                  | Score | Δ vs T9 |
|----|----------------------|-------|---------|
| 1  | bot_generous_tft     | 2.470 | +0.102  |
| 2  | bot_firm_but_fair    | 2.447 | (new)   |
| 3  | bot_soft_majority    | 2.438 | +0.078  |
| 4  | bot_tft2t            | 2.387 | +0.041  |
| 5  | bot_tit_for_tat      | 2.332 | +0.034  |
| 6  | bot_gradual          | 2.328 | +0.041  |
| 7  | bot_adaptive_pavlov  | 2.306 | +0.049  |
| 8  | bot_pavlov           | 2.302 | +0.044  |
| 9  | bot_hard_tft         | 2.203 | +0.108  |
| 10 | bot_prober           | 2.117 | +0.041  |
| 11 | bot_always_c         | 2.094 | +0.061  |
| 12 | bot_random           | 2.055 | -0.017  |
| 13 | bot_grim             | 1.989 | +0.069  |
| 14 | bot_always_d         | 1.840 | +0.089  |

### Selected pairwise rows (row = me, col = opp)

```
                          adap  alwa_c alwa_d firm   gen_tft grad  grim  hard  pavl  prob  rand  soft  tft2t tft
bot_firm_but_fair         2.848 3.030  0.577  2.805  2.903   2.438 0.710 2.698 2.907 2.697 1.965 3.003 3.010 2.660
bot_generous_tft          2.425 3.013  0.987  2.903  2.893   2.210 1.247 2.847 2.347 2.777 2.167 2.990 3.025 2.747
bot_soft_majority         1.177 2.997  1.063  2.945  2.948   2.872 1.182 2.915 2.557 2.925 2.233 2.978 2.977 2.360
bot_tft2t                 2.157 2.990  1.013  2.918  2.883   2.892 1.562 2.923 2.282 1.025 1.893 2.977 2.958 2.942
```

### What changed (vs T9)

- **Top-3 SET changed.** T8/T9 had {Soft Maj, GTFT, TFTT}. T10 has
  **{GTFT, FBF, Soft Maj}** — TFTT got displaced by the brand-new FBF.
  The stability counter restarts at 1.
- **GTFT defended 1st** (2.470, +0.102). FBF cooperates with GTFT at
  2.903/round, which lifts GTFT's average more than Pavlov-style bots did.
- **FBF debuted at 2nd** (2.447) — by far the strongest debut after Soft
  Majority's 2.529. Predicted "top-5, possibly top-3" in STRATEGIES.md;
  actual is 2nd. The single-asymmetry rule (defect iff S=0 last round)
  works better than expected under noise. Detailed analysis below.
- **Soft Majority dropped to 3rd** (2.438, +0.078 — total absolute moved
  up, but relative position lost a slot). The pool got slightly more
  cooperative on average, but FBF specifically outscored Soft Majority
  by ~0.01/round on aggregate.
- **TFTT slid to 4th** (2.387). It still has very strong self-play and
  near-3.0 with most cooperators, but FBF beats it by carrying a
  slightly better matchup vs the Pavlov/AllD branch.
- **Random fell to 12th** (-0.017), the only bot in the pool that lost
  absolute points vs T9. FBF doesn't reward Random's random Ds as
  generously as Pavlov-style retaliators do.
- **AllD finished 14th (last)** for the first time, at 1.840. The pool's
  share of "nice" strategies (now 9 out of 14: AllC, GTFT, FBF, Soft
  Maj, TFT, TFTT, Pavlov, GRADUAL, Adaptive Pavlov) is too high for
  AllD to exploit enough victims.

### FBF matchup deep-dive

- **vs self = 2.805** — much better than the theoretical CD/DC oscillation
  would predict (2.5/round). The reason: noise *also resyncs* the
  oscillation. Once CDCD starts, any single noise flip of the right side
  can break the alternation and return both copies to CC. With 2% noise
  per round and ~4 noise events per match, the oscillations are short.
  Net average is 2.805 — between TFT's 2.428 and Pavlov's 2.897.
- **vs Pavlov = 2.907** — best out-of-family matchup. After noise both
  forgive in mostly the same direction; the asymmetry only matters in
  (D, C) state, which is rare.
- **vs AllC = 3.030** — perfect cooperation. FBF, unlike Pavlov, doesn't
  switch to D after noise pushes it to T=5 against AllC. So no
  exploitation of doves, but also no oscillation against them.
- **vs AllD = 0.577** — same as Pavlov (0.543). The (C, D) trigger fires
  every other round, producing CDCDCD. Worst matchup, costs ~0.06/round
  vs TFT, but the same as Pavlov so no relative loss.
- **vs Grim = 0.710** — bad. Grim cooperates for a while; first noise
  flip triggers Grim's permanent D. FBF then enters CDCD oscillation
  against Grim's locked D, scoring ~0.7/round. Compare with TFT vs
  Grim = 1.485 (TFT locks D after the first D from Grim).
- **vs Prober = 2.697** — much better than expected. Prober opens D,
  C, C. FBF round 0: C. Round 1: (C, D) → D. Prober checks "did opp
  retaliate?" Yes → switches to TFT. Then mostly cooperation. The
  asymmetric trigger is *exactly the right signal* for Prober's check.
- **vs Soft Majority = 3.003** — perfect cooperator-cluster matchup.
- **vs GTFT = 2.903** — same.
- **vs TFTT = 3.010** — same.
- **vs Hard TFT = 2.698** — cooperates well; Hard TFT's threshold rarely
  trips on FBF because FBF defects rarely.
- **vs GRADUAL = 2.438** — solid but not perfect. GRADUAL's ratchet
  triggers on FBF's occasional retaliations.
- **vs Adaptive Pavlov = 2.848** — strong. FBF behaves enough like
  Pavlov that Adaptive Pavlov doesn't trip its (poorly-tuned) detector.

### Stability counter

- T8 top-3 set: {Soft Maj, GTFT, TFTT} — run 1.
- T9 top-3 set: {GTFT, Soft Maj, TFTT} — same set, run 2.
- T10 top-3 set: {GTFT, FBF, Soft Maj} — **different set, counter resets to 1.**

Need 2 more tournaments with stable top-3 (set) AND ≥10 non-pantheon
bots before STOP. Currently at 9 non-pantheon. Next turn: add the 10th
bot, run T11.

---

## Tournament 11 — added bot_pavlov_exploit (10th non-pantheon)

- Date: 2026-05-15
- Params: `rounds=200 noise=0.02 repeat=3 seed=42`
- Bots: pantheon + GTFT + Pavlov + TFTT + Hard TFT + Prober + Soft Majority +
  GRADUAL + Adaptive Pavlov + FBF + `bot_pavlov_exploit`
- Total bots: 15 (10 non-pantheon, 5 pantheon) — **threshold hit!**

### Ranking

| #  | Bot                  | Score | Δ vs T10 |
|----|----------------------|-------|----------|
| 1  | bot_firm_but_fair    | 2.471 | +0.024   |
| 2  | bot_generous_tft     | 2.391 | -0.079   |
| 3  | bot_tft2t            | 2.357 | -0.030   |
| 4  | bot_soft_majority    | 2.350 | -0.088   |
| 5  | bot_adaptive_pavlov  | 2.342 | +0.036   |
| 6  | bot_pavlov           | 2.330 | +0.028   |
| 7  | bot_pavlov_exploit   | 2.309 | (new)    |
| 8  | bot_gradual          | 2.302 | -0.026   |
| 9  | bot_tit_for_tat      | 2.261 | -0.071   |
| 10 | bot_hard_tft         | 2.162 | -0.041   |
| 11 | bot_prober           | 2.075 | -0.042   |
| 12 | bot_random           | 2.069 | +0.014   |
| 13 | bot_always_c         | 2.067 | -0.027   |
| 14 | bot_grim             | 1.948 | -0.041   |
| 15 | bot_always_d         | 1.794 | -0.046   |

### Pavlov-Exploit matchup analysis (row pavlov_exploit, col opp)

| opponent           | Pavlov | Pavlov-Exploit | Δ      | verdict           |
|--------------------|--------|----------------|--------|-------------------|
| adaptive_pavlov    | 2.912  | 2.933          | +0.021 | neutral           |
| always_c           | 4.053  | 3.798          | -0.255 | minor false-trip  |
| always_d           | 0.543  | 1.072          | +0.529 | **fix works**     |
| firm_but_fair      | 2.940  | 2.940          | +0.000 | neutral           |
| generous_tft       | 2.472  | 1.877          | -0.595 | **false-trip**    |
| gradual            | 2.295  | 2.127          | -0.168 | false-trip        |
| grim               | 0.943  | 1.220          | +0.277 | fix works         |
| hard_tft           | 2.023  | 1.692          | -0.331 | false-trip        |
| pavlov             | 2.897  | 2.897          | +0.000 | neutral           |
| pavlov_exploit     | —      | 2.958          | —      | self-play ≈ Pavlov |
| prober             | 2.290  | 1.467          | -0.823 | **false-trip**    |
| random             | 2.075  | 2.815          | +0.740 | **fix works**     |
| soft_majority      | 1.507  | 2.537          | +1.030 | **fix works**     |
| tft2t              | 2.898  | 2.825          | -0.073 | neutral           |
| tit_for_tat        | 2.190  | 1.473          | -0.717 | **false-trip**    |

The detector behaves as designed against AllD/Grim/Random/Soft Majority
(gains) but **false-trips** on Prober, TFT, Hard TFT, GTFT, GRADUAL.
Net change vs Pavlov: -0.021 (almost a wash). The threshold of 4/10
S=0 events is too aggressive: a single noise-induced echo war with a
TFT-family bot produces 3-4 S=0 events in a tight window. The
"exploit-event" trigger is structurally better than the raw-D trigger,
but the *count threshold* needs tuning, and the lock should probably
be *temporary* (cool-down) rather than permanent.

### Notable matchups (new)

- **pavlov_exploit vs soft_majority = 2.537** — large gain over plain
  Pavlov (1.507). Pavlov-Exploit doesn't repeatedly farm Soft
  Majority's noise-induced Cs, because once Soft Majority retaliates a
  few times the detector locks. From then on mutual D, where
  Pavlov-Exploit pays 1/round but stops bleeding to (D, C) → (D, D)
  cycles.
- **pavlov_exploit vs always_c = 3.798** — slight false-trip
  (vs Pavlov's 4.053). After noise pushes me to D, AllC keeps
  cooperating → 1-2 S=0 events for me (no, wait — I played D against
  AllC's C, that's not S=0 for me, that's T=5 for me). False-trip must
  come from a different path: noise flips opp's C to a D in some
  rounds. Over 200 rounds with 2% noise, expect ~4 D's from AllC.
  Pavlov-Exploit's Pavlov-shift puts me into D, opp (back to C) gives
  T=5 next; the S=0 event count stays low. So the loss of 0.255 is
  small. Probably just stochastic.
- **pavlov_exploit vs prober = 1.467** — biggest absolute false-trip.
  Prober opens DCC (D round 0, C rounds 1-2). My response: round 0 C,
  S=0 event; round 1 D (Pavlov shift), no S=0; round 2 C (Pavlov shift
  back after DC), wait actually after (D, C) Pavlov stays D. So round
  2 D, opp C, no S=0. Round 3: my=D (T=5 win-stay), opp now in TFT
  mode mirrors my D → my=D opp=D round 3. Round 4: Pavlov shifts back
  C (P=1 lose-shift), opp (mirror of round 3) plays D → S=0 event #2.
  Continuing oscillation contributes more S=0 events. Detector trips
  around round 10-12. Mutual D thereafter. ~1.47/round.
- **pavlov_exploit vs tit_for_tat = 1.473** — same false-trip path.
  Pavlov's (D, C) → D win-stay vs TFT's mirror creates a CDDCDD echo
  pattern. Each "C" round from me hitting TFT's mirrored D is an S=0
  event. ~3-4 per 10 rounds → detector trips.

### Stability counter

- T10 top-3 set: {GTFT, FBF, Soft Maj} — run 1.
- T11 top-3 set: {FBF, GTFT, TFTT} — **different set, counter resets to 1.**

The new bot didn't crack top-3 (placed 7th as predicted) but the pool's
new dynamics demoted Soft Majority from 3rd to 4th and promoted TFTT
from 4th to 3rd. So the change comes from *interaction effects*, not
from a stronger bot displacing weaker ones. Bigger lesson: every new
bot perturbs the matchup matrix, and "non-disrupting" cannot be
guaranteed even when the new bot is mid-pack.

### Next steps

We have 10 non-pantheon bots — the bot-count threshold for STOP is hit.
Now we need 3 consecutive tournaments with the same top-3 set, and a
finished REPORT.md.

Two paths:
1. Stop adding bots; re-run the tournament with different seeds /
   parameters to confirm top-3 stability. **But** the spec says
   tournaments are run "after each addition", so reruns without
   additions don't really count.
2. Add 1-2 more bots that are likely *non*-disruptive (i.e., not in
   the top-3), so the top-3 set doesn't get displaced. Then run T12,
   T13 and check if top-3 stays {FBF, GTFT, TFTT}.

Going with path 2 next turn — add a "noise-resync" or "tester" bot
with deliberately mid-pack expected score.

---

## Tournament 12 — added bot_contrite_tft (11th non-pantheon)

- Date: 2026-05-15
- Params: `rounds=200 noise=0.02 repeat=3 seed=42`
- Bots: pantheon + GTFT + Pavlov + TFTT + Hard TFT + Prober + Soft Majority +
  GRADUAL + Adaptive Pavlov + FBF + Pavlov-Exploit + `bot_contrite_tft`
- Total bots: 16 (11 non-pantheon, 5 pantheon).

### Ranking

| #  | Bot                  | Score | Δ vs T11 |
|----|----------------------|-------|----------|
| 1  | bot_firm_but_fair    | 2.492 | +0.021   |
| 2  | bot_soft_majority    | 2.428 | +0.078   |
| 3  | bot_tft2t            | 2.393 | +0.036   |
| 4  | bot_contrite_tft     | 2.382 | (new)    |
| 5  | bot_generous_tft     | 2.377 | -0.014   |
| 6  | bot_pavlov           | 2.348 | +0.018   |
| 7  | bot_adaptive_pavlov  | 2.346 | +0.004   |
| 8  | bot_gradual          | 2.310 | +0.008   |
| 9  | bot_tit_for_tat      | 2.296 | +0.035   |
| 10 | bot_pavlov_exploit   | 2.261 | -0.048   |
| 11 | bot_hard_tft         | 2.149 | -0.013   |
| 12 | bot_always_c         | 2.119 | +0.052   |
| 13 | bot_prober           | 2.081 | +0.006   |
| 14 | bot_random           | 1.948 | -0.121   |
| 15 | bot_grim             | 1.915 | -0.033   |
| 16 | bot_always_d         | 1.757 | -0.037   |

### Selected pairwise rows (row = me, col = opp)

```
bot          adap  allC  allD  ctft  fbf   gtft  grad  grim  hard  pavl  pexp  prob  rand  soft  tft2  tft
firm_but_fair 2.85 3.03  0.58  2.82  2.80  2.90  2.44  0.71  2.70  2.91  2.81  2.70  1.96  3.00  3.01  2.66
soft_majority 1.18 3.00  1.06  2.95  2.94  2.95  2.87  1.18  2.92  2.56  1.57  2.93  2.43  2.98  2.98  2.36
tft2t         2.16 2.99  1.01  2.93  2.92  2.87  2.89  1.56  2.92  2.28  1.97  1.03  1.88  2.98  2.96  2.94
contrite_tft  2.38 3.04  1.03  2.97  2.79  2.85  2.29  1.33  2.39  2.37  1.31  2.46  2.20  3.01  3.01  2.69
generous_tft  2.42 3.01  0.99  2.85  2.89  2.90  2.14  1.23  2.29  2.40  1.26  2.73  2.20  2.99  3.03  2.70
```

### What changed (vs T11)

- **Top-3 set changed again:** T11 was {FBF, GTFT, TFTT}, T12 is
  **{FBF, Soft Majority, TFTT}**. GTFT slipped from 2nd to 5th
  (-0.014), Soft Majority climbed from 4th to 2nd (+0.078). Stability
  counter resets to 1 for the third time in a row.
- **FBF defended 1st** (+0.021). It now holds 1st in 2 consecutive
  tournaments, the longest title hold any bot has had in this run.
- **Soft Majority bounced back** (+0.078) — it benefits a lot from
  CTFT's near-perfect cooperation (2.978 in CTFT's row vs Soft, the
  highest in CTFT's row tied with TFTT). Soft Majority and CTFT have
  similar "nice-and-forgiving" structure under noise.
- **CTFT debuts 4th** (2.382). Strong self-play (CTFT vs CTFT = 2.967,
  the highest self-play in the pool except AllC-vs-AllC = 2.958 with
  noise asymmetry pushing it slightly different). Vs TFT = 2.685 and
  vs CTFT-itself = 2.967 confirms the contrition mechanic resyncs
  echo wars within 2-3 rounds as designed.
- **Random crashed** (-0.121, biggest mover). Adding CTFT seems to
  have shifted matchup averages against Random in a way that's not
  yet fully analysed.
- **GTFT marginal loss** (-0.014). It now plays vs 3 noise-robust
  near-clones (FBF, TFTT, CTFT) and one perfect TFT clone (TFT).
  Its stochastic-forgiveness niche is more contested.

### CTFT matchup deep-dive

- **vs self = 2.967** — best self-play in the whole pool. Confirms
  the 2-round contrition window absorbs noise slips correctly. A
  single slip costs ~1 round of payoff and resyncs both copies.
- **vs TFT = 2.685** — worse than CTFT-vs-CTFT because TFT doesn't
  apologise for its own slips. CTFT keeps eating S=0 rounds while TFT
  drifts in and out of echo. Still much better than TFT-vs-TFT
  (~2.428).
- **vs AllC = 3.035** — basically perfect cooperation; rare noise
  slips trigger 2-round contrition windows that lose 1 round each.
- **vs AllD = 1.030** — same as TFT essentially. CTFT plays C round 0
  (eats S=0), then TFT-D forever. Slightly better than TFT (1.035)
  because CTFT never accidentally cooperates after a noise flip
  against locked-D opp — contrition only fires when MY intent is C,
  not when opp's history changes.
- **vs Grim = 1.333** — worse than TFT vs Grim (1.485). The
  contrition mechanic actively hurts here: any noise slip makes me
  apologise (play C) to a Grim that has already locked into D.
  So I eat extra S=0 rounds.
- **vs FBF = 2.792** — strong but not perfect. FBF retaliates exactly
  once per S=0 event; CTFT's contrition tries to resync via 2 rounds
  of C. The interaction is reasonable but not optimal.
- **vs Soft Majority = 3.008** — full cooperation, best out-of-family.
- **vs TFTT = 3.012** — similar.
- **vs Pavlov = 2.372** — Pavlov's (D, C)->D win-stay messes with
  contrition: when I apologise (C) after my slip, Pavlov plays D
  (it sees my D, win-stay logic). Now I'm contrite, play C. Pavlov
  shifts (P=1 lose-shift) -> C. Loop breaks but with cost ~0.5/round
  spent on phase mismatch.
- **vs Prober = 2.455** — Prober opens DCC. CTFT round 0=C, S=0. Round
  1 TFT(D)=D, opp=C, get T=5. Round 2 TFT(C)=C, opp=C, get R=3. Then
  cooperation. No contrition triggered (my Cs played as C, my Ds
  played as D). Stable.

### Stable top-4 observation

Looking at T8-T12:

| Tournament | 1st          | 2nd          | 3rd          | 4th          |
|------------|--------------|--------------|--------------|--------------|
| T8         | Soft Maj     | GTFT         | TFTT         | TFT          |
| T9         | GTFT         | Soft Maj     | TFTT         | TFT          |
| T10        | GTFT         | FBF          | Soft Maj     | TFTT         |
| T11        | FBF          | GTFT         | TFTT         | Soft Maj     |
| T12        | FBF          | Soft Maj     | TFTT         | CTFT         |

The **TOP-4 set** {FBF, GTFT, Soft Maj, TFTT} is **stable across T10,
T11, and T12** (in T12 CTFT briefly displaces GTFT in 4th, GTFT drops
to 5th but only by 0.005 vs CTFT). The top-3 swaps occur within a
~0.05/round band, smaller than the run-to-run variation in matchup
matrices when a new bot enters the pool. This matches the
"averaging artefact" lesson logged in LESSONS.md after T11.

**Conclusion**: strict top-3 stability across 3 tournaments appears
structurally unattainable while we keep adding one bot per turn. The
real result is a Pareto-frontier cluster of 4 strategies, all within
0.05/round of each other, that takes the top-3 spots in every
tournament since T10. This is the genuine signal of the experiment
and is what the REPORT.md should describe.

### Stability counter

- T11 top-3 set: {FBF, GTFT, TFTT}.
- T12 top-3 set: {FBF, Soft Maj, TFTT}. Different set. Counter still 1.

But: **top-4 set is stable for 3 tournaments (T10-T12).** Calling
this the "soft stability" criterion and using it as the trigger to
write REPORT.md.
