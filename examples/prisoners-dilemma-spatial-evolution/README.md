# Prisoners Dilemma Spatial Evolution

An `anima_sdk` task for evolving and auditing strategies in:

`/Users/krestnikov/giga/prisoners_dilemma`

Use this directory as the durable task wrapper. The actual game code, browser
experiment, strategies, reports, and GitHub Pages deployment live in the project
repository above.

Current goal: use the Codex harness to search for adaptive algorithms that react
to environmental shifts: noise, mutation flow, parasite pressure, disappearing
threats, and local ecological regimes. Each useful step should produce both a
measured result and a short research insight.

## Run

One agent step:

```bash
cd /Users/krestnikov/giga/anima_sdk/examples/prisoners-dilemma-spatial-evolution
bash run.sh
```

Loop current generation until `STOP`:

```bash
bash loop.sh
```

Meta-loop generations:

```bash
bash meta_loop.sh
```

The default harness is Codex with working root set to the project repository and
this task directory added as a writable side directory for notes and state.

## Tools

```bash
tools/pd_check.sh
tools/pd_quick_evolve.sh
```
