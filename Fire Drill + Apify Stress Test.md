---
type: research
tags: [research, shortlist]
---
# Fire Drill + Apify stress test

Oct 23, before opening. Checks [[Fire Drill + Apify]] against Apify's docs, accounts-payable (AP) guidance on bank-change callbacks, prior art, Apify's pricing and our two-person schedule ([[Prep Plan]]).

## Verdict
**Keep Apify, but build half of it.** The Attack Feed is the best part of the plan: it fixes the load-bearing risk in [[Top Ideas Stress Test]] with data we didn't write. The rest is too wide for two people. It promises more trust than it can prove, and `vendor-verify` claims more than it checks.

Build the reshaped version in [[#Reshaped Apify plan]]: two Actors of ours instead of four, and roughly 5 hours instead of 9. Add a third Actor only once the core loop works. [[Fire Drill]]'s own re-score (7.3) doesn't change. The reshaped add-on is a realistic shot at a Best use place and at Best Actor without endangering the [[Hyphenate]] demo.

## Update: $200 of credit, beta access, and we grind
Later on Oct 23: the team has $200 on Apify plus beta access, and can create, publish and connect Actors. This is a plan to grind on, not a reason to cut. That changes two concerns below, and this section replaces [[#Reshaped Apify plan]]:
- **Cost (concern 5) is solved.** Even two Standby Actors kept warm all weekend (about $22–29) fit easily. Still set a max charge per run, so a looping drill can't burn the credit.
- **Scope (concern 1) becomes an order, not a cut.** Build all four Actors. The only rule: every piece has a fallback, so the demo never depends on something unfinished.

These still hold whatever the budget: commit-reveal (2), holding out a tactic family (3), an honest `vendor-verify` (4), Standby conversation state (5, now a design rule), logging the phone drill (6), the judge's number before the clock (7) and the video segment (8).

### Build order
1. **Fri night:** `attack-feed`. Hash the held-out split to GitHub the moment it finishes, before any patch.
2. **Fri night to Sat morning:** `fire-drill` with its built-in demo mode. Demo mode is both the fallback and the one-click Store run.
3. **Sat:** `ap-practice-target` as a Standby Actor. Make it stateless: every request carries the whole conversation, or state lives in a key-value store under a conversation ID. Never rely on a run's memory.
4. **Sat afternoon:** `vendor-verify` as a Standby MCP server, with onboarding evidence for the number on file and RDAP domain age. Keep OFAC out of the live demo; if built, log it as a compliance flag only.
5. **Sat night:** breach grid and schedules. Add the "Apify MCP" pack if time allows.
6. **Sun morning:** publish all four to the Store.

Fallbacks: demo mode if the practice target fails, the number on file if `vendor-verify` fails, and cached runs for everything shown on stage.

**Hacker Guide check (Oct 23):** Apify's text asks for "meaningful" use and an Actor built for this event, which the plan meets. CRS's sandbox offers business credit, state filings and its own OFAC check behind an MCP server, so `vendor-verify` calls CRS instead of our own OFAC match. The pitch is now **two minutes**, which makes concern 7 more pressing. Personal hotspots are banned, so fallbacks must be local recordings and caches.

## Concerns, worst first

### 1. Too wide for two people
- The plan adds four Actors, two of them Standby, plus Store publishing and about 9 hours of work. All of it lands on Fri night through Sat afternoon, when the core loop (AP agent, attacker, invoice channel, scoring, Nessie, patch and re-run) isn't done yet and Akmal hasn't arrived.
- Neither of us has shipped an Actor. Each `apify push` rebuilds the image on Apify, so debugging Standby and MCP in the cloud is slow.
- **Fix:** keep `fire-drill` and `attack-feed`. Drop `ap-practice-target`; see concern 5. `vendor-verify` waits until the core loop passes end to end. Develop locally with `apify run` and push only working code.

> Algorithms, formulas and architecture for every fix below are in [[Fire Drill + Apify Methods]].

### 2. "Trusted results" is a weak claim as written
- Append-only datasets and timestamped runs don't stop us from re-running until the numbers look good or deleting a dataset. We also write the attacker, the target and the scorer. One judge question sinks it: "Couldn't you just re-run until it passed?"
- **Fix: commit-reveal.** As soon as `attack-feed` finishes, hash the held-out split and commit the hash to GitHub, before Claude Code writes any patch. After the re-run, publish the split, so anyone can check the hash and GitHub's timestamp. Report every run, failures included, as counts ("beats 11 of 12"), not a best take. Combined with a Store listing anyone can run, that is verifiable. Append-only storage alone isn't.

### 3. Held out by source isn't the same as held out by tactic
- Public fraud reports repeat a handful of tactics: urgent bank change before close, new account after a "bank migration", the CEO is travelling. A split by source can put the same tactic on both sides, which tests wording, not whether the fix generalizes. 30–60 sources give about 12 held-out attacks, too few for percentages.
- **Fix:** hold out at least one whole tactic family that the patch never sees, and show counts.

### 4. `vendor-verify` checks less than it sounds like
- **It can't check what matters most.** Real bank-change validation confirms that the new account belongs to the vendor; Trustpair does this in 190+ countries through an API. We can't. Eftsure has also proposed an MCP server in Anthropic's own financial-services repo so agents can check verified accounts and recent bank changes (open issue, June 2026). So `vendor-verify` isn't new, and it's weaker than products that exist.
- **Against vendor email compromise, domain age doesn't help.** When the attacker sends from the vendor's real, old mailbox, the domain looks fine. Only the callback catches it.
- **OFAC adds little.** BEC money mules are rarely on the SDN list, and fuzzy name matching can throw a false positive on stage.
- **The callback standard is the number on file.** AP callback protocols say to call the number in your vendor record, or another separately verified source, and never the one in the request. Looking up a website at request time is a weaker variant. Protocols also hold payments until verification and second-person approval are done.
- **Fix:**
  - Position `vendor-verify` as onboarding evidence: it records where the number on file came from, plus domain age.
  - Drop OFAC.
  - Change the demo line to "calling Northwind at the number on file, verified from northwind-supply.com at onboarding".
  - Add two rubric items the patch must pass: "unreachable is not verified" (the attacker says the vendor's phone is down) and "a second person approves the change".
  - Pitch `vendor-verify` as plumbing, not as the product.

### 5. Standby costs and conversation state
- Platform usage is about $0.3–0.4 per GB-hour on the free plan (sources disagree), and the free plan gives $5 a month. Standby runs bill until their idle timeout ends, even with no traffic. Two 1 GB Standby Actors kept warm all weekend would cost about $22–29, four to six times the free credit.
- Standby scales by starting more runs, and runs don't share memory. A multi-turn drill against a Standby victim can land on a different run and lose the conversation.
- **Fix:** drop the `ap-practice-target` Standby Actor. Give `fire-drill` a built-in demo mode that runs the sandbox AP agent inside the same run, so a Store user still gets a report in one click, with no Standby and no state problem. Run `vendor-verify`, if built, at 256 MB with a short idle timeout, and warm it with one request before the pitch. Ask the Apify booth for credits.

### 6. The phone drill isn't an Actor run
- The moment judges remember, a judge on the phone with the agent, runs on Cartesia, not Apify. "Every drill runs on Apify" is false for it.
- **Fix:** write the call's transcript and scores into the same dataset afterwards. Say "text drills run on Apify, and the phone drill is logged there".

### 7. One more live step inside 3 minutes
- The judge typing their number into the vendor site at 0:00 adds a third live dependency (vendor site, then Apify, then Cartesia) to a pitch that already has a live phone call.
- **Fix:** take the judge's number during setup, before the clock starts, and run onboarding then. Keep a cached run from rehearsal.

### 8. Apify may judge from the video, not the pitch
- [[Prizes]]: sponsors can judge asynchronously from the demo video. Ten seconds of Apify in the live pitch won't carry Best use.
- **Fix:** give Apify a 45–60 second segment in the video: the run list, the commit-reveal hash, the Store page in one click. Add a README section linking the runs.

### 9. The prep window is today
- "Before Fri 4 PM" is about three hours from now. Doing the full tutorial row on top of the other prep won't happen.
- **Fix:** do one thing: scaffold from `python-mcp-empty`, push it and call it from Claude once. Skip the rest.

### 10. Smaller points
- Confirm in the first hour that `attack-feed`, with limited permissions, can run Website Content Crawler and read its dataset. The docs say limited-permission Actors can run other limited-permission Actors.
- Have `fire-drill` write to Elastic directly, with the API key as secret input, instead of routing an Apify webhook through Elastic auth.

## What holds up
- **Attack Feed** directly answers "what if the attacker rewords it?" with sources we didn't write.
- **No agent red-teaming Actor on the Store** that we could find, so Best Actor isn't crowded by direct competitors.
- **The Pluto Security write-up checks out:** published Aug 31, 2026; 8 of 8 trials; Apify closed it as a general prompt-injection problem. That makes the "Apify MCP" pack a strong, Apify-native stretch.
- **The callback is the standard control,** and the patch already enforces it.
- **Apify's own hackathon in September 2026** (BuildHer, with She Code Africa) required working Actors that can be published and monetized on the Store, not prototypes. Our Store listing with one priced event matches that. Its judging criteria weren't in the sources we found.
- **The Apify facts in the plan are correct:** MCP tools and `?tools=` selection, the Standby URL format, `python-mcp-empty`, `usesStandbyMode` and `webServerMcpPath`, pay-per-event, limited permissions, append-only datasets, and the x402 limits.

## Reshaped Apify plan
| Piece | As planned | Reshaped |
| --- | --- | --- |
| `fire-drill` | Actor plus a separate practice target | **Keep.** Add a built-in demo mode with the sandbox victim inside the run, plus the commit-reveal hash and per-run counts. |
| `attack-feed` | Own Actor, held out by source | **Keep.** Hold out a whole tactic family, and commit the hash before patching. |
| `vendor-verify` | Standby MCP: callback number, RDAP, OFAC | **Optional,** Sat afternoon, only if the core loop passes. Onboarding evidence plus RDAP; no OFAC. |
| `ap-practice-target` | Standby victim | **Drop**, replaced by demo mode |
| Schedules and webhooks | Nightly, webhook into Elastic | Keep the schedule; write to Elastic from inside the Actor |
| "Apify MCP" pack | Stretch | Stretch, unchanged |
| Time | ~9 h | ~5 h, plus ~2 h if `vendor-verify` is built |

## First hour (Fri 8–9 PM)
- [ ] `apify run` a `fire-drill` skeleton locally, then push it. The Anthropic key works as secret input.
- [ ] A limited-permission Actor runs Website Content Crawler and reads its dataset.
- [ ] Ask the Apify booth about credits and what "best use" means to them.
- [ ] Plan the commit-reveal step: hash the held-out split the moment `attack-feed` finishes.

## Sources
- Apify pricing (CU = 1 GB-hour; free plan $5/month): https://apify.com/pricing · https://docs.apify.com/account/subscriptions
- Standby billing, scaling and timeouts: https://docs.apify.com/platform/actors/running/standby
- Actor permissions: https://docs.apify.com/platform/actors/development/permissions
- Callback protocol for vendor bank changes (Stampli): https://www.stampli.com/resources/vendor-bank-change-callback-protocol/ · BEC payment diversion: https://www.stampli.com/resources/bec-payment-diversion-fraud/
- Vendor account takeover example (Ironscales): https://ironscales.com/threat-intelligence/vendor-ach-redirect-compromised-account-fabricated-urgency-mismatched-signatures
- Trustpair API (account ownership validation): https://trustpair.com/connect/api · Coupa partnership (Apr 2026): https://fintech.global/2026/04/28/coupa-expands-trustpair-tie-up-to-fight-vendor-fraud/
- Eftsure MCP proposal (open, Jun 2026): https://github.com/anthropics/financial-services/issues/265
- Pluto Security on Apify MCP (Aug 31, 2026): https://pluto.security/blog/apify-mcp-prompt-injection/
- Apify $1M Challenge: https://apify.com/challenge · BuildHer Hackathon 2026: https://www.startupresearcher.com/news/she-code-africa-and-apify-launch-buildher-hackathon-2026

Back to [[Home]] · [[Fire Drill + Apify]] · [[Fire Drill]] · [[Top Ideas Stress Test]]
