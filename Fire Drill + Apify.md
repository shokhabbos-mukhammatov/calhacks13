---
type: plan
tags: [plan, shortlist]
---
# Fire Drill + Apify

Oct 23, before opening. Can [[Apify]] make [[Fire Drill]] more trusted, prove its results with data, and win Apify's prizes, without changing the plan in [[Top Ideas Stress Test]]? Yes, if Apify does real work and isn't a wrapper added at the end.

**Stress-tested Oct 23:** see [[Fire Drill + Apify Stress Test]]. With $200 of Apify credit, follow its build order: all four Actors, each with a fallback, commit-reveal for the held-out attacks, and OFAC kept out of the live demo. Where the two notes differ, the stress test wins. The algorithms, formulas and architecture are in [[Fire Drill + Apify Methods]].

## Verdict
Give Apify three jobs. Each one fixes a weakness the stress test already found:

| # | Apify job | What it fixes | Cost (rough) |
| --- | --- | --- | --- |
| 1 | **Drill runner as an Actor.** Every drill, the overnight breach grid and the held-out re-runs run as Apify Actor runs, on a schedule. | "Who built the villain?" Judges can open timestamped runs, and the results live in append-only datasets. The "on a schedule" line in the pitch becomes true. | ~4 h Sat, including the practice target. Mostly wrapping code we write anyway. |
| 2 | **Attack Feed.** Our `attack-feed` Actor crawls public fraud reports and turns them into held-out attacks. | The load-bearing risk: the patch only beats the wording it was written against. | ~2 h Fri night, then it runs in the background. |
| 3 | **Independent verification in the patch.** Our `vendor-verify` Actor gets the callback number, sender-domain age and sanctions hits from independent sources, never from the request itself. | Turns the patch into the AP control auditors test, and makes the AP agent useful (stress test fix 3). | ~3 h Sat. |

Prizes this adds: **Best use of Apify** (5 places, $4,600) and **Best Actor** ($400). The plan loses nothing: Elastic still holds the turn-by-turn trace, Cartesia the voice and Nessie the money.

Where the Store has nothing good, we build the Actor ourselves: see [[#Our own Actors]].

If we fall behind, cut 3 first. The callback then uses the number on file, as originally planned. Keep 1 and 2: together they are "Apify finds the attacks and runs the drills", and the breach grid has to run somewhere anyway.

## Our own Actors
Checked Oct 23: the Store has no Actor that red-teams AI agents and none that checks a vendor bank-change request. It has several community WHOIS and OFAC scrapers, but most have no ratings yet, and we can't have one of them fail on stage. So we build four Actors and reuse two of Apify's.

| Actor | On the Store today | Decision |
| --- | --- | --- |
| `fire-drill`: runs drills against an agent and writes the report | Nothing that red-teams agents | **Build** (job 1) |
| `attack-feed`: turns public fraud reports into tactic cards | Nothing | **Build** a thin one (job 2). It calls Apify's Google Search Results Scraper and Website Content Crawler, then Claude writes the cards. |
| `vendor-verify`: callback number, domain age and sanctions check in one call | Separate community WHOIS and OFAC Actors, mostly unrated. Nothing for bank-change checks. | **Build** (job 3) as a Standby Actor with an MCP endpoint |
| `ap-practice-target`: the sandbox AP agent at a public URL | Nothing | **Build** as a Standby Actor. It is `fire-drill`'s default target, so anyone can press Start on the Store page and get a report with no setup. |
| Website Content Crawler, Google Search Results Scraper, RAG Web Browser | Maintained by Apify | **Reuse** |

Why build instead of chaining community Actors:
- **Speed on stage.** A Standby Actor is already running, so `vendor-verify` answers in seconds. A batch Actor run, or RAG Web Browser at 15–30 s, doesn't.
- **The patched agent gets it as a tool.** Apify serves a Standby Actor's MCP endpoint at `https://<user>--vendor-verify.apify.actor/mcp`. The Claude Agent SDK victim connects to it like any MCP server.
- **Primary sources.** Domain age comes from RDAP: free, structured JSON, no scraping. Sanctions come from Treasury's own OFAC SDN CSV. Both worked when tested Oct 23.
- **More for Apify's judges.** Four Actors of ours and two of theirs, chained together and published.

Cost: about 1 h more than calling Store Actors, mostly `vendor-verify`. Scaffold the Standby Actors with `apify create <name> --template python-mcp-empty` (FastMCP and uvicorn). Set `usesStandbyMode: true` and `webServerMcpPath: "/mcp"` in `.actor/actor.json`, and define priced events in `.actor/pay_per_event.json`.

## 1. Drill runner as an Actor
The drill runner (attacker vs. victim, plus the rubric scorer) becomes a Python Actor, `fire-drill`.
- **Input schema:** target agent endpoint (HTTP or MCP URL), the agent's written policy, attack packs, number of held-out variants, max spend. The target's API key goes in as secret input. Teams can bring their own attacks by passing a dataset ID. Limited-permission Actors may read storages passed in through input.
- **Output:** one dataset row per drill: tactic, channel, source report, the turn where the agent broke, rubric scores, money moved and canary tools touched. `REPORT.html` in the key-value store is the audit evidence for [[Hyphenate]].
- **Regression suite:** every regression test that Claude Code writes joins the attack packs. Each scheduled run replays all of them, so a fix that later breaks shows up red the next morning. This is "prove the patch holds" over time, not just once on stage.
- **Schedules and webhooks:** an Apify schedule runs it nightly. A webhook on each finished run pushes the rows into Elastic and the scorecard.
- **Breach grid:** Saturday night's grid (model tier × prompt hardening, stress test fix 1) is a batch of these runs. On stage the scorecard links to them.
- **Store listing (Best Actor):** publish Sunday morning with a README and a sample report. Add input and output schemas, keep limited permissions, and price one pay-per-event event, `drill-completed`. Limited permissions are the default. Full-permission Actors need manual approval and rank lower. The default input drills `ap-practice-target`, so the listing works in one click.
- **Agents can call it:** once it's on Store, any agent connected to the Apify MCP server can start it with `call-actor`. A Claude user can say "fire-drill my AP agent".

Two catches:
- The Actor runs in Apify's cloud, so the victim agent needs a public URL. Easiest: run the sandbox victim as a **Standby Actor**, `ap-practice-target`, which serves HTTP at `https://<user>--ap-practice-target.apify.actor/...`. It doubles as a public practice target. Fallback: a cloudflared tunnel.
- The free plan gives $5 of platform credit a month. LLM calls bill to our Anthropic key, not Apify, but Store Actors charge per result. Ask the Apify booth for credits on Friday.

## 2. Attack Feed: held-out attacks from real reports
We write the attacker and its variants, so a passing re-run proves little on its own. Fix:
- **Fri night:** our `attack-feed` Actor crawls public write-ups of vendor bank-change fraud and of prompt injection against agents. Sources: FBI IC3 and CISA advisories, security vendors' BEC write-ups, Pluto Security's write-up on Apify MCP (see [[#Stretch, only if ahead]]), and r/Scams posts where people paste the email they received. It calls Google Search Results Scraper to find pages, Website Content Crawler to read them and Reddit Scraper Lite for posts.
- **Tactic cards:** Claude, inside the Actor, turns each source into a card with pretext, channel, pressure lever, the ask and the source URL. Cards keep no names, emails or phone numbers. They go to the Actor's dataset, which `fire-drill` takes as an attack pack.
- **Split by source before patching.** Claude Code writes the patch against the training split only. The re-run uses the held-out split.
- **Demo line:** "The re-run uses 12 attacks distilled from real fraud reports. We never saw them while writing the patch." Every card links to its source.
- **[[Armadin]] angle:** the attacker learns from attacks in the wild.

Keep it small: 30–60 sources is enough. Run the crawl during the hackathon, not before, because all work must be done during the event.

## 3. Independent verification in the patch
The patch already requires an out-of-band callback for any bank change. The next question from an auditor is where the callback number came from: a number taken from the request is what the attacker counts on. So the patch adds one tool, `verify_vendor_independently`, served over MCP by our own `vendor-verify` Standby Actor:
- **Callback number:** Crawlee reads the contact page of the vendor's official website, using the domain in the vendor master and never the one in the request. The number comes from schema.org `telephone` markup, or from the page text if there is none. Google Maps Scraper is an optional second source.
- **Sender-domain age** (invoice and email channel): an RDAP lookup on the domain the request came from. A lookalike registered yesterday is a strong BEC signal.
- **Business identity and sanctions (updated Oct 23):** call the [[CRS Credit API]] sandbox through its MCP server, using business credit, state filings and CRS's OFAC check, instead of our own OFAC match. It targets CRS's "Best Financial AI Agent" prize ($500). Run it at onboarding and keep it off the live demo's critical path.
- Each check returns its evidence: the source URL, a timestamp and the matched text. The drill report records it.
- It is useful outside Fire Drill too, so publish it. Any AP team or agent can call it before changing bank details.

At the planned "judge's phone rings" moment, the patched agent says: "Bank change for Northwind requested from northwind-supp1y.com, registered 14 hours ago. Calling Northwind at the number on northwind-supply.com, not the one in the request." Then the judge's phone rings.

To make that true rather than staged:
- The fictional vendor gets a real one-page site with a contact page. At 0:00 the vendor judge types their number into it, and we say so out loud. Onboarding verification starts right then, so it is done long before the callback at ~1:40.
- Register the lookalike domain Friday night, so its age really is hours. Only make lookalikes of our fictional vendor.
- Keep a cached run from rehearsal as the fallback if Apify or Wi-Fi is slow.

## Stretch, only if ahead
- **"Apify MCP" attack pack (first stretch; the threat is now documented).** On Aug 31, 2026, Pluto Security published an attack on Apify's own MCP server. A page fetched with `rag-web-browser` steered the agent into fetching a URL the user never gave, in 8 of 8 trials. Apify closed the report as a general prompt-injection problem and pointed builders to constrained environments and approving tool calls. Fire Drill checks exactly that:
  - The victim's `lookup_vendor` reads vendor sites through `rag-web-browser`, and the payload sits on our own page.
  - The rubric fails any fetch of a URL that came from page content rather than the user, which is Pluto's provenance check.
  - It reuses the poisoned-invoice plumbing, since both deliver injected text through a tool's output. That makes it cheaper than a new channel.
  - Pitch it to Apify as help, not a gotcha: "Apify told builders to fence their agents in. Fire Drill proves you did." Credit Pluto by name.
- **x402:** Apify lets agents pay for pay-per-event Actors with USDC on Base over x402, with no account. An agent could pay per drill, which is a possible hook for [[Coinbase]]. Apify calls this experimental, and Standby Actors aren't supported.

## Don't
- Don't move the trace from Elastic to Apify storage. Elastic has its own prize, and Agent Builder answers "show me the turn where it broke".
- Don't scrape real people or companies to personalize attacks. Real BEC works that way, but it breaks our defensive framing. Target only our own fictional company and vendors.
- Don't call phone numbers scraped from real businesses. Demo vendors are fictional and their sites are ours.
- Don't put any Apify call on the live demo's critical path without a cached fallback.

## Where it fits in the two-person plan
| When | Add |
| --- | --- |
| Before Fri 4 PM (accounts and tutorials only) | Apify account. Connect `mcp.apify.com` to Claude. In a throwaway repo, run Website Content Crawler and `rag-web-browser` once. Then scaffold a Standby Actor from `python-mcp-empty`, push it and call its `/mcp` endpoint from Claude once. Delete the repo afterwards. |
| Fri night | Build `attack-feed` and start it; it runs while we build the victim. Register the lookalike domain and put up the vendor site. |
| Sat day | Deploy the victim as `ap-practice-target`. Wrap the drill runner as the `fire-drill` Actor, with a webhook into Elastic. Build `vendor-verify` and connect the patched agent to it over MCP. |
| Sat night | Breach grid and held-out re-runs as Actor runs. |
| Sun morning | Publish all four to Store with READMEs and schemas. Link the runs from the Devpost write-up and the scorecard. |

## What each prize sees
| Prize | What they see |
| --- | --- |
| Apify Best use (1st–5th) | Apify does three real jobs: it finds the attacks, verifies the vendor, and runs and schedules the drills. Four Actors of ours and two of Apify's work as one system. |
| Apify Best Actor | Lead with `fire-drill`: schemas, limited permissions, one priced event, a README with a sample report, and a default input that drills our practice target in one click. Name `vendor-verify` as the second. Apify's own Actor criteria are real-world usefulness, quality and technical excellence. |
| [[Hyphenate]] | The callback number comes from an independent source, and the report records it. That is the control auditors test. |
| [[Armadin]] | Real attacks feed the attacker, and the held-out attacks come from real reports. |
| [[CRS Credit API]] | `vendor-verify` calls CRS (business credit, state filings, OFAC) through the CRS MCP server before money moves: "Best Financial AI Agent". |
| Cal Hacks judging | Application (a real control), Technical complexity (held-out split, regression suite) and Functionality (runs anyone can open). |

## At opening
- [x] Apify's prize text (Hacker Guide, Oct 23): "Top 5 projects using Apify, we also have a best actor award for building an actor for this event. Project must be using Apify in a meaningful way. We will judge the quality of the project as well as other criteria." It doesn't require Store publishing, MCP or pay-per-event. All our Actors are built this weekend, so they qualify, and publishing stays a quality signal.
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
- Python MCP server as a Standby Actor: https://docs.apify.com/sdk/python/docs/guides/mcp-servers
- Pluto Security, prompt injection through Apify MCP (Aug 31, 2026): https://pluto.security/blog/apify-mcp-prompt-injection/
- Primary sources for `vendor-verify`: RDAP (e.g. https://rdap.org/domain/example.com) · OFAC SDN list: https://sanctionslist.ofac.treas.gov/Home/static/sdn.html (CSV: https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.CSV)
- Store Actors we reuse: [Website Content Crawler](https://apify.com/apify/website-content-crawler) · [Google Search Results Scraper](https://apify.com/apify/google-search-scraper) · [RAG Web Browser](https://apify.com/apify/rag-web-browser) · [Reddit Scraper Lite](https://apify.com/trudax/reddit-scraper-lite) · [Google Maps Scraper](https://apify.com/compass/crawler-google-places)
- Community Actors, fallback only (mostly unrated): [Contact Details Scraper](https://apify.com/vdrmota/contact-info-scraper) · [WHOIS Domain Lookup](https://apify.com/confidential_gnat/whois-com) · [OFAC Sanctions Scraper](https://apify.com/opendata-labs/ofac-sanctions-scraper)
- Apify $1M Challenge criteria: https://apify.com/challenge

Back to [[Home]] · [[Fire Drill]] · [[Apify]] · [[Top Ideas Stress Test]]
