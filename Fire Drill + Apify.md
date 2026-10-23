---
type: plan
tags: [plan, shortlist]
---
# Fire Drill + Apify

Oct 23, before opening. Can [[Apify]] make [[Fire Drill]] more trusted, prove its results with data, and win Apify's prizes, without changing the plan in [[Top Ideas Stress Test]]? Yes, if Apify does real work and isn't a wrapper added at the end.

## Verdict
Give Apify three jobs. Each one fixes a weakness the stress test already found:

| # | Apify job | What it fixes | Cost (rough) |
| --- | --- | --- | --- |
| 1 | **Drill runner as an Actor.** Every drill, the overnight breach grid and the held-out re-runs run as Apify Actor runs, on a schedule. | "Who built the villain?" Judges can open timestamped runs, and the results live in append-only datasets. The "on a schedule" line in the pitch becomes true. | ~3 h Sat. Mostly wrapping code we write anyway. |
| 2 | **Attack Feed.** Crawl public fraud reports and turn them into held-out attacks. | The load-bearing risk: the patch only beats the wording it was written against. | ~2 h Fri night, then it runs in the background. |
| 3 | **Independent verification in the patch.** The callback number, sender-domain age and sanctions check come from the public web through Apify, never from the request itself. | Turns the patch into the AP control auditors test, and makes the AP agent useful (stress test fix 3). | ~2 h Sat. |

Prizes this adds: **Best use of Apify** (5 places, $4,600) and **Best Actor** ($400). The plan loses nothing: Elastic still holds the turn-by-turn trace, Cartesia the voice and Nessie the money.

If we fall behind, cut 3 first. The callback then uses the number on file, as originally planned. Keep 1 and 2: together they are "Apify finds the attacks and runs the drills", and the breach grid has to run somewhere anyway.

## 1. Drill runner as an Actor
The drill runner (attacker vs. victim, plus the rubric scorer) becomes a Python Actor, `fire-drill`.
- **Input schema:** target agent endpoint (HTTP or MCP URL), the agent's written policy, attack packs, number of held-out variants, max spend. The target's API key goes in as secret input. Teams can bring their own attacks by passing a dataset ID. Limited-permission Actors may read storages passed in through input.
- **Output:** one dataset row per drill: tactic, channel, source report, the turn where the agent broke, rubric scores, money moved and canary tools touched. `REPORT.html` in the key-value store is the audit evidence for [[Hyphenate]].
- **Regression suite:** every regression test that Claude Code writes joins the attack packs. Each scheduled run replays all of them, so a fix that later breaks shows up red the next morning. This is "prove the patch holds" over time, not just once on stage.
- **Schedules and webhooks:** an Apify schedule runs it nightly. A webhook on each finished run pushes the rows into Elastic and the scorecard.
- **Breach grid:** Saturday night's grid (model tier × prompt hardening, stress test fix 1) is a batch of these runs. On stage the scorecard links to them.
- **Store listing (Best Actor):** publish Sunday morning with a README and a sample report. Add input and output schemas, keep limited permissions, and price one pay-per-event event, `drill-completed`. Limited permissions are the default. Full-permission Actors need manual approval and rank lower.
- **Agents can call it:** once it's on Store, any agent connected to the Apify MCP server can start it with `call-actor`. A Claude user can say "fire-drill my AP agent".

Two catches:
- The Actor runs in Apify's cloud, so the victim agent needs a public URL. Easiest: run the sandbox victim as a **Standby Actor** (an Actor that serves HTTP at `https://<name>.apify.actor/...`). It doubles as a public practice target. Fallback: a cloudflared tunnel.
- The free plan gives $5 of platform credit a month. LLM calls bill to our Anthropic key, not Apify, but Store Actors charge per result. Ask the Apify booth for credits on Friday.

## 2. Attack Feed: held-out attacks from real reports
We write the attacker and its variants, so a passing re-run proves little on its own. Fix:
- **Fri night:** Apify crawls public write-ups of vendor bank-change fraud and of prompt injection against agents. Sources: FBI IC3 and CISA advisories, security vendors' BEC write-ups, and r/Scams posts where people paste the email they received. Use Google Search Results Scraper to find pages, Website Content Crawler to read them and Reddit Scraper Lite for posts.
- **Tactic cards:** Claude turns each source into a card with pretext, channel, pressure lever, the ask and the source URL. Cards keep no names, emails or phone numbers.
- **Split by source before patching.** Claude Code writes the patch against the training split only. The re-run uses the held-out split.
- **Demo line:** "The re-run uses 12 attacks distilled from real fraud reports. We never saw them while writing the patch." Every card links to its source.
- **[[Armadin]] angle:** the attacker learns from attacks in the wild.

Keep it small: 30–60 sources is enough. Run the crawl during the hackathon, not before, because all work must be done during the event.

## 3. Independent verification in the patch
The patch already requires an out-of-band callback for any bank change. The next question from an auditor is where the callback number came from: a number taken from the request is what the attacker counts on. So the patch adds one tool, `verify_vendor_independently`, backed by Apify:
- **Callback number:** read from the vendor's official website, using the domain in the vendor master and never the one in the request. Contact Details Scraper does this in bulk at vendor onboarding, and RAG Web Browser does a single page in about 15–30 s. Google Maps Scraper is a second source.
- **Sender-domain age** (invoice and email channel): a WHOIS Actor on the domain the request came from. A lookalike registered yesterday is a strong BEC signal.
- **Sanctions:** an OFAC screening Actor on the new beneficiary's name. This also ties in [[CRS Credit API]]'s Identity/Fraud prize.
- Each check returns evidence with its Apify run link, and the drill report records it.

At the planned "judge's phone rings" moment, the patched agent says: "Bank change for Northwind requested from northwind-supp1y.com, registered 14 hours ago. Calling Northwind at the number on northwind-supply.com, not the one in the request." Then the judge's phone rings.

To make that true rather than staged:
- The fictional vendor gets a real one-page site with a contact page. At 0:00 the vendor judge types their number into it, and we say so out loud. Onboarding verification starts right then, so the 15–30 s lookup is done long before the callback at ~1:40.
- Register the lookalike domain Friday night, so its age really is hours. Only make lookalikes of our fictional vendor.
- Keep a cached run from rehearsal as the fallback if Apify or Wi-Fi is slow.

## Stretch, only if ahead
- **Web channel:** the victim's `lookup_vendor` reads vendor sites through Apify's `rag-web-browser`, and the attacker plants hidden instructions on a page (our own). It tests "tool output is untrusted" on the most common way agents read the web. The Apify MCP server hands agents this same tool, so the pitch to Apify becomes "Fire Drill tells you whether your agent is safe to give web tools". It is a third channel, though, and the stress test said build two.
- **x402:** Apify lets agents pay for pay-per-event Actors with USDC on Base over x402, with no account. An agent could pay per drill, which is a possible hook for [[Coinbase]]. Apify calls this experimental, and Standby Actors aren't supported.

## Don't
- Don't move the trace from Elastic to Apify storage. Elastic has its own prize, and Agent Builder answers "show me the turn where it broke".
- Don't scrape real people or companies to personalize attacks. Real BEC works that way, but it breaks our defensive framing. Target only our own fictional company and vendors.
- Don't call phone numbers scraped from real businesses. Demo vendors are fictional and their sites are ours.
- Don't put any Apify call on the live demo's critical path without a cached fallback.

## Where it fits in the two-person plan
| When | Add |
| --- | --- |
| Before Fri 4 PM (accounts and tutorials only) | Apify account. Connect `mcp.apify.com` to Claude. In a throwaway repo, run Website Content Crawler, a WHOIS Actor and `rag-web-browser` once, then `apify create` a Python Actor and push it once. Delete the repo afterwards. |
| Fri night | Start the Attack Feed crawl; it runs while we build the victim. Register the lookalike domain and put up the vendor site. |
| Sat day | Wrap the drill runner as the `fire-drill` Actor, with a webhook into Elastic. Add `verify_vendor_independently` to the patch. |
| Sat night | Breach grid and held-out re-runs as Actor runs. |
| Sun morning | Publish to Store with README and schemas. Link the runs from the Devpost write-up and the scorecard. |

## What each prize sees
| Prize | What they see |
| --- | --- |
| Apify Best use (1st–5th) | Apify does three real jobs: it finds the attacks, verifies the vendor, and runs and schedules the drills. |
| Apify Best Actor | A published Actor with schemas, limited permissions, one priced event and a README with a sample report. Apify's own Actor criteria are real-world usefulness, quality and technical excellence. |
| [[Hyphenate]] | The callback number comes from an independent source, and the report records it. That is the control auditors test. |
| [[Armadin]] | Real attacks feed the attacker, and the held-out attacks come from real reports. |
| [[CRS Credit API]] | Vendor identity and sanctions check before money moves. |
| Cal Hacks judging | Application (a real control), Technical complexity (held-out split, regression suite) and Functionality (runs anyone can open). |

## At opening
- [ ] Read Apify's full prize text on Devpost; it blocked our fetcher. If it asks for a Store Actor or the MCP server specifically, re-order the three jobs.
- [ ] Visit the Apify booth Friday: ask for credits and what "best use" means to them.

## Sources
- Apify MCP server (tools, `?tools=` selection, auth): https://docs.apify.com/platform/integrations/mcp
- Standby mode (HTTP endpoints, MCP over Standby): https://docs.apify.com/platform/actors/running/standby
- Datasets are append-only: https://docs.apify.com/platform/storage/dataset
- Pay-per-event: https://docs.apify.com/platform/actors/publishing/monetize/pay-per-event
- Actor permissions: https://docs.apify.com/platform/actors/development/permissions
- Secret input: https://docs.apify.com/platform/actors/development/actor-definition/input-schema/secret-input
- Schedules: https://docs.apify.com/platform/schedules · Webhooks: https://docs.apify.com/platform/integrations/webhooks
- x402 on Apify: https://docs.apify.com/platform/integrations/x402
- Store Actors: [Website Content Crawler](https://apify.com/apify/website-content-crawler) · [Google Search Results Scraper](https://apify.com/apify/google-search-scraper) · [RAG Web Browser](https://apify.com/apify/rag-web-browser) · [Reddit Scraper Lite](https://apify.com/trudax/reddit-scraper-lite) · [Contact Details Scraper](https://apify.com/vdrmota/contact-info-scraper) · [Google Maps Scraper](https://apify.com/compass/crawler-google-places) · [WHOIS Domain Lookup](https://apify.com/confidential_gnat/whois-com) · [OFAC Sanctions Scraper](https://apify.com/opendata-labs/ofac-sanctions-scraper) (community Actors vary; test them Friday)
- Apify $1M Challenge criteria: https://apify.com/challenge

Back to [[Home]] · [[Fire Drill]] · [[Apify]] · [[Top Ideas Stress Test]]
