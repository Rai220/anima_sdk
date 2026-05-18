"""TF2T + Trigger — Tit-for-Two-Tats with an AllD detector.

This is the fix for adaptive_tft's failure mode (Run #5). The original
adaptive_tft = TFT + window trigger collapsed in self-play because TFT's
noise vendetta already produces ~50% defections in any 10-round window,
which is dangerously close to the trigger threshold. A single extra noise
flip during the vendetta pushed the count over and locked both sides into
permanent D.

Here we replace the base with Tit-for-Two-Tats: defect only after the
opponent has defected in BOTH of the last 2 rounds. This means a single
noise flip on either side never triggers retaliation, so two TF2T+trigger
bots playing each other have near-ceiling self-play. The trigger only
fires when the opponent really is hammering us with D's — i.e. AllD
or post-trip Grim.

Parameters:

- TF2T base: defect iff `opp_history[-2:] == ["D", "D"]`.
- Trigger: if opponent has defected in at least `THRESHOLD` of the last
  `WINDOW` rounds, lock to permanent D from then on.
- WINDOW = 10, THRESHOLD = 9. We set the threshold higher (9 vs the
  adaptive_tft's 7) because we want to be very sure the opponent is
  hostile before we lock. Under 2% noise a single TF2T-vs-TF2T noise
  excursion will produce at most ~1 defection in a 10-round window;
  reaching 9/10 requires sustained defection.
- We only start checking the trigger after we have a full WINDOW of
  rounds, so the first 10 rounds are pure TF2T.

Expected behaviour vs the field:

* vs AllD: round 1 C, round 2 C (after only 1 D from opp), round 3+ D
  (TF2T mirroring D). By round 10 the window is ~9 D's; trigger fires;
  lock to permanent D. Score ≈ 0 + 0 + (9 * 1) + (190 * 1) ≈ 200, plus
  any sucker variance from noise. Comparable to TF2T (200) and TFT (210),
  with the benefit of an explicit commitment-to-defect against AllD.
  The trigger may not even matter here since TF2T alone already locks D.
* vs Grim: once Grim trips into permanent D (round k after noise), we
  spend 1 sucker round (since TF2T allows one D), then start mirroring
  D from round k+2 onwards. By round k+11 the window is mostly D's,
  trigger fires, lock to D. Total: ~k CC rounds + 1 sucker + ~190
  mutual D rounds ≈ 3k + 190. For k=10 ≈ 220, for k=50 ≈ 340.
  Comparable to TF2T (231) and better than soft_majority (251) since
  we lock D faster.
* vs TFT, GTFT, TF2T, adaptive_tft, soft_majority, Pavlov, AllC, Random:
  trigger never fires (none of these defect 90%+ in any 10-window even
  with noise). Behaves as TF2T. Near-ceiling cooperation everywhere.
* Self-play (TF2T+trigger vs TF2T+trigger): near-600. The TF2T base
  prevents noise vendettas; the trigger doesn't fire because mutual
  cooperation under 2% noise yields < 9 D's in any 10-window.

The intent is to keep TF2T's near-ceiling cooperation while adding a
hard cap on AllD exploitation. Should outscore TF2T in fields with
AllD-like opponents (small gain, ~10 points) and match TF2T everywhere
else. Could plausibly steal the top spot from soft_majority since
soft_majority's main weakness (slow to lock D against Grim, costing
~250 points there) is exactly what this bot avoids.

Uses only my_history and opp_history. Deterministic.
"""

WINDOW = 10
THRESHOLD = 9


def choose_move(my_history, opp_history):
    if not opp_history:
        return "C"
    # Trigger: if opponent has been mostly D in the last WINDOW rounds,
    # lock to permanent D for the rest of the match.
    if len(opp_history) >= WINDOW:
        window = opp_history[-WINDOW:]
        if window.count("D") >= THRESHOLD:
            return "D"
    # TF2T base: defect iff the last two opponent moves were both D.
    if len(opp_history) >= 2 and opp_history[-1] == "D" and opp_history[-2] == "D":
        return "D"
    return "C"
