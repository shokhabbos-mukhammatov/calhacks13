"""Idea Council aggregator.

Usage:
  python aggregate.py cross <vault>    print each agent's round 2 cross-review brief
  python aggregate.py build <vault>    merge rounds into Idea Council/data/council.json
                                       and write Idea Council/Leaderboard.md
  python aggregate.py notes <vault>    write the council callout into every idea note

Council score of an idea family = best version's mean lens score
                                  + PICK_BONUS for each agent that picked any version.
A merge pivot ("Idea One + Idea Two") scores for its first parent only; it is listed
as related under the other parents.
"""
import json
import re
import sys
from pathlib import Path

AGENTS = ["A", "B", "C"]
AGENT_NAMES = {"A": "The Skeptic", "B": "The Impact Analyst", "C": "The Venture Scout"}
LENSES = {"A": "Substance", "B": "Impact", "C": "Novelty & venture"}
PICK_BONUS = 1.0


def load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def parse_idea_note(path):
    text = path.read_text(encoding="utf-8")
    fm = {}
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip('"')
        body = text[m.end():]
    else:
        body = text
    lines = body.splitlines()
    pitch = ""
    for i, line in enumerate(lines):
        if line.startswith("# "):
            for nxt in lines[i + 1:]:
                if nxt.strip():
                    pitch = nxt.strip()
                    break
            break
    sponsors = []
    sm = re.search(r"\*\*Sponsors:\*\*(.*)", body)
    if sm:
        sponsors = re.findall(r"\[\[([^\]]+)\]\]", sm.group(1))
    return {
        "name": path.stem,
        "pitch": pitch,
        "sponsors": sponsors,
        "angle": fm.get("cluster", ""),
        "trap": fm.get("trap") == "true",
        "shortlisted": fm.get("shortlisted") == "true",
        "old_score": float(fm["score"]) if fm.get("score") else None,
    }


def load_rounds(vault):
    data = vault / "Idea Council" / "data"
    r1 = {a: load_json(data / f"r1-{a}.json") for a in AGENTS}
    r2 = {a: load_json(data / f"r2-{a}.json") for a in AGENTS}
    missing = [a for a in AGENTS if r1[a] is None]
    if missing:
        sys.exit(f"Missing round 1 files for agents: {', '.join(missing)}")
    return data, r1, r2


def proposals(r1, agent):
    """Pivots and wildcards an agent proposed in round 1."""
    out = []
    for p in r1[agent].get("pivots", []) or []:
        out.append(("pivot", p))
    for w in r1[agent].get("wildcards", []) or []:
        out.append(("wildcard", w))
    return out


def cmd_cross(vault):
    _, r1, _ = load_rounds(vault)
    for agent in AGENTS:
        print(f"===== brief for {agent}")
        for other in AGENTS:
            if other == agent:
                continue
            for kind, p in proposals(r1, other):
                parent = f" (pivot of {p.get('parent')})" if kind == "pivot" else ""
                sponsors = f" Sponsors: {', '.join(p.get('sponsors', []))}." if p.get("sponsors") else ""
                change = f" Change: {p.get('change')}" if p.get("change") else ""
                print(f"- {p['id']} [{kind}] {p.get('name')}{parent}: {p.get('pitch')}{change}{sponsors} "
                      f"Proposer's reason: {p.get('why')}")
        print()


def cmd_build(vault):
    data, r1, r2 = load_rounds(vault)
    notes = {p.stem: parse_idea_note(p) for p in sorted((vault / "Ideas").glob("*.md"))}
    lower = {k.lower(): k for k in notes}

    candidates = {}

    def resolve_idea(name):
        name = (name or "").strip()
        return lower.get(name.lower())

    # Originals, scored by every agent in round 1.
    for name, note in notes.items():
        candidates[name] = {
            "id": name, "kind": "original", "name": name, "pitch": note["pitch"],
            "proposer": None, "parent": None, "change": None, "why": None,
            "families": [name], "scores": {},
        }
    for agent in AGENTS:
        for row in r1[agent]["ideas"]:
            key = resolve_idea(row.get("idea"))
            if key is None:
                print(f"warning: agent {agent} scored unknown idea {row.get('idea')!r}", file=sys.stderr)
                continue
            candidates[key]["scores"][agent] = {
                k: row.get(k) for k in
                ("score", "label", "take", "reasoning", "red_flag", "verdict", "sub", "evidence")
            }

    # Pivots and wildcards, scored by the proposer in round 1 and the others in round 2.
    for agent in AGENTS:
        for kind, p in proposals(r1, agent):
            fams = []
            if kind == "pivot":
                for part in re.split(r"\s*\+\s*", p.get("parent") or ""):
                    key = resolve_idea(part)
                    if key and key not in fams:
                        fams.append(key)
            if not fams:
                fams = [p["id"]]
            candidates[p["id"]] = {
                "id": p["id"], "kind": kind, "name": p.get("name"), "pitch": p.get("pitch"),
                "proposer": agent, "parent": p.get("parent"), "change": p.get("change"),
                "why": p.get("why"), "sponsors": p.get("sponsors", []), "families": fams,
                "scores": {agent: {"score": p.get("score"), "label": p.get("label"),
                                   "take": p.get("why"), "sub": p.get("sub")}},
            }
    for agent in AGENTS:
        if not r2[agent]:
            continue
        for row in r2[agent].get("cross", []):
            cand = candidates.get(row.get("ref"))
            if cand is None:
                print(f"warning: agent {agent} cross-scored unknown ref {row.get('ref')!r}", file=sys.stderr)
                continue
            cand["scores"][agent] = {"score": row.get("score"), "label": row.get("label"),
                                     "take": row.get("take")}

    # Final picks: round 2 if present, otherwise round 1.
    def resolve_ref(ref):
        if ref in candidates:
            return ref
        return resolve_idea(ref)

    picks = {}
    for agent in AGENTS:
        src = r2[agent] if r2[agent] else r1[agent]
        picks[agent] = []
        for p in src.get("picks", [])[:6]:
            cid = resolve_ref(p.get("ref"))
            if cid is None:
                print(f"warning: agent {agent} picked unknown ref {p.get('ref')!r}", file=sys.stderr)
                continue
            picks[agent].append({"rank": p.get("rank"), "ref": cid, "why": p.get("why")})

    for cand in candidates.values():
        vals = [s["score"] for s in cand["scores"].values() if isinstance(s.get("score"), (int, float))]
        cand["mean"] = round(sum(vals) / len(vals), 1) if vals else None
        cand["n_scores"] = len(vals)
        cand["pickers"] = [{"agent": a, "rank": p["rank"], "why": p["why"]}
                           for a in AGENTS for p in picks[a] if p["ref"] == cand["id"]]
        cand["council"] = round((cand["mean"] or 0) + PICK_BONUS * len(cand["pickers"]), 1)

    # Families: an original idea plus its pivots, or a standalone wildcard.
    families = {}
    for cand in candidates.values():
        families.setdefault(cand["families"][0], {"key": cand["families"][0], "versions": []})["versions"].append(cand["id"])
    fam_rows = []
    for key, fam in families.items():
        versions = [candidates[v] for v in fam["versions"]]
        scored = [v for v in versions if v["mean"] is not None]
        full = [v for v in scored if v["n_scores"] == len(AGENTS)]
        scored = full or scored
        best = max(scored, key=lambda v: (v["mean"], v["kind"] == "original")) if scored else versions[0]
        pickers = {}
        for v in versions:
            for p in v["pickers"]:
                prev = pickers.get(p["agent"])
                if prev is None or (p["rank"] or 99) < (prev["rank"] or 99):
                    pickers[p["agent"]] = {"agent": p["agent"], "rank": p["rank"], "via": v["id"],
                                           "via_kind": v["kind"], "why": p["why"]}
        note = notes.get(key)
        head = note or {"name": candidates[key]["name"], "pitch": candidates[key]["pitch"],
                        "sponsors": candidates[key].get("sponsors", []), "angle": "Wildcard",
                        "trap": False, "shortlisted": False, "old_score": None}
        fam_rows.append({
            "key": key, "kind": "original" if note else "wildcard",
            "name": head["name"], "pitch": head["pitch"], "sponsors": head["sponsors"],
            "angle": head["angle"], "trap": head["trap"], "shortlisted": head["shortlisted"],
            "old_score": head["old_score"], "versions": fam["versions"], "best": best["id"],
            "best_mean": best["mean"], "pickers": sorted(pickers.values(), key=lambda p: p["agent"]),
            "council": round((best["mean"] or 0) + PICK_BONUS * len(pickers), 1),
        })
    fam_rows.sort(key=lambda f: (-f["council"], -(f["best_mean"] or 0), f["name"]))
    for i, f in enumerate(fam_rows, 1):
        f["rank"] = i

    agents_meta = {}
    for a in AGENTS:
        agents_meta[a] = {
            "name": AGENT_NAMES[a], "lens": LENSES[a],
            "ceo_note": r1[a].get("ceo_note"),
            "changed": (r2[a] or {}).get("changed"),
            "picks_r1": r1[a].get("picks", []),
            "picks_final": picks[a],
        }

    out = {"pick_bonus": PICK_BONUS, "agents": agents_meta,
           "families": fam_rows, "candidates": list(candidates.values())}
    (data / "council.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    write_leaderboard(vault, out)
    write_dashboard_rows(data, out)
    print(f"{len(fam_rows)} families, {len(candidates)} candidates -> {data / 'council.json'}")


TAKE_FIELDS = [
    # A
    "components", "hard_core", "ai_necessity", "clone_time", "staging_risk", "feasibility_36h",
    # B
    "problem", "status_quo", "solution", "optimizes", "who", "frequency", "severity", "scale", "needed", "harm",
    # C
    "novelty", "venture", "win", "prior_art", "why_now", "buyer", "model", "usage", "wedge", "one_liner", "wow", "tracks",
]


def flat(v):
    if v is None:
        return ""
    if isinstance(v, list):
        return "; ".join(flat(x) for x in v)
    if isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False)
    return v


def write_dashboard_rows(data, out):
    """Flat row files for the Idea Council dashboard (one JSON array per dataset)."""
    dash = data / "dash"
    dash.mkdir(exist_ok=True)
    cands = {c["id"]: c for c in out["candidates"]}

    def sc(c, a):
        s = (c["scores"].get(a) or {}).get("score")
        return s if isinstance(s, (int, float)) else None

    def sub(c, a, k):
        return ((c["scores"].get(a) or {}).get("sub") or {}).get(k)

    def pick_text(p):
        if p is None:
            return ""
        return f"#{p['rank']}" + ("" if p["via_kind"] == "original" else f" via {cands[p['via']]['name']}")

    families = []
    for f in out["families"]:
        best, orig = cands[f["best"]], cands.get(f["key"])
        by = {p["agent"]: p for p in f["pickers"]}
        families.append({
            "key": f["key"], "rank": f["rank"], "name": f["name"], "kind": f["kind"], "pitch": f["pitch"],
            "angle": f["angle"], "sponsors": ", ".join(f["sponsors"]), "trap": "yes" if f["trap"] else "",
            "shortlisted": "yes" if f["shortlisted"] else "", "old_score": f["old_score"],
            "best_id": best["id"], "best_name": best["name"], "best_kind": best["kind"], "best_pitch": best["pitch"],
            "A": sc(best, "A"), "B": sc(best, "B"), "C": sc(best, "C"), "mean": best["mean"],
            "picks": len(f["pickers"]), "council": f["council"],
            "pick_A": pick_text(by.get("A")), "pick_B": pick_text(by.get("B")), "pick_C": pick_text(by.get("C")),
            "picked_by": ", ".join(p["agent"] for p in f["pickers"]),
            "orig_A": sc(orig, "A") if orig else None, "orig_B": sc(orig, "B") if orig else None,
            "orig_C": sc(orig, "C") if orig else None, "orig_mean": orig["mean"] if orig else None,
            "A_label": (best["scores"].get("A") or {}).get("label") or "",
            "B_label": (best["scores"].get("B") or {}).get("label") or "",
            "C_label": (best["scores"].get("C") or {}).get("label") or "",
            "feasibility": sub(best, "A", "feasibility_36h") or (sub(orig, "A", "feasibility_36h") if orig else None),
            "one_liner": sub(best, "C", "one_liner") or (sub(orig, "C", "one_liner") if orig else "") or "",
            "n_versions": len(f["versions"]),
            "verdict_A": ((orig or {}).get("scores", {}).get("A") or {}).get("verdict") or "",
            "verdict_B": ((orig or {}).get("scores", {}).get("B") or {}).get("verdict") or "",
            "verdict_C": ((orig or {}).get("scores", {}).get("C") or {}).get("verdict") or "",
        })

    versions, takes, evidence = [], [], []
    for c in out["candidates"]:
        versions.append({
            "cid": c["id"], "family": c["families"][0], "families": ", ".join(c["families"]),
            "kind": c["kind"], "name": c["name"], "pitch": c["pitch"] or "",
            "proposer": c["proposer"] or "", "parent": c["parent"] or "", "change": c["change"] or "",
            "why": c["why"] or "", "sponsors": ", ".join(c.get("sponsors") or []),
            "A": sc(c, "A"), "B": sc(c, "B"), "C": sc(c, "C"), "mean": c["mean"], "council": c["council"],
            "pickers": ", ".join(f"{p['agent']}#{p['rank']}" for p in c["pickers"]),
        })
        for a, s in c["scores"].items():
            row = {
                "key": f"{c['id']}|{a}", "cid": c["id"], "agent": a, "agent_name": AGENT_NAMES[a],
                "round": "r1" if (c["kind"] == "original" or c["proposer"] == a) else "r2",
                "score": s.get("score"), "label": s.get("label") or "", "verdict": s.get("verdict") or "",
                "take": s.get("take") or "", "reasoning": s.get("reasoning") or "",
                "red_flag": s.get("red_flag") or "",
            }
            subd = s.get("sub") or {}
            for k in TAKE_FIELDS:
                row[k] = flat(subd.get(k))
            takes.append(row)
            for i, e in enumerate(s.get("evidence") or []):
                url = (e or {}).get("url") or ""
                if url.startswith("https://") or url.startswith("http://"):
                    evidence.append({"eid": f"{c['id']}|{a}|{i}", "cid": c["id"], "agent": a,
                                     "title": (e.get("title") or url)[:200], "url": url})

    agents, picks = [], []
    for a, m in out["agents"].items():
        agents.append({"agent": a, "name": m["name"], "lens": m["lens"], "ceo_note": m["ceo_note"] or "",
                       "changed": m["changed"] or ""})
        for p in m["picks_final"]:
            c = cands[p["ref"]]
            picks.append({"pid": f"{a}|{p['rank']}", "agent": a, "rank": p["rank"], "cid": c["id"],
                          "name": c["name"], "kind": c["kind"], "family": c["families"][0], "why": p["why"] or ""})

    for name, rows in [("families", families), ("versions", versions), ("takes", takes),
                       ("evidence", evidence), ("agents", agents), ("picks", picks)]:
        (dash / f"{name}.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")


def fmt(x):
    return "–" if x is None else (f"{x:.1f}" if isinstance(x, float) else str(x))


def link(cand):
    return f"[[{cand['name']}]]" if cand["kind"] == "original" else f"**{cand['name']}** ({cand['id']})"


def write_leaderboard(vault, out):
    cands = {c["id"]: c for c in out["candidates"]}
    lines = [
        "---", "type: audit", "tags: [audit, council]", "---",
        "# Idea Council leaderboard", "",
        "Generated by `.claude/skills/idea-council/aggregate.py`. Do not edit by hand; rerun the council instead.",
        "",
        f"**Council score** = the average of the three lens scores for the idea's best version "
        f"(original or pivot) + {out['pick_bonus']:.0f} for each agent that picked any version. Max 13.",
        "",
        "| # | Idea | Council | Best version | Substance (A) | Impact (B) | Novelty & venture (C) | Picked by |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for f in out["families"]:
        best = cands[f["best"]]
        s = best["scores"]
        sc = [fmt((s.get(a) or {}).get("score")) for a in AGENTS]
        name = f"[[{f['name']}]]" if f["kind"] == "original" else f"**{f['name']}** (wildcard)"
        bv = "original" if best["kind"] == "original" else f"{best['name']} ({best['id']})"
        picked = ", ".join(
            f"{p['agent']}#{p['rank']}" + ("" if p["via_kind"] == "original" else f" via {p['via']}")
            for p in f["pickers"]) or "–"
        lines.append(f"| {f['rank']} | {name} | **{f['council']:.1f}** | {bv} | {sc[0]} | {sc[1]} | {sc[2]} | {picked} |")
    lines += ["", "## Pivots and wildcards", "",
              "| Id | Name | Of | Mean | A | B | C | Picked by | Pitch |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for c in sorted((c for c in out["candidates"] if c["kind"] != "original"),
                    key=lambda c: -(c["council"])):
        s = c["scores"]
        sc = [fmt((s.get(a) or {}).get("score")) for a in AGENTS]
        of = c["parent"] if c["kind"] == "pivot" else "wildcard"
        picked = ", ".join(f"{p['agent']}#{p['rank']}" for p in c["pickers"]) or "–"
        pitch = (c["pitch"] or "").replace("|", "/")
        lines.append(f"| {c['id']} | {c['name']} | {of} | {fmt(c['mean'])} | {sc[0]} | {sc[1]} | {sc[2]} | {picked} | {pitch} |")
    lines += ["", "Back to [[Council Verdict]] · [[Home]]", ""]
    (vault / "Idea Council" / "Leaderboard.md").write_text("\n".join(lines), encoding="utf-8")


CALLOUT_RE = re.compile(r"^> \[!abstract\] Idea Council.*\n(?:>.*\n)*\n?", re.M)


def cmd_notes(vault):
    """Write or refresh the Idea Council callout in every idea note."""
    out = json.loads((vault / "Idea Council" / "data" / "council.json").read_text(encoding="utf-8"))
    cands = {c["id"]: c for c in out["candidates"]}
    for f in out["families"]:
        path = vault / "Ideas" / f"{f['key']}.md"
        if not path.exists():
            continue
        best = cands[f["best"]]
        s = [fmt((best["scores"].get(a) or {}).get("score")) for a in AGENTS]
        picked = ", ".join(
            f"{p['agent']}#{p['rank']}" + ("" if p["via_kind"] == "original" else f" via {cands[p['via']]['name']}")
            for p in f["pickers"]) or "no agent"
        bv = "the original" if best["kind"] == "original" else f"pivot {best['name']}"
        block = (f"> [!abstract] Idea Council · #{f['rank']} of {len(out['families'])} · council {f['council']:.1f}\n"
                 f"> Substance {s[0]} · Impact {s[1]} · Novelty & venture {s[2]} (best version: {bv}). "
                 f"Picked by {picked}. See [[Council Verdict]].\n\n")
        text = path.read_text(encoding="utf-8")
        text = CALLOUT_RE.sub("", text)
        if "## Team notes" in text:
            text = text.replace("## Team notes", block + "## Team notes", 1)
        else:
            text = text.rstrip("\n") + "\n\n" + block
        path.write_text(text, encoding="utf-8")
    print(f"updated callouts in {len(out['families'])} notes")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("cross", "build", "notes"):
        sys.exit(__doc__)
    vault = Path(sys.argv[2])
    {"cross": cmd_cross, "build": cmd_build, "notes": cmd_notes}[sys.argv[1]](vault)
