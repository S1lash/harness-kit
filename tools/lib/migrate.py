#!/usr/bin/env python3
"""Carry a change the kit cannot express by replacing a file.

Replacement covers the kit's own paths and retirement covers the ones it dropped. Neither can
touch the person's space — which is right, it is theirs — so a kit change that REQUIRES something
there to move had no channel at all, and the kit was forbidden from making one.

Three properties decide the shape, and they are why this is not the ordered chain with a ledger
that comparable engines use:

- **Data, not code.** The updater replaces itself mid-run while the old copy is already in memory,
  so logic added to it takes effect one update late. The manifest is re-read from disk after the
  checkout, so a declaration takes effect in the same run it ships in.
- **Convergent, not sequential.** Every operation is idempotent by construction and re-runs on
  every update, so a base at any version — including one dark for a year — lands in the same
  state. A ledger would need a valid starting point that an old base has never had.
- **Refuses what it does not understand.** A verb from a newer kit reaching an older updater stops
  the run and says to update once more, rather than silently skipping a change the kit believes
  landed.

Syntax, one entry per line under `migrations:`:

    - move <from> -> <to>
    - move <from> -> <to> | what to tell the person about it
"""

from __future__ import annotations

import shutil
from pathlib import Path

from . import manifest as manifest_lib

MOVE = "move"
NOTE_SEPARATOR = "|"
ARROW = "->"


class MigrationRefused(Exception):
    """The declaration cannot be carried out safely. Nothing was changed."""


class Move:
    def __init__(self, source: str, destination: str, note: str = ""):
        self.source, self.destination, self.note = source, destination, note

    def __repr__(self):
        return "Move(%r -> %r)" % (self.source, self.destination)


def parse(root: Path) -> list:
    """Read the declared operations. An unknown verb stops the run rather than being skipped."""
    operations = []
    for entry in manifest_lib.read_section("migrations", root):
        body, _, note = entry.partition(NOTE_SEPARATOR)
        verb, _, rest = body.strip().partition(" ")
        if verb != MOVE:
            raise MigrationRefused(
                "this base does not understand '%s'. Its updater is older than the kit that "
                "declared it — run the update once more, now that the machinery itself has been "
                "replaced." % verb)
        source, _, destination = rest.partition(ARROW)
        source, destination = source.strip().rstrip("/"), destination.strip().rstrip("/")
        if not source or not destination:
            raise MigrationRefused("could not read the move in %r" % entry)
        operations.append(Move(source, destination, note.strip()))
    return operations


def _guard(root: Path, operations: list) -> None:
    """Refuse anything that would touch the kit's own space or overwrite the person's."""
    engine = manifest_lib.read_section("engine", root)
    for move in operations:
        for path, side in ((move.source, "from"), (move.destination, "to")):
            if manifest_lib.covers(engine, path):
                raise MigrationRefused(
                    "%s %s is the kit's own space, which replacement and retirement already "
                    "handle. Moving there is an authoring mistake, not a migration." % (side, path))
        target = root / move.destination
        if (root / move.source).exists() and target.exists():
            raise MigrationRefused(
                "%s already exists, so moving %s onto it would overwrite the person's own work."
                % (move.destination, move.source))


def run(root: Path, dry_run: bool = False) -> list:
    """Carry out every declared operation that still has something to do."""
    operations = parse(root)
    if not operations:
        return []
    _guard(root, operations)

    carried = []
    for move in operations:
        source = root / move.source
        if not source.exists():
            continue  # already carried out, on this base or before it was ever cloned
        carried.append(move)
        if dry_run:
            continue
        destination = root / move.destination
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
    return carried
