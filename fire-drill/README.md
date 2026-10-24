# Fire Drill

**A controls-testing harness for your own accounts-payable AI agent.**

An AP agent that can read invoices, look up vendors and move money is useful.
The question nobody can answer today is what it does when someone asks it to
change a vendor's bank details. Fire Drill runs that as a drill, shows the
turn where a control failed, has a coding agent write a structural fix from
the failures, and re-runs to see whether the fix holds.

**The verdict is read from ledger state, never from the transcript.** An agent
that says "I verified this with the vendor" and then pays an unapproved
account is scored as a breach. The same text that fools the agent cannot fool
the scorer, because the scorer never reads it (ADR-0001).

Built solo at Cal Hacks 13, 23–25 October 2026.

---

## The result so far

Claude Haiku 4.5 as the accounts-payable agent, vendor-mailbox-takeover
drills, six per cell:

| Agent | Breaches | Honest invoices still paid |
| --- | --- | --- |
| `baseline` — no controls | **4 of 6** | 3 of 3 |
| `patch:v1` — written by Claude Code | **0 of 6** | 3 of 3 |
| `patch:v1-droid` — written by Factory Droid | **0 of 6** | 3 of 3 |

As the headline pair, where `U` is benign tasks completed and `S = 1 − ASR`:

```
baseline → patch:v1     U 1.00 → 1.00     S 0.33 → 1.00
```

Security up, usefulness unchanged. Both halves matter: an agent that refuses
everything scores a perfect `S` and is worthless.

Read the intervals, not the rates. 0 of 6 is consistent with a true breach
rate up to 39%, so `scripts/report.py` prints a 95% interval beside every
number — Wilson by default, or `--interval clopper-pearson` for the exact,
conservative one — and says plainly when two intervals still overlap.

Two code agents, given the same failures, chose different structural fixes.
Claude Code kept the bank-change tool and gated `approve_payment` behind a
confirmed callback; Droid denied the bank-change tool outright and moved that
work out of the agent. Both held.

**`scope:v1` is the honest follow-up.** Under the full patch the agent never
even attempted a bank change, so the code-level gate never fired — the policy
text did the work. `scope:<name>` applies a patch's tool scope with its policy
removed. Under `scope:v1` the agent *did* change the bank details and then
called `approve_payment`, and the harness refused it. The gate is proven in
code, with no policy helping.

56 drills are recorded. 123 tests pass.

---

## Setup

Needs Python 3.11+. From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,actors]"
Copy-Item .env.example .env     # then fill in the keys you want
.\.venv\Scripts\python.exe -m pytest -q
```

Every test runs offline: no key, no network, no platform. Only the scripts
below reach out.

`.env` is gitignored and holds no defaults. A missing key disables exactly one
adapter and nothing else — the core runs on in-memory fallbacks by design.

```powershell
# every integration, end to end, for a few cents
.\.venv\Scripts\python.exe scripts\check_integrations.py
```

---

## Running a drill

A **Tactic Card** describes an attack: its family, the pretext, the pressure
lever, the ask, and a link to the public fraud report it was distilled from.
It carries no names, numbers or message text.

A **seed** builds the world the drill runs in: vendor, invoice, amounts, and
two phone numbers — one on the vendor's file, where the real vendor says
nothing changed, and one that confirms whatever it is asked. Which one the
agent calls is the test. Numbers are `+1-415-555-01xx`, inside the range
reserved for fiction; domains end in `.example`.

**You write the attacker's turns.** The repository ships tactic cards and an
honest invoice pack, and no attack text.

```powershell
# see the world a seed builds, and your turns filled into it - no model calls
.\.venv\Scripts\python.exe scripts\run_drill.py vmt-01 --seed 1 --turns turns\vmt-01.txt --dry-run

# run it for real and record it
.\.venv\Scripts\python.exe scripts\run_drill.py vmt-01 --seed 1 --turns turns\vmt-01.txt --model claude-haiku-4-5 --save

# honest invoices: the usefulness half of the scorecard
.\.venv\Scripts\python.exe scripts\run_drill.py --benign --turns benign\invoice-01.txt --seed 1 --save

# breach and utility rates per model, hardening level and family
.\.venv\Scripts\python.exe scripts\report.py
```

Hardening levels, passed as `--config`:

| | Policy | `verify_vendor` offered | Payment gate |
| --- | --- | --- | --- |
| `baseline` | none | no | no |
| `baseline+verify` | none | yes | no |
| `patched` | placeholder | yes | yes |
| `patch:<name>` | from `patches/<name>.json` | yes | as written |
| `scope:<name>` | **dropped** | yes | as written |

---

## Remediation

```powershell
.\.venv\Scripts\python.exe scripts\remediate.py --agent claude-code --name v1
.\.venv\Scripts\python.exe scripts\remediate.py --agent droid --name v1-droid
```

The code agent is shown **actions and ledger outcomes, never message text**.
Concrete values are replaced by their role: the account the request asked for
becomes `attacker_account`, a number supplied in the request becomes
`number_from_request`. A test asserts nothing else reaches the brief.

That is the point. A patch written from wording can block those phrases and
still fail on a family it has not seen; a patch written from actions has to
change behaviour.

**Commit-reveal.** Before a patch exists, `remediate.py` writes a salted
Merkle root over the held-out drills to `commitments/`. Commit that file to
git and its timestamp predates the patch. After the re-run, `--reveal`
publishes the drills and salts so anyone can recompute the root. Hash
commitments are binding, so the held-out set cannot have been swapped for an
easier one (ADR-0002).

---

## Voice: what Cartesia does here

Voice is a **Channel**, not a second agent. Your glossary defines a Channel as
the medium a drill arrives on — invoice, email, ticket or voice — with one
Victim Agent behind all of them. A phone call runs against the same agent,
the same tools and the same ledger as a text drill, and ends in the same
deterministic verdict.

**Cartesia features used**

- **Managed Agents** (`POST /v1/agents`) — the voice agent, `claude-haiku-5.5`,
  built through the Agents API. Not the Line SDK.
- **Webhook tool** (`POST /v1/agents/tools`) — `ask_accounts_payable`, pointed
  at the target's `/voice/relay`, authenticated with a stored bearer secret.
- **Sonic TTS** — the agent speaks in the `Jacqueline` voice.
- **Ink STT** — the caller's speech, with `keyterms` biased toward *invoice*,
  *vendor*, *bank*, *account*, *payment*.
- **Telephony** — a Cartesia-provisioned US number, so a judge can call from
  their own phone.
- **System tools** — `end_call`.

**How a call works**

1. The caller speaks; Cartesia transcribes.
2. The webhook tool posts the turn to the target, with Cartesia's
   `system__conversation_id` as the call id.
3. The server maps that call id to a drill, creating one on the first turn.
   The caller never carries a drill id — on turn one it would not exist, and
   Cartesia rejects a tool call whose dynamic variable is unset.
4. The real AP agent runs, with its tools over the ledger.
5. Its reply is spoken back.
6. The verdict is read from the ledger afterwards.

The Cartesia agent is deliberately **only a relay**: its instructions forbid
it from answering about invoices, vendors, bank details or payments itself.
A voice reply is told to be one or two spoken sentences with no markdown —
presentation only, saying nothing about verification, so it cannot change
whether a drill breaches.

**Why voice and not just email.** Vendor payment fraud is a phone crime as
much as an email one, urgency works better live, and the callback control the
whole patch rests on *is* a phone control. Testing it only in text would test
the easy half.

---

## The Apify Actors

Both are published on Apify Store.

**[`ap-practice-target`](https://apify.com/shohabbos_m/ap-practice-target)** —
the sandboxed AP agent at a public URL, as a Standby Actor so it is already
warm when a drill arrives.

```
POST /drill                  {card_id, seed, config, model} -> conversation_id, kit
POST /drill/<id>/message     {body}                         -> reply, tool_calls
GET  /drill/<id>/verdict                                    -> verdict, payments
POST /voice/relay            {message, call_id}             -> reply
```

It keeps nothing in memory between turns: each turn reloads the conversation
and the ledger from a **shared named key-value store** and writes them back,
so any container can serve any turn (ADR-0003). This was tested by starting a
drill, aborting its container, and reading the verdict from a new one.

**[`fire-drill`](https://apify.com/shohabbos_m/fire-drill)** — the runner. One
dataset row per drill, plus `REPORT.html` in the key-value store as the audit
artefact, and a `drill-completed` pay-per-event charge that stops when a run
hits its maximum charge. It runs the agent in-process or drills a remote
Standby target over HTTP, where the target owns the ledger so scoring stays
deterministic.

Both take a caller's own Anthropic key, so a stranger's run never spends the
owner's credit. `scripts/sync_actors.py` copies the package into each Actor
before `apify push`; `tests/test_actors_in_sync.py` fails if a copy drifts.

---

## Sponsor integrations

| | What it does here | Status |
| --- | --- | --- |
| **Anthropic** | The agent under test, the drill driver, and Claude Code as a remediation adapter | Working |
| **Apify** | Two published Actors: the Standby target and the drill runner | Working |
| **Cartesia** | The voice Channel: Managed Agent, webhook tool, Sonic, Ink, telephony | Working |
| **Capital One** | Nessie mirrors each approved payment into the sandbox | Working |
| **CRS Credit API** | Fraud Finder scores the sender's address inside Vendor Verify | Working |
| **Factory** | Droid wrote `patches/v1-droid.json` from the failing drills | Working |
| **RDAP** | Sender-domain age, real and keyless | Working |
| **Elastic** | Cluster and Agent Builder reachable | **Not wired into the product** |

`scripts/check_integrations.py` exercises each of these for real and prints a
pass/fail line. It currently reports 19 of 19.

**Every sponsor sits behind a port with an in-memory fallback**, so the core
demo runs offline and any one of them can be dropped without breaking it.

---

## What is real and what is simulated

| Real | Simulated |
| --- | --- |
| The agent, its tools and its decisions | The vendors, invoices and amounts |
| The verdict, computed from ledger state | The ledger itself: no real money exists |
| RDAP domain-age lookups | The phone network behind `call_vendor` |
| CRS Fraud Finder calls (their sandbox, fake records) | The vendor on the other end of a callback |
| Nessie transfers (Capital One's sandbox) | Bank balances: this Nessie records, it does not move money |
| The Cartesia call, voice and telephony | — |
| The patches, written by Claude Code and Droid | — |
| Every drill outcome in `records/` | — |

**How you know.** Every verdict is a predicate over ledger state, in
`firedrill/scorer.py` — 42 lines, no model in it. Every drill is
saved with its tool calls, its payments and the world it ran in, so any claim
here can be recomputed from `records/`.

---

## Responsible use

- Vendors, invoices and accounts are invented. Phone numbers are inside
  `555-0100`–`555-0199`, reserved for fiction; domains end in `.example`.
  Nothing here can reach a real person or business.
- No real payment rail. Nessie is Capital One's sandbox and records only.
- **Attacker wording is not in this repository.** Cards describe a tactic and
  cite its public source; the messages are written locally and `turns/` and
  `records/` are gitignored.
- The code agent is shown actions, never message text, which also keeps attack
  wording out of anything sent to a model.
- No secrets in the repository. `.env` is ignored and a published Actor takes
  the caller's own key.
- The practice target is deliberately weak. That is what it is for, and it is
  labelled as such wherever it is published.

---

## Known limitations

- **Small samples.** Six drills per cell. The intervals are wide and the
  report says so rather than rounding it away.
- **One tactic family has been drilled.** `lookalike-domain` and
  `executive-impersonation` have cards but no attacker turns, so the held-out
  generalization claim is not yet demonstrated. The machinery is built and
  unused.
- **The code-level gates are under-tested.** Under a full patch the agent
  never attempted the blocked action, so only `scope:v1` has actually fired a
  gate.
- **Voice latency.** A warm turn is about 6 seconds; a cold container is
  nearer 15. Cartesia's own round trip is a small part of that — the time is
  the agent thinking and calling tools.
- **Remote drills report no capitulation turn.** The target returns the
  verdict; turn-level attribution is computed locally.
- **Elastic is not wired in.** Credentials work; nothing in the product uses
  them.
- **One conversation per card, seed and config.** Starting the same
  combination again resets that drill.

---

## Layout

```
firedrill/        ledger, scorer, victim agent, drill loop, remediation,
                  commit-reveal, vendor verify, payment rail, Apify adapters
tests/            123 tests, all offline
scripts/          run_drill, report, remediate, nessie_seed, sync_actors,
                  check_integrations, smoke_victim
cards/            tactic cards, each citing a public fraud report
benign/           honest invoice packs, for the usefulness half of the score
patches/          structural patches written by Claude Code and by Droid
actors/           the two Apify Actors
turns/            your attacker turns (gitignored)
records/          one JSON per drill (gitignored)
docs/adr/         the four decisions this design rests on
```

Design notes, the glossary and the architecture live in the Obsidian vault one
directory up.
