"""The Actors ship a copy of the package, and the copy must not drift.

`apify push` skips anything git ignores, so the copies scripts/sync_actors.py
makes have to be committed. That makes drift possible: edit firedrill/ and an
Actor would deploy yesterday's code and fail only in the cloud. These tests
turn that into a local failure with a one-command fix.
"""
import hashlib
from pathlib import Path

import pytest

from scripts.sync_actors import ACTORS, ROOT, SHARED, actor_dirs

SKIP_DIRS = {"__pycache__", ".pytest_cache"}


def files_under(root: Path) -> dict[str, str]:
    """Relative path -> content hash, ignoring build leftovers."""
    out = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix == ".pyc":
            continue
        if SKIP_DIRS & set(path.relative_to(root).parts):
            continue
        out[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def test_there_are_actors_to_check():
    assert actor_dirs(), f"no actors with a .actor/actor.json under {ACTORS}"


@pytest.mark.parametrize("actor", actor_dirs(), ids=lambda p: p.name)
@pytest.mark.parametrize("shared", SHARED)
def test_the_actor_copy_matches_the_source(actor: Path, shared: str):
    source, copy = ROOT / shared, actor / shared
    if not source.exists():
        pytest.skip(f"{shared}/ is not in the project")
    assert copy.exists(), (
        f"{actor.name} has no {shared}/: run  .venv\\Scripts\\python.exe scripts\\sync_actors.py"
    )
    want, got = files_under(source), files_under(copy)
    missing, extra = sorted(set(want) - set(got)), sorted(set(got) - set(want))
    changed = sorted(f for f in set(want) & set(got) if want[f] != got[f])
    assert not (missing or extra or changed), (
        f"{actor.name}/{shared} is out of date "
        f"(missing={missing}, extra={extra}, changed={changed}); "
        "run  .venv\\Scripts\\python.exe scripts\\sync_actors.py"
    )


@pytest.mark.parametrize("actor", actor_dirs(), ids=lambda p: p.name)
def test_the_actor_is_deployable(actor: Path):
    """The pieces `apify push` needs, and the entry point the image runs."""
    for required in (".actor/actor.json", "Dockerfile", "requirements.txt",
                     "src/main.py", "src/__main__.py"):
        assert (actor / required).exists(), f"{actor.name} is missing {required}"


@pytest.mark.parametrize("actor", actor_dirs(), ids=lambda p: p.name)
def test_nothing_in_the_actor_is_git_ignored(actor: Path):
    """A git-ignored file never reaches the image: that is what made the first
    deploy fail with ModuleNotFoundError: No module named 'firedrill'."""
    import subprocess

    must_ship = [actor / shared for shared in SHARED if (actor / shared).exists()]
    must_ship += [actor / "src", actor / "Dockerfile", actor / "requirements.txt"]
    done = subprocess.run(
        ["git", "check-ignore", *[str(p) for p in must_ship]],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert not done.stdout.strip(), (
        f"{actor.name} would deploy without these, because git ignores them:\n{done.stdout}"
    )
