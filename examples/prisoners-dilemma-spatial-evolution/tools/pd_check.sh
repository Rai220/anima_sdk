#!/bin/bash
set -euo pipefail

PROJECT_DIR="${PD_PROJECT_DIR:-/Users/krestnikov/giga/prisoners_dilemma}"

cd "$PROJECT_DIR"

echo "== git status =="
git status --short --branch

echo
echo "== manifest =="
npm run scan

echo
echo "== js syntax =="
find src headless strategies tools web -name '*.js' -print0 | xargs -0 -n1 node --check

echo
echo "== strategy load =="
node --input-type=module -e "
import { loadStrategies } from './src/load-node.js';
const s = await loadStrategies({ manifest: false });
const names = s.map((x) => x.name);
const dup = names.filter((n, i) => names.indexOf(n) !== i);
console.log(JSON.stringify({
  count: s.length,
  duplicates: dup,
  alliance: names.filter((n) => n.includes('Alliance')).sort(),
}, null, 2));
if (dup.length) process.exit(1);
"

echo
echo "== terminology guard =="
if rg -n "массон|Массон|масон|Масон|каменщик|Каменщик|mason|Mason|Freemason|freemason|Masonic|masonic|MASON|FREEMASON|клик|Клик|clique|Clique|brother|Brother|брат|Брат|брать|Брать" .; then
  echo "Old terminology found." >&2
  exit 1
fi

echo
echo "OK"

