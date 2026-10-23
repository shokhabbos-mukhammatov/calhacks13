---
type: audit
idea: "Vault Heist"
verdict: "Best crowd demo and best Tier 1 game fit; win depends on turnout and balance"
tags: [audit, shortlist]
---
# Judge audit: [[Vault Heist]]

> [!warning] Verdict
> The most fun at the table, and the strongest fit for [[SpacetimeDB]] and [[Supercell]]. It has the most moving parts that can fail live: real players have to show up, and guards have to be breakable but not trivial. Expect the prior-art question in the first minute.

## Scorecard (1–5)
| Judge | Score | Why |
| --- | --- | --- |
| [[SpacetimeDB]] / [[Supercell]] | 5 | Money settles only in reducers, scheduled reducers spawn customers, players author the NPCs: their own pitch, built |
| General | 5 | Judges play on their phones. Nothing beats being inside the demo |
| [[Anthropic]] | 4 | Claude in four roles plus a safety-relevant benchmark. Will ask whether it’s a jailbreak farm |
| Data / evals | 4 | Ground-truth outcomes and novelty-weighted data. Will ask about size and label quality |
| Security | 3 | Realistic for agents with tool access, but “game” framing lowers the stakes |
| VC | 3 | Fun is not a business; the dataset or the B2B “agent wallet range” is |
| Finance, Quant, Fetch | 1–2 | Not their track |

## Prior art judges may know
- **[Freysa](https://www.theblock.co/post/328659/players-are-trying-to-convince-this-ai-to-hand-over-her-40000-crypto-stash)**: one AI guarding a crypto prize pool, talked out of ~$47K in 2024, with several later rounds.
- **Gandalf** (Lakera) and **Tensor Trust** (a Berkeley research game, so Berkeley judges may know it): single-player or single-shot prompt-injection games.
- **Real-world hook:** a reported May 2026 incident where one agent treated another agent’s decoded output as a command and moved funds ([write-up](https://www.zealynx.io/research/adversarial-security/indirect-prompt-injection)). Single source, so phrase it carefully.

**Our line:** “Freysa was one guard and one prize. Gandalf and Tensor Trust are single-player. Here every player writes a guard that must still serve real customers, thousands of attacks hit tool-using agents in real time, and every breach becomes a labeled exploit with its fix attached.”

## Killer questions and our answers
| Question | Answer |
| --- | --- |
| “Isn’t this Gandalf / Freysa / Tensor Trust?” | The line above. |
| “Can’t a guard just refuse everyone?” | Scheduled customers who know the side door, a go-live test, and an “Exposed” penalty for over-refusing. |
| “Is this collecting jailbreaks?” | Only authorization exploits (getting coins moved). Content is moderated to PG and nothing harmful is rewarded. The data is for agent authorization defenses. |
| “How big is the dataset, really?” | Show the live count, and keep bot self-play data in a separate, clearly marked split. |
| “Why SpacetimeDB and not Postgres + websockets?” | Atomic settlement, scheduled reducers, private tables and subscriptions in one module. Show how little server code exists. |
| “Is it fun after five minutes?” | Patch your guard, come back to see who robbed you, climb the board. Show repeat-play numbers from the weekend. |

## Red flags at the table
- **Nobody played.** An empty feed kills the story. Turnout needs a launch plan.
- **Guards too strong.** Judges fail in their 40 seconds and feel dumb.
- **Rate limits.** Hundreds of concurrent Claude calls can hit API limits on Saturday night.
- **Cost surprise.** Track spend live.

## Upgrades that make it judge-proof
1. Launch publicly by hour 18: QR posters at food lines, a post in the event Slack, a live player counter on the big screen.
2. Tune the demo vault so first-timers breach in 3 messages about 40% of the time; keep a hint card and a voiced best-heist replay as backup.
3. Ask Anthropic’s booth about hackathon rate limits early; default guards to a Haiku-class model with prompt caching.
4. Have a prior-art slide ready for the Q&A.
5. For the VC judge, pitch the B2B version: companies upload their wallet-holding agent and the crowd attacks it for bounties.

Related: [[Judge Panel]] · [[Judge Verdict]] · [[Shortlist]]
