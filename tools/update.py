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
from typing import NamedTuple

if hasattr(signal, "SIGPIPE"):
    # Piping this into `head` closes the pipe early. That is the reader's
    # business, not a failure of the update — die quietly rather than dumping a
    # traceback over a report the person is reading.
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import gitrun  # noqa: E402
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
# The line an agent is required to act on. One spelling, in one place: it is the contract
# between these scripts and whatever is reading their output.
DIRECTIVE = "YOU MUST:"


def git(*args, root: Path, timeout=None):
    """Run git in `root`. One binding of `gitrun.run`, so every call here shares its contract."""
    return gitrun.run(root, *args, timeout=timeout)


def git_ok(*args, root: Path, timeout=None):
    """Output when git succeeded, else None. Only where empty and failed mean the same thing."""
    return gitrun.ok(root, *args, timeout=timeout)


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


def resolve_remote(remote: str, root: Path):
    """(name, url) of the remote this base updates from — found by ADDRESS, then by name.

    The name is a convenience, never the contract. The installer already identifies the kit by the
    address the manifest declares rather than by whether a name contains a particular word, and
    this is the other half of that: a base whose kit remote was set up under some other name, or
    whose kit is renamed as a product, still updates. Only the address is stable — it is the one
    thing the kit itself publishes and can move deliberately (`reconcile_kit_remote`).

    Falls back to the configured name so a base whose manifest declares no address, or one whose
    remote is a local path used for testing, behaves exactly as before.
    """
    declared = manifest_lib.read_kit_remote(root)
    if declared:
        for name in (git_ok("remote", root=root) or "").split():
            url = git_ok("remote", "get-url", name, root=root)
            if manifest_lib.same_repository(url, declared):
                return name, url
    url = git_ok("remote", "get-url", remote, root=root)
    return (remote, url) if url else (remote, None)


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

    remote, url = resolve_remote(remote, root)
    if not url:
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
        print(DIRECTIVE + " mention it once, in one plain sentence, and offer to bring it in "
              "with /harness-update. Do not explain versions unless they ask.")
    return 0


def mode_self_heal(root: Path, remote: str, branch: str, argv: list) -> int:
    remote = resolve_remote(remote, root)[0]
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


class Incoming(NamedTuple):
    """What the manifest being SHIPPED declares. Named so a typo is an error, not an empty list."""
    engine: list
    template: list
    exclude: list
    migrations: list
    retired: list


def incoming_sections(ref: str, root: Path) -> Incoming:
    """What the manifest being SHIPPED declares, not what this base already knew.

    The manifest is itself one of the paths an update replaces, so anything a release declares —
    a new engine path, a move, a retirement, a seed — is invisible to a run that only reads the
    copy on disk. Falls back to the local manifest when the ref carries none, which is the shape
    of a base whose kit remote points at something that is not the kit.
    """
    text = ref_read_path(ref, manifest_lib.MANIFEST_NAME, root)
    sections = {}
    for name in Incoming._fields:
        entries = (manifest_lib.parse_section(name, text) if text
                   else manifest_lib.read_section(name, root))
        sections[name] = [p.rstrip("/") for p in entries] if name == "engine" else list(entries)
    return Incoming(**sections)


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


def seed_missing_templates(root: Path, ref: str, declared: list) -> list:
    """Create the seed files this base never received; never touch one it already has.

    A template seeds at clone time and an update leaves it alone — that is what keeps a person's
    own rows safe. But a template ADDED after their clone therefore reaches them never, while the
    canon arriving in the same update names it as though it were there. Creating only what is
    absent keeps both properties: nothing of theirs is overwritten, and the file the rules point
    at exists.

    `declared` is the template list from the manifest being SHIPPED, not the one on disk. Reading
    the local copy made the promise above false in its own headline case: a seed introduced by
    this release is not in the manifest the base still has, so it arrived one update late — while
    the dry-run, which already read the incoming list, promised it now.
    """
    created = []
    for relpath in declared:
        if (root / relpath).exists() or not ref_has_path(ref, relpath, root):
            continue
        git("checkout", ref, "--", relpath, root=root)
        if (root / relpath).exists():
            created.append(relpath)
    return created


def enclosing_repository(root: Path):
    """The repository this base sits inside, when the base is not one itself.

    `git -C <base>` answers for whichever repository encloses the base, so a base with no `.git`
    of its own silently borrows another one — and an update would then check kit paths out over
    that repository's worktree and delete from it.
    """
    code, toplevel = git("rev-parse", "--show-toplevel", root=root)[:2]
    if code != 0 or not toplevel:
        return None
    return None if Path(toplevel).resolve() == root.resolve() else toplevel


def preview(root: Path, ref: str, engine_paths: list, incoming: Incoming,
            protected_before: list, version_before: str, version_upstream: str) -> int:
    """What an update WOULD do, said in the terms the real run uses.

    Extracted from `mode_apply`, where it was a second program inside the first — its own
    output vocabulary, its own refusal handling and its own early return, reachable only by
    spawning the script against a configured remote.
    """
    print("%s dry-run — would replace these from %s:" % (PREFIX, ref))
    for relpath in sorted(set(engine_paths) | set(incoming.engine)):
        if not ref_has_path(ref, relpath, root):
            continue
        # `-R` reverses the direction: without it this reads ref -> here,
        # so everything the update ADDS renders as a deletion.
        stat = git_ok("diff", "--stat", "-R", ref, "--", relpath, root=root)
        print("  - %s%s" % (relpath, "" if not stat else "\n      " + stat.replace("\n", "\n      ")))
    for relpath in incoming.template:
        if not (root / relpath).exists() and ref_has_path(ref, relpath, root):
            print("  + add %s (a seed this base never received)" % relpath)
    # The guards inside these two read `engine:`/`exclude:` from the manifest on disk, which
    # a real run reads only AFTER the replacement. A release that moves a path between
    # sections and migrates or retires under it in the same release would therefore preview
    # against one manifest and apply against another; a refusal is reported as a refusal
    # rather than crashing the preview.
    try:
        for move in migrate_lib.run(root, dry_run=True, entries=incoming.migrations):
            print("  > move %s to %s" % (move.source, move.destination))
    except migrate_lib.MigrationRefused as refusal:
        print("  ! a declared move cannot be previewed from this base yet: %s" % refusal)
    try:
        removed = retire_lib.run(
            root, dry_run=True, entries=incoming.retired,
            protected=sorted(set(protected_before) | set(incoming.exclude)))
    except retire_lib.RetirementRefused as refusal:
        print("  ! a declared removal names paths this base calls its own: %s"
              % ", ".join(refusal.trespassing))
        removed = []
    for relpath in removed:
        print("  - drop %s (the kit no longer has it)" % relpath)
    print("%s dry-run: %s -> %s. Nothing applied." % (PREFIX, version_before or "?",
                                                      version_upstream or "?"))
    return 0



def report(root: Path, remote: str, resolved: int, changed: int, absent: int,
           changed_paths: list, added_paths: list, seeded: list, removed: list,
           carried: list, version_before: str, version_after: str) -> int:
    """Say what happened, path by path, and what the agent must do with it.

    An overwrite the person cannot see is one they cannot object to, so this names every
    path rather than a count. Extracted for the same reason as `preview`: reporting is a
    different job from deciding.
    """
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
        print(DIRECTIVE + " nothing arrived — the base was already current. Say so in one short "
              "line only if the person asked; otherwise say nothing.")
        return 0
    print(DIRECTIVE + " read CHANGELOG.md for what landed between those two versions, tell the "
          "person in one or two plain sentences what it means for THEM — not what changed in "
          "the kit — and save (python3 tools/sync.py save \"...\"). If none of it touches how "
          "they work, say that plainly and save anyway.")
    return 0


def mode_apply(root: Path, remote: str, branch: str, dry_run: bool,
               confirmed: bool = False) -> int:
    enclosing = enclosing_repository(root)
    if enclosing:
        return fail(
            "this base has no history of its own — it sits inside %s." % enclosing,
            "Every path below would be written into THAT repository, and the retirement pass",
            "would delete from it. Nothing has been touched. The base has to be its own thing",
            "before it can be updated: tell the person in their words, then set it up.",
        )
    remote, url = resolve_remote(remote, root)
    if not url:
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
        if manifest_lib.declares_section("engine", root):
            # Declared empty: a base that shares no paths with the kit. Not a fault — its own
            # canon is its own, and adopting a kit path is a decision made one path at a time.
            print("%s this base shares no paths with the kit, so an update has nothing to "
                  "replace." % PREFIX)
            print(DIRECTIVE + " say nothing unless asked. Adopting a kit path is a deliberate "
                  "choice — read the manifest's header before adding one to engine:.")
            return 0
        return fail("the manifest has no engine: section — nothing could be updated safely.",
                    "Either it is corrupt or it was never written. An update that replaces",
                    "nothing and reports success is indistinguishable from one that worked.")

    # Read the manifest being SHIPPED before anything is touched. Everything below — what to
    # guard, what to seed, what to replace — is decided by what the RELEASE declares, not by what
    # this base still happens to hold.
    incoming = incoming_sections(ref, root)
    # Read BEFORE the checkout replaces the manifest. What the base already treats as the
    # person's space cannot be revoked by the release doing the replacing.
    protected_before = manifest_lib.read_section("exclude", root)

    # A path this release ADDS to engine: has to be guarded BEFORE it is replaced, and it is the
    # likeliest of all of them to collide: until this run it was the person's own space, so
    # whatever is sitting there is theirs. Computing it here rather than at the checkout loop is
    # the whole point — the one pass whose job is preventing loss cannot run after the loss.
    adopted = [p for p in incoming.engine if p not in engine_paths]
    dirty = dirty_engine_paths(root, ref, engine_paths + adopted)
    if dirty:
        return fail(
            "these kit paths have unsaved local edits and would be overwritten:",
            *(["  %s" % p for p in dirty]
              + ["Save or undo them first. Editing a kit path is itself the problem:",
                 "it survives exactly until the next update (doctrine/kit-ownership.md)."]),
        )

    version_before = read_local_version(root)
    version_upstream = (ref_read_path(ref, VERSION_FILE, root) or "").strip()


    if dry_run:
        return preview(root, ref, engine_paths, incoming,
                       protected_before, version_before, version_upstream)

    seeded = seed_missing_templates(root, ref, incoming.template)
    resolved, absent, changed = 0, 0, 0
    changed_paths, added_paths = [], []

    # A path this release ADDS to engine: is not in the list read from the manifest that was on
    # disk when the run began — that manifest is itself one of the paths being replaced. Without
    # this the new file lands one whole update late, and the run that ships it says nothing.
    for relpath in engine_paths + adopted:
        if not ref_has_path(ref, relpath, root):
            absent += 1
            continue
        if git("diff", "--quiet", ref, "--", relpath, root=root)[0] != 0:
            changed += 1
            (added_paths if relpath in adopted else changed_paths).append(relpath)
        git("checkout", ref, "--", relpath, root=root)
        resolved += 1

    # A run that resolves nothing is a broken update, not an up-to-date base, and without this
    # check the two are indistinguishable: an engine that applies nothing reports success.
    if resolved == 0:
        return fail(
            "not one of the %d kit paths was found in %s."
            % (len(engine_paths) + len(adopted), ref),
            "That is never the shape of an up-to-date base — the kit would have to have",
            "deleted itself. Something mangled the paths before git saw them.",
            "Recover with: python3 tools/update.py --self-heal",
        )

    # `rules/safety.md` and `rules/git-safety.md` both require a deletion to be confirmed before
    # it runs. An update that silently deletes and moves on the strength of a file it just
    # fetched breaks the kit's own hard rule, so anything destructive stops here the first time
    # and names itself. Replacement is not affected: an update with nothing to delete or move
    # runs exactly as before, which is almost all of them.
    # A refusal here is reported by the real pass below, which knows how to say it; this
    # preview only decides whether the person has to see the moves first.
    try:
        pending_moves = migrate_lib.run(root, dry_run=True)
    except migrate_lib.MigrationRefused:
        pending_moves = []
    # Retirement is the other half of replacement — the kit withdrawing its own path, already
    # fenced off from the person's space by a protection that can only widen. So it runs here,
    # BEFORE the gate below: holding the kit's own withdrawal behind a confirmation that is
    # about the person's files leaves every declared deletion undone for as long as an
    # unrelated move stays unconfirmed, and nothing in the output would say so.
    carried, removed, blocked = [], [], []
    try:
        removed = retire_lib.run(
            root, protected=sorted(set(protected_before) | set(incoming.exclude)))
    except retire_lib.RetirementRefused as refusal:
        blocked.append("refusing to drop paths that belong to the person, not the kit: %s"
                       % ", ".join(refusal.trespassing))

    # A MOVE is different in kind: `migrations:` exists precisely to rearrange the person's own
    # space, so it is the one thing here that changes their files rather than the kit's, and
    # `rules/safety.md` requires it to be seen before it runs.
    if pending_moves and not confirmed and not blocked:
        print("%s this update wants to move things in the person's own space:" % PREFIX)
        for move in pending_moves:
            print("  > move %s to %s%s"
                  % (move.source, move.destination, " — %s" % move.note if move.note else ""))
        print("%s the kit paths above are already replaced%s. Nothing of the person's has moved."
              % (PREFIX, ", and what the kit withdrew is gone" if removed else ""))
        print(DIRECTIVE + " tell the person in plain words what is about to move and what it means "
              "for them — these are their own files, not the kit's — then run the same command "
              "with --confirm once they are content.")
        return 0

    # The two passes are independent, so one refusing must not cancel the other: returning on the
    # first refusal leaves every declared deletion undone for as long as an unrelated move stays
    # blocked, and says nothing about it.
    try:
        carried = migrate_lib.run(root)
    except migrate_lib.MigrationRefused as refusal:
        blocked.append("a declared change could not be carried out: %s" % refusal)

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

    return report(root, remote, resolved, changed, absent, changed_paths, added_paths,
                  seeded, removed, carried, version_before, version_after)


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
    parser.add_argument("--confirm", action="store_true",
                        help="proceed with declared deletions and moves after seeing them")
    args = parser.parse_args(argv[1:])

    root = manifest_lib.repo_root()
    if git_ok("rev-parse", "--is-inside-work-tree", root=root) != "true":
        return fail("this base is not tracked, so there is nothing to update from.")

    if args.self_heal:
        return mode_self_heal(root, args.remote, args.branch, argv[1:])
    if args.check:
        return mode_check(root, args.remote, args.branch, args.max_age)
    return mode_apply(root, args.remote, args.branch, args.dry_run, args.confirm)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except (manifest_lib.ManifestMissing, manifest_lib.UnsafeEntry) as problem:
        # A base whose contract is gone or untrustworthy is exactly the base that needs a
        # recovery command, and a traceback is not one.
        sys.stderr.write(manifest_lib.explain_refusal(problem))
        sys.exit(2)

