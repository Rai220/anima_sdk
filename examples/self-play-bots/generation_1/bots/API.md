# Bot API

Each bot lives in a single file `bots/bot_<idea>.py` and exposes one function:

```python
def choose_move(my_history: list[str], opp_history: list[str]) -> str:
    """Return 'C' (cooperate) or 'D' (defect).

    On the first round both histories are empty.
    On round k (0-indexed), len(my_history) == len(opp_history) == k.
    The histories are the *observed* moves after noise has been applied,
    i.e. exactly what each side saw the other do.
    """
```

Rules of engagement enforced by `tournament.py`:

- Anything other than `'C'` or `'D'` is treated as `'D'`.
- Any uncaught exception is treated as `'D'`.
- A bot must NOT read/write files, open sockets, spawn subprocesses, or
  inspect the opponent's source. Only `my_history` and `opp_history` are
  legitimate input.
- Standard library only. No `pip install`.

Payoffs (mine / opponent):

|       | C        | D        |
|-------|----------|----------|
| **C** | 3 / 3    | 0 / 5    |
| **D** | 5 / 0    | 1 / 1    |

Noise: with probability `--noise` the move you returned is flipped before
scoring and before being recorded into either history. Both players see the
post-noise move.

Files starting with `_` (e.g. `bots/_failed/...`) are ignored by the engine.
