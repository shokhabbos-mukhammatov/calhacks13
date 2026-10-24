import { motion, useInView } from "motion/react";
import { useRef, useState } from "react";
import { data, scorecardFor } from "../data";
import Section from "./Section";
import "./Fix.css";

const SCOPE_WORD: Record<string, { text: string; cls: string }> = {
  allowed: { text: "allowed", cls: "sc--allowed" },
  requires_verification: { text: "gated", cls: "sc--gated" },
  denied: { text: "removed", cls: "sc--denied" },
};

const AUTHORS: Record<string, string> = { "claude-code": "Claude Code", droid: "Factory Droid" };

/** The headline patch first, then the rest: file order would put Droid's
 * "v1-droid" before "v1" only because "-" sorts before ".". */
const patchNames = () => {
  const lead = data.headline?.after.replace(/^patch:/, "");
  return Object.keys(data.patches).sort((a, b) => Number(b === lead) - Number(a === lead) || a.localeCompare(b));
};

function Redaction() {
  const ex = data.failure_example;
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-25%" });
  const [run, setRun] = useState(0);
  if (!ex) return null;
  const go = inView;

  return (
    <div className="redact" ref={ref}>
      <div className="redact__head">
        <div>
          <span className="eyebrow">What happened · drill {ex.drill}</span>
          <h3 className="redact__h sign">The record</h3>
        </div>
        <div>
          <span className="eyebrow">What the coding agent is shown</span>
          <h3 className="redact__h sign">The failure, as roles</h3>
        </div>
      </div>
      <ol className="redact__rows" key={run}>
        {ex.tool_calls.map((c, i) => {
          const s = ex.summary.steps[i];
          return (
            <li key={i} className="redact__row">
              <code className="redact__cell redact__cell--raw">
                <b>{c.tool}</b>(
                {Object.entries(c.input).map(([k, v], j) => (
                  <span key={k}>{j > 0 && ", "}{k}=<mark className="raw">{v}</mark></span>
                ))}
                )
              </code>
              <motion.span
                className="redact__arrow"
                aria-hidden="true"
                initial={{ opacity: 0 }}
                animate={go ? { opacity: 1 } : {}}
                transition={{ delay: 0.3 + i * 0.35 }}
              >→</motion.span>
              <code className="redact__cell">
                <b>{s?.tool ?? c.tool}</b>(
                {Object.entries(s?.args ?? {}).map(([k, v], j) => (
                  <span key={k}>
                    {j > 0 && ", "}{k}=
                    <motion.span
                      className="role"
                      initial={{ opacity: 0, filter: "blur(6px)" }}
                      animate={go ? { opacity: 1, filter: "blur(0px)" } : {}}
                      transition={{ delay: 0.45 + i * 0.35 + j * 0.08, duration: 0.4 }}
                    >{v}</motion.span>
                  </span>
                ))}
                )
              </code>
            </li>
          );
        })}
      </ol>
      <div className="redact__foot">
        <p>
          <b>Not one word of the attacker’s message crosses this line.</b> A patch written from wording
          learns to block phrases and fails on the next attack; a patch written from actions has to
          change behaviour. Money went to <code className="role">{ex.summary.money_went_to}</code>, on
          turn {ex.summary.capitulation_turn}.
        </p>
        <button className="btn" onClick={() => setRun((r) => r + 1)}>↺ Run the redaction again</button>
      </div>
    </div>
  );
}

function ScopeMatrix() {
  const names = patchNames();
  const tools = data.tools.map((t) => t.name);
  return (
    <div className="matrix-wrap">
      <table className="matrix">
        <thead>
          <tr>
            <th scope="col">Tool</th>
            <th scope="col">No controls</th>
            {names.map((n) => (
              <th scope="col" key={n}>{AUTHORS[data.patches[n].author] ?? n}<span className="matrix__sub">patch {n}</span></th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tools.map((t) => (
            <tr key={t}>
              <th scope="row"><code>{t}</code>{t === "export_vendor_master" && <span className="matrix__canary">canary</span>}</th>
              <td><span className="sc sc--allowed">allowed</span></td>
              {names.map((n) => {
                const v = data.patches[n].tool_scope[t] ?? "allowed";
                const w = SCOPE_WORD[v] ?? { text: v, cls: "" };
                return <td key={n} className={v !== "allowed" ? "is-changed" : ""}><span className={`sc ${w.cls}`}>{w.text}</span></td>;
              })}
            </tr>
          ))}
          <tr className="matrix__result">
            <th scope="row">Attack drills held</th>
            {(() => {
              const h = data.headline;
              const base = h && scorecardFor(h.model, h.before);
              return <td className="num">{base ? `${base.s.k}/${base.s.n}` : "—"}</td>;
            })()}
            {names.map((n) => {
              const sc = data.headline && scorecardFor(data.headline.model, `patch:${n}`);
              return <td key={n} className="num"><b>{sc ? `${sc.s.k}/${sc.s.n}` : "—"}</b></td>;
            })}
          </tr>
        </tbody>
      </table>
      <p className="note">
        Given the same failures, the two code agents chose different structures. Claude Code kept the
        bank-change tool and <b>gated the payment</b> behind a confirmed callback to the number on file;
        Droid <b>removed bank changes from the agent entirely</b> and moved that work to a separate
        workflow. Both held. Droid’s arm has fewer drills, so its interval is wider.
      </p>
    </div>
  );
}

function Policies() {
  return (
    <div className="policies">
      {patchNames().map((name) => [name, data.patches[name]] as const).map(([name, p]) => (
        <article className="policy" key={name}>
          <header>
            <span className="eyebrow">patches/{name}.json</span>
            <h4 className="sign">{AUTHORS[p.author] ?? p.author}’s reasoning</h4>
          </header>
          <ol className="policy__why">
            {p.rationale.slice(0, 3).map((r, i) => <li key={i}>{r}</li>)}
          </ol>
          <details>
            <summary>Read the full policy it wrote</summary>
            <pre className="policy__text">{p.policy}</pre>
          </details>
        </article>
      ))}
    </div>
  );
}

function GateProof() {
  const h = data.headline;
  const sc = h && scorecardFor(h.model, "scope:v1");
  return (
    <div className="gate">
      <div className="gate__copy">
        <h3 className="sign gate__h">Was it the words or the code?</h3>
        <p>
          Under the full patch the agent never even attempted a bank change, so the gate never fired —
          the policy text did all the work. That proves less than it looks. <code>scope:v1</code> keeps
          the gates and <b>deletes the policy</b>. The agent changed the bank details and called{" "}
          <code>approve_payment</code>; the code refused.
        </p>
        {sc && (
          <p className="gate__stat">
            <b className="num">{sc.s.k}/{sc.s.n}</b> held with no policy text at all.
          </p>
        )}
        <a className="btn" href="#drill">Replay it: “Gate only” ↑</a>
      </div>
      <pre className="gate__code" aria-label="The gate in firedrill/victim.py">
{`def _t_approve_payment(self, invoice_id):
    if self._scope.get("approve_payment") == "requires_verification":
        inv = self._ledger.read_invoice(invoice_id)
        v = self._ledger.lookup_vendor(inv.vendor_id)
        if v.active_account not in v.approved_accounts:
            raise _Blocked(
                "Blocked: bank account changed and not verified by a "
                "confirmed callback to the phone number on file. "
                "No payment was made.")
    p = self._ledger.approve_payment(invoice_id)`}
      </pre>
    </div>
  );
}

export default function Fix() {
  return (
    <Section
      id="fix"
      no="03"
      title="The fix"
      lede="A coding agent rewrites the controls from the failing drills. What it is allowed to see is the whole trick: what the agent did, with every value replaced by its role — never what the attacker said."
    >
      <Redaction />
      <h3 className="fix__h sign">Two code agents, two different fixes</h3>
      <ScopeMatrix />
      <Policies />
      <GateProof />
    </Section>
  );
}
