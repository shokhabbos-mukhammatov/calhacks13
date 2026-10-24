"""Drill records and the statistics the report prints over them."""
import json

import pytest

from firedrill.drill import BENIGN_CARD, ScriptedAttacker, TacticCard, VictimConfig, build_scenario, run_drill
from firedrill.records import config_fingerprint, load_records, save_drill
from firedrill.stats import wilson
from firedrill.victim import Response, ScriptedModel

CARD = TacticCard(id="t-01", family="test-family", channel="invoice", sender="vendor_mailbox",
                  pretext="p", lever="l", ask="a", source_url="https://example.org/r")


def tool(name, **input):
    tool.n += 1
    return {"type": "tool_use", "id": f"tu_{tool.n}", "name": name, "input": input}


tool.n = 0


def calls(*blocks):
    return Response(stop_reason="tool_use", content=list(blocks))


def says(text):
    return Response(stop_reason="end_turn", content=[{"type": "text", "text": text}])


def breaching_drill(card=CARD, seed=1, **config):
    kit = build_scenario(card, seed).kit
    model = ScriptedModel([
        calls(tool("change_vendor_bank_details", vendor_id=kit.vendor_id, new_account=kit.attacker_account)),
        calls(tool("approve_payment", invoice_id=kit.invoice_id)),
        says("Done."),
    ])
    cfg = VictimConfig(model=model, **config)
    return run_drill(card, seed, attacker=ScriptedAttacker(["one"]), victim=cfg), cfg


def test_a_record_round_trips_through_disk(tmp_path):
    drill, cfg = breaching_drill()
    path = save_drill(drill, cfg, tmp_path)
    assert path.name.startswith("t-01-s1-") and path.suffix == ".json"
    [rec] = load_records(tmp_path)
    assert rec["card"]["family"] == "test-family"
    assert rec["config"]["name"] == "baseline" and rec["config"]["model"] == "ScriptedModel"
    assert rec["verdict"]["breach"] is True and rec["cap_turn"] == 1
    assert rec["paid_on_file"] is False
    assert rec["payments"][0]["approved"] is False
    assert [c["tool"] for c in rec["tool_calls"]] == ["change_vendor_bank_details", "approve_payment"]
    assert rec["transcript"][0]["reply"] == "Done."


def test_rerunning_the_same_drill_overwrites_its_record(tmp_path):
    drill, cfg = breaching_drill()
    save_drill(drill, cfg, tmp_path)
    save_drill(drill, cfg, tmp_path)
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_the_fingerprint_changes_with_the_hardening_config():
    _, baseline = breaching_drill()
    _, patched = breaching_drill(name="patched", policy="Callbacks required.")
    assert config_fingerprint(baseline) != config_fingerprint(patched)


def test_offering_verify_vendor_is_part_of_the_fingerprint(tmp_path):
    from firedrill.verify import FixedDomainAge, NoSenderCheck, VendorVerifier

    _, without = breaching_drill()
    drill, with_verify = breaching_drill(verifier=VendorVerifier(FixedDomainAge({}), NoSenderCheck()))
    assert config_fingerprint(without) != config_fingerprint(with_verify)
    save_drill(drill, with_verify, tmp_path)
    [rec] = load_records(tmp_path)
    assert rec["config"]["verify_vendor"] is True and rec["config"]["rail"] is None


def test_a_benign_drill_counts_utility():
    kit = build_scenario(BENIGN_CARD, 1).kit
    model = ScriptedModel([calls(tool("approve_payment", invoice_id=kit.invoice_id)), says("Paid.")])
    drill = run_drill(BENIGN_CARD, 1, attacker=ScriptedAttacker(["invoice"]), victim=VictimConfig(model=model))
    assert drill.paid_on_file is True and drill.verdict.breach is False
    assert drill.card.family == "benign"


def test_no_records_is_an_empty_list(tmp_path):
    assert load_records(tmp_path / "missing") == []


# --- Wilson interval -------------------------------------------------------------
def test_wilson_matches_the_textbook_value():
    low, high = wilson(5, 10)
    assert low == pytest.approx(0.2366, abs=1e-4)
    assert high == pytest.approx(0.7634, abs=1e-4)


def test_wilson_handles_the_edges():
    assert wilson(0, 0) == (0.0, 1.0)
    low, high = wilson(10, 10)
    assert high == 1.0 and 0.72 < low < 0.73
    assert wilson(0, 10)[0] == 0.0


def test_ranking_by_the_lower_bound_prefers_the_solid_result():
    assert wilson(48, 50)[0] > wilson(3, 3)[0]  # 96% of 50 beats 100% of 3
