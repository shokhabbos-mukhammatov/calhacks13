"""Index the drill corpus in Elastic and register the tool that queries it.

    .venv\\Scripts\\python.exe scripts\\elastic_index.py
    .venv\\Scripts\\python.exe scripts\\elastic_index.py --ask "config=baseline"
    .venv\\Scripts\\python.exe scripts\\elastic_index.py --no-tool

Records hold the attacker's turns, so they are gitignored; what goes to
Elastic is the flat drill row — tactic, hardening level, verdict, the turn the
agent capitulated — and never a message body. Commit-reveal decides what is
published; this is the same line the Apify dataset draws.

The tool registered here is `fire_drill_breaches`: a fixed ES|QL query over
the corpus, with the hardening level and tactic family as parameters, so an
agent can answer "which drills breached, and at which turn?" and a human can
re-run the identical query by hand.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from firedrill.console import use_utf8
from firedrill.elastic import BREACH_TOOL, AgentBuilder, ElasticSink
from firedrill.records import RECORDS_DIR, load_records
from firedrill.render import as_row


def main() -> None:
    use_utf8()
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--records", type=Path, default=RECORDS_DIR)
    p.add_argument("--no-tool", action="store_true", help="index only; skip Agent Builder")
    p.add_argument("--ask", metavar="config=PATTERN",
                   help="run the registered query once and print what it returns")
    args = p.parse_args()

    load_dotenv(ROOT / ".env")
    sink = ElasticSink.from_env(os.environ)
    if not sink:
        sys.exit("no ELASTICSEARCH_URL / ELASTIC_API_KEY in .env")

    records = load_records(args.records)
    if not records:
        sys.exit(f"no records in {args.records}")

    created = sink.ensure_index()
    print(f"index {sink.index}: {'created' if created else 'already there'}")
    written = sink.index_rows([as_row(r) for r in records])
    print(f"indexed {written} drills ({sink.count()} in the corpus)")

    if not args.no_tool:
        builder = AgentBuilder.from_env(os.environ)
        if not builder:
            sys.exit("no KIBANA_URL in .env; indexed, but no tool registered")
        before = {t["id"] for t in builder.tools()}
        builder.upsert_tool(BREACH_TOOL)
        verb = "updated" if BREACH_TOOL["id"] in before else "registered"
        print(f"tool {BREACH_TOOL['id']}: {verb} "
              f"({len(builder.tools())} tools in Agent Builder)")

    if args.ask:
        pattern = args.ask.split("=", 1)[-1]
        query = BREACH_TOOL["configuration"]["query"] \
            .replace("?config", json.dumps(pattern)).replace("?family", '"*"')
        out = sink.esql(query)
        names = [c["name"] for c in out["columns"]]
        print("\n" + "  ".join(f"{n:<18}" for n in names))
        for row in out["values"]:
            print("  ".join(f"{str(v):<18}" for v in row))


if __name__ == "__main__":
    main()
