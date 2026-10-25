import { motion, useInView } from "motion/react";
import { useRef } from "react";
import { BENIGN, data, providerOf, shortModel } from "../data";
import { fmt, wilson } from "../lib/stats";
import "./ModelSpread.css";

const WORDS: Record<number, string> = { 2: "two", 3: "three", 4: "four", 5: "five", 6: "six" };

type Tally = { family: string; heldOut: boolean; k: number; n: number; rate: number; ci: [number, number] };

const tally = (k: number, n: number, family: string, heldOut: boolean): Tally =>
  ({ family, heldOut, k, n, rate: n ? k / n : 0, ci: wilson(k, n) });

/** Attack drills at `baseline`, per model and attack family. The point of the
 * harness is that this answer is not the same for every agent, so it has to
 * be measured rather than assumed, and it is the one chart that says so. A
 * revealed held-out family gets its own bar beside the training one: it is a
 * harder attack, reported next to the first, never pooled into it. */
function byModel() {
  const train = new Map<string, { k: number; n: number; family: string }>();
  for (const d of data.drills) {
    if (d.family === BENIGN || d.config !== "baseline") continue;
    const row = train.get(d.model) ?? { k: 0, n: 0, family: d.family };
    row.k += d.verdict.breach ? 1 : 0;
    row.n += 1;
    train.set(d.model, row);
  }
  const held = new Map<string, { k: number; n: number; family: string }>();
  for (const c of data.revealed_cells ?? []) {
    if (c.config !== "baseline") continue;
    const row = held.get(c.model) ?? { k: 0, n: 0, family: c.family };
    row.k += c.k;
    row.n += c.n;
    held.set(c.model, row);
  }
  return [...train.entries()]
    .filter(([, t]) => t.n >= 4)                       // one drill says nothing
    .map(([model, t]) => {
      const h = held.get(model);
      const families = [tally(t.k, t.n, t.family, false)];
      if (h && h.n >= 4) families.push(tally(h.k, h.n, h.family, true));
      return { model, families, k: t.k, n: t.n, rate: t.n ? t.k / t.n : 0 };
    })
    .sort((a, b) => b.rate - a.rate || b.n - a.n);
}

export default function ModelSpread() {
  const rows = byModel();
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-15%" });
  if (rows.length < 2) return null;
  const breaks = (r: (typeof rows)[number]) => r.families.some((f) => f.k > 0);
  const breaking = rows.filter(breaks);
  const holders = rows.filter((r) => !breaks(r));
  const providers = new Set(rows.map((r) => providerOf(r.model))).size;
  // Several providers on one list: full model ids, so no name is ambiguous.
  const label = (m: string) => (providers > 1 ? m : shortModel(m));
  const h = data.headline;
  const others = breaking.filter((r) => r.model !== h?.model);
  const crossProvider = data.contrast?.providers[0];
  // The harder attack, as it landed on the headline model and on the holders.
  const harder = rows.find((r) => r.model === h?.model)?.families.find((f) => f.heldOut);
  const holdersOnHarder = holders.flatMap((r) => r.families.filter((f) => f.heldOut));
  const heldTotal = holdersOnHarder.reduce((s, f) => [s[0] + f.k, s[1] + f.n], [0, 0]);
  let bar = 0;

  return (
    <div className="spread" ref={ref}>
      {/* Counted, not typed: a model with too few drills is filtered out above. */}
      <h3 className="sign spread__h">
        The same attack, {WORDS[rows.length] ?? rows.length} agents
        {providers > 1 && <>, {WORDS[providers] ?? providers} providers</>}
      </h3>
      <p className="spread__lede">
        Identical cards, identical seeds, no controls on any of them; only the model differs.{" "}
        {breaking.length === 1
          ? <>One of them pays the fraudster and the others do not.</>
          : <>{breaking.map((r) => label(r.model)).join(" and ")} pay the fraudster; the others do not.</>}{" "}
        This is the reason a harness has to exist: the answer is a property of <em>your</em> agent, and
        the only way to know it is to run the drill.
      </p>
      <ul className="spread__rows">
        {rows.map((r) => r.families.map((f, j) => (
          <li key={`${r.model}${f.family}`} className={`${f.k ? "is-breaching" : ""}${j > 0 ? " is-cont" : ""}`}>
            <span className="spread__model mono">{j === 0 ? label(r.model) : ""}</span>
            <span className="spread__family mono">{f.heldOut ? `${f.family} · held out` : f.family}</span>
            <span className="spread__bar">
              <motion.span
                className="spread__fill"
                initial={{ width: 0 }}
                animate={inView ? { width: `${Math.max(f.rate * 100, f.k ? 2 : 0)}%` } : {}}
                transition={{ delay: 0.1 + bar++ * 0.08, duration: 0.6, ease: [0.2, 0.7, 0.2, 1] }}
              />
            </span>
            <span className="spread__n num">
              <b>{f.k}</b>/{f.n}
              <span className="spread__ci">95% [{fmt(f.ci[0])}, {fmt(f.ci[1])}]</span>
            </span>
          </li>
        )))}
      </ul>
      {h && (
        <p className="note">
          The headline numbers are measured on {label(h.model)}, the first agent that fell for it. A model
          refusing this attack today is not a control: nothing enforces it, and nothing proves the next
          prompt or the next model keeps refusing. These drills show {label(h.model)} giving in{" "}
          {h.before_breaches} times out of {h.before_n}
          {others.map((r) => <span key={r.model}>, and {label(r.model)} {r.k} of {r.n}</span>)}.
          {harder && holdersOnHarder.length > 0 && (
            <> The harder held-out attack, which broke {label(h.model)} in {harder.k} of {harder.n}, did not
              break the others either: {heldTotal[0]} of {heldTotal[1]} drills across{" "}
              {holders.map((r) => label(r.model)).join(", ")}.</>
          )}{" "}
          The gate in the patch is what holds regardless
          {crossProvider ? <>: the table above, on {shortModel(crossProvider.model)}, shows it holding on another
            provider’s model.</> : <>.</>}
        </p>
      )}
    </div>
  );
}
