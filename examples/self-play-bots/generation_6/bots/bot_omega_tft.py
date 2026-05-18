"""Omega Tit-for-Tat (Slany & Kienreich 2007).

TFT plus two safety overrides:

  1. **Deadlock detection**: if the last few rounds show classic CD/DC
     alternation (we and opp keep mirroring each other out of phase),
     unilaterally play C once to break the deadlock. This rescues
     TFT-vs-TFT pairs that fell into an echo after a noise flip.
  2. **Randomness / hopelessness detection**: count opp's "unjustified
     defections" — a D when we just played C, or D in self-consistent
     patterns we can't reconcile with reciprocal play. If this count
     crosses a threshold, give up trying to cooperate and play AllD
     for the rest of the match.

Concretely, on each round i:

  - i == 0: play C.
  - If randomness_counter >= R_THRESHOLD: play D forever.
  - Else if deadlock_counter >= D_THRESHOLD: play C this round.
  - Else: TFT (mirror opp's last observed move).

Counters are updated AFTER each round, looking at observed history:

  - randomness_counter:
      +2 if my_last == "C" and opp_last == "D"   (clean betrayal)
      +1 if my_last == "D" and opp_last == "C"   (opp inexplicably gave us a C)
      reset to 0 if my_last == opp_last           (we agree, things are fine)
  - deadlock_counter:
      +1 if (my_last != opp_last) and (my_prev != opp_prev) and (my_last != my_prev)
         (classic alternating CD/DC pattern, both swapping each round)
      reset to 0 otherwise

Thresholds (R=8, D=3) are taken from the original paper's defaults.
They give a generous noise budget (~4 betrayals tolerated under 2%
noise over 200 rounds) before declaring opp "random / hopeless", and
a tight deadlock window so a single bad echo gets broken in ~3 rounds.

Stateless implementation: deterministic given (my_history, opp_history),
so we reconstruct counters by replaying from round 0 on every call.

Predicted behaviour:

  - Omega vs grim, AllD: should still DD-floor, but the deadlock counter
    might give it a free C-burst that grim/AllD exploits. Net: ~205-220
    (slightly worse than TFT's 200 because of wasted apology C's). NOT
    a fix for grim/AllD.
  - Omega vs TFT, CTFT, GTFT under noise: deadlock detector should help
    break CD/DC echoes faster than TFT. Predicted ~520+ vs TFT (vs
    TFT's 533 in Run 011), comparable to GTFT.
  - Omega vs alternator: alternator's CDCD... triggers BOTH counters.
    Randomness threshold likely hits ~round 16, then AllD. Predicted
    similar to TFT-vs-alternator (~495) or slightly worse due to
    early-game C losses.
  - Omega vs prober: prober's early D's add to randomness counter.
    If threshold hit, switch to AllD. Otherwise TFT.
  - Omega self-play under noise: deadlock detector cleanly breaks
    CD/DC echoes from noise. Predicted ~580 (similar to GTFT-self).

Main hypothesis: Omega's deadlock-breaker recovers CD echoes that TFT
locks into, similar to CTFT but via a different mechanism (pattern-
detected vs intent-attributed). Should rank in the same #2-#4 tier.
"""

R_THRESHOLD = 8
D_THRESHOLD = 3


def _replay(my_history, opp_history):
    """Replay rule round-by-round to reconstruct intended moves + counters.

    Returns (intended_list, was_break_list, randomness_counter,
             deadlock_counter, alld_mode_flag) after `n` past rounds.

    `was_break_list[i] is True` if round i's intended C was a forced
    deadlock-break C (not a TFT mirror). We skip randomness updates on
    rounds following our own deadlock break, because opp had no chance
    to "agree" with our unilateral C yet.
    """
    intended = []
    was_break = []
    rand_c = 0
    dead_c = 0
    alld_mode = False
    n = len(my_history)
    for i in range(n):
        # Decide what we INTENDED on round i (using only data < i).
        broke_deadlock = False
        if alld_mode:
            intended_i = "D"
        elif i == 0:
            intended_i = "C"
        elif rand_c >= R_THRESHOLD:
            alld_mode = True
            intended_i = "D"
        elif dead_c >= D_THRESHOLD:
            intended_i = "C"
            broke_deadlock = True
        else:
            intended_i = opp_history[i - 1]  # TFT mirror
        intended.append(intended_i)
        was_break.append(broke_deadlock)

        # Update counters based on OBSERVED moves of round i (now visible).
        my_obs = my_history[i]
        opp_obs = opp_history[i]
        # Randomness counter — skipped if this round OR the previous round
        # was our deadlock-break C. Opp can't be expected to reciprocate
        # immediately (they decide round i simultaneously with us, so the
        # earliest opp can reflect our break is round i+1, and even then
        # only if they're a mirror-type bot).
        skip_rand = broke_deadlock or (i >= 1 and was_break[i - 1])
        if not skip_rand:
            if my_obs == "C" and opp_obs == "D":
                rand_c += 2
            elif my_obs == "D" and opp_obs == "C":
                rand_c += 1
            elif my_obs == opp_obs:
                rand_c = 0
        # Deadlock counter logic.
        if i >= 1:
            my_prev = my_history[i - 1]
            opp_prev = opp_history[i - 1]
            if (my_obs != opp_obs
                    and my_prev != opp_prev
                    and my_obs != my_prev):
                dead_c += 1
            else:
                dead_c = 0
    return intended, was_break, rand_c, dead_c, alld_mode


def choose_move(my_history, opp_history):
    n = len(my_history)
    if n == 0:
        return "C"
    _, _, rand_c, dead_c, alld_mode = _replay(my_history, opp_history)
    if alld_mode or rand_c >= R_THRESHOLD:
        return "D"
    if dead_c >= D_THRESHOLD:
        return "C"
    # Default: TFT mirror of opp's last observed move.
    return opp_history[-1]
