---
type: research
tags: [research, shortlist]
---
# Two-Face stress test

Written Oct 23, before opening. Checks [[Two-Face]] against the posted [[Prizes]], our team schedule ([[Prep Plan]]) and what has actually been published about agents and storefronts.

## Verdict
**Don't build Two-Face as written.** The pitch is good, but its core claim (stores show agents a different page than humans) has no published real-world evidence, and the experiment can't see what real agents see. The demo works only because we build the cheating stores ourselves, and the real-world study will most likely come back blocked or identical. It is also the widest build on the shortlist while we are two people until Saturday evening.

If we want this space, build the reshaped version in [[#A version worth building]]: compare what the human sees with what the agent reads, at the moment the agent is about to pay, on any URL a judge names. It keeps the Visa, Apify, Coinbase and Elastic targets and removes most of the risks below.

Re-score: as written **6.0** (novelty 7, buildable 5, sponsor fit 6) instead of 8.0. Reshaped: **7.0** (7 / 7 / 7).

## Concerns, worst first

### 1. Nobody has shown real stores doing this
- The attack is proven in a lab. SPLX (Oct 2025) built sites that served ChatGPT Atlas and Perplexity a different page based only on the user-agent, and the agents believed it. Those were SPLX's own sites. We found no audit of real merchants doing it.
- Merchants do say they will treat agents differently. In a PYMNTS survey of 60 merchants, a third would offer agents their full range "with different prices, promotions or delivery choices". That is announced channel pricing, like app-only deals. A different price is not deception on its own, so "price differs, therefore untrustworthy" will misfire on honest stores.
- An agent-only **price hike** is the least likely cheat. Agents compare stores, and price reliably lowers their choice rate (HBR, May 2026). A cheater would show the agent a *better* offer, a fake discount or persuasive hidden text, to win the selection. Our seeded "agent-only price hike" store models the wrong attack. A hike only pays where the agent can't shop around, such as rebooking on one airline.
- So the judge question that sinks us is "does anyone actually do this?", and today's honest answer is "not that anyone has measured". That costs us on **Application** ("realistic real-world use").

### 2. The experiment holds constant what stores actually check
- Real shopping agents mostly don't announce themselves in the user-agent. Amazon's complaint says Comet identified itself as a human user of Chrome.
- Agents that do identify themselves sign requests. Visa TAP is built on RFC 9421 and Web Bot Auth, and the merchant verifies the signature against a trusted key directory. Our "TAP-style" headers would be signed with our own key, so a store that checks sees unverified traffic, not a trusted agent. We can't produce OpenAI's signature or a Visa-registered one.
- Stores that discriminate on infrastructure (agent providers' datacenter IPs, browser fingerprints) are invisible to us too, because both profiles share one residential IP by design.
- That leaves the naive user-agent check SPLX demonstrated. Catching it is fine, but a scanner with a known identity gets cloaked: once Two-Face publishes scores, a cheating store shows our crawler the honest page. Search engines have fought this for 20 years. The one visitor a store can't hide from is the real agent at the moment it buys.

### 3. The real-world study will probably come back empty or blocked
- The one field study we found (Time Under Tension, 11 Australian retailers tested with browser agents) mainly found differences in site access and bot checks, not in prices.
- Two requests from one IP in the same second with different user-agents is itself a bot signal, and three repeats make it worse. Expect Profile A to get more challenges, which our own rules mark inconclusive. Likely headline: "N% of retailers blocked the agent; none showed a persistent price difference." That is a real finding, but it removes the 1:25 slide.
- Noise sources: cart and CSRF tokens, recommendations, stock, lazy-loaded images, currency and geo. Three repeats help. The standard method from price-discrimination research (Hannak et al., IMC 2014) is a **control pair**: run two identical human profiles side by side, measure how much they differ from each other, and count an H-vs-A difference only when it beats that baseline.

### 4. The crawler may fight the experiment
- Bright Data's Scraping Browser is built to look human. Its docs list headers among the things it manages and don't say whether we can set our own user-agent. The experiment needs exact control of the user-agent and headers.
- Bright Data has **no posted prize**, and Apify has six ($5K). Apify Proxy supports sticky sessions, and Crawlee with Playwright gives full header control. Crawl on Apify and drop Bright Data unless it announces a prize at opening. Apify judges will also prefer Apify doing real work over an Actor wrapper added at the end.
- First-hour test: send both profiles to `httpbin.org/headers` through the chosen proxy and confirm the headers arrive exactly as we set them.

### 5. The trust index contradicts our ethics rule
- The product is a per-merchant trust score, but our mitigation says never name real merchants and report only category stats. So on demo day, "the oracle any agent can call" has scores for five fake stores.
- An index is worth querying only once it covers many domains, and 50–100 pages isn't coverage.

### 6. Too much to build for two people
- Akmal arrives around 6:30 PM Saturday ([[Prep Plan]]), about 22 hours after hacking starts. The 36-hour split runs three parallel tracks from H2, and the third person arrives exactly when H18–24 needs the real-world crawl, Elastic, the MCP tools, the payment gate and the Actor.
- Thirteen moving parts: paired crawler, capture (DOM, text, JSON-LD, screenshot, network), perceptual-hash diff, persistence filter, 4–5 seeded stores with an admin, Claude classifier and eval, Elastic ingest, Agent Builder tools over MCP, Apify Actor, x402 paywall, Visa sandbox checkout, Agent SDK shopper, Next.js dashboard.

### 7. The sponsor fit is weaker than 8
| Sponsor | Posted prize | Real fit |
| --- | --- | --- |
| [[Visa]] | $5K, one winner, "Reimagining Shopping" | Two-Face audits shopping instead of reimagining it. Visa appears in one call at the end, sandbox access isn't confirmed, and many agent-shopping teams will chase this prize. |
| [[Apify]] | 6 prizes, $5K | Good, and better if Apify does the crawling |
| [[Elastic]] | 2 non-cash (~$2.6K) | Fine; matches last year's winners |
| [[Coinbase]] | $2K for x402 | Pay-per-check fits naturally |
| [[Bright Data]] | None posted | Drop unless announced |
| [[Creao AI]] | 9 placements | The idea note cites last year's MCP track. This year's tracks are AI-First Disruptor, One-Person Company and Team Empowerment, so that fit is stale. |
| [[Anthropic]], YC | None posted yet | Wait for opening |

### 8. The jaw-drop moment looks staged
A judge flips a switch on a store we built to cheat, and we catch the cheat we wrote. Judges will see the wire. The patterns in [[Recent Winners 2026]] reward judges taking part or trying to break things. The judge should write the cheat, and we catch it without knowing what it is.

### 9. Smaller points
- Comparing two prices doesn't need Claude. Claude earns its place classifying hidden or agent-targeted text and explaining the evidence, so lead with that.
- Profile H is software posing as a human browser, which is what Amazon sued Perplexity over (CFAA claims, Nov 2025). For ~100 allowlisted, robots.txt-respecting pages the risk is low. Skip Amazon, keep N small and say so in the pitch.
- Prior art cuts both ways. SPLX recommended "continuous monitoring of AI-served outputs" as the defense, so Two-Face is the obvious answer to a known attack. That makes it credible, but not novelty 9.

## What's genuinely good
- One sentence and one visual (the split screen with a red price). That's rare.
- "TAP lets merchants trust agents; Two-Face lets agents trust merchants." Keep this line whatever we build.
- Agent shopping is the exact topic of Visa's $5K prize, our biggest single target outside [[Hyphenate]].
- Seeded stores double as a labeled eval set.

## A version worth building
Keep the name. Change what the two faces are and where the check runs.

**The two faces are what the human sees and what the agent reads.** The attacks that have actually worked on shopping agents didn't need a different page:
- F-Secure planted a review with a fake discount code, and their shopping agent sent the user's personal data to a phishing site.
- Guardio's "Scamlexity" test had Perplexity's Comet buy an Apple Watch from a fake Walmart.

Everyone saw the same page in both cases.

**The check runs inside the purchase, not from a crawled index.** Build an MCP tool, `check_before_pay(url, cart)`, that the shopping agent calls right before paying. It runs these checks:
1. **Render parity** (one fetch, no impersonation): compares the visible text of the rendered page with the DOM and accessibility text the model reads. Flags hidden, off-screen, zero-size and same-color text, and aria or alt text aimed at AI.
2. **Structured-data parity**: compares the JSON-LD or meta price with the displayed price and the checkout total.
3. **Identity parity** (the original idea, scoped down): compares the agent's own fetch with a parallel human-profile fetch at decision time. A store can't hide from it without also hiding from the real agent, and it still catches SPLX-style user-agent cloaking.
4. **Store legitimacy**: lookalike domain, domain age, brand vs domain mismatch (the fake-Walmart case).
5. **Verdict**: Claude classifies the findings and cites the evidence. The agent refuses or proceeds, and pays through the Visa sandbox or x402 only on a pass.

Why it's better:
- Works on any URL. There's no cold-start index and no need to name merchants.
- Real-world hits are plausible (hidden text in reviews and listings), and clean results double as our false-positive check.
- Judges write the attack themselves.
- Smaller build: no paired-crawl fleet, no three-run persistence engine, no real-world study to babysit.

Sponsors:
- **Visa**: the payment happens only after a pass.
- **Apify**: fetching runs on Apify Proxy, and the check is published as an Actor any agent can call.
- **Coinbase**: agents pay per check over x402.
- **Elastic**: every check is indexed, and Agent Builder tools `explain_block` and `merchant_history` are exposed over MCP.
- **Anthropic**: Claude is the classifier and the Agent SDK runs the shopper.

### Demo (fits the 3-minute pitch)
1. 0:00 Hook: "Last year an AI browser bought an Apple Watch from a fake Walmart. Your agent is about to pay. Is it looking at the store you'd see?"
2. 0:20 Hand a judge the seeded store's admin on a tablet. They pick a trick or type their own: a hidden instruction, an agent-only discount, a JSON-LD price that doesn't match the page. We don't look.
3. 0:50 Tell the shopping agent to buy X under $60 from three stores. Before paying, it calls `check_before_pay`. The split screen lights up the judge's trick, and Claude's verdict cites the evidence. The agent refuses and pays the honest store through the Visa sandbox.
4. 1:50 A judge picks a real product URL on their phone, and we run the check live. Most come back clean, so say that, then show precision and recall on the seeded set with the judge's trick added live.
5. 2:30 Close with the TAP line.

## If we pick it anyway: go/no-go in the first two hours
- [ ] `httpbin.org/headers` through the chosen proxy shows exactly the user-agent and headers we set.
- [ ] Fetch 10 allowlisted real product pages with both profiles. If more than half get challenged, cut the real-world study from the pitch or present it as a finding about access.
- [ ] Visa sandbox credentials in hand. If not by Saturday noon, use x402 only.
- [ ] Read the full Visa and Creao track text at opening. If Visa wants a new shopping *experience*, treat Two-Face as a side bet for that prize.

## Against Fire Drill
| | Two-Face as written | Two-Face reshaped | [[Fire Drill]] |
| --- | --- | --- | --- |
| Evidence the threat is real | Shown only on researchers' own sites | Shown against real agents (F-Secure, Guardio, SPLX) | Business email compromise against finance teams; the agent version is our pitch |
| Judge's role | Flips our switch | Writes the attack | Plays the CFO on the phone |
| Biggest prize target | Visa $5K | Visa $5K, Apify $5K, Coinbase $2K | Hyphenate $16K |
| Single point of failure | Real-world crawl and control of the crawler | One live real URL (easy fallbacks) | Voice latency and telephony |

## Sources
- SPLX, AI-targeted cloaking against OpenAI Atlas (Oct 2025): https://splx.ai/blog/ai-targeted-cloaking-openai-atlas · coverage: https://thehackernews.com/2025/10/new-ai-targeted-cloaking-attack-tricks.html
- Visa Trusted Agent Protocol spec: https://developer.visa.com/capabilities/trusted-agent-protocol/trusted-agent-protocol-specifications
- IETF Web Bot Auth draft: https://datatracker.ietf.org/doc/html/draft-ietf-webbotauth-httpsig-protocol
- Amazon v. Perplexity (Nov 2025): https://www.retaildive.com/news/amazon-sues-perplexity-ai-shopping-agents/804871/
- Guardio "Scamlexity" (Aug 2025): https://cyberinsider.com/ai-browsers-fooled-by-phishing-and-fake-stores-in-real-world-tests/
- F-Secure shopping-agent test: https://www.f-secure.com/en/partners/insights/can-ai-shopping-agents-be-trusted-we-built-one-to-find-out
- PYMNTS merchant survey: https://www.pymnts.com/?p=4190028
- Time Under Tension retailer study: https://www.bandt.com.au/australian-retailers-risk-losing-customers-as-ai-shopping-agents-arrive-time-under-tension-study-reveals/
- HBR, "Traditional Marketing Doesn't Work on AI Shopping Agents" (May 2026): https://store.hbr.org/product/research-traditional-marketing-doesn-t-work-on-ai-shopping-agents/H096G7
- Bright Data Scraping Browser docs: https://docs.brightdata.com/scraping-automation/scraping-browser
- Hannak et al., "Measuring Price Discrimination and Steering on E-commerce Web Sites", IMC 2014

Back to [[Home]] · [[Two-Face]] · [[Shortlist]]
