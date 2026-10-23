---
type: audit
idea: "Netting House"
verdict: "Highest ceiling with finance, Fetch.ai and quant judges; credit Cycles and make it relatable"
tags: [audit, shortlist]
---
# Judge audit: [[Netting House]]

> [!success] Verdict
> The most rigorous idea and the best fit for two big tracks ([[Hyphenate]] and [[Fetch.ai]]), plus quant judges. Its risk is that general judges find it abstract. Lead with one person’s story and one number, and name Cycles before a judge does.

## Scorecard (1–5)
| Judge | Score | Why |
| --- | --- | --- |
| [[Fetch.ai]] | 5 | 13 agents with a real protocol, a reject and re-solve, and approval in ASI:One: the deepest Fetch use of any idea |
| [[Hyphenate]] / finance | 5 | Treasury, intercompany, journals, audit trail: their exact world. Must tie out to the cent |
| Quant | 5 | A max-circulation LP with integral cents and invariant checks is the rigor they recruit for |
| General | 4 | The debt-graph collapse is a great visual, but “multilateral set-off” loses people in 10 seconds |
| VC | 4 | Real pain (late payments) and a basis-points model. Expect the cold-start / network-effect question |
| [[Anthropic]] | 3 | Claude does reconciliation, policy and memos, but the hero is the solver. Lean on the Claude Code auditor |
| Security, Data, Games | 1–2 | Not their track |

## Prior art judges may know
- **[Cycles](https://cycles.money/blog/an-introduction-to-mtcs)** (Informal Systems) is building exactly this clearing network, with [papers in 2025–2026](https://arxiv.org/pdf/2507.22309). Slovenia has run national multilateral set-off for years.
- **CCP netting** (clearing houses for banks) is the classic version.

**Our line:** “The math is known: Cycles and Slovenia proved it works. What’s missing is participation: small firms won’t join a clearing network by hand. We make each firm’s agent do the joining: reconcile, apply the owner’s rules, vote, and settle.”

## Killer questions and our answers
| Question | Answer |
| --- | --- |
| “Isn’t this Cycles?” | The line above. Credit them openly; it makes us look informed, not derivative. |
| “Do strangers’ invoices really form cycles?” | In dense clusters (construction, food distribution) yes, and Slovenia’s system shows it at national scale. Our demo cluster is synthetic and we say so. |
| “Where does the AI touch the money?” | Nowhere. An LP plus invariant checks set every amount, and an independent Claude Code auditor re-derives every number. |
| “Why an LP instead of finding cycles one by one?” | Greedy cycle-cancelling is suboptimal. Max-circulation is optimal, and because the incidence matrix is totally unimodular, the answer is in whole cents. |
| “Are these real agents or functions in one process?” | Each has its own identity, protocol handler and Agentverse registration. Prove it: run two company agents on a teammate’s laptop during the demo. |
| “What if a firm disputes after settlement?” | Disputed invoices are excluded *before* netting; every commit carries a signed vote; set-off runs under a master agreement. |
| “What if someone goes bankrupt mid-round?” | Two-phase commit: nothing settles until every affected agent commits. |

## Red flags at the table
- **Abstraction.** If the first sentence contains “multilateral”, general judges tune out.
- **One cent off.** A finance judge who spots a journal that doesn’t balance stops listening.
- **12 agents in one process** can look fake to Fetch judges.
- **Synthetic data** invites “does this happen in reality?”

## Upgrades that make it judge-proof
1. Open with the tile subcontractor story and end on one number: “$412K settled, $38K moved.”
2. Put an always-visible invariant panel on screen: net positions unchanged ✔, journals balance ✔, whole cents ✔.
3. Run 2 of the 12 agents on a second laptop so agent independence is visible.
4. Add a “why this is real” slide with the Cycles and Slovenia references.
5. Have a one-page set-off journal printout for the finance judge.

Related: [[Judge Panel]] · [[Judge Verdict]] · [[Shortlist]]
