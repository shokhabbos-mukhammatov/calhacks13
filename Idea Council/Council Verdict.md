---
type: audit
tags: [audit, council, index]
---
# Council verdict

Three independent agents reviewed all 37 ideas on Oct 22, 2026, each through one lens, with web research for evidence. They proposed 15 pivots, picked the ideas they would bet the weekend on, then scored each other's pivots in a second round.

- **A, The Skeptic**: substance. Is it a wrapper, an API mashup or a real system?
- **B, The Impact Analyst**: the problem, what it optimizes, how big the impact is, whether it is needed.
- **C, The Venture Scout**: novelty against prior art, startup potential (buyer, repeat use), and win potential.

**Council score** = the average of the three lens scores for an idea's best version (original or pivot) + 1 for each agent that picked any version of it. Max 13.

Interactive dashboard: https://claude.ai/artifact/CaHbViV7tNGC1XhKS79YFS · Full table: [[Leaderboard]] · Rerun: `/idea-council`

## Bottom line (updated Oct 23 with the posted prizes)
> [!tip] Challenger round (Oct 23)
> 40 new ideas were generated to beat the leaders, and the best six were scored by the same agents ([[Challenger Verdict]]). No standalone new idea beat Fire Drill. The top result is Fire Drill wrapped in a controls gate the judge can write rules for (council 10.0, against plain Fire Drill's 9.8). So build Fire Drill as a controls gate: one product with two judge moments. Netting House drops behind two new ideas.

1. **Build [[Fire Drill]]**, in the merged version described below, packaged as a controls gate ([[Challenger Verdict]]). The agents left [[Netting House]] (10.8) and Fire Drill (10.7) almost level, and they are the only ideas all three picked. The posted [[Prizes]] and our two-person schedule break the tie: see [[#Decision with the posted prizes]].
2. **Netting House is the fallback.** Switch only if Hyphenate's full track text at opening stresses treasury, cash or settlement.
3. **[[Two-Face]]** (9.4), in its reshaped form, only if we decide to chase Visa and Apify instead of Hyphenate ([[Two-Face Stress Test]]).
4. **24 of 37 ideas are safe to drop**: no agent picked them and all three passed.

| # | Idea | Council | Best version | A | B | C | Picked by |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | [[Netting House]] | **10.8** | original | 8 | 8.5 | 7.0 | A#2, B#1, C#2 |
| 2 | [[Fire Drill]] | **10.7** | Fire Drill: Proving Ground (A-P1) | 8 | 8 | 7.0 | A#1 (A-P1), B#2 (C-P1), C#1 (C-P1) |
| 3 | [[Two-Face]] | **9.4** | original | 6 | 6.5 | 6.7 | A#6 (B-P2), B#5 (A-P2), C#3 (C-P3) |
| 4 | [[Short the PR]] | 7.4 | Refactor Insurance (A-P3) | 7 | 6.5 | 5.7 | A#5 |
| 5 | [[Memory Blame]] | 7.2 | original | 7.5 | 6.5 | 4.7 | A#3 |
| 6 | [[Vault Heist]] | 6.6 | original | 7 | 5 | 4.7 | A#4 |
| 7 | [[Flytrap]] | 6.4 | Tripwire (B-P1) | 4.5 | 7.5 | 4.3 | B#3 |
| 8 | [[Intent Diff]] | 6.1 | original | 5 | 7 | 3.3 | B#4 |

## Decision with the posted prizes
Devpost posted 66 prizes on Oct 21 ([[Prizes]]). Anthropic, Annapurna Labs, SpacetimeDB and Supercell had not posted a prize yet. The council's scores above don't change; this section uses the prizes to break the tie.

| | [[Fire Drill]] (merged) | [[Netting House]] |
| --- | --- | --- |
| Main pot | [[Hyphenate]] "Autonomous Systems for Finance": $8K / $5K / $3K, the largest real cash on Devpost | Same pot |
| Fit with Hyphenate's track | Needs framing: present it as continuous controls testing. Verifying vendor bank-detail changes is a standard accounts-payable control that auditors test | Fits as written: finance operations run by agents |
| Other posted prizes where its sponsor tech does real work | [[Cartesia]] ($1,516), [[Armadin]] Best Security Hack ($996), [[Capital One]] Nessie as the payment rail ($1,200), [[Elastic]] for the trace ($1,200 / $1,436), [[CRS Credit API]] Identity / Fraud | [[Fetch.ai]] ($1,500 / $1,000 / $500); [[Coinbase]] x402 ($2,000) is a stretch for paying invoices |
| Two people until Saturday evening ([[Prep Plan]]) | The core loop runs on text (poisoned invoice → policy block); voice and the callback come last | 12 agents locking, voting and settling in 30 seconds on venue Wi-Fi: the most fragile demo on the list |
| What recent winners had ([[Recent Winners 2026]]) | The judge takes part (plays the CFO, answers the callback); proof by numbers (breach table) | A strong closing visual, but judges watch rather than take part |
| Teammates' stress test ([[Top Ideas Stress Test]]) | Pick, with changes (re-scored 7.3) | Backup (re-scored 6.7): "prior art does the math; the agents are thin" |

**Why Fire Drill.** Both ideas compete for the same main pot, so the main pot doesn't decide it. The secondary prizes, the two-person schedule and the judging pattern all favor Fire Drill. Netting House wins on one thing, a native fit with Hyphenate's track. That is why the switch condition is Hyphenate's full track text.

**Tracks to enter:** Hyphenate (primary), Cartesia and Armadin. Use Capital One Nessie as the payment rail. Add Anthropic if it posts a prize at opening. Enter Creao's "Best AI-First Disruptor" if any project can. Keep the rest off the pitch to avoid logo soup.

## Fire Drill: build the merge, not the original
All three agents picked Fire Drill, but none picked the original as written. They split over which fix to build:

| Version | A | B | C | Avg | Picked by | What it adds |
| --- | --- | --- | --- | --- | --- | --- |
| Original | 6.5 | 8 | 7.0 | 7.2 | none | |
| A-P1 "Proving Ground" | 8 | 8 | 7.0 | 7.7 | A#1 | A deterministic provenance policy at the tool boundary, plus a breach-versus-utility table on 200 held-out attacks |
| C-P1 "Fire Drill + Callback" | 6 | 8.5 | 7.7 | 7.4 | B#2, C#1 | A Callback API: a real outbound call to the vendor's verified number and a signed attestation the payment rail requires |
| B-P8 "Fire Drill + Callback" | 5.5 | 8.5 | 7.3 | 7.1 | none (B moved its vote to C-P1) | The same callback, sold to human AP desks too |

B and C reached the callback independently. A scores it low ("adds a buyer, not an engine"). C's final pick is the callback "using A-P1's provenance policy as the trigger". So the version that satisfies all three lenses is:

> **The policy engine decides, the callback verifies, the drill proves it.** A tool-boundary proxy tags every value by its source and blocks any bank change or payment whose payee details trace to untrusted text (a call transcript, an email, invoice text). A blocked request triggers a separate voice agent that phones the vendor on the number of record. Fire Drill's adaptive attacker tries to beat it, and the result is a breach-versus-utility table on held-out attacks. Demo: a judge plays the fake CFO, the old agent caves, the patched one triggers a call to a teammate's "vendor" phone at the table, the vendor denies the change, and the payment is blocked on screen.

This merged version is our synthesis; the agents scored its two halves separately.

Changes from [[Top Ideas Stress Test]] that fit the merge:
- **Make both outcomes of the judge's call a win.** A sensibly prompted Claude agent may not cave in 35 seconds. If it caves, show the turn where it broke. If it holds, say "now watch the attacker try 20 variants" and fast-forward the attacker against the same agent.
- **Measure beforehand.** On Saturday night, run the attacker against a grid (model tier × prompt hardening) and on held-out attacks, and show the breach-versus-utility table before and after the policy engine. That answers "you built the victim, so the breach is rigged".
- **Canary tools** from [[Flytrap]] (the same idea as Tripwire, B-P1): decoy tools like `export_vendor_master` and `disable_callback` that no legitimate task calls. Any call to one is a second detection signal.
- **Payment proof on Capital One Nessie** instead of the Visa sandbox, because Visa's prize is about shopping.
- **Two channels only:** the poisoned invoice first, then voice. Add email only if there is time.

Build order, with two people until Saturday evening:
1. **Fri night:** AP agent on a mock ledger with Nessie; poisoned-invoice attack; the policy engine at the tool boundary blocking it. Get the Cartesia Line number working (30 minutes) so voice is ready later.
2. **Sat day:** scorecard and trace UI (Elastic); the Claude-proposed policy rule plus the held-out re-run; canary tools.
3. **Sat evening, third teammate:** voice drill, the callback to the judge's phone, latency tuning. Overnight: run the breach grid.
4. **Sun:** freeze, record the video, rehearse both outcomes of the judge call. The pitch is now 3 minutes plus 2 minutes of questions.

Fixes the agents asked for:
- Drop "KnowBe4 for AI agents". KnowBe4 launched [Agent Risk Manager](https://www.knowbe4.com/press/knowbe4-secures-the-human-and-ai-workforce-with-agent-risk-manager) in April 2026, with adversarial simulation for agents.
- Don't use the name "Proving Ground". It is [Gray Swan's weekly arena](https://app.grayswan.ai/arena/challenge/proving-ground).
- Name the competitors first: Trustpair and Eftsure (callback-style bank verification for human AP), [Cekura](https://docs.cekura.ai/documentation/red-teaming/overview) and [Hamming](https://hamming.ai/blog/hamming-ai-seed-funding-to-make-voice-agents-more-reliable) (voice-agent red teaming), KnowBe4 ARM.
- Lead with the human-desk loss: about $3B of reported business-email-compromise losses in 2025 ([IC3 via McDonald Hopkins](https://www.mcdonaldhopkins.com/insights/news/the-sobering-truth-of-the-fbis-2025-internet-crime-complaint-center-report)). Finance judges will say they would never let an agent change bank details, so show it protects human desks too.
- Name Hamming too: its adaptive social-engineering calls against bank voice agents were shown at FinovateFall 2026. LA Hacks 2026 1st place went to security agents with a benchmark. Our difference: finance-specific, money actually moves, and the fix is a policy engine proven on held-out attacks.

## Netting House: the fallback, build as written, fix the story
Use this only if Hyphenate's track text tips the decision. [[Top Ideas Stress Test]] adds a hook and two fixes: on Sardex data, obligation clearing cut the cash a typical firm needed by about 25%; give the agents a real decision (an agent dispute court for contested invoices); and settle all net payments atomically from prefunded wallets, or none.

- **A (8, Real system):** "The most real system in the pool: a solver, invariants and a commit protocol move the money."
- **B (8.5, Urgent):** "The biggest, most frequent real-money problem in the pool, with a mechanism already proven at national scale."
- **C (7.0, New angle):** the strongest Fetch.ai fit and a network-effect business, but "cold start is the question every VC will ask".

All three named the same risk: one firm alone saves nothing, and the demo economy is synthetic. So:
- Put real set-off evidence on screen (Slovenia's national netting; [Cycles](https://cycles.money/blog/an-introduction-to-mtcs)) and credit Cycles.
- Name [Causa Prima](https://dealroom.co/news/134810-causa-prima-raises-10m-pre-seed-led-by-creandum-for-agent-to-agent-b2b-p/) ($10M pre-seed for agent-to-agent B2B payments). It does not net yet, but it could add set-off.
- Have an answer for "who joins first?": a dense cluster that already trades with each other (one supply chain, one marketplace, one co-op).

## Two-Face: the agents agree on the core, not on the product
| Version | A | B | C | Picked by |
| --- | --- | --- | --- | --- |
| Original | 6 | 6.5 | 6.7 | none |
| B-P2 Render-Parity Shield | 7 | 7 | 5.3 | A#6 |
| A-P2 Parity Proxy | 7 | 7 | 5.0 | B#5 |
| C-P3 Two-Face KYM (merchant check for agent-card issuers) | 6 | 6 | 7.3 | C#3 |

A and B want the defensive firewall: strip what only an agent would see before the model reads it. C says that is a feature browser-agent vendors will build in, and wants the paid merchant check instead. Pick the firewall if you go this way; it has two votes and needs no real cheating store to exist. The teammates' reshaped version in [[Two-Face Stress Test]] (compare what the human sees with what the agent reads, at the moment the agent is about to pay) is close to it and keeps the Visa and Apify prizes in play.

## Where the agents disagree
- [[Memory Blame]]: A 7.5 ("an engine of its own", pick) vs C 4.7 ("open-source tools already do provenance and rollback; a feature").
- [[Intent Diff]]: B 7 ("a daily, growing pain", pick) vs C 3.3 ("already exists"; CodeRabbit ships linked-issue validation).
- [[Vault Heist]]: A 7 (real system, pick) vs C 4.7: [Tensor Trust](https://proceedings.iclr.cc/paper_files/paper/2024/hash/519c51529c3544b3430bd8b17d400365-Abstract-Conference.html) is already a multiplayer vault game from Berkeley, and Gray Swan [launched a $300K agent-hacking arena](https://fortune.com/2026/10/20/exclusive-ai-security-company-gray-swan-red-team-arena-contest-to-jailbreak-ai-agents/) sponsored by Anthropic on Oct 20. The "multiplayer" line in [[Judge Verdict]] is no longer a difference.
- Tripwire (B-P1, a pivot of [[Flytrap]]): B 7.5 vs C 4.3 ([Agent Canary](https://mcpservers.org/servers/dorianchn/agent-canary) already exists).

## What each agent told the CEO
- **A, The Skeptic:** More than half the pool is sponsor APIs chained to a prompt. Whatever you build, the thing that decides the outcome (moves money, blocks a call, settles a coin) must be code you wrote and can verify, with Claude doing the reasoning around it.
- **B, The Impact Analyst:** Only two problems in the pool are documented, costly and frequent today: small-business late payment (Netting House) and payment-redirect fraud (Fire Drill). Most "agent economy" ideas solve problems that exist mainly inside the idea.
- **C, The Venture Scout:** Nothing here is a new category. Every good idea has funded neighbors, so win by owning a narrow angle and naming the competitor before the judge does.

## Safe to drop
No agent picked these, and all three passed on the original: [[Close Raid]], [[Zero-Trust Base Defense]], [[Phone-a-Human]], [[Dial-In MMO]], [[Frame-Data Exchange]], [[Backlog Tower Defense]], [[Coyote Time]], [[Scar Tissue]], [[Stump Market]], [[AgentFICO]], [[Kernel Bounties]], [[Kernel Golf]], [[Market-Maker NPCs]], [[Thinking Rows]], [[Street Injection Lens]], [[Waitlist Exchange]], [[Cal Hacks Futures]], [[Kernel Swarm]], [[Thrift Ticker]], [[Where Did I Put It]], [[The Pit]], [[Save States]], [[Jailbreak Booth]], [[IRL Speedrun Splits]].

Note: [[Backlog Tower Defense]], [[Close Raid]] and [[Flytrap]] were moved up in the earlier [[Judge Verdict]]; the council disagrees on all three.

## Files
- Raw agent output: `Idea Council/data/r1-*.json` (round 1), `r2-*.json` (cross-review), merged in `council.json`
- Agents: `.claude/agents/council-*.md`; rules and scoring: `.claude/skills/idea-council/`

Related: [[Leaderboard]] · [[Judge Verdict]] · [[Shortlist]] · [[Home]]
