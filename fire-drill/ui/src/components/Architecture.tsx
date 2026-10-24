import { useReducedMotion } from "motion/react";
import { useState } from "react";
import Section from "./Section";
import "./Architecture.css";

type Kind = "core" | "adapter" | "loop" | "evidence";
interface Node {
  id: string; x: number; y: number; w: number; h: number; kind: Kind;
  label: string; sub: string; detail: string; file: string; adr?: string; sponsor?: string;
}

const NODES: Node[] = [
  { id: "card", x: 30, y: 60, w: 150, h: 66, kind: "core", label: "Tactic card", sub: "public fraud report",
    detail: "An attack, described without a word of attack text: family, pretext, pressure lever, the ask, and a link to the public report it was distilled from. A seed then builds the world it runs in.", file: "cards/*.json · firedrill/drill.py" },
  { id: "driver", x: 220, y: 60, w: 150, h: 66, kind: "core", label: "Attack driver", sub: "scripted turns",
    detail: "Sends the attacker’s turns, filled in for the seed’s world. The turns are written by a person; the harness never generates attack text.", file: "firedrill/drill.py · turns/" },
  { id: "channel", x: 410, y: 60, w: 150, h: 66, kind: "core", label: "Channel", sub: "text or voice",
    detail: "How a message reaches the agent. Text drills use the invoice channel; the voice channel is a real phone number relayed into the same agent and ledger.", file: "firedrill/victim.py · ChannelMessage" },
  { id: "agent", x: 600, y: 60, w: 150, h: 66, kind: "core", label: "Victim agent", sub: "Claude + 7 tools",
    detail: "The accounts-payable agent under test: a hand-built tool loop on the Anthropic API with seven tools, one of them a canary. Hardening is a policy plus a tool scope, and a gated tool is enforced in code where money moves.", file: "firedrill/victim.py", sponsor: "Anthropic" },
  { id: "ledger", x: 790, y: 60, w: 150, h: 66, kind: "core", label: "Ledger", sub: "every state change",
    detail: "The world’s state: vendors, approved accounts, the active account, invoices, callbacks, payments, canary hits. Tools change it; nothing else does.", file: "firedrill/ledger.py" },
  { id: "scorer", x: 980, y: 60, w: 150, h: 66, kind: "core", label: "Scorer", sub: "pure predicates",
    detail: "Three predicates over final ledger state: money in an unapproved account, a change verified out of band, the canary touched. No model reads a transcript.", file: "firedrill/scorer.py", adr: "ADR-0001" },

  { id: "voice", x: 410, y: 220, w: 140, h: 56, kind: "adapter", label: "Cartesia", sub: "phone line → relay",
    detail: "A Cartesia managed agent on a real phone number. Each caller turn goes through a webhook tool to the Standby target, which runs the same agent and ledger a text drill uses.", file: "actors/victim-standby · /voice/relay", sponsor: "Cartesia" },
  { id: "verify", x: 590, y: 220, w: 130, h: 56, kind: "adapter", label: "CRS + RDAP", sub: "vendor verify",
    detail: "Independent evidence the agent can ask for: the callback number from the file, the sender domain’s age from RDAP, and the sender address’s fraud score from CRS Fraud Finder.", file: "firedrill/verify.py", sponsor: "CRS" },
  { id: "store", x: 740, y: 220, w: 130, h: 56, kind: "adapter", label: "Apify KVS", sub: "shared state",
    detail: "The conversation and the ledger live in a shared key-value store, so any Standby container can serve any turn. Proven by killing a container mid-drill.", file: "actors/victim-standby", adr: "ADR-0003", sponsor: "Apify" },
  { id: "rail", x: 890, y: 220, w: 120, h: 56, kind: "adapter", label: "Nessie", sub: "payment rail",
    detail: "Every approved payment is mirrored into Capital One’s Nessie sandbox bank. It mirrors only: the ledger has already recorded the payment, so a rail outage cannot change a verdict.", file: "firedrill/payments.py", sponsor: "Capital One" },
  { id: "trace", x: 1030, y: 220, w: 120, h: 56, kind: "adapter", label: "Elastic", sub: "drill corpus",
    detail: "Every drill indexed, and an Agent Builder tool registered over the index: a fixed ES|QL query that answers which drills breached, at which turn, by hardening level.", file: "firedrill/elastic.py", sponsor: "Elastic" },

  { id: "records", x: 980, y: 360, w: 150, h: 66, kind: "loop", label: "Records", sub: "one JSON per drill",
    detail: "Each drill saved with its card, seed, config fingerprint, transcript, tool calls, final ledger and verdict. Content-addressed, so a re-run replaces itself and a replay is exact.", file: "firedrill/records.py · records/" },
  { id: "summary", x: 760, y: 360, w: 150, h: 66, kind: "loop", label: "Failure summary", sub: "actions → roles",
    detail: "Failing drills reduced to what the agent did, with every concrete value replaced by its role (attacker_account, number_from_request). No message text survives.", file: "firedrill/failures.py", adr: "ADR-0002" },
  { id: "codeagent", x: 540, y: 360, w: 150, h: 66, kind: "loop", label: "Code agent port", sub: "Claude Code · Droid",
    detail: "One interface, two adapters: Claude Code (claude -p) and Factory Droid (droid exec). Each gets the same brief and the same summaries and returns a patch with tests.", file: "firedrill/remediate.py", adr: "ADR-0004", sponsor: "Factory" },
  { id: "patch", x: 320, y: 360, w: 150, h: 66, kind: "loop", label: "Patch", sub: "policy + tool gates",
    detail: "A policy and a tool scope (allowed, gated, removed) with regression tests. Applied as a new hardening level, and run against the same drills on more seeds.", file: "patches/*.json" },

  { id: "stats", x: 980, y: 490, w: 150, h: 60, kind: "evidence", label: "Statistics", sub: "Wilson · CP · Fisher",
    detail: "Intervals on every rate, a breach grid that stops each cell at pre-planned looks with alpha split across them, Fisher’s exact test on before vs after, and the generalization gap.", file: "firedrill/stats.py · grid.py · scorecard.py" },
  { id: "ui", x: 760, y: 490, w: 150, h: 60, kind: "evidence", label: "Scorecard", sub: "this page + REPORT",
    detail: "This page, built from the same exported records, and the Actor’s REPORT.html. Both are single files that work with no network.", file: "ui/ · firedrill/render.py" },
  { id: "commit", x: 540, y: 490, w: 150, h: 60, kind: "evidence", label: "Commit-reveal", sub: "salted Merkle root",
    detail: "Held-out drills are committed as a salted Merkle root before any patch exists, then revealed with their salts, so anyone can check the test set was not swapped.", file: "firedrill/commit.py", adr: "ADR-0002" },
];

const EDGES: { d: string; kind: "core" | "adapter" | "loop" | "evidence"; label?: string }[] = [
  { d: "M180,93 H220", kind: "core" }, { d: "M370,93 H410", kind: "core" },
  { d: "M560,93 H600", kind: "core" }, { d: "M750,93 H790", kind: "core" },
  { d: "M940,93 H980", kind: "core" },
  { d: "M485,126 V220", kind: "adapter" }, { d: "M655,126 V220", kind: "adapter" },
  { d: "M725,126 V165 H805 V220", kind: "adapter" }, { d: "M910,126 V220", kind: "adapter" },
  { d: "M1090,126 V220", kind: "adapter" },
  { d: "M1130,93 H1170 V393 H1130", kind: "loop" }, { d: "M980,393 H910", kind: "loop" },
  { d: "M760,393 H690", kind: "loop" }, { d: "M540,393 H470", kind: "loop" },
  { d: "M395,360 V315 H570 V110 H600", kind: "loop", label: "patched config" },
  { d: "M1055,426 V490", kind: "evidence" }, { d: "M980,520 H910", kind: "evidence" },
  { d: "M1000,426 V460 H615 V490", kind: "evidence" },
];

const FLOWS = [
  { d: "M105,93 H1055", cls: "pkt pkt--attack", dur: 4.2, n: 3 },
  { d: "M1130,93 H1170 V393 H395 V315 H570 V110 H600", cls: "pkt pkt--fix", dur: 6, n: 2 },
];

const BANDS = [
  { y: 30, text: "Core · deterministic" },
  { y: 205, text: "Ports & adapters · each swappable, each with an offline fallback" },
  { y: 345, text: "Remediation loop" },
  { y: 475, text: "Evidence" },
];

const ADRS = [
  { id: "ADR-0001", title: "Deterministic scoring", text: "The verdict is a predicate over ledger state, never a model reading a transcript." },
  { id: "ADR-0002", title: "Held out by family, committed first", text: "Patches are written from some tactic families and tested on others, committed as a salted Merkle root before any patch exists." },
  { id: "ADR-0003", title: "Stateless Standby", text: "Conversation and ledger live in a shared key-value store, so any container serves any turn." },
  { id: "ADR-0004", title: "Swappable code-agent port", text: "Claude Code and Factory Droid sit behind one interface and receive the same brief." },
];

export default function Architecture() {
  const [sel, setSel] = useState("agent");
  const reduce = useReducedMotion();
  const node = NODES.find((n) => n.id === sel)!;

  return (
    <Section
      id="system"
      no="06"
      title="The system"
      lede="Ports and adapters. The core — drill, agent, ledger, scorer — runs offline with no sponsor at all; every integration plugs into a port and can be dropped without breaking a verdict. Red packets are an attack moving through; dark ones are a fix coming back. Select any part."
    >
      <div className="arch">
        <div className="arch__map">
          <svg viewBox="0 0 1190 580" role="group" aria-label="System map">
            <defs>
              <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                <path d="M0,0 L10,5 L0,10 z" className="arch__arrowhead" />
              </marker>
            </defs>
            {BANDS.map((b) => <text key={b.y} x={30} y={b.y} className="arch__band">{b.text.toUpperCase()}</text>)}
            {EDGES.map((e, i) => (
              <path key={i} d={e.d} className={`arch__edge arch__edge--${e.kind}`} markerEnd="url(#arrow)" />
            ))}
            <text x={480} y={306} className="arch__edgelabel">patched config ↑</text>
            {!reduce && FLOWS.flatMap((f) =>
              Array.from({ length: f.n }, (_, i) => (
                <circle key={`${f.cls}${i}`} r={5} className={f.cls}>
                  <animateMotion dur={`${f.dur}s`} begin={`${(i * f.dur) / f.n}s`} repeatCount="indefinite" path={f.d} />
                </circle>
              )),
            )}
            {NODES.map((n) => (
              <g
                key={n.id}
                className={`arch__node arch__node--${n.kind}${sel === n.id ? " is-sel" : ""}`}
                role="button"
                tabIndex={0}
                aria-pressed={sel === n.id}
                aria-label={`${n.label}: ${n.sub}`}
                onClick={() => setSel(n.id)}
                onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setSel(n.id); } }}
              >
                <rect x={n.x} y={n.y} width={n.w} height={n.h} />
                <text x={n.x + 12} y={n.y + (n.h > 60 ? 28 : 25)} className="arch__label">{n.label.toUpperCase()}</text>
                <text x={n.x + 12} y={n.y + (n.h > 60 ? 48 : 43)} className="arch__sub">{n.sub}</text>
                {n.sponsor && n.kind !== "adapter" && <rect x={n.x + n.w - 10} y={n.y} width={10} height={10} className="arch__spon" />}
              </g>
            ))}
          </svg>
        </div>

        <aside className="arch__detail" aria-live="polite">
          <div>
            <span className="eyebrow">{node.kind === "adapter" ? "Adapter" : node.kind === "loop" ? "Remediation" : node.kind === "evidence" ? "Evidence" : "Core"}</span>
            <h3 className="sign arch__h">{node.label}</h3>
          </div>
          <p>{node.detail}</p>
          <dl>
            <div><dt>Code</dt><dd><code>{node.file}</code></dd></div>
            {node.sponsor && <div><dt>Sponsor</dt><dd>{node.sponsor}</dd></div>}
            {node.adr && <div><dt>Decision</dt><dd>{node.adr}</dd></div>}
          </dl>
        </aside>
      </div>

      <ol className="adrs">
        {ADRS.map((a) => (
          <li key={a.id}>
            <span className="adrs__id num">{a.id}</span>
            <h4 className="sign">{a.title}</h4>
            <p>{a.text}</p>
          </li>
        ))}
      </ol>
    </Section>
  );
}
