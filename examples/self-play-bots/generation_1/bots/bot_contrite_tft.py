"""Contrite Tit-for-Tat (CTFT) — TFT with apology for own noise slips.

Boyd (1989), "Mistakes allow evolutionary stability in the repeated
Prisoner's Dilemma"; Sugden (1986). Designed to fix TFT's catastrophic
fragility under noise: under any positive noise rate, two TFT players
sooner or later get out of phase and start a CDCD echo war that costs
both ~1.5/round for the rest of the match.

Idea. Reconstruct on every call what THIS bot intended to play in each
prior round (by re-running its own state machine on the histories).
A "slip" is a round where intended = C but actual = D, i.e. noise
flipped the bot's cooperation into a defection. The bot owes an
apology and enters a 2-round contrition window: play C regardless of
opp's move for the next 2 rounds. Two rounds is the minimum that
breaks the echo against a plain TFT opponent (see derivation below).

Why 2 rounds and not 1. Suppose I slip on round t (actual D, opp
played C). Then:

    t+1: I am contrite -> C. Opp plays TFT(D)=D. Score for me: 0.
    t+2: 1-round contrite policy -> back to TFT. Opp's last was D,
         so I play D. Opp plays TFT(C)=C. Score: 5 for me.
    t+3: I play TFT(C)=C. Opp plays TFT(D)=D. Score: 0. Echo loop!

With 2 rounds of contrition:

    t+1: contrite -> C. Opp: TFT(D)=D. Score: 0.
    t+2: still contrite -> C. Opp: TFT(C)=C. Score: 3. Resynced.
    t+3: not contrite, TFT(C)=C. Mutual C from here.

The cost of one slip is therefore exactly 1 round of payoff (the
round-1 score is 0 instead of 3). The benefit is avoiding the
infinite echo. At 2% noise per move per round there are ~8 slips per
200-round match, so the long-run average is 600/200 = 3.0 minus ~8
lost rounds out of 200 ≈ 2.96 per round in CTFT-vs-CTFT or
CTFT-vs-TFT. Compare with TFT vs TFT under 2% noise: classic result
is ~2.27/round.

Reconstruction note. `choose_move` is stateless across rounds, so on
each call we re-derive our intended-move trajectory by simulating our
own state machine on (my_history, opp_history). Each step is O(n);
the total cost over a 200-round match is O(n^2)=40k ops — fine.

Predicted matchups:
- vs self: ~2.96 (best self-play in the nice class, edges GTFT/TFTT).
- vs TFT, GTFT, FBF, TFTT: ~2.95 (cooperation cluster).
- vs AllC: ~3.0 modulo noise. Slips are corrected via contrition.
- vs AllD: ~1.0. Initial C eats S=0; then TFT locks D. Any noise flip
  on opp from D->C while I'm in TFT-D mode is followed by TFT-C from
  me one round later; mostly mutual D. Slight cost from contrition
  firing on rare noise that flips my D to C? No -- contrition only
  fires on C-intent flipping to D, not the other way.
- vs Grim: ~1.0. Same as TFT, possibly slightly worse if my contrition
  fires after a noise slip while Grim has already locked D (wastes a
  C against locked-D Grim).
- vs Pavlov: ~2.4-2.6. Contrition can break Pavlov echo wars too.
- vs Prober: similar to TFT, ~2.0-2.2. Prober opens D -> I TFT-D -> if
  Prober switches to TFT we get cooperation; my contrition fires only
  on my own noise slips, so no effect.

Reference: Boyd (1989); Wu & Axelrod (1995); also Axelrod & Dion
(1988) for the original observation that TFT is fragile under noise.
"""


def _simulate_intent_and_contrition(my_history, opp_history):
    """Simulate the state machine forward over the history.

    Returns:
        intent: list of "C"/"D" same length as my_history.
        contrition_left: int in {0, 1, 2}: how many rounds of contrition
            are still pending going INTO round len(my_history).
    """
    n = len(my_history)
    intent = []
    contrition_left = 0  # rounds of forced-C remaining going into round t
    for t in range(n):
        if t == 0:
            intent_t = "C"
        elif contrition_left > 0:
            intent_t = "C"
        else:
            # Plain TFT
            intent_t = opp_history[t - 1]
        intent.append(intent_t)

        actual_t = my_history[t]
        # State update for next round.
        if contrition_left > 0:
            contrition_left -= 1
            # While in contrition, no new slip detection (we're already
            # apologising; a second simultaneous slip will be re-armed
            # only after contrition expires).
        else:
            if intent_t == "C" and actual_t == "D":
                # Noise flipped me. Start a 2-round contrition window.
                contrition_left = 2
    return intent, contrition_left


def choose_move(my_history, opp_history):
    n = len(my_history)
    if n == 0:
        return "C"
    _, contrition_left = _simulate_intent_and_contrition(my_history, opp_history)
    if contrition_left > 0:
        return "C"
    return opp_history[-1]
