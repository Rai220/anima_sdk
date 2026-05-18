"""Firm-but-Fair (FBF) — Pavlov variant with asymmetric S=0 trigger.

Defined by Boyd & Lorberbaum (1987) and revisited by Hilbe et al. (2018)
as a memory-one strategy that only defects in response to *being exploited*
(I played C, opp played D = S=0), and cooperates in every other state.

Transition rule (last state -> next move):

    (C, C) R=3  -> C   (stay cooperative)
    (C, D) S=0  -> D   (punish exploitation)
    (D, C) T=5  -> C   (do NOT continue exploiting; "fair")
    (D, D) P=1  -> C   (forgive mutual punishment)

Compare to Pavlov / Win-Stay-Lose-Shift:

    (D, C) T=5  -> D   (Pavlov stays defecting -- "win-stay")
    All other states identical.

So FBF differs from Pavlov in exactly one transition: after I successfully
exploited the opponent (T=5), Pavlov keeps milking it; FBF returns to C.
That asymmetry costs the T=5 exploitation upside (FBF won't farm AllC after
a noise flip), but in exchange FBF doesn't become a "predator after a slip":
its only defection trigger is the S=0 outcome, which is true exploitation.

Predicted properties:

- Nice (never defects unprovoked from CC).
- Retaliatory (one-round D after every S=0 event).
- Forgiving (single-round retaliation, then re-extends C).
- Vs AllC: ~3.0/round under noise. After a noise flip the (C, D) state
  triggers a D once, but then (D, C) sends FBF back to C immediately.
  Pavlov would have farmed AllC for T=5 instead.
- Vs AllD: same as Pavlov — CDCD oscillation, ~0.5/round. After (C, D)
  FBF goes D; after (D, D) FBF goes C; that's the alternation.
- Vs TFT: full cooperation modulo noise. After a single flip both forgive
  via (D, D) -> C and (D, C) -> C, resyncing in 1-2 rounds.
- Vs self: this is the known FBF self-play weakness. After a single noise
  flip the two copies enter a CD-DC oscillation:
    flip:    A=D, B=C        (S=0 for B, T=5 for A; histories last (D,C)/(C,D))
    rnd t+1: A: last (D,C) -> C; B: last (C,D) -> D.  Result CD.
    rnd t+2: A: last (C,D) -> D; B: last (D,C) -> C.  Result DC.
    ... infinite alternation, ~2.5/round average.
  Pavlov would resync after one DD round. FBF won't.
  This is why the FBF rank prediction is mid-pack, not top-3.

Reference:
- Boyd & Lorberbaum, "No pure strategy is evolutionarily stable in the
  repeated Prisoner's Dilemma game" (Nature, 1987).
- Hilbe, Chatterjee, Nowak, "Partners and rivals in direct reciprocity"
  (Nature Human Behaviour, 2018) — discusses FBF as a partner strategy.
"""


def choose_move(my_history, opp_history):
    if not my_history:
        return "C"
    last_mine = my_history[-1]
    last_opp = opp_history[-1]
    # The only D-trigger is "I cooperated and got exploited last round".
    if last_mine == "C" and last_opp == "D":
        return "D"
    return "C"
