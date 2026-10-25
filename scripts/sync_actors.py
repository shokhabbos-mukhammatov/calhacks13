"""Copy the package into each Actor directory so the image ships one source.

An Apify build's context is the Actor's own folder, so it cannot reach up to
firedrill/. Rather than keep a second copy of the code under version control,
this syncs the real one in just before a push; the copies are gitignored.

    .venv\\Scripts\\python.exe scripts\\sync_actors.py          # sync all actors
    .venv\\Scripts\\python.exe scripts\\sync_actors.py --clean  # remove the copies

Then, from the actor's folder:  apify push
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTORS = ROOT / "actors"
# What each Actor needs beside its own src/. patches/ may not exist yet.
SHARED = ("firedrill", "cards", "benign", "patches")
SKIP = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache")


def actor_dirs() -> list[Path]:
    return sorted(p for p in ACTORS.iterdir() if (p / ".actor" / "actor.json").exists())


def main() -> None:
    clean = "--clean" in sys.argv
    actors = actor_dirs()
    if not actors:
        sys.exit(f"no actors found under {ACTORS}")
    for actor in actors:
        for name in SHARED:
            target = actor / name
            if target.exists():
                shutil.rmtree(target)
            if clean:
                continue
            source = ROOT / name
            if not source.exists():
                print(f"  {actor.name}: {name}/ not in the project, skipped")
                continue
            shutil.copytree(source, target, ignore=SKIP)
        print(f"{'cleaned' if clean else 'synced'} {actor.name}")
    if not clean:
        print("\nNow run `apify push` from inside each actor folder.")


if __name__ == "__main__":
    main()
