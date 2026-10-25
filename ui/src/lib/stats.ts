// The interval lab recomputes intervals live as the sliders move, so this is
// the one place the frontend does statistics. It is a port of
// firedrill/stats.py, line for line where it matters, and
// scripts/check_ui_stats.py compares the two on 214 (k, n) pairs.

export const Z95 = 1.959963984540054;

/** The textbook normal-approximation interval. Here only to show how it fails:
 * at k = 0 its width is exactly zero, a claim of certainty from six drills. */
export function wald(k: number, n: number, z = Z95): [number, number] {
  if (n <= 0) return [0, 1];
  const p = k / n;
  const half = z * Math.sqrt((p * (1 - p)) / n);
  return [Math.max(0, p - half), Math.min(1, p + half)];
}

export function wilson(k: number, n: number, z = Z95): [number, number] {
  if (n <= 0) return [0, 1];
  const p = k / n;
  const z2 = z * z;
  const centre = (p + z2 / (2 * n)) / (1 + z2 / n);
  const half = (z * Math.sqrt((p * (1 - p)) / n + z2 / (4 * n * n))) / (1 + z2 / n);
  return [k === 0 ? 0 : Math.max(0, centre - half), k === n ? 1 : Math.min(1, centre + half)];
}

// --- the regularized incomplete beta, for Clopper-Pearson ------------------
function betacf(a: number, b: number, x: number): number {
  const tiny = 1e-300;
  const qab = a + b, qap = a + 1, qam = a - 1;
  let c = 1;
  let d = 1 - (qab * x) / qap;
  if (Math.abs(d) < tiny) d = tiny;
  d = 1 / d;
  let h = d;
  for (let m = 1; m <= 300; m++) {
    const m2 = 2 * m;
    for (const num of [
      (m * (b - m) * x) / ((qam + m2) * (a + m2)),
      (-(a + m) * (qab + m) * x) / ((a + m2) * (qap + m2)),
    ]) {
      d = 1 + num * d;
      if (Math.abs(d) < tiny) d = tiny;
      c = 1 + num / c;
      if (Math.abs(c) < tiny) c = tiny;
      d = 1 / d;
      h *= d * c;
    }
    if (Math.abs(d * c - 1) < 1e-15) break;
  }
  return h;
}

function lgamma(x: number): number {
  // Lanczos, g = 7: accurate to ~1e-15 for the arguments used here.
  const g = 7;
  const coef = [
    0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
    -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6,
    1.5056327351493116e-7,
  ];
  if (x < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * x)) - lgamma(1 - x);
  x -= 1;
  let a = coef[0];
  const t = x + g + 0.5;
  for (let i = 1; i < g + 2; i++) a += coef[i] / (x + i);
  return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(t) - t + Math.log(a);
}

export function betainc(a: number, b: number, x: number): number {
  if (x <= 0) return 0;
  if (x >= 1) return 1;
  const front = Math.exp(lgamma(a + b) - lgamma(a) - lgamma(b) + a * Math.log(x) + b * Math.log(1 - x));
  return x < (a + 1) / (a + b + 2) ? (front * betacf(a, b, x)) / a : 1 - (front * betacf(b, a, 1 - x)) / b;
}

export function betaQuantile(p: number, a: number, b: number): number {
  let lo = 0, hi = 1;
  for (let i = 0; i < 200; i++) {
    const mid = (lo + hi) / 2;
    if (betainc(a, b, mid) < p) lo = mid;
    else hi = mid;
  }
  return (lo + hi) / 2;
}

/** Exact and conservative: coverage never below the nominal level. */
export function clopperPearson(k: number, n: number, alpha = 0.05): [number, number] {
  if (n <= 0) return [0, 1];
  const low = k === 0 ? 0 : betaQuantile(alpha / 2, k, n - k + 1);
  const high = k === n ? 1 : betaQuantile(1 - alpha / 2, k + 1, n - k);
  return [low, high];
}

export const fmt = (x: number, digits = 2) => x.toFixed(digits);

/** 1.29e-5 -> "1.3 × 10⁻⁵", for a p-value too small for decimals to carry. */
export function sci(x: number): string {
  if (x >= 0.001) return x.toFixed(4);
  const exp = Math.floor(Math.log10(x));
  const mant = x / 10 ** exp;
  const sup = String(exp).replace(/-/g, "⁻").replace(/\d/g, (d) => "⁰¹²³⁴⁵⁶⁷⁸⁹"[+d]);
  return `${mant.toFixed(1)} × 10${sup}`;
}
