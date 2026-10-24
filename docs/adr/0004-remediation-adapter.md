# Remediation goes through a swappable code-agent adapter

The Remediator depends on a code-agent port with one method (write a Patch and a regression test from failing Drills). Claude Code is the production adapter; the Factory Droid SDK is an alternative adapter behind the same port.

**Why:** two prizes pull in opposite directions. Claude Code is the Anthropic story; the Factory Droid SDK is a $2K track. A port lets us demo either without touching the remediation logic, and decide which to feature late.

**Consequence:** the Remediator never imports a code agent directly. Two adapters justify the seam (ADR exists because the choice is real and late-bound).
