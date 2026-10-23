---
type: audit
tags: [audit, council, challengers]
---
# Challenger round: candidates

Oct 23. New ideas built to beat the two leaders, scored by the same three council agents in one run, next to the leaders, with the posted [[Prizes]] in mind.

How they were made: five idea generators worked in isolation under different frames (regulator, logistics, game design, a 10-year-old, removing a fixed assumption) and produced 40 ideas. Those were scored for novelty, viability and fit. The top three were then worked out in depth by separate agents; the next two are short specs. CH6 is a synthesis: all three deep dives proposed merging with Fire Drill.

> [!warning] Unverified claims
> The deep dives were written without web research. Legal and regulatory claims below (UCC Article 12, 12 CFR 1006, the FCC's AI-voice ruling, competitor lists) are the generators' claims. Reviewers must verify them before relying on them.

## The two leaders (incumbents)

### INC1 · Fire Drill (merged council version)
**Pitch:** An accounts-payable agent whose tool boundary runs a deterministic provenance policy: any payment or bank-detail change whose payee details trace to untrusted text (an email, a call transcript, invoice text) is blocked. A blocked request triggers a separate voice agent that phones the vendor on the number of record, which is a judge's phone at the table. An adaptive attacker drills it, and the result is a breach-versus-utility table on held-out attacks.
**Demo:** a judge plays a fake CFO and pushes a payment redirect. The old agent caves at a visible turn; the patched one triggers the callback, the "vendor" judge denies the change, and the payment on Capital One Nessie is blocked. If the agent holds from the start, the attacker's 20 variants are fast-forwarded instead.
**Sponsors:** Hyphenate (primary), Cartesia, Armadin, Capital One Nessie, Elastic for the trace.
**Buyer:** finance teams running AP agents and human AP desks; per-payment verification plus scheduled drills.
**Known prior art:** KnowBe4 Agent Risk Manager, Hamming, Cekura, Trustpair and Eftsure. Details in [[Ideas/Fire Drill]], [[Council Verdict]], [[Top Ideas Stress Test]].

### INC2 · Netting House
**Pitch:** Small businesses' agents post invoices to a clearing house; a solver cancels circular debt; only the net amounts move, settled atomically from prefunded wallets or not at all.
**Demo:** 12 agents in a seeded economy; arrows collapse from 41 into 4, "$412K settled, $38K moved".
**Sponsors:** Hyphenate, Fetch.ai, Coinbase x402 (a stretch).
**Buyer:** a dense cluster that already trades together (a construction project, a co-op); network-effect business with a cold start.
**Known prior art:** Slovenia's national set-off, Cycles (Informal Systems), Sardex, Causa Prima. Details in [[Ideas/Netting House]] and [[Top Ideas Stress Test]].

## Challengers

### CH1 · Ledger CI ("the auditor writes the tests first")
**Pitch:** A small business's accountant writes controls as plain sentences, and every bookkeeping entry and payment must pass them before it is recorded or released, like unit tests before a merge.
**How it works:** Every write to the books (bookkeeper entry, bank-feed import, a bill the Claude AP agent proposes) goes through one Convex mutation that evaluates every active rule against the ledger plus the proposed entry in the same serializable transaction, so two concurrent payments can't both slip under a split rule. Claude doesn't write rules as code: it translates each sentence into a typed tree in a small team-written rule language of about eight control types (uniqueness, threshold, windowed sum for split payments, vendor age, cooldown after a bank-detail change, separation of duties, allow/deny lists, approval exemption). Vague sentences ("unusual", "reasonable") are refused, naming the number that's missing. A rule goes live only after four team-written gates: template read-back into English; 10–15 pass/fail examples written by a separate Claude call that never sees the tree, which the tree must classify correctly; every one-edit variant of the tree (±1 cent, < vs <=, ±1 day, payee by name vs by bank account) must be caught by an example, and each survivor becomes a yes/no question to the author; a replay over the historical ledger. Only a "cleared" verdict lets the release action create the Nessie bill; the agent never holds the bank key.
**Demo:** a judge types a rule in their own words, sees the read-back, 12 independent examples and one clarifying question ("$1,300 Monday and $1,300 eight days later: block?"), and the rule goes live ("would have flagged 3 of 4,100 entries"). The judge then tries two $2,400 invoices, a renamed vendor with the same bank account, and a simultaneous submit from two phones; each is refused with their sentence quoted, and the Nessie balance doesn't move. Closing table: on 25 controls from published AP checklists, wrong-meaning rules accepted with compile-only versus with the gates, and zero violating releases across randomized concurrent attacks.
**Sponsors:** Hyphenate (primary), Capital One Nessie, Convex.
**Buyer and use:** fractional CFOs and small bookkeeping firms running AP for 10–50 clients, priced per entity per month; the gate runs on every entry daily.
**Named competitors (to verify):** Ramp, BILL and Brex policy menus inside their own rails; MindBridge (after-the-fact ledger scoring); AppZen (enterprise invoice audit); AuditBoard and Workiva (document controls, don't run them).
**Load-bearing risk:** a judge's sentence compiles to a subtly different meaning and the gates miss it live.

### CH2 · Original Bill
**Pitch:** One signed "original" per receivable that changes hands only by endorsement, so the debtor's AP agent pays only whoever controls it now. It targets invoice double-pledging, the fraud alleged behind receivables-finance collapses like First Brands.
**How it works:** An invoice becomes an original only when the debtor's Claude AP agent acknowledges it against the debtor's own PO and goods-receipt line, so the record is tied to the obligation, not the document: renumbered, re-dated or split copies land on the same anchor, and a conservation invariant keeps the total minted per anchor at or below the acknowledged amount. Control moves only by endorsement signed on the controller's own device and committed by compare-and-swap in a Convex mutation, with a hash-chained audit log. The AP agent's pay tool has no payee argument: the pay-to account comes only from the current controller, at most once per anchor, so neither a fake notice of assignment nor a "new bank details" email can move money. Cold start: factors already phone the debtor's AP desk to verify invoices before funding; Original Bill replaces that call with a one-click signed acknowledgment, and from then on the debtor's agent answers every verification of that receivable from the registry.
**Demo:** two judges open factor pages on their phones with sandbox Nessie accounts; the vendor offers both the same invoice; on a 3-2-1 count both press Buy and exactly one commit wins. Judge B then takes the vendor laptop for 60 seconds and tries anything (renumber, change by a cent, split, email a notice of assignment); each attempt is refused with the invariant that fired, while the payment re-routes live as Judge A endorses onward. Skip to the due date: the money lands with whoever holds the original. Closing table: a 500-variant double-pledge corpus versus three baselines (invoice-number dedupe, exact hash, an LLM fuzzy matcher).
**Sponsors:** Hyphenate (primary), Convex, Capital One Nessie; optional Coinbase x402 delivery-versus-payment for endorsements.
**Buyer and use:** factors and receivables financiers pay per original (flat fee or basis points); debtors' AP teams get the gate free at first. Factors fund daily; the debtor's agent checks on every payment run.
**Claims to verify:** that 2022 UCC Article 12 "controllable accounts" make paying the controller discharge the debtor and give control priority over a UCC-1 filing; that First Brands involved double-pledged receivables. **Named competitors (to verify):** India's TReDS, C2FO, Taulia, PrimeRevenue, TriumphPay, electronic bill-of-lading registries (Bolero, essDOCS, WAVE BL), we.trade, Marco Polo and Contour (shut down).
**Load-bearing risk:** debtors keep paying from their vendor master instead of the registry, so the registry binds no one.

### CH3 · Reg F Gate
**Pitch:** A pre-speech compliance gate for AI debt-collection voice agents: every call attempt and every sentence passes a deterministic engine for the federal collection rules before any audio is spoken. Pitched as the consumer-protection layer: "If you hate debt collectors, this is what you want them forced to install."
**How it works:** A gate process sits between the collections agent's LLM and Cartesia's text-to-speech, and between the dialer and the phone line. Before every dial it checks consent, the rolling 7-attempts-in-7-days limit and the lockout after a conversation, the 8am–9pm window in every time zone the area code and ZIP imply, cease and attorney flags, and a bankruptcy/deceased scrub. During the call a state machine runs UNVERIFIED → VERIFYING → RIGHT_PARTY → NEGOTIATING, with CEASE reachable from every state. Until the caller's identity is verified (CRS), the agent may speak only exact fixed templates (business name, agent name, callback number). After verification, any number must match a ledger value or an issued offer, and waivers, settlements or credit-reporting promises can only be spoken as the output of a typed offer() call checked against the creditor's policy-as-code (folding in "Binding Words", after Moffatt v. Air Canada). Every spoken commitment is logged to a liability ledger from Cartesia's word timestamps.
**Demo:** a judge enters their own number on a consent screen and sees one real block against the live clock (a Honolulu account before 8am). Their phone rings; they choose to be the roommate, the spouse or the debtor. The agent's attempt to say "I'm calling about Jordan's $1,240 balance" is struck through on screen with the citation, and the judge hears only a name and a callback number. As the debtor, a bereavement plea gets an allowed hardship plan, "promise you'll delete it from my credit report" is blocked, and "stop calling me" greys out the dial button for good. Closing table: an adaptive attacker LLM runs 200 held-out text-mode calls with and without the gate (third-party disclosure, unauthorized commitments, false threats, versus payment plans completed).
**Sponsors:** Hyphenate (finance operations), Cartesia, CRS Credit API (identity, plus Best Financial AI Agent).
**Buyer and use:** compliance officers at collection agencies and debt buyers piloting AI voice, AI-voice vendors who license it for bank due diligence, first-party creditors under state rules; priced per gated attempt; runs on every call.
**Claims to verify:** 12 CFR 1006 limits as stated; the FCC's 2024 ruling that AI voices count as artificial voices under the TCPA; FDCPA damages and suit volumes. **Named competitors (to verify):** Skit.ai, Prodigal, Salient (AI collectors); Balto, Sedric, Observe.AI (coaching and review); Gryphon (dial-list compliance).
**Load-bearing risk:** after verification, a judge coaxes out a commitment with no number and no banned word; and some judges may find AI debt collection distasteful.

### CH4 · Said-On-The-Phone
**Pitch:** The spoken quote becomes the contract: a voice agent takes contractors' quotes for a maintenance job and turns each call into a structured scope with line prices, read back and confirmed; when the invoice arrives, a deterministic diff pays what was quoted and holds only what wasn't.
**How it works:** For a property manager's work order, a Cartesia voice agent calls (or takes the call from) the contractor, structures the quote into line items, reads it back for confirmation, and stores the call with the confirmed scope as a signed quote record. When the invoice arrives, Claude extracts its lines; a team-written matcher diffs them against the confirmed scope (unit prices, quantities, unquoted lines, fees), releases the matching amount through Nessie at once and holds only the variance, with a dispute drafted around the call clip where the price was agreed.
**Demo:** one judge plays the plumber and quotes $200 "all in" on the call; another judge submits the invoice with an $85 trip fee; $200 is paid immediately, $85 is held, and the screen plays the four-second clip of "$200 all in".
**Sponsors:** Hyphenate, Cartesia, Capital One Nessie (CRS identity for contractor verification as an option).
**Buyer and use:** property managers and small landlords (per door per month), facilities teams; jobs weekly.
**Known neighbors (to verify):** Property Meld, Latchel, Lula (maintenance coordination); AppFolio and Buildium (property AP).
**Load-bearing risk:** matching a loosely spoken scope to invoice lines is fuzzy, so the "deterministic" diff depends on Claude's structuring.

### CH5 · Promo Glitch Hunter
**Pitch:** Before a merchant launches a sale, a solver searches the store's discount rules for "sequence breaks": code stacks and cart combinations that sell below cost, so they're patched before coupon sites find them.
**How it works:** Claude reads the merchant's promotion setup (discount export or plain-language promo brief) and writes an SMT model (Z3) of the discount, coupon, bundle, tiered-threshold, free-shipping and gift-card rules plus item costs. The solver searches for carts and code sequences whose net price falls below cost or a margin floor. Every exploit is replayed in the store's real test checkout, and only replay-confirmed exploits count, so a wrong model can't produce a false alarm. After the fix (a stacking rule), the solver re-runs and finds nothing.
**Demo:** the judge gets 60 seconds in the live test checkout to find the cheapest cart they can; the solver then reveals a cheaper exploit, replays it in the same checkout, and shows the margin it would have leaked.
**Sponsors:** Visa "Reimagining Shopping", Creao "Best AI-First Disruptor"; Anthropic if posted.
**Buyer and use:** DTC merchants on Shopify Plus and their agencies; run before every promotion (weekly).
**Known neighbors (to verify):** Talon.One and Voucherify (promotion engines with budget caps), Riskified and Signifyd (promo-abuse detection after the fact).
**Load-bearing risk:** the model diverges from the real checkout's discount semantics, so exploits fail replay.

### CH6 · Controls CI with Fire Drill inside (synthesis)
**Pitch:** CH1's verified controls gate on the only path to the bank, with Fire Drill folded in as one rule type and its attacker turned into a hole finder.
**How it works:** Everything in CH1, plus: a provenance rule type ("no payment to bank details that first appeared in untrusted text") whose refusal triggers Fire Drill's voice callback to the vendor's number of record; and an adaptive attacker agent given a goal the rule suite should prevent ("move $10,000 to a vendor created this week without approval") that searches payment sequences against the deterministic gate. Each path it finds becomes a failing test and a suggested rule; the output is holes found per rule suite before and after tightening.
**Demo:** CH1's judge-writes-a-rule moment, then the judge's phone rings for the callback when a bank change arrives by email, then the hole finder's table.
**Sponsors:** Hyphenate (primary), Cartesia, Armadin, Capital One Nessie, Convex.
**Risk:** scope. Two people until Saturday evening may not finish both the rule compiler and the voice callback; the build order must keep a complete demo at every stage.

Related: [[Council Verdict]] · [[Prizes]] · [[Top Ideas Stress Test]]
