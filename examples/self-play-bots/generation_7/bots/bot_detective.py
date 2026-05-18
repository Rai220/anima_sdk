"""Detective: a fingerprint-based bot that probes opponent retaliation,
then either exploits forgivers via D/C alternation or falls back to
Tit-For-Tat against reciprocators.

Probe phase (rounds 1-3): play D, C, C.

This is the classic Axelrod-test fingerprint, shortened from 4 rounds to
3 to leave more rounds for exploitation in a 200-round match.

After the probe (round 4 onwards):

- If opponent defected at least once during the probe (rounds 1-3):
  the opponent is a reciprocator. Play TFT (mirror their last move)
  for the rest of the game.
- If opponent stayed cooperative throughout the probe: the opponent
  is either AllC, TF2T, or some other bot that does not punish a
  single D. Try to extract value by ALTERNATING D, C starting with D.
  Average payoff in this mode against a non-punisher = (T + R) / 2 =
  (5 + 3) / 2 = 4.0 per round — better than TFT's 3.0 against AllC.

Safety net during exploit mode: if opponent's post-probe D rate exceeds
~15% (well above the ~2% noise floor), the opponent has become hostile
in response to the alternation, and we fall back to TFT to avoid a
DC-DD spiral. The threshold also requires at least 4 actual D events,
so a few stray noise flips do not trigger fallback prematurely.

Expected behaviour against the current pantheon:

- vs AllC: probe gives [C,C,C] -> exploit mode forever. ~799 (huge win).
- vs TF2T: probe gives [C,C,C] (TF2T waits for 2 consecutive D's).
  Alternation D-C-D-C never produces 2 consecutive D's, so TF2T stays
  in C mode forever. ~799 (huge win).
- vs TFT: probe gives [C,D,C] (TFT punishes the D in round 1, then
  forgives my C in round 2). Has a D in probe -> TFT mode -> ~599
  (slightly above mutual CC ceiling because of R1's T=5 bonus).
- vs Soft Majority: probe gives [C,D,C] (SM defects in R2 after seeing
  a single D, then re-cooperates when tally re-balances). TFT mode.
- vs reciprocators (CTFT, ATFT, GTFT, Grim, Pavlov): probe almost
  certainly gives at least one D -> TFT mode for the rest.
- vs AllD: probe gives [D,D,D] -> TFT mode -> mutual DD forever after
  the probe.
- vs another Detective (self-play): both play [D,C,C] in probe, so
  both see [D,C,C] in opp_probe -> TFT mode for both -> mutual CC
  from round 4 onwards.

The big bets are AllC and TF2T: these two opponents give ~+200 each
relative to the reciprocator block's typical 580-600 cells. If they
appear together in the pool, Detective gains ~400 points / 2 cells =
~30 points to the row average — enough to potentially overtake the
Soft Majority leader.
"""


def choose_move(my_history, opp_history):
    n = len(my_history)
    # Probe phase: D, C, C.
    if n == 0:
        return "D"
    if n == 1 or n == 2:
        return "C"
    # Post-probe decision.
    opp_probe = opp_history[:3]
    if opp_probe.count("D") >= 1:
        # Opponent retaliated during probe. Play TFT.
        return "C" if opp_history[-1] == "C" else "D"
    # Opponent did NOT retaliate. Check whether they have started
    # retaliating post-probe (could be a late-trigger bot like Grim
    # that didn't see enough provocation in the first 3 rounds, or
    # a bulk-statistics bot whose tally has finally flipped).
    post = opp_history[3:]
    post_n = len(post)
    post_d = post.count("D")
    if post_d >= 4 and post_d / post_n > 0.15:
        # Opponent's D rate is well above noise. Fall back to TFT.
        return "C" if opp_history[-1] == "C" else "D"
    # Exploit mode: alternate D, C starting with D at round 4 (n=3).
    return "D" if (n - 3) % 2 == 0 else "C"
