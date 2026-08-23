#!/usr/bin/env python3
"""The single reader of `.engine-manifest.yml`.

Dependency-free on purpose. The manifest is a flat document — a version scalar
and five lists of path entries — and every machine running this kit has a stock
python and nothing else guaranteed. A YAML library would be a second reader to
keep in step and one more thing a person has to install before their base can
update itself.
"""

from __future__ import annotations

import re
from pathlib import Path

MANIFEST_NAME = ".engine-manifest.yml"
LIST_SECTIONS = ("engine", "template", "exclude", "retired")

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
    """One list-shaped section, in document order, comments and blanks dropped."""
    if section not in LIST_SECTIONS:
        raise ValueError("%r is not a list-shaped manifest section" % section)
    entries: list[str] = []
    current: str | None = None
    for raw in manifest_path(root).read_text(encoding="utf-8").splitlines():
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


def read_version(root: Path | None = None) -> str:
    """The kit version the manifest declares, or an empty string."""
    match = _VERSION.search(manifest_path(root).read_text(encoding="utf-8"))
    return match.group(1).strip() if match else ""


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
