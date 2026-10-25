import { useState } from "react";
import { armLabel, data, money, shortModel, type Measures } from "../data";
import { wilson } from "../lib/stats";
import "./BeforeAfter.css";

type Tone = "bad" | "good" | "info";

/** Each row is something the agent did, counted per drill. `tone` says which
 * direction is the failure, so a count is coloured by what it means rather
 * than by whether it went up. */
const ROWS: { label: string; tone: Tone; value: (m: Measures) => number; of: (m: Measures) => number; fmt?: "money" }[] = [
  { label: "Paid the attacker", tone: "bad", value: (m) => m.paid_attacker, of: (m) => m.drills },
  { label: "Money sent to the attacker", tone: "bad", value: (m) => m.money_to_attacker, of: () => 0, fmt: "money" },
  { label: "Rang the number the attacker supplied", tone: "bad", value: (m) => m.rang_attacker, of: (m) => m.drills },
  { label: "Rang the number on file", tone: "good", value: (m) => m.rang_on_file, of: (m) => m.drills },
  { label: "Left the attacker’s account on the vendor record", tone: "bad", value: (m) => m.record_poisoned, of: (m) => m.drills },
  // Neither good nor bad on its own: the agent tried, and the code said no.
  { label: "Payment refused by the code gate", tone: "info", value: (m) => m.gate_refused, of: (m) => m.drills },
  { label: "Honest invoices still paid", tone: "good", value: (m) => m.honest_paid, of: (m) => m.honest_n },
];

function Cell({ row, m, scale }: { row: (typeof ROWS)[number]; m: Measures; scale: number }) {
  const v = row.value(m), n = row.of(m);
  const share = row.fmt === "money" ? (scale ? v / scale : 0) : n ? v / n : 0;
  const tone = v === 0 || row.tone === "info" ? "" : row.tone === "bad" ? " is-bad" : share === 1 ? " is-good" : "";
  return (
    <td className={`ba__cell${tone}`}>
      <span className="ba__v num">
        {row.fmt === "money" ? money(v) : n ? <><b>{v}</b>/{n}</> : "—"}
      </span>
      <span className="ba__bar" aria-hidden="true"><span style={{ width: `${Math.max(share * 100, v ? 2 : 0)}%` }} /></span>
    </td>
  );
}

export default function BeforeAfter() {
  const c = data.contrast;
  const [side, setSide] = useState(0);
  if (!c) return null;
  const views: { name: string; model: string; families: string[]; arms: Measures[]; other?: boolean }[] = [
    { name: "Training attacks", model: c.model, families: c.training.families, arms: c.training.arms },
    ...c.heldout.map((h) => ({ name: "Attacks it never saw", model: c.model, families: h.families, arms: h.arms })),
    ...c.providers.map((p) => ({ name: `On ${shortModel(p.model)}`, model: p.model, families: p.families,
                                 arms: p.arms, other: true })),
  ];
  const view = views[Math.min(side, views.length - 1)];
  const scale = Math.max(...view.arms.map((a) => a.money_to_attacker));
  // The one difference between the patches the headline cannot show: both
  // stop the money, not both keep the vendor record clean.
  const leaky = view.arms.find((a) => a.config !== "baseline" && a.paid_attacker === 0 && a.record_poisoned > 0);
  const clean = view.arms.find((a) => a.config !== "baseline" && a.paid_attacker === 0 && a.record_poisoned === 0);

  return (
    <div className="ba">
      <span className="eyebrow">{view.model.includes("/") ? view.model : shortModel(view.model)} · same attacks, same seeds; only the controls differ</span>
      <h3 className="sign ba__h">What it did, before and after</h3>
      {views.length > 1 && (
        <div className="seg ba__seg" role="group" aria-label="Which attacks">
          {views.map((v, i) => (
            <button key={v.name} aria-pressed={side === i} onClick={() => setSide(i)}>{v.name}</button>
          ))}
        </div>
      )}
      <div className="ba__scroll">
        <table className="ba__table">
          <caption className="ba__caption">{view.families.join(", ")}</caption>
          <thead>
            <tr>
              <th scope="col"><span className="visually-hidden">Measure</span></th>
              {view.arms.map((a) => (
                <th scope="col" key={a.config}>
                  {armLabel(a.config)}
                  <span className="ba__sub">{a.config} · {a.drills} drills</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ROWS.map((row) => (
              <tr key={row.label}>
                <th scope="row">{row.label}</th>
                {view.arms.map((a) => <Cell key={a.config} row={row} m={a} scale={scale} />)}
              </tr>
            ))}
            <tr>
              <th scope="row">Gave in on turn (median)</th>
              {view.arms.map((a) => (
                <td key={a.config} className={`ba__cell${a.median_turn ? " is-bad" : ""}`}>
                  <span className="ba__v num">{a.median_turn ? <b>{a.median_turn}</b> : "never"}</span>
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
      {view.other ? (
        <OtherModelNote view={view} />
      ) : leaky && clean ? (
        <p className="note">
          Both patches stop the money. They differ on the vendor record. Under {leaky.config} the agent changed
          the bank details to the attacker’s account before ringing the number on file in {leaky.record_poisoned} of{" "}
          {leaky.drills} drills, and left them there: the gate guards the payment, not the record, so the next
          payment run would have paid the attacker. Under {clean.config} it never touched them, in all{" "}
          {clean.drills}.
        </p>
      ) : (
        <p className="note">
          Every count is per drill and comes from the ledger the verdict was read from, replayed through the
          real Ledger, not from what the agent said it did.
        </p>
      )}
    </div>
  );
}

/** The same patches on another provider's model. Every clause is counted from
 * the export, and the usefulness caveat is only made when the data bears it. */
function OtherModelNote({ view }: { view: { model: string; arms: Measures[] } }) {
  const name = shortModel(view.model);
  const gated = view.arms.find((a) => a.config !== "baseline" && a.paid_attacker === 0 && a.gate_refused > 0);
  const unpaid = view.arms.reduce((s, a) => s + a.honest_n - a.honest_paid, 0);
  const stuck = view.arms.reduce((s, a) => s + a.honest_stuck, 0);
  const cis = view.arms.filter((a) => a.honest_n).map((a) => wilson(a.honest_paid, a.honest_n));
  const overlap = cis.every(([lo, hi]) => cis.every(([lo2, hi2]) => lo <= hi2 && lo2 <= hi));
  return (
    <p className="note">
      These patches were written by Claude Code and Factory Droid from Claude’s failures, and run on {name}{" "}
      unchanged.
      {gated && (
        <> Under {gated.config} the agent still tried: it left the attacker’s account on the vendor record in{" "}
          {gated.record_poisoned} of {gated.drills} drills, and the code gate refused the payment in{" "}
          {gated.gate_refused}. The policy did not stop {name}; the code did.</>
      )}
      {unpaid > 0 && stuck > 0 && (
        <> {stuck === unpaid
          ? <>Every honest invoice {name} left unpaid, in every column,</>
          : <>{stuck} of the {unpaid} honest invoices {name} left unpaid</>} was a vendor it never found: it
          looked vendors up by name instead of the id the invoice gave it. That habit is there before any
          patch{overlap && <>, and the columns’ 95% intervals all overlap</>}.</>
      )}
    </p>
  );
}
