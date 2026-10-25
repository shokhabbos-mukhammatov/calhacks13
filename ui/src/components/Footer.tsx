import { data, providerOf } from "../data";
import "./Footer.css";

/** What the page does not show is part of the result. */
export default function Footer() {
  const m = data.meta;
  const held = data.heldout;
  // The models a fix has been measured on: the headline's, and every other
  // model that breaks at baseline and has a patch run on it.
  const fixedOn = [data.headline?.model, ...(data.contrast?.providers ?? []).map((p) => p.model)]
    .filter((x): x is string => !!x);
  const fixedProviders = new Set(fixedOn.map(providerOf)).size;
  return (
    <footer className="foot">
      <div className="wrap foot__grid">
        <div>
          <h2 className="sign foot__h">What this does not show yet</h2>
          <ul className="foot__gaps">
            <li>
              {held.length ? (
                <>
                  <b>One held-out family.</b> The fix was tested against {held.length === 1 ? "one family" : `${held.length} families`} it
                  never saw ({held.flatMap((h) => h.families).join(", ")}). Executive impersonation has
                  cards but no attacker turns yet, so it is the next test, not a result.
                </>
              ) : (
                <>
                  <b>Generalization is untested.</b> The fix has not been run against a family it never
                  saw, so it is not yet known whether it learned behaviour or wording.
                </>
              )}
            </li>
            <li>
              {fixedOn.length > 1 ? (
                <>
                  <b>The fix is measured on {fixedOn.length} models, from {fixedProviders} providers.</b>{" "}
                  {fixedOn.join(" and ")} are the agents that
                  fall for the attack, so they are the ones a before-and-after means anything on. The held-out
                  test ran on the first of them only. The other models refused the attack at baseline,
                  leaving nothing for a patch to fix.
                </>
              ) : (
                <>
                  <b>The fix is measured on one model.</b> It is the agent that falls for the attack, so it
                  is the one every before-and-after is measured on. The other models refused it at baseline,
                  leaving nothing for a patch to fix.
                </>
              )}
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
