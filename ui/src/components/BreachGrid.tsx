import { useState } from "react";
import { data, type Cell } from "../data";
import { fmt } from "../lib/stats";
import Units from "./Units";
import "./BreachGrid.css";

type Kind = "wilson" | "cp";
const EXPLORATORY = 6;   // fewer drills than one look: a cell that says nothing yet

/** The breach grid as a grid: a row per model and card, the hardening levels
 * as columns, so before and after read left to right on one line. Nothing is
 * dropped. Models that never broke, and exploratory runs of a few drills, are
 * folded behind a toggle, because a column of empty squares under a patch
 * that had nothing to fix is not a result, and burying the rows that are one
 * under it is its own way of dressing the data up. */
export default function BreachGrid({ kind }: { kind: Kind }) {
  const [showHolders, setShowHolders] = useState(false);
  const [showExploratory, setShowExploratory] = useState(false);
  const all: Cell[] = [...data.cells, ...(data.revealed_cells ?? [])];
  const h = data.headline;

  // A model is exploratory if none of its cells reaches one look.
  const models = [...new Set(all.map((c) => c.model))];
  const exploratoryModel = (m: string) => all.filter((c) => c.model === m).every((c) => c.n < EXPLORATORY);
  const baseline = (m: string) => all.filter((c) => c.model === m && c.config === "baseline");
  const rate = (m: string) => {
    const b = baseline(m), n = b.reduce((s, c) => s + c.n, 0);
    return n ? b.reduce((s, c) => s + c.k, 0) / n : 0;
  };
  const breaks = (m: string) => baseline(m).some((c) => c.k > 0);
  const order = (m: string) => (m === h?.model ? -1 : -rate(m));
  const breaking = models.filter((m) => !exploratoryModel(m) && breaks(m)).sort((a, b) => order(a) - order(b));
  const holders = models.filter((m) => !exploratoryModel(m) && !breaks(m)).sort();
  const exploratory = models.filter(exploratoryModel).sort();

  // Columns: no controls, then the headline patch, the other patches, then the
  // rest. A level whose every cell is exploratory only shows with the toggle.
  const levelRank = (cfg: string) =>
    cfg === "baseline" ? 0 : cfg === h?.after ? 1 : cfg.startsWith("patch:") ? 2 : cfg === "baseline+verify" ? 3 : 4;
  const shownModels = [...breaking, ...(showHolders ? holders : []), ...(showExploratory ? exploratory : [])];
  const levels = [...new Set(all.filter((c) => shownModels.includes(c.model)).map((c) => c.config))]
    .filter((cfg) => showExploratory || all.some((c) => c.config === cfg && c.n >= EXPLORATORY))
    .sort((a, b) => levelRank(a) - levelRank(b) || a.localeCompare(b));

  const heldOutFamilies = new Set((data.revealed_cells ?? []).map((c) => c.family));
  const cardsOf = (m: string) => [...new Set(all.filter((c) => c.model === m).map((c) => c.card_id))]
    .sort((a, b) => Number(heldOutFamilies.has(familyOf(a))) - Number(heldOutFamilies.has(familyOf(b))) || a.localeCompare(b));
  const familyOf = (card: string) => all.find((c) => c.card_id === card)?.family ?? "";
  const cell = (m: string, cfg: string, card: string) =>
    all.find((c) => c.model === m && c.config === cfg && c.card_id === card);

  const holderSummary = (() => {
    const base = all.filter((c) => holders.includes(c.model) && c.config === "baseline");
    const patched = all.filter((c) => holders.includes(c.model) && c.config.startsWith("patch:"));
    const sum = (cs: Cell[]) => [cs.reduce((s, c) => s + c.k, 0), cs.reduce((s, c) => s + c.n, 0)];
    return { base: sum(base), patched: sum(patched) };
  })();

  const rows = (m: string, dim: boolean) => {
    const cards = cardsOf(m);
    return cards.map((card, i) => (
      <tr key={`${m}${card}`} className={`${i === 0 ? "is-first" : ""}${dim ? " is-dim" : ""}`}>
        {i === 0 && <th scope="rowgroup" rowSpan={cards.length} className="bmx__model mono">{m}</th>}
        <th scope="row" className="bmx__card mono">
          {card}
          {heldOutFamilies.has(familyOf(card)) && <span className="bmx__tag">held out</span>}
        </th>
        {levels.map((cfg) => {
          const c = cell(m, cfg, card);
          return (
            <td key={cfg} className={`bmx__cell${c && c.n < EXPLORATORY ? " is-small" : ""}`}>
              {c ? (
                <>
                  <Units cell={c} dim={c.n < EXPLORATORY} micro />
                  <span className="bmx__k num">
                    <b className={c.k ? "t-signal" : ""}>{c.k}</b>/{c.n}
                    <span className="bmx__ci"> [{fmt(c[kind][0])}, {fmt(c[kind][1])}]</span>
                  </span>
                </>
              ) : (
                <span className="bmx__none" aria-label="not run">·</span>
              )}
            </td>
          );
        })}
      </tr>
    ));
  };

  return (
    <div className="bmx">
      <div className="bmx__scroll">
        <table className="bmx__table">
          <thead>
            <tr>
              <th scope="col">Model</th>
              <th scope="col">Card</th>
              {levels.map((cfg) => <th scope="col" key={cfg} className="mono">{cfg}</th>)}
            </tr>
          </thead>
          <tbody>
            {breaking.map((m) => rows(m, false))}
            {holders.length > 0 && !showHolders && (
              <tr className="bmx__fold">
                <td colSpan={levels.length + 2}>
                  <b>{holders.length} {holders.length === 1 ? "model" : "models"} never broke:</b>{" "}
                  <span className="mono">{holders.join(", ")}</span>. {holderSummary.base[0]} of{" "}
                  {holderSummary.base[1]} drills paid the attacker with no controls
                  {holderSummary.patched[1] > 0 && <>, and {holderSummary.patched[0]} of {holderSummary.patched[1]} under a patch</>}:
                  nothing for a patch to fix.{" "}
                  <button className="bmx__toggle" onClick={() => setShowHolders(true)}>Show their rows</button>
                </td>
              </tr>
            )}
            {showHolders && holders.map((m) => rows(m, true))}
            {showExploratory && exploratory.map((m) => rows(m, true))}
          </tbody>
        </table>
      </div>
      <div className="bmx__controls">
        {showHolders && <button className="bmx__toggle" onClick={() => setShowHolders(false)}>Fold the models that never broke</button>}
        <button className="bmx__toggle" onClick={() => setShowExploratory((v) => !v)}>
          {showExploratory ? "Hide" : "Show"} exploratory runs (fewer than {EXPLORATORY} drills)
        </button>
      </div>
    </div>
  );
}
