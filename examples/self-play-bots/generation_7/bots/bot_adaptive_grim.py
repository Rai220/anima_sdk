"""Adaptive Grim: Grim Trigger with periodic forgiveness probes.

Vanilla Grim's lethal weakness is noise: a single accidental D
from an otherwise-cooperative opponent locks both into permanent
DD for the rest of the match. In a 200-round match with noise=0.02
this is expected to happen ~4 times per side, and vanilla Grim
"dies" on the first one — losing roughly 199 * 2 = ~400 points of
foregone CC against a peaceful opponent (e.g. TFT, GTFT, AllC).

Adaptive Grim keeps Grim's heavy-handed punishment but adds an
"olive branch" mechanism: periodically test whether the opponent
is willing to come back to cooperation.

Mechanism (stateless, reconstructed from history each call):

1. Start in `cooperate` mode. Play C until opp plays D.
2. On the first D from opp (while in `cooperate`), enter `punish`
   mode and start a punish cycle.
3. Each punish cycle is K + PROBE rounds long:
   - K rounds of D (punishment)
   - PROBE rounds of C (olive branch)
4. At the end of each cycle, evaluate forgiveness:
   - If at least FORGIVE of opp's last PROBE moves were C
     (i.e. opp reciprocated the olive branch), return to
     `cooperate` mode.
   - Otherwise, start another K + PROBE cycle.

Parameters (chosen by analytic trade-off):
- K = 10. Long enough that AllD-style exploiters earn very little
  per cycle (10 D's for 10 rounds, then 2 free T=5 cells).
- PROBE = 2. Two C's give the opponent a clear, unambiguous signal
  that we are open to repair, and give us a 2-round window to
  observe their reply.
- FORGIVE = 1. Generous: even a single C from opp in the probe
  window triggers forgiveness. This is intentional because noise
  may corrupt one of the two replies, and the alternative (require
  both) is too brittle. AllD never plays C, so it never triggers
  forgiveness.

Predicted behaviour:
- vs AllD: 10 D's per cycle (P=1 each) + 2 C's per cycle (S=0
  each). Per-cycle score = 10 over 12 rounds = ~0.83/round.
  Total ~167 in 200 rounds (vs Grim's ~199). Cost ~30 pts.
- vs TFT after noise trigger: ~12-round recovery window then
  CC for the remaining ~188 rounds. Score per noise event ~17
  pts in window vs 36 in CC = 19-pt loss. With 4 events / match,
  total ~524 (vs Grim's ~289). Gain ~235 pts on that cell.
- vs Pavlov, GTFT, CTFT, ATFT, Soft Majority: similar — recovers
  from noise events that vanilla Grim would lock into DD.
- vs AllC: no clean-play trigger (AllC never plays D). Noise on
  AllC's side triggers us; we punish 10 rounds then probe; AllC
  plays C in probe → forgive. ~10-round episode per noise event;
  ~4 events / match ~80 pts loss vs perfect CC of 600 → ~520.
- self-play: a noise event triggers one side; the triggered side
  plays D for K rounds; the untriggered side sees D after one
  round of delay and triggers itself. Both then run staggered
  punish cycles. The forgiveness boundaries are also staggered,
  so the late-triggered side's probe-C falls in the early-side's
  D-phase but the early-side's probe-C falls in the late-side's
  D-phase too — they meet at FORGIVE=1 (one C in 2 probe replies
  is enough) most of the time. Expect ~13-round trigger
  episodes, ~4 per match → ~52 pts loss vs CC=600 → ~548.
- vs Random: opp plays D ~50% of the time. After first D,
  enter punish. During probe, opp plays C with p=0.5 in each
  probe round → P(at least one C) = 0.75. So 75% of cycles end
  in forgiveness — but then opp's next D re-triggers
  immediately. Net behaviour: roughly TFT-like vs Random.

Real-world analogue: a coalition partner who treats any breach
of agreement as a serious matter (long retaliation), but
periodically re-extends the offer of cooperation to test if the
breach was a one-off (noise) or a structural change (defector).
Most credible arms-control regimes work this way: long periods
of distrust after a violation, with periodic verification windows
that allow re-engagement if the partner is willing.
"""


K = 10           # rounds of D in each punish cycle
PROBE = 2        # rounds of C-probe at end of each cycle
FORGIVE = 1      # min C's in opp's last PROBE moves to forgive
CYCLE = K + PROBE


def choose_move(my_history, opp_history):
    # Round 0: always cooperate.
    if not opp_history:
        return "C"

    # Reconstruct mode by walking through opp_history.
    # `mode` is "cooperate" or "punish".
    # `made` = number of punish-mode decisions we have ALREADY
    # made in the current punish episode (and observed opp's
    # reply for). Starts at 0 when we trigger.
    mode = "cooperate"
    made = 0

    for t in range(len(opp_history)):
        if mode == "cooperate":
            if opp_history[t] == "D":
                mode = "punish"
                made = 0  # no punish-move made yet
        else:  # punish
            # Round t was a punish-mode decision; we now see opp's
            # reply at index t. Bump the counter.
            made += 1
            # Forgiveness check at the end of each full cycle.
            if made % CYCLE == 0:
                # Just completed CYCLE decisions: K D's + PROBE C's.
                # Probe replies live at opp_history[t-PROBE+1 .. t].
                start = max(0, t - PROBE + 1)
                probe_replies = opp_history[start : t + 1]
                if probe_replies.count("C") >= FORGIVE:
                    mode = "cooperate"
                    made = 0

    # Decide the next move.
    if mode == "cooperate":
        return "C"

    # In punish: the (made + 1)-th decision in this episode.
    # 0-indexed position in current cycle: pos = made % CYCLE.
    # pos in 0..K-1 → D, pos in K..CYCLE-1 → C.
    pos = made % CYCLE
    if pos < K:
        return "D"
    return "C"
