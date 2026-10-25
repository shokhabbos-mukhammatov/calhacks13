import { motion, useInView } from "motion/react";
import { useRef } from "react";
import { data, scorecardFor, type Patch, type TraceStep } from "../data";
import "./DroidAtWork.css";

// The harness's own tools, as Droid sees them. Script and ToolSearch are how
// this version of Droid reaches MCP tools; they are plumbing, not decisions,
// so the timeline folds them away.
const HARNESS = new Set(["get_failures", "get_agent_tools", "check_patch"]);

interface Step {
  key: string;
  kind: "fetch" | "try" | "result" | "thought" | "gate";
  title: string;
  body?: string;
  tone?: "bad" | "good";
}

function scopeLine(input: Record<string, unknown>): string {
  const scope = (input.tool_scope ?? {}) as Record<string, string>;
  const changed = Object.entries(scope).filter(([, v]) => v !== "allowed");
  return changed.length
    ? changed.map(([t, v]) => `${t} → ${v === "requires_verification" ? "gated" : v === "denied" ? "removed" : v}`).join(" · ")
    : "no gates";
}

/** The recorded session, reduced to the decisions in it. */
function steps(trace: TraceStep[]): Step[] {
  const out: Step[] = [];
  trace.forEach((s, i) => {
    const key = String(i);
    if (s.kind === "tool_call" && HARNESS.has(s.tool)) {
      if (s.tool === "check_patch") out.push({ key, kind: "try", title: "Tries a scope", body: scopeLine(s.input) });
      else out.push({ key, kind: "fetch", title: s.tool === "get_failures" ? "Reads the failures (as roles)" : "Reads what each scope means" });
    } else if (s.kind === "tool_result" && s.tool === "check_patch") {
      // The trace clips long results, so read the verdict fields from the
      // front of the text rather than parsing JSON that may be cut off.
      const blocked = s.content.match(/"failures_blocked":\s*"(\d+ of \d+)/)?.[1];
      const all = /"all_failures_blocked":\s*true/.test(s.content);
      const paid = /"ordinary_invoice_paid_on_file":\s*true/.test(s.content);
      out.push(blocked
        ? { key, kind: "result", tone: all && paid ? "good" : "bad",
            title: `Harness: ${blocked} failure paths blocked`,
            body: `ordinary invoice still paid on file: ${paid ? "yes" : "no"}` }
        : { key, kind: "result", title: "Harness replied", body: s.content.slice(0, 160) });
    } else if (s.kind === "message" && !s.text.trim().startsWith("{")) {
      out.push({ key, kind: "thought", title: "Droid", body: s.text });
    } else if (s.kind === "permission") {
      out.push({ key, kind: "gate", tone: s.approved ? "good" : "bad",
        title: `Permission gate ${s.approved ? "approved" : "cancelled"}`, body: s.actions.join(", ") });
    }
  });
  return out;
}

export default function DroidAtWork() {
  const entry = Object.entries(data.patches).find(([, p]) => p.author === "droid-sdk" && p.trace?.length);
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-20%" });
  if (!entry) return null;
  const [name, patch] = entry as [string, Patch];
  const timeline = steps(patch.trace ?? []);
  const measured = data.headline && scorecardFor(data.headline.model, `patch:${name}`);

  return (
    <div className="droid" ref={ref}>
      <div className="droid__head">
        <div>
          <span className="eyebrow">Factory Droid SDK · patches/{name}.json</span>
          <h3 className="sign droid__h">Droid, fired by the grid</h3>
          <p className="droid__lede">
            Nobody asked Droid to run. The breach grid did, the moment a control was decidedly broken —
            and Droid can touch exactly three harness tools, nothing else. It checks its own patch
            against the deterministic scorer before handing it back.
          </p>
        </div>
        <dl className="droid__access">
          <div><dt>Trigger</dt><dd>{patch.trigger?.reason ?? "—"}</dd></div>
          <div><dt>Can use</dt><dd><code>get_failures</code> · <code>get_agent_tools</code> · <code>check_patch</code></dd></div>
          <div><dt>Cannot</dt><dd>read files, run a shell, fetch a URL, or see the attacker’s words — probed, not assumed</dd></div>
        </dl>
      </div>

      <ol className="droid__steps">
        {timeline.map((s, i) => (
          <motion.li
            key={s.key}
            className={`dstep dstep--${s.kind}${s.tone ? ` dstep--${s.tone}` : ""}`}
            initial={{ opacity: 0, x: -10 }}
            animate={inView ? { opacity: 1, x: 0 } : {}}
            transition={{ delay: 0.15 + i * 0.22 }}
          >
            <span className="dstep__n num">{String(i + 1).padStart(2, "0")}</span>
            <div>
              <b>{s.title}</b>
              {s.body && <p>{s.body}</p>}
            </div>
          </motion.li>
        ))}
      </ol>

      <div className="droid__end">
        <div>
          <span className="eyebrow">Re-checked by the harness, not taken on Droid’s word</span>
          <p className="num">{patch.check?.failures_blocked ?? "—"}</p>
        </div>
        {measured && (
          <div>
            <span className="eyebrow">Then measured on real drills</span>
            <p className="num">
              <b className="t-safe">{measured.asr.k}/{measured.asr.n}</b> breaches ·{" "}
              <b>{measured.u.k}/{measured.u.n}</b> honest invoices paid
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
