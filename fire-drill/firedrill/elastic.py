"""Elastic adapters: the drill corpus as something an agent can ask about.

Two seams, both optional and both absent unless the environment is set:

- `ElasticSink` is the `TraceSink` the architecture reserved. It indexes one
  document per drill, in the same flat shape the Apify dataset uses, so a
  drill reads the same in a dataset view, in a webhook payload and in Elastic.
- `AgentBuilder` registers a tool over that index, so an agent can be asked
  "which drills breached, and at which turn?" and answer it from the corpus
  instead of from a transcript.

The second one is the point. A pile of drill records is only evidence if
someone can interrogate it, and the question a reviewer actually asks —
*which controls failed, where* — is a query, not a document. Registering it as
a tool makes the corpus answerable by an agent rather than only by whoever
wrote the aggregation.

Nothing here is on the scoring path. A verdict is a predicate over ledger
state (ADR-0001); Elastic sees drills only after they are decided, so an
outage or a mapping change can cost you a query and never a result.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

DRILL_INDEX = "fire-drill-drills"

# Keyword where we filter and group, number where we aggregate. `drill_id` is
# the document id too, so re-indexing a corpus overwrites rather than doubles
# it — the same content-addressed habit records/ uses.
DRILL_MAPPING = {
    "properties": {
        "drill_id": {"type": "keyword"},
        "card_id": {"type": "keyword"},
        "family": {"type": "keyword"},
        "channel": {"type": "keyword"},
        "sender_kind": {"type": "keyword"},
        "source_url": {"type": "keyword", "index": False},
        "seed": {"type": "integer"},
        "model": {"type": "keyword"},
        "config": {"type": "keyword"},
        "breach": {"type": "boolean"},
        "verified_out_of_band": {"type": "boolean"},
        "canary_touched": {"type": "boolean"},
        "capitulation_turn": {"type": "integer"},
        "paid_on_file": {"type": "boolean"},
        "ended_by": {"type": "keyword"},
        "turns": {"type": "integer"},
        "money_moved": {"type": "long"},
        "tool_calls": {"type": "keyword"},
        "indexed_at": {"type": "date"},
    }
}


class ElasticError(RuntimeError):
    """An error with Elastic's own message in it.

    `urllib` raises `HTTPError: 400 Bad Request` and drops the body, which is
    the only part that says what was wrong. Re-raising with the body attached
    turns a guessing game into a fix."""

    def __init__(self, status: int, url: str, body: str) -> None:
        super().__init__(f"HTTP {status} from {url}: {body[:1500]}")
        self.status, self.url, self.body = status, url, body


def _request(url: str, api_key: str, method: str = "GET", body: Any = None,
             extra_headers: Mapping[str, str] | None = None, timeout: float = 30) -> dict:
    headers = {"Authorization": f"ApiKey {api_key}", "Content-Type": "application/json"}
    headers.update(extra_headers or {})
    data = None
    if body is not None:
        data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise                     # callers tell "absent" apart from "broken"
        raise ElasticError(e.code, url, e.read().decode(errors="replace")) from None
    return json.loads(raw) if raw else {}


@dataclass
class ElasticSink:
    """The drill corpus in Elasticsearch."""

    url: str
    api_key: str
    index: str = DRILL_INDEX

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "ElasticSink | None":
        url, key = env.get("ELASTICSEARCH_URL"), env.get("ELASTIC_API_KEY")
        return cls(url.rstrip("/"), key) if url and key else None

    # --- the index ---------------------------------------------------------
    def ensure_index(self) -> bool:
        """Create the index with its mapping. True if it had to be created.

        An explicit mapping rather than dynamic: `capitulation_turn` is null
        on every held drill, and letting Elastic guess from the first document
        it happens to see is how a field ends up a `text` you cannot aggregate.
        """
        try:
            _request(f"{self.url}/{self.index}", self.api_key)
            return False
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
        _request(f"{self.url}/{self.index}", self.api_key, "PUT", {"mappings": DRILL_MAPPING})
        return True

    def index_rows(self, rows: list[dict]) -> int:
        """Bulk-index drill rows, keyed by drill_id and config so a re-run
        replaces its own document. Returns the number written."""
        if not rows:
            return 0
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        lines = []
        for row in rows:
            doc = {k: v for k, v in row.items() if k in DRILL_MAPPING["properties"]}
            doc["indexed_at"] = stamp
            doc_id = f"{row['drill_id']}-{row['config']}-{row['model']}"
            lines.append(json.dumps({"index": {"_index": self.index, "_id": doc_id}}))
            lines.append(json.dumps(doc))
        out = _request(f"{self.url}/_bulk?refresh=true", self.api_key, "POST",
                       "\n".join(lines) + "\n",
                       {"Content-Type": "application/x-ndjson"})
        failed = [i for i in out.get("items", []) if i.get("index", {}).get("error")]
        if failed:
            raise RuntimeError(f"{len(failed)} document(s) rejected: "
                               f"{failed[0]['index']['error']}")
        return len(rows)

    def count(self) -> int:
        return _request(f"{self.url}/{self.index}/_count", self.api_key).get("count", 0)

    def esql(self, query: str) -> dict:
        return _request(f"{self.url}/_query", self.api_key, "POST", {"query": query})

    # --- the TraceSink port ------------------------------------------------
    def emit(self, event) -> None:
        """Satisfies `firedrill.trace.TraceSink`. Drill-level documents are
        what the corpus is for, so a per-turn event is recorded only as part
        of its drill; this is here so the sink can stand in anywhere the port
        is expected without a special case."""
        return None


# --- Agent Builder ----------------------------------------------------------
# One tool, registered against the corpus. ES|QL rather than a free search:
# the query is fixed and reviewable, the agent supplies only parameters, and
# an answer can be reproduced by running the same query by hand.

BREACH_TOOL = {
    "id": "fire_drill_breaches",
    "type": "esql",
    "description": (
        "Which Fire Drill manipulation drills breached an accounts-payable agent's controls, "
        "and on which turn it capitulated. A breach means money left for a bank account that "
        "was never verified out of band. Filter by hardening level (config, e.g. 'baseline' or "
        "'patch:v1'), by tactic family, or by model. Use this to compare hardening levels, to "
        "find which tactic a control failed against, or to show the turn an agent broke."
    ),
    "tags": ["fire-drill", "security", "evals"],
    "configuration": {
        "query": (
            f"FROM {DRILL_INDEX}\n"
            "| WHERE family != \"benign\" AND config LIKE ?config AND family LIKE ?family\n"
            "| STATS drills = COUNT(*), breaches = COUNT(CASE(breach, 1)),"
            " first_capitulation = MIN(capitulation_turn), moved = SUM(money_moved)"
            " BY config, card_id, model\n"
            "| SORT breaches DESC, config ASC"
        ),
        "params": {
            "config": {
                "type": "string",
                "description": "Hardening level to include, with * as a wildcard. "
                               "Use \"*\" for every level.",
            },
            "family": {
                "type": "string",
                "description": "Tactic family to include, with * as a wildcard. "
                               "Use \"*\" for every family.",
            },
        },
    },
}


@dataclass
class AgentBuilder:
    """Kibana's Agent Builder tool registry."""

    kibana_url: str
    api_key: str

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "AgentBuilder | None":
        url, key = env.get("KIBANA_URL"), env.get("ELASTIC_API_KEY")
        return cls(url.rstrip("/"), key) if url and key else None

    def _call(self, path: str, method: str = "GET", body: Any = None) -> dict:
        return _request(f"{self.kibana_url}{path}", self.api_key, method, body,
                        {"kbn-xsrf": "true"})

    def tools(self) -> list[dict]:
        out = self._call("/api/agent_builder/tools")
        return out.get("results", out if isinstance(out, list) else [])

    def upsert_tool(self, tool: dict) -> dict:
        """Create the tool, or update it if it is already registered.

        Idempotent on purpose: this runs from a script that may be run twice,
        and a half-registered tool is worse than none."""
        known = {t.get("id") for t in self.tools()}
        if tool["id"] in known:
            patch = {k: v for k, v in tool.items() if k != "id" and k != "type"}
            return self._call(f"/api/agent_builder/tools/{tool['id']}", "PUT", patch)
        return self._call("/api/agent_builder/tools", "POST", tool)

    def delete_tool(self, tool_id: str) -> dict:
        return self._call(f"/api/agent_builder/tools/{tool_id}", "DELETE")
