#!/usr/bin/env python3
"""Remove the paths the manifest says the kit no longer owns.

An update copies what the kit HAS. It cannot express what the kit no longer
has: the updater walks the `engine:` list, and a path that is gone is simply
never walked — so it stays on the base forever. A removed command goes on being
discoverable, describing a contract nothing honours; a removed script goes on
being importable.

`retired:` is the missing half. The author lists a path once and every update
converges every base. This runs on each update rather than as a one-off, on
purpose: a one-off reaches only the bases that have not run it yet, while this
reaches a base at any version, including one that has been dark for months.

Two properties make it safe to run unattended:

- **It never leaves kit space.** A retired path falling under `exclude:` — the
  manifest's own enumeration of the person's space — is refused, and the refusal
  is an error rather than a skip, because a path in the wrong section is an
  authoring mistake that has to be seen.
- **It only deletes what the manifest names.** No globs, no inference from what
  the kit lacks. "Absent upstream" is equally the shape of a botched path list.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from . import manifest as manifest_lib


class RetirementRefused(Exception):
    """A retired path reaches into the person's space. Nothing was deleted."""

    def __init__(self, trespassing: list[str]):
        super().__init__("retired paths fall under exclude: %s" % ", ".join(trespassing))
        self.trespassing = trespassing


def trespassing_paths(retired: list[str], excluded: list[str]) -> list[str]:
    """Retired entries that would reach the person's space. Empty is the good case."""
    return [p for p in retired if any(manifest_lib.covered_by(e, p) for e in excluded)]


def run(root: Path, dry_run: bool = False) -> list[str]:
    """Delete every listed path that is present. Returns what was (or would be) removed."""
    retired = manifest_lib.read_section("retired", root)
    if not retired:
        return []
    trespassing = trespassing_paths(retired, manifest_lib.read_section("exclude", root))
    if trespassing:
        raise RetirementRefused(trespassing)

    removed = []
    for relpath in retired:
        target = root / relpath
        if not target.exists() and not target.is_symlink():
            continue
        removed.append(relpath)
        if dry_run:
            continue
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink()
        _prune_empty_parents(root, target.parent)
    return removed


def _prune_empty_parents(root: Path, directory: Path) -> None:
    """An emptied directory left behind still reads as a place things live."""
    while directory != root and directory.is_dir() and not any(directory.iterdir()):
        directory.rmdir()
        directory = directory.parent
