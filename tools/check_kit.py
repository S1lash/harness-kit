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
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import manifest as manifest_lib  # noqa: E402
from lib import migrate as migrate_lib  # noqa: E402
from lib import portability  # noqa: E402

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
    # A repeat inside one section is silent otherwise: the path count the update reports goes up,
    # the work does not, and an author adding an entry that is already there reads the higher
    # number as proof their change landed.
    for section, entries in (("engine", engine), ("template", template)):
        seen = set()
        for entry in entries:
            key = entry.rstrip("/")
            if key in seen:
                fail("listed twice under %s: %s" % (section, entry),
                     "The count goes up and the work does not, which reads as a change landing.")
            seen.add(key)


def check_kit_remote_is_this_repository(root, fail):
    """A fork that keeps the upstream address has its bases quietly pulled back upstream.

    Every update reconciles a base's `harness-kit` remote to whatever `kit_remote:` declares —
    which is what makes moving the kit possible at all. The other side of it: fork this repository,
    forget this line, and every base you set up follows YOUR clone once and upstream ever after,
    on one line of output nobody reads twice.
    """
    declared = manifest_lib.read_kit_remote(root)
    if not declared:
        return
    code, actual = git("remote", "get-url", "origin", root=root)
    if code != 0 or not actual.strip():
        return  # no origin to compare against; nothing can be concluded
    normalise = lambda url: url.strip().rstrip("/").removesuffix(".git").lower()
    if normalise(declared) != normalise(actual):
        fail("kit_remote: names %s but this repository's origin is %s" % (declared, actual.strip()),
             "If you forked the kit, point kit_remote: at YOUR clone — otherwise every base you "
             "set up is reconciled back to upstream on its first update.")


def check_retired(root, engine, template, exclude, retired, fail):
    for entry in retired:
        if (root / entry).exists():
            fail("retired path still ships: %s" % entry,
                 "Every update would check it out and then delete it again, forever.")
        if any(manifest_lib.covered_by(e, entry) for e in exclude):
            fail("retired path falls under exclude: %s" % entry,
                 "That is the person's space. The updater refuses the whole sweep over this.")
        # Coverage by a DIRECTORY entry is the ordinary case, not a fault: retiring a file from
        # inside `rules/` or `doctrine/` is exactly what the section is for. `git checkout <ref>
        # -- <dir>` writes what the ref holds and never recreates a file the ref does not have,
        # so there is no restore-then-delete loop to warn about. The real condition — the path
        # still shipping — is the first check above, and `check_paths_exist` refuses an
        # individually-listed engine entry that no longer exists on disk.
        for cover in [e for e in engine + template if e == entry]:
            fail("retired path is still listed on its own under %s: %s" % (cover, entry),
                 "One manifest cannot both ship a path and drop it. Remove the listing.")


def check_versions(root, fail):
    version_file = (root / "VERSION")
    if not version_file.exists():
        return fail("VERSION is missing", "The updater's own post-condition cannot run without it.")
    version = version_file.read_text(encoding="utf-8").strip()
    plugin = json.loads((root / PLUGIN_MANIFEST).read_text(encoding="utf-8")).get("version")
    if plugin != version:
        fail("%s says %r but VERSION says %r" % (PLUGIN_MANIFEST, plugin, version),
             "They are mirrors of one number and move in the same edit.")
    # Three mirrors, not two. The manifest's own `version:` drifted freely while the doctrine,
    # the doctor's check list and the manifest header all promised it was held to the other two.
    declared = manifest_lib.read_version(root)
    if declared and declared != version:
        fail("the manifest says version %r but VERSION says %r" % (declared, version),
             "All three mirrors move in the same edit, or the number means nothing.")


def check_canon_listed_once(root, fail):
    rules = sorted(p.name for p in (root / "rules").glob("*.md"))
    contract = (root / "AGENTS.md").read_text(encoding="utf-8")
    for name in rules:
        # The whole entry, never the bare filename: `safety.md` is a substring of
        # `git-safety.md`, so a bare search reports a rule as listed when nothing lists it —
        # and the rule then reaches no runtime while the gate says the kit is ready to ship.
        if ("@rules/%s" % name) not in contract:
            fail("rule not listed in AGENTS.md: %s" % name,
                 "It is silently not in force for any runtime.")
    # A second list anywhere, not only in CLAUDE.md. Wherever it sits — a bridge file, a README,
    # a doctrine page — it is a second truth: it drifts, and the person goes on believing a rule
    # applies. Two entries is a mention; several is a list.
    for relpath in portability.shipped_paths(root):
        if not relpath.endswith(".md") or relpath == "AGENTS.md":
            continue
        text = (root / relpath).read_text(encoding="utf-8")
        restated = [n for n in rules if "@rules/%s" % n in text]
        if len(restated) > 2:
            fail("%s restates the canon list: %s" % (relpath, ", ".join(restated)),
                 "One list, in AGENTS.md. A second copy drifts and nobody notices.")


def check_section_references(root, fail):
    """A pointer into a named section must land on a heading that exists.

    `rules/present-not-history.md` forbids referencing a section without opening the target —
    a citation from a remembered heading rots the first time a file is rewritten, and then points
    confidently at the wrong paragraph, which is worse than no pointer at all. Until now only a
    person's eyes could catch that.

    Scope is what the kit ships: those files land on machines nobody here will ever see, so a rot
    there is one nobody can diagnose. A pointer inside the person's own writing is the agent's job
    under the rule, not a machine's under a gate.
    """
    pattern = re.compile(r"`?([A-Za-z0-9_./-]+\.md)`?\s*(?:\u2192|->)\s*[\"\u201c]([^\"\u201d]+)[\"\u201d]")
    for relpath in portability.shipped_paths(root):
        if not relpath.endswith(".md"):
            continue
        source = root / relpath
        for match in pattern.finditer(source.read_text(encoding="utf-8")):
            name, heading = match.group(1), match.group(2)
            target = root / name
            if not target.exists():
                target = source.parent / name
            if not target.exists():
                fail("%s points at %s, which does not exist" % (relpath, name),
                     "A pointer to a missing file reads as a place to look and is not one.")
                continue
            headings = re.findall(r"^#+\s+(.+?)\s*$",
                                  target.read_text(encoding="utf-8"), re.M)
            if heading not in headings:
                fail("%s cites a section %s does not have: %r" % (relpath, name, heading),
                     "Open the target and copy the heading. A remembered one rots on the first "
                     "rewrite and then points confidently at the wrong paragraph.")


def check_clause_ids(root, fail):
    """A clause and the mechanism that enforces it must know about each other, both ways.

    A gate enforcing an id no rule defines is a check with no authority — nobody can look up what
    it means. A rule marked as machine-enforced with nothing enforcing it is worse: it reads as
    guarded and is not. Two mechanisms can carry a clause — the portability scanner and the test
    suite — and each names the ids it covers.
    """
    rule_file = root / "rules" / "cross-platform.md"
    if not rule_file.exists():
        return  # nothing defines clauses here, so nothing can drift from them
    rule_text = rule_file.read_text(encoding="utf-8")
    defined = set(re.findall(r"\[(CP-\d+)\]", rule_text))
    scanned = set(portability.clauses())
    test_file = root / "tools" / "tests" / "test_kit.py"
    tested = set(re.findall(r"\[(CP-\d+)\]", test_file.read_text(encoding="utf-8"))
                 ) if test_file.exists() else set()

    for clause in sorted(scanned - defined):
        fail("the portability gate enforces %s, which no rule defines" % clause,
             "A finding nobody can look up is a check with no authority.")
    for clause in sorted(defined - (scanned | tested)):
        fail("%s is marked machine-enforced but nothing enforces it" % clause,
             "It reads as guarded and is not. Enforce it, or drop the marker.")


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
        if not manifest_lib.covers(declared, relpath):
            fail("tool declared nowhere: %s" % relpath,
                 "Name it under engine: to ship it, or exclude: if it is the person's.")


def check_kit_tools_are_catalogued(root, engine, fail):
    """A shipped tool the catalogue does not name is one the agent will never reach for.

    `tools/_kit.md` is how an agent orienting in a base learns what it can run. A tool that ships
    to everyone and appears in no catalogue is invisible in exactly the surface it exists for, and
    nothing about a missing row is ever reported by anything.
    """
    catalogue = root / "tools" / "_kit.md"
    if not catalogue.exists():
        return
    listed = catalogue.read_text(encoding="utf-8")
    for entry in engine:
        name = entry.rsplit("/", 1)[-1]
        if not entry.startswith("tools/") or entry.endswith("/") or name.startswith("_"):
            continue
        if (root / entry).suffix.lower() not in (".py", ".js", ".mjs", ".sh", ".ps1"):
            continue
        if name not in listed:
            fail("%s ships but tools/_kit.md does not name it" % entry,
                 "An agent orients from that catalogue; a tool missing there reaches nobody.")


def check_kit_tools_run_everywhere(root, engine, fail):
    """[CP-4] A kit tool has to be runnable on every platform the kit installs on.

    The gate that reads a script's CONTENTS cannot answer this: a `.sh` full of impeccably
    portable bash still cannot be executed by PowerShell, and `check_portability.py` would report
    it clean. What makes a tool runnable everywhere is the interpreter it is invoked through —
    `python3`, which the installer hard-requires on every platform, or node for an MCP wrapper.
    A shell or PowerShell tool needs its twin, exactly as the installers have.
    """
    for entry in engine:
        if not entry.startswith("tools/"):
            continue
        suffix = (root / entry).suffix.lower()
        if suffix not in (".sh", ".ps1"):
            continue
        twin = entry[: -len(suffix)] + (".ps1" if suffix == ".sh" else ".sh")
        if twin not in engine:
            fail("%s is a kit tool with no platform twin" % entry,
                 "Write it in python, or ship %s beside it and keep the two in lockstep." % twin)


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


def check_seeds_unchanged(root, template, ref, fail):
    """A seed that already exists on a base is never rewritten — so changing one reaches nobody.

    Templates seed at clone time and an update creates one that is MISSING, but never touches one
    that is present: that is what keeps a person's own rows safe. The cost is that the kit's half
    of a mixed file is frozen at their clone date. Editing a seed therefore looks like shipping a
    change and is not one, and nothing downstream ever reports it.

    A seed added since the ref is fine — seeding delivers it. Only an edit to one that already
    existed is the trap.
    """
    code, _ = git("rev-parse", "--verify", "--quiet", ref, root=root)
    if code != 0:
        return
    if git("cat-file", "-e", "%s:VERSION" % ref, root=root)[0] != 0:
        # Nothing has ever been released from this ref, so no base carries a frozen seed yet.
        return
    for entry in template:
        if not git("cat-file", "-e", "%s:%s" % (ref, entry), root=root)[0] == 0:
            continue  # new since the ref — seeding delivers it
        code, out = git("diff", "--name-only", ref, "--", entry, root=root)
        if code == 0 and out.strip():
            fail("a seed that already exists on every base was edited: %s" % entry,
                 "Nobody who has it will ever see the change. Move the part the kit needs to "
                 "keep current into an engine file this seed links to.")


def check_migrations(root, engine, fail):
    """A declared move must be readable, and must never reach the kit's own space."""
    try:
        operations = migrate_lib.parse(root)
    except migrate_lib.MigrationRefused as refusal:
        return fail("a declared migration cannot be read: %s" % refusal,
                    "Every base that takes this release would stop on it.")
    for move in operations:
        for path, side in ((move.source, "from"), (move.destination, "to")):
            if manifest_lib.covers(engine, path):
                fail("migration %s %s is the kit's own space" % (side, path),
                     "Replacement and retirement already handle that; a move there is a mistake.")


def check_person_space_ships_pristine(root, template, exclude, fail):
    """The kit's own person-space must be empty, because a clone carries the whole repository.

    There is no extraction step: what is in this repository is what a person gets. `exclude:`
    keeps an update from touching their space; it does nothing at clone time. So a note the kit's
    author left under `activities/` or `knowledge/` lands in every base as though it were theirs.
    """
    seeds = {entry.rstrip("/") for entry in template}
    for entry in exclude:
        if not entry.endswith("/"):
            continue
        code, listing = git("ls-files", "--", entry, root=root)
        if code != 0:
            continue
        for relpath in listing.splitlines():
            name = relpath.rsplit("/", 1)[-1]
            if relpath in seeds or name in (".gitkeep", ".gitignore"):
                continue
            fail("the kit ships its own content in the person's space: %s" % relpath,
                 "Every clone gets it as though the person wrote it. Move it to a kit-owned path.")


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
    # nobody's anything and reports success. But `engine: []` declared on purpose is a base
    # whose own canon has been developed past the kit's, keeping the machinery so that adopting
    # a path later is a decision rather than a rebuild — `update.py` makes exactly this
    # distinction, and a gate that calls such a base corrupt every run teaches its owner to
    # ignore the message that would matter if the file really were damaged.
    if not engine and not manifest_lib.declares_section("engine", root):
        fail("the manifest has no engine: section",
             "Either it is corrupt or it was never written — no update can work either way.")

    check_paths_exist(root, engine, template, fail)
    check_no_double_listing(engine, template, fail)
    check_retired(root, engine, template, exclude, retired, fail)
    check_versions(root, fail)
    check_canon_listed_once(root, fail)
    check_migrations(root, engine, fail)
    check_clause_ids(root, fail)
    check_section_references(root, fail)
    findings = portability.scan(root)
    for finding in findings:
        fail("%s:%s not portable [%s]" % (finding.path, finding.line or "-", finding.rule.clause),
             finding.rule.why)

    if args.authoring:
        # Authoring-only: on a person's base their own knowledge and activities are exactly what
        # is supposed to be there. This asks whether the KIT is shipping any.
        check_person_space_ships_pristine(root, template, exclude, fail)
        check_seeds_unchanged(root, template, args.since, fail)
        check_tools_classified(root, engine, template, exclude, fail)
        check_kit_tools_are_catalogued(root, engine, fail)
        check_kit_tools_run_everywhere(root, engine, fail)
        check_removals_retired(root, engine, retired, args.since, fail)
        check_version_moved(root, engine, args.since, fail)
        check_kit_remote_is_this_repository(root, fail)

    if not failures:
        scope = "ready to ship" if args.authoring else "structurally sound"
        print("check_kit: %s — %d engine paths, %d templates, %d retired"
              % (scope, len(engine), len(template), len(retired)))
        return 0
    # An author is shipping; a person is being told about their own base. The same wording for
    # both reads to the second as though their base were a release candidate.
    verdict = ("this kit is not ready to ship" if args.authoring
               else "this base has something to fix")
    print("check_kit: %d problem(s) — %s\n" % (len(failures), verdict), file=sys.stderr)
    for message, why in failures:
        print("  x %s" % message, file=sys.stderr)
        if why:
            print("    %s" % why, file=sys.stderr)
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except manifest_lib.ManifestMissing as gone:
        # The base that most needs the recovery command is the one whose manifest is
        # gone; a traceback is not a recovery command.
        sys.stderr.write(
            "the kit/person contract is missing: %s\n"
            "  Nothing can tell a kit path from a person's without it, so no tool\n"
            "  here will guess. Restore it with:\n"
            "    git checkout harness-kit/main -- .engine-manifest.yml\n"
            "  or, if the machinery is damaged too:\n"
            "    python3 tools/update.py --self-heal\n" % gone)
        sys.exit(2)

