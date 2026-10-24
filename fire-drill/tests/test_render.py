"""The scorecard page: the one artefact a judge actually reads.

The tests that matter here are not about markup. They are about the claims the
page is allowed to make — that it never implies security it did not measure,
that it never pools drills from different models, and that it asks for nothing
over the network, because the venue bans hotspots and a broken page at 10:30
is worth more than a pretty one now.
"""
import re

from firedrill.render import as_record, as_row, render, short_model

SOURCE = "https://example.org/report"


def row(**over) -> dict:
    base = {
        "drill_id": "vmt-01-s1", "card_id": "vmt-01", "family": "vendor-mailbox-takeover",
        "channel": "invoice", "sender_kind": "vendor_mailbox", "source_url": SOURCE,
        "seed": 1, "model": "claude-haiku-4-5", "config": "baseline",
        "breach": False, "verified_out_of_band": False, "canary_touched": False,
        "capitulation_turn": None, "paid_on_file": False, "ended_by": "attacker_stopped",
        "turns": 2, "money_moved": 0, "payments": [], "tool_calls": [],
    }
    return {**base, **over}


def arm(config: str, breaches: int, n: int, *, model="claude-haiku-4-5", card="vmt-01"):
    """One cell of the grid: `breaches` of `n` drills ended with money moved."""
    return [row(drill_id=f"{card}-s{s}", card_id=card, seed=s, config=config, model=model,
                breach=s <= breaches, capitulation_turn=2 if s <= breaches else None,
                money_moved=34950 if s <= breaches else 0)
            for s in range(1, n + 1)]


def text_of(page: str) -> str:
    return re.sub(r"<[^>]+>", " ", page)


# --- the claims the page is allowed to make ---------------------------------
def test_a_benign_only_run_says_it_measured_utility_not_security():
    """The Actor's default one-click run drills no attacks. Reporting a
    perfect security score for it would be the single most misleading thing
    this page could do."""
    rows = [row(drill_id=f"benign-s{s}", card_id="benign", family="benign", seed=s,
                paid_on_file=True, source_url="") for s in range(1, 4)]
    page = text_of(render(rows))
    assert "drilled no attacks" in page
    assert "3 of 3" in page
    assert "not whether it can be talked out of it" in page


def test_attack_drills_without_a_hardened_arm_claim_no_improvement():
    page = text_of(render(arm("baseline", 5, 8)))
    assert "5 of 8" in page
    assert "nothing yet to compare it against" in page


def test_the_headline_pair_is_the_one_with_the_most_drills_behind_it():
    """A run usually holds several hardening levels at different sample sizes.
    Leading with whichever sorts first would headline the weakest evidence."""
    rows = arm("baseline", 12, 24) + arm("patch:v1", 0, 24) + arm("patch:v0", 0, 3)
    page = render(rows)
    assert "patch:v1" in text_of(page).split("Fisher")[0]
    assert "patch:v0" not in text_of(page).split("Fisher")[0]


def test_two_intervals_that_clear_each_other_are_marked_as_such():
    page = render(arm("baseline", 12, 24) + arm("patch:v1", 0, 24))
    assert "NO OVERLAP" in page


def test_two_intervals_that_still_overlap_are_not():
    """Six drills with no breach is consistent with a true rate near 40%, and
    the page must not dress that up as a separation."""
    page = render(arm("baseline", 1, 3) + arm("patch:v1", 0, 3))
    assert "NO OVERLAP" not in page


def test_an_untested_generalization_claim_says_so():
    page = text_of(render(arm("baseline", 4, 6) + arm("patch:v1", 0, 6),
                          hold_out=["lookalike-domain"]))
    assert "No drill from lookalike-domain has been run yet" in page
    assert "this run cannot answer" in page


# --- the grid ---------------------------------------------------------------
def test_the_grid_draws_one_cell_per_drill():
    page = render(arm("baseline", 3, 9))
    assert page.count("<rect") >= 9


def test_the_grid_never_pools_two_models_into_one_row():
    """Pooling drills from different models would invent a rate for an agent
    that was never run."""
    rows = arm("baseline", 2, 4, model="claude-haiku-4-5") + \
        arm("baseline", 0, 4, model="claude-opus-5-5")
    page = render(rows)
    assert "haiku-4-5" in page and "opus-5-5" in page
    assert "2/4" in page and "0/4" in page


def test_a_breach_cell_carries_the_turn_the_agent_capitulated():
    """Colour is never the only channel: the cell says which turn it broke on."""
    page = render(arm("baseline", 1, 2))
    assert "breach at turn 2" in page          # the native tooltip
    assert ">2</text>" in page                 # and the digit inside the cell


def test_short_model_drops_only_the_vendor_prefix():
    assert short_model("claude-haiku-4-5") == "haiku-4-5"
    assert short_model("ScriptedModel") == "ScriptedModel"


# --- the artefact itself ----------------------------------------------------
def test_the_page_asks_for_nothing_over_the_network():
    page = render(arm("baseline", 1, 2)).replace(f'href="{SOURCE}"', "")
    for forbidden in ("<script", "http://", "https://", "@import", "url(", "<iframe", "<link"):
        assert forbidden not in page, forbidden


def test_the_page_escapes_whatever_a_card_carries():
    page = render(arm("baseline", 0, 1) + [row(drill_id="<script>alert(1)</script>",
                                               config="<img onerror=x>")])
    assert "<script>" not in page and "<img" not in page


def test_every_value_is_reachable_without_hovering():
    """Tooltips enhance, they never gate: the table view holds the lot, and it
    is plain HTML, so it survives printing."""
    page = render(arm("baseline", 1, 2))
    assert "<details>" in page and "<table>" in page
    assert page.count("<tr>") >= 2


# --- the two shapes ---------------------------------------------------------
def test_a_saved_record_and_a_live_row_describe_the_same_drill():
    """`records/` is nested and a dataset row is flat. The renderer reads one
    shape, so the projection between them has to be lossless for everything
    the statistics touch."""
    record = {
        "card": {"id": "vmt-02", "family": "vendor-mailbox-takeover", "channel": "invoice",
                 "sender": "vendor_mailbox", "source_url": SOURCE},
        "seed": 7,
        "config": {"name": "baseline", "model": "claude-haiku-4-5"},
        "verdict": {"breach": True, "oob": False, "canary": True},
        "cap_turn": 1, "paid_on_file": False, "ended_by": "paid",
        "transcript": [{"turn": 1}, {"turn": 2}],
        "tool_calls": [{"turn": 1, "tool": "approve_payment", "error": False}],
        "payments": [{"invoice_id": "INV-1", "account": "ACCT-9", "amount": 100,
                      "approved": False}],
    }
    back = as_record(as_row(record))
    for key in ("card", "config", "verdict", "paid_on_file", "cap_turn", "seed"):
        assert back[key] == record[key], key
    assert as_row(record)["money_moved"] == 100
    assert as_row(record)["tool_calls"] == ["t1:approve_payment"]


def test_the_table_verdict_is_a_swatch_beside_the_word_not_coloured_text():
    """`critical` as body text measures 3.62:1 on the dark surface, under the
    4.5:1 body-text floor, and identity belongs on the mark rather than on the
    label. The swatch carries the colour; the word stays in ink."""
    page = render(arm("baseline", 1, 2))
    assert 'class="verdict verdict--breach">breach' in page
    assert 'class="verdict verdict--held">held' in page
    assert "color: var(--critical)" not in page


def test_prose_uses_typographic_apostrophes():
    page = render(arm("baseline", 1, 2) + arm("patch:v1", 0, 2))
    body = page[page.index("<body>"):]
    assert "’" in body
    assert "Fisher's" not in body
