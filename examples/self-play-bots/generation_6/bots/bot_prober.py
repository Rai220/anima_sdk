"""Prober: open with D to test, then classify the opponent and switch.

Classical strategy: Round 1 = D (a probe). Then look at the opponent's
response in rounds 2 and 3:

- If the opponent played D in *either* round 2 or 3 (i.e. they
  retaliated), classify them as a reciprocator and play TFT for the
  rest of the match.
- If the opponent played C in BOTH round 2 and round 3 (no
  retaliation at all), classify them as a sucker and defect for the
  rest of the match.

The 2-round probe window is a deliberate buffer against the 2% noise:
a single noisy C from a true reciprocator (TFT retaliating but the
retaliation got flipped to C) shouldn't be enough to misclassify them
as a sucker.

Why I'm adding this. The current field has two cooperator-friendly
philosophies (detector-based: cycle_detector, adaptive_tft;
mechanism-based: gradual). Both are "nice" (never defect first). A
prober tests how robust the field is to a *not-nice* opener: bots
that probe via early defection and exploit sucker behaviour.

Expected matchups (heuristic).

- vs always_c: probe D, opp plays C, opp plays C again -> classify as
  sucker -> AllD for remaining 197 rounds. Score: 5 + 5 + 5*197 = ~985.
  Best case in the field for harvesting.
- vs always_d: probe D, opp plays D, opp plays D -> classify as
  reciprocator -> TFT for the rest. From round 4 onwards both play D
  (we mirror opp's D from prior round). Score: 1 + 1 + ... = ~200,
  the DD-floor.
- vs tit_for_tat: probe D, TFT plays C (default first move), TFT plays
  D (mirroring our round 1). Round 2: opp=C, round 3: opp=D -> opp
  retaliated in round 3 -> classify as reciprocator -> switch to TFT.
  From round 4: we mirror opp; opp mirrors us. The round-3 D from
  opp gets echoed by us in round 4, and round-3 C from us gets echoed
  by opp in round 4. So round 4 we play D (echo of opp's R3 D), opp
  plays C (echo of our R3 C). Round 5: we play C (echo of opp's R4 C),
  opp plays D (echo of our R4 D). CD/DC oscillation, but TFT-style
  it should re-sync under noise. Net: T+C-D oscillation for ~5-10
  rounds, then stabilises on CC. Expect ~460-500.
- vs tf2t: probe D, TF2T plays C (doesn't retaliate after 1 D),
  TF2T plays C (still hasn't seen 2 D's in a row) -> we classify
  TF2T as a sucker -> AllD. From round 4 we play D, TF2T sees 2 D's
  (rounds 1 + 3) and starts retaliating. But we're already locked
  in AllD. Score: high (5 for the first probe + 0 + 0 then 5+5+5+...
  until TF2T catches on, then 1+1+1...). Probably ~500-700 — TF2T's
  late retaliation locks us into DD-floor for most of the match.
  This is the headline exploit: TF2T is the most vulnerable.
- vs generous_tft: probe D, GTFT retaliates with D in round 2 (~90%
  of the time; ~10% forgives). Likely classify as reciprocator and
  switch to TFT. Then mutual cooperation under noise. Similar to TFT
  outcome.
- vs adaptive_tft: probe D. adaptive_tft starts as TFT, retaliates
  in round 2. Classify reciprocator -> switch to TFT. Same as vs TFT.
- vs grim: probe D, Grim locks into permanent D from round 2 onward.
  Round 2: opp=D, round 3: opp=D -> classify reciprocator. We mirror
  Grim's D. Net: DD-floor ~200, similar to vs AllD.
- vs random: opp ~50/50. Probably classify as reciprocator (50% chance
  opp plays D in round 2 OR round 3). Then TFT against random. ~430.
- vs pavlov: probe D, opp=C (Pavlov starts C), round 2 we see Pavlov's
  C, round 3 we see Pavlov's response to our R2 move. We played D in
  R1, then... wait, we play D in R1 and our R2 move is determined by
  this strategy's logic which is in the "probing" state. We probably
  play C in R2 and R3 while waiting for opp's response. So Pavlov
  sees DCCC... and Pavlov's logic: R2 = WSLS based on R1 outcome.
  R1: we D, Pavlov C -> Pavlov got 0 (S). Pavlov shifts -> D in R2.
  We see Pavlov's R2 = D. Classify as reciprocator. Then mutual
  noise-driven TFT outcome. ~470.
- vs alternator: probe D, opp starts D (round 1). We probably play C
  in round 2 (the "probe waiting" phase). Opp R2 = C (alternator's
  second move). We see opp R2 = C. Round 3 we wait again, play C.
  Opp R3 = D (alternator's third move). We see opp's first D at R1
  and second at R3 -> classify reciprocator -> TFT for rest. TFT vs
  alternator = ~488. So we get similar.
- vs gradual: probe D in R1. Gradual cooperates first, sees our D,
  triggers a 1-round D punishment. R2: opp plays D. We classify
  reciprocator. R3: opp plays C (cooling). We switch to TFT in R4.
  Then mutual CC under noise. ~580-590.
- vs cycle_detector: opp cooperates first, sees our D in R1.
  cycle_detector's logic (need to check the file) — likely it
  doesn't lock D from a single round, plays TFT-style early.
  R2: opp plays D (TFT echo). We classify reciprocator. Same as
  vs TFT. ~488.
- vs self (prober vs prober): both probe D in R1, both play C in R2
  (waiting), both play C in R3 (waiting). Both see opp R2=C, R3=C ->
  both classify as sucker -> both switch to AllD. Mutual DD from R4
  onward. Net: ~200 + small bonus from the early round mix. Actually
  no: R1 mutual DD = 1+1, R2 mutual CC = 3+3, R3 mutual CC = 3+3,
  then mutual DD for 197 rounds. Self-score = 2 + 6 + 6 + 197 = 211.
  Bad self-play. This is a structural weakness.

Net prediction: Prober should do very well against AllC and TF2T
(the two suckers), badly against Grim/AllD/self, and tie everyone
else. The headline question is whether the AllC + TF2T harvest is
enough to outweigh the self-play penalty and the lost-cooperation
with reciprocators.

Risk: probing kills mutual cooperation in self-play because both
sides see the other's "waiting" C as a sucker signal. A real-world
analogue: if every nation starts every relationship with a small
provocation, mutual trust never forms.
"""


def choose_move(my_history, opp_history):
    n = len(opp_history)
    if n == 0:
        return "D"  # Round 1: probe.
    if n == 1:
        return "C"  # Round 2: wait and observe opp's response to probe.
    if n == 2:
        return "C"  # Round 3: wait one more round to debounce noise.

    # Classify based on opp's moves in rounds 2 and 3 (indices 1 and 2).
    retaliated = (opp_history[1] == "D") or (opp_history[2] == "D")

    if not retaliated:
        # Sucker classified — exploit for the rest of the match.
        return "D"
    # Reciprocator classified — play TFT from here on.
    return opp_history[-1]
