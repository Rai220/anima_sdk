"""Gradual (Beaufils, Delahaye, Mathieu 1996).

A classic strategy often cited as outperforming TFT in noisy round-robins.

Behaviour:
* Round 0: cooperate.
* Let N = total number of times the opponent has defected so far.
* Let k = number of full rounds elapsed since the opponent's *most recent*
  defection (k=0 means we are choosing the move that comes right after seeing
  the defection).
* If k < N: play D (escalating retaliation — N D's in a row).
* Elif k < N + 2: play C (two "calming" C's to signal we are done punishing).
* Else: play C until the opponent defects again.

The key trick is the *escalating* punishment: every new defection makes the
next retaliation one D longer. This deters exploiters that try to sneak in
the occasional D (e.g. Joss-style), because they accumulate longer and longer
sentences. The two calming C's give the opponent a chance to come back —
unlike Grim which never forgives.

Expected behaviour in this field:

* vs Gradual (self): under 2% noise we'll occasionally see opp's D. After
  the first noise-flip we retaliate with 1 D + 2 calming C's. The opponent
  (also Gradual) sees one D from us and does the same — they retaliate with
  1 D + 2 C's that overlap with our calming. With luck the dance ends; with
  bad luck it spirals briefly. Self-play should sit comfortably above the
  TFT-vs-TFT floor of 495 but probably not as high as TF2T (which never
  retaliates at all on a single flip).
* vs AllD: round 0 we play C (sucker). From round 1: opp has 1 D, k=0,
  k < 1 -> we play D. Round 2: opp has 2 D's (still in retaliation),
  k=0 again, k < 2 -> D. And so on. Effectively we mirror AllD perfectly
  from round 1 (because every round opp defects, the count grows and so
  does the retaliation requirement). Should be near TFT's 210.
* vs AllC: never any defections, we always C. Near-ceiling 600.
* vs TFT: a noise flip from us causes TFT to retaliate; we then retaliate
  with N D's; TFT mirrors them; vendetta extends. This is the danger spot
  for Gradual under noise — escalation can blow up between two reciprocators.
  Mitigated by our 2 calming C's, which TFT will receive and respond to
  with C.
* vs Random: opp defects ~50% of the time. Each defection extends N by 1,
  so our retaliation length grows; meanwhile we keep handing out 2 calming
  C's after each burst. The dance is noisy but should be no worse than TFT.
* vs Grim: a single noise flip from us trips Grim into permanent D. After
  that, we see opp D's piling up; each new D increments N; we retaliate
  forever (because the calming-C window never closes — opp keeps defecting,
  k resets to 0 each round). So we lock to mutual D, like TFT does. Cost
  similar to TFT-vs-Grim.

Trade-off summary: Gradual exchanges TFT's simplicity for the property
that exploiters are deterred from probing — a single probe costs them
more than 1 sucker payoff because we lengthen punishment each time. The
calming C's provide a clear "I am done now" signal that helps recovery
under noise, unlike Grim.
"""


def choose_move(my_history, opp_history):
    if not opp_history:
        return "C"

    # Total number of opponent defections seen so far.
    n_defections = sum(1 for x in opp_history if x == "D")
    if n_defections == 0:
        return "C"

    # Find index of the most recent opponent defection.
    last_d_index = len(opp_history) - 1
    while last_d_index >= 0 and opp_history[last_d_index] != "D":
        last_d_index -= 1
    # last_d_index is guaranteed to be >= 0 here because n_defections >= 1.

    # k = how many rounds have already passed since the defection.
    # When last_d_index == len(opp_history) - 1 (opp just defected), k = 0
    # and this is our first reaction round.
    k = len(opp_history) - 1 - last_d_index

    if k < n_defections:
        return "D"            # escalating retaliation
    if k < n_defections + 2:
        return "C"            # calming
    return "C"                # back to baseline cooperation
