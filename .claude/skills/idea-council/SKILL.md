---
name: idea-council
description: Run the CEO's three-agent Idea Council over every note in Ideas/ - The Skeptic (wrapper or real system?), The Impact Analyst (problem, impact, is it needed?) and The Venture Scout (novelty, startup and win potential) - with pivots, picks, a cross-review round, a council leaderboard and the Idea Council dashboard. Use on /idea-council, or when asked to re-score, re-rank or re-evaluate the hackathon ideas.
---

# Idea Council

Three independent agents review every idea in `Ideas/`, propose pivots, pick the ideas they would bet the weekend on, then cross-review each other's pivots. The aggregator turns that into one council score per idea:

> **Council score** = average of the three lens scores for the idea's best version (original or pivot) + 1 for each agent that picked any version of it. Max 13.

Files:
- Agents: `.claude/agents/council-skeptic.md` (A), `council-impact.md` (B), `council-venture.md` (C)
- Shared rules and JSON shapes: `protocol.md` (this folder)
- Aggregator: `aggregate.py` (this folder)
- Outputs: `Idea Council/data/` (raw rounds, `council.json`, `dash/*.json`), `Idea Council/Leaderboard.md` (generated), `Idea Council/Council Verdict.md` (written by you)
- Dashboard: https://claude.ai/artifact/CaHbViV7tNGC1XhKS79YFS

## Steps

1. **Round 1, in parallel.** Launch three background agents at once. If the `council-*` agent types are available use them; otherwise use `general-purpose` and tell each to read its definition file. Each writes `Idea Council/data/r1-<A|B|C>.json` and must not read the others' files. Move any older `r1-*`/`r2-*` files into `Idea Council/data/archive/<date>/` first.
2. **Round 2.** When all three are done, run
   `python .claude/skills/idea-council/aggregate.py cross "<vault>"`
   and send each agent (SendMessage, continuing the same agent) only its own block: the other two agents' pivots and wildcards. Each writes `r2-<agent>.json` per `protocol.md`.
3. **Build.** `python .claude/skills/idea-council/aggregate.py build "<vault>"`. Read the warnings it prints (unknown idea names or refs) and fix the JSON if needed. Then `aggregate.py notes "<vault>"` refreshes the council callout in every idea note (safe to rerun).
4. **Synthesize.** Read `council.json` and write `Idea Council/Council Verdict.md`: the decision, the top ideas with each agent's take, the strongest pivots, where the agents disagree, and what to drop. Also write `Idea Council/data/dash/memo.json` (rows `{id, heading, text}`, 3–5 rows, plain words, no numbers that aren't in the data).
5. **Dashboard.** Upload every file in `Idea Council/data/dash/` as an asset of the dashboard, then update each `datasets/<id>` document's `source.url`, `source.name` and `updated` (dataset ids: `families`, `versions`, `takes`, `evidence`, `agents`, `picks`, `memo`). Read the dashboard's `check` document afterwards.
6. Link the verdict from `Home.md` if it isn't already.

## Rules
- The agents' scores are theirs; never edit them. If something is wrong, rerun that agent.
- Existing frontmatter scores in idea notes are a previous brainstorm's opinion. Leave them as they are.
