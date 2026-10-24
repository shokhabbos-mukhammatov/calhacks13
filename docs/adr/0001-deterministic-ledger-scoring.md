# Score drills from Ledger state, not an LLM judge

A Drill's Verdict is computed by deterministic functions over the Ledger's final state (did money reach a non-approved account, was the change verified out of band, was a Canary touched), never by asking a model to grade the transcript.

**Why:** the same injected text that manipulates the Victim Agent can manipulate an LLM judge, so an LLM verdict is not trustworthy evidence. AgentDojo (arXiv:2406.13352) made the same choice for the same reason. This is the project's main credibility claim, so it is fixed early.

**Consequence:** every scorable outcome must be reducible to a Ledger state check. A behaviour we cannot express as a state predicate cannot be a pass/fail Verdict; at most it is a soft label, reported separately and never as the Verdict.
