#!/usr/bin/env python3
"""The one way this kit runs git.

One helper, one contract. A copy per tool means the same failure is reported differently
depending on which tool meets it — one raising when git is missing, one letting the exception
escape, one discarding stderr — and a caller cannot know which behaviour it is getting without
reading the helper beside it.

`Result` is a named triple rather than a bare tuple so that `out` and `err` cannot be swapped by
position, and `ok()` is separate from `run()` because "git failed" and "git returned nothing" are
different facts: collapsing them lets a failed `status` read as a clean base.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import NamedTuple

TIMED_OUT = 124


class GitMissing(RuntimeError):
    """git is not on this machine. Nothing here can work, and saying so beats a traceback."""


class Result(NamedTuple):
    code: int
    out: str
    err: str

    @property
    def failed(self) -> bool:
        return self.code != 0


def run(root: Path, *args, timeout=None) -> Result:
    """Run git in `root`. Never raises for an ordinary git failure — that is a Result.

    stdout keeps its leading whitespace: porcelain status encodes state in columns 1 and 2, and
    stripping it once cost every path in a report its first character.
    """
    try:
        done = subprocess.run(
            ["git", "-C", str(root)] + list(args),
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return Result(TIMED_OUT, "", "timed out after %ss" % timeout)
    except FileNotFoundError:
        raise GitMissing("git is not installed on this machine")
    return Result(done.returncode, done.stdout.rstrip("\n"), done.stderr.strip())


def ok(root: Path, *args, timeout=None):
    """The output when git succeeded, else None.

    Use only where empty output and failure mean the same thing to the caller. Where they differ,
    call `run` and read `failed` — that distinction is load-bearing more often than it looks.
    """
    result = run(root, *args, timeout=timeout)
    return None if result.failed else result.out
