# Strategy notes

What works, what doesn't, and why. Append-only; each section is one tournament.

---

## After Run #1 (reference pantheon)

### Why Grim leads (461.6)
- Crushes AllC (892.3) and Random (627.3) with pure cooperation — both opponents
  hand it free CC streaks because neither punishes anything.
- Holds AllD to a draw (206.7) — both end up locked in DD which is ≈P=1 per round.
- The price it pays is self-play (292.7) and TFT-play (272.3): a single noise
  flip turns the entire rest of the match into DD. Without noise Grim self-play
  would be ~600.

### Why AllD is right behind (446.0)
- Free exploitation against AllC (970.3) and Random (586.7) is just too lucrative.
- The cost — being permanently distrusted by Grim and partly by TFT — only
  bites in two of the five matchups.
- AllD wins individual matches a lot, but it cannot achieve the >3-per-round
  ceiling that mutual cooperators reach with each other. In a population
  saturated with reciprocators, AllD's advantage evaporates.

### Why TFT is "only" 3rd at this noise level (410.3)
- TFT vs TFT under noise is the famous "vendetta": a flip from C→D triggers
  an alternating CD/DC ping-pong worth (5+0)/2 = 2.5 per round, well below
  CC=3. TFT-clones average 495 per 200 rounds (~2.48/round) where lossless
  mutual C would give 600.
- Against AllD, TFT loses 1 sucker payoff in round 1 and then mirrors forever
  — basically a draw (210.7).
- TFT's strength is that it never gets exploited *long term*, but it is
  cursed in noisy environments.

### Why Random and AllC fall to the bottom
- Random hands out free defections (-3 per surprise D against cooperators)
  and free cooperations (-5 per surprise C against defectors). It can't
  build a reputation either way.
- AllC is the textbook sucker. Its self-play (591) and TFT-play (584) are
  great, but a single AllD opponent destroys its average.

### Take-aways for next iteration
1. Grim's fragility under noise is the obvious place to attack — build
   forgiving variants.
2. Need a strategy that recognises AllD and stops handing it free C's
   while still cooperating with reciprocators.
3. Pavlov / Win-Stay-Lose-Shift might handle noise better than TFT because
   it self-corrects after a single bad round.

---

## After Run #2 (+pavlov)

### Pavlov debuts at #3 (458.5)
- Best non-trivial self-play in the field: 571.7 / 600. A noise flip
  produces DD, both Pavlov agents lose-shift to C in the same step,
  and CC resumes immediately. This is the classic noise-correction
  property that makes WSLS shine in stochastic environments.
- Strong vs Random (498.7) and vs AllC (789.7).
- **Weakness**: Pavlov is gameable by AllD (119.7). Every other round
  Pavlov re-offers C after a forced DD shift, and AllD just keeps
  pocketing the 5. TFT against AllD scores 210 — much better — because
  TFT mirrors D forever after the first defection.
- **Weakness**: Pavlov vs Grim is asymmetric (348 vs 593). Pavlov's
  occasional probing D (after a noise-induced loss) is unforgivable to
  Grim. Pavlov loses 245 points compared to Grim's mirror match.

### Why Grim still leads (483.5)
- Adding Pavlov as opponent gives Grim *another* mostly-cooperating
  victim (593 vs Pavlov). Grim's win-rate from naive cooperators only
  grew with the new entrant.
- Grim has not faced a strategy yet that explicitly punishes "permanent
  hatred". A "remorseful" or "contrite TFT" might break its rule by
  re-cooperating to test if the other side has cooled down.

### Take-aways for next iteration
1. Need a Pavlov-killer that exploits its cycle-of-forgiveness against
   defectors. **Tit-for-Two-Tats** is the textbook candidate: it
   tolerates a single defection (so noise doesn't trigger a vendetta)
   but breaks Pavlov's cycle because Pavlov never gets two D's in a row
   "for free" from it — wait, actually TF2T might *give* Pavlov free C's.
   Probably better: a forgiving TFT that occasionally offers an olive
   branch even mid-vendetta.
2. **Generous TFT** is the obvious next step: TFT but with a small
   probability of forgiving a defection. Should beat plain TFT under
   noise without losing too much to AllD.
3. Need an AllD-detector. A "TFT that escalates to permanent D after
   N straight D's" would catch the Pavlov exploit and still cooperate
   with reciprocators.

---

## After Run #3 (+generous_tft, p=1/3)

### GTFT debuts at #5 (433.57) — below plain TFT
- **Self-play and cross-play with cooperators are excellent:** GTFT-GTFT
  585, GTFT-TFT 572, GTFT-Pavlov 526. These are all 70–100 points above
  TFT's equivalents. The vendetta loop is broken.
- **AllD exploitation hurts:** 146.7 vs AllD vs TFT's 210.7 — a 64-point
  hole. With AllD being 1/7 of the field, the per-bot cost is ~9 points;
  with TFT being 1/7, GTFT loses ~3 points there (GTFT 572 vs TFT 605
  in TFT's perspective). Net headline cost ~6 points overall.
- The 1/3 forgiveness rate is the textbook optimum for an evolutionary
  population *without* AllD-types. In a mixed field with non-trivial AllD
  share, it's too generous.

### Why Grim still leads (484.48)
- Yet another forgiving reciprocator in the field gave Grim more
  cooperation to drink from (Grim-GTFT 490 from Grim's side).
- Grim's lead over Pavlov is now razor-thin (~8 points). One more
  cooperative bot and Pavlov might catch up.

### Pavlov rises to #2 (476.81)
- Same effect — Pavlov harvests GTFT well (586 vs GTFT), and its main
  weakness vs AllD (119.7) still costs it, but it now mostly cooperates
  with the rest of the field.
- Pavlov is gaining ground on Grim as the population diversifies.

### Take-aways for next iteration
1. **GTFT-light**: a lower forgiveness rate, say p ≈ 0.1, would cap the
   AllD damage. Worth trying if we expect AllD-type opponents.
2. **Tit-for-Two-Tats** (TF2T): waits for *two* consecutive D's before
   retaliating. Solves the noise problem differently (no forgiveness
   probability, just a hysteresis of length 2). Should be tested before
   we commit GTFT-style probabilistic forgivers.
3. **Contrite TFT**: TFT but if I defected last round on a cooperator
   (i.e. I was the noise victim), I apologize with a C. This targets
   the noise vendetta *from the apologetic side* and should beat plain
   TFT while still being unforgiving to true defectors.
4. **AllD-detector / "trigger-N"**: after N consecutive opponent D's
   (say N=5), permanently switch to D. Robust to noise (a single flip
   doesn't trip the trigger) but unbeatable by AllD.

---

## After Run #4 (+tit_for_two_tats)

### TF2T debuts at #5 (452.25) — middle of the pack, but field-shifter
- **Self-play near-ceiling:** TF2T-TF2T = 594.7 / 600. Even better than
  Pavlov's 571.7 and GTFT's 585.3. Two noise flips on the same side
  *in a row* are extremely rare (~0.04%), so retaliation almost never
  happens between two TF2Ts.
- **Cross-play with reciprocators excellent:** TF2T-TFT = 591/599,
  TF2T-GTFT = 587/599. The single-D hysteresis kills noise vendettas
  on both sides.
- **vs AllD: 200** — only ~10 points worse than TFT (210). The first
  two rounds are sucker rounds (S=0), then TF2T mirrors D forever at
  P=1. Cost is bounded by the hysteresis size, NOT proportional to
  forgiveness rate as in GTFT. This is the key TF2T strength.
- **vs Pavlov: 432 vs 567** — the textbook TF2T weakness shows up.
  Pavlov's "occasional D after a noise-loss" probe is forgiven by TF2T
  on the first round, Pavlov pockets a T=5, then Pavlov wins-stays
  (D after C/D), pockets another sucker. TF2T eventually retaliates
  after two consecutive D's, Pavlov lose-shifts to C, TF2T forgives.
  Net: Pavlov nets ~1 extra T per cycle that TFT wouldn't grant.
- **vs Grim: 231 vs 283** — also worse than TFT. Once Grim trips
  (noise), TF2T eats an extra sucker round before locking to D.

### Why the leaderboard reshuffled so much
Adding one mostly-cooperative non-vindictive bot (TF2T) to the field:
- **Inflates cooperators' averages** (Pavlov, TFT, GTFT all gain
  20–30 points). They harvest near-ceiling scores from TF2T.
- **Cuts AllD's average** by 29 points. AllD only gets 200 from TF2T,
  far below its harvest from the naive AllC (970) and Random (586).
  The field is "less juicy" for hawks.
- **Cuts Grim's average** by 25 points. Grim's permanent-D after a
  noise trip turns into mutual DD with TF2T, an extra ~190 rounds at
  P=1 each, vs the CC bonanza Grim is missing.

This is exactly the Axelrod evolutionary effect: a population enriched
with reciprocators makes life easier for cooperators and harder for
defectors. Pavlov's lead now (488) over Grim/TFT (~459) is statistically
real (~30-point gap with ~10-point per-match noise).

### Take-aways for next iteration
1. **Pavlov-killer**: TF2T can't punish Pavlov's "probe-D-after-loss"
   because Pavlov spaces its defections out. A variant of TFT or TF2T
   that also tracks "did opponent recently exploit my forgiveness?"
   could catch Pavlov. **Contrite TFT** alone won't help (Pavlov isn't
   the noise victim). Maybe a "TFT-with-suspicion" that escalates
   tolerance based on T's received vs given.
2. **Trigger-N / AllD-detector** is still missing and would dominate
   AllD without losing self-play.
3. **GTFT-light (p=0.1)** — lower forgiveness rate to cap AllD exposure.
4. **Pavlov-variants**: maybe a "two-step" Pavlov that needs two
   consecutive losses to shift, mirroring the TF2T idea on the
   Pavlov side. Should be more stable against Grim and AllD.

---

## After Run #5 (+adaptive_tft, WINDOW=10 THRESHOLD=7)

### Adaptive_TFT debuts at #7 (433.22) — below plain TFT (441.30)
A negative result, and an instructive one.

The strategy is plain TFT with one extra rule: after the opponent has
defected in ≥7 of the last 10 rounds, switch to permanent D. The intent
was to keep all of TFT's behaviour against reciprocators while putting
a hard cap on AllD exploitation.

What happened in practice:
- **vs AllD:** worked as designed. AllD trips the trigger by round 11
  and from then on it's mutual DD. Score 216.3 — only 5 points better
  than TFT's 210.7. Net gain too small to matter.
- **vs cooperators (AllC, GTFT, TF2T):** trigger never fires; behaviour
  identical to TFT. Scores 608 / 595 / 600.
- **Catastrophic self-play and TFT-cross-play under noise.** This is
  the killer. Self-play 367.7, vs-TFT 328.3, both far worse than
  TFT-vs-TFT (495.3) and TFT-vs-adaptive_TFT.

Why does noise breaks self-play? Two failure modes compound:
1. The TFT vendetta begins normally after a noise flip — alternating
   CD/DC at 2.5 points/round.
2. *Further* noise flips during the vendetta convert some C's into D's,
   pushing the 10-round window above 7 defections on one side. That
   side locks to permanent D. The other side now sees an all-D stream
   and locks to D within 10 rounds. Final: ~30 rounds of CC at the
   start, ~170 rounds of DD ≈ 260, plus some early-vendetta variance.

The combination of (a) noise-vendetta and (b) a window-based
escalator is unstable. Each by itself is bearable; together they form
a positive feedback loop into mutual D.

### Key insight: trigger needs a hysteresis-tolerant base
If the base strategy is TF2T instead of TFT, the noise vendetta never
starts in the first place — so the trigger only fires when the opponent
genuinely defects many times. The fix is a "trigger-N with TF2T base",
to be tried next.

Alternative fix: relax the trigger threshold (e.g., 9 of 10 D's
required). That's borderline equivalent to "trigger after 9 consecutive
D's", which detects AllD just as well but is even more conservative.

### Why Pavlov still leads (483.07)
Pavlov harvests another mostly-cooperative bot (adaptive_tft gives
Pavlov 457.7 — better than TFT does at 420). The gap to GTFT is now
~15 points; Pavlov is clearly the most robust strategy in this field.

### Top 3 reshuffles again (Pavlov / GTFT / TF2T)
Run #4 top 3: Pavlov / Grim / TFT. Run #5 top 3: Pavlov / GTFT / TF2T.
Grim slid from #2 to #6 (−22) because adaptive_tft's window-trigger
behaviour interacts identically badly with Grim's permanent-D lockup;
both sides get stuck in DD. TFT slid out of the top 3 because adaptive_tft
behaves like TFT against most opponents but is *worse* in self-play, so
TFT's relative ranking didn't improve; the bigger story is that GTFT
and TF2T benefited more from the new cooperative-ish bot in the field.

### Take-aways for next iteration
1. **Hard-trigger-on-TF2T-base**: same idea but with TF2T as the default
   to avoid the noise-vendetta self-defeat. Should outscore TF2T against
   AllD without losing TF2T's near-ceiling self-play.
2. **Pavlov-killer is still missing.** Pavlov's only weakness is AllD
   (119.7). Any strategy that punishes Pavlov's probing-D-after-loss
   would shift the ranking. A "Suspicious TFT" that plays D for the
   first two rounds (and then TFT) might do it — Pavlov sees mutual
   D early, lose-shifts, eventually settles, but pays an extra cost
   in the dance. Worth trying.
3. **GTFT-light (p=0.1)** still untested. Smaller forgiveness rate
   trades less AllD damage for less self-play recovery. With the field
   now containing more cooperative reciprocators, the trade may favour
   the lighter version.
4. **Note**: with 4 custom bots now (pavlov, gtft, tf2t, adaptive_tft),
   we need 6 more "non-trivial" strategies before the STOP condition
   can be considered. Aim for variety: a prober, a hard-defector
   detector with a better base, a generous-light, a Pavlov-variant,
   a majority-rule bot, a contrite TFT.

---

## After Run #6 (+soft_majority)

### Soft Majority debuts at #1 (496.33) — first new leader
A *statistical* strategy (looks at the entire opponent history, plays
C iff opponent's C-count ≥ D-count). Three structural advantages:

1. **No noise vendettas.** A single random flip doesn't shift the
   majority of the whole history. So soft_majority-vs-soft_majority is
   602.0 — the best non-AllC self-play in the field. Better than even
   TF2T's 594.7 because TF2T can still be tipped by *consecutive* noise
   flips on the same side (rare but possible), whereas soft_majority
   requires the majority of the entire history to flip.
2. **AllD-resistant.** Round 1 sucker, then opp_history is all D, so
   soft_majority plays D forever. Score 208.7 vs AllD — only ~2 points
   below TFT (210.7) and on par with TF2T (200.0).
3. **Universal cooperator against reciprocators.** Near-ceiling against
   TFT (582), GTFT (590), TF2T (603), adaptive_tft (585), tf2t_trigger
   (595). Better than any other bot at not getting drawn into vendettas.

### Why soft_majority beats Pavlov
Pavlov's main strength is "self-correction after noise" (it lose-shifts
back to C after a DD round). But Pavlov *also probes D* after any
non-CC-CC outcome — this is what makes it gameable by AllD (free T's).
Soft_majority doesn't probe; it just patiently waits for the majority
to flip. So against opponents who *do* punish probing (like soft_majority
itself, vs Pavlov: 504 to 402), it does better. Pavlov drops from #1
to #4 between Run #5 and Run #6.

### Soft Majority's weakness: Grim
Soft_majority vs Grim: **251.0**. Once Grim trips (noise flip ~round 5),
Grim plays D forever. But soft_majority's opp_history at that point has
~4 C's and 1 D, majority still C, so soft_majority keeps playing C —
eating sucker rounds until the D-count exceeds the C-count. For an
early Grim-trip this takes another ~4 sucker rounds; for a mid-match
trip (round 50) it takes 50+ sucker rounds. The damage is large in
expectation. But Grim itself is now #8 in the field (only 1/11 of
opponents), so the per-tournament cost is small.

A "Hard Majority" variant (defect on ties / start with D) would pay
less to Grim but lose to noise in self-play. Not worth trying.

### Take-aways for next iteration
1. **TF2T-with-trigger** is the obvious next "patch" — TF2T base
   avoids noise vendetta self-defeat that killed adaptive_tft. The
   trigger only fires for genuine AllD-style sustained defection.
   Should outscore TF2T against AllD and roughly match elsewhere.
2. **GTFT-light (p=0.1)** still untested. Lower forgiveness rate.
3. **Prober** — opens with D to test the opponent. Should detect
   suckers (AllC, Random) and switch to AllD; punish-back-once
   strategies revert to TFT.
4. **Contrite TFT** — apologizes for self-noise. Complicated to
   implement correctly; full Sugden good-standing tracking is
   needed (single-side CTFT doesn't actually solve noise vendetta
   when paired with plain TFT, per pen-and-paper trace).
5. **Custom count update**: 5 custom strategies now (pavlov, gtft,
   tf2t, adaptive_tft, soft_majority). Need 5 more before STOP.

---

## After Run #7 (+tf2t_trigger)

### tf2t_trigger debuts at #4 (484.70) — improvement over adaptive_tft
Same trigger idea as adaptive_tft (lock to permanent D after 9/10 recent
defections) but with TF2T as the base instead of TFT. This was the fix
recommended after Run #5. Result: self-play is now near-ceiling (595.0,
vs adaptive_tft's disastrous 367.7). The TF2T hysteresis prevents the
noise vendetta from ever starting, so the trigger never fires
incorrectly between cooperative bots.

### tf2t_trigger does NOT beat plain TF2T
- **Marginal gain vs AllD:** 207.7 vs TF2T's 200.0 (+8). Negligible
  given TF2T already locks D after 2 sucker rounds anyway.
- **Loss vs Random:** 362.7 vs TF2T's 383.7 (−21). Random's high
  D rate occasionally pushes the 10-round window above the threshold,
  triggering the permanent-D lockup. Once locked, Random's random C's
  cost us C-against-D suckers — but more importantly, Random keeps
  playing C ~50% of the time, giving Random a stream of T's against
  our D-lock. We score ~1.8/round, Random ~3.2/round.
- **Loss vs Pavlov:** 406.3 vs TF2T's 432.3 (−26). Same mechanism —
  Pavlov's D-probes plus noise occasionally trigger the lockup.

Net: tf2t_trigger trades ~8 points of AllD-gain for ~21+ points of
Random/Pavlov-loss. The trigger is a *liability* in a field where AllD
is just one of many opponents.

### Key insight: ad-hoc triggers are brittle against medium-D opponents
The whole class of "lock to D after N recent defections" strategies
shares this weakness: any opponent with persistent ~50% D rate
(Random, Pavlov occasionally) has a non-negligible chance of tripping
the trigger by random fluctuation. To beat AllD without losing to
Random, the strategy needs to *also* track context — for example, only
lock D when the opponent is *also* unresponsive to my own moves. That
gets into reactive-tester territory.

### Top 3 status
Run #6 top 3: {soft_majority, GTFT, TF2T} (in that order).
Run #7 top 3: {soft_majority, TF2T, GTFT} (with GTFT/TF2T tied within
0.03 points). The *set* is identical — 2 runs with the same top 3 as
a set. If Run #8 keeps the same set, that's three in a row and the
STOP condition for top-3 stability is met. We also need 10 custom
bots (currently 6: pavlov, gtft, tf2t, adaptive_tft, soft_majority,
tf2t_trigger) so 4 more bots are needed regardless.

### Take-aways for next iteration
1. **GTFT-light (p=0.1)** — still untested. Lower forgiveness rate
   should reduce the AllD damage (currently 146.7) toward TFT's
   210 without sacrificing too much against TFT-vs-GTFT noise rescue.
2. **Prober** — opens with D, then 2x C; if punished, behaves as TFT,
   else AllD. Could catch the field's "suckers" (AllC, Random) for
   extra points, while not getting too punished by reciprocators.
3. **Reverse TFT / Suspicious TFT** — opens with D and then TFT.
   Tests Pavlov's reaction to early D's and might catch Pavlov in
   a bad cycle.
4. **Contrite TFT** — full good-standing tracking. Could fix the
   noise vendetta in mixed TFT-CTFT play.
5. **Tester** — Axelrod's prober variant: D, C, C; if opp ever
   defects, switch to TFT; else alternate C/D forever. Designed
   to exploit overly-forgiving strategies (GTFT, TF2T, soft_majority).

---

## Run #8 — gradual (Beaufils 1996 escalating retaliation)

### Concept
Three-phase reactive: peace → escalating retaliation (N D's, where N =
total opp defections so far) → 2 calming C's → back to peace. Reset on
any new opp defection. Designed to deter probes by making each probe
more expensive than the last.

### What worked
- **vs soft_majority: 623.7** — gradual's single best matchup. SoftMaj
  shrugs off our retaliation bursts (the majority of opp_history doesn't
  flip on a few extra D's), keeps cooperating, and we harvest near-
  ceiling from the calming C phases.
- **vs Pavlov: 593.3** and **vs Random: 589.7** — escalation punishes
  their D-probes harshly; their continued C's during our calming windows
  give us T payoffs.
- **As a field perturbation:** gradual single-handedly knocked GTFT
  (#2 → #4) and Pavlov (#4 → #6) out of contention by punishing them
  so badly. This *helped* the patient strategies (soft_majority widened
  its lead).

### What didn't
- **Self-play: 236.3.** Below TFT-vs-TFT (495.3), barely above mutual
  D (200). Under 2% noise the first flipped move triggers a 1-D
  retaliation; both sides see opp's D, escalate; calming windows get
  interrupted by fresh noise flips. The strategy *cannot* coexist with
  copies of itself in a noisy environment.
- **vs TFT: 272.0** and **vs adaptive_tft: 237.0** — same escalation-
  with-a-reciprocator death spiral.
- **vs GTFT: 497.0 / 162.0** — asymmetric. GTFT keeps offering olive
  branches; gradual eats them during retaliation and the calming
  windows are too short for GTFT's rate-of-forgiveness to land.

### Why it ranks #10 not top 3
The wins (vs forgiving/lose-shift opponents) net to *less* than the
losses (vs self-copies and tight reciprocators). In a field where
3+ bots use escalation-friendly retaliation (TFT, adaptive_tft, self),
the self-poisoning self-play alone subtracts ~250 points compared
to a TF2T or SoftMaj self-play of 590+.

### Key insight: escalation is great in noiseless IPD, toxic in noisy
Beaufils's original Gradual was tested in a noiseless tournament where
escalation strictly deters probing without ever firing on accidents.
At 2% per-move noise, every match between Gradual-likes accumulates
multiple "accidental" D's that trip the escalation ladder. The 2
calming C's, originally enough to signal peace, are too short when
the next noise flip is only ~25 rounds away on average.

### Comparison with real-world analogues
Gradual is the "proportional retaliation doctrine" of Cold War
strategists (Kahn, Schelling). It works as a deterrent when the
opponent is rational, *signals are clean*, and the opponent can
distinguish "real provocation" from "accident". Under noise (= fog
of war, miscommunication, low-confidence intel), the escalation
ladder gets climbed by mistake. The Cuban Missile Crisis is the
canonical example: both sides came close to escalating in response
to a series of misinterpreted "defections" (the U-2 shootdown, the
B-59 incident). The "calming C's" map onto back-channels and hotlines
— they need to be *louder* and *longer* when the noise floor is high.

### Top 3 status
- Run #6: {soft_majority, GTFT, TF2T}
- Run #7: {soft_majority, TF2T, GTFT}  ← same set
- Run #8: {soft_majority, TF2T, tf2t_trigger}  ← *different set* (GTFT dropped, tf2t_trigger entered)

Adding gradual *changed the top-3 set* by hurting GTFT enough to push
it down to #4. Stability counter resets to 1. Need 3 more runs with
the same top-3 set before STOP. Also still need 4 more nontrivial bots
to reach the 10-custom threshold.

### Take-aways for next iteration
1. **Prober / Tester** — open with D to probe; if punished, play TFT;
   if not punished, exploit. Should beat AllC (free T's) and might
   catch SoftMaj's slow-react weakness for some extra points.
2. **Contrite TFT** — needs internal state of intended moves; might be
   borderline against API rules. Skip unless we relax the rule.
3. **OmegaTFT** — Slany & Kienzle. Detects randomness/deadlock; should
   handle Random and AllD better than plain TFT.
4. **Reverse TFT (Suspicious TFT)** — opens with D and then TFT. Useful
   data point for "how much does the opening matter" question.
5. **Lookback / Memory-N TFT** — TFT but answering not the last move
   but the most-frequent of last N moves. Like a mini-soft-majority
   with shorter horizon. Might beat soft_majority by reacting faster
   to Grim's trip.
6. **Adaptive Pavlov** — Pavlov base with "if opp always D for last K
   rounds, switch to D". Combines lose-shift recovery with AllD
   protection.

---

## Run #9 — adaptive_pavlov (Pavlov + K=8 consecutive AllD lock)

### Concept
Pavlov's win-stay-lose-shift dominates noisy cooperative matchups
(self-play near 580+, vs TFT-family near 570+) but bleeds vs AllD
(plain Pavlov scored 119.7). Adaptive Pavlov bolts on a *consecutive*-D
detector: K=8 D's in a row from the opponent → permanent D. Streak-based
(not windowed) to avoid tf2t_trigger's Random/Pavlov false-positives.

### What worked
- **vs AllD: 193.7** (+74 vs plain Pavlov). Lock fires by round 9,
  saves ~190 rounds of sucker cycling. ≈ TFT-level (210.7).
- **vs gradual: 255.3** (+102 vs plain Pavlov!). Plain Pavlov was a
  victim of gradual's escalation (153.3); adaptive_pavlov locks D
  around the time gradual's retaliation phase starts a long D streak,
  ending the exploitation.
- **vs adaptive_tft: 473.3** (+30 vs plain Pavlov, +106 vs adaptive_tft
  self-play). Both bots have lock-D triggers; the early symmetry means
  fewer wasted rounds vs adaptive_tft's vendetta.
- **Self-play: 585.0** — near-ceiling, identical to Pavlov-Pavlov. Lock
  never fires on cooperators-with-noise.
- **vs Pavlov: 581.7** — slight gain over Pavlov-Pavlov self-play
  (571.7) due to favourable match-key variance.

### What didn't
- **vs Grim: 211.7** (-136 vs plain Pavlov's 348.0). The big regression.
  Plain Pavlov *exploited* tripped-Grim by cycling C/D — Grim was already
  in permanent-D mode and didn't punish our D's, so every D turn was
  a free T=5 for us (~2.5 avg per round). Locking D throws away the
  exploit; we get mutual D ≈ 1.0/round.
- **vs Random: 480.3** (-18 vs plain Pavlov). Random's max D-streak in
  200 rounds has expected length ~log2(200) ≈ 7.6, with significant
  variance. With 2% noise on top, the trigger sometimes fires
  prematurely.

### Why it ranked #4, not top 3
The top 3 are still the patient/forgiving strategies that dominate
cooperative matchups *and* are immune to noise vendettas:
- soft_majority (493.74)
- tit_for_two_tats (483.59)
- tf2t_trigger (481.15)

Adaptive Pavlov (474.31) is right behind them. It beat plain Pavlov by
~9 points but the gap is small because Pavlov-family's biggest loss
(vs Grim's tripped state) is *converted from a tactical win to a tactical
draw* by the lock, while only AllD and Gradual yield big gains. It's
a trade, not a free improvement.

### Key insight: AllD-detection is ambiguous information
An "AllD detector" cannot tell the difference between:
1. **Rational AllD** (literally the AllD strategy): every C wasted, lock
   D saves you. Big positive.
2. **Tripped Grim** (Grim past a noise flip): looks like AllD, but
   Grim no longer punishes *new* defections by you. You can exploit
   it with C/D oscillation. Locking D wastes the exploit. Big negative.
3. **Random streak** (Random happens to hit 8 D's in a row): the next
   8 rounds will probably be a normal ~50% mix again. Locking D throws
   away an otherwise profitable matchup. Small negative.

There is no purely-passive way to distinguish these. To do so, the bot
would have to *test* with a C and see if the opponent ever cooperates
again (AllD won't, tripped-Grim won't, Random will ~50% of the time).
That's reactive-probing territory and a more complex strategy.

### Real-world parallel: "is this hostility or a misunderstanding?"
This is the same ambiguity that drives diplomatic crises. A neighbour
who hasn't returned your call in 8 days could be:
- Permanently hostile (cut them off — rational lock-D).
- Reacting to a perceived insult you didn't even know you gave them
  (apology and re-engagement is correct).
- Just busy / their phone is broken (do nothing, wait).
Without an explicit channel for clarification, you have to choose a
prior. Locking-D is a "defensive prior" — minimises worst-case loss,
maximises false-positives.

### Top 3 status
- Run #7: {soft_majority, GTFT, tit_for_two_tats}
- Run #8: {soft_majority, tit_for_two_tats, tf2t_trigger}
- Run #9: {soft_majority, tit_for_two_tats, tf2t_trigger} ← same set

**Stability counter = 2.** One more run with the same top 3 unlocks
the STOP criterion (we also need 10 custom bots; currently 8).

### Take-aways for next iteration
1. **Prober** (Axelrod's classic) — D, C, C opening then conditional.
   Could squeeze extra points from AllC and snake-oil into SoftMaj's
   tolerance.
2. **OmegaTFT** — deadlock + randomness detectors on a TFT base.
   Should outperform plain TFT vs Random and break TFT-vs-TFT noise
   vendettas.
3. **Hard Majority** — for contrast with soft_majority. Opens D, only
   cooperates if opp_C strictly > opp_D. Should fix soft_majority's
   "eat suckers vs Grim" cost.
4. **Hybrid Pavlov-TFT** — Pavlov core + TFT-style "last-move" check
   as a tie-breaker. Might recover the tripped-Grim exploit while
   keeping AllD-detection (mark each opp D and reset to D, but never
   permanently lock).

---

## Run #10 — prober (Axelrod's "probe then policy")

### Concept
Open with a fixed probe sequence: D, C, C. Observe how the opponent
responds in rounds 2 and 3 (their first chances to retaliate against
the round-1 D). If opp played C twice in a row after we kicked them
— they're a "sucker", switch to permanent D and exploit. Otherwise
they have some reciprocity, switch to plain Tit-for-Tat.

The point is to *gather information cheaply*: rounds 1-3 cost at most
a couple of points (one provocation D + two probe C's), and the
verdict guides the next ~197 rounds.

### What worked
- **vs AllC: 960.0** — near the 1000 theoretical max. AllC fails the
  sucker test instantly; we play D for 197 rounds and harvest T=5 each.
  No other bot in the field comes close to this exploit (next-best vs
  AllC is AllD's 970, but AllD doesn't get this much *anywhere else*).
- **vs TF2T: 250.0 / TF2T 203.3** — *predicted* exploit. TF2T's
  forgiveness window is exactly the wrong shape for Prober: it
  tolerates one D so plays C in rounds 2 and 3, failing the sucker
  test. We then play D forever; TF2T eventually catches on and plays
  D too, mutual D for ~195 rounds. We come out ahead by 47 points
  but at a low absolute level.
- **vs tf2t_trigger: 235.7 / 212.3** — same dynamic as TF2T.
- **vs GTFT: 550.7 / 425.7** — partial exploit because GTFT has 10%
  forgiveness rate. Sometimes its round-2-or-3 reply is C (forgive),
  sometimes D (reciprocate). Average comes out as a mix of "exploit
  mode" and "TFT mode" — net positive for Prober.

### What didn't
- **Self-play: 221.7 / 213.3** — *classic Prober problem*. Both copies
  play D, C, C in rounds 1-3. Each sees the other as a sucker. Both
  switch to permanent D. The rest of the match is mutual DD. The
  strategy *cannot recognise itself as reciprocal* because the probe
  response (C in rounds 2-3) is mathematically indistinguishable from
  a true sucker's behaviour.
- **vs AllD: 200.3** — pays a 2-sucker-round tax for the probe. After
  the probe, TFT pins to D forever. About 10 points worse than plain
  TFT vs AllD (210.7).
- **vs Grim: 210.0** — round 1 D trips Grim. Probe rounds 2-3 see D's
  from tripped-Grim, so verdict: TFT. TFT vs tripped-Grim = mutual D.
- **vs Pavlov / adaptive_tft / adaptive_pavlov / gradual**: ~400-425
  range. Decent reciprocation matchups but never reaches the ~570-595
  ceiling that TF2T/SoftMaj-type bots get from each other.

### Why rank #12 (not higher despite the AllC exploit)
Prober ranks #12 because:
1. The huge gain vs AllC (+~370 over typical reciprocators) is offset
   by huge losses vs every reciprocator (mutual ~500 vs ceiling ~595
   = -95 in each matchup, and there are 7+ such bots in the field).
2. Self-play disaster (-300 vs typical reciprocator self-play).
3. Probe cost vs AllD/Grim (-10 each).

In a field with *many* AllC-likes Prober would dominate. In a field
with mostly reciprocators Prober is suboptimal. This is the same
"environmental sensitivity" Axelrod identified: strategies are not
universally good, they're good *for a given ecology*.

### What Prober changed in the rankings
| Bot              | Run #9 rank | Run #10 rank | Δ |
|------------------|-------------|--------------|---|
| soft_majority    | #1 (493.7)  | #1 (500.3)   | +6.6 — gained from being a "non-sucker": soft_maj plays D in rounds 2-3 (counts say 1 D > 0 C), passes Prober's test. Then prober plays TFT-mode and they cooperate. We're now Prober's *best* non-AllC matchup (597). |
| tit_for_two_tats | #2 (483.6)  | #4 (463.6)   | **-20.0 — main Prober victim**. Tolerated the probe and got locked into mutual D. |
| tf2t_trigger     | #3 (481.2)  | #6 (461.9)   | -19.2 — same as TF2T. |
| adaptive_pavlov  | #4 (474.3)  | #2 (470.6)   | -3.7 (small absolute drop, big rank gain) — Pavlov plays D in rounds 2-3 after losing rounds, passes prober test. Score vs prober ~422, decent. |
| generous_tft     | #5 (469.0)  | #3 (465.9)   | -3.1 — GTFT retaliates ~90% of the time, mostly passes prober test, holds up. |

Net: Prober *itself* lands middle/low, but it **acts as an
evolutionary filter**: forgiving cooperators (TF2T-family) drop, and
fast-retaliators (SoftMaj, Pavlov, GTFT) rise. Top-3 stability
**resets to 1** because the set changed from {SM, TF2T, tf2t_trigger}
to {SM, adaptive_pavlov, GTFT}.

### Key insight: tolerance is dangerous in adversarial environments
TF2T's "ignore the first D" is *the* mechanism that makes it dominate
the noisy field — single noise flips don't trigger retaliation. But
the same mechanism is *exactly* what a Prober looks for. A defector
disguised as "noise" gets through TF2T's filter. **You can't have
noise-tolerance and probe-immunity at the same time** unless you
distinguish noise from deliberate defection by some other channel
(e.g., timing, magnitude, pattern). With only `my_history` and
`opp_history`, they're identical.

This is the central tension of trust-based systems in the real world:
- **Forgive small mistakes** → vulnerable to gradual encroachment
  ("boiling frog" exploitation).
- **Punish every mistake** → vulnerable to genuine errors and noise
  cascading into mutual destruction.
- The only escape is *out-of-band information* (intent declarations,
  reputation systems, explicit communication).

### Real-world parallels
- **Diplomatic probing**: a state makes a minor provocation (overflight,
  small sanction) precisely to test the response. If response is
  measured + proportionate → "they have red lines, behave normally".
  If response is empty → "they'll tolerate more, push further". The
  *probe itself is cheap*; the information is valuable.
- **Bullying / playground politics**: kids test new arrivals with
  small acts of meanness. Reaction (cry / tell adult / fight back)
  determines the rest of the relationship.
- **Negotiation tactics ("anchor low")**: open with an unreasonable
  ask. If the other side concedes → they're a sucker, extract more.
  If they push back → recalibrate to fair.
- **Credit / insurance fraud detection**: companies sometimes "probe"
  customers with small unauthorised charges to see if anyone notices.
  Customers who never check their statements get more.

### Take-aways for next iteration
1. **Anti-Prober TF2T**: TF2T's two-D tolerance is its weakness. A
   version that tolerates one D *only if it's not in the first 5
   rounds* would pass the sucker test while keeping noise-tolerance
   for the late game. Worth trying as the 10th custom bot.
2. **Reverse Prober ("Joss")**: TFT with occasional random D's.
   Probes constantly rather than once at the start. Should beat
   AllC well, decent vs TFT/TF2T, terrible vs Grim. Lower-effort
   variant of Prober.
3. **OmegaTFT** (Slany & Kienzle): deadlock + randomness detection
   on a TFT base. Should specifically address TFT-vs-TFT noise
   vendettas and Random exploitation, both visible in the current
   matrix.
4. **Hard majority**: opens D, only cooperates when opp_C > opp_D.
   Direct contrast with soft_majority; should pass Prober test
   easily but probably be too defensive elsewhere.

---

## Run #11 — firm_tf2t (phase-switched TFT → TF2T)

### Concept
A direct attack on the noise/probe tension identified in Run #10.
Phase 1 (rounds 1-5): pure Tit-for-Tat. Phase 2 (rounds 6-200):
Tit-for-Two-Tats. The boundary at 5 is heuristic — it covers all
known prober opening sequences (Axelrod's classic is 3 rounds, our
own bot_prober is 3, plausible extensions might run to 4-5) while
still giving 195 rounds of noise-tolerant late game.

The bet: most adversarial information about an opponent is
extractable in the first ~5 rounds. Noise, by contrast, is *uniformly
distributed* across 200 rounds, so paying for noise-tolerance early
is wasteful and paying for it late is most of the win.

### What worked
- **vs Prober: 586.3 (TF2T: 203.3, +383).** Headline result. Round-2
  TFT retaliation against Prober's opening D causes Prober to verdict
  TFT (not "exploit"), and the two then cooperate for ~195 rounds.
  Direct measurement of the cost of TF2T's tolerance: 383 points per
  match. With ~14 opponents in this field, plain TF2T was *bleeding*
  out roughly 25 average-points just to keep this single defence
  against probing strategies.
- **vs Grim: +149.** Slightly surprising. The TFT-phase actually helps
  here: once Grim is tripped (by noise), it plays D every round. TFT
  mirrors D and we don't accumulate the long sucker tail TF2T eats
  while it waits for "two D's in a row". Both bots reach mutual-D
  faster.
- **vs adaptive_pavlov: +80.** adaptive_pavlov has a K=8 "if opponent
  played ≥8 D's in the last 16 rounds, switch to permanent D" rule.
  Plain TF2T can drift into long D-streaks during noise spirals; firm
  TF2T's strict early phase prevents those streaks from accumulating,
  so adaptive_pavlov never enters lock-D mode.
- **Self-play: 593.** Near-ceiling. The TFT-phase never bites itself
  because firm_tf2t doesn't defect first; the TF2T-phase handles
  noise the way TF2T-vs-TF2T does.

### What didn't
- **vs Gradual: -98.** Gradual escalates each new D-detection by
  playing more D's. Under noise, our round-1 C may flip to D in
  Gradual's view, triggering escalation. In TFT-phase we mirror
  Gradual's D's, which makes Gradual escalate further; mutual-D
  cascade. Plain TF2T's "ignore the first D" actually breaks the
  cascade better here. **Lesson**: phase-strict is bad against
  *escalating* opponents — the second-order interaction (their D's
  multiply because of our D's) makes a small early-vendetta
  catastrophically self-amplifying.
- **vs Pavlov: -43.** Similar to Gradual but milder. Pavlov flips
  state on lost rounds, and our TFT-phase response creates more
  state-flips than TF2T's tolerance would.
- **vs Random: -14.** TFT-phase punishes Random's many early D's,
  triggers mirror-spirals; TF2T just lets them wash through.

### Why rank #2 (502.5) — strong but not #1
firm_tf2t beats #3 by ~25 points but loses to soft_majority by ~4
points. Soft_majority's edge comes from being even more
"majority-based" patient: it ignores not just isolated D's but
*scattered* D-bursts as long as cumulative C > cumulative D. Against
Prober this works because Prober's *first* move D, even isolated, is
quickly outweighed by subsequent C's in soft_majority's accounting,
so soft_maj plays D in rounds 2-3 (cumulative counts say so),
passing the sucker test the same way firm_tf2t does. soft_majority
*also* doesn't pay firm_tf2t's Pavlov/Gradual tax because it's
slower to escalate.

So the lesson: **soft_majority and firm_tf2t are convergent
solutions to the same problem (anti-Prober + noise-tolerant), but
soft_majority uses cumulative statistics and firm_tf2t uses a hard
phase boundary**. Cumulative statistics adapt smoothly to the
opponent; hard phase boundaries are more predictable but lose
information when the opponent's behaviour spans the boundary.

### Real-world parallel
"Trust but verify" + "give them time to prove themselves first". The
classic dating, hiring, and diplomatic-relations heuristic:
- Be strict / scrutinise in the first interactions (job probation
  period, dating first months, new alliance with conditions).
- Once you've built a baseline of trust, tolerate small mistakes
  (let your spouse forget your birthday once, let an ally miss one
  summit).

The mathematical insight from this bot: the *right* length of the
"strict phase" is governed by the threat model. If you only have
liars/probers, 5 interactions is plenty. If you have escalating
adversaries (Gradual-types), strict-phase can backfire — better to
defuse early via patience and re-establish via talk later.

### Open questions / follow-ups
- **firm-firm-tf2t** (longer strict phase, e.g. 10 or 20 rounds)
  would lose more vs noise-prone bots but be immune to longer
  probes. Likely net-loss given the current field.
- **Smart-firm**: replace fixed-5 with "be TFT until the cumulative
  C-fraction of opp's recent history is > 60%". Adapts the phase
  length to the data. Risk: becomes a knock-off of soft_majority.
- **Counter-firm Prober**: a Prober that delays its sucker test
  until rounds 6-8 would beat firm_tf2t's defence. We could test
  this with `bot_prober_late.py` — it would *also* lose against
  soft_majority and most others (because the probe cost grows with
  delay), but it would specifically punish firm_tf2t.
- The top-2 gap (soft_maj 506 vs firm_tf2t 502) is within seed
  noise. Across 3 different seeds, soft_maj wins all three but the
  gap is 3-7 points. Calling soft_maj "the winner" requires more
  averaging or longer matches.

### Axelrod's four principles, scored on firm_tf2t
1. **Nice** (never defect first): YES — round-1 C, never defects
   without provocation.
2. **Retaliatory**: YES, *strictly* in rounds 2-5, *eventually* in
   rounds 6+ (needs two D's in a row).
3. **Forgiving**: YES, late-game; an isolated noise-D after round 6
   is forgiven the very next round.
4. **Non-envious**: YES — never tries to "win" the matchup, only
   ever mirrors or cooperates.

All four hold. The bot's high rank confirms Axelrod's heuristics
even in noisy, prober-laden environments. Soft_majority similarly
ticks all four.
