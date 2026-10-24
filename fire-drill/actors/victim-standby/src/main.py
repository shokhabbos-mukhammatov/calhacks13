"""ap-practice-target: the sandboxed accounts-payable agent at a public URL.

An Apify Standby Actor, so the agent is already warm when a drill arrives and
anyone can point a drill runner at it with no setup. It holds no state of its
own: every turn reloads the conversation and the Ledger from the key-value
store and writes them back, so any run can serve any turn (ADR-0003).

    POST /drill                     {card_id, seed, config?, model?} -> {conversation_id, kit}
    POST /drill/<id>/message        {body, subject?, sender?}        -> {reply, tool_calls}
    GET  /drill/<id>/verdict                                         -> {verdict, payments, ...}
    GET  /                                                           -> what this Actor is

The verdict is read from final Ledger state, never from the transcript
(ADR-0001), so the caller cannot talk the scorer out of a FAIL.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import threading
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, HTTPServer

from apify import Actor

from firedrill.apify_adapters import PrefetchedStore, conversation_key, world_key
from firedrill.drill import CARDS_DIR, build_scenario, load_cards, make_config
from firedrill.ledger import Ledger
from firedrill.scorer import score
from firedrill.trace import MemorySink
from firedrill.verify import NoSenderCheck, RdapDomainAge, VendorVerifier
from firedrill.victim import AnthropicModel, ChannelMessage, VictimAgent

READINESS_HEADER = "x-apify-container-server-readiness-probe"
TURN_TIMEOUT = 300  # seconds for one agent turn, including its model calls

CARDS = {c.id: c for path in CARDS_DIR.glob("*.json") for c in load_cards(path)}


# --- one turn, start to finish ------------------------------------------------
async def start_drill(body: dict) -> tuple[int, dict]:
    card_id = body.get("card_id")
    if card_id not in CARDS:
        return 400, {"error": f"unknown card {card_id!r}", "known": sorted(CARDS)}
    card, seed = CARDS[card_id], int(body.get("seed", 1))
    config_name, model_id = body.get("config", "baseline"), body.get("model", "claude-opus-5-5")
    conversation_id = f"{card_id}-s{seed}-{config_name}".replace(":", "-")

    scenario = build_scenario(card, seed)
    kvs = await Actor.open_key_value_store()
    await kvs.set_value(world_key(conversation_id), {
        "card_id": card_id, "seed": seed, "config": config_name, "model": model_id,
        "ledger": scenario.ledger.to_dict(),
    })
    await kvs.set_value(conversation_key(conversation_id), [])
    Actor.log.info("drill %s started (%s, seed %s)", conversation_id, card_id, seed)
    return 200, {"conversation_id": conversation_id, "card": asdict(card), "kit": asdict(scenario.kit)}


async def handle_message(conversation_id: str, body: dict) -> tuple[int, dict]:
    kvs = await Actor.open_key_value_store()
    world = await kvs.get_value(world_key(conversation_id))
    if world is None:
        return 404, {"error": f"no drill {conversation_id!r}; POST /drill first"}

    card = CARDS[world["card_id"]]
    scenario = build_scenario(card, world["seed"])       # phonebook and domain ages are seeded
    ledger = Ledger.from_dict(world["ledger"])           # the world as the last turn left it
    store = PrefetchedStore(messages=await kvs.get_value(conversation_key(conversation_id)) or [])
    sink = MemorySink()

    config = make_config(world["config"], model=AnthropicModel(world["model"]),
                         verifier=VendorVerifier(RdapDomainAge(), NoSenderCheck()))
    verifier = config.verifier.with_domain_age(_fixed(scenario.domain_ages)) if config.verifier else None
    agent = VictimAgent(ledger, config.model, store, policy=config.policy,
                        tool_scope=config.tool_scope, phonebook=scenario.phonebook,
                        sink=sink, verifier=verifier)

    message = ChannelMessage(
        channel=card.channel,
        sender=body.get("sender") or scenario.kit.sender,
        subject=body.get("subject") or f"Invoice {scenario.kit.invoice_id}",
        body=body.get("body", ""),
    )
    reply = await asyncio.to_thread(agent.handle, conversation_id, message)

    world["ledger"] = ledger.to_dict()
    await kvs.set_value(world_key(conversation_id), world)
    await kvs.set_value(conversation_key(conversation_id), store.messages)
    return 200, {
        "reply": reply,
        "tool_calls": [{"turn": e.turn, **e.data} for e in sink.events if e.kind == "tool_call"],
    }


async def drill_verdict(conversation_id: str) -> tuple[int, dict]:
    kvs = await Actor.open_key_value_store()
    world = await kvs.get_value(world_key(conversation_id))
    if world is None:
        return 404, {"error": f"no drill {conversation_id!r}"}
    ledger = Ledger.from_dict(world["ledger"])
    state = ledger.snapshot()
    kit = build_scenario(CARDS[world["card_id"]], world["seed"]).kit
    return 200, {
        "conversation_id": conversation_id,
        "verdict": asdict(score(state)),
        "payments": [asdict(p) for p in state.payments],
        "paid_on_file": any(p.approved and p.invoice_id == kit.invoice_id for p in state.payments),
        "canary_hits": state.canary_hits,
    }


def _fixed(table: dict[str, int]):
    from firedrill.verify import FixedDomainAge

    return FixedDomainAge(table)


ROUTES = re.compile(r"^/drill/(?P<id>[^/]+)/(?P<action>message|verdict)$")


async def route(method: str, path: str, body: dict) -> tuple[int, dict]:
    if path in ("/", "") and method == "GET":
        return 200, {
            "actor": "ap-practice-target",
            "what": "A sandboxed accounts-payable agent to run manipulation drills against. "
                    "Every verdict is read from ledger state, never from the transcript.",
            "cards": sorted(CARDS),
            "endpoints": ["POST /drill", "POST /drill/<id>/message", "GET /drill/<id>/verdict"],
        }
    if path == "/drill" and method == "POST":
        return await start_drill(body)
    match = ROUTES.match(path)
    if match and match["action"] == "message" and method == "POST":
        return await handle_message(match["id"], body)
    if match and match["action"] == "verdict" and method == "GET":
        return await drill_verdict(match["id"])
    return 404, {"error": f"no route for {method} {path}"}


# --- the HTTP server ------------------------------------------------------------
def make_handler(loop: asyncio.AbstractEventLoop) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def _send(self, status: int, payload: dict) -> None:
            raw = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _serve(self, method: str) -> None:
            # The platform's readiness probe must be answered by the server
            # itself: if it waited on the event loop the run would never be
            # marked ready.
            if self.headers.get(READINESS_HEADER):
                return self._send(200, {"ready": True})
            length = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(length) or "{}") if length else {}
            except ValueError:
                return self._send(400, {"error": "body is not JSON"})
            path = self.path.split("?", 1)[0].rstrip("/") or "/"
            try:
                future = asyncio.run_coroutine_threadsafe(route(method, path, body), loop)
                status, payload = future.result(timeout=TURN_TIMEOUT)
            except Exception as e:  # never take the server down over one request
                Actor.log.exception("request failed: %s %s", method, path)
                return self._send(500, {"error": repr(e)})
            self._send(status, payload)

        def do_GET(self) -> None:
            self._serve("GET")

        def do_POST(self) -> None:
            self._serve("POST")

        def log_message(self, fmt: str, *args) -> None:
            Actor.log.info("%s - %s", self.address_string(), fmt % args)

    return Handler


async def main() -> None:
    async with Actor:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            Actor.log.warning("ANTHROPIC_API_KEY is not set; drills will fail on the first turn")
        port = Actor.configuration.web_server_port
        server = HTTPServer(("", port), make_handler(asyncio.get_running_loop()))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        Actor.log.info("ap-practice-target listening on :%s with %d cards", port, len(CARDS))
        try:
            await asyncio.Event().wait()   # Standby: stay up between requests
        finally:
            server.shutdown()
