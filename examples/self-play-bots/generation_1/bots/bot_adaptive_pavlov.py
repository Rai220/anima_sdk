"""Adaptive Pavlov: Pavlov with an AllD detector.

Pure Pavlov has one big known weakness: it loses to AllD because the
win-stay-lose-shift rule oscillates CDCDCD against a constant defector
and yields ~0.5/round (worse than TFT's ~1.0/round).

Adaptive Pavlov plays standard WSLS by default but adds a detector that
switches to permanent D once it is statistically certain the opponent
is a defector.

Detector
--------
After round 10, examine opp's last 10 moves. If at least 8 of them are
D, lock into permanent D for the rest of the match.

Why this threshold:
- In CC steady state under noise=0.02, opp's per-round D probability is
  ~0.02. P(>=8 D in 10) is astronomically small, so the detector never
  trips in self-play with a cooperator.
- Against AllD, Pavlov's CDCD oscillation means opp plays D every round,
  so opp's last 10 = all D. Detector trips immediately at round 10.
- Against TFT/TFTT under noise, opp's D rate stays low (a few isolated
  echoes per match). Detector stays off.
- Against Grim that has been triggered, opp will play D constantly from
  the trigger onward. After 10 rounds of constant D, detector trips and
  we lock D — correct response, since cooperating with a locked-Grim
  pays 0 per round.

Self-play
---------
Two Adaptive Pavlovs behave exactly like two Pavlovs in the
non-detector regime. Pavlov self-play under noise spends most time at
CC (R=3 win-stay) and recovers from mutual D within one round (P=1
lose-shift back to C). The detector never fires because opp's D-rate
stays around the noise floor.

Vs AllD
-------
Rounds 0-9: Pavlov oscillates CDCDCD, scoring ~0.5/round = ~5 over 10
rounds. Round 10+: detector trips, lock D, scoring 1.0/round for the
remaining 190 rounds. Total ~195/200 = ~0.975/round. Matches TFT's
performance vs AllD (~1.0/round). Worth giving up the first 10 rounds
of CDCD for noise-robustness on the detection.

Vs TFT-family under noise
-------------------------
Pavlov-on-Pavlov logic produces mostly CC with occasional 1-2 round
desyncs. Vs TFT specifically: Pavlov's first reaction to a noise-D from
TFT is to play D (S=0 shift). This triggers a longer echo from TFT.
Pavlov then plays C after the (D, D) round (P=1 shift), TFT plays D
again (mirror of my last D), Pavlov plays D (S=0 shift)... the
sync re-establishes after a few rounds. No detector trip.

Vs Random
---------
Random's D-rate is ~0.5. P(>=8 D in 10) with p=0.5 is sum_{k=8..10}
C(10,k) * 0.5^10 = 56/1024 ≈ 0.0547. So per 10-round window, ~5.5%
chance of triggering. Over 19 windows in a 200-round match, expected
1 trigger. Once it trips, we lock D against Random — Random pays ~5
on its Cs (T=5) and ~1 on its Ds (P=1), so we get ~3/round from there.
That's much better than Pavlov's ~2.27 vs Random.

Reference: my own variant. The general idea of an AllD detector + WSLS
appears in the IPD literature as "adaptive Pavlov" or "Pavlov with
provocability"; concrete thresholds vary.
"""


def choose_move(my_history, opp_history):
    if not my_history:
        return "C"

    # AllD detector: if we've already triggered, stay in D.
    # We re-derive the trigger from history each call rather than
    # carrying state (the API forbids state across calls). The trigger
    # is "monotonic": once it ever fired we want to keep defecting. So
    # we check whether *any* 10-round window in our history has had
    # >=8 D from opp. If yes, lock D.
    n = len(opp_history)
    if n >= 10:
        # Slide a 10-round window over opp's history. If any window
        # has >=8 D, we've already committed to D-lock.
        # Quick optimisation: use a running count. But we run choose_move
        # only ~200 times per match; a simple linear scan is fine.
        for start in range(n - 9):
            window = opp_history[start:start + 10]
            if window.count("D") >= 8:
                return "D"

    # Otherwise standard Pavlov (win-stay-lose-shift).
    last_mine = my_history[-1]
    last_opp = opp_history[-1]
    if last_mine == "C" and last_opp == "C":
        return "C"  # R=3, win, stay
    if last_mine == "D" and last_opp == "C":
        return "D"  # T=5, win, stay
    if last_mine == "C" and last_opp == "D":
        return "D"  # S=0, loss, shift
    return "C"  # (D, D) -> P=1, loss, shift
