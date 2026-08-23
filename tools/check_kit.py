#!/usr/bin/env python3
"""Author-side gate: prove this kit can be shipped before anyone runs it.

Every failure below is one a person would otherwise meet on their own machine, where nobody can
see it and they cannot diagnose it. The discipline is the author's tax; the point of paying it
here is that the people running the kit never do.

Structural checks run anywhere, including on a person's base — that is what `/harness-doctor`
calls. The `--authoring` checks compare this working tree against the release branch and only make
sense in the kit's own repository; run them before every release.

Usage:
  python3 tools/check_kit.py                  # structural — safe on any base
  python3 tools/check_kit.py --authoring      # everything, before shipping a release
  python3 tools/check_kit.py --authoring --since <ref>
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import manifest as manifest_lib  # noqa: E402

RELEASE_REF = "main"
PLUGIN_MANIFEST = ".claude-plugin/plugin.json"


def git(*args, root: Path):
    done = subprocess.run(["git", "-C", str(root)] + list(args), capture_output=True, text=True)
    return done.returncode, done.stdout.rstrip("\n")


def files_under(root: Path, entry: str) -> set:
    """Concrete repo-relative files one manifest entry covers, right now, on disk."""
    target = root / entry.rstrip("/")
    if target.is_dir():
        return {str(p.relative_to(root)).replace(os.sep, "/")
                for p in target.rglob("*") if p.is_file()}
    return {entry} if target.is_file() else set()


def check_paths_exist(root, engine, template, fail):
    for entry in engine:
        if not (root / entry.rstrip("/")).exists():
            fail("engine path does not exist: %s" % entry,
                 "It reaches nobody — the updater skips what it cannot find.")
    for entry in template:
        if not (root / entry).exists():
            fail("template path does not exist: %s" % entry,
                 "A base cloned today would be missing a file the kit assumes is there.")


def check_no_double_listing(engine, template, fail):
    overlap = {e.rstrip("/") for e in engine} & {t.rstrip("/") for t in template}
    for entry in sorted(overlap):
        fail("listed as both engine and template: %s" % entry,
             "engine wins on update and would overwrite what the person put in it.")


def check_retired(root, engine, template, exclude, retired, fail):
    for entry in retired:
        if (root / entry).exists():
            fail("retired path still ships: %s" % entry,
                 "Every update would check it out and then delete it again, forever.")
        if any(manifest_lib.covered_by(e, entry) for e in exclude):
            fail("retired path falls under exclude: %s" % entry,
                 "That is the person's space. The updater refuses the whole sweep over this.")
        covering = [e for e in engine + template
                    if manifest_lib.covered_by(e if e.endswith("/") else e, entry)]
        for cover in covering:
            fail("retired path is still covered by %s: %s" % (cover, entry),
                 "It would be restored by the checkout and deleted in the same run.")


def check_versions(root, fail):
    version_file = (root / "VERSION")
    if not version_file.exists():
        return fail("VERSION is missing", "The updater's own post-condition cannot run without it.")
    version = version_file.read_text(encoding="utf-8").strip()
    plugin = json.loads((root / PLUGIN_MANIFEST).read_text(encoding="utf-8")).get("version")
    if plugin != version:
        fail("%s says %r but VERSION says %r" % (PLUGIN_MANIFEST, plugin, version),
             "They are mirrors of one number and move in the same edit.")


def check_canon_listed_once(root, fail):
    rules = sorted(p.name for p in (root / "rules").glob("*.md"))
    contract = (root / "AGENTS.md").read_text(encoding="utf-8")
    for name in rules:
        if name not in contract:
            fail("rule not listed in AGENTS.md: %s" % name,
                 "It is silently not in force for any runtime.")
    bridge = (root / "CLAUDE.md").read_text(encoding="utf-8")
    restated = [n for n in rules if "@rules/%s" % n in bridge]
    if restated:
        fail("CLAUDE.md restates the canon list: %s" % ", ".join(restated),
             "One list, in AGENTS.md. A second copy drifts and nobody notices.")


def check_tools_classified(root, engine, template, exclude, fail):
    """A kit tool nobody declared reaches nobody.

    `tools/` holds both the kit's executables and the person's own, so it is listed file by file
    rather than wholesale. The cost of that safety is that a new kit tool is invisible until it is
    named — it simply never ships, and no base ever reports a problem.
    """
    declared = [e for e in engine + template + exclude]
    for path in sorted((root / "tools").glob("*")):
        relpath = "tools/%s" % path.name
        # Generated output is not a tool. Ask git rather than guessing by name — a guess that
        # misses leaves a permanent false failure, and one that over-matches hides a real tool.
        if git("check-ignore", "-q", relpath, root=root)[0] == 0:
            continue
        # A directory entry is written with a trailing slash; the path itself has none, so it
        # has to be offered in both shapes or every kit directory reads as undeclared.
        shapes = (relpath, relpath + "/") if path.is_dir() else (relpath,)
        if not any(manifest_lib.covered_by(entry, shape)
                   for entry in declared for shape in shapes):
            fail("tool declared nowhere: %s" % relpath,
                 "Name it under engine: to ship it, or exclude: if it is the person's.")


def check_version_moved(root, engine, ref, fail):
    """A release that changes the kit without moving VERSION is invisible to everyone."""
    code, _ = git("rev-parse", "--verify", "--quiet", ref, root=root)
    if code != 0:
        return
    changed = []
    for entry in engine:
        code, out = git("diff", "--name-only", ref, "--", entry.rstrip("/"), root=root)
        if code == 0 and out.strip():
            changed.append(entry)
    if not changed:
        return
    code, before = git("show", "%s:VERSION" % ref, root=root)
    now = (root / "VERSION").read_text(encoding="utf-8").strip()
    if code != 0:
        # No baseline to compare against — say so rather than passing in silence, which is
        # indistinguishable from "the version moved correctly".
        print("  (no VERSION at %s — treating %s as the first release)" % (ref, now))
        return
    if before.strip() == now:
        fail("kit paths changed since %s but VERSION is still %s" % (ref, now),
             "Nobody's daily check will notice, and the updater cannot tell them what arrived.")
        return
    code, out = git("diff", "--name-only", ref, "--", "CHANGELOG.md", root=root)
    if code == 0 and not out.strip():
        fail("VERSION moved since %s but CHANGELOG.md did not" % ref,
             "The update tells each person what changed by reading it.")


def check_removals_retired(root, engine, retired, ref, fail):
    """A file removed from inside an engine directory must be retired, or it lives forever.

    The updater checks a directory out of the kit; git ADDS and UPDATES, it does not delete what
    the kit no longer has. So every removal inside an engine path needs a `retired:` line, and
    forgetting one is invisible until a person is carrying a file the kit stopped shipping.
    """
    code, _ = git("rev-parse", "--verify", "--quiet", ref, root=root)
    if code != 0:
        print("  (skipped removal check — %s is not available here)" % ref)
        return
    retired_set = {r.rstrip("/") for r in retired}
    for entry in engine:
        if not entry.endswith("/"):
            continue
        code, listing = git("ls-tree", "-r", "--name-only", ref, "--", entry, root=root)
        if code != 0:
            continue
        before = {line for line in listing.splitlines() if line}
        gone = sorted(before - files_under(root, entry))
        for path in gone:
            if path not in retired_set:
                fail("removed from %s since %s but not retired: %s" % (entry, ref, path),
                     "It stays on every base that already has it, forever.")


def main(argv) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", default=RELEASE_REF)
    parser.add_argument("--authoring", action="store_true",
                        help="also run the release checks against --since")
    args = parser.parse_args(argv[1:])

    root = manifest_lib.repo_root()
    failures = []

    def fail(message, why=""):
        failures.append((message, why))

    engine = manifest_lib.read_section("engine", root)
    template = manifest_lib.read_section("template", root)
    exclude = manifest_lib.read_section("exclude", root)
    retired = manifest_lib.read_section("retired", root)

    # A manifest that parses to nothing passes every check below by having nothing to check.
    # That is the exact shape of a corrupted file, and it would ship an update that deletes
    # nobody's anything and reports success.
    if not engine:
        fail("the manifest lists no engine paths",
             "Either it is corrupt or the kit owns nothing — both mean no update can work.")

    check_paths_exist(root, engine, template, fail)
    check_no_double_listing(engine, template, fail)
    check_retired(root, engine, template, exclude, retired, fail)
    check_versions(root, fail)
    check_canon_listed_once(root, fail)
    if args.authoring:
        check_tools_classified(root, engine, template, exclude, fail)
        check_removals_retired(root, engine, retired, args.since, fail)
        check_version_moved(root, engine, args.since, fail)

    if not failures:
        scope = "ready to ship" if args.authoring else "structurally sound"
        print("check_kit: %s — %d engine paths, %d templates, %d retired"
              % (scope, len(engine), len(template), len(retired)))
        return 0
    print("check_kit: %d problem(s) — this kit is not ready to ship\n" % len(failures),
          file=sys.stderr)
    for message, why in failures:
        print("  x %s" % message, file=sys.stderr)
        if why:
            print("    %s" % why, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
