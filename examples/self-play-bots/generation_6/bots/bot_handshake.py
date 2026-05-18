"""Handshake: probe with DD, then classify and (for handshake candidates) verify.

Motivation. Prober (run 009) demonstrated that a not-nice opener pays a
heavy price in this field: AllC exploitation (~985) isn't enough to
offset the detector lock-outs (cycle_detector locks D) and the self-
play disaster (two probers mutually classify each other as suckers
and end in mutual DD).

The Handshake idea: solve Prober's self-play problem by using a *two-
round signal* that another Handshake bot can recognise. If both sides
play DD in rounds 1 and 2, they're "saying" we're both Handshakes,
and they switch to mutual cooperation forever. AllC bots will play CC
in those rounds and get exploited as before. Reciprocators will play
CD or DC (TFT-like) and get treated with TFT.

The catch: AllD ALSO plays DD in rounds 1 and 2. We can't tell AllD
apart from another Handshake bot just from rounds 1-2 alone. So we
add a *verification step*: in round 3, the Handshake-candidate plays
C (signalling "I'm switching to cooperate, are you?"). In round 4 we
check what the opponent played in round 3:

- Opp R3 = C: confirmed Handshake (or noise + AllC, which is fine).
  Switch to AllC for the remainder of the match.
- Opp R3 = D: false alarm (AllD-like opponent that didn't reciprocate
  our cooperation signal). Switch to AllD for the remainder.

The verification round costs 1 round of being exploited if the
opponent turns out to be AllD (we play C, they play D), but that's a
small price: 0 points instead of 1 for one round = -1 to our score,
compared to the ~590 points we gain when we ARE matched with a real
Handshake.

Classification grid (using opp's rounds 1 and 2):

- DD: handshake candidate. Verify by playing C in R3.
  - Opp R3 = C: AllC forever (mutual cooperation locked in).
  - Opp R3 = D: AllD forever (it was a defector pretending to handshake).
- CC: pure cooperator / sucker. AllD forever (exploit).
- CD or DC: reciprocator. TFT for the rest of the match (mirror last).

Self-play prediction (handshake vs handshake):

- R1: both D-D -> 1+1
- R2: both D-D -> 1+1
- R3: both see opp DD -> both play C -> 3+3
- R4-200: both see opp R3 = C -> AllC forever -> 3*197 = 591 each
- Total: 1+1+3+3*197 = 596 each. (Same as TF2T-self if no noise; TF2T-
  self is ~598.7 empirically. Handshake-self should be ~595 under 2%
  noise.) MAJOR improvement over Prober-self (217.0) and on par with
  the best self-cooperators in the field.

Expected matchups (heuristic predictions to validate against the
tournament matrix):

- vs always_c: DD-DD-D-D-D-... opp CC-CC-CC-... we classify CC ->
  AllD. Score: 5+5+5+5+...+5 = 5*200 = 1000 (perfect exploit, slightly
  better than Prober's 977 because we have ONE more D round before
  classifying). THIS IS THE HEADLINE EXPLOIT.
- vs always_d: DD-DD-DC-DD-... we classify DD -> verify with C in R3.
  Opp R3 = D. R4 onwards: AllD. Total: 1+1+0+1*197 = 199. Just below
  DD-floor (200) due to the one wasted C in R3. Comparable to Gradual
  vs AllD (199.0). Acceptable cost.
- vs tit_for_tat: R1 DvC; TFT R2 = D (echo R1 D); R2 DvD; TFT R3 = D
  (echo R2 D). We see opp CD -> mixed -> TFT mode. We play opp's last
  = D. R3 = DvD. R4: TFT plays our R3 = D. We play opp R3 = D. Mutual
  DD until a noise flip breaks the lock. Estimate ~330-470 (DD-floor
  for a long stretch, then noise-mediated recovery to CC).
- vs tf2t: R1 DvC; TF2T R2 = C (only 1 D seen); R2 DvC; TF2T R3 = D
  (now 2 D's in a row). We see opp CC -> AllD mode. From R3 onwards
  AllD vs TF2T. TF2T retaliates after seeing 2 D's. Estimate: 1+5+5+
  1*197 = 208 for us, or so. Like Prober's 257 cell. Headline target
  for the exploit.
- vs grim: R1 DvC; Grim R2 = D (Grim locks after seeing first D);
  R2 DvD; Grim R3 = D. We see opp CD -> TFT mode. Mirror Grim's D
  forever. Score: ~210, DD-floor with the early 5 mixed in. ~250.
- vs generous_tft: R1 DvC; GTFT retaliates with D ~90% of the time
  in R2. With 10% prob GTFT plays C in R2 (forgive). Avg: opp R2 ~ D.
  R2 DvD-ish; GTFT R3 = D-ish. We see opp ~CD -> TFT mode. Mutual
  D-D-D-... then GTFT forgives. Estimate ~440 (better than vs pure
  TFT because GTFT recovers faster from the D-D lock).
- vs cycle_detector: R1 DvC; cycle_detector R2 = D (echo our R1 D);
  R2 DvD. We see opp CD -> TFT mode. cycle_detector may lock into
  permanent D if it sees our 2 D's. If locked: DD-floor ~220. If
  not locked: ~470.
- vs pavlov: R1 DvC; Pavlov R2 = D (WSLS shifts after S=0); R2 DvD;
  Pavlov R3 = C (WSLS shifts after P=1). We see opp CD -> TFT mode.
  Play opp's R2 = D in R3. Then opp R3 = C, opp R4 = D (WSLS-shift
  after S=0 from our R3 D). Noise-driven cycle ensues. ~470.
- vs random: opp plays ~50/50. P(opp DD in R1+R2) = 25%, P(opp CC) =
  25%, P(mixed) = 50%. Expected: 25% chance we play AllC against
  random (terrible, ~100), 25% chance we play AllD (great, ~430),
  50% chance TFT (~440). Weighted average: ~340. Bad cell.
- vs alternator: alternator plays D-C-D-C-... R1 DvD; R2 DvC; we see
  opp DC -> mixed -> TFT mode. Then alternator vs TFT pattern:
  noise-mediated lock. ~400.
- vs prober: R1 DvD (both probe); R2 DvC (prober waits); we see opp
  DC -> mixed -> TFT mode. Prober at R4 sees our DDC -> retaliated in
  R2 -> classify reciprocator -> TFT. Mutual TFT from R4. Both
  mirror opp's last. ~580 (very good cell — the asymmetry where we
  recognise prober as a reciprocator while prober recognises us as
  the same lets both bots stabilise on CC).
- vs adaptive_tft: R1 DvC; ATFT retaliates in R2 with D; R2 DvD. We
  see opp CD -> mixed -> TFT mode. ATFT may detect us as a defector
  if it locks early. ~400-500.
- vs gradual: R1 DvC; Gradual R2 = D (1 round punishment for our R1
  D); R2 DvD; Gradual R3 = C (cooling). We see opp CD -> TFT mode.
  Mutual recovery via Gradual's cooling phase. ~540.

Net prediction. Handshake should rank around #5-7 in total score, but
should beat Prober on two criteria:

1. Self-play: ~595 vs Prober's 217 -> +378 in one cell.
2. AllC exploit: ~1000 vs Prober's 977 -> +23 in one cell.

The cost: Handshake plays D for 2 rounds instead of 1, so its
classification window is *shifted* but not larger. Against reciprocators
this means an extra round of mutual DD before the noise-mediated
recovery — roughly -50 points per reciprocator cell. With ~8 reciprocators
in the field, total cost ~ -400 points. Net: Handshake's score should
be close to Prober's, but with very different per-cell shape.

If Handshake DOES outscore Prober, it'll be a clean demonstration that
*adding a coordination signal fixes the self-play problem of probing
strategies*, which is the canonical solution in evolutionary game
theory for "tribe-recognition" — see green-beard signalling, kin
selection markers, religious/cultural tribal cues. The bot is a
miniature model for "How does a non-cooperative tribe internally
cooperate?"

Risk: if cycle_detector or adaptive_tft permanently locks into D
against our 2-D opener (it might — cycle_detector locked against
prober's 1-D opener), we'll be at DD-floor for multiple cells. This
would push Handshake below Prober. The matrix will tell.
"""


def choose_move(my_history, opp_history):
    n = len(my_history)

    # Phase 1: handshake probe (rounds 1 and 2).
    if n == 0:
        return "D"  # Round 1: probe.
    if n == 1:
        return "D"  # Round 2: handshake signal (second D).

    opp_r1 = opp_history[0]
    opp_r2 = opp_history[1]

    # Round 3: act on the rounds-1-and-2 classification.
    if n == 2:
        if opp_r1 == "D" and opp_r2 == "D":
            # Handshake candidate: send a C as the verification signal.
            return "C"
        if opp_r1 == "C" and opp_r2 == "C":
            # Sucker: exploit forever.
            return "D"
        # Mixed: reciprocator. Play TFT (mirror opp's last move).
        return opp_history[-1]

    # Phase 3: rounds 4 onwards. Lock in a stable strategy.
    if opp_r1 == "D" and opp_r2 == "D":
        # Handshake-candidate path: verify by checking opp's R3 response.
        opp_r3 = opp_history[2]
        if opp_r3 == "C":
            # Confirmed handshake -> mutual cooperation forever.
            return "C"
        # Opp didn't reciprocate the verification C -> AllD-like opponent.
        return "D"

    if opp_r1 == "C" and opp_r2 == "C":
        # Pure cooperator classified at R3 -> keep exploiting.
        return "D"

    # Reciprocator path: TFT for the remainder.
    return opp_history[-1]
