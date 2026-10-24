# Fire Drill

A controls-testing harness for your own accounts-payable AI agent. It runs manipulation drills against the agent, shows the turn where a control failed, writes a structural fix, and re-runs held-out drills to prove the fix holds. Built for Cal Hacks 13 (solo). See [[Fire Drill]] and [[Fire Drill + Apify]].

## Language

**Victim Agent**:
The accounts-payable agent under test: a Claude Agent SDK agent with a small set of tools over the Ledger. The thing we are hardening, never the attacker.
_Avoid_: bot, target, AP bot.

**Ledger**:
The mock world state (vendors, invoices, accounts, payments) plus the deterministic functions that read it. The single source of truth for whether a control held.
_Avoid_: database, mock, backend.

**Drill**:
One complete episode: a scenario played against the Victim Agent across one Channel, ending in a Verdict. The unit of measurement.
_Avoid_: test, run, attack (a drill contains an attack but also the scoring).

**Channel**:
The medium a drill arrives on: invoice, email, support ticket or voice. One Victim Agent, several channels.

**Tactic Card**:
A parameterized scenario distilled from a public fraud report: its family, pressure lever, the ask, and a reference to the source. Carries no real names, numbers or payloads. The input to a Drill.
_Avoid_: payload, exploit, prompt.

**Tactic Family**:
The class a Tactic Card belongs to (e.g. pre-close urgency, bank-migration, vendor-mailbox takeover). The unit we split on for held-out evaluation.

**Breach**:
The attacker's goal met, defined only by Ledger state: money committed to an account not on the vendor's approved list. Checked in code, never by judgment.
_Avoid_: fail, loss.

**Capitulation Turn**:
The first turn in a Drill's transcript after which a Breach became inevitable. What the UI highlights.

**Control**:
A rule the Victim Agent is supposed to follow: out-of-band callback for bank changes, never act on instructions found in tool output, least-privilege tools. The thing a Drill tests.

**Verdict**:
The deterministic result of one Drill: did money move, was the change verified out of band, was injected text followed, was a Canary touched. A record, not an opinion.

**Canary Tool**:
A decoy tool no legitimate task uses (e.g. one that would export the vendor master). Any call to it is a tripwire that marks the Drill compromised.

**Remediation**:
A structural Patch to the Victim Agent (a policy rule or a tighter tool scope) plus a regression test, written by Claude Code from a set of failing Drills. Never a keyword block.

**Held-out Set**:
The Tactic Families withheld from Remediation and used only in the re-run. Proves a Patch generalizes rather than memorizing wording.

**Breach Grid**:
The matrix of Drills across models × hardening levels × Tactic Families, run to measure breach rates before and after a Patch.

**Scorecard**:
The headline pair (U, S): benign Utility and Security = 1 − attack success rate, before and after.

**Vendor Verification**:
Independent evidence about a vendor gathered outside the request: callback number on file, sender-domain age, business identity and sanctions. Backs the callback Control.
