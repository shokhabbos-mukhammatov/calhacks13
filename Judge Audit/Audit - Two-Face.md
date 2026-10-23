---
type: audit
idea: "Two-Face"
verdict: "Best web-data track fit; highest risk of looking staged"
tags: [audit, shortlist]
---
# Judge audit: [[Two-Face]]

> [!warning] Verdict
> The cleanest fit for [[Bright Data]], [[Elastic]] and [[Apify]], and the problem is now documented by security researchers. The weak spot: if the only cheating stores in the demo are ones we built, judges will call it staged. It needs real-world evidence, even if the finding is “mostly benign”.

## Scorecard (1–5)
| Judge | Score | Why |
| --- | --- | --- |
| Sponsor tracks ([[Bright Data]], [[Elastic]], [[Apify]]) | 5 | Same-exit paired sessions, Agent Builder tools over MCP, a published Actor: textbook use of each |
| General | 4 | The judge flips a cloak switch and the shopping agent refuses to buy: clear and visual |
| Security | 4 | AI-targeted cloaking is a published attack; we turn it into continuous measurement |
| Quant | 3 | Will respect the controlled-experiment design if we show the numbers |
| [[Anthropic]] | 3 | Claude as an intent classifier with evidence: solid, not spectacular |
| VC | 3 | “Who pays, and won’t OpenAI or Perplexity build this in?” |
| [[Visa]] | 3 | Trust-gated checkout is a good story only if sandbox access arrives |

## Prior art judges may know
- **[SPLX’s “AI-targeted cloaking” research](https://thehackernews.com/2025/10/new-ai-targeted-cloaking-attack-tricks.html)** (Oct 2025) showed sites serving different content to ChatGPT and Perplexity crawlers. That is the best possible validation, and judges who read it will ask what we add.
- Classic **search-engine cloaking detection** in SEO tooling.

**Our line:** “SPLX proved sites can show AI agents a different page. Nobody is measuring it continuously or letting agents check before they pay. Two-Face is that check: a controlled experiment per page, Claude judging intent, and a trust score any agent can call over MCP.”

## Killer questions and our answers
| Question | Answer |
| --- | --- |
| “You built the cheating stores. Does this happen for real?” | Cite SPLX, then show our real-site study: how many pages, what share differed, and in which categories. Honest “mostly benign” beats invented drama. |
| “Isn’t agent-specific content often legitimate?” | Yes: simpler layouts and structured data are benign. The classifier separates benign, commercial divergence and agent-targeted text, and we show its precision on labeled data. |
| “Won’t cloakers detect your ‘human’ browser too?” | Residential exits and a real browser profile raise the bar. It’s an arms race, so we sell continuous measurement plus attestation, not a one-time scan. |
| “Who pays?” | Agent platforms and payment networks before they let agents spend; merchants who want an “agent-honest” badge. |
| “Is the scraping legal and polite?” | robots.txt respected, rate-limited, blocked pages marked inconclusive, never bypassed. |

## Red flags at the table
- **Staged demo.** Seeded stores alone look rigged.
- **Empty index.** A 36-hour crawl may find little real cloaking.
- **Network.** Crawling over venue Wi-Fi is slow; run it overnight and cache results.
- **Naming and shaming.** Accusing a real merchant on stage is a credibility and ethics risk.

## Upgrades that make it judge-proof
1. Run the real-site crawl overnight Saturday and show category statistics, never named merchants.
2. Add one test against real AI-crawler user agents (the SPLX setup) next to our signed-agent profile.
3. Show classifier precision and recall on the labeled set.
4. Consider leading with the defensive variant, a “render-parity firewall” that strips anything a human wouldn’t see before the agent reads it. It works on any page whether or not we find a real cloaker.
5. Keep a mock payment adapter in case the Visa sandbox doesn’t arrive.

Related: [[Judge Panel]] · [[Judge Verdict]] · [[Shortlist]]
