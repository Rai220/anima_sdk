"""Shadow: late-probe variant of Detective.

The lesson from Run 009 was that Detective's probe (D, C, C in the first
3 rounds) is too cheap for the exploiters it bait-and-switches (AllC,
TF2T, Soft Majority) but too expensive against retaliators (Grim, AllD,
the reciprocator block). Detective bought ~200 points against AllC/TF2T
and paid ~200 points against Grim/AllD — net wash, and self-play
collapses to 448 because of probe-misreading under noise.

Shadow flips the cost structure:

1. **Reconnaissance** (rounds 0..PROBE_ROUND-1, default 30): play pure
   Tit-For-Tat. No provocation, no premature signal. Against any
   reciprocator this is mutual CC (modulo noise hiccups). Against Grim
   this avoids the upfront D that would lock it permanently. Against
   AllD this is identical to TFT.
2. **Decision** (round PROBE_ROUND): inspect the opponent's D rate over
   the recon window. If it is at or below the noise floor (≤ 5%), the
   opponent has not punished any noise events — almost certainly a
   tolerant cooperator (AllC, TF2T, Soft Majority, or another Shadow
   that is still in recon). Probe with a single D. Otherwise continue
   TFT for the rest of the match.
3. **Test phase** (rounds PROBE_ROUND+1 .. PROBE_ROUND+TEST_LEN):
   play C unconditionally. This gives a retaliator block time to
   "discharge" its single retaliation cleanly — TFT will retaliate once
   in round PROBE_ROUND+1 and then re-cooperate from PROBE_ROUND+2
   onwards, which lets us re-enter TFT in mutual CC mode without a
   cascade.
4. **Verdict** (round PROBE_ROUND+TEST_LEN+1 onwards):
   - If opponent defected at least once during the test phase, they
     are a retaliator (e.g. TFT, CTFT, ATFT, Pavlov, Grim). Drop the
     exploit plan and play TFT for the remainder.
   - If opponent stayed pure C through the test phase, they are a
     tolerant cooperator. Enter exploit mode and alternate D, C with
     D first, banking (T+R)/2 = 4.0 per round on average.
5. **Exploit guard rails**:
   - **Sync detector**: another Shadow against me will probe at the
     same round and run the same alternation. After two synchronized
     mutual D's, switch to permanent C — this is the cheapest
     equilibrium with another Shadow (better than oscillating DC/CD).
   - **Late retaliation guard**: if the opponent's D rate over the
     last 12 rounds exceeds 25%, an opponent that initially looked
     tolerant has started fighting back (e.g. a delayed-trigger
     bulk-statistics bot). Fall back to TFT.

Predicted cells (compare to Detective in Run 009 — same payoff matrix
and noise but Shadow has 30 free rounds at the front):

- vs AllC: 30 rounds × 3 (recon CC) = 90, 1 probe T=5, 3 test C=9,
  ~166 rounds × 4.0 alternation = 664. ~768.  (Detective: 779)
- vs TF2T: ~768 (TF2T never sees two consecutive D, exploit holds).
- vs Soft Majority: 90 + 5 + 9 + ~664 = ~768 — IF SM stays in C mode
  (it will because D count stays below C count over 200 rounds).
  (Detective managed only 605 here.)
- vs TFT: 30 rounds CC ~88, probe T=5, retaliation S=0, test C-C-C ~6,
  recovery to mutual CC ~165 rounds of TFT-vs-TFT in noise ≈ 412.
  ~511. (Detective: ~500.)
- vs Grim: identical to TFT vs Grim for the first 30 rounds; if no noise
  trigger, the probe at round 30 fires Grim into permanent D. We then
  test-C and revert to TFT (which produces mutual DD against locked
  Grim). Expected ~210. (Detective: 212.)
- vs AllD: opp_d_rate = 1.0 → never probe → pure TFT vs AllD = 199.
- vs Pavlov: 30 rounds of TFT-vs-Pavlov-in-CC mode + a probe that
  flips Pavlov to D for a chaotic stretch. Test fails, revert to TFT,
  which produces typical TFT-vs-Pavlov churn (≈ 444).
- vs Detective: Detective probes [D,C,C], I play TFT [C,D,C]. Detective
  sees ≥1 D in my probe → TFT mode for the remainder. After round 3
  we're both in TFT. At round 30, opp_d_rate from Detective is 1/30 ≈
  0.033 ≤ 0.05 → I probe again. Detective (TFT-mode) retaliates once
  → test fails → revert to TFT → mutual CC recovery. Score ~565.
- vs Random: opp_d_rate ~0.5 → never probe → TFT vs Random ~450.
- self-play: 30 rounds TFT (~85), round 30 DD (1), test rounds 31-33
  CC (9), exploit triggers but sync-detector kicks in by round 37 →
  recover to permanent CC for ~163 rounds (~489). Total ~589.

Row average prediction: weighted mean of the above over 13 opponents
≈ (768+768+768+511+210+199+444+565+450+589 + 2 other reciprocator
cells around 565) / 13 ≈ 525-540 — potentially #1 over Soft Majority
(508.85).

The big question is robustness: does the sync detector reliably fire
in self-play under 0.02 noise? Two synchronized D's must survive
noise. Probability of a single intended D surviving on both sides =
0.98^2 = 0.96; probability over the two intended D-rounds (34 and 36)
of getting both surviving = ~0.85. So ~85% of self-play matches should
trigger the sync detector by round 37; the other 15% will keep
alternating D-C until either a late noise alignment triggers detection
or the match ends.
"""

PROBE_ROUND = 30
TEST_LEN = 3
RECENT_WINDOW = 12
RECENT_D_THRESHOLD = 0.25
SYNC_DD_REQUIRED = 2
PROBE_D_RATE_THRESHOLD = 0.05


def _tft(opp_history):
    return "C" if opp_history[-1] == "C" else "D"


def _would_have_probed(opp_prefix):
    """Re-derive intent: would Shadow have probed given opp's
    first PROBE_ROUND moves? Pure function of the prefix."""
    if len(opp_prefix) < PROBE_ROUND:
        return False
    d_count = opp_prefix[:PROBE_ROUND].count("D")
    return (d_count / PROBE_ROUND) <= PROBE_D_RATE_THRESHOLD


def choose_move(my_history, opp_history):
    n = len(my_history)

    # Phase 1: recon (rounds 0 .. PROBE_ROUND-1). Pure TFT with C opener.
    if n == 0:
        return "C"
    if n < PROBE_ROUND:
        return _tft(opp_history)

    # Phase 2: round PROBE_ROUND — decision point.
    if n == PROBE_ROUND:
        if _would_have_probed(opp_history):
            return "D"
        return _tft(opp_history)

    # Phase 3 onwards: re-derive whether I probed at PROBE_ROUND.
    if not _would_have_probed(opp_history[:PROBE_ROUND]):
        # Never entered probe path. Continue pure TFT.
        return _tft(opp_history)

    # I intended to probe at round PROBE_ROUND.
    test_end = PROBE_ROUND + 1 + TEST_LEN  # first post-test round index.

    # Test phase: play C, give opponent room to retaliate or stay calm.
    if n < test_end:
        return "C"

    # Verdict on the test phase.
    opp_test = opp_history[PROBE_ROUND + 1:test_end]
    if opp_test.count("D") >= 1:
        # Retaliator detected. Fall back to TFT for the rest of the match.
        return _tft(opp_history)

    # Test passed: opponent tolerates a probe. Enter exploit phase.
    my_post = my_history[test_end:]
    opp_post = opp_history[test_end:]

    # Sync detector: another Shadow against me will mirror my D-rounds.
    sync_dd = sum(
        1 for a, b in zip(my_post, opp_post) if a == "D" and b == "D"
    )
    if sync_dd >= SYNC_DD_REQUIRED:
        return "C"

    # Late retaliation guard: opp may be a slow-tally bot that has just
    # started defecting. Switch to TFT if recent window is hostile.
    if len(opp_post) >= RECENT_WINDOW:
        recent = opp_post[-RECENT_WINDOW:]
        if recent.count("D") / RECENT_WINDOW > RECENT_D_THRESHOLD:
            return _tft(opp_history)

    # Default exploit: D, C alternation starting with D at round test_end.
    return "D" if (n - test_end) % 2 == 0 else "C"
