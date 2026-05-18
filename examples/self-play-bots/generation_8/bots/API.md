# Bot API

Every bot lives in a single file `bots/bot_<name>.py` and exposes one function:

```python
def choose_move(my_history: list[str], opp_history: list[str]) -> str:
    """Return 'C' (cooperate) or 'D' (defect).

    On the first move both histories are empty.
    `my_history[i]` is the move I played in round i.
    `opp_history[i]` is the move the opponent played in round i.
    Both lists have the same length and grow by one each round.
    """
```

## Rules

- Return value must be exactly `'C'` or `'D'`. Anything else (None, lowercase,
  exception, infinite loop / timeout) is counted as `'D'` for that round.
- Bots see only `my_history` and `opp_history`. No file I/O, no network, no
  inspecting the opponent's source. Stdlib only.
- Bots are pure-ish: they may use `random` (the tournament reseeds it per
  match through its own RNG, so bot randomness is independent).
- The same `choose_move` is called every round; bots may keep no global
  state between matches (each match is fresh).

## Payoff matrix (per round)

| Me \ Opp | C    | D    |
|----------|------|------|
| **C**    | 3/3  | 0/5  |
| **D**    | 5/0  | 1/1  |

## Tournament knobs

- `--rounds` (default 200) — round count per match.
- `--noise` (default 0.02) — each side's move is flipped with this
  probability *after* the bot returned it (the bot does not see the flipped
  version directly; it sees the post-noise move of the opponent on the next
  round, which is what actually got scored).
- `--repeat` (default 3) — each pairing is played this many times with
  different RNG seeds and the scores are averaged.
