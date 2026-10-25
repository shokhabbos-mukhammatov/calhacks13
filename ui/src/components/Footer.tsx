import { data } from "../data";
import "./Footer.css";

/** What the page does not show is part of the result. */
export default function Footer() {
  const m = data.meta;
  return (
    <footer className="foot">
      <div className="wrap foot__grid">
        <div>
          <h2 className="sign foot__h">What this does not show yet</h2>
          <ul className="foot__gaps">
            <li>
              <b>Generalization is untested.</b> Every drill so far is one tactic family. The fix has not
              been run against families it never saw, so it is not yet known whether it learned
              behaviour or wording. The held-out machinery is built and waiting.
            </li>
            <li>
              <b>One model.</b> The headline is Claude Haiku 4.5. Other models were drilled only in early
              exploratory runs, at a few drills each.
            </li>
            <li>
              <b>Phone calls are a demonstration, not the measurement.</b> The statistics come from
              recorded text drills; a live call runs the same agent and ledger but is not counted.
            </li>
          </ul>
        </div>
        <div className="foot__meta">
          <span className="nav__mark" aria-hidden="true">F</span>
          <p className="sign foot__brand">Fire Drill</p>
          <p>Built solo at Cal Hacks 13.</p>
          <dl>
            <div><dt>Drills on this page</dt><dd className="num">{m.records}</dd></div>
            <div><dt>Exported</dt><dd className="num">{m.generated_at.replace("T", " ").replace("+00:00", " UTC")}</dd></div>
            {m.commit && <div><dt>Commit</dt><dd className="num">{m.commit}</dd></div>}
            {m.attacks_withheld && <div><dt>Note</dt><dd>Attacker message text withheld from this build</dd></div>}
          </dl>
          <a href={data.live.repo} target="_blank" rel="noreferrer">Source on GitHub ↗</a>
        </div>
      </div>
    </footer>
  );
}
