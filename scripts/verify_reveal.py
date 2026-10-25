"""Check a published reveal against the commitment it claims to open (ADR-0002).

    .venv\\Scripts\\python.exe scripts\\verify_reveal.py v3

Needs nothing but a clone: no key, no salts file, no network. It reads the
commitment as it was first committed, from git history rather than from the
working tree, so a commitment edited after the fact would not match. Then it
recomputes the Merkle root from the revealed drills and salts.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from firedrill.commit import COMMITMENTS_DIR, verify
from firedrill.console import use_utf8


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True).stdout


def main() -> None:
    use_utf8()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("name", help="the commitment's name, e.g. v3")
    name = p.parse_args().name

    public = (COMMITMENTS_DIR / f"{name}.commit.json").relative_to(ROOT).as_posix()
    first = git("log", "--diff-filter=A", "--format=%H %cI", "--", public).strip().splitlines()
    if not first:
        sys.exit(f"{public} was never committed")
    sha, when = first[-1].split()
    committed = json.loads(git("show", f"{sha}:{public}"))
    reveal = json.loads((COMMITMENTS_DIR / f"{name}.reveal.json").read_text(encoding="utf-8"))

    print(f"commitment first committed in {sha[:7]} at {when}")
    print(f"  root   {committed['root']}  over {committed['count']} drills ({', '.join(committed['families'])})")
    same = reveal["commitment"]["root"] == committed["root"]
    print(f"reveal names the same root: {'yes' if same else 'NO'}")
    ok = same and verify(committed, reveal["drills"], reveal["salts"])
    print(f"root recomputed from the {len(reveal['drills'])} revealed drills and salts: "
          f"{'MATCHES' if ok else 'DOES NOT MATCH'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
