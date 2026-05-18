"""Soft Majority — Axelrod classic, statistical rather than reactive.

Cooperate on the first move. Thereafter, look at the *entire* history of
the opponent and cooperate iff opponent has cooperated at least as often
as defected (ties broken in favour of C — hence "soft"). Otherwise defect.

Contrast with the reactive strategies in the field:
- TFT / TF2T / Grim / Pavlov all react to the very recent past
  (last 1-2 moves, or last outcome). Their behaviour is forgetful.
- Soft Majority integrates *all* observed history. Brief deviations
  (a single noise flip, a single probing D) get drowned out by the
  bulk of cooperative play. Sustained defection eventually flips
  the majority and triggers retaliation.

Expected behaviour in this field (rounds=200, noise=0.02):

* vs AllC: opponent's C-count strictly grows, D-count stays 0 except
  for ~4 noise flips out of 200. Majority C forever, both play C
  forever. Near-ceiling 600.
* vs AllD: round 1 I cooperate (S=0). From round 2 onwards opp_history
  has more D than C, so I play D every round. ≈ 1·199 = 199, about
  10 points worse than TFT (lose 1 sucker round vs TFT's near-zero).
  Comparable to TF2T (which pays 2 sucker rounds).
* vs TFT under noise: both start in CC. After a noise flip on opp's
  side, opp_history accumulates *one* D among many C's — majority still
  C, I keep cooperating. TFT sees my C and returns to C. No vendetta.
  This is similar to TF2T's behaviour but more robust: even multiple
  scattered D's from noise won't flip the majority. Expected: near-600.
* vs TF2T / GTFT: same story — almost-all-C histories on both sides,
  majority stays C, both keep cooperating. Near-ceiling.
* vs Grim: a noise flip trips Grim into permanent D from round k.
  My opp_history is k-1 C's then a tail of D's. I keep playing C until
  the D-tail exceeds the C-prefix in count, which takes about k-1
  more rounds. So I eat ~k-1 sucker rounds before locking. If k=10
  (early flip), I eat ~9 sucker rounds — worse than TFT's 1, slightly
  worse than TF2T's 2. If k=50 (mid match), I eat ~50 sucker rounds
  before flipping — disaster. Expected: poor vs Grim, possibly worse
  than TF2T.
* vs Random: opp's D-rate is ~50%; the majority can flip back and forth
  early in the match, leading to a chaotic mix of CC, CD, DC, DD. Hard
  to predict; probably middling.
* vs Pavlov: Pavlov plays mostly C with occasional D after noise events
  (frequency ~ 1% of rounds). Majority stays C, I cooperate. Pavlov
  doesn't punish my C, so we settle into mostly CC with a few stray T's
  for Pavlov. Pavlov nets a small edge here.
* vs self (Soft Majority vs Soft Majority): both start C. Noise flips
  produce isolated D's that don't flip the majority. Stays in mostly-CC
  regime forever. Near-ceiling.

Strategic role in the field:
- A "patient" cooperator: harder to provoke into retaliation than TFT,
  but eventually catches sustained defection.
- The cost vs Grim (eating many sucker rounds before locking) is the
  obvious weakness. Hard Majority (defect on ties / start with D) would
  pay less to Grim but more to noise vendettas in self-play.
- Brings a fundamentally new flavour to the field: statistical/Bayesian
  rather than reactive. Useful for the report's "diversity of strategies"
  section.

This bot uses only my_history and opp_history (no global state, no I/O,
no random). Deterministic given the histories.
"""


def choose_move(my_history, opp_history):
    if not opp_history:
        return "C"
    c_count = opp_history.count("C")
    d_count = len(opp_history) - c_count
    # Soft: ties go to C.
    if c_count >= d_count:
        return "C"
    return "D"
