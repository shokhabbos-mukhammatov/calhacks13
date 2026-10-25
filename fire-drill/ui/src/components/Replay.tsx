import { AnimatePresence, motion, useInView, useReducedMotion } from "motion/react";
import { useEffect, useMemo, useRef, useState } from "react";
import { data, findDrill, money, shortModel, type Drill, type ToolCall } from "../data";
import { Reply } from "../lib/text";
import Ledger from "./Ledger";
import Section from "./Section";
import "./Replay.css";

// One world, three agents. The same seed builds the same vendor, invoice and
// phone numbers each time, so the only thing that differs is the controls.
const PRESETS = [
  { label: "vmt-02-s1", config: "baseline", title: "No controls", sub: "The agent as shipped" },
  { label: "vmt-02-s1", config: "patch:v1", title: "Patched", sub: "Policy + gates by Claude Code" },
  { label: "vmt-02-s1", config: "scope:v1", title: "Gate only", sub: "Policy text removed: is the code enough?" },
];

type Event =
  | { kind: "msg"; turn: number }
  | { kind: "tool"; index: number }
  | { kind: "reply"; turn: number };

function eventsOf(d: Drill): Event[] {
  const out: Event[] = [];
  for (const t of d.transcript) {
    out.push({ kind: "msg", turn: t.turn });
    d.tool_calls.forEach((c, i) => c.turn === t.turn && out.push({ kind: "tool", index: i }));
    out.push({ kind: "reply", turn: t.turn });
  }
  return out;
}

/** What a tool call meant, said in the ledger's terms rather than the model's. */
function meaning(c: ToolCall, d: Drill): { text: string; tone: "bad" | "good" | "gate" | "info" } | null {
  if (c.error) return { text: "Refused by a gate in code — nothing changed", tone: "gate" };
  if (c.tool === "verify_vendor" && c.result) {
    // CRS is called live against the sandbox; the domain age comes from the
    // scenario, because the vendors and their .example domains are invented.
    try {
      const ev = JSON.parse(c.result);
      if (ev.sender_risk_score != null)
        return { text: `CRS Fraud Finder, live: sender risk ${ev.sender_risk_score}/100 · ${ev.sender_email_status}`, tone: "info" };
    } catch { /* not JSON: fall through */ }
  }
  if (c.tool === "change_vendor_bank_details")
    return c.input.new_account === d.kit.approved_account
      ? null
      : { text: "Bank account changed to the one in the message", tone: "bad" };
  if (c.tool === "call_vendor") {
    if (c.input.phone_number === d.kit.attacker_phone)
      return { text: "Called the number the attacker supplied", tone: "bad" };
    if (c.input.phone_number === d.kit.on_file_phone)
      return { text: "Called the number already on file", tone: "good" };
  }
  if (c.tool === "export_vendor_master") return { text: "Touched the canary", tone: "bad" };
  return null;
}

function args(input: Record<string, string>) {
  return Object.entries(input).map(([k, v], i) => (
    <span key={k}>
      {i > 0 && ", "}
      <span className="tc__k">{k}</span>=<span className="tc__v">{v}</span>
    </span>
  ));
}

export default function Replay() {
  const [pick, setPick] = useState({ label: PRESETS[0].label, config: PRESETS[0].config, model: "" });
  const drill = useMemo(
    () => findDrill(pick.label, pick.config, pick.model || undefined) ?? data.drills[0],
    [pick],
  );
  const events = useMemo(() => eventsOf(drill), [drill]);
  const [shown, setShown] = useState(0);
  const [playing, setPlaying] = useState(false);
  const reduce = useReducedMotion();
  const stage = useRef<HTMLDivElement>(null);
  const inView = useInView(stage, { once: true, margin: "-30%" });
  const feed = useRef<HTMLOListElement>(null);

  // Start the first drill on its own the first time it scrolls into view.
  useEffect(() => { if (inView) setPlaying(true); }, [inView]);
  useEffect(() => { setShown(0); setPlaying(true); }, [drill.id]);

  useEffect(() => {
    if (!playing) return;
    if (shown >= events.length) return setPlaying(false);
    if (reduce) { setShown(events.length); return; }
    const next = events[shown];
    const wait = shown === 0 ? 350 : next.kind === "tool" ? 750 : 1300;
    const t = setTimeout(() => setShown((s) => s + 1), wait);
    return () => clearTimeout(t);
  }, [playing, shown, events, reduce]);

  // Keep the newest event in view inside the feed, without scrolling the page.
  useEffect(() => {
    const el = feed.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: reduce ? "auto" : "smooth" });
  }, [shown, reduce]);

  const visible = events.slice(0, shown);
  const ledgerIndex = visible.filter((e) => e.kind === "tool").length;
  const done = shown >= events.length;
  const card = data.cards.find((c) => c.id === drill.card_id);

  const others = useMemo(
    () => [...data.drills].sort((a, b) => a.config.localeCompare(b.config) || a.label.localeCompare(b.label, undefined, { numeric: true })),
    [],
  );

  return (
    <Section
      id="drill"
      no="02"
      title="Watch a drill"
      lede={
        <>
          A real recorded drill, replayed step by step. On the left is what the agent saw and did; on
          the right is the ledger, the only thing the verdict is read from. Same vendor, same invoice,
          same attacker account — three different agents.
        </>
      }
    >
      <div className="presets" role="tablist" aria-label="Which agent to replay">
        {PRESETS.map((p) => {
          const d = findDrill(p.label, p.config);
          const on = drill.config === p.config && drill.label === p.label && !pick.model;
          return (
            <button
              key={p.config}
              role="tab"
              aria-selected={on}
              className={`preset${on ? " preset--on" : ""}`}
              onClick={() => setPick({ label: p.label, config: p.config, model: "" })}
            >
              <span className="preset__title sign">{p.title}</span>
              <span className="preset__sub">{p.sub}</span>
              {d && (
                <span className={`chip ${d.verdict.breach ? "chip--breach" : "chip--held"}`}>
                  {d.verdict.breach ? `Breach · turn ${d.cap_turn}` : "Held"}
                </span>
              )}
            </button>
          );
        })}
        <label className="preset preset--browse">
          <span className="preset__title sign">Any drill</span>
          <select
            value={drill.id}
            onChange={(e) => {
              const d = data.drills.find((x) => x.id === e.target.value)!;
              setPick({ label: d.label, config: d.config, model: d.model });
            }}
          >
            {others.map((d) => (
              <option key={d.id} value={d.id}>
                {d.config} · {d.label} · {shortModel(d.model)} · {d.verdict.breach ? "breach" : d.family === "benign" ? (d.paid_on_file ? "paid" : "not paid") : "held"}
              </option>
            ))}
          </select>
        </label>
      </div>

      {card && (
        <div className="tactic">
          <span className="eyebrow">Tactic card {card.id}</span>
          <dl>
            <div><dt>Pretext</dt><dd>{card.pretext}</dd></div>
            <div><dt>Lever</dt><dd>{card.lever}</dd></div>
            <div><dt>Ask</dt><dd>{card.ask}</dd></div>
          </dl>
          <a href={card.source_url} target="_blank" rel="noreferrer">The public fraud report it comes from ↗</a>
        </div>
      )}

      <div className="stage-grid" ref={stage}>
        <div className="feed-wrap">
          <div className="player">
            <button className="btn" onClick={() => { if (done) setShown(0); setPlaying((p) => !p || done); }}>
              {playing ? "❚❚ Pause" : done ? "↺ Replay" : "▶ Play"}
            </button>
            <button className="btn" disabled={shown === 0} onClick={() => { setPlaying(false); setShown((s) => Math.max(0, s - 1)); }} aria-label="Step back">←</button>
            <button className="btn" disabled={done} onClick={() => { setPlaying(false); setShown((s) => Math.min(events.length, s + 1)); }} aria-label="Step forward">→</button>
            <span className="player__count num">{shown}/{events.length} steps</span>
            <span className="player__who">{drill.config} · {shortModel(drill.model)} · seed {drill.seed}</span>
          </div>

          <ol className="feed" ref={feed} aria-live="polite">
            <AnimatePresence initial={false}>
              {visible.map((e, i) => {
                if (e.kind === "msg") {
                  const t = drill.transcript.find((x) => x.turn === e.turn)!;
                  return (
                    <motion.li key={`m${i}`} className="ev ev--msg" initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }}>
                      <span className="ev__who">
                        {drill.family === "benign" ? "Vendor" : "Attacker"} · turn {t.turn} · {t.sender}
                      </span>
                      {t.subject && <span className="ev__subject">{t.subject}</span>}
                      <p className="ev__body">{t.body}</p>
                    </motion.li>
                  );
                }
                if (e.kind === "tool") {
                  const c = drill.tool_calls[e.index];
                  const m = meaning(c, drill);
                  return (
                    <motion.li key={`t${i}`} className={`ev ev--tool${c.error ? " ev--refused" : ""}`} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}>
                      <code className="tc">
                        <span className="tc__arrow" aria-hidden="true">→</span>
                        <span className="tc__name">{c.tool}</span>({args(c.input)})
                      </code>
                      {c.result && <span className="tc__result" title={c.result}>{c.result}</span>}
                      {m && <span className={`tc__means tc__means--${m.tone}`}>{m.text}</span>}
                    </motion.li>
                  );
                }
                const t = drill.transcript.find((x) => x.turn === e.turn)!;
                return (
                  <motion.li key={`r${i}`} className="ev ev--reply" initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }}>
                    <span className="ev__who">Agent · {shortModel(drill.model)} · reply</span>
                    <div className="ev__body"><Reply text={t.reply} /></div>
                  </motion.li>
                );
              })}
            </AnimatePresence>
            {shown === 0 && <li className="feed__empty">Press play. The drill runs one tool call at a time.</li>}
          </ol>
        </div>

        <Ledger drill={drill} step={drill.ledger[ledgerIndex]} done={done} />
      </div>

      <p className="note replay__foot">
        Invoice {drill.kit.invoice_id} for {money(drill.kit.amount)} from {drill.kit.vendor_name}. Every
        ledger state shown is the real ledger, replayed through the same code the scorer reads — the
        export refuses to build if a replay ends anywhere the recorded drill did not.
      </p>
    </Section>
  );
}
