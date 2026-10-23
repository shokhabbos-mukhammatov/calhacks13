---
type: idea
cluster: "CFO office, made live"
score: 8.3
novelty: 8
buildable: 8
sponsor_fit: 9
shortlisted: true
trap: false
status: idea
tags: [idea, shortlist]
---
# Netting House

Small businesses' agents post open invoices. A netting engine finds circular debts and cancels them so only net amounts move; each company's agent approves, settlement runs through Visa, and every step is audited.

**Score 8.3** · novelty 8 · buildable in 36h 8 · sponsor fit 9
**Angle:** [[CFO office, made live]]
**Sponsors:** [[Hyphenate]], [[Visa]], [[Fetch.ai]], [[Anthropic]], [[Coinbase]], [[Creao AI]], [[Y Combinator]]

## Pitch line
A clearing house for small businesses. Agents post invoices, a solver cancels circular debt, and only the net amounts move.

## How it works
Each small business connects an accounting export (mock NetSuite or QuickBooks CSV, or PDFs) to its own Fetch.ai agent on Agentverse, which uses Claude to turn open receivables and payables into a standard obligation format and posts them privately to a clearing agent. An obligation enters the graph only when both sides agree: Claude matches A’s payable to B’s receivable and turns mismatches ($9,850 vs $9,800) into disputes instead of netting them. Owners write treasury policy in plain English (‘nothing with Delta until the pallet claim closes; anything over $25K needs me’) and Claude compiles it into typed solver constraints. A deterministic solver (an OR-Tools max-circulation LP, which returns whole cents) finds the largest set-off in which every company’s cleared inflow equals its outflow, then computes the few remaining net payments. Claude never picks a number that moves money. The clearing agent runs a two-phase commit: agents lock invoices and return signed approve or reject votes, a rejection triggers an instant re-solve, and large items escalate to the owner in ASI:One chat. On commit, each company gets a balanced set-off journal entry, the remaining amounts settle in USDC over x402 (or Visa if the sandbox comes through), and every step lands in a hash-chained audit log.

## The 2-minute demo
1. 0:00 Hook: a tile subcontractor is owed $61K by a contractor and owes $48K to a supplier, who is waiting on the contractor’s sister company. Everyone is solvent on paper and broke at the bank. Banks solved this with clearing houses; small businesses never got one.
2. 0:15 The graph: 12 businesses, each a Fetch agent on Agentverse, $412K of open invoices. Nobody sees anyone else’s books.
3. 0:35 Run Round: Claude flags two disputed invoices; 3-, 5- and 7-company cycles light up; the solver answers in about 200 ms.
4. 0:55 Votes tick in; one agent rejects because of its owner’s policy. The solver re-solves without that edge. ‘The math is an LP, not an LLM.’
5. 1:15 A $27K payment exceeds a CFO’s threshold. Hand the judge the phone with the ASI:One approval and Claude’s memo, including CRS credit context.
6. 1:35 Jaw-drop: the judge taps approve and 41 arrows collapse into 4. ‘$412,300 settled. $38,600 moved.’ USDC payments appear on the Base Sepolia explorer and each company’s balanced journal entry pops in.
7. 1:50 Close: Slovenia has run national multilateral set-off for decades. We make it continuous and agent-native, and charge basis points on cleared volume.

## Architecture
- Company agents (×12): Fetch.ai uAgents in one Bureau, registered on Agentverse, Chat Protocol for ASI:One, and a custom netting protocol (post, propose, lock, vote, commit, abort).
- Clearing agent: a Fetch.ai uAgent that coordinates reconciliation, solver calls and the two-phase commit, with 3 s timeouts and automatic re-solve.
- Solver: Python + Google OR-Tools max-circulation LP, then greedy net settlement. An invariant checker blocks any proposal that changes a net position or unbalances a journal.
- Claude layer (Agent SDK + MCP): invoice extraction, AP↔AR matching and disputes, policy-to-constraint compiler, escalation memos, plain-English explanations.
- Independent auditor: headless Claude Code re-derives every net position after each round and signs a report.
- Settlement: Coinbase CDP wallets + x402 USDC on Base Sepolia; a Visa Intelligent Commerce leg if sandbox access is granted; votes signed in the Trusted Agent Protocol style (RFC 9421).
- Credit: CRS business credit reports feed exposure limits and memos.
- Dashboard: Next.js + Convex live tables, a force-directed graph that animates cycles collapsing, an audit explorer, NetSuite-format journal export.

## How to qualify, per sponsor
| Sponsor | How |
| --- | --- |
| [[Fetch.ai]] | 13 agents on Agentverse with Chat Protocol; real multi-agent work (two-phase commit, a reject, a re-solve); approval live in ASI:One. |
| [[Hyphenate]] | Maps to their treasury, bank rec, GL and audit trail modules: the inter-company layer their per-company agents lack. Use their API if offered; otherwise export NetSuite journals. |
| [[Anthropic]] | Claude handles reconciliation, policy compilation and memos; a headless Claude Code auditor and test hooks show creative Claude Code use. |
| [[Coinbase]] | One CDP wallet per company; invoices become x402 URLs; net payments settle in USDC with explorer links. |
| [[Visa]] | Signed votes in the Trusted Agent Protocol style; a card-rail payment if the sandbox is granted. |
| [[CRS Credit API]] | Business credit drives exposure limits and escalation context. |
| [[Convex]] | Realtime source of truth for agents and dashboard. |
| [[Creao AI]] | If they repeat last year's tracks, enter Best Real-World Productivity Tool: the solver is exposed as an MCP tool and the dashboard is the designed web app. |
| YC / [[a16z]] | B2B fintech with network effects and a basis-points business model. |

## Load-bearing risk
The jaw-drop needs about 12 independent agents to lock, vote, re-solve and commit, plus on-chain settlement, within roughly 30 seconds on hackathon Wi-Fi. One stuck agent kills it, and a one-cent mismatch loses the finance judges.

**Mitigation:** Run all agents in one Bureau with local endpoints for the round; Agentverse registration is still used for discovery and ASI:One. Treat timeouts as a feature: abort and re-solve without the silent agent. Block any proposal that fails the invariant checker, prefund testnet wallets, and keep a labeled replay mode plus a recorded video by hour 31.

## 36-hour split
- P1, agents and rails (Python): uAgents, netting protocol, two-phase commit, CDP + x402, Visa-style signatures.
- P2, math and Claude (Python): synthetic economy, OR-Tools solver, invariants and property tests, Claude layer, CRS, auditor.
- P3, product and story (TS): Next.js + Convex dashboard, collapse animation, audit explorer, journal export, video, pitch.
- H0–2: shared data model and repo scaffold; ask Hyphenate and Visa about sandbox access at their booths.
- H2–10: agents registered early; solver + tests; graph renders seeded data; first integration.
- H10–22: two-phase commit and x402 payments; Claude extraction, matching and policy compiler; animation and audit log; ASI:One escalation.
- H22–29: 20+ full end-to-end rounds; fix flakiness; feature freeze at H29.
- H29–36: replay mode, video, README, 10+ pitch run-throughs, submit.

## Prep before Oct 23
- [ ] Fetch.ai: uAgents quickstart, Chat Protocol example and mailbox registration in a throwaway repo; note the payment-protocol message names.
- [ ] Coinbase CDP + x402 quickstart; testnet ETH and USDC from faucets.
- [ ] Request Visa and CRS sandbox access now; ask Hyphenate whether they will offer an API or sample data.
- [ ] Read: OR-Tools LP and min-cost-flow docs, set-off journal entries, Slovenia’s multilateral set-off system, Informal Systems’ Cycles protocol.
- [ ] Find one credible statistic on small-business late payments for the hook.

## Variations
- Catalyst loans: lenders bid to bridge a loop that is one link short, ranked by debt cleared per dollar lent.
- Intercompany netting for multi-entity companies, embedded inside Hyphenate.
- Construction pay-when-paid clearing with automatic lien waivers.
- US–Mexico supplier corridor: net across currencies, settle the rest in USDC.
- Agent dispute court: buyer and seller agents negotiate disputed invoices with evidence before each round.

## Why other teams won't build it
Most teams will build an agent that pays invoices. Netting needs a real optimization model, an all-or-nothing commit across independent agents, and a demo that balances to the cent in front of finance judges.

## Team notes
- Oct 23: see [[Top Ideas Stress Test]]. Backup for Hyphenate + Fetch.ai. Hook stat: obligation clearing cut a typical firm's cash needs ~25% (Sardex data). Have the net-settlement answer ready.
