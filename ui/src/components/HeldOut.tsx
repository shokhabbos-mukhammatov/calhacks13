import { shortModel, type HeldOut as Result } from "../data";
import { fmt, sci } from "../lib/stats";
import Units from "./Units";
import "./HeldOut.css";

const utc = (iso: string) => `${new Date(iso).toISOString().slice(0, 16).replace("T", " ")} UTC`;
const signed = (v: number) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${fmt(Math.abs(v))}`;

/** The claim a patch has to survive: attacks it never saw. Everything here is
 * the held-out family on its own, beside the training family under the same
 * patch. Nothing elsewhere on the page is pooled with these drills. */
export default function HeldOut({ result: h, kind }: { result: Result; kind: "wilson" | "cp" }) {
  const b = h.held_before, a = h.held_after, t = h.train_after, u = h.utility_after;
  const was = h.behaviour.before, now = h.behaviour.after;
  const family = h.families.join(", ");
  const c = h.commitment;

  return (
    <div className="held">
      <span className="eyebrow">{shortModel(h.model)} · held-out family: {family}</span>
      <h3 className="sign held__h">On attacks it never saw</h3>
      <p className="note held__lede">
        Droid wrote patch {h.name} from the {h.train_families.join(", ")} failures alone. The {family} family
        was held out: its {c.count} drills against the unpatched agent were committed by hash before the
        patch existed, and revealed only after it had been run against them.
      </p>

      <div className="bgrid held__grid">
        <div className="bgrid__head">
          <span>Model</span><span>Hardening</span><span>Card</span><span>One cell per drill</span><span className="num">Breaches</span><span>95% interval</span>
        </div>
        {h.cells.map((cell) => (
          <div key={`${cell.config}${cell.card_id}`} className="bgrid__row">
            <span className="mono">{shortModel(cell.model)}</span>
            <span className="mono">{cell.config}</span>
            <span className="mono">{cell.card_id}</span>
            <Units cell={cell} />
            <span className="num bgrid__k"><b>{cell.k}</b>/{cell.n}</span>
            <span className="num bgrid__ci">[{fmt(cell[kind][0])}, {fmt(cell[kind][1])}]</span>
          </div>
        ))}
      </div>

      <div className="held__stats">
        <div className="res__stat">
          <span className="eyebrow">Breaches, held-out family</span>
          <span className="res__big num"><b className={b.k ? "t-signal" : ""}>{b.k}</b>/{b.n} → <b className="t-safe">{a.k}</b>/{a.n}</span>
          <span className="res__small">{h.before} → {h.after}</span>
        </div>
        <div className="res__stat">
          <span className="eyebrow">Fisher’s exact test, one-sided</span>
          <span className="res__big num">p = {sci(h.fisher_one_sided)}</span>
          <span className="res__small">before against after, on the held-out drills only</span>
        </div>
        <div className="res__stat">
          <span className="eyebrow">Generalization gap Δ</span>
          <span className="res__big num">{h.gap === null ? "—" : signed(h.gap)}</span>
          <span className="res__small">
            held-out {a.k}/{a.n} minus training {t.k}/{t.n}, both under {h.after}. A patch that learned the
            wording would show a large positive gap. Upper bounds {fmt(a[kind][1])} and {fmt(t[kind][1])}.
          </span>
        </div>
        <div className="res__stat">
          <span className="eyebrow">Honest invoices under {h.after}</span>
          <span className="res__big num">{u.k}/{u.n}</span>
          <span className="res__small">paid to the account on file, so it did not get safe by refusing</span>
        </div>
      </div>

      <dl className="held__proof">
        <div>
          <dt>Committed</dt>
          <dd>
            root <code title={c.root}>{c.root.slice(0, 16)}…</code> over {c.count} drills
            {c.commit && <>, in {c.commit_url
              ? <a href={c.commit_url} target="_blank" rel="noreferrer"><code>{c.commit.sha.slice(0, 7)}</code></a>
              : <code>{c.commit.sha.slice(0, 7)}</code>} at {utc(c.commit.committed_at)}</>}
            {c.original && (
              <span className="held__orig" title={c.original.note}>
                Originally{" "}
                <a href={c.original.url} target="_blank" rel="noreferrer"><code>{c.original.sha.slice(0, 7)}</code></a>,
                which GitHub logged at {utc(c.original.pushed_at)}. History was later rewritten to correct
                commit authorship: every commit ID changed, no file did.
              </span>
            )}
          </dd>
        </div>
        {h.patch_commit && (
          <div>
            <dt>Patch</dt>
            <dd>{h.name} first appears in <code>{h.patch_commit.sha.slice(0, 7)}</code> at {utc(h.patch_commit.committed_at)}</dd>
          </div>
        )}
        <div>
          <dt>Reveal</dt>
          <dd>
            {h.verified
              ? <b className="t-safe">The root recomputes from the revealed drills and salts.</b>
              : <b className="t-signal">The root does not recompute from the revealed drills.</b>}{" "}
            <a href={c.reveal_url} target="_blank" rel="noreferrer">Drills and salts ↗</a>
          </dd>
        </div>
      </dl>

      <p className="note">
        What changed is the number it rang. Unpatched, the agent called the number in the message{" "}
        {was.called_attacker} times and tried to change the bank details in {was.tried_bank_change} of{" "}
        {was.drills} drills. Under {h.after} it called the number on file {now.called_on_file} times
        {now.called_attacker === 0 ? " and the attacker’s never" : ` and the attacker’s ${now.called_attacker} times`},
        {now.tried_bank_change === 0
          ? " and it never asked to change the bank details or to pay anyone new, so the payment gate never had to fire: the patch’s policy did the work, with the gate behind it."
          : ` and it tried to change the bank details ${now.tried_bank_change} times, each one stopped by the gate.`}{" "}
        One held-out family and one model: evidence that the patch learned the behaviour rather than the
        wording, not proof that it covers every attack.
      </p>
    </div>
  );
}
