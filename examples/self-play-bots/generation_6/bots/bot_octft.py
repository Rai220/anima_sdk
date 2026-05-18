"""Omega-Contrite TFT (OCTFT): hybrid of Contrite TFT (Wu & Axelrod 1995)
and Omega TFT's deadlock detector (Slany & Kienreich 2007), minus the
randomness counter.

Motivation
----------
Run 012 showed Contrite TFT (#1) and Omega TFT (#2) using DIFFERENT
mechanisms to escape CD/DC echoes caused by noise:

  - CTFT: track my INTENDED moves; if I flipped from C to D in the last
    2 rounds, apologise with a unilateral C. Repairs noise quickly when
    BOTH players forgive (CTFT-vs-CTFT self-play ~592 vs CC ceiling 600).
  - Omega TFT: track CD/DC alternation pattern over the last 3 rounds;
    if pattern detected, play a unilateral C to break it. Repairs noise
    when EITHER player notices the echo. Useful asymmetrically (omega vs
    plain TFT got 556 while TFT vs omega got 437 - omega unilaterally
    fixed the echo while TFT stayed stuck).

These two mechanisms are *complementary*:

  - Apology fires when I KNOW I flipped (introspection).
  - Deadlock break fires when I see a pattern (extrospection).

If the noise hit OPP's side (a noise flip from C to D on their roll),
the apology window doesn't fire (I never intended C wrongly), but the
deadlock detector still catches the resulting CD/DC echo a few rounds
later. Conversely, if the noise hit MY side, the apology fires
immediately (round AFTER opp retaliates), no need to wait for a 3-round
pattern.

Omega TFT also has a "randomness counter" that switches to AllD mode if
opp seems random/uncooperative. Run 012 showed this counter has bad
false positives against bot_prober (omega vs prober = 338.0, vs TFT's
473.3, a 135-point loss). I drop the randomness counter entirely. The
hypothesis: against true random/AllD opponents, plain TFT-floor (~200
vs AllD) is acceptable; the randomness counter pays for marginal gains
against alternator/random by giving up ~135 points vs prober and ~20
vs grim. Net cost > net benefit in our field.

Rule
----
On each round i:

  - i == 0: play C.
  - If apology window fires (I flipped C->D in rounds i-2 or i-1):
      play C.
  - Else if deadlock counter >= 3 (CD/DC alternation):
      play C (forced break).
  - Else: TFT — mirror opp's last observed move.

Apology takes priority over deadlock-break because apology fires SOONER
(round i-1 noise → apology at round i+1; pattern needs at least 3 rounds
of alternation to fire). If both fire at once, they prescribe the same
action anyway (C).

Counters update after each round based on OBSERVED history. The
randomness counter from Omega is dropped entirely.

Stateless implementation: deterministic given (my_history, opp_history),
reconstruct by replaying from round 0 on every call.

Predictions
-----------
vs CTFT: should be similar to CTFT-self (~592). Apology fixes my flips,
  CTFT's apology fixes its flips. The deadlock detector adds a backup
  in case both apologies miss.
vs Omega TFT: should be near 556 (omega-vs-omega self) or better. My
  apology fires faster than omega's pattern detector for MY flips.
vs Plain TFT: I should win the asymmetric pair similar to omega
  (~556 / 437). I unilaterally break echoes; TFT stays stuck.
vs Grim: still DD-floor (~200). Apology never fires (after grim's first
  D, I TFT back D forever; I never intend C). Deadlock break never
  fires (DD ≠ alternation).
vs AllD: pure DD ~200. Same as TFT.
vs Prober: prober plays D twice then TFT. I TFT back D-D, then prober
  switches to TFT mode from round 4. We mutually-TFT from round 4 with
  occasional noise. Better than omega-vs-prober (338) because I don't
  trip into AllD mode. Predicted ~470 like TFT-vs-prober.
vs Alternator: I get CDCD echo with alternator. My deadlock detector
  fires after 3 rounds of alternation, I play C, alternator plays C
  too (alternator's pattern: C,D,C,D,... so on the round AFTER my
  forced C, alternator plays D). This actually DOESN'T fix it - my C
  + opp D, my D + opp C, deadlock break fails to lock in cooperation
  with alternator. Predicted ~490 like TFT-vs-alternator, maybe a bit
  worse from wasted C's.
vs Self under noise: ~590 (like CTFT-self).

Overall: should rank #1 or top-3 by beating CTFT vs TFT-family pairs
asymmetrically (deadlock break) while keeping CTFT's apology efficiency.
Main risk: against alternator and random, no randomness-counter
exploitation - losing ~5-10 points vs omega. Against grim/prober, no
brittleness - gaining ~15-25 points vs omega. Net should be positive.
"""

D_THRESHOLD = 3


def _replay(my_history, opp_history):
    """Reconstruct intended moves and deadlock counter over past rounds.

    Returns (intended_list, was_break_list, deadlock_counter) reflecting
    the state AFTER `n = len(my_history)` past rounds.

    was_break_list[i] is True if our intended move on round i was a
    forced deadlock-break C (so we don't immediately repunish on the
    next round's pattern).
    """
    intended = []
    was_break = []
    dead_c = 0
    n = len(my_history)
    for i in range(n):
        # Decide intended move at round i using only data < i.
        broke_deadlock = False
        if i == 0:
            intended_i = "C"
        else:
            # Apology window first.
            apologise = False
            for k in (i - 2, i - 1):
                if k < 0:
                    continue
                if intended[k] == "C" and my_history[k] == "D":
                    apologise = True
                    break
            if apologise:
                intended_i = "C"
            elif dead_c >= D_THRESHOLD:
                intended_i = "C"
                broke_deadlock = True
            else:
                intended_i = opp_history[i - 1]  # TFT mirror
        intended.append(intended_i)
        was_break.append(broke_deadlock)

        # Update deadlock counter using observed history.
        if i >= 1:
            my_obs = my_history[i]
            opp_obs = opp_history[i]
            my_prev = my_history[i - 1]
            opp_prev = opp_history[i - 1]
            if (my_obs != opp_obs
                    and my_prev != opp_prev
                    and my_obs != my_prev):
                dead_c += 1
            else:
                dead_c = 0
    return intended, was_break, dead_c


def choose_move(my_history, opp_history):
    n = len(my_history)
    if n == 0:
        return "C"
    intended, _, dead_c = _replay(my_history, opp_history)
    # Apology window for round n.
    for k in (n - 2, n - 1):
        if k < 0:
            continue
        if intended[k] == "C" and my_history[k] == "D":
            return "C"
    if dead_c >= D_THRESHOLD:
        return "C"
    return opp_history[-1]
