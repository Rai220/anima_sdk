# Tournament Scores Log

All scores are sums per 200-round match, averaged over `repeat` matches per
pairing, and ranking is the mean across all opponents (including self-play).

---

## Run #1 — 2026-05-17 — reference pantheon only

Params: `rounds=200 noise=0.02 repeat=3 seed=42`
Bots (5): `bot_always_c`, `bot_always_d`, `bot_grim`, `bot_random`, `bot_tit_for_tat`.

### Ranking
| # | Bot | Avg score |
|---|-----|-----------|
| 1 | bot_grim         | 461.60 |
| 2 | bot_always_d     | 446.00 |
| 3 | bot_tit_for_tat  | 410.33 |
| 4 | bot_random       | 387.20 |
| 5 | bot_always_c     | 330.13 |

### Matrix (row gets these points vs column)
```
                 always_c always_d grim     random   tit
bot_always_c        591.0     23.7    144.0    308.0    584.0
bot_always_d        970.3    217.3    216.7    586.7    239.0
bot_grim            892.3    206.7    292.7    627.3    289.0
bot_random          788.0    115.0    107.3    463.0    462.7
bot_tit_for_tat     605.7    210.7    272.3    467.7    495.3
```

### Notable pairings
- AllC vs AllD: 23.7 - 970.3 — the textbook exploitation.
- Grim vs Grim: 292.7 — after a single random noise flip, both go to permanent
  D and the match collapses. Grim is fragile under noise.
- TFT vs TFT: 495.3 — also takes a hit from noise (a flip starts a vendetta
  loop of alternating retaliations), but the alternating reciprocations keep
  the score above mutual D.
- Grim beat AllD: 206.7 vs 216.7 — basically a tie (both defect from round 2),
  the small gap is just noise variance.
- Grim made the most against the sucker (AllC: 892.3) and rode hard on random
  (627.3).

---

## Run #2 — 2026-05-17 — pantheon + pavlov

Params: `rounds=200 noise=0.02 repeat=3 seed=42`
Bots (6): pantheon + `bot_pavlov`.

### Ranking
| # | Bot | Avg score |
|---|-----|-----------|
| 1 | bot_grim         | 483.50 |
| 2 | bot_always_d     | 470.22 |
| 3 | bot_pavlov       | 458.50 |
| 4 | bot_tit_for_tat  | 411.94 |
| 5 | bot_random       | 391.06 |
| 6 | bot_always_c     | 327.00 |

### Matrix (row gets these points vs column)
```
                 always_c always_d grim     pavlov   random   tit
bot_always_c        591.0     23.7    144.0    311.3    308.0    584.0
bot_always_d        970.3    217.3    216.7    591.3    586.7    239.0
bot_grim            892.3    206.7    292.7    593.0    627.3    289.0
bot_pavlov          789.7    119.7    348.0    571.7    498.7    423.3
bot_random          788.0    115.0    107.3    410.3    463.0    462.7
bot_tit_for_tat     605.7    210.7    272.3    420.0    467.7    495.3
```

### Notable pairings
- Pavlov vs Pavlov: 571.7 — almost the 600 ceiling. After a noise flip into
  DD, both lose-shift back to C the next round and re-establish CC. Best
  self-play of any non-trivial bot here.
- Pavlov vs AllD: 119.7 — the famous Achilles heel. Pavlov keeps cycling
  C→D→C→D because DD triggers a shift back to C, which AllD then exploits
  every other round (≈0.5 sucker payoff). Loses 100+ points to TFT here.
- Pavlov vs Grim: 348.0 / 593.0 — Grim catches Pavlov's occasional D
  experiments (and noise) and never forgives. Pavlov bleeds out.
- Pavlov vs Random: 498.7 — outpaces both TFT (467.7) and Grim's 627
  exploitation here is bigger; but Pavlov is more resilient when random
  flickers.
- Top 3 unchanged from Run #1 in terms of ordering (Grim, AllD, then
  a reciprocator). Pavlov displaces TFT for the bronze.

---

## Run #3 — 2026-05-17 — pantheon + pavlov + generous_tft

Params: `rounds=200 noise=0.02 repeat=3 seed=42`
Bots (7): pantheon + `bot_pavlov` + `bot_generous_tft`.

### Ranking
| # | Bot | Avg score |
|---|-----|-----------|
| 1 | bot_grim          | 484.48 |
| 2 | bot_pavlov        | 476.81 |
| 3 | bot_always_d      | 469.71 |
| 4 | bot_tit_for_tat   | 437.95 |
| 5 | bot_generous_tft  | 433.57 |
| 6 | bot_random        | 415.48 |
| 7 | bot_always_c      | 363.62 |

### Matrix (row gets these points vs column)
```
                  always_c always_d gen_tft  grim     pavlov   random   tit
bot_always_c         591.0     23.7    583.3    144.0    311.3    308.0    584.0
bot_always_d         970.3    217.3    466.7    216.7    591.3    586.7    239.0
bot_generous_tft     601.7    146.7    585.3    207.0    526.7    395.3    572.3
bot_grim             892.3    206.7    490.3    292.7    593.0    627.3    289.0
bot_pavlov           789.7    119.7    586.7    348.0    571.7    498.7    423.3
bot_random           788.0    115.0    562.0    107.3    410.3    463.0    462.7
bot_tit_for_tat      605.7    210.7    594.0    272.3    420.0    467.7    495.3
```

### Notable pairings
- GTFT vs GTFT: 585.3 — almost the 600 ceiling. The forgiveness probability
  p=1/3 makes noise vendettas expected to last ~3 rounds before someone
  cools down, so most of the match stays at CC. This is a *huge* upgrade
  over TFT-vs-TFT (495.3) and on par with Pavlov-vs-Pavlov (571.7).
- GTFT vs TFT: 572.3 — also near-ceiling. GTFT's forgiveness rescues both
  sides from a noise vendetta with plain TFT too. Compare TFT-vs-TFT 495.3
  for the cost of a single GTFT entry to the population.
- GTFT vs Pavlov: 526.7 / 586.7 — asymmetric and Pavlov nets more. Pavlov
  occasionally tries D after a noise-induced loss; GTFT often forgives,
  Pavlov pockets a T. Still much better than TFT-vs-Pavlov (420.0).
- GTFT vs AllD: 146.7 vs 466.7 — GTFT's Achilles heel. AllD exploits the
  1/3 forgiveness rate: every defection has 33% chance of being met with C,
  so AllD earns ≈ (5·1/3 + 1·2/3) = 2.33/round instead of TFT's ~1.05/round.
  Compare TFT vs AllD: 210.7. GTFT pays 64 points to AllD relative to TFT.
- GTFT vs Grim: 207.0 — also worse than TFT (272.3). Grim never forgives
  GTFT's noise-induced retaliations, and GTFT's own forgiveness gets
  wasted on a permanently-D opponent.
- **GTFT places 5th in this field** because the gain vs other cooperators
  is smaller than the loss vs AllD in a population where AllD is just
  1/7 of opponents. GTFT would dominate a population of mostly
  reciprocators — exactly the Axelrod evolutionary scenario.

---

## Run #4 — 2026-05-17 — pantheon + pavlov + generous_tft + tit_for_two_tats

Params: `rounds=200 noise=0.02 repeat=3 seed=42`
Bots (8): all of the above + `bot_tit_for_two_tats`.

### Ranking
| # | Bot | Avg score |
|---|-----|-----------|
| 1 | bot_pavlov            | 488.12 |
| 2 | bot_grim              | 459.29 |
| 3 | bot_tit_for_tat       | 458.12 |
| 4 | bot_generous_tft      | 454.29 |
| 5 | bot_tit_for_two_tats  | 452.25 |
| 6 | bot_always_d          | 441.00 |
| 7 | bot_random            | 440.25 |
| 8 | bot_always_c          | 392.42 |

### Matrix (row gets these points vs column)
```
                  allc  alld  gtft  grim  pav   rand  tft   tf2t
bot_always_c      591.0  23.7 583.3 144.0 311.3 308.0 584.0 594.0
bot_always_d      970.3 217.3 466.7 216.7 591.3 586.7 239.0 240.0
bot_generous_tft  601.7 146.7 585.3 207.0 526.7 395.3 572.3 599.3
bot_grim          892.3 206.7 490.3 292.7 593.0 627.3 289.0 283.0
bot_pavlov        789.7 119.7 586.7 348.0 571.7 498.7 423.3 567.3
bot_random        788.0 115.0 562.0 107.3 410.3 463.0 462.7 613.7
bot_tit_for_tat   605.7 210.7 594.0 272.3 420.0 467.7 495.3 599.3
bot_tit_for_two   597.3 200.0 587.7 231.3 432.3 383.7 591.0 594.7
```

### Big movements vs Run #3
- **Pavlov leaps to #1** (488.12, +11). Adding another mostly-cooperating
  opponent (TF2T) inflates the entire reciprocator tier; Pavlov benefits
  the most because its self-correcting CC restoration works against any
  partner who is also non-vindictive.
- **Grim drops from #1 to #2** (459.29, −25). TF2T pulls Grim's average
  down (Grim vs TF2T = 231.3) because once Grim trips into permanent D
  (after the first noise flip), TF2T eventually sees two D's in a row
  and locks to D itself. Mutual D for the remaining ~190 rounds at 1/round.
- **AllD slides from #3 to #6** (441.00, −29). TF2T does NOT play sucker
  forever — it gives AllD only the first two rounds free, then mirrors D.
  AllD only gets 200 from TF2T (vs 970 from AllC, 586 from Random). The
  whole field is shifting away from naive cooperation, hurting AllD.
- **Top 3 changed** (was Grim/Pavlov/AllD, now Pavlov/Grim/TFT). The
  stop condition (3 stable top-3 runs) is reset.

### Notable pairings involving TF2T
- TF2T vs TF2T: 594.7 — essentially the 600 ceiling. A single noise flip
  is absorbed; only a rare double-flip event triggers any retaliation,
  and even that ends within two rounds.
- TF2T vs TFT: 591.0 (TF2T) / 599.3 (TFT) — much better than TFT-vs-TFT
  (495.3). One noise flip on TFT's side: TFT plays D once; TF2T forgives
  (only one D); TFT sees C and returns to C. No vendetta.
- TF2T vs GTFT: 587.7 / 599.3 — same story.
- TF2T vs AllD: 200.0 vs 240.0 — TF2T pays two sucker rounds, then locks
  to mutual D. About 10 points worse than TFT here; the cost is small.
- TF2T vs Grim: 231.3 / 283.0 — symmetric problem. Noise tips Grim into
  permanent D; TF2T eventually catches up after two consecutive D's. The
  cumulative damage from "Grim won't forgive" still hurts TF2T more than
  TFT (272.3) because TF2T is slower to switch and so eats one more
  sucker round before mirroring.
- TF2T vs Pavlov: 432.3 / 567.3 — TF2T is *bad* against Pavlov! Pavlov
  occasionally probes D; TF2T forgives one D; Pavlov gets a free T=5,
  back to CD, win-stays at D; eats another sucker; eventually TF2T sees
  the second D and retaliates; Pavlov lose-shifts to C; TF2T sees C and
  forgives — Pavlov pockets more T's per cycle than against TFT. This
  is the textbook TF2T weakness against alternators / probers.

---

## Run #5 — 2026-05-17 — pantheon + pavlov + generous_tft + tit_for_two_tats + adaptive_tft

Params: `rounds=200 noise=0.02 repeat=3 seed=42`
Bots (9): all of the above + `bot_adaptive_tft` (TFT + AllD detector,
WINDOW=10 / THRESHOLD=7).

### Ranking
| # | Bot | Avg score |
|---|-----|-----------|
| 1 | bot_pavlov            | 483.07 |
| 2 | bot_generous_tft      | 467.70 |
| 3 | bot_tit_for_two_tats  | 467.63 |
| 4 | bot_random            | 441.74 |
| 5 | bot_tit_for_tat       | 441.30 |
| 6 | bot_grim              | 437.11 |
| 7 | bot_adaptive_tft      | 433.22 |
| 8 | bot_always_d          | 415.85 |
| 9 | bot_always_c          | 413.07 |

### Matrix (row gets these points vs column)
```
                  adap   allc   alld   gtft   grim   pav    rand   tft    tf2t
bot_adaptive_tft  367.7  608.3  216.3  595.0  249.7  457.7  475.3  328.3  600.7
bot_always_c      578.3  591.0   23.7  583.3  144.0  311.3  308.0  584.0  594.0
bot_always_d      214.7  970.3  217.3  466.7  216.7  591.3  586.7  239.0  240.0
bot_generous_tft  575.0  601.7  146.7  585.3  207.0  526.7  395.3  572.3  599.3
bot_grim          259.7  892.3  206.7  490.3  292.7  593.0  627.3  289.0  283.0
bot_pavlov        442.7  789.7  119.7  586.7  348.0  571.7  498.7  423.3  567.3
bot_random        453.7  788.0  115.0  562.0  107.3  410.3  463.0  462.7  613.7
bot_tit_for_tat   306.7  605.7  210.7  594.0  272.3  420.0  467.7  495.3  599.3
bot_tit_for_two   590.7  597.3  200.0  587.7  231.3  432.3  383.7  591.0  594.7
```

### Big movements vs Run #4
- **Pavlov holds #1** (483.07, −5 vs 488.12). Pavlov is robust; the new
  adaptive_tft scores 457.7 against Pavlov in Pavlov's column — Pavlov
  treats adaptive_tft like another reciprocator and milks it.
- **GTFT jumps from #4 to #2** (467.70, +13). GTFT vs adaptive_tft = 575.0,
  one of GTFT's better matches in the field. Adaptive_tft plays TFT against
  GTFT (no trigger fires), and GTFT's forgiveness rescues both from noise
  vendettas.
- **TF2T moves from #5 to #3** (467.63, +15). Same story: adaptive_tft is
  another mostly-cooperative opponent under noise, TF2T gets 590.7 against
  it (near-ceiling).
- **Grim drops from #2 to #6** (437.11, −22). The field grew by one more
  bot whose self-play locks into mutual D once Grim trips. Grim's
  mostly-D streaks against adaptive_tft trigger adaptive_tft's lock-up
  too, ensuring permanent DD = ~190 points for both.
- **AllD slides further** (8th, 415.85, −25). The detector finally bites:
  AllD vs adaptive_tft = 214.7, only 4 points better than TFT (210.7).
  Cumulative AllD damage from the whole field keeps shrinking.
- **Top 3 changed again**: Run #4 was Pavlov / Grim / TFT; Run #5 is
  Pavlov / GTFT / TF2T. The stop condition (3 stable top-3 runs) is
  reset again.

### Notable pairings involving adaptive_tft
- adaptive_tft vs adaptive_tft (self): **367.7** — disaster. A single
  noise flip starts a TFT-style vendetta. The vendetta itself has ~50%
  D rate, which alone doesn't trip the 7/10 threshold — but additional
  noise flips during the vendetta push the count over, one side locks D,
  the other now sees all-D and locks D within 10 rounds. Net: ~30 early
  CC rounds, then ~170 rounds of mutual D ≈ 90 + 170 = 260, plus some
  noise variance ≈ 368. Far below TFT-vs-TFT 495.3.
- adaptive_tft vs TFT: **328.3 / 306.7** — similar failure mode but
  asymmetric. The vendetta + noise triggers adaptive_tft to lock D
  faster than TFT. TFT then mirrors permanent D, score collapses to
  near-DD. Way worse than TFT-vs-TFT (495.3).
- adaptive_tft vs AllD: 216.3 — marginally better than TFT's 210.7.
  The trigger does fire (10 D's in 10 rounds), but the gain over TFT's
  mirroring is small because we still eat ~9 sucker rounds before
  locking.
- adaptive_tft vs Pavlov: 457.7 — better than TFT vs Pavlov (420.0).
  Pavlov's occasional D probes never accumulate to 7/10, so adaptive_tft
  behaves as TFT does. The gain is just noise variance in this seed.
- adaptive_tft vs Grim: 249.7 — slightly worse than TFT (272.3). Once
  Grim locks D, adaptive_tft locks D too within ~7 rounds (vs TFT's
  immediate mirror after 1 sucker). Cost: ~6 extra sucker rounds.
- adaptive_tft vs cooperators (AllC, GTFT, TF2T): essentially TFT-level
  scores (608 / 595 / 600). The detector never fires, no harm done.

### Verdict on adaptive_tft
Sits at #7, between TFT and Grim. The trigger does what it's supposed
to do against AllD, but the self-play penalty under noise (vendetta +
extra noise pushing the count over the threshold) wipes out the gain.
Either lower THRESHOLD is wrong direction, or the strategy needs a
different base than pure TFT (e.g., TF2T base would avoid the vendetta
in the first place, so the trigger only fires against genuine AllD).

---

## Run #6 — 2026-05-18 — pantheon + pavlov + gtft + tf2t + adaptive_tft + soft_majority

Params: `rounds=200 noise=0.02 repeat=3 seed=42`
Bots (10): all of the above + `bot_soft_majority`.

### Ranking
| #  | Bot                  | Avg score |
|----|----------------------|-----------|
| 1  | bot_soft_majority    | 496.33    |
| 2  | bot_generous_tft     | 480.13    |
| 3  | bot_tit_for_two_tats | 479.83    |
| 4  | bot_pavlov           | 475.00    |
| 5  | bot_tit_for_tat      | 457.70    |
| 6  | bot_adaptive_tft     | 450.23    |
| 7  | bot_random           | 448.23    |
| 8  | bot_grim             | 436.33    |
| 9  | bot_always_c         | 431.50    |
| 10 | bot_always_d         | 396.13    |

### Matrix (row gets these points vs column)
```
                  adap   allc   alld   gtft   grim   pav    rand   soft   tft    tf2t
bot_adaptive_tft  367.7  608.3  216.3  595.0  249.7  457.7  475.3  603.3  328.3  600.7
bot_always_c      578.3  591.0   23.7  583.3  144.0  311.3  308.0  597.3  584.0  594.0
bot_always_d      214.7  970.3  217.3  466.7  216.7  591.3  586.7  218.7  239.0  240.0
bot_generous_tft  575.0  601.7  146.7  585.3  207.0  526.7  395.3  592.0  572.3  599.3
bot_grim          259.7  892.3  206.7  490.3  292.7  593.0  627.3  429.3  289.0  283.0
bot_pavlov        442.7  789.7  119.7  586.7  348.0  571.7  498.7  402.3  423.3  567.3
bot_random        453.7  788.0  115.0  562.0  107.3  410.3  463.0  506.7  462.7  613.7
bot_soft_majority 585.0  595.7  208.7  590.3  251.0  504.0  441.7  602.0  582.0  603.0
bot_tit_for_tat   306.7  605.7  210.7  594.0  272.3  420.0  467.7  605.3  495.3  599.3
bot_tit_for_two   590.7  597.3  200.0  587.7  231.3  432.3  383.7  589.7  591.0  594.7
```

### Big movements vs Run #5
- **Soft Majority debuts at #1** (496.33). It harvests every cooperator
  near-ceiling (TFT 605.3, GTFT 590.3, TF2T 589.7, AllC 595.7, self 602)
  and only pays a modest cost to AllD (208.7, basically TFT-level) and
  random (441.7). Crucially it doesn't suffer self-play noise vendettas
  at all: a single flip never moves the majority. Its self-play 602.0
  is the highest non-AllC self-play in the field.
- **Pavlov drops from #1 to #4** (−8). It still has Pavlov-vs-Pavlov 571
  and the new soft_majority match is 402.3, a 70-point hole versus the
  500+ that soft_majority gets from Pavlov. Pavlov's "probe-D-after-loss"
  doesn't shift soft_majority's majority C, but soft_majority eventually
  catches enough Pavlov D's that it punishes — and once it starts playing
  D, Pavlov's lose-shift takes time to recover.
- **GTFT to #2, TF2T to #3.** Both near-tied (~480). They were already
  #2/#3 in Run #5 — adding soft_majority gives them another near-ceiling
  partner (~590 each), confirming their robustness in cooperator-rich
  fields.
- **Grim falls from #6 to #8** (436.33, −1 but rank slips). The new
  cooperator doesn't trip Grim, but Grim's miserable matches stay at the
  same level while everyone else climbs.
- **AllD slides to dead last** (10th, 396.13, −20). Soft Majority is yet
  another bot that punishes sustained defection — AllD gets only 218.7
  from it, comparable to TFT's mirror. The harvest from AllC and Random
  is no longer enough to offset.
- **Top 3 changed again** (Run #5: Pavlov/GTFT/TF2T → Run #6:
  SoftMaj/GTFT/TF2T). Stability counter for STOP condition resets.

### Notable pairings involving soft_majority
- soft_majority vs soft_majority: **602.0** — best non-AllC self-play in
  the field. Noise flips don't accumulate enough to flip the majority.
- soft_majority vs TFT: 582.0 / 605.3 — near-ceiling. TFT's occasional
  noise-induced D doesn't flip soft_majority's majority, so soft keeps
  C, TFT mirrors C back. Almost no vendetta.
- soft_majority vs TF2T: 603.0 / 589.7 — also near-ceiling.
- soft_majority vs GTFT: 590.3 / 592.0 — same.
- soft_majority vs AllD: **208.7** — only ~2 points below TFT (210.7).
  Round 1 is a sucker; from round 2 onwards opp_history has 100% D, so
  soft_majority plays D forever. Pretty much TFT-level cost.
- soft_majority vs AllC: 595.7 — wins like everyone else against the
  sucker, but doesn't have the AllD-like 970 harvest.
- soft_majority vs Grim: **251.0** vs Grim's **429.3** — the predicted
  weakness. After noise tips Grim into permanent D around round k,
  soft_majority's opp_history holds (k-1) C's. It takes another (k-1)
  rounds of D's to flip the majority. So soft_majority eats ~(k-1)
  sucker rounds before retaliating. For early flips (k≈5-10) the cost
  is manageable; for mid-match flips (k≈50) it's brutal.
- soft_majority vs Pavlov: **504.0** vs Pavlov's 402.3 — solidly better.
  Soft_majority's tolerance lets Pavlov's CC streaks be long; the few
  Pavlov-D probes don't flip the majority. Pavlov never gets to exploit
  soft_majority the way it exploits forgiving-by-probability strategies.
- soft_majority vs adaptive_tft: 585.0 / 603.3 — also near-ceiling. The
  adaptive trigger never fires (soft_majority is rarely D), and noise
  doesn't trigger soft_majority's majority either.

### Verdict on soft_majority
A clear top-tier strategy in this field. Its main weakness is "slow to
notice a permanent defector" — costly against Grim, but Grim itself is
near the bottom now. Against the rest of the field its blend of
near-ceiling cooperation + TFT-level AllD response makes it the most
robust bot we have.

---

## Run #7 — 2026-05-18 — Run #6 + tf2t_trigger (TF2T + AllD detector)

Params: `rounds=200 noise=0.02 repeat=3 seed=42`
Bots (11): all of the above + `bot_tf2t_trigger` (WINDOW=10, THRESHOLD=9).

### Ranking
| #  | Bot                  | Avg score |
|----|----------------------|-----------|
| 1  | bot_soft_majority    | 505.48    |
| 2  | bot_tit_for_two_tats | 491.09    |
| 3  | bot_generous_tft     | 491.06    |
| 4  | bot_tf2t_trigger     | 484.70    |
| 5  | bot_pavlov           | 483.30    |
| 6  | bot_tit_for_tat      | 470.85    |
| 7  | bot_random           | 465.15    |
| 8  | bot_adaptive_tft     | 464.36    |
| 9  | bot_always_c         | 446.88    |
| 10 | bot_grim             | 418.82    |
| 11 | bot_always_d         | 380.97    |

### Matrix (row gets these points vs column)
```
                  adap   allc   alld   gtft   grim   pav    rand   soft   tf2t_t tft    tf2t
bot_adaptive_tft  367.7  608.3  216.3  595.0  249.7  457.7  475.3  603.3  605.7  328.3  600.7
bot_always_c      578.3  591.0   23.7  583.3  144.0  311.3  308.0  597.3  600.7  584.0  594.0
bot_always_d      214.7  970.3  217.3  466.7  216.7  591.3  586.7  218.7  229.3  239.0  240.0
bot_generous_tft  575.0  601.7  146.7  585.3  207.0  526.7  395.3  592.0  600.3  572.3  599.3
bot_grim          259.7  892.3  206.7  490.3  292.7  593.0  627.3  429.3  243.7  289.0  283.0
bot_pavlov        442.7  789.7  119.7  586.7  348.0  571.7  498.7  402.3  566.3  423.3  567.3
bot_random        453.7  788.0  115.0  562.0  107.3  410.3  463.0  506.7  634.3  462.7  613.7
bot_soft_majority 585.0  595.7  208.7  590.3  251.0  504.0  441.7  602.0  597.0  582.0  603.0
bot_tf2t_trigger  582.3  592.3  207.7  587.0  228.7  406.3  362.7  595.3  595.0  585.7  588.7
bot_tit_for_tat   306.7  605.7  210.7  594.0  272.3  420.0  467.7  605.3  602.3  495.3  599.3
bot_tit_for_two   590.7  597.3  200.0  587.7  231.3  432.3  383.7  589.7  603.7  591.0  594.7
```

### Big movements vs Run #6
- **Soft Majority holds #1** (505.48, +9). Yet another cooperator joins
  the field, and soft_majority harvests near-ceiling from it (595.3).
  Its lead is now ~14 points over #2.
- **TF2T and GTFT essentially tied at #2/#3** (491.09 / 491.06). Both
  benefit from another reciprocator (each gets ~600 from tf2t_trigger).
- **tf2t_trigger debuts at #4** (484.70). The trigger helps a *little*
  against AllD/Grim but hurts noticeably against Random (362.7 vs
  TF2T's 383.7). The downside dominates the upside.
- **Top 3 stability check:** Run #6 top 3 = {SoftMaj, GTFT, TF2T}.
  Run #7 top 3 = {SoftMaj, TF2T, GTFT}. Same *set*, but order of #2/#3
  flipped. They're 0.03 points apart so this is effectively a tie.
  Treating top-3 as a set, this is run #2 in a row with the same top 3.
  One more run with the same set → STOP eligibility.

### Notable pairings involving tf2t_trigger
- tf2t_trigger vs tf2t_trigger (self): **595.0** — near-ceiling, on par
  with TF2T-vs-TF2T (594.7). The TF2T base prevents the noise vendetta
  and the trigger threshold (9/10) is too strict to ever fire between
  two cooperative bots under 2% noise.
- tf2t_trigger vs AllD: 207.7 — basically TF2T-level (200.0) +
  noise variance. The trigger does fire (around round 11) but TF2T's
  natural mirror after the first 2 sucker rounds already locked us
  to D, so the trigger only marginally improves things.
- tf2t_trigger vs Grim: **228.7 / 243.7** — slightly worse than TF2T
  (231.3). The trigger doesn't help here because once Grim trips into
  permanent D, TF2T locks D anyway. Single-match test (`tournament.py
  bots/bot_tf2t_trigger.py bots/bot_grim.py`) gave 251.67 / 261.67 —
  the discrepancy is just per-match noise variance.
- tf2t_trigger vs Random: **362.7 / 634.3** — the Achilles heel.
  Random plays D about 50% of the time. With 2% noise, occasionally
  Random hits 9 D's in a 10-round window, triggering tf2t_trigger's
  permanent-D lockup. Once locked, Random keeps giving free T's
  (~50% chance per round), pushing Random's score way up. TF2T
  without the trigger scored 383.7 against Random — the trigger
  costs us ~21 points there.
- tf2t_trigger vs Pavlov: **406.3 / 566.3** — also worse than TF2T's
  432.3. Pavlov occasionally probes D after noise-induced losses;
  these defections combined with noise sometimes trigger the lockup.
  Once locked, Pavlov harvests free T's like Random does.
- tf2t_trigger vs cooperators (TFT, GTFT, TF2T, soft_majority, AllC):
  near-ceiling. Trigger never fires.

### Verdict on tf2t_trigger
A small improvement over adaptive_tft (no self-play disaster) but does
*not* beat plain TF2T overall. The trigger gives a marginal gain vs
AllD (~8 points) but costs significantly more vs Random (~21) and
Pavlov (~26). The TF2T base saved it from adaptive_tft's catastrophe,
but the trigger itself remains a net negative in this field where
AllD is just 1 of 11 opponents.

Key lesson: ad-hoc "lock to permanent D" triggers are dangerous against
*any* opponent with a non-trivial D rate, not just AllD. They are best
used when AllD is known to be a substantial share of opponents, or
when paired with a release mechanism (e.g., re-test cooperation after
N rounds of mutual D).

---

## Run #8 — 2026-05-18 — Run #7 + gradual (Beaufils escalating Gradual)

Params: `rounds=200 noise=0.02 repeat=3 seed=42`
Bots (12): all of the above + `bot_gradual`.

### Ranking
| #  | Bot                  | Avg score |
|----|----------------------|-----------|
| 1  | bot_soft_majority    | 509.22    |
| 2  | bot_tit_for_two_tats | 490.72    |
| 3  | bot_tf2t_trigger     | 485.19    |
| 4  | bot_generous_tft     | 463.64    |
| 5  | bot_always_c         | 457.78    |
| 6  | bot_pavlov           | 455.81    |
| 7  | bot_tit_for_tat      | 453.58    |
| 8  | bot_adaptive_tft     | 445.42    |
| 9  | bot_random           | 437.61    |
| 10 | bot_gradual          | 430.61    |
| 11 | bot_grim             | 407.06    |
| 12 | bot_always_d         | 366.92    |

### Matrix (row gets these points vs column)
```
                  adap   allc   alld   gtft   grad   grim   pav    rand   soft   tf2t_t tft    tf2t
bot_adaptive_tft  367.7  608.3  216.3  595.0  237.0  249.7  457.7  475.3  603.3  605.7  328.3  600.7
bot_always_c      578.3  591.0   23.7  583.3  577.7  144.0  311.3  308.0  597.3  600.7  584.0  594.0
bot_always_d      214.7  970.3  217.3  466.7  212.3  216.7  591.3  586.7  218.7  229.3  239.0  240.0
bot_generous_tft  575.0  601.7  146.7  585.3  162.0  207.0  526.7  395.3  592.0  600.3  572.3  599.3
bot_gradual       237.0  609.3  215.7  497.0  236.3  272.7  593.3  589.7  623.7  502.3  272.0  518.3
bot_grim          259.7  892.3  206.7  490.3  277.7  292.7  593.0  627.3  429.3  243.7  289.0  283.0
bot_pavlov        442.7  789.7  119.7  586.7  153.3  348.0  571.7  498.7  402.3  566.3  423.3  567.3
bot_random        453.7  788.0  115.0  562.0  134.7  107.3  410.3  463.0  506.7  634.3  462.7  613.7
bot_soft_majority 585.0  595.7  208.7  590.3  550.3  251.0  504.0  441.7  602.0  597.0  582.0  603.0
bot_tf2t_trigger  582.3  592.3  207.7  587.0  490.7  228.7  406.3  362.7  595.3  595.0  585.7  588.7
bot_tit_for_tat   306.7  605.7  210.7  594.0  263.7  272.3  420.0  467.7  605.3  602.3  495.3  599.3
bot_tit_for_two   590.7  597.3  200.0  587.7  486.7  231.3  432.3  383.7  589.7  603.7  591.0  594.7
```

### Big movements vs Run #7
- **Soft Majority widens its lead** (509.22, +4 vs 505.48). It is the only
  reciprocator that handles Gradual gracefully: SoftMaj vs Gradual = 550.3
  (and Gradual gets a huge 623.7 from it, which actually doesn't hurt
  SoftMaj's rank because everyone gets near-ceiling from Gradual when not
  in escalation). Gradual barely perturbs SoftMaj because SoftMaj's
  majority test doesn't escalate.
- **TF2T holds #2** (490.72, ≈unchanged). TF2T's two-D-in-a-row threshold
  means Gradual's bursts of single D's mostly don't trigger TF2T, so
  TF2T vs Gradual = 486.7 (reasonable). Gradual gets 518.3 from TF2T.
- **tf2t_trigger climbs to #3** (485.19, +0). Same TF2T resilience as
  vanilla TF2T plus the (rarely-firing) AllD detector. Gets 490.7 vs
  Gradual, basically TF2T-level.
- **GTFT drops from #3 to #4** (463.64, −28). GTFT's probabilistic
  forgiveness collides badly with Gradual's escalating retaliation:
  GTFT vs Gradual = only 162.0! Gradual punishes GTFT's noise-induced
  D harder each time, and GTFT's random forgiveness occasionally hands
  Gradual another easy round. Catastrophic pairing.
- **TFT drops to #7** (453.58, −17). Same escalation problem: TFT vs
  Gradual = 263.7. Each TFT mirror of our retaliation gets escalated.
- **AllC jumps to #5** (457.78, +11). Gradual scores 609 from AllC and
  AllC scores 577.7 from Gradual — Gradual hands AllC near-ceiling
  because it never has a *reason* to defect against AllC (besides 2%
  noise flips of AllC's C → D in the record).
- **Pavlov drops to #6** (455.81, −28). Pavlov vs Gradual = only 153.3.
  Pavlov's classic D-probe-after-noise-loss triggers Gradual's escalation;
  Pavlov's "lose-shift" cycles back to C briefly but Gradual is still in
  retaliation phase, so Pavlov keeps eating sucker payoffs.
- **Top 3 changed** (Runs #6/#7 top 3 set = {SoftMaj, GTFT, TF2T};
  Run #8 set = {SoftMaj, TF2T, tf2t_trigger}). Stability counter resets.

### Notable pairings involving gradual
- **gradual vs gradual (self-play): 236.3** — the strategy's biggest
  weakness. Under 2% noise, the first flipped move triggers a 1-D
  retaliation. Both sides see opp's D, escalate to longer retaliations,
  and the calming C's get washed out by fresh flips. Far below
  TFT-vs-TFT (495.3), let alone TF2T-vs-TF2T (594.7).
- **gradual vs TFT: 272.0 / 263.7** — symmetric escalation. The 2 calming
  C's help slightly, but each noise flip can restart the spiral.
- **gradual vs adaptive_tft: 237.0 / 237.0** — adaptive_tft's lock-D
  trigger fires on our retaliation streaks. Once locked, gradual sees
  pure D and stays in retaliation forever. Mutual DD ≈ 200 + variance.
- **gradual vs GTFT: 497.0 / 162.0** — asymmetric disaster. GTFT's
  occasional D (from real defection + 10% noise forgiveness sometimes
  giving up retaliation) feeds gradual's escalation; gradual keeps
  punishing while GTFT keeps offering olive branches that get eaten.
- **gradual vs soft_majority: 623.7 / 550.3** — best matchup for gradual.
  Soft majority shrugs off our retaliation bursts (a few extra D's
  don't flip the majority of opp_history). We harvest near-ceiling
  from soft_majority's continued C's during our calming phases.
- **gradual vs Pavlov: 593.3 / 153.3** — gradual's #2 strongest score.
  Pavlov's D-after-loss probing gets escalated punishment; gradual rides
  through Pavlov's lose-shift cycles getting many T's.
- **gradual vs Random: 589.7 / 134.7** — similar story. Random's frequent
  D's get escalated punishment; Random's C's during our retaliation give
  us T's.
- **gradual vs AllD: 215.7 / 212.3** — fine, ≈ TFT-level. The escalation
  doesn't help because we can't retaliate harder than always-D.
- **gradual vs Grim: 272.7 / 277.7** — also fine. Once Grim is tripped
  by our retaliation, both lock to D.

### Verdict on gradual
A genuine high-variance strategy. Average rank #10 hides huge
matchup-dependent swings: gradual wins big against
patient/forgiving/lose-shift opponents (SoftMaj, Pavlov, Random, AllC
all near 590+) and loses badly against escalating reciprocators (self,
TFT, adaptive_tft all near 235-272). Its biggest "win" is actually
collateral damage to the field: by punishing GTFT and Pavlov badly,
it knocks both out of the top tier and lets the patient strategies
widen their lead.

In a noiseless world Gradual's escalation is a textbook deterrent. In
a 2% noise world, escalation triggers on every flip and the
self-poisoning self-play kills its average. Classic Axelrod-era result
that Gradual underperforms in noisy fields.

---

## Run #9 — 2026-05-18 — Run #8 + adaptive_pavlov (Pavlov + K=8 AllD lock)

Params: `rounds=200 noise=0.02 repeat=3 seed=42`
Bots (13): all of the above + `bot_adaptive_pavlov`.

### Ranking
| #  | Bot                  | Avg score |
|----|----------------------|-----------|
| 1  | bot_soft_majority    | 493.74    |
| 2  | bot_tit_for_two_tats | 483.59    |
| 3  | bot_tf2t_trigger     | 481.15    |
| 4  | bot_adaptive_pavlov  | 474.31    |
| 5  | bot_generous_tft     | 469.00    |
| 6  | bot_pavlov           | 464.97    |
| 7  | bot_tit_for_tat      | 452.26    |
| 8  | bot_adaptive_tft     | 447.95    |
| 9  | bot_always_c         | 440.38    |
| 10 | bot_random           | 436.41    |
| 11 | bot_gradual          | 423.92    |
| 12 | bot_grim             | 398.56    |
| 13 | bot_always_d         | 357.95    |

### Matrix (row gets these points vs column)
```
                      adap_p adap_t allc   alld   gtft   grad   grim   pav    rand   soft   tf2t_t tft    tf2t
bot_adaptive_pavlov   585.0  473.3  831.7  193.7  580.0  255.3  211.7  581.7  480.3  399.7  571.0  438.0  564.7
bot_adaptive_tft      478.3  367.7  608.3  216.3  595.0  237.0  249.7  457.7  475.3  603.3  605.7  328.3  600.7
bot_always_c          231.7  578.3  591.0   23.7  583.3  577.7  144.0  311.3  308.0  597.3  600.7  584.0  594.0
bot_always_d          250.3  214.7  970.3  217.3  466.7  212.3  216.7  591.3  586.7  218.7  229.3  239.0  240.0
bot_generous_tft      533.3  575.0  601.7  146.7  585.3  162.0  207.0  526.7  395.3  592.0  600.3  572.3  599.3
bot_gradual           343.7  237.0  609.3  215.7  497.0  236.3  272.7  593.3  589.7  623.7  502.3  272.0  518.3
bot_grim              296.7  259.7  892.3  206.7  490.3  277.7  292.7  593.0  627.3  429.3  243.7  289.0  283.0
bot_pavlov            575.0  442.7  789.7  119.7  586.7  153.3  348.0  571.7  498.7  402.3  566.3  423.3  567.3
bot_random            422.0  453.7  788.0  115.0  562.0  134.7  107.3  410.3  463.0  506.7  634.3  462.7  613.7
bot_soft_majority     308.0  585.0  595.7  208.7  590.3  550.3  251.0  504.0  441.7  602.0  597.0  582.0  603.0
bot_tf2t_trigger      432.7  582.3  592.3  207.7  587.0  490.7  228.7  406.3  362.7  595.3  595.0  585.7  588.7
bot_tit_for_tat       436.3  306.7  605.7  210.7  594.0  263.7  272.3  420.0  467.7  605.3  602.3  495.3  599.3
bot_tit_for_two_tats  398.0  590.7  597.3  200.0  587.7  486.7  231.3  432.3  383.7  589.7  603.7  591.0  594.7
```

### adaptive_pavlov vs plain Pavlov diff (per opponent)
| Opponent           | Pavlov | AdaptPav | Δ      |
|--------------------|--------|----------|--------|
| AllC               | 789.7  | 831.7    | +42.0  | (noise variance in match-key seed; ~ceiling either way)
| AllD               | 119.7  | 193.7    | **+74.0**  | ✓ main goal: AllD-detect activates ~round 8
| TFT                | 423.3  | 438.0    | +14.7  | (same Pavlov behaviour; minor variance)
| TF2T               | 567.3  | 564.7    | -2.6   | ≈ same
| GTFT               | 586.7  | 580.0    | -6.7   | ≈ same
| Grim               | 348.0  | 211.7    | **-136.3** | ✗ Pavlov was *exploiting* tripped-Grim by cycling C/D; lock-D kills the exploit
| Pavlov             | 571.7  | 581.7    | +10.0  | ≈ same (the original Pavlov in this row)
| Random             | 498.7  | 480.3    | -18.4  | small loss to occasional false triggers
| soft_majority      | 402.3  | 399.7    | -2.6   | ≈ same
| adaptive_tft       | 442.7  | 473.3    | +30.6  | both have lock-D; we lock earlier or vice versa, net symmetric
| tf2t_trigger       | 566.3  | 571.0    | +4.7   | ≈ same
| gradual            | 153.3  | 255.3    | **+102.0** | ✓ early lock-D ends gradual's exploit phase
| self vs self       | 571.7  | 585.0    | +13.3  | near-ceiling either way

Net: avg score 464.97 vs 474.31 → **+9.3 per match**. Lock helps massively
vs AllD (+74) and gradual (+102), hurts massively vs Grim (-136). On
balance positive in this 13-bot field.

### Top 3 stability
- Run #7: {soft_majority, GTFT, tit_for_two_tats}
- Run #8: {soft_majority, tit_for_two_tats, tf2t_trigger}
- Run #9: {soft_majority, tit_for_two_tats, tf2t_trigger} ← same as Run #8

**Stability counter = 2** (Run #8 and Run #9 have the same top-3 set).
Need one more run with the same top-3 to satisfy "three runs in a row".

### Custom-bot count
1. bot_pavlov, 2. bot_generous_tft, 3. bot_tit_for_two_tats,
4. bot_adaptive_tft, 5. bot_soft_majority, 6. bot_tf2t_trigger,
7. bot_gradual, 8. bot_adaptive_pavlov → **8/10**. Need 2 more.

---

## Run #10 — 2026-05-18 — Run #9 + prober (Axelrod-style probe-then-policy)

Params: `rounds=200 noise=0.02 repeat=3 seed=42`
Bots (14): all of the above + `bot_prober`.

### Ranking
| #  | Bot                  | Avg score |
|----|----------------------|-----------|
| 1  | bot_soft_majority    | 500.31    |
| 2  | bot_adaptive_pavlov  | 470.62    |
| 3  | bot_generous_tft     | 465.90    |
| 4  | bot_tit_for_two_tats | 463.57    |
| 5  | bot_pavlov           | 462.07    |
| 6  | bot_tf2t_trigger     | 461.95    |
| 7  | bot_tit_for_tat      | 455.52    |
| 8  | bot_adaptive_tft     | 443.69    |
| 9  | bot_random           | 429.52    |
| 10 | bot_gradual          | 414.12    |
| 11 | bot_always_c         | 410.71    |
| 12 | bot_prober           | 408.26    |
| 13 | bot_grim             | 386.17    |
| 14 | bot_always_d         | 349.43    |

### Matrix (row gets these points vs column)
```
                      adap_p adap_t allc   alld   gtft   grad   grim   pav    prob   rand   soft   tf2t_t tft    tf2t
bot_adaptive_pavlov   585.0  473.3  831.7  193.7  580.0  255.3  211.7  581.7  422.7  480.3  399.7  571.0  438.0  564.7
bot_adaptive_tft      478.3  367.7  608.3  216.3  595.0  237.0  249.7  457.7  388.3  475.3  603.3  605.7  328.3  600.7
bot_always_c          231.7  578.3  591.0   23.7  583.3  577.7  144.0  311.3   25.0  308.0  597.3  600.7  584.0  594.0
bot_always_d          250.3  214.7  970.3  217.3  466.7  212.3  216.7  591.3  238.7  586.7  218.7  229.3  239.0  240.0
bot_generous_tft      533.3  575.0  601.7  146.7  585.3  162.0  207.0  526.7  425.7  395.3  592.0  600.3  572.3  599.3
bot_gradual           343.7  237.0  609.3  215.7  497.0  236.3  272.7  593.3  286.7  589.7  623.7  502.3  272.0  518.3
bot_grim              296.7  259.7  892.3  206.7  490.3  277.7  292.7  593.0  225.0  627.3  429.3  243.7  289.0  283.0
bot_pavlov            575.0  442.7  789.7  119.7  586.7  153.3  348.0  571.7  424.3  498.7  402.3  566.3  423.3  567.3
bot_prober            424.3  385.0  960.0  200.3  550.7  276.7  210.0  422.7  221.7  485.0  597.3  235.7  496.3  250.0
bot_random            422.0  453.7  788.0  115.0  562.0  134.7  107.3  410.3  340.0  463.0  506.7  634.3  462.7  613.7
bot_soft_majority     308.0  585.0  595.7  208.7  590.3  550.3  251.0  504.0  585.7  441.7  602.0  597.0  582.0  603.0
bot_tf2t_trigger      432.7  582.3  592.3  207.7  587.0  490.7  228.7  406.3  212.3  362.7  595.3  595.0  585.7  588.7
bot_tit_for_tat       436.3  306.7  605.7  210.7  594.0  263.7  272.3  420.0  498.0  467.7  605.3  602.3  495.3  599.3
bot_tit_for_two_tats  398.0  590.7  597.3  200.0  587.7  486.7  231.3  432.3  203.3  383.7  589.7  603.7  591.0  594.7
```

### Prober's per-opponent scores (sanity)
| Opponent           | Prober | Opp's | Prediction matched? |
|--------------------|--------|-------|---------------------|
| AllC               | 960.0  | 25.0  | ✓ ~996 expected (exploit sucker) |
| AllD               | 200.3  | 238.7 | ✓ ~198 (TFT after probe, lost 2 sucker rounds) |
| TFT                | 496.3  | 498.0 | ✓ ~495 (TFT-vs-TFT under noise) |
| TF2T               | 250.0  | 203.3 | ✓ exploit hit (TF2T tolerates 1 D so we got 2 sucker rounds, then locked D) |
| GTFT               | 550.7  | 425.7 | partial exploit (GTFT's 10% forgive rate let us get some sucker rounds) |
| Grim               | 210.0  | 225.0 | ✓ ~200 (locked-D after Grim tripped) |
| Pavlov             | 422.7  | 424.3 | ≈ TFT-vs-Pavlov (~420) |
| soft_majority      | 597.3  | 585.7 | best non-AllC matchup: softmaj forgives one D in opening, then we play TFT and cooperate |
| adaptive_tft       | 385.0  | 388.3 | adaptive_tft's lock-D mode fired vs our defection probe, mutual D for late rounds |
| adaptive_pavlov    | 424.3  | 422.7 | ≈ Pavlov: AllD detector doesn't fire on TFT-mode prober |
| tf2t_trigger       | 235.7  | 212.3 | similar to TF2T but trigger's window-D detector probably fired during exploit phase |
| gradual            | 276.7  | 286.7 | gradual's escalation triggered on our probe D; ~mutual punishment |
| Random             | 485.0  | 340.0 | TFT-vs-Random with a 2-sucker handicap |
| Prober (self)      | 221.7  | 213.3 | ✓ self-play disaster (both verdict-exploit each other → mutual D) |

### Top 3 stability
- Run #8: {soft_majority, tit_for_two_tats, tf2t_trigger}
- Run #9: {soft_majority, tit_for_two_tats, tf2t_trigger}
- Run #10: {soft_majority, adaptive_pavlov, generous_tft} ← **CHANGED**

**Stability counter resets to 1.** Adding prober pushed TF2T (→#4) and
tf2t_trigger (→#6) out of the top 3. They both got exploited by Prober
for sucker payoffs (TF2T: 203, tf2t_trigger: 212). adaptive_pavlov and
GTFT climbed because they didn't get exploited as hard (~423 and 425
respectively).

### Custom-bot count
1. bot_pavlov, 2. bot_generous_tft, 3. bot_tit_for_two_tats,
4. bot_adaptive_tft, 5. bot_soft_majority, 6. bot_tf2t_trigger,
7. bot_gradual, 8. bot_adaptive_pavlov, 9. bot_prober → **9/10**.
Need 1 more for the STOP criterion.

### Headline story
**Prober demonstrates the "exploit-but-stay-honest" middle path is
hard.** Prober itself ranks #12 (408) because its self-play is awful
(221.7 — both copies misclassify each other as suckers) and it loses
mutual-cooperation payoffs against every reciprocator. But it
*reshuffles* the top of the field: any patient/forgiving bot that
tolerates one D (TF2T, tf2t_trigger, GTFT) becomes prey to Prober.
The new top 3 is dominated by strategies that *retaliate quickly
enough* in rounds 2-3 to fail Prober's "sucker test":
- **soft_majority** plays D in rounds 2-3 (count of opp D > count of
  opp C after the probe), so Prober drops it into TFT mode early.
- **adaptive_pavlov** plays D in rounds 2-3 (Pavlov: D after losing
  round 1, D again after losing round 2), passes the test.
- **GTFT** mostly defects in rounds 2-3 (90% retaliation rate), passes
  the test most of the time.

So Prober selects *against* "forgive one D" strategies and *for*
"react quickly to the first D" strategies, even at the cost of more
noise vendettas. **This is a classic real-world finding**: in
populations that include probers/testers, an "open-handed" cooperator
gets eaten alive; a "you have to earn my trust" cooperator survives.
Compare with social-trust dynamics: communities with high baseline
predation evolve to "guilty until proven innocent" defaults, while
low-predation communities can afford "innocent until proven guilty".

---

## Run #11 — 2026-05-18 — Run #10 + firm_tf2t (anti-prober TF2T)

Params: `rounds=200 noise=0.02 repeat=3 seed=42`
Bots (15): all of the above + `bot_firm_tf2t`.

### Ranking
| #  | Bot                  | Avg score |
|----|----------------------|-----------|
| 1  | bot_soft_majority    | 506.51    |
| 2  | bot_firm_tf2t        | 502.53    |
| 3  | bot_adaptive_pavlov  | 477.78    |
| 4  | bot_generous_tft     | 475.07    |
| 5  | bot_tit_for_two_tats | 472.42    |
| 6  | bot_tf2t_trigger     | 470.73    |
| 7  | bot_pavlov           | 468.56    |
| 8  | bot_tit_for_tat      | 465.29    |
| 9  | bot_adaptive_tft     | 454.18    |
| 10 | bot_random           | 442.42    |
| 11 | bot_always_c         | 423.07    |
| 12 | bot_prober           | 420.91    |
| 13 | bot_gradual          | 414.76    |
| 14 | bot_grim             | 388.11    |
| 15 | bot_always_d         | 342.71    |

### Matrix (row gets these points vs column)
```
                      adap_p adap_t allc   alld   firm   gtft   grad   grim   pav    prob   rand   soft   tf2t_t tft    tf2t
bot_adaptive_pavlov   585.0  473.3  831.7  193.7  578.0  580.0  255.3  211.7  581.7  422.7  480.3  399.7  571.0  438.0  564.7
bot_adaptive_tft      478.3  367.7  608.3  216.3  601.0  595.0  237.0  249.7  457.7  388.3  475.3  603.3  605.7  328.3  600.7
bot_always_c          231.7  578.3  591.0   23.7  596.0  583.3  577.7  144.0  311.3   25.0  308.0  597.3  600.7  584.0  594.0
bot_always_d          250.3  214.7  970.3  217.3  248.7  466.7  212.3  216.7  591.3  238.7  586.7  218.7  229.3  239.0  240.0
bot_firm_tf2t         478.0  587.7  594.3  205.3  593.0  590.0  388.7  380.3  389.3  586.3  369.7  598.3  598.7  583.7  594.7
bot_generous_tft      533.3  575.0  601.7  146.7  603.3  585.3  162.0  207.0  526.7  425.7  395.3  592.0  600.3  572.3  599.3
bot_gradual           343.7  237.0  609.3  215.7  423.7  497.0  236.3  272.7  593.3  286.7  589.7  623.7  502.3  272.0  518.3
bot_grim              296.7  259.7  892.3  206.7  415.3  490.3  277.7  292.7  593.0  225.0  627.3  429.3  243.7  289.0  283.0
bot_pavlov            575.0  442.7  789.7  119.7  559.3  586.7  153.3  348.0  571.7  424.3  498.7  402.3  566.3  423.3  567.3
bot_prober            424.3  385.0  960.0  200.3  598.0  550.7  276.7  210.0  422.7  221.7  485.0  597.3  235.7  496.3  250.0
bot_random            422.0  453.7  788.0  115.0  623.0  562.0  134.7  107.3  410.3  340.0  463.0  506.7  634.3  462.7  613.7
bot_soft_majority     308.0  585.0  595.7  208.7  593.3  590.3  550.3  251.0  504.0  585.7  441.7  602.0  597.0  582.0  603.0
bot_tf2t_trigger      432.7  582.3  592.3  207.7  593.7  587.0  490.7  228.7  406.3  212.3  362.7  595.3  595.0  585.7  588.7
bot_tit_for_tat       436.3  306.7  605.7  210.7  602.0  594.0  263.7  272.3  420.0  498.0  467.7  605.3  602.3  495.3  599.3
bot_tit_for_two_tats  398.0  590.7  597.3  200.0  596.3  587.7  486.7  231.3  432.3  203.3  383.7  589.7  603.7  591.0  594.7
```

### firm_tf2t per-opponent (compare to plain TF2T)
| Opponent           | firm_tf2t | plain TF2T | Δ      |
|--------------------|-----------|------------|--------|
| AllC               | 594.3     | 597.3      | -3.0   | ≈ same, near-ceiling
| AllD               | 205.3     | 200.0      | +5.3   | TFT-phase costs one fewer sucker round
| TFT                | 583.7     | 591.0      | -7.3   | TFT-phase amplifies noise vendettas a bit early
| TF2T               | 594.7     | 594.7      | 0      | no first defectors here, identical
| GTFT               | 590.0     | 587.7      | +2.3   | ≈ same
| Grim               | 380.3     | 231.3      | **+149.0** | ✓ TFT-phase mirrors Grim's first D after a noise-flip, both lock symmetrically; we don't eat the long tail of sucker rounds TF2T does
| Pavlov             | 389.3     | 432.3      | -43.0  | Pavlov's win-stay/lose-shift triggers more cycles with TFT-phase noise punishment
| Prober             | **586.3** | **203.3**  | **+383.0** | ✓ MAIN GOAL: round-2 retaliation defeats Prober's sucker test → mutual TFT cooperation
| Random             | 369.7     | 383.7      | -14.0  | TFT-phase punishes random D's too aggressively
| soft_majority      | 598.3     | 589.7      | +8.6   | very mild gain
| tf2t_trigger       | 598.7     | 603.7      | -5.0   | ≈ same
| adaptive_tft       | 587.7     | 590.7      | -3.0   | ≈ same
| adaptive_pavlov    | 478.0     | 398.0      | **+80.0**  | TFT-phase prevents adaptive_pavlov's K=8 AllD-lock from firing; mutual reciprocation holds
| gradual            | 388.7     | 486.7      | **-98.0**  | TFT-phase punishes gradual's escalation strictly; gradual amplifies into long mutual-D vs TF2T's "wait it out"
| firm_tf2t (self)   | 593.0     | —          | —      | near-ceiling, noise-resistant in TF2T phase

**Net average: 502.5 vs TF2T's 472.4 → +30.1 per match.** firm_tf2t is
the second-best bot overall.

The biggest improvement is **vs Prober (+383)** — exactly what the
bot was designed to fix. Secondary improvements vs Grim (+149) and
adaptive_pavlov (+80) compensate for losses vs Pavlov (-43) and
Gradual (-98).

### Top 3 stability
- Run #9: {soft_majority, tit_for_two_tats, tf2t_trigger}
- Run #10: {soft_majority, adaptive_pavlov, generous_tft}
- Run #11: {soft_majority, firm_tf2t, adaptive_pavlov} ← **CHANGED again**

**Stability counter resets to 1.** firm_tf2t (a brand-new bot) took
the #2 slot, displacing GTFT. The set partially overlaps with Run
#10 ({soft_majority, adaptive_pavlov} survive) but the new bot
moved in.

### Robustness check across seeds (same 15-bot field)
- seed=42: 1.soft_majority 2.firm_tf2t 3.adaptive_pavlov
- seed=43: 1.soft_majority 2.firm_tf2t 3.adaptive_pavlov ← same
- seed=44: 1.soft_majority 2.firm_tf2t 3.tf2t_trigger    ← differs at #3

Top-2 (soft_majority + firm_tf2t) is rock-solid across seeds. The #3
slot is contested between adaptive_pavlov, tf2t_trigger, and
generous_tft — they cluster around ~475-490, within noise of each
other. With current `repeat=3` averaging, RNG luck moves them.

### Custom-bot count
1. bot_pavlov, 2. bot_generous_tft, 3. bot_tit_for_two_tats,
4. bot_adaptive_tft, 5. bot_soft_majority, 6. bot_tf2t_trigger,
7. bot_gradual, 8. bot_adaptive_pavlov, 9. bot_prober,
10. bot_firm_tf2t → **10/10**. Bot-count criterion satisfied.

### Headline story
**firm_tf2t resolves the noise/probe tension** — partially. By being
TFT-strict in rounds 1-5 and TF2T-tolerant from round 6, it
sidesteps Prober's sucker test (the test happens in the strict
phase) while keeping most of TF2T's noise-tolerance for the long
late-game. The trade-off is a 5-round "vendetta window" against any
bot that defects early due to escalation or noise (Gradual, Pavlov);
the gains vs Prober and Grim more than compensate.

This is the first bot in the field engineered *specifically* to
counter another bot (Prober). The result confirms a general
pattern: when you can predict the threat model, a small targeted
defence (5 strict rounds) buys disproportionate benefit (~+30 avg
score). Natural follow-up: can a *better* Prober beat firm_tf2t by
extending its probe window past round 5?
