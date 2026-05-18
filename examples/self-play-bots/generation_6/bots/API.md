# Bot API

Every bot is a Python file in `bots/` named `bot_<idea>.py`. It must expose:

```python
def choose_move(my_history: list[str], opp_history: list[str]) -> str:
    """Return 'C' (cooperate) or 'D' (defect)."""
```

Rules:

- Both histories are equal-length lists of past moves. They are empty on the
  first round.
- The history is what was **observed** (after noise). With `--noise` > 0, a
  bot's intended move may have been flipped before being recorded -- both
  bots see the same observed history.
- Anything except the strings `"C"` or `"D"` (including exceptions) counts
  as `"D"` for that round.
- Bots may **not** read files, open sockets, call subprocesses, install
  packages, or import non-stdlib modules. They may use `random` only if
  they seed it themselves or use a module-level `random.Random(seed)`.
  Tournaments must remain reproducible from `--seed`.
- Bots may not inspect the opponent's source or any global state -- only
  `my_history` and `opp_history`.

Conventions:

- Keep the function pure-ish: no module-level mutable state that crosses
  matches. A new match starts with fresh empty histories.
- Top of file: one-paragraph docstring explaining the strategy.

Single-match invocation: `python3 tournament.py bots/X.py bots/Y.py`.
