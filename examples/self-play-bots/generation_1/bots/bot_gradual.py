"""GRADUAL (Beaufils 1996).

Cooperates by default. When the opponent defects for the N-th time
(cumulative count, ever), the strategy retaliates by playing D for N
consecutive rounds, then plays C for 2 rounds (the "reconciliation
period"), and then returns to default cooperation.

While inside a punishment-or-reconciliation sequence, opponent moves are
ignored as triggers (we do not start a new sequence mid-sequence). New
defections during a sequence still count toward the cumulative D total
that will determine the *next* punishment length.

Properties:
- nice: never defects first (default mode is C).
- retaliatory: every defection is eventually punished, and the
  punishment grows with the opponent's defection count.
- forgiving: each punishment ends with 2 calming Cs.
- non-envious: focused on building cooperation, not on score gaps.

Self-play under noise: a single accidental D triggers exactly one
D-then-2-Cs cycle on the opposite side, then both return to C. Recovery
takes ~3-4 rounds per noise flip.

Statelessness: state is reconstructed from `opp_history` each call by
replaying the deterministic state machine from round 0.
"""


def choose_move(my_history: list[str], opp_history: list[str]) -> str:
    state = "normal"     # "normal" | "punishing" | "calming"
    pending = 0          # remaining D's (punishing) or C's (calming)
    t_total = len(opp_history)
    move = "C"
    for t in range(t_total + 1):
        # Trigger from normal mode: opp just defected last round.
        if state == "normal" and t > 0 and opp_history[t - 1] == "D":
            total_d = opp_history[:t].count("D")
            state = "punishing"
            pending = total_d  # play D this round + (total_d - 1) more.
        if state == "punishing":
            move = "D"
            pending -= 1
            if pending == 0:
                state = "calming"
                pending = 2
        elif state == "calming":
            move = "C"
            pending -= 1
            if pending == 0:
                state = "normal"
        else:
            move = "C"
        if t == t_total:
            return move
    return move
