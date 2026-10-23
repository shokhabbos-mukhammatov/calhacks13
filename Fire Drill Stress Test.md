---
type: research
tags: [research]
---
# Fire Drill stress test

Oct 23, before opening. The Fire Drill section of the original stress test of every idea scored 7.6+.

## Fire Drill (8.0 → 7.3): pick it, with changes
**What holds up**
- The threat is real and expensive. Business email compromise caused about $3.05B in reported US losses in 2025, the second-largest category, including $30M+ with a confirmed AI link (IC3 2025, as reported). In 2024 Arup lost about $25M to a deepfake video call impersonating its CFO.
- Posted prizes: Hyphenate $16K, Cartesia, Armadin, CRS Identity/Fraud, Capital One Nessie and Elastic.
- It degrades gracefully. The poisoned-invoice attack loop runs on text, so voice can come last.

**Concerns and fixes**
1. **The breach can look rigged.** We write the AP agent's prompt, so we decide whether it falls. Current models resist simple attacks: in a LangWatch test, single-turn attacks got nothing from a banking agent, and it took a 50-turn adaptive attack to leak parts of its system prompt by turn 20. A sensibly prompted Claude agent probably won't fold to a judge in 35 seconds, and an obviously weak one looks like a strawman.
   **Fix: make both outcomes a win, and measure beforehand.** On Saturday night, run the autonomous attacker against a grid (model tier × prompt hardening) and show the breach rates. On stage the judge tries first. If the agent caves, show the turn where it broke. If it holds, say "now watch the attacker try 20 variants" and fast-forward the attacker against the same agent.
2. **Red-teaming agents isn't new.** Hamming AI (FinovateFall 2026) already places hundreds of adaptive social-engineering calls against bank voice agents. LA Hacks 2026 1st place went to security agents with a benchmark, and Armadin will draw other security teams. **Our difference:** finance-specific, ends in money actually moving, and closes the loop with a patch and a held-out re-run. Say that in the pitch.
3. **Hyphenate may read it as a security project.** Their prize is "Autonomous Systems for Finance". **Frame it as continuous controls testing.** Independently verifying changes to vendor bank details is a standard accounts-payable control that auditors test. Fire Drill tests that control when an agent runs AP and outputs the audit evidence. Make the AP agent genuinely useful too.
4. **Too many channels.** The note lists voice, email, invoice and ticket. Build two: the poisoned invoice (text, Friday night) and the voice call (when Akmal arrives). Add email only if there's time.
5. **The runtime Claude Code patch is slow on stage.** Let it stream while we talk, and cache the diff in case it stalls.

**Pull in from the dropped ideas**
- **Canary tools** (from [[Flytrap]]): give the AP agent decoy tools no legitimate task uses, such as `export_vendor_master` and `disable_callback`. Any call to one is a tripwire. It's cheap to build and gives a second detection signal.
- **The judge's phone rings** (from [[Phone-a-Human]]): the patch adds an out-of-band callback for bank changes, so make the callback real. After the patch, the agent phones the "real vendor", which is a judge's phone, to verify the change. The judge says they never asked for it, and the payment is blocked. That's a second live moment on the same Cartesia setup.
- **Payment proof on [[Capital One]] Nessie** (posted $1.2K) instead of the Visa sandbox, since Visa's prize is about shopping ([[Shortlist]] already suggests this).

**Two-person plan**
- **Fri night:** AP agent on a mock ledger with Nessie; attacker with the poisoned-invoice channel; scoring rubric. Spend 30 minutes getting the Cartesia Line number working, so voice is ready for later.
- **Sat day:** scorecard and trace UI, patch plus held-out re-run, canary tools, Elastic trace.
- **Sat evening (Akmal):** voice drill, callback to the judge, latency tuning. Overnight: run the breach grid.
- **Sun:** freeze, record the video, rehearse both outcomes of the judge call.

## Sources
- The threat is real and expensive. Business email compromise caused about $3.05B in reported US losses in 2025, the second-largest category, including $30M+ with a confirmed AI link (IC3 2025, as reported). In 2024 Arup lost about $25M to a deepfake video call impersonating its CFO.
1. **The breach can look rigged.** We write the AP agent's prompt, so we decide whether it falls. Current models resist simple attacks: in a LangWatch test, single-turn attacks got nothing from a banking agent, and it took a 50-turn adaptive attack to leak parts of its system prompt by turn 20. A sensibly prompted Claude agent probably won't fold to a judge in 35 seconds, and an obviously weak one looks like a strawman.
2. **Red-teaming agents isn't new.** Hamming AI (FinovateFall 2026) already places hundreds of adaptive social-engineering calls against bank voice agents. LA Hacks 2026 1st place went to security agents with a benchmark, and Armadin will draw other security teams. **Our difference:** finance-specific, ends in money actually moving, and closes the loop with a patch and a held-out re-run. Say that in the pitch.
- FBI IC3 2025 BEC figures, as reported: https://www.nacha.org/news/fbis-ic3-finds-almost-85-billion-lost-business-email-compromise-last-three-years · https://redsift.com/de/blog/fbi-ic3-2025-report-email-fraud
- Hamming AI red team (FinovateFall 2026): https://finovate.com/videos/finovatefall-2026-hamming-ai/
- LangWatch on multi-turn red teaming: https://langwatch.ai/blog/why-ai-red-teaming-is-broken-(and-how-we-fixed-it)

Back to [[Home]] · [[Fire Drill]]
