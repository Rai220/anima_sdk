# Bot API

Every bot is a single `.py` file in this directory, named `bot_*.py`.
It must expose:

```python
def choose_move(my_history: list[str], opp_history: list[str]) -> str:
    """Return 'C' (cooperate) or 'D' (defect).

    On the very first round both histories are empty lists.
    Each subsequent round, the histories contain all PREVIOUSLY
    PLAYED (post-noise) moves in the order they occurred. They
    are of equal length, equal to the round index.
    """
```

## Rules

- Return value must be exactly `'C'` or `'D'`. Anything else is
  scored as `'D'` for that round.
- An exception is also scored as `'D'`.
- The bot may use anything from the standard library: `random`,
  `collections`, `itertools`, etc. **No imports** of third-party
  packages, no file I/O, no network.
- The bot must NOT inspect or import other bots' source code.
- The bot must NOT keep mutable module-level state that persists
  across rounds. The engine assumes the function is **pure**:
  the same `(my_history, opp_history)` yields the same probability
  distribution over the next move. Self-play imports the bot module
  ONCE and calls the same `choose_move` for both sides, so any
  shared module-level state will be corrupted by the other side's
  calls. Reconstruct any needed memory from the histories at each
  call.
- If you need a private RNG (e.g. for random bots), create a fresh
  `random.Random()` instance inside `choose_move`. Do not rely on
  the global `random` state.

## Histories and noise

The engine applies noise AFTER `choose_move` returns: each move is
flipped with probability `--noise` (default 0.02) before being
appended to the histories and scored. So `my_history` reflects what
the engine actually played for me, not what I tried to play. If you
want to know your intended move, replay your own logic.

## Payoffs

| me \ opp | C       | D       |
|----------|---------|---------|
| **C**    | 3 / 3   | 0 / 5   |
| **D**    | 5 / 0   | 1 / 1   |
