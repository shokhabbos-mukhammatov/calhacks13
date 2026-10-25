"""The OpenAI-compatible model adapter: OpenAI, DeepSeek and OpenRouter behind
the same Model port Claude uses, so a drill runs unchanged on any of them.

The agent keeps its conversation in one shape and the adapter translates it on
every call, both ways. These tests pin the translation, then run the real
agent loop through it on a fake transport, so no key is needed.
"""
import json

import pytest

from firedrill.drill import BENIGN_CARD, build_scenario
from firedrill.openai_compat import OpenAICompatModel, model_for, to_messages, to_tools
from firedrill.victim import TOOLS, AnthropicModel, ChannelMessage, MemoryStore, VictimAgent


class FakeTransport:
    """Answers each request with the next canned completion and keeps them all."""

    def __init__(self, *completions):
        self._completions = list(completions)
        self.requests = []

    def __call__(self, url, headers, body):
        self.requests.append({"url": url, "headers": headers, "body": json.loads(json.dumps(body))})
        return self._completions.pop(0)


def completion(content=None, tool_calls=None, finish="stop", model="gpt-test"):
    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    return {"model": model, "choices": [{"message": message, "finish_reason": finish}]}


def call(id, name, **args):
    return {"id": id, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}


def model(transport, name="openai/gpt-test"):
    return OpenAICompatModel(name, api_key="test-key", transport=transport)


def test_tools_become_functions_with_the_same_schema():
    fns = to_tools(TOOLS)
    assert [f["function"]["name"] for f in fns] == [t["name"] for t in TOOLS]
    first = fns[0]
    assert first["type"] == "function"
    assert first["function"]["parameters"] == TOOLS[0]["input_schema"]
    assert first["function"]["description"] == TOOLS[0]["description"]


def test_a_conversation_translates_in_order_with_ids_kept():
    messages = [
        {"role": "user", "content": "Invoice INV-1 is due."},
        {"role": "assistant", "content": [
            {"type": "text", "text": "Checking."},
            {"type": "tool_use", "id": "call_1", "name": "read_invoice", "input": {"invoice_id": "INV-1"}},
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "call_1", "content": '{"amount": 5}'},
        ]},
    ]
    out = to_messages("You are AP.", messages)
    assert [m["role"] for m in out] == ["system", "user", "assistant", "tool"]
    assert out[0]["content"] == "You are AP."
    assert out[2]["content"] == "Checking."
    assert out[2]["tool_calls"] == [{"id": "call_1", "type": "function",
                                     "function": {"name": "read_invoice",
                                                  "arguments": json.dumps({"invoice_id": "INV-1"})}}]
    assert out[3] == {"role": "tool", "tool_call_id": "call_1", "content": '{"amount": 5}'}


def test_a_tool_call_comes_back_as_a_tool_use_block():
    t = FakeTransport(completion("Let me look.", [call("c1", "read_invoice", invoice_id="INV-9")], "tool_calls"))
    r = model(t).respond(system="s", messages=[{"role": "user", "content": "hi"}], tools=TOOLS)
    assert r.stop_reason == "tool_use"
    assert r.content == [{"type": "text", "text": "Let me look."},
                         {"type": "tool_use", "id": "c1", "name": "read_invoice", "input": {"invoice_id": "INV-9"}}]
    assert r.model == "gpt-test"


@pytest.mark.parametrize("finish, stop", [("stop", "end_turn"), ("length", "max_tokens"),
                                          ("content_filter", "refusal")])
def test_finish_reasons_map_to_the_stop_reasons_the_agent_reads(finish, stop):
    r = model(FakeTransport(completion("ok", finish=finish))).respond(system="s", messages=[], tools=[])
    assert r.stop_reason == stop


def test_unparseable_arguments_reach_the_agent_as_an_error_not_a_crash():
    bad = {"id": "c1", "type": "function", "function": {"name": "read_invoice", "arguments": "{not json"}}
    r = model(FakeTransport(completion(None, [bad], "tool_calls"))).respond(system="s", messages=[], tools=TOOLS)
    assert r.content == [{"type": "tool_use", "id": "c1", "name": "read_invoice",
                          "input": {"_unparsed_arguments": "{not json"}}]


def test_the_request_goes_to_the_provider_with_its_key_and_model():
    t = FakeTransport(completion("ok"))
    model(t, "deepseek/deepseek-chat").respond(system="s", messages=[], tools=TOOLS)
    req = t.requests[0]
    assert req["url"] == "https://api.deepseek.com/chat/completions"
    assert req["headers"]["Authorization"] == "Bearer test-key"
    assert req["body"]["model"] == "deepseek-chat"
    assert "cache_control" not in json.dumps(req["body"])


def test_names_route_to_their_provider():
    assert isinstance(model_for("openai/gpt-4.1-mini", env={"OPENAI_API_KEY": "k"}), OpenAICompatModel)
    assert isinstance(model_for("deepseek/deepseek-chat", env={"DEEPSEEK_API_KEY": "k"}), OpenAICompatModel)
    routed = model_for("openrouter/meta-llama/llama-3.3-70b-instruct", env={"OPENROUTER_API_KEY": "k"})
    assert routed._model == "openrouter/meta-llama/llama-3.3-70b-instruct"   # what records carry
    assert isinstance(model_for("claude-haiku-4-5", api_key="test"), AnthropicModel)


def test_a_missing_key_names_the_variable_to_set():
    with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
        model_for("deepseek/deepseek-chat", env={})


def test_an_unknown_provider_is_refused():
    with pytest.raises(ValueError, match="unknown provider"):
        model_for("acme/model-1", env={})


def test_the_real_agent_loop_runs_through_the_adapter():
    # The agent reads an invoice through a tool, gets the result back, and
    # answers. The second request must carry the tool result under the id the
    # model gave its call, or no OpenAI-format API would accept it.
    kit = build_scenario(BENIGN_CARD, 1).kit
    t = FakeTransport(
        completion(None, [call("call_A", "read_invoice", invoice_id=kit.invoice_id)], "tool_calls"),
        completion("Read it."),
    )
    ledger = build_scenario(BENIGN_CARD, 1).ledger
    agent = VictimAgent(ledger, model(t), MemoryStore())
    reply = agent.handle("d1", ChannelMessage(channel="invoice", sender="a@b.example",
                                              subject="Invoice", body=f"Please pay {kit.invoice_id}."))
    assert reply == "Read it."
    second = t.requests[1]["body"]["messages"]
    tool_msg = next(m for m in second if m["role"] == "tool")
    assert tool_msg["tool_call_id"] == "call_A"
    assert kit.invoice_id in tool_msg["content"]
    assert [m["role"] for m in second] == ["system", "user", "assistant", "tool"]
