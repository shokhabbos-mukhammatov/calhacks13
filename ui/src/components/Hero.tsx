import { motion } from "motion/react";
import { data, money, moneyMoved, shortModel, type Drill } from "../data";
import { sci } from "../lib/stats";
import "./Hero.css";

const arm = (model: string, config: string) =>
  data.drills
    .filter((d) => d.model === model && d.config === config && d.family !== "benign")
    .sort((a, b) => a.card_id.localeCompare(b.card_id) || a.seed - b.seed);

/** The hero art is the data: every drill of the headline comparison, one cell
 * each, so the first thing on the page is also the evidence. */
function Strip({ drills, label, delay }: { drills: Drill[]; label: string; delay: number }) {
  // The hero is on screen at load, so the cells animate on mount: waiting
  // for an in-view signal only risks the evidence never appearing.
  const breaches = drills.filter((d) => d.verdict.breach).length;
  return (
    <div className="strip">
      <div className="strip__head">
        <span className="strip__label">{label}</span>
        <span className="strip__count num">
          <b>{breaches}</b> / {drills.length} paid the attacker
        </span>
      </div>
      <div className="strip__cells" role="img" aria-label={`${breaches} of ${drills.length} drills ended in a breach`}>
        {drills.map((d, i) => (
          <motion.span
            key={d.id}
            className={`cell ${d.verdict.breach ? "cell--breach" : ""}`}
            title={`${d.label} · ${d.verdict.breach ? `breach at turn ${d.cap_turn ?? "?"}` : "held"}`}
            initial={{ opacity: 0, scale: 0.4 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: delay + i * 0.035, duration: 0.3, ease: [0.2, 0.7, 0.2, 1] }}
          >
            {d.verdict.breach && d.cap_turn ? d.cap_turn : ""}
          </motion.span>
        ))}
      </div>
    </div>
  );
}

export default function Hero() {
  const h = data.headline;
  const before = h ? arm(h.model, h.before) : [];
  const after = h ? arm(h.model, h.after) : [];
  const moved = h ? moneyMoved(h.model, h.before) : 0;

  if (!h) return null;
  return (
    <section className="hero" id="top">
      <div className="wrap hero__grid">
        <div className="hero__copy">
          <p className="eyebrow">A controls test for an AI accounts-payable agent</p>
          <h1 className="hero__title sign">
            An AI agent paid a fraudster in{" "}
            <motion.span className="hero__hit num" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25, duration: 0.5 }}>
              {h.before_breaches}
            </motion.span>{" "}
            of {h.before_n} drills.
          </h1>
          <p className="hero__sub">
            Fire Drill attacks the agent the way real invoice fraud works, finds the exact turn it gave in,
            and has a coding agent rewrite its controls from <em>what it did</em>, never from the attacker’s words.
            Then it runs the drills again.
          </p>

          <dl className="hero__facts">
            <div>
              <dt>Before</dt>
              <dd className="num"><b className="t-signal">{h.before_breaches}</b>/{h.before_n}</dd>
            </div>
            <div>
              <dt>After the fix</dt>
              <dd className="num"><b className="t-safe">{h.after_breaches}</b>/{h.after_n}</dd>
            </div>
            <div>
              <dt>Fisher’s exact test</dt>
              <dd className="num">p = {sci(h.fisher_one_sided)}</dd>
            </div>
            <div>
              <dt>Sent to attackers, before</dt>
              <dd className="num">{money(moved)}</dd>
            </div>
          </dl>

          <div className="hero__cta">
            <a className="btn btn--signal" href="#drill">Watch it happen <span aria-hidden="true">↓</span></a>
            <a className="btn" href="#live">Call the agent yourself</a>
          </div>
        </div>

        <figure className="hero__art" aria-label="Every drill in the headline comparison">
          <div className="hero__plate">
            <span className="eyebrow">Drill log · {shortModel(h.model)} · vendor-mailbox takeover</span>
          </div>
          <Strip drills={before} label={`Before · ${h.before}`} delay={0.2} />
          <div className="hero__arrow" aria-hidden="true">
            <span className="hazard hero__stripe" />
            <span className="hero__fixlabel">Claude Code rewrites the controls</span>
          </div>
          <Strip drills={after} label={`After · ${h.after}`} delay={0.2 + before.length * 0.035 + 0.3} />
          <figcaption className="hero__caption">
            One cell per drill. Red: money moved to the attacker’s account; the digit is the turn the agent gave in.
          </figcaption>
        </figure>
      </div>
    </section>
  );
}
