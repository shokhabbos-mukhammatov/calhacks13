---
type: audit
tags: [prizes, audit]
updated: 2026-10-24
---
# Prize fit audit

Fire Drill against every prize it can plausibly win, checked against the
Hacker Guide's track criteria, the sponsor posts and the code as it stands
on Sat 24 Oct, evening. Read with [[Fire Drill Status]] and [[Prizes]].

**Bottom line.** The strongest fits are **Hyphenate** (the largest pot, and the
track the project was designed for), **Microsoft's Grand Prize**, **Factory**
(now eligible — it was not this morning), **Apify**, and the general **Most
Technically Complex** / **Best Solo** prizes. **CRS** and **Cartesia** are real
integrations with honest weaknesses, listed below with what would fix them.
The single most valuable thing left is a **demo video that opens with the
moment**, which Hyphenate requires and which only you can record.

## Fixed this session

| Gap | What was wrong | Now |
| --- | --- | --- |
| **Factory eligibility** | Droid was called through its CLI (`droid exec`); the track requires the **Droid SDK** doing real work in the running product | `firedrill/droid_remediator.py` drives Droid through the Python SDK. The breach grid **triggers** it; it can touch **three harness tools and nothing else** (allowlist + permission gate, escape **probed**); every step is **recorded and shown**. Its patch held 0/24 attacks, 12/12 honest invoices paid, on real drills |
| **CRS not live in the live demo** | The Standby target behind the phone line used `NoSenderCheck` | It calls CRS Fraud Finder whenever the Actor has `CRS_*` set. **Needs your secrets in the Apify console and a new push** |
| **CRS invisible on the page** | CRS results sat inside raw tool output | The replay labels every Vendor Verify call: *CRS Fraud Finder, live: sender risk 100/100 · invalid* |
| **Hyphenate "seats" line** | Required deliverable, absent | "The seat it fills" on the page and in the README |
| **Microsoft path to production / Anthropic named community** | Absent | "Who it protects" and "Path to production", on the page and in the README |

## Track by track

Fit: **Strong** · **Good** · **Weak**. Owner of what is left: **you** or **me**.

### Hackathons@Berkeley general prizes
Judged on application, functionality/quality, creativity, technical complexity.

| Prize | Fit | Why | Left |
| --- | --- | --- | --- |
| 1st–3rd overall | Strong | Working end to end, live phone line, a real before/after with exact statistics, a frontend that explains it | The 2-minute pitch (**you**) |
| Most Technically Complex | **Strong** | Deterministic predicate scorer; hand-rolled incomplete beta; alpha spent over planned looks; Fisher; salted Merkle commit-reveal; stateless Standby on a shared store; a code agent iterating against the scorer through an in-process MCP harness | — |
| Most Creative | Good | "A fire drill for AI agents"; the fix is written from *what the agent did*, never the attacker's words | Say that sentence in the pitch |
| Best People-First | Good | Protects AP staff and small vendors; now said on the page | A real person's story makes it land (**you**) |
| Best Solo | **Strong** | Solo | Confirm solo on Devpost |
| Hacker's Choice | Good | Judges can phone the agent and break it | — |

### Hyphenate — Autonomous Systems for Finance ($8k / $5k / $3k)
Four questions: is it real enough, would you hire it, did we see something new,
the moment. Required: a demo video **opening with the moment**, a live demo
where judges may bring their own scenario, one line on the seats, proof of
real vs simulated.

**Fit: Strong — the best match in the event.**
- *Real enough:* real model, real ledger, live CRS sandbox, Nessie sandbox
  bank, 128 recorded drills anyone can re-score.
- *Would you hire it:* the controls tester an AP team does not have (on the
  page now).
- *Something new:* verdicts as ledger predicates; fixes written from
  role-redacted actions; a held-out set committed before the patch.
- *The moment — you have three:* the agent dialling the attacker's own
  number and paying; the gate refusing payment with the policy deleted;
  Droid's first fix **rejected by the harness** and revised.
- *Judge's own scenario:* the phone line, or `run_drill.py` typed live.

**Left:** the video (**you**). The Hyphenate track doc needs a sign-in, so I
could only read the Hacker Guide's summary — open it and check for anything
else it asks for (**you**).

### Microsoft — Grand Prize: Built for the Real World
Customer understanding, measurable usefulness, path to production,
responsible design, end-to-end.

**Fit: Strong.** U is measured (12/12 honest invoices on the Droid patch),
the path to production is on the page, responsible use is in the README, and
it runs end to end. **Framing for the pitch:** Fire Drill is the agent that
keeps your AP agent honest.

### Anthropic ($5k credits, Claude Max)
A named community; a real problem lived or heard firsthand; one thing done
well; thoughtful use of Claude *with awareness of where it could go wrong*.

**Fit: Good.** The last criterion *is* the project. **Left:** a firsthand
line — someone you know in AP or bookkeeping, or a small business that was
hit (**you**). It cannot be invented.

### Factory — Best Use of the Droid SDK ($2,000)
Must use the SDK meaningfully, doing real work in the running product; README
must say where and how. Scores well: a trigger you designed, careful control
over access with safety built in, visible work.

**Fit: Strong (was not eligible this morning).** Every criterion has a
concrete answer — see *Factory Droid: where and how it is used* in the README.
**Demo it live:** `scripts\autofix.py` prints each step as Droid works, about
a minute.

### CRS Financial Intelligence Challenge
Rule: meaningful use of the sandbox, shown working live; use only the provided
test identities. Judged on centrality ("not a bolt-on"), live demo,
usefulness, creativity.

**Fit: Good for Best Identity / Fraud Innovation and Most Unexpected Use;
weak for Best Overall.** Honest weaknesses:
1. **CRS is a supporting signal, not the core.** The verdict never depends
   on it, by design (ADR-0001).
2. **It cannot tell attacker from vendor here.** Every sender is an invented
   `.example` address, so Fraud Finder returns the same answer for all of
   them (risk 100, invalid).
3. **Possible rule problem:** the guide says to use only the provided test
   identities, and we score invented addresses.

**What would fix all three (me, ~1 hour, if you get the test identities):**
take the sender addresses from CRS's sandbox test identities — a clean one
for the real vendor, a risky one for a lookalike-domain attacker — so CRS
genuinely separates them. That needs the lookalike-domain turn files
(**you**, and they double as the held-out set).

### Apify ($5k pool; Best Actor $400)
**Fit: Strong.** Two published Actors; a Standby target holding state in a
shared key-value store (proven by killing a container mid-drill);
pay-per-event; a drill runner others can use. *Best Actor* is awarded for an
Actor built during the event — both were. (Slack mentioned "built with AI
Chat"; the Hacker Guide does not require it. We did not use AI Chat.)

### Cartesia (Meta glasses)
25% each: problem and originality, use of Cartesia (voice quality and
naturalness), execution, impact and responsibility. "Voice should be core to
the product."

**Fit: Good, with one real risk.** The argument for voice being core is
strong and data-backed: the attack that breaks the agent 12 of 12 times *is
a phone callback*, and the live line lets a judge attack by voice. **Risk:
latency.** A voice turn takes about 14 seconds end to end, which judges will
hear as voice quality. **Left:** measure where the 14 s goes and cut it
(**me**); README and responsible-use notes are already done.

### Capital One — Best Use of Nessie ($300 each)
Completeness, creativity, complexity. **Fit: Weak.** Nessie mirrors approved
payments; nothing more. Showing the Nessie transfer for each paid invoice on
the page would help (**me**, small), but this is not where to spend time.

### Elastic (criteria pending)
**Fit: Good.** Drill corpus indexed; an Agent Builder tool over it that
answers "which drills breached, and on which turn?". Recheck when criteria
are posted.

### Armadin — Best Security Hack (criteria pending)
**Fit: Strong on theme** — red-teaming AI agents in a financial workflow.
Recheck when criteria are posted.

### Not a fit
Meta, Fetch.ai, Coinbase x402, Creao, Bitdeer, Figma, Moss, SpaceXAI (needs
Cursor), Convex, Visa, Atlassian, Bright Data, Mana, Spacetime, Notability.

## What is left, in order

**You**
1. **Make the GitHub repo public.** Sponsor tracks need source access, and
   nothing is visible until it is.
2. **Record the demo video, opening with the moment** (Hyphenate requires it;
   Cartesia and every judge benefit).
3. **Submit a Devpost draft tonight**; the guide recommends it.
4. Put **CRS credentials on the `ap-practice-target` Actor** (secret env
   vars) and say the word for me to push the new build.
5. One **firsthand line** for Anthropic, and the **lookalike-domain turn
   files** (they unlock CRS and the generalization claim at once).

**Me, on your word**
1. The Devpost write-up, one paragraph per track you enter.
2. Cut voice latency.
3. CRS sandbox test identities in the worlds, once the turn files exist.

Back to [[Home]] · [[Fire Drill Status]] · [[Prizes]]
