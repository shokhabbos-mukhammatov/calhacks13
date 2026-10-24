// Prints the TypeScript port's intervals over a grid of (k, n) as JSON, for
// scripts/check_ui_stats.py to compare against firedrill/stats.py.
import { clopperPearson, wilson } from "../src/lib/stats.ts";

const out = [];
for (const n of [1, 2, 3, 6, 12, 18, 24, 30, 48, 60]) {
  for (let k = 0; k <= n; k++) out.push({ k, n, wilson: wilson(k, n), cp: clopperPearson(k, n) });
}
console.log(JSON.stringify(out));
