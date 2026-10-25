import { motion, useInView, useReducedMotion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import Section from "./Section";
import "./Loop.css";

const STAGES = [
  {
    key: "Drill",
    what: "A tactic card distilled from a public fraud report, and a seed that builds the world: a vendor, an invoice, the phone number on file and the attacker’s number. Attacker turns arrive on a channel — an invoice, an email, or a real phone call.",
    parts: ["Tactic card", "Seed", "Channel"],
  },
  {
    key: "Break",
    what: "Claude, as the accounts-payable agent, works its tools. A ledger records every state change, and the verdict is a predicate over that ledger: did money reach an account nobody verified? No model ever grades a transcript.",
    parts: ["Victim agent", "Ledger", "Scorer"],
  },
  {
    key: "Fix",
    what: "The failing drills go to a coding agent as actions, with every value replaced by its role. It never sees the attacker’s words. Claude Code and Factory Droid each write a patch: a policy plus gates on the tools.",
    parts: ["Remediator", "Claude Code", "Factory Droid"],
  },
  {
    key: "Re-run",
    what: "The same attacks on more seeds, in looks of six with the error rate split across them in advance, until every cell is decided. Fisher’s exact test compares before with after.",
    parts: ["Breach grid", "Wilson", "Fisher"],
  },
];

/** A token walks the four stages on a loop. It pauses off-screen and never
 * moves for a reader who asked for reduced motion: then every stage is lit. */
export default function Loop() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { margin: "-20%" });
  const reduce = useReducedMotion();
  const [step, setStep] = useState(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    if (!inView || reduce || paused) return;
    const t = setInterval(() => setStep((s) => (s + 1) % STAGES.length), 2600);
    return () => clearInterval(t);
  }, [inView, reduce, paused]);

  return (
    <Section
      id="how"
      no="01"
      title="How it works"
      lede="Four steps, run as a loop. Every number later on this page comes out of step two, and none of it depends on a model’s opinion of what happened."
    >
      <div
        className="loop"
        ref={ref}
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}
      >
        <div className="loop__rail" aria-hidden="true">
          <motion.span
            className="loop__token"
            animate={{ left: `calc(${(step / STAGES.length) * 100}% + ${100 / STAGES.length / 2}% - 9px)` }}
            transition={{ type: "spring", stiffness: 120, damping: 20 }}
          />
        </div>
        <ol className="loop__stages">
          {STAGES.map((s, i) => (
            <li
              key={s.key}
              className={`stage${reduce || i === step ? " stage--on" : ""}`}
              onMouseEnter={() => setStep(i)}
              onFocus={() => setStep(i)}
              tabIndex={0}
            >
              <span className="stage__no num">{String(i + 1).padStart(2, "0")}</span>
              <h3 className="stage__key sign">{s.key}</h3>
              <p className="stage__what">{s.what}</p>
              <ul className="stage__parts">
                {s.parts.map((p) => <li key={p}>{p}</li>)}
              </ul>
            </li>
          ))}
        </ol>
        <div className="loop__return">
          <span className="loop__return-line" aria-hidden="true" />
          <p>
            <b>Repeat until it holds</b> — then test the fix on attack families it never saw. Those are
            committed as a salted Merkle root <em>before</em> the patch is written, so the held-out set
            cannot be swapped for an easier one afterwards.
          </p>
        </div>
      </div>

      <dl className="seats">
        <div>
          <dt>The seat it fills</dt>
          <dd>The controls tester an accounts-payable team does not have: it red-teams an AI agent
            before it is allowed near the vendor master, and again after every change to its prompt,
            tools or model.</dd>
        </div>
        <div>
          <dt>Who it protects</dt>
          <dd>Finance staff at small and mid-sized businesses, now being handed agents that can change
            a vendor’s bank details and approve the payment — and the vendors whose money goes
            missing when they do.</dd>
        </div>
        <div>
          <dt>Path to production</dt>
          <dd>Put your own agent behind the same tool interface, run the grid in CI on every change,
            and let a decided breach open a patch for a human to review. Every verdict is something an
            auditor can re-check.</dd>
        </div>
      </dl>
    </Section>
  );
}
