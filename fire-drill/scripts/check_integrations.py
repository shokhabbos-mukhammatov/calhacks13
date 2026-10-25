"""Check every sponsor integration end to end, cheaply.

    .venv\\Scripts\\python.exe scripts\\check_integrations.py

One line per integration: what was actually exercised, and whether it worked.
Each check is the smallest real call that proves the path, so the whole sweep
costs a few cents. Secrets are never printed.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from firedrill.console import use_utf8

from dotenv import dotenv_values

ENV = {k: (v or "") for k, v in dotenv_values(ROOT / ".env").items()}
STANDBY = "https://c2tHmrAQShJ2Rh8KF.apify.actor"
RUNNER_ID, TARGET_ID = "ySN2UCHtbXn6pUPee", "c2tHmrAQShJ2Rh8KF"

results: list[tuple[str, str, bool, str]] = []


def record(sponsor: str, what: str, ok: bool, detail: str = "") -> None:
    results.append((sponsor, what, ok, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {sponsor:<14} {what}" + (f"  — {detail}" if detail else ""))


def http(method: str, url: str, body=None, headers=None, timeout=120):
    data = json.dumps(body).encode() if body is not None else None
    h = dict(headers or {})
    if data:
        h.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode(errors="replace")
            return r.status, (json.loads(raw) if raw[:1] in "{[" else raw)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")[:200]
    except Exception as e:
        return None, repr(e)


def check_anthropic() -> None:
    from firedrill.victim import TOOLS, AnthropicModel, ROLE

    try:
        r = AnthropicModel("claude-haiku-4-5", api_key=ENV["ANTHROPIC_API_KEY"]).respond(
            system=ROLE, tools=TOOLS,
            messages=[{"role": "user", "content": "[invoice channel] From: a@b.example\n\nRead invoice INV-1."}])
        used = [b["name"] for b in r.content if b["type"] == "tool_use"]
        record("Anthropic", "victim agent calls its tools", bool(used), f"called {used or 'nothing'}")
    except Exception as e:
        record("Anthropic", "victim agent calls its tools", False, repr(e)[:90])


def check_apify() -> None:
    tok = {"Authorization": f"Bearer {ENV['APIFY_TOKEN']}"}
    for name, aid in (("fire-drill", RUNNER_ID), ("ap-practice-target", TARGET_ID)):
        s, a = http("GET", f"https://api.apify.com/v2/acts/{aid}", headers=tok)
        pub = isinstance(a, dict) and a["data"].get("isPublic")
        record("Apify", f"{name} published", bool(pub), "on Store" if pub else "private")
    s, _ = http("GET", "https://apify.com/shohabbos_m/fire-drill")
    record("Apify", "Store page loads for a stranger", s == 200, f"HTTP {s}")
    t0 = time.monotonic()
    s, b = http("GET", f"{STANDBY}/", headers=tok, timeout=300)
    record("Apify", "Standby target answers", s == 200,
           f"{len(b.get('cards', [])) if isinstance(b, dict) else 0} cards, {time.monotonic() - t0:.0f}s")


def check_cartesia() -> None:
    h = {"Authorization": f"Bearer {ENV['CARTESIA_API_KEY']}", "Cartesia-Version": ENV["CARTESIA_VERSION"]}
    s, a = http("GET", f"https://api.cartesia.ai/v1/agents/{ENV['CARTESIA_AGENT_ID']}", headers=h)
    ok = s == 200
    tools = [t["id"] for t in a["config"].get("tools", [])] if ok else []
    record("Cartesia", "voice agent exists", ok, a.get("name", "") if ok else str(a)[:70])
    record("Cartesia", "relay tool attached", bool(tools), f"{len(tools)} tool(s)")
    if tools:
        s, t = http("GET", f"https://api.cartesia.ai/v1/agents/tools/{tools[0]}", headers=h)
        url = t.get("api_schema", {}).get("url", "") if s == 200 else ""
        props = list((t.get("api_schema", {}).get("request_body_schema", {}).get("properties") or {}))
        record("Cartesia", "tool points at the live relay", url.startswith(STANDBY), url[-24:] or "none")
        record("Cartesia", "tool sends message + call id", {"message", "call_id"} <= set(props), ", ".join(props))
    s, v = http("GET", f"https://api.cartesia.ai/voices/{ENV['CARTESIA_VOICE_ID']}", headers=h)
    record("Cartesia", "voice id resolves", s == 200, v.get("name", "") if s == 200 else str(v)[:60])
    s, n = http("GET", "https://api.cartesia.ai/agents/phone-numbers", headers=h)
    count = len(n.get("data", [])) if s == 200 else 0
    record("Cartesia", "phone number attached", count > 0, f"{count} number(s)")
    # The call path itself, exactly as the webhook tool sends it.
    t0 = time.monotonic()
    s, out = http("POST", f"{STANDBY}/voice/relay",
                  {"message": "Hi, Northwind Traders calling about invoice INV-7833.",
                   "call_id": f"check_{int(time.time())}"},
                  {"Authorization": f"Bearer {ENV['APIFY_TOKEN']}"}, timeout=300)
    took = time.monotonic() - t0
    spoken = isinstance(out, dict) and out.get("reply") and "**" not in out["reply"]
    record("Cartesia", "a voice turn runs", s == 200 and bool(spoken),
           f"{took:.1f}s, {'spoken prose' if spoken else 'bad reply'}")
    return out if isinstance(out, dict) else {}


def check_nessie() -> None:
    from firedrill.payments import NessieRail

    rail = NessieRail.from_env(os.environ)
    if rail is None:
        return record("Capital One", "payment rail mirrors", False, "NESSIE_* not set")
    r = rail.transfer(invoice_id="INV-CHECK", account="ACCT-CHECK", amount=1)
    record("Capital One", "payment rail mirrors", r.ok, r.reference or r.error or "")


def check_crs() -> None:
    from firedrill.crs_personas import CONTACTS, IMPOSTORS
    from firedrill.verify import CrsFraudFinder, CrsReverseLookup

    # The personas a drill's phone numbers come from must still answer the way
    # firedrill/crs_personas.py records, or the callback control is checking
    # nothing. This is the live half of tests/test_crs_personas.py.
    lookup = CrsReverseLookup.from_env(os.environ)
    if lookup is None:
        record("CRS", "reverse lookup", False, "CRS_* not set")
    else:
        wrong = []
        for persona in CONTACTS + IMPOSTORS:
            got = lookup.owner(persona.number)
            if (got.name or None) != persona.expect:
                wrong.append(f"{persona.id} expected {persona.expect!r}, got {got.name!r}")
        record("CRS", "personas answer as recorded", not wrong,
               f"{len(CONTACTS)} contacts + {len(IMPOSTORS)} impostors" if not wrong
               else "; ".join(wrong)[:90])
        # The separation the control rests on, end to end.
        contact, impostor = CONTACTS[0], IMPOSTORS[0]
        a, b = lookup.owner(contact.number), lookup.owner(impostor.number)
        record("CRS", "a vendor's number and an impostor's differ", a.name != b.name,
               f"{a.name} vs {b.name or 'no record'}")

    # Fraud Finder only answers for a full persona body; with the email alone
    # the request misses the sandbox and falls through to the real vendor.
    finder = CrsFraudFinder.from_env(os.environ)
    if finder:
        scores = {p.id: finder.check_number(p.number).score for p in (CONTACTS[0], IMPOSTORS[0])}
        low, high = scores[CONTACTS[0].id], scores[IMPOSTORS[0].id]
        record("CRS", "Fraud Finder scores the party behind a number",
               low is not None and high is not None and low < high,
               f"{CONTACTS[0].id} {low} vs {IMPOSTORS[0].id} {high}")

    if finder is None:
        return record("CRS", "sender risk check", False, "CRS_* not set")
    # Deliberately a persona, not a made-up address: an unmatched request
    # leaves the sandbox for the real AtData vendor, where it can be billed.
    risk = finder.check_number(IMPOSTORS[1].number)
    record("CRS", "sender risk check", risk.score is not None,
           f"{IMPOSTORS[1].id} score={risk.score}")


def check_rdap() -> None:
    from firedrill.verify import RdapDomainAge

    age = RdapDomainAge().age_days("apify.com")
    record("RDAP", "sender domain age", age is not None and age > 365, f"{age} days")


def check_elastic() -> None:
    from firedrill.elastic import BREACH_TOOL, DRILL_INDEX

    h = {"Authorization": f"ApiKey {ENV.get('ELASTIC_API_KEY', '')}"}
    es = ENV.get("ELASTICSEARCH_URL", "https://none.invalid").rstrip("/")
    kb = ENV.get("KIBANA_URL", "https://none.invalid").rstrip("/")
    s, b = http("GET", es + "/", headers=h)
    record("Elastic", "cluster reachable", s == 200,
           b.get("version", {}).get("number", "") if s == 200 else str(b)[:50])

    # Reachable is not the same as useful: the corpus has to hold drills, and
    # the tool has to come back with an answer, or nothing is actually wired.
    s, b = http("GET", f"{es}/{DRILL_INDEX}/_count", headers=h)
    record("Elastic", "drill corpus indexed", s == 200 and b.get("count", 0) > 0,
           f"{b.get('count', 0)} drills in {DRILL_INDEX}" if s == 200 else str(b)[:50])

    s, b = http("POST", f"{kb}/api/agent_builder/tools/_execute",
                {"tool_id": BREACH_TOOL["id"],
                 "tool_params": {"config": "baseline", "family": "*"}},
                headers={**h, "kbn-xsrf": "true"})
    # An execution returns the echoed query first and the table after it, so
    # pick the result out by type rather than by position.
    rows = next((r["data"]["values"] for r in (b.get("results") or [])
                 if r.get("type") == "esql_results"), []) if s == 200 else []
    record("Elastic", "Agent Builder tool answers", bool(rows),
           f"{BREACH_TOOL['id']} -> {len(rows)} cell(s)" if rows else str(b)[:70])


def check_factory() -> None:
    exe = Path(os.environ.get("USERPROFILE", "")) / "bin" / "droid.exe"
    if not exe.exists():
        return record("Factory", "droid CLI present", False, "not installed")
    try:
        v = subprocess.run([str(exe), "--version"], capture_output=True, text=True, timeout=120)
        record("Factory", "droid CLI present", v.returncode == 0, v.stdout.strip()[:20])
    except Exception as e:
        record("Factory", "droid CLI present", False, repr(e)[:60])
    try:
        import droid_sdk
        record("Factory", "Droid SDK installed", True, f"droid-sdk {droid_sdk.PACKAGE_VERSION}")
    except ImportError as e:
        record("Factory", "Droid SDK installed", False, repr(e)[:60])
    # The product's path: a patch the SDK remediator wrote on a trigger, with
    # its recorded steps, that the harness re-checked as blocking every failure.
    sdk = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "patches").glob("*.json"))]
    sdk = [p for p in sdk if p.get("author") == "droid-sdk"]
    best = max(sdk, key=lambda p: len(p.get("trace") or []), default=None)
    ok = bool(best and best.get("trace") and (best.get("check") or {}).get("all_failures_blocked")
              and (best.get("trigger") or {}).get("fired"))
    record("Factory", "SDK patch: triggered, traced, re-checked", ok,
           f"{len(best['trace'])} steps, {best['check']['failures_blocked']}" if ok else "none yet")


def main() -> None:
    use_utf8()
    os.environ.update({k: v for k, v in ENV.items() if v})
    print("Checking every integration end to end.\n")
    for fn in (check_anthropic, check_apify, check_cartesia, check_nessie,
               check_crs, check_rdap, check_elastic, check_factory):
        try:
            fn()
        except Exception as e:
            record(fn.__name__.replace("check_", ""), "check itself failed", False, repr(e)[:90])
    passed = sum(1 for *_, ok, _ in results if ok)
    print(f"\n{passed}/{len(results)} checks passed")
    for sponsor, what, ok, detail in results:
        if not ok:
            print(f"  still failing: {sponsor} — {what} ({detail})")


if __name__ == "__main__":
    main()
