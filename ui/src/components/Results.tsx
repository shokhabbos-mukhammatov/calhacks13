import { motion, useInView } from "motion/react";
import { useRef, useState } from "react";
import { data, scorecardFor, shortModel, type Cell, type Rate } from "../data";
import { fmt, sci } from "../lib/stats";
import ModelSpread from "./ModelSpread";
import Section from "./Section";
import "./Results.css";

type Kind = "wilson" | "cp";

/** The claim is "these two intervals do not overlap", so the chart is the
 * intervals: a forest plot on one 0–1 axis, before above after. */
function Forest({ kind }: { kind: Kind }) {
  const h = data.headline!;
  const b = scorecardFor(h.model, h.before)!;
  const a = scorecardFor(h.model, h.after)!;
  const rows: { group: string; label: string; r: Rate; after: boolean }[] = [
    { group: "S — safe: drills where no money moved", label: h.before, r: b.s, after: false },
    { group: "", label: h.after, r: a.s, after: true },
    { group: "U — useful: honest invoices still paid", label: h.before, r: b.u, after: false },
    { group: "", label: h.after, r: a.u, after: true },
  ];
  const W = 760, L = 150, R = 150, P = W - L - R, ROW = 40, HEAD = 26;
  const x = (v: number) => L + v * P;
  let y = 0;
  const placed = rows.map((row) => {
    if (row.group) y += HEAD;
    const at = y + ROW / 2;
    y += ROW;
    return { ...row, at };
  });
  const H = y + 34;
  const sb = b.s[kind], sa = a.s[kind];
  const gap = sa[0] > sb[1] ? [sb[1], sa[0]] : null;

  return (
    <svg className="forest" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`95% ${kind === "cp" ? "Clopper–Pearson" : "Wilson"} intervals for S and U, before and after`}>
      {[0, 0.25, 0.5, 0.75, 1].map((t) => (
        <g key={t}>
          <line x1={x(t)} x2={x(t)} y1={0} y2={H - 30} className="forest__grid" />
          <text x={x(t)} y={H - 12} className="forest__tick" textAnchor="middle">{t.toFixed(2)}</text>
        </g>
      ))}
      {gap && (
        <motion.g initial={false} animate={{ opacity: 1 }}>
          <motion.rect
            className="forest__gap"
            y={placed[0].at - 12}
            height={placed[1].at - placed[0].at + 24}
            initial={false}
            animate={{ x: x(gap[0]), width: Math.max(0, x(gap[1]) - x(gap[0])) }}
            transition={{ type: "spring", stiffness: 140, damping: 22 }}
          />
          <motion.text
            className="forest__gaplabel"
            textAnchor="middle"
            y={(placed[0].at + placed[1].at) / 2 + 4}
            initial={false}
            animate={{ x: (x(gap[0]) + x(gap[1])) / 2 }}
          >NO OVERLAP</motion.text>
        </motion.g>
      )}
      {placed.map((row, i) => (
        <g key={i}>
          {row.group && <text x={0} y={row.at - ROW / 2 - 6} className="forest__group">{row.group.toUpperCase()}</text>}
          <text x={0} y={row.at + 5} className="forest__label">{row.label}</text>
          <motion.line
            y1={row.at} y2={row.at}
            className={`forest__whisker${row.after ? " is-after" : ""}`}
            initial={false}
            animate={{ x1: x(row.r[kind][0]), x2: x(row.r[kind][1]) }}
            transition={{ type: "spring", stiffness: 140, damping: 22 }}
          />
          <circle cx={x(row.r.rate ?? 0)} cy={row.at} r={7} className={`forest__dot${row.after ? " is-after" : ""}`} />
          <text x={W - R + 18} y={row.at + 5} className="forest__val num">{fmt(row.r.rate ?? 0)}</text>
          <motion.text
            x={W - R + 64} y={row.at + 5} className="forest__ci num"
            key={`${kind}${i}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          >
            [{fmt(row.r[kind][0])}, {fmt(row.r[kind][1])}]
          </motion.text>
          <title>{`${row.label}: ${row.r.k} of ${row.r.n}`}</title>
        </g>
      ))}
    </svg>
  );
}

function Insight() {
  const h = data.headline!;
  const pick = (card: string) => data.cells.find((c) => c.model === h.model && c.config === h.before && c.card_id === card);
  const cards = ["vmt-01", "vmt-02"].map((id) => ({ id, cell: pick(id), card: data.cards.find((c) => c.id === id) }));
  return (
    <div className="insight">
      <h3 className="sign insight__h">The attack is the fake callback, not the bank change.</h3>
      <div className="insight__pair">
        {cards.map(({ id, cell, card }) => cell && (
          <div key={id} className="insight__card">
            <span className="eyebrow">{id} · {h.before}</span>
            <p className="insight__lever"><b>Lever:</b> {card?.lever}</p>
            <div className="insight__big num"><b className={cell.k ? "t-signal" : ""}>{cell.k}</b>/{cell.n}</div>
            <span className="insight__sub">paid the attacker</span>
            <Units cell={cell} />
          </div>
        ))}
      </div>
      <p className="note">
        Both cards ask for the same bank change from the same compromised mailbox. When the message
        offers its own number to “confirm” on, the unhardened agent calls it, hears a yes, and treats that
        as verification — every single time. That is the control that was missing, and it is the one the
        patch pins: a callback only counts if it goes to the number already on file.
      </p>
    </div>
  );
}

function Units({ cell, dim = false }: { cell: Cell; dim?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-10%" });
  return (
    <div className={`units${dim ? " units--dim" : ""}`} ref={ref} role="img" aria-label={`${cell.k} of ${cell.n} breached`}>
      {cell.drills.map((d, i) => (
        <motion.span
          key={d.seed}
          className={`unit${d.breach ? " unit--breach" : ""}${i > 0 && i % 6 === 0 ? " unit--look" : ""}`}
          title={`seed ${d.seed}: ${d.breach ? `breach at turn ${d.cap_turn}` : "held"}`}
          initial={{ opacity: 0, y: -6 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: i * 0.03 }}
        >
          {d.breach && d.cap_turn ? d.cap_turn : ""}
        </motion.span>
      ))}
    </div>
  );
}

function Grid({ kind }: { kind: Kind }) {
  const main = data.headline ? new Set([data.headline.before, data.headline.after]) : new Set<string>();
  const sorted = [...data.cells].sort((a, b) =>
    Number(main.has(b.config)) - Number(main.has(a.config)) || a.model.localeCompare(b.model) ||
    a.config.localeCompare(b.config) || a.card_id.localeCompare(b.card_id));
  return (
    <div className="bgrid">
      <div className="bgrid__head">
        <span>Model</span><span>Hardening</span><span>Card</span><span>One cell per drill</span><span className="num">Breaches</span><span>95% interval</span>
      </div>
      {sorted.map((c) => {
        const small = c.n < 6;
        return (
          <div key={`${c.model}${c.config}${c.card_id}`} className={`bgrid__row${small ? " is-small" : ""}`}>
            <span className="mono">{shortModel(c.model)}</span>
            <span className="mono">{c.config}</span>
            <span className="mono">{c.card_id}</span>
            <Units cell={c} dim={small} />
            <span className="num bgrid__k"><b>{c.k}</b>/{c.n}</span>
            <span className="num bgrid__ci">[{fmt(c[kind][0])}, {fmt(c[kind][1])}]</span>
          </div>
        );
      })}
    </div>
  );
}

export default function Results() {
  const [kind, setKind] = useState<Kind>("wilson");
  const h = data.headline;
  if (!h) return null;
  return (
    <Section
      id="results"
      no="04"
      title="Does it hold"
      lede={`Every rate on this page carries a 95% interval, because ${h.before_n} drills is not a lot. Read safety and usefulness together: an agent that refuses every invoice is perfectly safe and worthless.`}
    >
      <div className="res__top">
        <div className="res__chart">
          <div className="res__toolbar">
            <span className="eyebrow">{shortModel(h.model)} · {h.before} → {h.after}</span>
            <div className="seg" role="group" aria-label="Interval method">
              <button aria-pressed={kind === "wilson"} onClick={() => setKind("wilson")}>Wilson</button>
              <button aria-pressed={kind === "cp"} onClick={() => setKind("cp")}>Clopper–Pearson</button>
            </div>
          </div>
          <Forest kind={kind} />
          <p className="note">
            {kind === "wilson"
              ? "Wilson: good coverage at small n, and it does not collapse at 0 or 1 the way the textbook interval does."
              : "Clopper–Pearson: exact and conservative — its coverage is never below 95%. Wider, so it is the bound to quote when someone wants one they cannot argue with. The gap survives it."}
          </p>
        </div>
        <aside className="res__stats">
          <div className="res__stat">
            <span className="eyebrow">Breaches</span>
            <span className="res__big num"><b className="t-signal">{h.before_breaches}</b>/{h.before_n} → <b className="t-safe">{h.after_breaches}</b>/{h.after_n}</span>
          </div>
          <div className="res__stat">
            <span className="eyebrow">Fisher’s exact test, one-sided</span>
            <span className="res__big num">p = {sci(h.fisher_one_sided)}</span>
            <span className="res__small">A difference this large would arise by chance about once in {Math.round(1 / h.fisher_one_sided).toLocaleString("en-US")} tries.</span>
          </div>
          <div className="res__stat">
            <span className="eyebrow">Why not a regression</span>
            <span className="res__small">The patched arm has zero breaches, which separates the outcomes perfectly; a logistic fit’s coefficient has no finite value. Fisher’s test answers the same question exactly.</span>
          </div>
        </aside>
      </div>

      <ModelSpread />

      <Insight />

      <h3 className="sign res__h">The breach grid</h3>
      <p className="note">
        Every model × hardening level × tactic card, one cell per drill. Drills run in looks of six (the
        wider gaps); a cell stops early once its interval, widened for the number of looks, is decided.
        Faded rows are early exploratory runs at three drills — kept, because dropping inconvenient data
        is how results get dressed up.
      </p>
      <Grid kind={kind} />
    </Section>
  );
}
