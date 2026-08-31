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
# Said whenever a recovery command needs the kit remote. Both remedies reach the kit through a
# remote named `harness-kit`, which lives in git config and which no clone carries, so the
# device that most needs the instruction is the one least likely to have it already.
KIT_REMOTE_FALLBACK = (
    "  Neither works without a connection to the kit. If git says there is no\n"
    "  such remote, add it first:\n"
    "    git remote add harness-kit <the address the kit lives at>\n")
LIST_SECTIONS = ("engine", "template", "exclude", "retired", "migrations")

_ENTRY = re.compile(r"^\s*-\s+(.+?)\s*$")
# YAML ends a scalar at a `#` preceded by whitespace. Miss that and an entry
# carrying a trailing note — `.gitattributes  # forces LF` — reaches the caller
# as a path that does not exist, which every consumer then reads as "absent".
_INLINE_COMMENT = re.compile(r"\s+#.*$")
_VERSION = re.compile(r"^version:\s*(.+?)\s*$", re.M)
_KIT_REMOTE = re.compile(r"^kit_remote:\s*(.+?)\s*$", re.M)


class ManifestMissing(FileNotFoundError):
    """The manifest is not on disk. Nothing that reads it can proceed.

    Raised here rather than left as a bare `FileNotFoundError` so the three tools can say what to
    do about it. The base that most needs `--self-heal` is exactly the base whose manifest is
    gone, and a traceback is not a recovery instruction.
    """


def explain_refusal(problem) -> str:
    """What to DO about a contract that cannot be read, for the person holding the broken base.

    The two ways it fails are opposite and the remedies differ, but neither is a traceback: the
    base that most needs a recovery command is exactly the one whose machinery just refused.
    Both tools that read the manifest print this, so the wording exists once.
    """
    if isinstance(problem, ManifestMissing):
        return ("the kit/person contract is missing: %s\n"
                "  Nothing can tell a kit path from a person's without it, so no tool\n"
                "  here will guess. Restore it with:\n"
                "    git checkout harness-kit/main -- %s\n"
                "  or, if the machinery is damaged too:\n"
                "    python3 tools/update.py --self-heal\n"
                "%s" % (problem, MANIFEST_NAME, KIT_REMOTE_FALLBACK))
    return ("the kit/person contract cannot be trusted: %s\n"
            "  An entry that reaches outside this base would be deleted, moved or\n"
            "  overwritten on the next update, so nothing here will act on the file\n"
            "  at all. Open %s and remove the entry named above, or restore it:\n"
            "    git checkout harness-kit/main -- %s\n"
            "  or, if the machinery is damaged too:\n"
            "    python3 tools/update.py --self-heal\n"
            "%s" % (problem, MANIFEST_NAME, MANIFEST_NAME, KIT_REMOTE_FALLBACK))


class UnsafeEntry(ValueError):
    """A manifest entry that would reach outside the base.

    Every consumer of this file turns entries into filesystem operations — `retire` DELETES them,
    `migrate` MOVES them, `update` checks them out. The containment guards those passes carry are
    string comparisons against `exclude:`, and a string comparison cannot see that `../x` leaves
    the base or that an absolute path was never inside it. So containment belongs here, at the one
    place every entry passes through, and it is a refusal rather than a silent repair: rewriting
    `../secrets` into `secrets` would delete a different real file and report success.
    """


def safe_entry(raw: str, section: str = "") -> str:
    """One manifest entry, normalised, or a refusal. The only way an entry becomes a path.

    Normalises `./x` to `x` — the same path written two ways, and the second slips past every
    `startswith` check in the kit. Refuses anything absolute, anything with a `..` component, and
    anything with a Windows drive or UNC prefix, because no legitimate entry needs one and every
    illegitimate one does.
    """
    entry = raw.strip().replace("\\", "/")
    where = " in %s:" % section if section else ":"
    if not entry:
        raise UnsafeEntry("an empty manifest entry%s nothing can be done with it" % where)
    if entry.startswith("/") or entry.startswith("~"):
        raise UnsafeEntry("an absolute manifest entry%s %r — entries are relative to the base"
                          % (where, raw))
    if len(entry) > 1 and entry[1] == ":":
        raise UnsafeEntry("a drive-qualified manifest entry%s %r" % (where, raw))
    trailing = "/" if entry.endswith("/") else ""
    parts = [p for p in entry.split("/") if p not in ("", ".")]
    if ".." in parts:
        raise UnsafeEntry("a manifest entry that climbs out of the base%s %r" % (where, raw))
    if not parts:
        raise UnsafeEntry("a manifest entry that names the base itself%s %r" % (where, raw))
    return "/".join(parts) + trailing


def contains(root: Path, relpath: str) -> bool:
    """Whether a path resolves inside the base. The check a string comparison cannot make.

    Defence in depth behind `safe_entry`: a symlink inside the base can still point out of it, and
    that is invisible to any amount of text inspection.
    """
    try:
        target = (root / relpath).resolve()
        base = root.resolve()
    except OSError:
        return False
    return target == base or base in target.parents


def repo_root() -> Path:
    """The base root — the parent of `tools/`, resolved from this file."""
    return Path(__file__).resolve().parents[2]


def manifest_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / MANIFEST_NAME


def manifest_text(root: Path | None = None) -> str:
    """The manifest's text. The single read — every other reader goes through this one.

    Not named `read_text`: at module level that reads as `Path.read_text` to everything that
    looks at this file, the portability gate included, and a name that has to be explained is
    the wrong name.
    """
    path = manifest_path(root)
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ManifestMissing(str(path))


def read_section(section: str, root: Path | None = None) -> list[str]:
    """One list-shaped section of the manifest on disk."""
    return parse_section(section, manifest_text(root))


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
                # `migrations:` entries are operations (`move a -> b | note`), not paths; their
                # own parser checks each side. Everything else IS a path and is contained here.
                entries.append(value if section == "migrations"
                               else safe_entry(value, section))
    return entries


def declares_section(section: str, root: Path | None = None) -> bool:
    """Whether the manifest names this section at all.

    `read_section` cannot tell `engine: []` from a manifest that lost the key: both read as empty,
    and the two mean opposite things. An empty list is a base that deliberately shares no paths
    with the kit — its own harness, updated by hand — while a missing key is a corrupt file whose
    update would report success having done nothing.
    """
    pattern = re.compile(r"^%s\s*:" % re.escape(section), re.M)
    return bool(pattern.search(manifest_text(root)))


def read_version(root: Path | None = None) -> str:
    """The kit version the manifest declares, or an empty string."""
    match = _VERSION.search(manifest_text(root))
    return match.group(1).strip() if match else ""


def covers(entries, relpath: str) -> bool:
    """True when any entry covers this path, whether or not it was written as a directory.

    A directory entry carries a trailing slash and the path being classified does not, so asking
    the raw question misses every directory — which is the shape a guard fails silently in.
    """
    shapes = (relpath, relpath.rstrip("/") + "/")
    return any(covered_by(entry, shape) for entry in entries for shape in shapes)


def same_repository(a: str, b: str) -> bool:
    """Two URLs naming the same repository. Mirror of `same_repo` in install.sh.

    Lives beside `read_kit_remote` because it is a fact about kit addresses. It had two identical
    copies — one deciding which remote the updater fetches from, one deciding whether a release
    is a fork that kept the upstream address. The gate's whole job is to predict what the updater
    will do, so a rule gained by one and not the other passes a fork whose bases are then pulled
    back upstream.
    """
    if not a or not b:
        return False
    normalise = lambda url: url.strip().rstrip("/").removesuffix(".git").lower()
    return normalise(a) == normalise(b)


def files_under(root: Path, entry: str) -> set:
    """Repo-relative POSIX paths one manifest directory entry covers, right now, on disk."""
    target = root / entry.rstrip("/")
    if target.is_dir():
        return {str(p.relative_to(root)).replace("\\", "/")
                for p in target.rglob("*") if p.is_file()}
    return {entry.rstrip("/")} if target.is_file() else set()


def read_kit_remote(root: Path | None = None) -> str:
    """The kit's own address, so a base that lost the remote is reconnected without guessing."""
    match = _KIT_REMOTE.search(manifest_text(root))
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
