#!/usr/bin/env python3
"""The single reader of `.engine-manifest.yml`.

Dependency-free on purpose. The manifest is a flat document — two scalars
and five lists of path entries — and every machine running this kit has a stock
python and nothing else guaranteed. A YAML library would be a second reader to
keep in step and one more thing a person has to install before their base can
update itself.
"""

from __future__ import annotations

import re
from pathlib import Path

MANIFEST_NAME = ".engine-manifest.yml"
LIST_SECTIONS = ("engine", "template", "exclude", "retired", "migrations")

_ENTRY = re.compile(r"^\s*-\s+(.+?)\s*$")
# YAML ends a scalar at a `#` preceded by whitespace. Miss that and an entry
# carrying a trailing note — `.gitattributes  # forces LF` — reaches the caller
# as a path that does not exist, which every consumer then reads as "absent".
_INLINE_COMMENT = re.compile(r"\s+#.*$")
_VERSION = re.compile(r"^version:\s*(.+?)\s*$", re.M)
_KIT_REMOTE = re.compile(r"^kit_remote:\s*(.+?)\s*$", re.M)


def repo_root() -> Path:
    """The base root — the parent of `tools/`, resolved from this file."""
    return Path(__file__).resolve().parents[2]


def manifest_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / MANIFEST_NAME


def read_section(section: str, root: Path | None = None) -> list[str]:
    """One list-shaped section of the manifest on disk."""
    return parse_section(section, manifest_path(root).read_text(encoding="utf-8"))


def parse_section(section: str, text: str) -> list[str]:
    """One list-shaped section of any manifest text, in document order.

    Separated from the file read so the same parser serves the manifest a base has and the one a
    release is bringing it — an update has to be able to see what the INCOMING manifest declares,
    not only what the base already knew.
    """
    if section not in LIST_SECTIONS:
        raise ValueError("%r is not a list-shaped manifest section" % section)
    entries: list[str] = []
    current: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if not line.startswith((" ", "\t", "-")):
            current = line.split(":", 1)[0].strip()
            continue
        if current != section:
            continue
        match = _ENTRY.match(line)
        if match:
            value = _INLINE_COMMENT.sub("", match.group(1)).strip().strip('"').strip("'")
            if value:
                entries.append(value)
    return entries


def declares_section(section: str, root: Path | None = None) -> bool:
    """Whether the manifest names this section at all.

    `read_section` cannot tell `engine: []` from a manifest that lost the key: both read as empty,
    and the two mean opposite things. An empty list is a base that deliberately shares no paths
    with the kit — its own harness, updated by hand — while a missing key is a corrupt file whose
    update would report success having done nothing.
    """
    pattern = re.compile(r"^%s\s*:" % re.escape(section), re.M)
    return bool(pattern.search(manifest_path(root).read_text(encoding="utf-8")))


def read_version(root: Path | None = None) -> str:
    """The kit version the manifest declares, or an empty string."""
    match = _VERSION.search(manifest_path(root).read_text(encoding="utf-8"))
    return match.group(1).strip() if match else ""


def covers(entries, relpath: str) -> bool:
    """True when any entry covers this path, whether or not it was written as a directory.

    A directory entry carries a trailing slash and the path being classified does not, so asking
    the raw question misses every directory — which is the shape a guard fails silently in.
    """
    shapes = (relpath, relpath.rstrip("/") + "/")
    return any(covered_by(entry, shape) for entry in entries for shape in shapes)


def read_kit_remote(root: Path | None = None) -> str:
    """The kit's own address, so a base that lost the remote is reconnected without guessing."""
    match = _KIT_REMOTE.search(manifest_path(root).read_text(encoding="utf-8"))
    return match.group(1).strip() if match else ""


def covered_by(entry: str, relpath: str) -> bool:
    """True when `relpath` falls under one manifest entry.

    `*/` covers the SUBDIRECTORIES of a directory and not the files sitting
    directly in it. Reading the star as a plain prefix looks like the cautious
    choice and is not: it swallows sibling files into the covered set, and a
    guard built on it then refuses the very work it exists to permit. A guard
    that over-covers does not fail safe — it fails shut.
    """
    entry = entry.strip()
    if not entry:
        return False
    if entry.endswith("*/"):
        prefix = entry[:-2]
        return relpath.startswith(prefix) and "/" in relpath[len(prefix):]
    if entry.endswith("/"):
        return relpath.startswith(entry)
    return relpath == entry
