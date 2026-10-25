# Hold out whole tactic families, and commit them before patching

Remediation sees only the training Tactic Families. At least one whole Held-out Family is withheld and used only in the re-run. Before any Patch is written, a Merkle root over the held-out Drills is committed to the public GitHub repo with a timestamp; the Drills are revealed after the re-run.

**Why:** a random split leaks wording across the split (soft contamination), so it tests paraphrase, not generalization. And because we write both attacker and scorer, "you re-ran until it passed" is the obvious objection; a pre-commit the audience can verify answers it. Reversing this later would invalidate every number already shown.

**Consequence:** the harness must label every Tactic Card with a family and partition by family, and the commit step must run before Remediation in the pipeline.

**Amendment (24 Oct 2026): training drills are published.** `records/`, attacker turns included, is in the repository, so anyone can re-score a drill from its final ledger instead of taking the numbers on trust. This decision covers training families only. A held-out family is still committed as a salted Merkle root before any patch it tests exists, and its drills are published only when they are revealed. Publishing the training wording does carry a cost: a future patch could be tuned to it. That cost is exactly the reason held-out families exist.
