"""Make stdout survive whatever the agent said.

A Windows console defaults to a legacy code page, so one em dash or curly
quote in a model's reply raises `UnicodeEncodeError` and takes the whole run
down with it — a crash mid-demo, caused by punctuation. The intervals printed
by `firedrill.scorecard` carry an em dash too, so this is not only about model
output.

Every script that prints either one calls `use_utf8()` before it prints
anything. It is deliberately forgiving: a stream that cannot be reconfigured
(already UTF-8, or redirected to a pipe that owns its own encoding) is left
exactly as it was rather than treated as an error.
"""
from __future__ import annotations

import sys


def use_utf8() -> None:
    """Print UTF-8, and replace anything the console still cannot render."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass
