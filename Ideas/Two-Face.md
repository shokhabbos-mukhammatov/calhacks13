---
type: idea
cluster: "Trust rails for the agent economy"
score: 8.0
novelty: 9
buildable: 7
sponsor_fit: 8
shortlisted: true
trap: false
status: idea
tags: [idea, shortlist]
---
# Two-Face

Crawl storefronts with paired "human" and "AI shopper" sessions. Flag sites that show agents different prices, fake reviews or hidden instructions, and publish a trust score shopping agents check over MCP before they pay.

**Score 8.0** · novelty 9 · buildable in 36h 7 · sponsor fit 8
**Angle:** [[Trust rails for the agent economy]]
**Sponsors:** [[Bright Data]], [[Apify]], [[Visa]], [[Anthropic]], [[Elastic]], [[Coinbase]], [[Creao AI]], [[Y Combinator]]

## Pitch line
Agents shop for us now. Two-Face checks whether a store shows your agent the same page it shows you.

## How it works
Two-Face loads each product page twice at the same moment from the same geo-pinned exit IP, and the only difference is identity. Profile H is an ordinary browser. Profile A declares itself a shopping agent with an agent user-agent and Trusted-Agent-Protocol-style signed headers. Each pair is captured as rendered DOM, visible text, structured product data (price, stock, rating), a screenshot and a network summary, and re-run three times so A/B tests and ad rotation drop out. A diff engine flags persistent differences, and Claude classifies each as benign (layout, localization), commercial divergence (different price or terms) or agent-targeted text, with evidence and a confidence score. Verdicts roll up into a per-domain trust index in Elastic, which agents query through Agent Builder tools over MCP and as a published Apify Actor. For a reliable demo the team deploys 4–5 of its own storefronts (honest, benign personalizer, agent-only price hike, agent-only reviews, hidden canary text), and also runs a robots-respecting measurement study on a small allowlist of real sites, reported as category statistics.

## The 2-minute demo
1. 0:00 Hook: two screenshots of one product page that look identical. ‘The store your agent sees isn’t always the store you see.’
2. 0:15 Click Diff: agent-only text lights up and the price turns red ($49 for humans, $64 for agents). Claude’s verdict: agent-targeted text + commercial divergence, confidence 0.94, with evidence.
3. 0:35 How: same exit IP, city and second, with identity as the only variable, and three repeats to remove noise. Bright Data runs the pairs, Claude judges intent, Elastic holds the index, agents query it over MCP.
4. 0:55 Jaw-drop: a judge flips the ‘cloak’ switch on a store that scored honest. It rescans in about 20 s and the trust score drops. The shopping agent about to buy there checks the index, refuses, explains why, and checks out with an honest merchant via the Visa sandbox.
5. 1:25 Real-world study: N pages from M retailers, X% showed persistent differences, most of them benign. Show the categories and the classifier’s precision on the labeled set.
6. 1:45 Close: a trust oracle any agent can call today, as an MCP tool or an Apify Actor, before it spends your money.

## Architecture
- Paired crawler: Bright Data Scraping Browser + Playwright with sticky residential geo sessions; only identity headers and a TAP-style signature change.
- URL discovery: Bright Data SERP API, filtered by robots.txt and an allowlist.
- Capture and diff (Python): visible-text extraction, JSON-LD price parsing, screenshots with perceptual-hash diff, a three-run persistence filter.
- Classifier: Claude with structured output, evaluated for precision and recall on the seeded stores.
- Trust index: Elastic indices for pairs, diffs, verdicts and domain scores.
- Agent API: Elastic Agent Builder tools (get_merchant_trust, explain_flags, compare_offer) over MCP; an Apify Actor ‘two-face-scan’; optional x402 paywall for deep scans.
- Demo shopper: a Claude Agent SDK agent that checks trust before paying via the Visa sandbox or x402.
- Seeded stores on Vercel with an admin cloak toggle; Next.js dashboard with split screen and diff overlay.

## How to qualify, per sponsor
| Sponsor | How |
| --- | --- |
| [[Bright Data]] | Same-exit paired sessions are what make the experiment valid; say so in the pitch. SERP API for discovery. |
| [[Elastic]] | Ingest verdicts, register custom tools in Agent Builder, expose them over MCP; the demo agent calls them live. Matches last year’s criteria. |
| [[Visa]] | Trust-gated checkout through the sandbox. Pitch: TAP lets merchants trust agents; Two-Face lets agents trust merchants. |
| [[Apify]] | Publish ‘two-face-scan’ as a public Actor and call it through the Apify MCP server. |
| [[Anthropic]] | Claude is the intent classifier with cited evidence; the Agent SDK runs the shopper; show the eval numbers. |
| [[Coinbase]] | x402 pay-per-scan for agents, which is the oracle’s business model. |
| [[Creao AI]] | Last year’s Best MCP Integration track fits: the trust index is an MCP tool any agent can call. |
| YC | A trust layer for agent commerce is a clear startup story: merchants and agent platforms both pay. |
| [[Armadin]] | Defensive security for agent commerce, with canary fixtures and responsible disclosure. |

## Load-bearing risk
Real sites may show almost no identity-based differences within 36 hours, or too much noise from A/B tests and bot challenges, making the index look empty or full of false positives. Wrongly naming real merchants would be an ethics problem.

**Mitigation:** Keep identity as the only variable; count only differences that persist across three runs; mark challenged pages inconclusive, never flagged. Seeded stores make the demo reliable and double as a labeled eval set. Present real-site results as an honest measurement study with category stats only. Fallbacks: a mock payment adapter if the Visa sandbox stalls, a thin MCP server over the Elastic REST API if Agent Builder is flaky.

## 36-hour split
- A, crawl: paired sessions, capture, diff engine, real-world study.
- B, intelligence: seeded stores, Claude classifier and eval, Elastic ingest, Agent Builder tools.
- C, product: dashboard, shopping agent, Visa/x402 gate, Apify Actor, video and pitch.
- H0–2: agree on contracts (PagePair, Diff, Verdict, DomainScore) and the demo choreography.
- H2–14: paired sessions working; seeded stores deployed; diff engine and classifier on seeded data; dashboard wired.
- H18–24: real-world crawl (50–100 pages); Elastic + MCP tools; payment gate; Actor.
- H24–30: end-to-end loop in under 30 s: toggle → rescan → index → agent refuses → pays elsewhere.
- H30–36: freeze, README and eval table, video, 8+ timed rehearsals, submit.

## Prep before Oct 23
- [ ] Accounts: Bright Data (ask about hackathon credits), Apify, Elastic trial with Agent Builder, Anthropic, Coinbase CDP, Visa sandbox request, Vercel.
- [ ] Throwaway tutorials: Playwright on Scraping Browser, one Agent Builder tool, a hello-world Actor, one x402 testnet payment.
- [ ] On paper: diff taxonomy, JSON contracts, trust-score formula, the five seeded-store behaviors.
- [ ] Draft the real-world study plan: retailer list, robots.txt and terms checks, rate limits, responsible wording.

## Variations
- Agent-honest badge: merchants opt in to continuous verification and get a signed badge that agents check at checkout.
- Render-parity firewall: MCP middleware that strips anything a human wouldn’t see before the model reads it.
- Identity × city price-parity watchdog for consumer advocates.
- Reverse Two-Face for merchants: catch traffic that claims to be a trusted agent but fails signature checks.

## Why other teams won't build it
It is a controlled experiment, not a scraper: isolating identity as the only variable while filtering real-world noise, having Claude judge intent with evidence, and feeding the verdict into a live agent’s payment decision.

## Team notes
- Oct 23: see [[Two-Face Stress Test]]. Short version: don't build it as written. A reshaped version that compares what the human sees with what the agent reads, checked at the moment of payment, fixes most of the problems.
