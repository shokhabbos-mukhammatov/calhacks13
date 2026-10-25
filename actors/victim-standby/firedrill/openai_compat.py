"""Any OpenAI-compatible chat API as the agent under test.

The Victim Agent talks to its model through one port, `Model.respond`, and
keeps the conversation in one shape: content blocks, with `tool_use` and
`tool_result` (the shape AnthropicModel speaks natively). This adapter
translates that conversation to OpenAI chat messages on every call and the
reply back again, so the agent, its tools, the ledger and the scorer are the
same code whichever provider answers. That is the point: a drill measures the
agent you ship, and a breach is still read from the ledger, never the text.

Model names carry their provider, `<provider>/<model>`, and records keep the
full name, so a grid cell can never mix providers:

    openai/gpt-4.1-mini                 OPENAI_API_KEY
    deepseek/deepseek-chat              DEEPSEEK_API_KEY
    openrouter/<vendor>/<model>         OPENROUTER_API_KEY

A plain name with no provider is Claude, through AnthropicModel.

Plain HTTP, no SDK, like the Elastic adapter: one request shape is all this
needs, and the offline core stays free of another dependency.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Mapping

from firedrill.victim import AnthropicModel, Model, Response

# provider -> (chat completions URL, the environment variable holding its key)
PROVIDERS: dict[str, tuple[str, str]] = {
    "openai": ("https://api.openai.com/v1/chat/completions", "OPENAI_API_KEY"),
    "deepseek": ("https://api.deepseek.com/chat/completions", "DEEPSEEK_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1/chat/completions", "OPENROUTER_API_KEY"),
}

# What the agent loop reads: it keeps going only on "tool_use".
STOP_REASONS = {"stop": "end_turn", "length": "max_tokens", "content_filter": "refusal",
                "tool_calls": "tool_use", "function_call": "tool_use"}

Transport = Callable[[str, dict, dict], dict]


def to_tools(tools: list[dict]) -> list[dict]:
    return [{"type": "function",
             "function": {"name": t["name"], "description": t["description"],
                          "parameters": t["input_schema"]}} for t in tools]


def to_messages(system: str, messages: list[dict]) -> list[dict]:
    """The agent's conversation as OpenAI chat messages, in order. A tool
    result becomes a `tool` message under the id the model gave its call;
    block types this API has no place for are dropped."""
    out: list[dict] = [{"role": "system", "content": system}]
    for m in messages:
        content = m["content"]
        if isinstance(content, str):
            out.append({"role": m["role"], "content": content})
            continue
        if m["role"] == "assistant":
            text = "".join(b["text"] for b in content if b.get("type") == "text")
            calls = [{"id": b["id"], "type": "function",
                      "function": {"name": b["name"], "arguments": json.dumps(b["input"])}}
                     for b in content if b.get("type") == "tool_use"]
            msg: dict[str, Any] = {"role": "assistant", "content": text or None}
            if calls:
                msg["tool_calls"] = calls
            out.append(msg)
            continue
        for b in content:
            if b.get("type") == "tool_result":
                body = b["content"]
                if not isinstance(body, str):
                    body = "".join(x.get("text", "") for x in body)
                out.append({"role": "tool", "tool_call_id": b["tool_use_id"], "content": body})
            elif b.get("type") == "text":
                out.append({"role": "user", "content": b["text"]})
    return out


def from_choice(choice: dict) -> tuple[str, list[dict]]:
    """A completion's first choice as the agent's stop reason and blocks."""
    msg = choice.get("message") or {}
    blocks: list[dict] = []
    if msg.get("content"):
        blocks.append({"type": "text", "text": msg["content"]})
    for c in msg.get("tool_calls") or []:
        raw = c["function"].get("arguments") or "{}"
        try:
            args = json.loads(raw)
        except json.JSONDecodeError:
            # Kept, not guessed: the agent's tool runner turns it into an
            # error result the model sees, exactly as a bad Claude call would.
            args = {"_unparsed_arguments": raw}
        blocks.append({"type": "tool_use", "id": c["id"], "name": c["function"]["name"],
                       "input": args if isinstance(args, dict) else {"_unparsed_arguments": raw}})
    finish = choice.get("finish_reason") or "stop"
    stop = "tool_use" if any(b["type"] == "tool_use" for b in blocks) else STOP_REASONS.get(finish, finish)
    return stop, blocks


def http_transport(url: str, headers: dict, body: dict, *, attempts: int = 4, timeout: int = 180) -> dict:
    """POST JSON, retrying rate limits and server errors with backoff."""
    data = json.dumps(body).encode()
    for attempt in range(attempts):
        req = urllib.request.Request(url, data=data, method="POST",
                                     headers={**headers, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:300]
            if e.code in (429, 500, 502, 503, 504) and attempt < attempts - 1:
                time.sleep(2 ** attempt * 2)
                continue
            raise RuntimeError(f"{url} returned {e.code}: {detail}") from None
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < attempts - 1:
                time.sleep(2 ** attempt * 2)
                continue
            raise RuntimeError(f"{url} unreachable: {e}") from None
    raise RuntimeError(f"{url}: gave up after {attempts} attempts")


class OpenAICompatModel:
    """An OpenAI-compatible chat model behind the agent's Model port."""

    def __init__(self, model: str, *, api_key: str | None = None,
                 env: Mapping[str, str] | None = None, transport: Transport | None = None) -> None:
        provider, _, name = model.partition("/")
        if provider not in PROVIDERS or not name:
            raise ValueError(f"unknown provider in {model!r}; known: {', '.join(PROVIDERS)} "
                             "(as provider/model), or a plain Claude model name")
        self._url, key_var = PROVIDERS[provider]
        env = os.environ if env is None else env
        key = api_key or env.get(key_var, "")
        if not key:
            raise RuntimeError(f"{model} needs {key_var} in .env")
        self._key = key
        self._name = name           # what the provider calls it
        self._model = model         # what records carry: provider included
        self._transport = transport or http_transport

    def respond(self, *, system: str, messages: list[dict], tools: list[dict]) -> Response:
        body: dict[str, Any] = {"model": self._name, "messages": to_messages(system, messages)}
        if tools:
            body["tools"] = to_tools(tools)
        out = self._transport(self._url, {"Authorization": f"Bearer {self._key}"}, body)
        choices = out.get("choices") or []
        if not choices:
            raise RuntimeError(f"{self._model}: no choices in response: {str(out)[:200]}")
        stop, blocks = from_choice(choices[0])
        return Response(stop_reason=stop, content=blocks, model=out.get("model") or self._name)


def model_for(name: str, *, api_key: str | None = None,
              env: Mapping[str, str] | None = None) -> Model:
    """The model for a name: `provider/model` goes to its OpenAI-compatible
    API, a plain name is Claude. `api_key` is for Claude, where a caller can
    pay for its own calls."""
    if "/" in name:
        return OpenAICompatModel(name, env=env)
    return AnthropicModel(name, api_key=api_key) if api_key else AnthropicModel(name)
