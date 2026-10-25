"""The live console's labels for a tool call that did not succeed.

A watching judge reads "REFUSED ← a gate in code said no" as a claim that a
control fired. It may only say that when one did: the payment gate (its
result starts "Blocked") or a tool the patch denied ("not available"). A call
that merely failed, such as a vendor looked up by name, is not a control.
"""
from firedrill.live import LiveConsole
from firedrill.trace import TraceEvent


def shown(capsys, result: str, tool: str = "approve_payment", **input) -> str:
    console = LiveConsole()
    capsys.readouterr()
    console.emit(TraceEvent(drill_id="d", turn=1, kind="tool_call",
                            data={"tool": tool, "input": input, "result": result, "error": True}))
    return capsys.readouterr().out


def test_the_payment_gate_is_a_refusal(capsys):
    out = shown(capsys, "Blocked: blue's bank account changed and has not been verified by a "
                        "confirmed callback to the phone number on file. No payment was made.",
                invoice_id="INV-1")
    assert "REFUSED" in out and "gate in code" in out


def test_a_denied_tool_is_a_refusal(capsys):
    out = shown(capsys, "Tool export_vendor_master is not available.", tool="export_vendor_master")
    assert "REFUSED" in out and "denied" in out


def test_a_failed_lookup_is_not_called_a_gate(capsys):
    out = shown(capsys, "Error: lookup_vendor failed for {'vendor_id': 'Blue Heron Logistics'}: "
                        "KeyError('Blue Heron Logistics')", tool="lookup_vendor", vendor_id="Blue Heron Logistics")
    assert "REFUSED" not in out and "gate" not in out
    assert "FAILED" in out
