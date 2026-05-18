"""Hard TFT (TFT + AllD lock-in).

Behaviour:

- Default behaviour: classical Tit-for-Tat (open C, then copy opp's last
  move).
- Additional rule: maintain a sliding window of the opponent's last 20
  moves. If the window is full (i.e. round >= 20) and the share of D
  in it is greater than 0.6, play D this round regardless of TFT
  output. Re-evaluated every round; if the opp's defection rate later
  drops below threshold we return to TFT behaviour. This is "adaptive
  hard TFT", not truly permanent.

Rationale: TFT and GTFT both suffer disproportionately against AllD-
class opponents (AllD itself, post-trigger Grim). They keep handing out
periodic Cs that the opponent banks as free T=5 rounds.

A defection-rate detector lets us keep TFT's cooperative behaviour
against nice opponents (whose D rate stays near the noise floor of ~2%)
while neutralising bullies. Threshold of 0.6 over 20 rounds is well
above any plausible noise-only flip rate (E ~= 0.02 * 20 = 0.4 D's,
P[>= 12 D's in 20 rounds | p=0.02] ~ 0). So nice bots cannot trigger
the lock by accident.

Trade-offs:

- *Vs AllD*: instead of TFT's "lose one round then DD forever"
  (score ~= 1.04), Hard TFT detects after round 20 and from then on
  the dynamic is the same. The gain vs plain TFT here is tiny, because
  TFT already locks DD vs AllD after the first round. The detector
  mainly helps against mixed defectors (Random, post-noise Grim) and
  against future "Prober"-style bots.
- *Vs Grim*: Grim cooperates initially, then locks to D after a noise
  flip. After Grim's switch our window fills with D's; we lock to D
  too. Slightly better than TFT's perpetual echo war post-flip.
- *Vs Random*: Random's D rate is ~0.5, below 0.6 threshold. So we
  remain in TFT mode. Same as plain TFT here.
- *Vs nice cooperators (TFT, GTFT, TFTT, Pavlov, AllC)*: behaves as
  pure TFT — never trips the lock, because their D rates stay near
  the noise floor.

In short: this is "TFT, but does not feed bullies forever".
"""

WINDOW = 20
THRESHOLD = 0.6


def choose_move(my_history, opp_history):
    if not opp_history:
        return "C"
    # Once we have a full window of opponent moves, check defection rate.
    if len(opp_history) >= WINDOW:
        window = opp_history[-WINDOW:]
        d_rate = window.count("D") / WINDOW
        if d_rate > THRESHOLD:
            return "D"  # locked-in once condition is met any round
    # Otherwise: classical Tit-for-Tat.
    return opp_history[-1]
