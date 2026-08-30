#!/usr/bin/env python3
"""Bring the kit half of this base up to the version the kit ships.

An update is a REPLACEMENT, not a merge. `.engine-manifest.yml` says which
paths belong to the kit and which belong to the person; the kit's paths are
checked out from the kit remote, the person's are not touched, and the result
is one ordinary save in their own base — reversible like any other. Nobody is
ever asked to resolve an overlap in a file they did not write.

Written in python rather than shell on purpose. The engine this is modelled on
had to defend a python-to-bash boundary against CRLF-mangled paths and against
Windows rewriting a `<ref>:<path>` argument — both of which turned a broken
update into a silent success that exited 0 having applied nothing. Removing the
boundary removes the whole class, and one file runs on every platform instead of
a shell pair that has to be kept in step.

Modes
  (default)    fetch, replace the kit's paths, retire what it dropped, verify
  --dry-run    show what would change, change nothing
  --check      report whether a newer version exists; changes nothing
  --self-heal  restore the updater itself from the remote first, then re-run

The updater ships THROUGH the update, so a base carrying a broken copy can
never receive its own repair by the normal path. `--self-heal` is that path —
for a copy that still LOADS. A file python cannot even parse fails before the
flag is read, and no mode inside this file can help. That one is recovered
without python at all, and the command is the whole of it:

    git fetch harness-kit main
    git checkout harness-kit/main -- tools/update.py tools/lib .engine-manifest.yml
"""

from __future__ import annotations

import argparse
import json
import signal
import subprocess
import sys
import time
from pathlib import Path

if hasattr(signal, "SIGPIPE"):
    # Piping this into `head` closes the pipe early. That is the reader's
    # business, not a failure of the update — die quietly rather than dumping a
    # traceback over a report the person is reading.
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import manifest as manifest_lib  # noqa: E402
from lib import migrate as migrate_lib  # noqa: E402
from lib import retire as retire_lib  # noqa: E402

DEFAULT_REMOTE = "harness-kit"
DEFAULT_BRANCH = "main"
NETWORK_TIMEOUT_SECONDS = 120
VERSION_FILE = "VERSION"
# Restored before the updater is trusted to read anything. Everything the
# update mechanism itself is made of.
SELF_HEAL_PATHS = ("tools/update.py", "tools/lib", ".engine-manifest.yml")
PREFIX = "[harness-update]"


def git(*args, root: Path, timeout=None):
    """Run git in the base. Returns (returncode, stdout, stderr)."""
    try:
        done = subprocess.run(
            ["git", "-C", str(root)] + list(args),
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 124, "", "timed out after %ss" % timeout
    return done.returncode, done.stdout.rstrip("\n"), done.stderr.strip()


def git_ok(*args, root: Path, timeout=None):
    code, out, _ = git(*args, root=root, timeout=timeout)
    return out if code == 0 else None


def ref_has_path(ref: str, relpath: str, root: Path) -> bool:
    return git("cat-file", "-e", "%s:%s" % (ref, relpath), root=root)[0] == 0


def ref_read_path(ref: str, relpath: str, root: Path):
    return git_ok("show", "%s:%s" % (ref, relpath), root=root)


def read_local_version(root: Path) -> str:
    path = root / VERSION_FILE
    return path.read_text(encoding="utf-8").strip() if path.exists() else ""


def fail(message: str, *followups: str) -> int:
    print("%s %s" % (PREFIX, message), file=sys.stderr)
    for line in followups:
        print("  %s" % line, file=sys.stderr)
    return 2


def require_remote(remote: str, root: Path):
    url = git_ok("remote", "get-url", remote, root=root)
    if url:
        return url
    return None


# ---------------------------------------------------------------------------
# modes
# ---------------------------------------------------------------------------

def mode_check(root: Path, remote: str, branch: str, max_age: int) -> int:
    """Is a newer kit version out? Cheap, cached, and silent when there is nothing to say."""
    cache = root / ".git" / "harness-update-check"
    if max_age > 0 and cache.exists():
        try:
            if time.time() - json.loads(cache.read_text(encoding="utf-8"))["at"] < max_age:
                return 0
        except (ValueError, KeyError, OSError):
            pass  # unreadable cache is not a reason to skip the check

    if not require_remote(remote, root):
        return 0  # a base with no kit remote has nothing to check against

    if git("fetch", "--quiet", remote, branch, root=root,
           timeout=NETWORK_TIMEOUT_SECONDS)[0] != 0:
        return 0  # offline is not news

    try:
        cache.write_text(json.dumps({"at": time.time()}), encoding="utf-8")
    except OSError:
        pass

    here = read_local_version(root)
    there = (ref_read_path("%s/%s" % (remote, branch), VERSION_FILE, root) or "").strip()
    if there and here and there != here:
        print("%s a newer version of the kit is out: %s (this base is on %s)"
              % (PREFIX, there, here))
        print("YOU MUST: mention it once, in one plain sentence, and offer to bring it in "
              "with /harness-update. Do not explain versions unless they ask.")
    return 0


def mode_self_heal(root: Path, remote: str, branch: str, argv: list) -> int:
    print("%s self-heal: restoring the updater from %s/%s" % (PREFIX, remote, branch))
    if git("fetch", remote, branch, root=root, timeout=NETWORK_TIMEOUT_SECONDS)[0] != 0:
        return fail("could not reach the kit remote to repair from.")
    ref = "%s/%s" % (remote, branch)
    for relpath in SELF_HEAL_PATHS:
        if ref_has_path(ref, relpath, root):
            git("checkout", ref, "--", relpath, root=root)
            print("  + %s" % relpath)
    print("%s self-heal: re-running the repaired updater" % PREFIX)
    rerun = [a for a in argv if a != "--self-heal"]
    return subprocess.run([sys.executable, str(Path(__file__).resolve())] + rerun).returncode


def incoming_sections(ref: str, root: Path) -> dict:
    """What the manifest being SHIPPED declares, not what this base already knew.

    The manifest is itself one of the paths an update replaces, so anything a release declares —
    a new engine path, a move, a retirement, a seed — is invisible to a run that only reads the
    copy on disk. Falls back to the local manifest when the ref carries none, which is the shape
    of a base whose kit remote points at something that is not the kit.
    """
    text = ref_read_path(ref, manifest_lib.MANIFEST_NAME, root)
    sections = {}
    for name in ("engine", "template", "migrations", "retired"):
        if text:
            sections[name] = [p.rstrip("/") if name == "engine" else p
                              for p in manifest_lib.parse_section(name, text)]
        else:
            sections[name] = [p.rstrip("/") if name == "engine" else p
                              for p in manifest_lib.read_section(name, root)]
    return sections


def dirty_engine_paths(root: Path, ref: str, engine_paths: list) -> list:
    """Kit paths carrying uncommitted local edits.

    A path whose working tree already MATCHES the remote holds no customisation
    — there is nothing there to lose — so it is not an abort. Without that
    carve-out a self-heal deadlocks the updater against itself: the repair makes
    those paths dirty, and the very next run refuses to proceed past them.
    """
    dirty = []
    for relpath in engine_paths:
        unstaged = git("diff", "--quiet", "--", relpath, root=root)[0] != 0
        staged = git("diff", "--cached", "--quiet", "--", relpath, root=root)[0] != 0
        if not (unstaged or staged):
            continue
        if git("diff", "--quiet", ref, "--", relpath, root=root)[0] == 0:
            continue
        dirty.append(relpath)
    return dirty


def reconcile_kit_remote(root: Path, remote: str) -> str:
    """Point the kit remote at the address the kit now publishes.

    The remote lives in git config, which no manifest section reaches and no clone carries. If the
    kit ever moves, a base still pointed at the old address cannot fetch the update that would have
    told it the new one — the repair ships only through the channel that is broken. Publishing the
    new address one release BEFORE the move closes that: every base adopts it while the old address
    still works.
    """
    declared = manifest_lib.read_kit_remote(root)
    current = git_ok("remote", "get-url", remote, root=root)
    if not declared or not current or declared == current:
        return ""
    if git("remote", "set-url", remote, declared, root=root)[0] != 0:
        return ""
    return declared


def stale_global_wiring(root: Path) -> list:
    """Global agent config that no longer names this base. Reported, never edited.

    `install.sh` writes a marked block into each runtime's global entry. Nothing re-runs it, so a
    base that moved, or one wired before the contract became `AGENTS.md`, keeps a block pointing
    somewhere else — and the canon then reaches that runtime from the wrong place, or not at all.
    """
    home = Path.home()
    expected = "@%s/AGENTS.md" % root
    stale = []
    for relpath in (".claude/CLAUDE.md", ".codex/AGENTS.md"):
        entry = home / relpath
        try:
            text = entry.read_text(encoding="utf-8")
        except OSError:
            continue
        if "BEGIN HARNESS-KIT" in text and expected not in text and str(root) not in text:
            stale.append(str(entry))
    return stale


def seed_missing_templates(root: Path, ref: str) -> list:
    """Create the seed files this base never received; never touch one it already has.

    A template seeds at clone time and an update leaves it alone — that is what keeps a person's
    own rows safe. But a template ADDED after their clone therefore reaches them never, while the
    canon arriving in the same update names it as though it were there. Creating only what is
    absent keeps both properties: nothing of theirs is overwritten, and the file the rules point
    at exists.
    """
    created = []
    for relpath in manifest_lib.read_section("template", root):
        if (root / relpath).exists() or not ref_has_path(ref, relpath, root):
            continue
        git("checkout", ref, "--", relpath, root=root)
        if (root / relpath).exists():
            created.append(relpath)
    return created


def mode_apply(root: Path, remote: str, branch: str, dry_run: bool) -> int:
    if not require_remote(remote, root):
        address = manifest_lib.read_kit_remote(root)
        return fail(
            "this base is not connected to the kit it came from, so it cannot be updated.",
            "This is normal on a device that only ever cloned their base: the connection is",
            "machine-local and no clone carries it. Tell the person in their words, then:",
            "  git remote add %s %s" % (remote, address or "<the kit's repository>"),
        )

    ref = "%s/%s" % (remote, branch)
    print("%s fetching %s ..." % (PREFIX, ref))
    if git("fetch", remote, branch, root=root, timeout=NETWORK_TIMEOUT_SECONDS)[0] != 0:
        return fail("could not reach the kit remote. Nothing changed.")

    engine_paths = [p.rstrip("/") for p in manifest_lib.read_section("engine", root)]
    if not engine_paths:
        return fail("the manifest lists no kit paths — nothing could be updated safely.")

    dirty = dirty_engine_paths(root, ref, engine_paths)
    if dirty:
        return fail(
            "these kit paths have unsaved local edits and would be overwritten:",
            *(["  %s" % p for p in dirty]
              + ["Save or undo them first. Editing a kit path is itself the problem:",
                 "it survives exactly until the next update (doctrine/kit-ownership.md)."]),
        )

    version_before = read_local_version(root)
    version_upstream = (ref_read_path(ref, VERSION_FILE, root) or "").strip()

    incoming = incoming_sections(ref, root)

    if dry_run:
        print("%s dry-run — would replace these from %s:" % (PREFIX, ref))
        for relpath in sorted(set(engine_paths) | set(incoming["engine"])):
            if not ref_has_path(ref, relpath, root):
                continue
            # `-R` reverses the direction: without it this reads ref -> here,
            # so everything the update ADDS renders as a deletion.
            stat = git_ok("diff", "--stat", "-R", ref, "--", relpath, root=root)
            print("  - %s%s" % (relpath, "" if not stat else "\n      " + stat.replace("\n", "\n      ")))
        for relpath in incoming["template"]:
            if not (root / relpath).exists() and ref_has_path(ref, relpath, root):
                print("  + add %s (a seed this base never received)" % relpath)
        for move in migrate_lib.run(root, dry_run=True, entries=incoming["migrations"]):
            print("  > move %s to %s" % (move.source, move.destination))
        removed = retire_lib.run(root, dry_run=True, entries=incoming["retired"])
        for relpath in removed:
            print("  - drop %s (the kit no longer has it)" % relpath)
        print("%s dry-run: %s -> %s. Nothing applied." % (PREFIX, version_before or "?",
                                                          version_upstream or "?"))
        return 0

    seeded = seed_missing_templates(root, ref)
    resolved, absent, changed = 0, 0, 0
    changed_paths, added_paths = [], []

    # A path this release ADDS to engine: is not in the list read from the manifest that was on
    # disk when the run began — that manifest is itself one of the paths being replaced. Without
    # this the new file lands one whole update late, and the run that ships it says nothing.
    newly_declared = [p for p in incoming["engine"] if p not in engine_paths]
    for relpath in engine_paths + newly_declared:
        if not ref_has_path(ref, relpath, root):
            absent += 1
            continue
        if git("diff", "--quiet", ref, "--", relpath, root=root)[0] != 0:
            changed += 1
            (added_paths if relpath in newly_declared else changed_paths).append(relpath)
        git("checkout", ref, "--", relpath, root=root)
        resolved += 1

    # A run that resolves nothing is a broken update, not an up-to-date base, and
    # the two are indistinguishable without this check — which is exactly how an
    # engine once reported success for weeks while applying nothing at all.
    if resolved == 0:
        return fail(
            "not one of the %d kit paths was found in %s." % (len(engine_paths), ref),
            "That is never the shape of an up-to-date base — the kit would have to have",
            "deleted itself. Something mangled the paths before git saw them.",
            "Recover with: python3 tools/update.py --self-heal",
        )

    # The two passes are independent, so one refusing must not cancel the other. Returning on the
    # first refusal left every declared deletion undone for as long as an unrelated move stayed
    # blocked — and said nothing about it, so nobody could know retirement had been skipped.
    carried, removed, blocked = [], [], []
    try:
        carried = migrate_lib.run(root)
    except migrate_lib.MigrationRefused as refusal:
        blocked.append("a declared change could not be carried out: %s" % refusal)

    try:
        removed = retire_lib.run(root)
    except retire_lib.RetirementRefused as refusal:
        blocked.append("refusing to drop paths that belong to the person, not the kit: %s"
                       % ", ".join(refusal.trespassing))

    if blocked:
        return fail(*(blocked + [
            "The kit paths above are already in place and anything that COULD be carried out was.",
            "Nothing was moved or deleted that is named here; running the update again is safe.",
        ]))

    version_after = read_local_version(root)
    if version_upstream and version_after != version_upstream:
        return fail(
            "%s reads '%s' after the update but the kit ships '%s'."
            % (VERSION_FILE, version_after or "?", version_upstream),
            "The checkout did not land what it reported. Nothing was rolled back;",
            "inspect with: git status",
        )

    moved_address = reconcile_kit_remote(root, remote)
    print("%s %d kit path(s) checked, %d changed, %d absent, %d added, %d dropped — %s -> %s"
          % (PREFIX, resolved, changed, absent, len(seeded), len(removed),
             version_before or "?", version_after or "?"))
    # Name every path, never just a count: an overwrite the person cannot see is one they cannot
    # object to, and `.claude/settings.json` is a kit path they may well have edited.
    for relpath in changed_paths:
        print("  ~ replaced %s" % relpath)
    for relpath in added_paths:
        print("  ~ replaced %s (a kit path this release introduced)" % relpath)
    for relpath in seeded:
        print("  + added %s (a seed this base never received)" % relpath)
    for relpath in removed:
        print("  - dropped %s" % relpath)
    for move in carried:
        print("  > moved %s to %s%s"
              % (move.source, move.destination, " — %s" % move.note if move.note else ""))
    if moved_address:
        print("  = the kit now lives at %s; this base follows it from the next update"
              % moved_address)
    for entry in stale_global_wiring(root):
        print("  ! %s still points somewhere else — that runtime is not reading this base" % entry)
    if not changed and not removed and not seeded and not carried:
        print("YOU MUST: nothing arrived — the base was already current. Say so in one short "
              "line only if the person asked; otherwise say nothing.")
        return 0
    print("YOU MUST: read CHANGELOG.md for what landed between those two versions, tell the "
          "person in one or two plain sentences what it means for THEM — not what changed in "
          "the kit — and save (python3 tools/sync.py save \"...\"). If none of it touches how "
          "they work, say that plainly and save anyway.")
    return 0


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description="Update the kit half of this base")
    parser.add_argument("--remote", default=DEFAULT_REMOTE)
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true",
                        help="report whether a newer version exists; change nothing")
    parser.add_argument("--max-age", type=int, default=0,
                        help="with --check: stay silent if the last check is younger than this")
    parser.add_argument("--self-heal", action="store_true")
    args = parser.parse_args(argv[1:])

    root = manifest_lib.repo_root()
    if git_ok("rev-parse", "--is-inside-work-tree", root=root) != "true":
        return fail("this base is not tracked, so there is nothing to update from.")

    if args.self_heal:
        return mode_self_heal(root, args.remote, args.branch, argv[1:])
    if args.check:
        return mode_check(root, args.remote, args.branch, args.max_age)
    return mode_apply(root, args.remote, args.branch, args.dry_run)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
