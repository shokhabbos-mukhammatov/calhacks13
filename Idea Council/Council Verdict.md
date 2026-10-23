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

## Bottom line
1. **Two ideas, almost level.** [[Netting House]] (10.8) and [[Fire Drill]] (10.7) are the only ideas all three agents picked. The next idea scores 9.4 and the rest score 7.4 or less. Stop debating the pool; choose between these two on Friday once the tracks are out.
2. **Fire Drill**, if the big tracks are Anthropic, security, Cartesia or Hyphenate. Build the merged version (below), not the original.
3. **Netting House**, if the big tracks are Fetch.ai, Hyphenate or fintech (Visa, Coinbase, CRS). Build it as written; fix the cold-start story.
4. **[[Two-Face]]** is the backup (9.4): every agent picked a version of it, but each a different one, and none beats the leaders.
5. **24 of 37 ideas are safe to drop**: no agent picked them and all three passed.

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

Fixes the agents asked for:
- Drop "KnowBe4 for AI agents". KnowBe4 launched [Agent Risk Manager](https://www.knowbe4.com/press/knowbe4-secures-the-human-and-ai-workforce-with-agent-risk-manager) in April 2026, with adversarial simulation for agents.
- Don't use the name "Proving Ground". It is [Gray Swan's weekly arena](https://app.grayswan.ai/arena/challenge/proving-ground).
- Name the competitors first: Trustpair and Eftsure (callback-style bank verification for human AP), [Cekura](https://docs.cekura.ai/documentation/red-teaming/overview) and [Hamming](https://hamming.ai/blog/hamming-ai-seed-funding-to-make-voice-agents-more-reliable) (voice-agent red teaming), KnowBe4 ARM.
- Lead with the human-desk loss: about $3B of reported business-email-compromise losses in 2025 ([IC3 via McDonald Hopkins](https://www.mcdonaldhopkins.com/insights/news/the-sobering-truth-of-the-fbis-2025-internet-crime-complaint-center-report)). Finance judges will say they would never let an agent change bank details, so show it protects human desks too.

## Netting House: build as written, fix the story
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

A and B want the defensive firewall: strip what only an agent would see before the model reads it. C says that is a feature browser-agent vendors will build in, and wants the paid merchant check instead. Pick the firewall if you go this way; it has two votes and needs no real cheating store to exist.

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
