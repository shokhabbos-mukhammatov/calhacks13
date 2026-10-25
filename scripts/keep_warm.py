"""Keep the Standby target awake while judging is on.

    .venv\\Scripts\\python.exe scripts\\keep_warm.py
    .venv\\Scripts\\python.exe scripts\\keep_warm.py --every 90
    .venv\\Scripts\\python.exe scripts\\keep_warm.py --url https://<actor-id>.apify.actor

A Standby Actor sleeps when nothing calls it, and the next call pays for the
container to start: eight seconds of silence on a phone line while a judge
waits. Leave this running in a second terminal from the moment you sit down.

It is a loop over one GET, on purpose. A platform schedule would be invisible
during the demo and would bill for a run; this prints a line every time it
touches the target, so you can see at a glance that the thing is warm, and it
stops when you close the window.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from firedrill.console import use_utf8

# The published ap-practice-target. Overridable, because the Actor id changes
# if someone forks it.
DEFAULT_URL = "https://c2tHmrAQShJ2Rh8KF.apify.actor"


def ping(url: str, token: str | None, timeout: float) -> tuple[int, float]:
    """(status, seconds). A cold container can take most of a minute."""
    req = urllib.request.Request(url, method="GET")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read(64)
            return resp.status, time.monotonic() - started
    except urllib.error.HTTPError as e:
        return e.code, time.monotonic() - started


def main() -> None:
    use_utf8()
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", default=os.environ.get("STANDBY_URL") or DEFAULT_URL)
    p.add_argument("--every", type=float, default=120, help="seconds between pings (default 120)")
    p.add_argument("--timeout", type=float, default=300,
                   help="seconds to wait for a cold start (default 300)")
    args = p.parse_args()

    load_dotenv(ROOT / ".env")
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        print("no APIFY_TOKEN in .env — pinging unauthenticated, which a private "
              "Actor will refuse", file=sys.stderr)

    print(f"warming {args.url} every {args.every:.0f}s — Ctrl-C to stop")
    warm_since: float | None = None
    try:
        while True:
            status, took = ping(args.url, token, args.timeout)
            stamp = datetime.now().strftime("%H:%M:%S")
            if status == 200 and took < 2:
                warm_since = warm_since or time.monotonic()
                state = f"warm for {time.monotonic() - warm_since:.0f}s"
            elif status == 200:
                warm_since = time.monotonic()
                state = "woke it up"
            else:
                warm_since = None
                state = "NOT READY — check the Actor is running"
            print(f"  {stamp}  HTTP {status}  {took:5.2f}s  {state}", flush=True)
            time.sleep(args.every)
    except KeyboardInterrupt:
        print("\nstopped warming. The target will go cold in a few minutes.")


if __name__ == "__main__":
    main()
