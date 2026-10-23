---
type: research
tags: [research, council, challengers]
---
# Challenger idea pool

Oct 23. Forty new ideas from five idea generators that worked in isolation, each under one frame: a regulator, logistics, game design, a curious 10-year-old, and removing an assumption everyone treats as fixed. Each generator had the same brief: what the council and the stress tests rewarded, the posted [[Prizes]], and the list of ideas already considered.

Scores are a first-pass filter, not council scores: **N** novelty, **V** viable for two people until Saturday evening, **F** fit with the posted prizes and what the reviewers rewarded. Weighted = 0.35 N + 0.40 V + 0.25 F. The top ideas went to [[Candidates]] for the council.

## Clusters

### Controls before the money moves
| Idea | One line | N | V | F | Weighted |
| --- | --- | --- | --- | --- | --- |
| **Auditor Writes the Tests First** → CH1 | The accountant's controls in plain sentences, compiled into checks every entry must pass before it's recorded | 8 | 8 | 9 | **8.25** |
| Quorum Treasury | A PTA or booster-club account no single treasurer can move money from: 2 of 5 members approve by text | 7 | 8 | 7 | 7.4 |
| Fair Jar | Tip pool split by hours under California rules; an invariant refuses any share to a manager | 6 | 9 | 6 | 7.2 |
| Quicksave for Stores | Bulk catalog and price edits run in a shadow copy with invariant checks, with one-key rollback | 7 | 8 | 6 | 7.15 |
| Whose Money | Hourly per-customer proof of reserves for fintech pooled accounts (the Synapse problem) | 8 | 7 | 6 | 7.1 |
| Restatement Radar | Lineage for every figure in documents already sent; edit a source row and the wrong documents turn red | 7 | 7 | 7 | 7.0 |

### Speech is a commitment
| Idea | One line | N | V | F | Weighted |
| --- | --- | --- | --- | --- | --- |
| **Reg F Gate** → CH3 | A deterministic gate for debt-collection voice agents: every dial and every sentence checked against the federal rules before it is spoken | 7 | 8 | 9 | **7.9** |
| **Said-On-The-Phone** → CH4 | A voice agent turns a contractor's spoken quote into the contract; the invoice is diffed against it | 8 | 8 | 7 | **7.75** |
| Binding Words (merged into CH3) | A voice agent can make refund or waiver promises only through a typed offer tool checked against policy | 7 | 8 | 8 | 7.65 |
| Signed Manifest | Phone orders closed with a read-back that's hashed into chargeback evidence | 7 | 7 | 7 | 7.0 |

### Title and evidence for money claims
| Idea | One line | N | V | F | Weighted |
| --- | --- | --- | --- | --- | --- |
| **Original Bill** → CH2 | One signed original per receivable, transferred by endorsement, so the debtor pays only the current holder (against double-pledging) | 9 | 7 | 8 | **7.95** |
| Corner-Store Tab | A bodega tab both sides co-sign, with Friday voice reminders in the customer's language | 7 | 9 | 5 | 7.3 |
| Fake Receipt Court | Expense receipts checked against the card charge, the real menu, the ZIP's tax rate and coworkers' duplicates | 7 | 7 | 8 | 7.25 |
| Reason Code | Credit-denial reasons proven true by a counterfactual check the applicant can run | 7 | 7 | 6 | 6.75 |
| Friendly-Fire / Chargeback Deckbuilder | Rules engine that assembles Visa Compelling Evidence 3.0 packets (crowded: Chargeflow, Justt, Chargebacks911) | 5 | 8 | 7 | 6.7 |

### Pay what's proven, hold only what's disputed
| Idea | One line | N | V | F | Weighted |
| --- | --- | --- | --- | --- | --- |
| Partial Release + Dispute Pot | Pay the clean invoice lines now; only the disputed amount waits, in a sub-account both sides control | 6 | 8 | 9 | 7.55 |
| Dock-Written Bill | The buyer's receiving photo is the bill (evaluated receipt settlement for restaurants) | 7 | 7 | 8 | 7.25 |
| Shrinking No-Show Hold | A no-show charge that shrinks by what walk-ins spent at that table | 8 | 7 | 6 | 7.1 |
| Return to Sender | Recovery audit for small businesses (duplicate payments, unclaimed credits), with a voice agent asking for the refund | 6 | 8 | 7 | 7.05 |

### Timing solvers for cash
| Idea | One line | N | V | F | Weighted |
| --- | --- | --- | --- | --- | --- |
| Cutoff | Learn each customer's hidden AP payment-run schedule and time collection calls just before it | 8 | 7 | 8 | 7.6 |
| Payday Shuffle | Reschedule bills inside grace windows so the balance never goes negative | 6 | 8 | 7 | 7.05 |
| Wave Approvals | Batch an owner's payment approvals into waves, priced by lost discounts and late fees | 7 | 7 | 7 | 7.0 |
| Payables Speedrun | Weekly bill-pay route: capture early-pay discounts, avoid late fees, keep a cash floor | 5 | 8 | 8 | 6.95 |
| Shift Trade Chains | Multi-hop shift swaps that stay under overtime and San Francisco's predictability-pay rules | 7 | 8 | 5 | 6.9 |
| Oven-Slot Pricing | A bakery's price depends on how wide a pickup window you accept | 8 | 7 | 5 | 6.85 |
| Fire Window | Kitchen fire times so every plate for a table lands within 60 seconds | 7 | 7 | 5 | 6.5 |

### Price truth for shoppers and stores
| Idea | One line | N | V | F | Weighted |
| --- | --- | --- | --- | --- | --- |
| **Promo Glitch Hunter** → CH5 | A solver finds discount stacks that sell below cost before a sale goes live | 8 | 7 | 8 | **7.6** |
| The Price Is The Price | Crawl a restaurant's online ordering to checkout and flag fees hidden under California's drip-pricing law | 8 | 7 | 7 | 7.35 |
| Sticker vs Beep | Phone camera checks shelf tags against the POS price before the county inspector does | 7 | 7 | 6 | 6.75 |

## Traps
- **Sweetheart** (checkout camera versus POS), **DIM Tetris** (camera box sizing), **Where Did The $20 Go** (camera cash count), **Seal Check** (skimmer detection): computer vision that must work live in 36 hours, and Everseen, Paccurate and Packsize already exist.
- **Tear to Approve** (receipt printer, nail switch and scale as the bill-pay interface): needs hardware the team doesn't have the day before.
- **Cheapest Card Please**: steers customers off rewards cards, which a Visa judge won't like, and handles judges' card data.
- **Hold Music Any%**: real hold times are longer than a 3-minute pitch, and it calls real 800 numbers from the venue.
- **Ten Percent** (price-gouging evidence): needs a pre-emergency price baseline nobody stored.
- **Cross-Dock Returns**: a two-sided marketplace plus physical logistics; the demo would have to be staged.

## What the pool says
- The strongest ideas share one move: **put a check the team writes at the point where money, speech or ownership changes hands**, and let the judge try to get past it.
- All three deep-dived ideas proposed merging with [[Fire Drill]] on their own. That is why the council also scores a synthesis (CH6).

Related: [[Candidates]] · [[Council Verdict]]
