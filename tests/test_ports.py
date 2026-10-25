"""Sponsor ports with their in-memory adapters.

Every sponsor integration sits behind one of these ports, so the core demo
runs offline and any sponsor adapter can be dropped without breaking it.
"""
from firedrill.payments import MemoryRail
from firedrill.remediate import FakeCodeAgent, PatchDiff
from firedrill.trace import MemorySink, TraceEvent


def test_memory_rail_records_transfers():
    rail = MemoryRail()
    receipt = rail.transfer(invoice_id="INV-1", account="ACCT-APPROVED", amount=10_000)
    assert receipt.ok is True
    assert rail.transfers[0].account == "ACCT-APPROVED"


def test_fake_code_agent_returns_a_structural_patch():
    patch = FakeCodeAgent().patch(failing=[], policy="", train_families=["pre-close-urgency"])
    assert isinstance(patch, PatchDiff)
    # Least-privilege first: bank changes and payments need elevation.
    assert patch.tool_scope["change_vendor_bank_details"] == "requires_verification"
    assert patch.tool_scope["approve_payment"] == "requires_verification"
    assert patch.tests  # a regression test always ships with the patch


def test_memory_sink_collects_events_in_order():
    sink = MemorySink()
    sink.emit(TraceEvent(drill_id="d1", turn=1, kind="message", data={"channel": "invoice"}))
    sink.emit(TraceEvent(drill_id="d1", turn=2, kind="tool_call", data={"tool": "lookup_vendor"}))
    assert [e.turn for e in sink.events] == [1, 2]
