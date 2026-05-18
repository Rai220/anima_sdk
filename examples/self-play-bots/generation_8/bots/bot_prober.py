"""Prober — Axelrod's classic "test then choose policy" strategy.

Opens with a fixed three-move probe sequence: D, C, C. After that,
look at how the opponent reacted in rounds 2 and 3 (their *first two
opportunities to retaliate* against our round-1 D):

* If the opponent played C in both rounds 2 and 3 (i.e. did not
  retaliate even though we kicked them in round 1) -> they look like
  a "sucker" / unconditional cooperator. Switch to permanent D and
  exploit them.

* Otherwise -> switch to Tit-for-Tat. They retaliated at least once,
  so they have some reciprocity, and TFT is the safe default.

The point of the probe is to *gather information cheaply* about the
opponent's type. Rounds 1-3 cost at most a few points (one provocation
and two cooperations); the verdict then guides the next ~197 rounds.

Expected behaviour under 2% noise:

* **vs AllC**: rounds 2 and 3 are C (modulo a ~4% chance of a noise
  flip). Verdict: exploit. We get round-1 T=5, rounds 2-3 R=3+R=3 (or
  some sucker payoff if noise), then T=5 for ~197 rounds. Per match
  ~ 5 + 3 + 3 + 5*197 = 996, near the theoretical max of 1000. AllC
  gets ~ 0 + 3 + 3 + 0 = 6. **Best matchup for any strategy.**

* **vs AllD**: rounds 2 and 3 are D. Verdict: TFT. Probe cost: round 1
  = D vs D (1+1), round 2 = C vs D (0+5, *one sucker round*), round 3
  = C vs D (0+5, *another sucker round*). After that TFT pins to D.
  Score ~ 1 + 0 + 0 + 1*197 = 198. About -12 vs plain TFT's 210.7.

* **vs TFT**: round 1 = D vs C, round 2 = C vs D (TFT mirrors our D),
  round 3 = C vs C (TFT mirrors our C). Round 2 was D -> verdict: TFT.
  Subsequent play is TFT-vs-TFT modulo a slightly different starting
  phase. Expected ~ 495 (the TFT-vs-TFT noise figure).

* **vs Grim**: round 1 D trips Grim. Round 2 Grim plays D, round 3 D.
  Verdict: TFT. TFT vs tripped Grim = locked D after a few rounds.
  ~200. Bad but unavoidable given the probe.

* **vs soft_majority / TF2T**: round 1 = D. Round 2: soft_majority
  looks at history of one D, has C-majority not satisfied (1 D, 0 C)
  so plays D. Round 3: history has 1 D, 1 C, equal -> plays D (soft
  majority cooperates only if C >= D strictly, depends on impl). Hmm,
  in our soft_majority impl `c >= d` so equal counts -> C. Anyway,
  most likely at least one D in rounds 2-3 -> verdict: TFT. Cost:
  -10 to -15 from the cooperative ceiling. Similar story for TF2T:
  it tolerates one D, won't retaliate in rounds 2-3, so will play
  C twice -> *verdict: EXPLOIT*. **This is a problem**: TF2T is one
  of the top-3 patient cooperators, and Prober will *misclassify it
  as a sucker* and then defect for the rest of the match. TF2T's own
  forgiveness becomes the trap.

  Concretely vs TF2T: round 1 D vs C, rounds 2-3 C vs C (TF2T tolerates
  one D so plays C). Verdict: exploit. Then we play D vs TF2T's
  reciprocation pattern. TF2T sees 1 D from us in rounds 1, then 0
  from rounds 2-3, then D from us in round 4 -> still only "one D
  in window of last 2" so still C. Then D from us in round 5 -> *two
  D's in a row* -> TF2T finally plays D in round 6. Then we keep
  playing D (we're locked in exploit mode), TF2T plays D (responding
  to our continuous D). Mutual D from round 6 to end. Score ~ 5*5 +
  1*195 = 220. TF2T score ~ 0*5 + 1*195 = 195. **We beat TF2T
  significantly** at the cost of mutually-D for 195 rounds.

  This is the *interesting* prediction: Prober should knock TF2T down
  in the rankings by extracting suckers from it, then refusing to
  cooperate. The cost is that we ourselves don't get the patient
  cooperator's high score (we settle for ~220 instead of ~590 mutual
  CC). But we *also* deny TF2T those points, which is the point of
  an evolutionary tournament: relative scores matter for ranking.

* **vs GTFT (generous TFT)**: round 1 D, GTFT might forgive (10%
  forgiveness rate). Round 2 likely C. Round 3 likely C. Verdict:
  *may exploit*, depending on luck. If exploit, similar TF2T-style
  takedown of a patient cooperator.

* **vs Pavlov**: round 1 D vs C (P sees us D, opp = C -> Pavlov win),
  Pavlov plays C in round 2 (win-stay after CC? no, Pavlov reacts to
  *its own last + opp's last*; Pavlov got 0 in round 1 (lose) so it
  shifts: plays D in round 2). So round 2 = C vs D. Round 3: Pavlov
  last move D, opp last move C -> got 5 (win) -> stay -> D again.
  Round 3 = C vs D. Both rounds 2 and 3 are D from opp -> verdict:
  TFT. Then TFT vs Pavlov is the usual ~420.

* **Self-play (Prober vs Prober)**: both play D, C, C in rounds 1-3.
  Each sees opp = C in rounds 2 and 3 -> *both verdict: exploit*.
  Then both play D forever. Total: round 1 mutual D (1+1), round 2
  mutual C (3+3), round 3 mutual C (3+3), rounds 4-200 mutual D
  (1*197 each) = 1 + 3 + 3 + 197 = 204. **Self-play disaster.** This
  is Prober's classic weakness — it can't recognize itself as
  reciprocal because the probe response looks sucker-like.

In aggregate Prober is expected to rank middle-of-pack: huge wins vs
AllC (and maybe TF2T/GTFT depending on noise), modest losses vs the
reciprocators, terrible self-play, and identical-to-TFT against the
hard cases (AllD/Grim/SoftMaj). The interesting effect is
*third-party*: it should pull TF2T's score down by misclassifying it.

Real-world parallel: "throw a small insult and see who escalates".
Bullies and diplomatic actors both do this — a minor provocation that
costs little is a probe for the other party's response function. If
the response is appeasement, exploit; if it's retaliation, fall back
to normal relations. Same logic, same payoff structure.

Determinism: no randomness; choose_move depends only on histories.
"""

PROBE_OPENING = ["D", "C", "C"]


def choose_move(my_history, opp_history):
    rnd = len(my_history)

    # Phase 1: fixed 3-round opening probe.
    if rnd < len(PROBE_OPENING):
        return PROBE_OPENING[rnd]

    # End of round 3: classify opponent based on their rounds 2 and 3.
    # (opp_history[1] is opp's round-2 move, opp_history[2] is round 3.)
    sucker_signal = opp_history[1] == "C" and opp_history[2] == "C"

    if sucker_signal:
        # Opponent didn't retaliate against our round-1 D. Exploit.
        return "D"

    # Otherwise: switch to Tit-for-Tat.
    return opp_history[-1]
