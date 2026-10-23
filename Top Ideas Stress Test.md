---
type: research
tags: [research, shortlist]
---
# Top ideas stress test

Oct 23, before opening. Applies the [[Two-Face Stress Test]] checks to every idea scored 7.6 or higher:
- Is the threat or problem real outside our own demo?
- Has someone already built it?
- Can two people build it before Akmal arrives?
- Is there a posted prize behind each sponsor?

## Verdict
**Pick [[Fire Drill]], with the changes below.** It is the only top idea that passes all four checks:
- The threat is real and expensive.
- Nobody has published this exact product.
- The biggest posted pot ([[Hyphenate]], $16K) fits it.
- The core loop works without voice, so it survives two people until Saturday evening.

Backups, depending on what's announced at opening:
- **Two-Face, reshaped** ([[Two-Face Stress Test]]): if we want Visa + Apify instead of Hyphenate.
- **[[Netting House]]**: if Hyphenate's full track text leans toward treasury, cash or settlement, and the team would rather build math than voice.
- **[[Vault Heist]]**: only if SpacetimeDB and Supercell post real prizes at opening.

## Re-scored
| Idea | Vault | Re-score | Biggest problem | Call |
| --- | --- | --- | --- | --- |
| [[Fire Drill]] | 8.0 | **7.3** | We build the victim, so the breach can look rigged | **Pick, with changes** |
| [[Two-Face]] (reshaped) | 8.0 | 7.0 | Smaller pots than Hyphenate | Backup for Visa + Apify |
| [[Netting House]] | 8.3 | 6.7 | Prior art does the math; the agents are thin | Backup for Hyphenate + Fetch.ai |
| [[Close Raid]] | 7.6 | 6.3 | A game skin on what Hyphenate already sells | Drop |
| [[Phone-a-Human]] | 7.6 | 6.3 | HumanLayer and RentAHuman exist | Drop; reuse its phone moment in Fire Drill |
| [[Flytrap]] | 7.6 | 6.0 | Almost no hostile AI agents in the wild to catch | Drop; reuse its canary tools in Fire Drill |
| [[Death Heatmap]] | 7.6 | 6.0 | Inspector was a finalist and won Hacker's Choice at these organizers' spring hackathon | Drop |
| [[Two-Face]] (as written) | 8.0 | 6.0 | See [[Two-Face Stress Test]] | Drop |
| [[Vault Heist]] | 7.8 | 5.7 | Tensor Trust is Berkeley's own bank-vault prompt game | Only if game prizes are posted |
| [[Stump Market]] | 8.0 | 5.7 | Humanity's Last Exam (Scale) already did it | Drop |
| [[Zero-Trust Base Defense]] | 7.6 | 5.7 | No posted prize behind it; heaviest build | Drop |

Re-scores are rough. Like the vault, they average three numbers: novelty, buildable with two people until Saturday evening, and fit with *posted* prizes. The reasons below matter more than the decimals.

## Problems every idea shares
1. **Two people until about H22.** Akmal arrives around 6:30 PM Saturday ([[Prep Plan]]). Every shortlisted 36-hour split runs three tracks from H2. Prefer ideas whose core loop two people can finish, with the third person's part added on top.
2. **Unposted prizes.** As of Oct 21 these had no prize on Devpost: Anthropic, SpacetimeDB, Supercell, Bright Data, Afterquery, Scale, Illumio, Listen Labs, Decagon, Wajo and YC. Ideas built mainly on them are bets on opening-day announcements. Posted money: Hyphenate $16K, Creao $15K real cash, Visa $5K, Apify $5K, Figma $5K, Fetch.ai $3K, Coinbase $2K, then smaller.
3. **Who built the villain?** When we build both the attacker and the victim, or both the cheat and the detector, judges see a staged demo. Fix it the same way every time: let the judge supply the attack, and show numbers measured beforehand.
4. **Berkeley judges know Berkeley prior art.** Tensor Trust is from Berkeley. Inspector placed at the Berkeley AI Hackathon this spring. Name prior art in the first sentence and say what's different.

## Fire Drill (8.0 → 7.3): pick it, with changes
**What holds up**
- The threat is real and expensive. Business email compromise caused about $3.05B in reported US losses in 2025, the second-largest category, including $30M+ with a confirmed AI link (IC3 2025, as reported). In 2024 Arup lost about $25M to a deepfake video call impersonating its CFO.
- Posted prizes: Hyphenate $16K, Cartesia, Armadin, CRS Identity/Fraud, Capital One Nessie and Elastic.
- It degrades gracefully. The poisoned-invoice attack loop runs on text, so voice can come last.

**Concerns and fixes**
1. **The breach can look rigged.** We write the AP agent's prompt, so we decide whether it falls. Current models resist simple attacks: in a LangWatch test, single-turn attacks got nothing from a banking agent, and it took a 50-turn adaptive attack to leak parts of its system prompt by turn 20. A sensibly prompted Claude agent probably won't fold to a judge in 35 seconds, and an obviously weak one looks like a strawman.
   **Fix: make both outcomes a win, and measure beforehand.** On Saturday night, run the autonomous attacker against a grid (model tier × prompt hardening) and show the breach rates. On stage the judge tries first. If the agent caves, show the turn where it broke. If it holds, say "now watch the attacker try 20 variants" and fast-forward the attacker against the same agent.
2. **Red-teaming agents isn't new.** Hamming AI (FinovateFall 2026) already places hundreds of adaptive social-engineering calls against bank voice agents. LA Hacks 2026 1st place went to security agents with a benchmark, and Armadin will draw other security teams. **Our difference:** finance-specific, ends in money actually moving, and closes the loop with a patch and a held-out re-run. Say that in the pitch.
3. **Hyphenate may read it as a security project.** Their prize is "Autonomous Systems for Finance". **Frame it as continuous controls testing.** Independently verifying changes to vendor bank details is a standard accounts-payable control that auditors test. Fire Drill tests that control when an agent runs AP and outputs the audit evidence. Make the AP agent genuinely useful too.
4. **Too many channels.** The note lists voice, email, invoice and ticket. Build two: the poisoned invoice (text, Friday night) and the voice call (when Akmal arrives). Add email only if there's time.
5. **The runtime Claude Code patch is slow on stage.** Let it stream while we talk, and cache the diff in case it stalls.

**Pull in from the dropped ideas**
- **Canary tools** (from [[Flytrap]]): give the AP agent decoy tools no legitimate task uses, such as `export_vendor_master` and `disable_callback`. Any call to one is a tripwire. It's cheap to build and gives a second detection signal.
- **The judge's phone rings** (from [[Phone-a-Human]]): the patch adds an out-of-band callback for bank changes, so make the callback real. After the patch, the agent phones the "real vendor", which is a judge's phone, to verify the change. The judge says they never asked for it, and the payment is blocked. That's a second live moment on the same Cartesia setup.
- **Payment proof on [[Capital One]] Nessie** (posted $1.2K) instead of the Visa sandbox, since Visa's prize is about shopping ([[Shortlist]] already suggests this).

**Two-person plan**
- **Fri night:** AP agent on a mock ledger with Nessie; attacker with the poisoned-invoice channel; scoring rubric. Spend 30 minutes getting the Cartesia Line number working, so voice is ready for later.
- **Sat day:** scorecard and trace UI, patch plus held-out re-run, canary tools, Elastic trace.
- **Sat evening (Akmal):** voice drill, callback to the judge, latency tuning. Overnight: run the breach grid.
- **Sun:** freeze, record the video, rehearse both outcomes of the judge call.

## Netting House (8.3 → 6.7): backup for Hyphenate + Fetch.ai
**What holds up**
- A real problem with a real number, which the vault was missing. On Sardex network data (3,199 firms, 138K transactions), obligation clearing alone cut the cash a typical firm needed to settle invoices by about 25%, and about 50% when combined with mutual credit (Fleischman et al., 2020). Use it as the hook.
- Finance-credible: a deterministic solver, an invariant checker and balanced journal entries.
- The arrows collapsing and "$412K settled, $38K moved" make a strong closing visual.

**Concerns**
1. **Prior art does the math, and the agents are thin.** Slovenia's state clearing system, Informal Systems' Cycles and the Sardex study already exist, so our novelty is the agents. As designed, though, they are 12 processes in one Bureau voting by rules, and Fetch.ai judges may see one program playing 13 parts. **Fix:** give the agents a real decision. Build the "agent dispute court" variation, where two agents negotiate a disputed invoice with evidence before the round.
2. **Claude plays a supporting role** (extraction, matching, compiling policy). That's right for finance judges but weak for an AI hackathon. Show owners the compiled policy for confirmation, because it shapes which debts get cleared.
3. **Finance judges will ask about net settlement.** Cancelling cycles only removes debts everyone already owes. Paying the remaining *net* amounts means some firms pay companies they never invoiced, and everyone depends on everyone else paying. **Answer to have ready:** all net payments settle atomically from prefunded wallets, or none do.
4. **Who joins first?** Slovenia's system works because the state runs it for every company, while 12 strangers is a cold start. **Wedge:** a construction project, where the contractor, subs and suppliers already owe each other in a loop (the note's pay-when-paid variation).
5. **The graph is ours.** "41 arrows into 4" comes from an economy we designed. Generate it from Sardex-like statistics and say so.
6. **Sponsor drift.** Visa's prize is about shopping, so it's out. Paying invoices over x402 is a stretch that Coinbase judges may or may not accept.
7. **The most fragile demo on the list:** 12 agents locking, voting and settling on-chain in 30 seconds on venue Wi-Fi.

## Vault Heist (7.8 → 5.7): only if game prizes are posted at opening
- **Tensor Trust** (UC Berkeley, ICLR 2024) is a bank where players protect accounts with LLM prompts and others attack them; it released 563K attacks and 118K defenses. Our differences are real: a guard that calls a transfer tool, legitimate customers it must still serve, multiple turns and a live economy. They have to come first in the pitch, or it reads as a reskin.
- **The data claim is weak.** A weekend's few hundred attempts won't matter to Scale or Afterquery next to Tensor Trust's 563K.
- **Its main targets** (SpacetimeDB, Supercell, Scale, Afterquery) had no posted prizes on Oct 21.
- It needs attendees to play during a hackathon and organizer permission, and the public feed needs moderation.
- **Keep it if** SpacetimeDB and Supercell announce real prizes. It's then also the strongest Hacker's Choice and Most Creative entry on the list.

## The rest, briefly
- **[[Stump Market]] → drop.** Humanity's Last Exam (Scale AI and CAIS) collected 70K questions from about 1,000 experts, kept those that stumped frontier models, and paid from a $500K pool (up to $5K a question). Scale is one of our target sponsors, and this was their project. Its incentive is also backwards: audits found about 29% of HLE's chemistry and biology answers wrong or misleading (FutureHouse), and 22 of 48 sampled questions had substantial errors (Epoch). Paying per model stumped pays for wrong questions.
- **[[Close Raid]] → drop.** The core (Claude proposes matches, accountants approve) is bank reconciliation Hyphenate already sells. The raid skin may read as unserious to finance judges, and it came up in two research branches, so other teams will think of it too. Its game sponsors haven't posted prizes.
- **[[Flytrap]] → drop, keep the canary tools.** Palisade Research's LLM honeypot logged 8.1M attempts over about three months and found 8 possible AI agents. We would be the only attacker in our own demo. Illumio has no posted prize.
- **[[Zero-Trust Base Defense]] → drop.** There's no real network to load at a hackathon, and nobody will upload theirs. Illumio and Supercell have no posted prizes, and Armadin's ~$1K is the only one. It's the heaviest build on the list.
- **[[Phone-a-Human]] → drop, keep the phone moment.** HumanLayer (YC Fall 2024) already lets agents contact humans for help and approvals. RentAHuman.ai (Feb 2026) lets agents hire humans over MCP and pay in stablecoins, and reports say far more humans signed up than agents posted jobs. Afterquery has no posted prize.
- **[[Death Heatmap]] → drop.** Inspector ("agents that QA your app by using it") was a finalist and won Hacker's Choice at the Berkeley AI Hackathon this spring ([[Recent Winners 2026]]). Synthetic-user products exist (Brox.ai, Synthetic Users), LLM personas are weak stand-ins for real people, and computer-use swarms are slow live. Consider it only as a Figma play (5 × $1K).

## At opening (Fri 4 PM)
- [ ] Read Hyphenate's full track text. If it stresses treasury or settlement, re-weigh Netting House.
- [ ] Check whether Anthropic, SpacetimeDB, Supercell and Bright Data post prizes. That decides Vault Heist and the Two-Face crawler.
- [ ] Check Creao's "Best AI-First Disruptor" rules. If any project can enter, enter whatever we build ($3K / $1.5K / $500 cash).
- [ ] Decide within 90 minutes ([[Prep Plan]]).

## Sources
- FBI IC3 2025 BEC figures, as reported: https://www.nacha.org/news/fbis-ic3-finds-almost-85-billion-lost-business-email-compromise-last-three-years · https://redsift.com/de/blog/fbi-ic3-2025-report-email-fraud
- Hamming AI red team (FinovateFall 2026): https://finovate.com/videos/finovatefall-2026-hamming-ai/
- LangWatch on multi-turn red teaming: https://langwatch.ai/blog/why-ai-red-teaming-is-broken-(and-how-we-fixed-it)
- Fleischman et al., "Liquidity-Saving through Obligation-Clearing and Mutual Credit" (2020): https://wiki.p2pfoundation.net/Liquidity-Saving_through_Obligation-Clearing_and_Mutual_Credit
- Tensor Trust (ICLR 2024): https://arxiv.org/pdf/2311.01011
- Humanity's Last Exam: https://www.scale.com/blog/humanitys-last-exam · FutureHouse audit: https://the-decoder.com/nearly-29-percent-of-humanitys-last-exam-questions-are-wrong-or-misleading/ · Epoch review: https://epoch.ai/benchmarks/hle/review
- Palisade Research LLM Agent Honeypot: https://arxiv.org/html/2410.13919v1
- HumanLayer: https://humanlayer.dev · RentAHuman: https://decrypt.co/356784
- Synthetic-user tools: https://aimultiple.com/synthetic-users

Back to [[Home]] · [[Shortlist]] · [[Two-Face Stress Test]]
