#!/bin/bash
set -euo pipefail

PROJECT_DIR="${PD_PROJECT_DIR:-/Users/krestnikov/giga/prisoners_dilemma}"

cd "$PROJECT_DIR"

node headless/evolve.js \
  --mode generalist \
  --fitness roundrobin \
  --noise 0,0.05 \
  --pop 20 \
  --gens 6 \
  --rounds 60 \
  --repeats 1 \
  --seed quick-smoke \
  --every 3 \
  --no-out

