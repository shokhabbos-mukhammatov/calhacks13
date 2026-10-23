---
type: audit
tags: [audit, judges]
---
# Judge panel

Who will look at our project, what each of them rewards, and the question each one asks to find the weak spot. Built from the Cal Hacks 12 judging format, last year's sponsor criteria, and each sponsor's business.

## How judging works (Cal Hacks 12 format)
- Table-side expo: **2-minute pitch + 2-minute Q&A** per judge group. Judges see 15–30 tables in a session, so the first 20 seconds decide whether they lean in.
- General criteria: **Application, Functionality/Quality, Creativity, Technical Complexity**.
- Sponsor judges visit separately for their own tracks and check that their tech is used for real, not as a logo.
- Required: GitHub repo, image, table number, a locally stored demo video. Judges can and do open the commit history.
- Judges must have finished undergrad, so expect working engineers, founders, investors and domain experts, not students.

## The panel

| Judge | Who they are | What earns points | What loses points | The question they will ask |
| --- | --- | --- | --- | --- |
| **General judge** | Volunteer engineer or alum, tired, many tables | A live moment in the first 20 s; it works; clear real-world use | Slides before demo; broken flows; jargon | “Show me it working. What happens if I do X?” |
| **[[Anthropic]]** | Applied AI engineer | Claude doing hard reasoning; creative Claude Code use; safety awareness | Thin wrappers; Claude used only as a chatbot | “What does Claude do here that a regex or a script couldn’t?” |
| **[[Fetch.ai]]** | DevRel / chief AI officer (CH12 judges were their CDO and CAIO) | Agents registered on Agentverse, chat protocol, real agent-to-agent messaging, ASI:One discoverable | One agent wrapping an LLM; agents that are just functions | “Show me these agents talking. Are they discoverable on Agentverse?” |
| **[[Hyphenate]]** / finance | Controller or finance-ops engineer | Accounting that is correct to the cent; audit trail; human escalation; ERP realism | Numbers that don’t tie out; AI moving money unchecked | “Would a controller sign off on this? Where is the audit trail?” |
| **Security** ([[Armadin]], [[Illumio]]) | Offensive security / detection engineer | A realistic threat model; measurable results; defense that generalizes | Toy prompt-injection demos; scripted attacks; overclaiming | “Is the attacker adaptive or scripted? How do you know the fix isn’t overfit?” |
| **[[SpacetimeDB]] / [[Supercell]]** | Engine engineer / game designer | Reducers and subscriptions doing real work; a fun loop; retention | A CRUD app on a game skin; DB used as a key-value store | “Why does this need SpacetimeDB? Is it fun after five minutes?” |
| **VC** ([[Y Combinator]], [[a16z]], [[Llama Ventures]], [[The House Fund]]) | Partner or associate | Why now, a clear buyer, a wedge, awareness of competitors | “No one does this” when someone does; no buyer | “Who else does this, and who pays?” |
| **Quant** ([[Jane Street]], [[Citadel]], [[D. E. Shaw]]) | Engineer who recruits | Rigor, correctness, real numbers, edge cases | Hand-waving; unmeasured claims | “What’s the worst case? How did you verify it?” |
| **Data / evals** ([[Scale]], [[Afterquery]]) | Data and eval researchers | Ground-truth labels, dedup, quality checks, honest dataset size | Noisy crowd data presented as gold | “How do you know the labels are right? How big is it really?” |

## What every judge checks
1. **Does it work live?** A working demo beats a better idea on slides.
2. **Was it built here?** Commit early and often during the event. A first commit at hour 30 with 5,000 lines invites questions.
3. **Is the sponsor tech load-bearing?** Sponsor judges reward depth in their tool, not a list of logos.
4. **Has this been done?** Name the closest prior art yourself before they do, then say what is new.

Back to [[Judge Verdict]] · [[Home]]
