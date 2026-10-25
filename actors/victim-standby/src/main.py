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
import secrets
import threading
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, HTTPServer

from apify import Actor

from firedrill.apify_adapters import PrefetchedStore, call_key, conversation_key, world_key
from firedrill.drill import CARDS_DIR, build_scenario, load_cards, make_config
from firedrill.ledger import Ledger
from firedrill.scorer import score
from firedrill.trace import MemorySink
from firedrill.verify import (
    CrsFraudFinder,
    CrsReverseLookup,
    NoPhoneOwner,
    NoSenderCheck,
    RdapDomainAge,
    VendorVerifier,
)
from firedrill.victim import AnthropicModel, ChannelMessage, VictimAgent

READINESS_HEADER = "x-apify-container-server-readiness-probe"
TURN_TIMEOUT = 300  # seconds for one agent turn, including its model calls
STORE_NAME = "fire-drill-worlds"
# A phone call is a live demo: it needs the same world every time, so a caller
# can be handed a card with the vendor and invoice on it, and a model fast
# enough that a turn does not outlast the line's patience.
DEFAULT_VOICE_CARD = "vmt-01"
# Pinned so the judge card matches the world: Northwind Traders, and the
# number the caller offers belongs to a different CRS identity (Rajesh
# Menon), which the agent can check with verify_vendor while on the call.
DEFAULT_VOICE_SEED = 205
DEFAULT_VOICE_MODEL = "claude-haiku-4-5"
# The hardening level a call runs at. Cartesia's tool sends only the caller's
# words and a call id, so the Actor decides. "baseline+verify" offers the
# agent CRS through verify_vendor and nothing else: no policy and no gates, so
# a caller can still talk it into paying, and when it does check the number,
# CRS answers live. Set VOICE_CONFIG on the Actor to change it ("baseline"
# takes CRS away again) without touching the code.
DEFAULT_VOICE_CONFIG = "baseline+verify"

CARDS = {c.id: c for path in CARDS_DIR.glob("*.json") for c in load_cards(path)}


def voice_config(body: dict, env) -> str:
    """The caller's config if it names one, else the Actor's VOICE_CONFIG, else
    the default. A setting that names no real config falls back to the
    default rather than failing every call on a live line."""
    name = body.get("config") or env.get("VOICE_CONFIG") or DEFAULT_VOICE_CONFIG
    if name == DEFAULT_VOICE_CONFIG or body.get("config"):
        return name
    try:
        make_config(name, model=None)   # checks the name, and that a patch file exists
    except (ValueError, FileNotFoundError, OSError):
        Actor.log.warning("VOICE_CONFIG %r is not a config; calls use %s", name, DEFAULT_VOICE_CONFIG)
        return DEFAULT_VOICE_CONFIG
    return name

_store = None


async def open_store():
    """The drills' storage, shared across runs.

    A run's default key-value store belongs to that run alone, so a drill
    started on one Standby container would vanish when the platform scaled or
    restarted it. A named store is the whole point of ADR-0003: state lives
    outside the process, and any run can serve any turn. If the account's
    permissions refuse a named store we fall back to the default one and say
    so, because a drill inside a single run still works."""
    global _store
    if _store is None:
        try:
            _store = await Actor.open_key_value_store(name=STORE_NAME)
            Actor.log.info("using the shared key-value store %r", STORE_NAME)
        except Exception as e:
            Actor.log.warning(
                "could not open the shared store %r (%r); falling back to this run's own "
                "store, so a drill will not outlive this container", STORE_NAME, e)
            _store = await Actor.open_key_value_store()
    return _store


# --- one turn, start to finish ------------------------------------------------
async def start_drill(body: dict) -> tuple[int, dict]:
    card_id = body.get("card_id")
    if card_id not in CARDS:
        return 400, {"error": f"unknown card {card_id!r}", "known": sorted(CARDS)}
    card, seed = CARDS[card_id], int(body.get("seed", 1))
    config_name, model_id = body.get("config", "baseline"), body.get("model", "claude-opus-5-5")
    conversation_id = f"{card_id}-s{seed}-{config_name}".replace(":", "-")

    scenario = build_scenario(card, seed)
    kvs = await open_store()
    await kvs.set_value(world_key(conversation_id), {
        "card_id": card_id, "seed": seed, "config": config_name, "model": model_id,
        "ledger": scenario.ledger.to_dict(),
    })
    await kvs.set_value(conversation_key(conversation_id), [])
    Actor.log.info("drill %s started (%s, seed %s)", conversation_id, card_id, seed)
    return 200, {"conversation_id": conversation_id, "card": asdict(card), "kit": asdict(scenario.kit)}


async def handle_message(conversation_id: str, body: dict, api_key: str | None) -> tuple[int, dict]:
    kvs = await open_store()
    world = await kvs.get_value(world_key(conversation_id))
    if world is None:
        return 404, {"error": f"no drill {conversation_id!r}; POST /drill first"}

    card = CARDS[world["card_id"]]
    scenario = build_scenario(card, world["seed"])       # phonebook and domain ages are seeded
    ledger = Ledger.from_dict(world["ledger"])           # the world as the last turn left it
    store = PrefetchedStore(messages=await kvs.get_value(conversation_key(conversation_id)) or [])
    sink = MemorySink()

    # The key arrives per request and is never written anywhere: a caller
    # pays for its own model calls, so a public target cannot spend its
    # owner's credit. Falls back to the Actor's own key when one is set.
    # CRS Fraud Finder runs live whenever the Actor has CRS_* credentials set,
    # so a drill on a hardened config calls the CRS sandbox during the demo
    # itself; without them the check reports "unknown", never a guess.
    sender_check = CrsFraudFinder.from_env(os.environ) or NoSenderCheck()
    phone_owner = CrsReverseLookup.from_env(os.environ) or NoPhoneOwner()
    config = make_config(world["config"],
                         verifier=VendorVerifier(RdapDomainAge(), sender_check, phone_owner),
                         model=AnthropicModel(world["model"], api_key=api_key))
    verifier = config.verifier.with_domain_age(_fixed(scenario.domain_ages)) if config.verifier else None
    agent = VictimAgent(ledger, config.model, store, policy=config.policy,
                        tool_scope=config.tool_scope, phonebook=scenario.phonebook,
                        sink=sink, verifier=verifier)

    message = ChannelMessage(
        channel=world.get("channel") or card.channel,
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
    kvs = await open_store()
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


async def voice_relay(body: dict, api_key: str | None) -> tuple[int, dict]:
    """One turn of a phone call, relayed to the same Victim Agent a text drill
    uses (ADR: one Victim Agent, several Channels).

    The caller speaks, Cartesia transcribes, this plays the turn against the
    Ledger and returns what the agent says back. The verdict still comes from
    ledger state afterwards, so a smooth-talking caller cannot talk the scorer
    out of a FAIL.

    The first turn has no drill_id and starts a drill on a fresh random world;
    the id comes back in the response and Cartesia sends it on later turns.
    """
    # The call id is the session key, so the server owns the mapping. Keying on
    # a value the tool had to be handed back first could not work: on the first
    # turn it does not exist yet, and Cartesia rejects a tool call whose dynamic
    # variable is unset.
    call_id = (body.get("call_id") or "").strip()
    kvs = await open_store()
    conversation_id = (await kvs.get_value(call_key(call_id)) or "") if call_id else ""
    if not conversation_id:
        card_id = body.get("card_id") or DEFAULT_VOICE_CARD
        if card_id not in CARDS:
            return 400, {"error": f"unknown card {card_id!r}", "known": sorted(CARDS)}
        seed = int(body.get("seed") or DEFAULT_VOICE_SEED)
        conversation_id = f"voice-{card_id}-s{seed}-{secrets.token_hex(3)}"
        scenario = build_scenario(CARDS[card_id], seed)
        config = voice_config(body, os.environ)
        await kvs.set_value(world_key(conversation_id), {
            "card_id": card_id, "seed": seed, "config": config,
            "model": body.get("model") or DEFAULT_VOICE_MODEL, "channel": "voice",
            "ledger": scenario.ledger.to_dict(),
        })
        await kvs.set_value(conversation_key(conversation_id), [])
        if call_id:
            await kvs.set_value(call_key(call_id), conversation_id)
        Actor.log.info("voice drill %s started (%s, seed %s, %s, call %s)",
                       conversation_id, card_id, seed, config, call_id or "none")

    status, out = await handle_message(
        conversation_id,
        {"body": body.get("message", ""), "sender": body.get("caller_id") or "caller on the phone",
         "subject": "Phone call"},
        api_key,
    )
    if status != 200:
        return status, out
    # The agent's reply is spoken, so hand back only that. The drill id is
    # returned for the caller's own logging; the session does not depend on it.
    return 200, {"reply": out["reply"], "drill_id": conversation_id,
                 "tools_used": [c["tool"] for c in out.get("tool_calls", [])]}


def _fixed(table: dict[str, int]):
    from firedrill.verify import FixedDomainAge

    return FixedDomainAge(table)


ROUTES = re.compile(r"^/drill/(?P<id>[^/]+)/(?P<action>message|verdict)$")


async def route(method: str, path: str, body: dict, api_key: str | None = None) -> tuple[int, dict]:
    if path in ("/", "") and method == "GET":
        return 200, {
            "actor": "ap-practice-target",
            "what": "A sandboxed accounts-payable agent to run manipulation drills against. "
                    "Every verdict is read from ledger state, never from the transcript.",
            "cards": sorted(CARDS),
            "endpoints": ["POST /drill", "POST /drill/<id>/message", "GET /drill/<id>/verdict",
                          "POST /voice/relay"],
        }
    if path == "/drill" and method == "POST":
        return await start_drill(body)
    if path == "/voice/relay" and method == "POST":
        return await voice_relay(body, api_key)
    match = ROUTES.match(path)
    if match and match["action"] == "message" and method == "POST":
        return await handle_message(match["id"], body, api_key)
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
                key = self.headers.get("x-anthropic-api-key")
                future = asyncio.run_coroutine_threadsafe(route(method, path, body, key), loop)
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
            Actor.log.warning("ANTHROPIC_API_KEY is not set; a turn then needs the caller to "
                              "send its own key in the x-anthropic-api-key header")
        port = Actor.configuration.web_server_port
        server = HTTPServer(("", port), make_handler(asyncio.get_running_loop()))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        Actor.log.info("ap-practice-target listening on :%s with %d cards", port, len(CARDS))
        try:
            await asyncio.Event().wait()   # Standby: stay up between requests
        finally:
            server.shutdown()
