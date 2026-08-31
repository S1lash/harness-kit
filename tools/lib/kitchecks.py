#!/usr/bin/env python3
"""The checks behind the author-side gate — one function per thing that can be wrong.

Separated from `tools/check_kit.py` for the reason every check here exists: a file that holds
both the questions and the machinery for asking them grows until neither half is readable, and
the questions are what an author actually maintains. This module answers "what would be wrong
with this kit"; the tool beside it answers "how does a person hear about it".

A check never prints and never exits. It reports through `fail`, which takes the same four
things every time — WHERE to look, WHAT is wrong, and WHY it costs something — so one place
decides how a failure reads and no check invents its own line format.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import NamedTuple

from . import gitrun
from . import manifest as manifest_lib
from . import migrate as migrate_lib
from . import portability

RELEASE_REF = "main"
PLUGIN_MANIFEST = ".claude-plugin/plugin.json"

# What an assistant-authorship mark looks like in git history. The address is the unambiguous
# one: a person may legitimately be named Claude, but nobody commits from a vendor's noreply
# address by hand. The message marks are the ones tools append on their own.
ASSISTANT_ADDRESS = "anthropic.com"
ASSISTANT_MESSAGE_MARKS = (
    "Co-Authored-By: Claude",
    "noreply@anthropic.com",
    "Generated with [Claude Code]",
    "\U0001f916 Generated with",
)


class Failure(NamedTuple):
    """One thing that is wrong, in the shape the report prints and the tests read.

    `where` is the file to open — empty only when the finding is about the kit as a whole —
    and `line` is 0 when the whole file is the finding.
    """

    where: str
    line: int
    what: str
    why: str


class Report:
    """Collects failures in the order the checks make them. Passed to every check as `fail`."""

    def __init__(self):
        self.failures = []
        self.notes = []

    def note(self, text: str):
        """Something the author should know that is not a failure — a check that could not run.

        Silence here is indistinguishable from a check that ran and passed, which is the one
        thing a gate must never be.
        """
        self.notes.append(text)

    def __call__(self, where: str, what: str, why: str = "", line: int = 0):
        self.failures.append(Failure(where, line, what, why))

    def __len__(self):
        return len(self.failures)

    def __contains__(self, text: str) -> bool:
        return any(text in "%s %s %s" % (f.where, f.what, f.why) for f in self.failures)

    def __iter__(self):
        return iter(self.failures)

    def __repr__(self):
        return repr(self.failures)


def git(*args, root: Path):
    """Run git in `root`. Same contract as everywhere else, stderr included.

    Included because without it a failure here can only ever be reported as "it did not work".
    """
    return gitrun.run(root, *args)


files_under = manifest_lib.files_under

def check_paths_exist(root, engine, template, fail):
    for entry in engine:
        if not (root / entry.rstrip("/")).exists():
            fail(entry, "listed under engine: and not on disk",
                 "It reaches nobody — the updater skips what it cannot find.")
    for entry in template:
        if not (root / entry).exists():
            fail(entry, "listed under template: and not on disk",
                 "A base cloned today would be missing a file the kit assumes is there.")


def check_no_double_listing(engine, template, fail):
    overlap = {e.rstrip("/") for e in engine} & {t.rstrip("/") for t in template}
    for entry in sorted(overlap):
        fail(entry, "listed as both engine: and template:",
             "engine wins on update and would overwrite what the person put in it.")
    # A repeat inside one section is silent otherwise: the path count the update reports goes up,
    # the work does not, and an author adding an entry that is already there reads the higher
    # number as proof their change landed.
    for section, entries in (("engine", engine), ("template", template)):
        seen = set()
        for entry in entries:
            key = entry.rstrip("/")
            if key in seen:
                fail(entry, "listed twice under %s:" % section,
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
    probe = git("remote", "get-url", "origin", root=root)
    code, actual = probe.code, probe.out
    if code != 0 or not actual.strip():
        return  # no origin to compare against; nothing can be concluded
    if not manifest_lib.same_repository(declared, actual):
        fail(manifest_lib.MANIFEST_NAME,
             "kit_remote: names %s but this repository's origin is %s"
             % (declared, actual.strip()),
             "If you forked the kit, point kit_remote: at YOUR clone — otherwise every base you "
             "set up is reconciled back to upstream on its first update.")


def check_retired(root, engine, template, exclude, retired, fail):
    for entry in retired:
        if (root / entry).exists():
            fail(entry, "retired and still shipping",
                 "Every update would check it out and then delete it again, forever.")
        if any(manifest_lib.covered_by(e, entry) for e in exclude):
            fail(entry, "retired and falls under exclude:",
                 "That is the person's space. The updater refuses the whole sweep over this.")
        # Coverage by a DIRECTORY entry is the ordinary case, not a fault: retiring a file from
        # inside `rules/` or `doctrine/` is exactly what the section is for. `git checkout <ref>
        # -- <dir>` writes what the ref holds and never recreates a file the ref does not have,
        # so there is no restore-then-delete loop to warn about. The real condition — the path
        # still shipping — is the first check above, and `check_paths_exist` refuses an
        # individually-listed engine entry that no longer exists on disk.
        for cover in [e for e in engine + template if e == entry]:
            fail(entry, "retired and still listed on its own under %s" % cover,
                 "One manifest cannot both ship a path and drop it. Remove the listing.")


def check_versions(root, fail):
    version_file = (root / "VERSION")
    if not version_file.exists():
        return fail("VERSION", "missing",
                    "The updater's own post-condition cannot run without it.")
    version = version_file.read_text(encoding="utf-8").strip()
    plugin = json.loads((root / PLUGIN_MANIFEST).read_text(encoding="utf-8")).get("version")
    if plugin != version:
        fail(PLUGIN_MANIFEST, "says version %r but VERSION says %r" % (plugin, version),
             "They are mirrors of one number and move in the same edit.")
    # Three mirrors, not two. The manifest's own `version:` drifted freely while the doctrine,
    # the doctor's check list and the manifest header all promised it was held to the other two.
    declared = manifest_lib.read_version(root)
    if declared and declared != version:
        fail(manifest_lib.MANIFEST_NAME,
             "says version %r but VERSION says %r" % (declared, version),
             "All three mirrors move in the same edit, or the number means nothing.")


def check_canon_listed_once(root, fail):
    rules = sorted(p.name for p in (root / "rules").glob("*.md"))
    contract = (root / "AGENTS.md").read_text(encoding="utf-8")
    # The whole entry, never a substring of it. `safety.md` sits inside `git-safety.md`, so a
    # bare filename search reports a rule as listed when nothing lists it; and a malformed
    # entry — a typo, a suffix, a stray word — CONTAINS the correct one and passes on it. The
    # rule then reaches no runtime while the gate calls the kit ready to ship.
    #
    # A leading bullet, number or indent is not malformation: `- @rules/x.md` is a live
    # import, and `AGENTS.md` tells the agent to repair this list itself without saying the
    # format is exact. Rejecting a shape the contract invites is a false alarm on the one check
    # whose whole value is being believed.
    listed = {re.sub(r"^(?:[-*+]|\d+[.)])\s*", "", line.strip()) for line in contract.splitlines()}
    for name in rules:
        if ("@rules/%s" % name) not in listed:
            fail("AGENTS.md", "does not list the rule rules/%s" % name,
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
            fail(relpath, "restates the canon list: %s" % ", ".join(restated),
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
                fail(relpath, "points at %s, which does not exist" % name,
                     "A pointer to a missing file reads as a place to look and is not one.")
                continue
            headings = re.findall(r"^#+\s+(.+?)\s*$",
                                  target.read_text(encoding="utf-8"), re.M)
            if heading not in headings:
                fail(relpath, "cites a section %s does not have: %r" % (name, heading),
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
        fail("rules/cross-platform.md", "does not define %s, which the gate enforces" % clause,
             "A finding nobody can look up is a check with no authority.")
    for clause in sorted(defined - (scanned | tested)):
        fail("rules/cross-platform.md",
             "marks %s machine-enforced and nothing enforces it" % clause,
             "It reads as guarded and is not. Enforce it, or drop the marker.")


def check_tools_classified(root, engine, template, exclude, fail):
    """A kit tool nobody declared reaches nobody.

    `tools/` holds both the kit's executables and the person's own, so it is listed file by file
    rather than wholesale. The cost of that safety is that a new kit tool is invisible until it is
    named — it simply never ships, and no base ever reports a problem.
    """
    declared = engine + template + exclude
    for path in sorted((root / "tools").glob("*")):
        relpath = "tools/%s" % path.name
        # Generated output is not a tool. Ask git rather than guessing by name — a guess that
        # misses leaves a permanent false failure, and one that over-matches hides a real tool.
        if git("check-ignore", "-q", relpath, root=root)[0] == 0:
            continue
        # A directory entry is written with a trailing slash; the path itself has none, so it
        # has to be offered in both shapes or every kit directory reads as undeclared.
        if not manifest_lib.covers(declared, relpath):
            fail(relpath, "declared in no section of the manifest",
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
            fail("tools/_kit.md", "does not name %s, which ships" % entry,
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
            fail(entry, "is a kit tool with no platform twin",
                 "Write it in python, or ship %s beside it and keep the two in lockstep." % twin)


def check_no_assistant_authorship(root, ref, fail):
    """A release may not carry a commit marked as written by an assistant.

    `rules/communication.md` forbids the mark "anywhere … or any artifact", and git authorship is
    the canonical attribution field of a public repository. The rule existed and nothing held it,
    so the only thing standing between it and a permanent line in the history was somebody
    reading `git log` — and after a merge it can be removed only by rewriting history, which
    `rules/git-safety.md` forbids without the person's approval in the moment. Cheap to fix
    while a branch is still a branch; impossible afterwards.

    Scoped to what this release ADDS. History already merged is history, and a gate that fails
    every run over something nobody may rewrite teaches its reader to ignore it.
    """
    if git("rev-parse", "--verify", "--quiet", ref, root=root).code != 0:
        fail.note("skipped the authorship check — %s is not available here" % ref)
        return
    span = "%s..HEAD" % ref
    listing = git("log", span, "--format=%h%x09%ae%x09%ce", root=root)
    if listing.code != 0:
        return
    for line in listing.out.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        commit, author, committer = parts
        if ASSISTANT_ADDRESS in author.lower() or ASSISTANT_ADDRESS in committer.lower():
            fail(commit, "is authored by an assistant address (%s)" % (author or committer),
                 "Restamp it before this merges — afterwards it is history nobody may rewrite.")
    # Gathered per commit rather than per mark: one message often carries several, and three
    # lines about one commit read as three problems.
    marked = {}
    for mark in ASSISTANT_MESSAGE_MARKS:
        found = git("log", span, "--fixed-strings", "--regexp-ignore-case",
                    "--grep", mark, "--format=%h", root=root)
        if found.code != 0:
            continue
        for commit in found.out.split():
            marked.setdefault(commit, []).append(mark)
    for commit, marks in marked.items():
        fail(commit, "has %s in its message" % ", ".join(repr(m) for m in marks),
             "Rewrite the message before this merges; afterwards it cannot be removed.")


def check_version_moved(root, engine, ref, fail):
    """A release that changes the kit without moving VERSION is invisible to everyone."""
    result = git("rev-parse", "--verify", "--quiet", ref, root=root)
    code, _ = result.code, result.out
    if code != 0:
        return
    changed = []
    for entry in engine:
        result = git("diff", "--name-only", ref, "--", entry.rstrip("/"), root=root)
        code, out = result.code, result.out
        if code == 0 and out.strip():
            changed.append(entry)
    if not changed:
        return
    result = git("show", "%s:VERSION" % ref, root=root)
    code, before = result.code, result.out
    now = (root / "VERSION").read_text(encoding="utf-8").strip()
    if code != 0:
        # No baseline to compare against — say so rather than passing in silence, which is
        # indistinguishable from "the version moved correctly".
        fail.note("no VERSION at %s — treating %s as the first release" % (ref, now))
        return
    if before.strip() == now:
        fail("VERSION", "still %s, though kit paths changed since %s" % (now, ref),
             "Nobody's daily check will notice, and the updater cannot tell them what arrived.")
        return
    result = git("diff", "--name-only", ref, "--", "CHANGELOG.md", root=root)
    code, out = result.code, result.out
    if code == 0 and not out.strip():
        fail("CHANGELOG.md", "unchanged since %s, though VERSION moved" % ref,
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
    result = git("rev-parse", "--verify", "--quiet", ref, root=root)
    code, _ = result.code, result.out
    if code != 0:
        return
    if git("cat-file", "-e", "%s:VERSION" % ref, root=root)[0] != 0:
        # Nothing has ever been released from this ref, so no base carries a frozen seed yet.
        # Said out loud rather than returning quietly: the real trigger is a CLONE, not a
        # release, and silence here is indistinguishable from the check running and passing.
        fail.note("skipped the frozen-seed check — nothing was ever released from %s" % ref)
        return
    for entry in template:
        if not git("cat-file", "-e", "%s:%s" % (ref, entry), root=root)[0] == 0:
            continue  # new since the ref — seeding delivers it
        result = git("diff", "--name-only", ref, "--", entry, root=root)
        code, out = result.code, result.out
        if code == 0 and out.strip():
            fail(entry, "is a seed that already exists on every base, and it was edited",
                 "Nobody who has it will ever see the change. Move the part the kit needs to "
                 "keep current into an engine file this seed links to.")


def check_migrations(root, engine, fail):
    """A declared move must be readable, and must never reach the kit's own space."""
    try:
        operations = migrate_lib.parse(root)
    except migrate_lib.MigrationRefused as refusal:
        return fail(manifest_lib.MANIFEST_NAME,
                    "declares a migration that cannot be read: %s" % refusal,
                    "Every base that takes this release would stop on it.")
    for move in operations:
        for path, side in ((move.source, "from"), (move.destination, "to")):
            if manifest_lib.covers(engine, path):
                fail(path, "is the kit's own space, and a migration moves %s it" % side,
                     "Replacement and retirement already handle that; a move there is a mistake.")


def check_person_space_ships_pristine(root, template, exclude, fail):
    """The kit's own person-space must be empty, because a clone carries the whole repository.

    There is no extraction step: what is in this repository is what a person gets. `exclude:`
    keeps an update from touching their space; it does nothing at clone time. So a note the kit's
    author left under `activities/` or `knowledge/` lands in every base as though it were theirs.
    """
    seeds = {entry.rstrip("/") for entry in template}
    for entry in exclude:
        # A single FILE listed here may ship, but only empty: the kit gives the person the shape
        # to fill, never a line of its own. Skipping non-directory entries leaves that unwatched.
        if not entry.endswith("/"):
            target = root / entry
            if target.is_file() and target.stat().st_size and entry not in seeds:
                fail(entry, "is the kit's own content in a file that belongs to the person",
                     "A clone carries it as though they wrote it. Ship it empty, or move it to a "
                     "kit-owned path.")
            continue
        result = git("ls-files", "--", entry, root=root)
        code, listing = result.code, result.out
        if code != 0:
            continue
        for relpath in listing.splitlines():
            name = relpath.rsplit("/", 1)[-1]
            if relpath in seeds or name in (".gitkeep", ".gitignore"):
                continue
            fail(relpath, "is the kit's own content sitting in the person's space",
                 "Every clone gets it as though the person wrote it. Move it to a kit-owned path.")


def check_removals_retired(root, engine, retired, ref, fail):
    """A file removed from inside an engine directory must be retired, or it lives forever.

    The updater checks a directory out of the kit; git ADDS and UPDATES, it does not delete what
    the kit no longer has. So every removal inside an engine path needs a `retired:` line, and
    forgetting one is invisible until a person is carrying a file the kit no longer ships.
    """
    result = git("rev-parse", "--verify", "--quiet", ref, root=root)
    code, _ = result.code, result.out
    if code != 0:
        fail.note("skipped the removal check — %s is not available here" % ref)
        return
    retired_set = {r.rstrip("/") for r in retired}
    for entry in engine:
        if not entry.endswith("/"):
            continue
        result = git("ls-tree", "-r", "--name-only", ref, "--", entry, root=root)
        code, listing = result.code, result.out
        if code != 0:
            continue
        before = {line for line in listing.splitlines() if line}
        gone = sorted(before - files_under(root, entry))
        for path in gone:
            if path not in retired_set:
                fail(path, "removed from %s since %s and not retired" % (entry, ref),
                     "It stays on every base that already has it, forever.")




def run(root: Path, since: str = RELEASE_REF, authoring: bool = False):
    """Ask every question that applies, and answer none of them out loud.

    Structural checks hold on any base — that is what `/harness-doctor` runs. The authoring
    ones compare this working tree against a release ref and only mean anything inside the
    kit's own repository.
    """
    report = Report()
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
        report(manifest_lib.MANIFEST_NAME, "has no engine: section",
               "Either it is corrupt or it was never written — no update can work either way.")

    check_paths_exist(root, engine, template, report)
    check_no_double_listing(engine, template, report)
    check_retired(root, engine, template, exclude, retired, report)
    check_versions(root, report)
    check_canon_listed_once(root, report)
    check_migrations(root, engine, report)
    check_clause_ids(root, report)
    check_section_references(root, report)
    for finding in portability.scan(root):
        report(finding.path, "not portable [%s]" % finding.rule.clause, finding.rule.why,
               line=finding.line or 0)

    if authoring:
        # Authoring-only: on a person's base their own knowledge and activities are exactly what
        # is supposed to be there. This asks whether the KIT is shipping any.
        check_person_space_ships_pristine(root, template, exclude, report)
        check_seeds_unchanged(root, template, since, report)
        check_tools_classified(root, engine, template, exclude, report)
        check_kit_tools_are_catalogued(root, engine, report)
        check_kit_tools_run_everywhere(root, engine, report)
        check_removals_retired(root, engine, retired, since, report)
        check_version_moved(root, engine, since, report)
        check_kit_remote_is_this_repository(root, report)
        check_no_assistant_authorship(root, since, report)

    return report, (len(engine), len(template), len(retired))
