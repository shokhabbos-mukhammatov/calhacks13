import { motion, useInView } from "motion/react";
import { useRef } from "react";
import { BENIGN, data, providerOf, shortModel } from "../data";
import { fmt, wilson } from "../lib/stats";
import "./ModelSpread.css";

const WORDS: Record<number, string> = { 2: "two", 3: "three", 4: "four", 5: "five", 6: "six" };

/** Attack drills at `baseline`, per model. The point of the harness is that
 * this answer is not the same for every agent, so it has to be measured
 * rather than assumed — and it is the one chart that says so. */
function byModel() {
  const tally = new Map<string, { k: number; n: number }>();
  for (const d of data.drills) {
    if (d.family === BENIGN || d.config !== "baseline") continue;
    const row = tally.get(d.model) ?? { k: 0, n: 0 };
    row.k += d.verdict.breach ? 1 : 0;
    row.n += 1;
    tally.set(d.model, row);
  }
  return [...tally.entries()]
    .map(([model, { k, n }]) => ({ model, k, n, rate: k / n, ci: wilson(k, n) }))
    .filter((r) => r.n >= 4)                       // one drill says nothing
    .sort((a, b) => b.rate - a.rate || b.n - a.n);
}

export default function ModelSpread() {
  const rows = byModel();
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-15%" });
  if (rows.length < 2) return null;
  const breaking = rows.filter((r) => r.k > 0);
  const providers = new Set(rows.map((r) => providerOf(r.model))).size;
  // Several providers on one list: full model ids, so no name is ambiguous.
  const label = (m: string) => (providers > 1 ? m : shortModel(m));
  const h = data.headline;
  const others = breaking.filter((r) => r.model !== h?.model);
  const crossProvider = data.contrast?.providers[0];

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
        {rows.map((r, i) => (
          <li key={r.model} className={r.k ? "is-breaching" : ""}>
            <span className="spread__model mono">{label(r.model)}</span>
            <span className="spread__bar">
              <motion.span
                className="spread__fill"
                initial={{ width: 0 }}
                animate={inView ? { width: `${Math.max(r.rate * 100, r.k ? 2 : 0)}%` } : {}}
                transition={{ delay: 0.1 + i * 0.12, duration: 0.6, ease: [0.2, 0.7, 0.2, 1] }}
              />
              <span className="spread__ci num">
                95% [{fmt(r.ci[0])}, {fmt(r.ci[1])}]
              </span>
            </span>
            <span className="spread__n num">
              <b>{r.k}</b>/{r.n}
            </span>
          </li>
        ))}
      </ul>
      {h && (
        <p className="note">
          The headline numbers are measured on {label(h.model)}, the first agent that fell for it. A model
          refusing this attack today is not a control: nothing enforces it, and nothing proves the next
          prompt or the next model keeps refusing. These drills show {label(h.model)} giving in{" "}
          {h.before_breaches} times out of {h.before_n}
          {others.map((r) => <span key={r.model}>, and {label(r.model)} {r.k} of {r.n}</span>)}. The gate in the
          patch is what holds regardless
          {crossProvider ? <>: the table above, on {shortModel(crossProvider.model)}, shows it holding on another
            provider’s model.</> : <>.</>}
        </p>
      )}
    </div>
  );
}
