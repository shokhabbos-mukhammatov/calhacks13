---
type: audit
idea: "Fire Drill"
verdict: "Keep as #1, with a sharper competitor answer and a noise-proof demo"
tags: [audit, shortlist]
---
# Judge audit: [[Fire Drill]]

> [!success] Verdict
> Still our strongest idea: the widest judge appeal of the four. Two things must change before it is judge-proof: a one-sentence answer to “isn’t this Hamming / Cekura / Coval?”, and a phone demo that survives a loud expo hall.

## Scorecard (1–5)
| Judge | Score | Why |
| --- | --- | --- |
| General | 5 | A judge phones the agent and talks it into wiring money: unforgettable, and the problem needs no explanation |
| [[Anthropic]] | 4 | Claude as attacker, victim and fixer; Claude Code writing patches at runtime; safety-positive framing |
| [[Hyphenate]] / finance | 4 | Vendor bank-change fraud is a top finance risk. Expect: “we’d never let an agent change bank details” |
| Security | 4 | Realistic business-email-compromise threat. Loses points instantly if the attacker looks scripted |
| VC | 3 | Crowded neighborhood: voice-agent testing platforms already sell red-teaming |
| [[Fetch.ai]] | 2 | No Fetch use unless we add it (see upgrades) |
| Data / evals | 3 | The drill library is a small labeled eval set |
| SpacetimeDB / Supercell, Quant | 1–2 | Not their track |

## Prior art judges may know
- **Voice-agent testing platforms**: [Hamming](https://hamming.ai/blog/hamming-vs-coval), [Cekura](https://www.cekura.ai/blogs/hamming-alternative) (a YC company, so YC judges may know it) and [Coval](https://www.coval.ai/blog/hamming-vs-cekura) all advertise red-teaming or jailbreak testing for voice agents. None of them describe social-engineering drills against agents that can move money, or automatic remediation.
- **Prompt-injection red-teaming tools** (Lakera, Promptfoo and similar) test prompts, not multi-turn, multi-channel pressure on an agent with payment tools.

**Our line:** “Testing platforms check whether your support bot sounds right. Fire Drill checks whether an agent with payment authority can be talked into moving money, finds the exact turn it gave in, patches it, and proves the patch holds on attacks it has never seen. It’s KnowBe4 for agents, not QA.”

## Killer questions and our answers
| Question | Answer |
| --- | --- |
| “Isn’t this Hamming, Cekura or Coval?” | The line above. They test conversation quality; we test authority under social engineering and close the loop with a verified fix. |
| “Did it fail because you made the victim dumb on purpose?” | Show its system prompt on screen: production-style, explicitly told to verify bank changes. Show breach rates across 2–3 model tiers. |
| “What if the attacker rewords it?” | The re-run is a held-out variant with a different channel, wording and amount. Show 3–5 variants passing after the patch. |
| “How do you score it? Another LLM?” | Ground truth from tool calls: did `approve_payment` fire to a changed account? The LLM only labels *why*. |
| “Is a synthetic CFO voice a deepfake tool?” | A synthetic persona, never a cloned real person. Drills only target agents you own, with consent and logs. |
| “Would anyone give an agent bank-change rights?” | AP automation already processes vendor changes with approval steps. The drill tests whether the agent routes to the human, and the fix often *removes* the permission. |

## Red flags at the table
- **Noise.** A phone call in a packed hall: speech-to-text mishears the judge and the agent looks broken for the wrong reason.
- **Network.** Telephony over venue Wi-Fi (Cal Hacks 12 had Wi-Fi problems).
- **Looks scripted.** If the attack works on the first line every time, security judges assume it’s rigged.
- **Overfit patch.** A patch that just bans the word “urgent” is the fastest way to lose the security judges.

## Upgrades that make it judge-proof
1. Give the judge a headset, or use Cartesia’s browser call instead of the PSTN line. Keep a typed-chat fallback for the same drill.
2. Show a small table: breach rate before/after across 3 model tiers and 5 held-out variants. One table answers three questions.
3. Make the patch visibly structural: a tool-permission diff (remove `change_vendor_bank_details`, add `request_human_approval`), not a prompt tweak.
4. Use one realistic artifact: an invoice PDF with hidden text that the agent obeys. Judges remember props.
5. **Fetch bolt-on:** register Fire Drill on Agentverse so any agent owner can request a drill over the chat protocol. That earns a Fetch track entry without changing the core.
6. Bring a phone hotspot and run the agents locally.

Related: [[Judge Panel]] · [[Judge Verdict]] · [[Shortlist]]
