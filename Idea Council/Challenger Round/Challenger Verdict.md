---
type: audit
tags: [audit, council, challengers, index]
---
# Challenger verdict

Oct 23. Can a new idea beat [[Fire Drill]] and [[Netting House]]? Five isolated idea generators produced 40 new ideas ([[Idea Pool]]). The best five, plus one synthesis, were scored by the same three council agents in one run, next to the two leaders, on their round 1 scales and with the posted [[Prizes]] in hand ([[Candidates]]). Council score = the average of the three lens scores + 1 for each agent that picked it (each agent picked at most 2).

## Result
| # | Candidate | A Substance | B Impact | C Novelty & venture | Avg | Picked by | Council |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **CH6 Controls CI with Fire Drill inside** (synthesis) | 8.5 | 8.5 | 7.0 | 8.0 | A#2, B#1 | **10.0** |
| 2 | **INC1 Fire Drill** (merged council version) | 7.5 | 8.5 | 7.3 | 7.8 | B#2, C#1 | **9.8** |
| 3 | CH1 Ledger CI ("the auditor writes the tests first") | 8 | 6.5 | 6.3 | 6.9 | A#1 | 7.9 |
| 4 | CH2 Original Bill | 6 | 7 | 7.0 | 6.7 | C#2 | 7.7 |
| 5 | INC2 Netting House | 7.5 | 8 | 6.7 | 7.4 | none | 7.4 |
| 6 | CH3 Reg F Gate | 7 | 7 | 5.7 | 6.6 | none | 6.6 |
| 7 | CH5 Promo Glitch Hunter | 6.5 | 5 | 6.0 | 5.8 | none | 5.8 |
| 8 | CH4 Said-On-The-Phone | 4.5 | 5 | 6.0 | 5.2 | none | 5.2 |

## What it means
1. **No standalone new idea beats Fire Drill.** The only candidate above it is CH6, which *is* Fire Drill with Ledger CI's rule compiler around it, and the margin (10.0 against 9.8) is a tie. The new ideas upgrade Fire Drill rather than replace it.
2. **Netting House is no longer the second-best option.** Ledger CI (7.9) and Original Bill (7.7) both finish above it (7.4), and nobody picked Netting House this round.
3. **The agents split on how much to add to Fire Drill:**
   - **A, the Skeptic**, picks Ledger CI first: it is "the first idea in either round that answers the Anthropic judge's 'how do you know Claude got it right?' with a mechanism instead of a promise".
   - **B, the Impact Analyst**, picks CH6 but says the voice callback is not optional. Ledger CI alone scores 6.5 from B, because "the insider who embezzles usually has the bank login and pays around the gate".
   - **C, the Venture Scout**, stays with plain Fire Drill. CH6 is "two products in one 3-minute pitch", and judges may remember neither moment.

## Decision: build Fire Drill as a controls gate, with one product and two moments
This is our synthesis of the three positions; no agent scored this exact plan.

> **"Your accountant's controls, run like unit tests before the money moves, starting with the one that stops payment-redirect fraud."**

- **Control #1 is Fire Drill.** It is the provenance rule: no payment to bank details that first appeared in untrusted text. A refusal triggers the voice callback to the vendor's number of record, which is the judge's phone. This is the headline, as B and C require.
- **Second moment: the judge writes a control in their own words.** It goes live only after the read-back, the blind examples and the one clarifying question, so A's mechanism is on stage. Then the judge tries to get a payment past it. One product (a gate on the only path to the bank), two judge moments.
- **Cut the hole finder.** A says cut it first, C says the pitch is already full, and B gives it no weight.
- **Build order for two people:**
  - **Fri night:** the gate mutation, the rule language, and hand-written versions of the provenance, duplicate and split rules. Add the poisoned-invoice attack and Nessie. The demo is complete from here on.
  - **Sat day:** the sentence-to-rule compiler with its gates, the 25-control benchmark, and the held-out attack table.
  - **Sat evening (third teammate):** the voice callback.
  - **Sun:** freeze and rehearse both judge moments.
- **Don't claim Convex's serializable transactions as our engineering** (A). Our original work is the rule gates, the provenance rule and the benchmark.
- **Name the neighbors first** (C): Hamming showed an adaptive red team against bank voice agents at FinovateFall 2026 ([Finovate](https://finovate.com/videos/finovatefall-2026-hamming-ai/)). Basware completed its acquisition of Trustpair on Oct 5 ([ITPro](https://www.itpro.com/business/acquisition/basware-to-acquire-trustpair-to-strengthen-payment-fraud-prevention)). Eftsure, KnowBe4 Agent Risk Manager, CaMeL, and Ramp's plain-English spend policies are the others.
- **The impact case** (B): about $3.05B of reported business email compromise losses in 2025. Small organizations lose the most to internal fraud: ACFE's 2026 median loss is about $126K, as reported by B.

**If Hyphenate's track text tips the decision at opening**, the alternative is now a near-tie between [[Netting House]] (A and B prefer it) and Original Bill (C's pick, 7.7). Use Netting House if the track stresses treasury, cash or settlement. Use Original Bill if it stresses receivables, financing or fraud. Original Bill has the best "why now" in the round: prosecutors allege First Brands used fake and double-pledged invoices (B verified). Iridium Credit just raised $3M to verify invoices for factors ([Dealroom](https://dealroom.co/news/160636-iridium-credit-raises-3m-to-help-lenders-verify-unpaid-invoices/)). Its weak points are A's ("the AI is decorative") and B's ("debtors have no reason to join").

## Why the others fell short
- **Reg F Gate (6.6):** C says every funded AI collector (Salient, Domu, Prodigal) already sells "compliant by design". B flags the distaste risk. A says half of it is frequency rules vendors already ship.
- **Promo Glitch Hunter (5.8):** B sees a modest problem. C's venture score is 4, because promotion engines already cap budgets.
- **Said-On-The-Phone (5.2):** A rates it a 4.5 (thin). The diff depends on how Claude structures a loosely spoken scope.

## Files
- Candidates and specs: [[Candidates]]. All 40 ideas: [[Idea Pool]]
- Raw scores: `Idea Council/Challenger Round/cr-A.json`, `cr-B.json`, `cr-C.json`; totals in `results.json`

Related: [[Council Verdict]] · [[Top Ideas Stress Test]] · [[Prizes]]
