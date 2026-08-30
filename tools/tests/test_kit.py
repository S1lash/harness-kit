#!/usr/bin/env python3
"""Tests for the machinery a person's base runs on its own.

Everything here was verified by hand once, which is worth exactly one session. These are the
same checks, re-runnable: the manifest reader, the retirement guard, and the updater driven
end to end against a real git remote — including the shapes that must FAIL, because a broken
update that exits 0 is indistinguishable from an up-to-date base.

Run:  python3 -m unittest discover -s tools/tests
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KIT_ROOT / "tools"))

from lib import manifest as manifest_lib  # noqa: E402
from lib import migrate as migrate_lib  # noqa: E402
from lib import portability  # noqa: E402
import check_kit  # noqa: E402
import update as update_module  # noqa: E402
from lib import retire as retire_lib  # noqa: E402

TOOL_FILES = ("update.py", "check_kit.py")
MANIFEST = """version: 1.0.0

engine:
  - rules/
  - VERSION
  - .engine-manifest.yml   # inline note the reader must drop

template:
  - seed.md

exclude:
  - mine/

retired:
  - old/gone.md
"""


def git(root, *args, check=True):
    done = subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
        + list(args),
        capture_output=True, text=True,
    )
    if check and done.returncode != 0:
        raise AssertionError("git %s failed: %s" % (" ".join(args), done.stderr))
    return done


def write(root: Path, relpath: str, text: str):
    target = root / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def install_tools(root: Path):
    """Put the real code under test into a fake base, the way a real base carries it."""
    (root / "tools").mkdir(parents=True, exist_ok=True)
    for name in TOOL_FILES:
        shutil.copy2(KIT_ROOT / "tools" / name, root / "tools" / name)
    shutil.copytree(KIT_ROOT / "tools" / "lib", root / "tools" / "lib", dirs_exist_ok=True)


def run_update(base: Path, *args):
    return subprocess.run(
        [sys.executable, str(base / "tools" / "update.py"), "--branch", "main", *args],
        capture_output=True, text=True,
    )


class ManifestReaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        write(self.root, ".engine-manifest.yml", MANIFEST)
        self.addCleanup(self.tmp.cleanup)

    def test_sections_are_read_in_order(self):
        self.assertEqual(manifest_lib.read_section("engine", self.root),
                         ["rules/", "VERSION", ".engine-manifest.yml"])
        self.assertEqual(manifest_lib.read_section("template", self.root), ["seed.md"])
        self.assertEqual(manifest_lib.read_section("retired", self.root), ["old/gone.md"])

    def test_inline_comment_is_not_part_of_the_path(self):
        # A trailing note reaching a caller as part of the path names a file that never exists,
        # and every consumer reads that as "absent".
        self.assertIn(".engine-manifest.yml", manifest_lib.read_section("engine", self.root))

    def test_version_is_read(self):
        self.assertEqual(manifest_lib.read_version(self.root), "1.0.0")

    def test_unknown_section_is_refused(self):
        with self.assertRaises(ValueError):
            manifest_lib.read_section("nonsense", self.root)


class SilentDivergenceTests(unittest.TestCase):
    """Two states the base could be in while reporting that everything was fine."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name) / "base"
        (self.base / "projects").mkdir(parents=True)
        write(self.base, "knowledge/note.md", "theirs\n")
        install_tools(self.base)
        shutil.copy2(KIT_ROOT / "tools" / "sync.py", self.base / "tools")
        git(self.base, "init", "-q", "-b", "main")

    def run_sync(self, *args):
        return subprocess.run([sys.executable, str(self.base / "tools" / "sync.py"), *args],
                              capture_output=True, text=True, cwd=str(self.base))

    def test_a_project_that_is_its_own_repository_is_named(self):
        """A gitlink records a commit id and no content, so a clone gets an empty folder.

        The base's whole promise is that what is inside it travels. Nothing said otherwise: the
        save reported success, and the phone found nothing there.
        """
        app = self.base / "projects" / "myapp"
        app.mkdir()
        write(app, "main.py", "print('hi')\n")
        git(app, "init", "-q", "-b", "main")
        git(app, "add", "-A")
        git(app, "commit", "-qm", "the app")
        # A base with no remote has a louder problem, and its directive correctly wins. Give it
        # one so the nested-repository directive is the one under test.
        remote = Path(self.tmp.name) / "their-remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        git(self.base, "add", "-A")
        git(self.base, "commit", "-qm", "their base")
        git(self.base, "remote", "add", "origin", str(remote))
        git(self.base, "push", "-q", "-u", "origin", "main")

        done = self.run_sync("status")
        self.assertIn("projects kept separately: projects/myapp", done.stdout)
        self.assertIn("do NOT travel with this base", done.stdout)
        self.assertIn("does not travel with the base", done.stdout, "the directive must say so")

    def test_a_base_with_no_nested_repository_says_nothing_about_it(self):
        done = self.run_sync("status")
        self.assertNotIn("projects kept separately", done.stdout)

    def test_a_public_remote_stops_the_save(self):
        """"Private" was asserted once at creation and never checked again.

        A fork of a public repository is itself public, and its address does not match the kit's,
        so nothing moved it aside — the person's whole life then pushed somewhere anyone can
        read, while the installer and the doctor both reported a private place online on the
        sole evidence that a URL existed.
        """
        fake_bin = Path(self.tmp.name) / "bin"
        fake_bin.mkdir()
        gh = fake_bin / "gh"
        gh.write_text("#!/bin/sh\necho public\n", encoding="utf-8")
        gh.chmod(0o755)
        remote = Path(self.tmp.name) / "their-remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        git(self.base, "remote", "add", "origin", str(remote))

        done = subprocess.run(
            [sys.executable, str(self.base / "tools" / "sync.py"), "status"],
            capture_output=True, text=True, cwd=str(self.base),
            env={**os.environ, "PATH": "%s:%s" % (fake_bin, os.environ.get("PATH", ""))})
        self.assertIn("PUBLIC", done.stdout)
        self.assertIn("readable by anyone", done.stdout)

        saving = subprocess.run(
            [sys.executable, str(self.base / "tools" / "sync.py"), "save", "anything"],
            capture_output=True, text=True, cwd=str(self.base),
            env={**os.environ, "PATH": "%s:%s" % (fake_bin, os.environ.get("PATH", ""))})
        self.assertNotEqual(saving.returncode, 0, "it saved to a public remote")

    def test_a_private_remote_raises_no_alarm(self):
        # The other direction, and the one a false-positive would ruin: a base that IS private
        # must never be told it is public, or the warning stops meaning anything.
        fake_bin = Path(self.tmp.name) / "bin-private"
        fake_bin.mkdir()
        gh = fake_bin / "gh"
        gh.write_text("#!/bin/sh\necho private\n", encoding="utf-8")
        gh.chmod(0o755)
        remote = Path(self.tmp.name) / "private.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        git(self.base, "remote", "add", "origin", str(remote))
        done = subprocess.run(
            [sys.executable, str(self.base / "tools" / "sync.py"), "status"],
            capture_output=True, text=True, cwd=str(self.base),
            env={**os.environ, "PATH": "%s:%s" % (fake_bin, os.environ.get("PATH", ""))})
        self.assertNotIn("PUBLIC", done.stdout)

    def test_a_visibility_that_cannot_be_established_is_not_called_public(self):
        # Unknown is not a finding: `gh` absent or signed out must not produce a false alarm.
        remote = Path(self.tmp.name) / "quiet.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        git(self.base, "remote", "add", "origin", str(remote))
        done = self.run_sync("status")
        self.assertNotIn("PUBLIC", done.stdout)

    def test_a_base_git_cannot_read_is_not_reported_as_clean(self):
        """`git_ok` returned None for a failure and for an empty result alike.

        `porcelain or ""` then made "cannot tell" identical to "nothing to save", and
        session-start would fast-forward on that reading.
        """
        (self.base / ".git" / "index").write_bytes(b"CORRUPT")
        done = self.run_sync("status")
        self.assertIn("UNREADABLE", done.stdout)
        self.assertIn("STOP", done.stdout)
        saving = self.run_sync("save", "anything")
        self.assertNotEqual(saving.returncode, 0, "it saved over a base it could not read")


class InstallerSafetyTests(unittest.TestCase):
    """Two ways the installer reached past what it was pointed at.

    Both were demonstrated end to end: the legacy-projects migration absorbed the person's own
    `~/projects` — an ordinary folder name, nothing to do with this kit — and committed a live
    API key with it; and a blank email left a base with every file staged and no history while
    the installer printed thirteen OK lines and "Done".
    """

    def source(self):
        source = Path(self.tmp.name) / "src"
        shutil.copytree(KIT_ROOT, source, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        return source

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "home"
        self.home.mkdir()

    def install(self, answers):
        done = subprocess.run(["bash", str(self.source() / "install.sh")],
                              input=answers, capture_output=True, text=True,
                              cwd=str(self.tmp.name),
                              env={**os.environ, "HOME": str(self.home),
                                   "HARNESS_ANSWERS_ON_STDIN": "1"})
        return done

    def test_an_ordinary_projects_folder_is_left_alone(self):
        # The trigger is a marker an old harness leaves, never the folder's name.
        theirs = self.home / "projects" / "client-work"
        theirs.mkdir(parents=True)
        (theirs / ".env").write_text("STRIPE_KEY=sk_live_real\n", encoding="utf-8")
        done = self.install("%s\nharness\nEnglish\nn\nn\nn\nn\nElena\ne@example.invalid\nn\n"
                            % self.home)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertNotIn("an earlier harness left it there", done.stdout)
        self.assertTrue((theirs / ".env").exists(), "the person's own folder was absorbed")
        # And it must not have been committed into the base either.
        tracked = subprocess.run(["git", "-C", str(self.home / "harness"), "ls-files"],
                                 capture_output=True, text=True).stdout
        self.assertNotIn("client-work", tracked, "the person's unrelated work was committed")

    def test_a_former_harness_projects_folder_is_offered_and_defaults_to_no(self):
        legacy = self.home / "projects"
        legacy.mkdir(parents=True)
        (legacy / "_index.md").write_text("# projects\n", encoding="utf-8")
        # A name the base does not already carry: `_index.md` exists on both sides, so the
        # migration skips it and it can never show whether the move happened.
        (legacy / "old-work.md").write_text("from the previous base\n", encoding="utf-8")
        # The migration question comes BEFORE the language one; an empty answer takes the
        # default, and the default has to be "leave it where it is".
        done = self.install("%s\nharness\n\nEnglish\nn\nn\nn\nn\nElena\ne@example.invalid\nn\n"
                            % self.home)
        self.assertIn("an earlier harness left it there", done.stdout)
        self.assertIn("It holds:", done.stdout, "it must show what it would move")
        self.assertTrue((legacy / "old-work.md").exists(),
                        "an empty answer moved the folder — the default is not no")

    def test_an_ordinary_install_records_the_base(self):
        done = self.install("%s\nharness\nEnglish\nn\nn\nn\nn\nElena\ne@example.invalid\nn\n"
                            % self.home)
        self.assertIn("OK   your work here is being recorded", done.stdout)
        head = subprocess.run(["git", "-C", str(self.home / "harness"), "log", "-1", "--format=%H"],
                              capture_output=True, text=True)
        self.assertTrue(head.stdout.strip(), "the base was left with no history")

    def test_a_base_that_could_not_record_anything_says_so(self):
        """A swallowed commit failure left every file staged, no history, and thirteen OK lines.

        The reachable cause is a project repository with no commits of its own sitting under
        `projects/`: `git add -A` fails outright on it, the failure was discarded, and the
        installer printed its health check and "Done" over a base that had recorded nothing.
        """
        source = self.source()
        nested = source / "projects" / "newapp"
        nested.mkdir(parents=True)
        (nested / "main.py").write_text("print('hi')\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(nested), "init", "-q"], check=True)
        done = subprocess.run(["bash", str(source / "install.sh")],
                              input="%s\nharness\nEnglish\nn\nn\nn\nn\nElena\ne@example.invalid\nn\n"
                                    % self.home,
                              capture_output=True, text=True, cwd=str(self.tmp.name),
                              env={**os.environ, "HOME": str(self.home),
                                   "HARNESS_ANSWERS_ON_STDIN": "1"})
        base = self.home / "harness"
        head = subprocess.run(["git", "-C", str(base), "log", "-1", "--format=%H"],
                              capture_output=True, text=True).stdout.strip()
        if not head:
            self.assertIn("MISS your work here is being recorded", done.stdout,
                          "a base with no history was reported as fine")
            self.assertIn("PROBLEM", done.stdout)
        else:
            self.assertIn("OK   your work here is being recorded", done.stdout)


class EnclosingRepositoryTests(unittest.TestCase):
    """Being INSIDE a repository is not the same as BEING one.

    A base with no `.git` of its own, anywhere under another repository, makes `git -C <base>`
    answer for THAT repository. Demonstrated before the fix: `save` staged the enclosing
    project's whole worktree — an unrelated `.env` and someone's work-in-progress — committed it
    and pushed it to that project's remote, and reported "saved" in the plain language the rules
    require, with nothing in the output naming the repository it had actually written to.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.company = Path(self.tmp.name) / "company"
        (self.company / "src").mkdir(parents=True)
        write(self.company, ".env", "DB_PASSWORD=s3cr3t\n")
        write(self.company, "src/wip.py", "half-finished\n")
        git(self.company, "init", "-q", "-b", "main")
        git(self.company, "add", "-A")
        git(self.company, "commit", "-qm", "the company's repository")

        self.base = self.company / "harness"      # no .git of its own
        self.base.mkdir()
        write(self.base, "knowledge/note.md", "the person's note\n")
        install_tools(self.base)
        shutil.copy2(KIT_ROOT / "tools" / "sync.py", self.base / "tools")

    def run_sync(self, *args):
        return subprocess.run([sys.executable, str(self.base / "tools" / "sync.py"), *args],
                              capture_output=True, text=True, cwd=str(self.base))

    def test_saving_refuses_and_names_the_repository_it_would_have_written_to(self):
        done = self.run_sync("save", "write down what we decided")
        self.assertNotEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("NOT ITS OWN", done.stdout)
        self.assertIn(str(self.company), done.stdout)
        # Nothing staged: the enclosing repository is exactly as it was.
        staged = git(self.company, "diff", "--cached", "--name-only").stdout.strip()
        self.assertEqual(staged, "", "the enclosing repository was staged")

    def test_status_says_so_before_anything_else(self):
        done = self.run_sync("status")
        self.assertIn("NOT ITS OWN", done.stdout)
        self.assertIn("STOP", done.stdout)

    def test_a_base_that_is_its_own_repository_is_unaffected(self):
        git(self.base, "init", "-q", "-b", "main")
        done = self.run_sync("status")
        self.assertNotIn("NOT ITS OWN", done.stdout)

    def test_the_updater_refuses_too(self):
        done = subprocess.run([sys.executable, str(self.base / "tools" / "update.py"), "--dry-run"],
                              capture_output=True, text=True, cwd=str(self.base))
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("no history of its own", done.stdout + done.stderr)


class ContainmentTests(unittest.TestCase):
    """A manifest entry becomes a filesystem operation, so containment is the manifest's job.

    Every guard downstream compared strings against `exclude:`, and a string comparison cannot
    see that `../x` leaves the base or that an absolute path was never in it. Demonstrated before
    the fix: a `retired:` entry deleted a file outside the base and the parent-pruning walked UP
    the filesystem removing three more directories; `./knowledge/x` deleted the person's space
    that `exclude: knowledge/` exists to protect.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "base"
        (self.root / "knowledge").mkdir(parents=True)
        write(self.root, ".engine-manifest.yml",
              "version: 1.0.0\n\nengine:\n  - rules/\n\nexclude:\n  - knowledge/\n")
        self.addCleanup(self.tmp.cleanup)

    def test_a_missing_manifest_names_the_recovery_instead_of_a_traceback(self):
        """The base that most needs `--self-heal` is the one whose manifest is gone.

        Every reader used to open the file itself, so there was no single place the absence could
        be handled — and all three tools raised FileNotFoundError at a person who cannot act on
        one. update.py died inside `resolve_remote` before it ever reached the carefully worded
        refusal written two lines below.
        """
        bare = Path(self.tmp.name) / "no-manifest"
        bare.mkdir()
        with self.assertRaises(manifest_lib.ManifestMissing):
            manifest_lib.read_section("engine", bare)
        # The tools resolve their base from their OWN location, so they have to be run from
        # inside the manifest-less base rather than pointed at it.
        install_tools(bare)
        shutil.copy2(KIT_ROOT / "tools" / "check_portability.py", bare / "tools")
        # A tracked base, so `update.py` reaches the manifest read rather than stopping earlier
        # on "not tracked" — the manifest-less case is what is under test here.
        git(bare, "init", "-q", "-b", "main")
        for tool in ("update.py", "check_kit.py", "check_portability.py"):
            done = subprocess.run([sys.executable, str(bare / "tools" / tool)],
                                  capture_output=True, text=True, cwd=str(bare))
            self.assertEqual(done.returncode, 2, tool + ": " + done.stdout + done.stderr)
            self.assertIn("self-heal", done.stderr, tool)

    def test_an_entry_that_leaves_the_base_is_refused_at_the_parser(self):
        for entry in ("../outside/x", "/etc/passwd", "~/secrets", "C:/Windows", "..", "."):
            with self.assertRaises(manifest_lib.UnsafeEntry, msg=entry):
                manifest_lib.safe_entry(entry, "retired")

    def test_a_dot_slash_entry_cannot_slip_past_the_persons_space(self):
        # `"./knowledge/x".startswith("knowledge/")` is False, so every guard in the kit missed it.
        self.assertEqual(manifest_lib.safe_entry("./knowledge/x", "retired"), "knowledge/x")
        self.assertTrue(manifest_lib.covers(["knowledge/"],
                                            manifest_lib.safe_entry("./knowledge/x")))

    def test_a_directory_entry_keeps_its_trailing_slash(self):
        self.assertEqual(manifest_lib.safe_entry("knowledge/"), "knowledge/")
        self.assertEqual(manifest_lib.safe_entry("./a/b/"), "a/b/")

    def test_retirement_refuses_a_path_that_resolves_outside_the_base(self):
        # Defence in depth behind the parser: a symlink inside the base can still point out.
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        (outside / "victim.txt").write_text("theirs\n", encoding="utf-8")
        (self.root / "link").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(retire_lib.RetirementRefused):
            retire_lib.run(self.root, entries=["link/victim.txt"])
        self.assertTrue((outside / "victim.txt").exists())

    def test_a_move_may_not_reach_outside_the_base_in_either_direction(self):
        # Outbound loses the person's file; INBOUND drags an arbitrary file into a repository the
        # next save commits and pushes, which is an exfiltration primitive, not a misplaced file.
        for entry in ("move ../outside/id_rsa -> knowledge/harmless.md | tidy",
                      "move knowledge/secret.md -> ../exfil/secret.md | tidy"):
            with self.assertRaises(migrate_lib.MigrationRefused, msg=entry):
                migrate_lib.run(self.root, entries=[entry])


class CoverageRuleTests(unittest.TestCase):
    def test_directory_entry_covers_everything_beneath(self):
        self.assertTrue(manifest_lib.covered_by("rules/", "rules/a/b.md"))

    def test_file_entry_matches_only_itself(self):
        self.assertTrue(manifest_lib.covered_by("VERSION", "VERSION"))
        self.assertFalse(manifest_lib.covered_by("VERSION", "VERSION.bak"))

    def test_star_slash_covers_subdirectories_but_not_files_beside_them(self):
        # Reading the star as a plain prefix looks cautious and is not: it swallows sibling
        # files into the covered set, and a guard built on it refuses the work it exists to allow.
        self.assertTrue(manifest_lib.covered_by("roles/*/", "roles/alice/state.md"))
        self.assertFalse(manifest_lib.covered_by("roles/*/", "roles/_run-frame.md"))


class RetirementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_listed_path_is_removed_and_its_empty_parent_pruned(self):
        write(self.root, ".engine-manifest.yml", MANIFEST)
        write(self.root, "old/gone.md", "dead")
        removed = retire_lib.run(self.root)
        self.assertEqual(removed, ["old/gone.md"])
        self.assertFalse((self.root / "old").exists())

    def test_absent_path_is_not_reported_as_removed(self):
        write(self.root, ".engine-manifest.yml", MANIFEST)
        self.assertEqual(retire_lib.run(self.root), [])

    def test_dry_run_deletes_nothing(self):
        write(self.root, ".engine-manifest.yml", MANIFEST)
        write(self.root, "old/gone.md", "dead")
        self.assertEqual(retire_lib.run(self.root, dry_run=True), ["old/gone.md"])
        self.assertTrue((self.root / "old" / "gone.md").exists())

    def test_a_retired_path_in_the_persons_space_refuses_the_whole_sweep(self):
        write(self.root, ".engine-manifest.yml",
              MANIFEST.replace("  - old/gone.md", "  - mine/notes.md"))
        write(self.root, "mine/notes.md", "theirs")
        with self.assertRaises(retire_lib.RetirementRefused):
            retire_lib.run(self.root)
        self.assertTrue((self.root / "mine" / "notes.md").exists(),
                        "a refused sweep must delete nothing at all")


class UpdateEndToEndTests(unittest.TestCase):
    """The updater against a real remote, on a base that shares no history with the kit."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.kit, self.base = root / "kit", root / "base"
        self.addCleanup(self.tmp.cleanup)

        self.kit.mkdir()
        write(self.kit, ".engine-manifest.yml", MANIFEST)
        write(self.kit, "rules/canon.md", "new canon\n")
        write(self.kit, "rules/added.md", "arrived with this version\n")
        write(self.kit, "seed.md", "pristine seed\n")
        write(self.kit, "VERSION", "1.0.0\n")
        git(self.kit, "init", "-q", "-b", "main")
        git(self.kit, "add", "-A")
        git(self.kit, "commit", "-qm", "kit")

        # A base created by copying, then `git init` — no commit in common with the kit.
        self.base.mkdir()
        write(self.base, ".engine-manifest.yml", MANIFEST)
        write(self.base, "rules/canon.md", "old canon\n")
        write(self.base, "seed.md", "pristine seed\nwhat the person added\n")
        write(self.base, "old/gone.md", "the kit stopped shipping this\n")
        write(self.base, "mine/notes.md", "theirs\n")
        write(self.base, "VERSION", "0.9.0\n")
        install_tools(self.base)
        git(self.base, "init", "-q", "-b", "main")
        git(self.base, "add", "-A")
        git(self.base, "commit", "-qm", "their base")
        git(self.base, "remote", "add", "harness-kit", str(self.kit))

    def test_update_replaces_the_kit_keeps_the_person_and_drops_what_was_retired(self):
        done = run_update(self.base)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

        self.assertEqual((self.base / "rules/canon.md").read_text(), "new canon\n")
        self.assertTrue((self.base / "rules/added.md").exists())
        self.assertEqual((self.base / "VERSION").read_text().strip(), "1.0.0")

        self.assertEqual((self.base / "seed.md").read_text(),
                         "pristine seed\nwhat the person added\n",
                         "a template seeds once and is never touched again")
        self.assertTrue((self.base / "mine/notes.md").exists())
        self.assertFalse((self.base / "old").exists(), "a retired path must be dropped")

    def test_the_kit_is_found_by_its_address_whatever_the_remote_is_called(self):
        """Renaming the product must not strand every base that already exists.

        The remote's NAME lives in each base's git config, which no manifest section reaches and
        no clone carries — so it cannot be changed by shipping anything. If the updater looked the
        kit up by name, renaming the kit would silently cut off every base already in the world,
        and the fix could only travel through the channel it had just broken. The address is the
        one identifier the kit itself publishes and can move on purpose.
        """
        declared = MANIFEST.replace("version: 1.0.0",
                                    "version: 1.0.0\n\nkit_remote: %s" % self.kit, 1)
        write(self.kit, ".engine-manifest.yml", declared)
        write(self.base, ".engine-manifest.yml", declared)
        git(self.kit, "add", "-A"); git(self.kit, "commit", "-qm", "declare the address")
        git(self.base, "add", "-A"); git(self.base, "commit", "-qm", "same address")

        # The base calls it something else entirely — an older name, or one the person chose.
        git(self.base, "remote", "remove", "harness-kit")
        git(self.base, "remote", "add", "some-other-name", str(self.kit))

        done = run_update(self.base)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual((self.base / "rules/canon.md").read_text(), "new canon\n")

    def test_two_spellings_of_one_address_are_one_repository(self):
        """The same repository is written several ways, and all of them have to match.

        A manifest declares `https://host/owner/kit`; git config commonly holds
        `https://host/owner/kit.git` because that is what `git clone` records. Compared literally
        they differ, the kit is not recognised, and the base falls back to matching by name —
        which is exactly the fragility this replaced.
        """
        for a, b in (("https://h/o/kit", "https://h/o/kit.git"),
                     ("https://h/o/kit/", "https://h/o/kit"),
                     ("https://H/O/Kit", "https://h/o/kit")):
            self.assertTrue(update_module.same_repository(a, b), "%s vs %s" % (a, b))
        for a, b in (("https://h/o/kit", "https://h/o/other"),
                     ("https://h/o/kit", ""), ("", "")):
            self.assertFalse(update_module.same_repository(a, b), "%s vs %s" % (a, b))

    def test_the_persons_own_copy_is_never_mistaken_for_the_kit(self):
        """Every base has two remotes, and one of them is the person's private copy.

        `origin` is theirs and is listed first. Matching an address loosely — or not at all —
        makes the updater replace this base's kit paths out of the person's OWN repository, which
        looks like a successful update and is a silent corruption of the standard.
        """
        declared = MANIFEST.replace("version: 1.0.0",
                                    "version: 1.0.0\n\nkit_remote: %s" % self.kit, 1)
        write(self.kit, ".engine-manifest.yml", declared)
        write(self.base, ".engine-manifest.yml", declared)
        git(self.kit, "add", "-A"); git(self.kit, "commit", "-qm", "declare the address")

        # The person's own private copy, holding an older canon, added FIRST.
        theirs = Path(self.tmp.name) / "their-copy"
        theirs.mkdir()
        write(theirs, "rules/canon.md", "the person's stale copy\n")
        write(theirs, "VERSION", "0.0.1\n")
        write(theirs, ".engine-manifest.yml", declared)
        git(theirs, "init", "-q", "-b", "main")
        git(theirs, "add", "-A"); git(theirs, "commit", "-qm", "their copy")

        # `upstream` is an ordinary name for it, and git lists remotes alphabetically — so the
        # person's own copy comes FIRST. Anything that picks a remote by position rather than by
        # address lands on theirs.
        git(self.base, "remote", "remove", "harness-kit")
        git(self.base, "remote", "add", "origin", str(theirs))
        git(self.base, "remote", "add", "upstream", str(self.kit))
        git(self.base, "add", "-A"); git(self.base, "commit", "-qm", "two remotes")

        done = run_update(self.base)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual((self.base / "rules/canon.md").read_text(), "new canon\n",
                         "the update came from the person's own copy, not from the kit")
        self.assertEqual((self.base / "VERSION").read_text().strip(), "1.0.0")

    def test_a_seed_added_after_their_clone_still_reaches_them(self):
        # The gap this closes: templates never sync, so a seed introduced after somebody cloned
        # reached them never — while the canon arriving in the same update named it as if it
        # were there. Absent is created; present is left exactly alone.
        (self.base / "seed.md").unlink()
        done = run_update(self.base)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual((self.base / "seed.md").read_text(), "pristine seed\n")
        self.assertIn("a seed this base never received", done.stdout)

    def test_the_daily_check_stays_quiet_after_it_has_just_run(self):
        """`--max-age` is what `.claude/settings.json` runs at every session start.

        The existing check-mode test passes no `--max-age`, so `max_age > 0` is never true and
        the cache path — the flag's entire reason to exist — was never executed. A stuck cache
        would have made the daily check silently permanent, or a broken one made it announce the
        same version every session until the person stopped reading it.
        """
        first = run_update(self.base, "--check", "--max-age", "86400")
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertIn("a newer version of the kit is out", first.stdout)
        self.assertTrue((self.base / ".git" / "harness-update-check").exists(),
                        "the check did not record that it ran")

        again = run_update(self.base, "--check", "--max-age", "86400")
        self.assertEqual(again.returncode, 0)
        self.assertEqual(again.stdout.strip(), "", "it spoke twice within the same window")

        # A window that has passed lets it speak again — a cache that never expires is the same
        # failure as no check at all.
        stale = run_update(self.base, "--check", "--max-age", "0")
        self.assertIn("a newer version of the kit is out", stale.stdout)

    def test_global_wiring_that_names_another_base_is_reported(self):
        """Reported, never edited — it is outside the base (`rules/safety.md`).

        Nothing re-runs the installer, so a base that moved keeps a block pointing at where it
        used to be, and the canon then reaches that runtime from the wrong place or not at all.
        """
        import update as updater
        home = Path(self.tmp.name) / "fake-home"
        (home / ".claude").mkdir(parents=True)
        entry = home / ".claude" / "CLAUDE.md"
        original = Path.home

        entry.write_text("<!-- BEGIN HARNESS-KIT -->\n@/somewhere/else/AGENTS.md\n",
                         encoding="utf-8")
        Path.home = staticmethod(lambda: home)
        self.addCleanup(setattr, Path, "home", original)
        self.assertEqual(updater.stale_global_wiring(self.base), [str(entry)])

        # Naming this base — by import or by plain path — is not stale.
        entry.write_text("<!-- BEGIN HARNESS-KIT -->\n@%s/AGENTS.md\n" % self.base,
                         encoding="utf-8")
        self.assertEqual(updater.stale_global_wiring(self.base), [])
        # An entry this kit never wrote is none of its business.
        entry.write_text("something the person wrote themselves\n", encoding="utf-8")
        self.assertEqual(updater.stale_global_wiring(self.base), [])

    def test_a_dry_run_reports_a_refusal_instead_of_crashing(self):
        """A preview that raises tells the person nothing about what an update would do.

        The guards inside the migrate and retire passes read `engine:` and `exclude:` from the
        manifest on disk, which a real run reads only after the replacement — so a release that
        moves a path between sections can make the two disagree. Whatever else that produces, the
        preview has to come back with an answer.
        """
        declared = MANIFEST.replace("retired:", "retired:\n  - mine/notes.md")
        write(self.kit, ".engine-manifest.yml", declared)
        git(self.kit, "add", "-A")
        git(self.kit, "commit", "-qm", "retire a path this base calls its own")

        done = run_update(self.base, "--dry-run")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("dry-run", done.stdout)
        self.assertTrue((self.base / "mine/notes.md").exists(), "a dry run deleted something")

    def test_an_unreadable_check_cache_does_not_skip_the_check(self):
        cache = self.base / ".git" / "harness-update-check"
        cache.write_text("not json at all", encoding="utf-8")
        done = run_update(self.base, "--check", "--max-age", "86400")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("a newer version of the kit is out", done.stdout)

    def test_unsaved_work_at_a_path_this_release_claims_stops_the_update(self):
        """The likeliest collision of all, and the one pass that must not run after the loss.

        Until this run the path was the person's own space, so whatever sits there is theirs.
        Guarding only the paths the LOCAL manifest calls the kit's replaced it silently: exit 0,
        no warning, unrecoverable — the one outcome `rules/git-safety.md` exists to prevent.
        """
        write(self.base, "NOTICE.md", "the person's own file\n")
        git(self.base, "add", "-A")
        git(self.base, "commit", "-qm", "their file")
        write(self.base, "NOTICE.md", "the person's own file\nwith unsaved edits\n")

        widened = MANIFEST.replace("  - rules/", "  - rules/\n  - NOTICE.md")
        write(self.kit, ".engine-manifest.yml", widened)
        write(self.kit, "NOTICE.md", "the kit's version\n")
        git(self.kit, "add", "-A")
        git(self.kit, "commit", "-qm", "claim NOTICE.md for the kit")

        done = run_update(self.base)
        self.assertNotEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("NOTICE.md", done.stdout + done.stderr)
        self.assertIn("with unsaved edits", (self.base / "NOTICE.md").read_text(),
                      "the update destroyed work it had never guarded")

    def test_a_release_cannot_unprotect_the_persons_space_and_then_delete_it(self):
        """The guard compared the incoming manifest against itself.

        `retire` read `exclude:` from disk, and by the time it ran the update had already
        replaced the manifest — so both sides of the comparison came from the release. A release
        shipping `exclude:` empty could name the person's own directories under `retired:` and
        have them deleted, then instruct the agent to save, propagating the deletion to their
        only backup. Protection may widen in an update; it may never narrow.
        """
        hostile = MANIFEST.replace("exclude:\n  - mine/", "exclude: []")
        hostile = hostile.replace("retired:\n  - old/gone.md", "retired:\n  - mine/")
        write(self.kit, ".engine-manifest.yml", hostile)
        git(self.kit, "add", "-A")
        git(self.kit, "commit", "-qm", "a release that unprotects the person's space")

        done = run_update(self.base)
        self.assertNotEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("belong to the person", done.stdout + done.stderr)
        self.assertTrue((self.base / "mine" / "notes.md").exists(),
                        "a release deleted the person's own space")

    def test_moving_the_persons_own_files_is_shown_before_it_happens(self):
        """`rules/safety.md` requires a deletion or move to be seen before it runs.

        Replacement is the kit's own space and needs no ceremony, but `migrations:` exists
        precisely to rearrange the PERSON's — and an update carried them out on the strength of a
        manifest it had just fetched, reporting them afterwards.
        """
        declared = MANIFEST.replace(
            "retired:", "migrations:\n  - move pointers -> knowledge/pointers | note\n\nretired:")
        write(self.kit, ".engine-manifest.yml", declared)
        git(self.kit, "add", "-A")
        git(self.kit, "commit", "-qm", "declare a move")
        write(self.base, "pointers/stack.md", "theirs\n")
        git(self.base, "add", "-A")
        git(self.base, "commit", "-qm", "their pointers")

        shown = run_update(self.base)
        self.assertEqual(shown.returncode, 0, shown.stdout + shown.stderr)
        self.assertIn("their own files, not the kit's", shown.stdout)
        self.assertTrue((self.base / "pointers" / "stack.md").exists(),
                        "the move happened without being confirmed")
        # The replacement half still ran: only the person's own space waits on them.
        self.assertEqual((self.base / "rules/canon.md").read_text(), "new canon\n")

        done = run_update(self.base, "--confirm")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertTrue((self.base / "knowledge" / "pointers" / "stack.md").exists())

    def test_a_seed_this_release_introduces_lands_in_the_run_that_ships_it(self):
        """The asymmetry that hid this: the same case for `engine:` was tested and this was not.

        The existing seeding test deletes a seed the base's OWN manifest already declares, which
        never exercises a template the incoming release introduces — the headline case the
        seeding docstring promises. Preview and apply disagreed: the dry-run read the incoming
        list and said the seed would arrive, the run read the local one and did not deliver it.
        """
        widened = MANIFEST.replace("  - seed.md", "  - seed.md\n  - newseed.md")
        write(self.kit, ".engine-manifest.yml", widened)
        write(self.kit, "newseed.md", "a seed this release introduces\n")
        git(self.kit, "add", "-A")
        git(self.kit, "commit", "-qm", "introduce a seed")

        preview = run_update(self.base, "--dry-run")
        self.assertIn("newseed.md", preview.stdout, "the dry-run did not promise the seed")
        done = run_update(self.base)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertTrue((self.base / "newseed.md").exists(),
                        "the dry-run promised a seed the run did not deliver")
        self.assertIn("newseed.md", done.stdout)

    def test_a_path_this_release_adds_to_engine_lands_in_the_run_that_ships_it(self):
        """The manifest is itself one of the paths being replaced.

        Read the engine list only from the copy on disk and a file the release introduces is
        invisible to the run that ships it: it appears one whole update late, and the run that
        should have carried it says nothing at all.
        """
        widened = MANIFEST.replace("  - rules/", "  - rules/\n  - GLOSSARY.md")
        write(self.kit, ".engine-manifest.yml", widened)
        write(self.kit, "GLOSSARY.md", "a kit path this release introduces\n")
        git(self.kit, "add", "-A")
        git(self.kit, "commit", "-qm", "widen engine")

        done = run_update(self.base)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertTrue((self.base / "GLOSSARY.md").exists(),
                        "a newly declared kit path did not land in the run that shipped it")
        self.assertIn("a kit path this release introduced", done.stdout)

    def test_a_dry_run_previews_what_the_release_declares_not_what_the_base_knows(self):
        """Moves and deletions are the two operations review-before-the-fact exists for."""
        declared = MANIFEST.replace(
            "retired:",
            "migrations:\n  - move pointers -> knowledge/pointers | note\n\nretired:")
        declared = declared.replace("retired:\n", "retired:\n  - old/gone.md\n", 1)
        write(self.kit, ".engine-manifest.yml", declared)
        git(self.kit, "add", "-A")
        git(self.kit, "commit", "-qm", "declare a move and a retirement")
        write(self.base, "pointers/stack.md", "theirs\n")
        git(self.base, "add", "-A")
        git(self.base, "commit", "-qm", "their pointers")

        done = run_update(self.base, "--dry-run")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("move pointers to knowledge/pointers", done.stdout)
        self.assertIn("drop old/gone.md", done.stdout)
        self.assertTrue((self.base / "pointers/stack.md").exists(), "a dry run changed something")

    def test_a_blocked_move_does_not_cancel_an_unrelated_deletion(self):
        """The two passes are independent, so one refusing must not silently skip the other.

        Returning on the first refusal left every declared deletion undone for as long as an
        unrelated move stayed blocked — and said nothing, so nobody could know.
        """
        declared = MANIFEST.replace(
            "retired:",
            "migrations:\n  - move pointers -> knowledge/pointers | note\n\nretired:")
        write(self.kit, ".engine-manifest.yml", declared)
        git(self.kit, "add", "-A")
        git(self.kit, "commit", "-qm", "declare the move")
        write(self.base, "pointers/stack.md", "theirs\n")
        write(self.base, "knowledge/pointers/already.md", "in the way\n")
        git(self.base, "add", "-A")
        git(self.base, "commit", "-qm", "a destination already occupied")

        done = run_update(self.base, "--confirm")
        self.assertNotEqual(done.returncode, 0, "a blocked move must not report success")
        self.assertTrue((self.base / "pointers/stack.md").exists(), "the move must not be forced")
        self.assertFalse((self.base / "old").exists(),
                         "the unrelated retirement was skipped because the move was blocked")

    def test_a_declared_move_is_carried_by_the_update_itself(self):
        # End to end: the kit declares it, the base takes the update, the path has moved. The
        # declaration is read from the manifest that arrives in the SAME run — which is why it is
        # data and not code in the updater, whose own new code would take effect an update late.
        declared = MANIFEST.replace(
            "retired:",
            "migrations:\n  - move pointers -> knowledge/pointers | your notes may name the old place\n\nretired:")
        write(self.kit, ".engine-manifest.yml", declared)
        git(self.kit, "add", "-A")
        git(self.kit, "commit", "-qm", "declare the move")
        write(self.base, "pointers/stack.md", "theirs\n")
        git(self.base, "add", "-A")
        git(self.base, "commit", "-qm", "their pointers")

        # Shown first: a move rearranges the person's own files, so they see it before it runs.
        shown = run_update(self.base)
        self.assertEqual(shown.returncode, 0, shown.stdout + shown.stderr)
        self.assertIn("move pointers to knowledge/pointers", shown.stdout)
        self.assertTrue((self.base / "pointers").exists(), "it moved without being confirmed")

        done = run_update(self.base, "--confirm")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertFalse((self.base / "pointers").exists())
        self.assertEqual((self.base / "knowledge/pointers/stack.md").read_text(), "theirs\n")
        self.assertIn("may name the old place", done.stdout)

        # And it converges: a second update has nothing left to carry.
        git(self.base, "add", "-A")
        git(self.base, "commit", "-qm", "saved")
        again = run_update(self.base)
        self.assertNotIn("moved pointers", again.stdout)

    def test_the_base_follows_the_kit_when_the_kit_publishes_a_new_address(self):
        # The remote lives in git config, which no manifest section reaches. Publishing the new
        # address a release BEFORE the move is the only way a base can follow: by the time the kit
        # moves, everyone is already pointed at where it went.
        moved = MANIFEST.replace("version: 1.0.0",
                                 "version: 1.0.0\n\nkit_remote: https://example.invalid/moved")
        write(self.kit, ".engine-manifest.yml", moved)
        git(self.kit, "add", "-A")
        git(self.kit, "commit", "-qm", "publish the new address")

        done = run_update(self.base)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(
            git(self.base, "remote", "get-url", "harness-kit").stdout.strip(),
            "https://example.invalid/moved")
        self.assertIn("the kit now lives at", done.stdout)

    def test_a_second_run_changes_nothing_and_says_so(self):
        run_update(self.base)
        git(self.base, "add", "-A")
        git(self.base, "commit", "-qm", "saved")
        done = run_update(self.base)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("0 changed", done.stdout)
        self.assertIn("already current", done.stdout)

    def test_dry_run_applies_nothing(self):
        done = run_update(self.base, "--dry-run")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual((self.base / "rules/canon.md").read_text(), "old canon\n")
        self.assertTrue((self.base / "old/gone.md").exists())

    def test_unsaved_edits_in_kit_space_stop_the_update(self):
        write(self.base, "rules/canon.md", "the person edited a kit path\n")
        done = run_update(self.base)
        self.assertEqual(done.returncode, 2)
        self.assertIn("unsaved local edits", done.stderr)
        self.assertEqual((self.base / "rules/canon.md").read_text(),
                         "the person edited a kit path\n", "nothing may be overwritten")

    def test_a_base_with_no_kit_remote_says_so_instead_of_failing_obscurely(self):
        git(self.base, "remote", "remove", "harness-kit")
        done = run_update(self.base)
        self.assertEqual(done.returncode, 2)
        self.assertIn("not connected to the kit", done.stderr)

    def test_a_retired_path_reaching_the_persons_space_refuses_and_deletes_nothing(self):
        broken = MANIFEST.replace("  - old/gone.md", "  - mine/notes.md")
        write(self.kit, ".engine-manifest.yml", broken)
        git(self.kit, "add", "-A")
        git(self.kit, "commit", "-qm", "bad retirement")
        write(self.base, ".engine-manifest.yml", broken)
        git(self.base, "add", "-A")
        git(self.base, "commit", "-qm", "same manifest")

        done = run_update(self.base)
        self.assertEqual(done.returncode, 2)
        self.assertIn("belong to the person", done.stderr)
        self.assertTrue((self.base / "mine/notes.md").exists())

    def test_check_mode_reports_a_newer_version_and_changes_nothing(self):
        done = subprocess.run(
            [sys.executable, str(self.base / "tools" / "update.py"),
             "--branch", "main", "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("1.0.0", done.stdout)
        self.assertEqual((self.base / "rules/canon.md").read_text(), "old canon\n")


class SyncTests(unittest.TestCase):
    """The tool every session runs, on a base of its own."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name) / "base"
        self.base.mkdir(parents=True)
        self.addCleanup(self.tmp.cleanup)
        (self.base / "tools").mkdir()
        shutil.copy2(KIT_ROOT / "tools" / "sync.py", self.base / "tools" / "sync.py")
        git(self.base, "init", "-q", "-b", "main")
        git(self.base, "config", "user.name", "t")
        git(self.base, "config", "user.email", "t@example.invalid")
        write(self.base, "note.md", "first\n")
        write(self.base, ".gitattributes", "* text=auto\n")
        git(self.base, "add", "-A")
        git(self.base, "commit", "-qm", "start")

    def run_sync(self, *args):
        return subprocess.run(
            [sys.executable, str(self.base / "tools" / "sync.py"), *args],
            capture_output=True, text=True,
        )

    def test_a_base_with_no_remote_is_told_it_lives_on_one_machine(self):
        # This fixture has no remote, which is the loudest state there is — not a quiet one.
        done = self.run_sync("status")
        self.assertIn("unsaved here: none", done.stdout)
        self.assertIn("lives only on this machine", done.stdout)

    def test_a_base_in_step_says_nothing_at_all(self):
        """The branch that governs every ordinary session, and nothing covered it.

        A test whose fixture has no remote can never reach it: the tool correctly asks for a
        remote instead, so `unsaved here: none` passed while the directive said the opposite of
        the test's own name.
        """
        remote = Path(self.tmp.name) / "their-remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        git(self.base, "remote", "add", "origin", str(remote))
        git(self.base, "push", "-q", "-u", "origin", "main")
        done = self.run_sync("status")
        self.assertIn("unsaved here: none", done.stdout)
        self.assertIn("nothing — the base is in step", done.stdout)

    def test_a_base_on_more_than_one_branch_is_reported(self):
        """What ARCHITECTURE names as holding invariant 2, and nothing tested.

        Reported rather than enforced on purpose — someone mid-experiment has a reason, and
        refusing to sync would strand them. But a report nothing checks is not a report.
        """
        before = self.run_sync("status")
        self.assertNotIn("branches:", before.stdout, "one branch should say nothing")
        git(self.base, "branch", "experiment")
        after = self.run_sync("status")
        self.assertIn("branches: 2", after.stdout)
        self.assertIn("invisible on a phone", after.stdout)

    def test_a_detached_head_is_named_before_anything_else(self):
        # Every later question — ahead, behind, which branch to push — is meaningless here, so
        # this has to be caught first rather than reported alongside them.
        head = git(self.base, "rev-parse", "HEAD").stdout.strip()
        git(self.base, "checkout", "-q", head)
        done = self.run_sync("status")
        self.assertIn("single branch", done.stdout)

    def test_a_changed_tracked_dotfile_keeps_its_leading_dot(self):
        # Porcelain encodes state in the first two columns, so a MODIFIED tracked file's line
        # begins with a space. Strip the output and that space goes with the first line's dot,
        # naming a file that does not exist. An untracked file starts with `??` and would not
        # reproduce it — the regression needs a tracked one, sorting first.
        write(self.base, ".gitattributes", "* text=auto eol=lf\n")
        done = self.run_sync("status")
        self.assertIn(".gitattributes", done.stdout)
        self.assertNotIn("(gitattributes", done.stdout)

    def test_save_records_the_work_and_says_why(self):
        write(self.base, "note.md", "second\n")
        done = self.run_sync("save", "Record why this exists")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("Record why this exists",
                      git(self.base, "log", "-1", "--format=%B").stdout)

    def test_save_without_a_reason_is_refused(self):
        write(self.base, "note.md", "third\n")
        done = self.run_sync("save")
        self.assertEqual(done.returncode, 2)
        self.assertIn("WHY", done.stdout)

    def test_a_base_with_nowhere_to_send_work_says_it_stayed_here(self):
        write(self.base, "note.md", "fourth\n")
        done = self.run_sync("save", "Keep it local")
        self.assertEqual(done.returncode, 0)
        self.assertIn("recorded on this machine", done.stdout)

    def test_session_start_never_fails_a_session(self):
        write(self.base, "note.md", "fifth\n")
        self.assertEqual(self.run_sync("session-start").returncode, 0)


class RefusalWordingTests(unittest.TestCase):
    """A refusal the person cannot read is worse than none."""

    def setUp(self):
        sys.path.insert(0, str(KIT_ROOT / "tools"))
        import importlib
        self.sync = importlib.import_module("sync")

    def test_a_private_email_refusal_becomes_an_offer(self):
        directive = self.sync.push_refusal_directive(
            "remote: error: GH007: Your push would publish a private email address.")
        self.assertIn("noreply", directive)
        self.assertNotIn("GH007", directive)

    def test_an_unknown_refusal_still_says_what_it_costs_them(self):
        directive = self.sync.push_refusal_directive("some brand new failure")
        self.assertIn("safe on this machine", directive)


class DivergenceAndOutageTests(unittest.TestCase):
    """The two shapes that lose work if they are handled wrong: both sides moved, and no network."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.remote = root / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.remote)], check=True)
        # Seed the remote first. Cloning an EMPTY repository twice gives each copy its own root
        # commit, which is a different situation entirely — covered by its own test below.
        seed = root / "seed"
        subprocess.run(["git", "clone", "-q", str(self.remote), str(seed)], check=True)
        git(seed, "config", "user.name", "t")
        git(seed, "config", "user.email", "t@example.invalid")
        write(seed, "base.md", "the base\n")
        git(seed, "add", "-A")
        git(seed, "commit", "-qm", "start")
        git(seed, "push", "-q", "origin", "main")
        self.phone = self._clone(root / "phone")
        self.laptop = self._clone(root / "laptop")

    def _clone(self, path: Path) -> Path:
        subprocess.run(["git", "clone", "-q", str(self.remote), str(path)], check=True)
        git(path, "config", "user.name", "t")
        git(path, "config", "user.email", "t@example.invalid")
        (path / "tools").mkdir(exist_ok=True)
        shutil.copy2(KIT_ROOT / "tools" / "sync.py", path / "tools" / "sync.py")
        return path

    def sync(self, base: Path, *args):
        return subprocess.run([sys.executable, str(base / "tools" / "sync.py"), *args],
                              capture_output=True, text=True)

    def test_work_on_two_sides_is_put_together_and_neither_is_dropped(self):
        write(self.laptop, "on-the-laptop.md", "written at the desk\n")
        self.assertEqual(self.sync(self.laptop, "save", "Laptop work").returncode, 0)

        write(self.phone, "on-the-phone.md", "written on the train\n")
        done = self.sync(self.phone, "save", "Phone work")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

        self.assertTrue((self.phone / "on-the-laptop.md").exists(),
                        "the other side's work must be picked up, not overwritten")
        self.assertTrue((self.phone / "on-the-phone.md").exists())
        landed = git(self.remote, "ls-tree", "-r", "--name-only", "main").stdout
        self.assertIn("on-the-laptop.md", landed)
        self.assertIn("on-the-phone.md", landed)

    def test_no_force_or_rebase_is_ever_issued(self):
        # Every python tool that touches git, not just this one: the invariant is about what the
        # kit does to a person's repository, and it does not stop at one file. Look for them as
        # passed ARGUMENTS, not as words — these files explain in prose that they never rebase,
        # and a prose ban must not read as a violation of itself.
        for name in ("sync.py", "update.py", "check_kit.py"):
            source = (KIT_ROOT / "tools" / name).read_text(encoding="utf-8")
            for banned in ('"--force"', '"-f"', '"--hard"', '"rebase"', '"--force-with-lease"'):
                self.assertNotIn(banned, source, "%s in %s disables the protection that makes "
                                                 "divergence recoverable" % (banned, name))

    def test_the_updater_replaces_and_never_merges(self):
        """The invariant the whole update design rests on, and nothing was checking it.

        An update must never hand the person a conflict inside a file they did not write. That
        holds today only because the updater issues `checkout` and nothing else — a property no
        gate stated, so a merge added here would have shipped green.
        """
        source = (KIT_ROOT / "tools" / "update.py").read_text(encoding="utf-8")
        for banned in ('"merge"', '"cherry-pick"', '"stash"', '"reset"', '"revert"'):
            self.assertNotIn(banned, source,
                             "%s can leave the person adjudicating a kit file they never wrote"
                             % banned)

    def test_two_different_bases_pointed_at_one_place_are_named_not_merged(self):
        # A person who runs the installer again on a second machine as a NEW base, then points it
        # at the repository their real base already lives in. git calls it "unrelated histories";
        # the person must be told what it means for them, and nothing may be merged blindly.
        stranger = self.phone.parent / "stranger"
        stranger.mkdir()
        git(stranger, "init", "-q", "-b", "main")
        git(stranger, "config", "user.name", "t")
        git(stranger, "config", "user.email", "t@example.invalid")
        (stranger / "tools").mkdir()
        shutil.copy2(KIT_ROOT / "tools" / "sync.py", stranger / "tools" / "sync.py")
        write(stranger, "fresh.md", "a brand new base\n")
        git(stranger, "add", "-A")
        git(stranger, "commit", "-qm", "fresh")
        git(stranger, "remote", "add", "origin", str(self.remote))
        git(stranger, "fetch", "-q", "origin", "main")
        git(stranger, "branch", "--set-upstream-to", "origin/main", "main")

        done = self.sync(stranger, "save", "Work on the second machine")
        self.assertEqual(done.returncode, 1)
        self.assertIn("DIFFERENT base", done.stdout)
        self.assertNotIn("fatal:", done.stdout, "raw git output must never reach the person")
        self.assertTrue((stranger / "fresh.md").exists(), "nothing of theirs may be lost")

    def test_an_unreachable_remote_keeps_the_work_and_says_where_it_stands(self):
        git(self.phone, "remote", "set-url", "origin", str(self.phone.parent / "gone.git"))
        write(self.phone, "note.md", "written while offline\n")
        done = self.sync(self.phone, "save", "Offline work")
        self.assertEqual(done.returncode, 1)
        self.assertIn("could not send it out", done.stdout)
        self.assertNotEqual(git(self.phone, "log", "-1", "--format=%s").stdout.strip(), "",
                            "the work must still be recorded locally")


class SelfHealTests(unittest.TestCase):
    """The updater ships through the update, so a broken one cannot repair itself normally."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.kit, self.base = root / "kit", root / "base"
        self.addCleanup(self.tmp.cleanup)

        self.kit.mkdir()
        write(self.kit, ".engine-manifest.yml", MANIFEST)
        write(self.kit, "rules/canon.md", "new canon\n")
        write(self.kit, "seed.md", "pristine seed\n")
        write(self.kit, "VERSION", "1.0.0\n")
        install_tools(self.kit)
        git(self.kit, "init", "-q", "-b", "main")
        git(self.kit, "add", "-A")
        git(self.kit, "commit", "-qm", "kit")

        self.base.mkdir()
        write(self.base, ".engine-manifest.yml", "version: 0.9.0\n")  # nothing readable in it
        write(self.base, "rules/canon.md", "old canon\n")
        write(self.base, "seed.md", "pristine seed\n")
        write(self.base, "VERSION", "0.9.0\n")
        install_tools(self.base)
        git(self.base, "init", "-q", "-b", "main")
        git(self.base, "add", "-A")
        git(self.base, "commit", "-qm", "their base")
        git(self.base, "remote", "add", "harness-kit", str(self.kit))

    def test_a_base_that_declares_no_kit_paths_is_not_treated_as_corrupt(self):
        """`engine: []` and a lost `engine:` key read the same and mean opposite things.

        A base can legitimately share no paths with the kit — its own canon, developed past the
        kit's, with the machinery present so that adopting a path later is a decision rather than
        a rebuild. Refusing that base with a corruption error every session teaches its owner to
        ignore the one message that would matter if the file really were damaged.
        """
        write(self.base, ".engine-manifest.yml",
              "version: 1.0.0\n\nengine: []\n\ntemplate: []\n\nexclude:\n  - mine/\n")
        git(self.base, "add", "-A")
        git(self.base, "commit", "-qm", "no kit paths adopted")
        done = run_update(self.base)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("shares no paths with the kit", done.stdout)
        self.assertNotIn("corrupt", done.stdout + done.stderr)

    def test_a_base_whose_manifest_is_unreadable_refuses_rather_than_doing_nothing(self):
        done = run_update(self.base)
        self.assertEqual(done.returncode, 2)
        self.assertIn("no engine: section", done.stderr)
        self.assertEqual((self.base / "rules/canon.md").read_text(), "old canon\n")

    def test_self_heal_restores_the_machinery_and_completes_the_update(self):
        done = run_update(self.base, "--self-heal")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual((self.base / "rules/canon.md").read_text(), "new canon\n")
        self.assertEqual((self.base / "VERSION").read_text().strip(), "1.0.0")


@unittest.skipIf(shutil.which("bash") is None, "the shell installer needs bash")
class InstallerTests(unittest.TestCase):
    """The installer, run the way a person runs it — once, on a machine that has nothing."""

    ANSWERS = ("{home}", "mybase", "Русский", "Y", "N", "N", "N",
               "Test Person", "test@example.invalid", "N")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        self.home.mkdir(parents=True)
        self.addCleanup(self.tmp.cleanup)

    def install(self):
        answers = "\n".join(a.format(home=self.home) for a in self.ANSWERS) + "\n"
        # Declaring this is the point: without it the installer refuses, because an unanswered
        # question taking a default is indistinguishable from a real answer in the output.
        env = dict(os.environ, HOME=str(self.home), HARNESS_ANSWERS_ON_STDIN="1")
        return subprocess.run(["bash", str(KIT_ROOT / "install.sh")], input=answers,
                              capture_output=True, text=True, env=env, cwd=str(KIT_ROOT))

    def test_a_fresh_install_leaves_a_base_that_can_travel(self):
        done = self.install()
        self.assertEqual(done.returncode, 0, done.stdout[-2000:] + done.stderr[-2000:])
        base = self.home / "mybase"

        self.assertTrue((base / "projects" / "_index.md").exists(),
                        "what the person builds must live inside the base")
        self.assertTrue((base / "tools" / "sync.py").exists())
        self.assertTrue((base / ".claude" / "settings.json").exists())

        self.assertEqual(git(base, "symbolic-ref", "--short", "HEAD").stdout.strip(), "main",
                         "a base on another branch pushes to a second branch, and the phone "
                         "clones the default one and finds nothing")
        self.assertEqual(len(git(base, "log", "--oneline").stdout.strip().splitlines()), 1,
                         "the base starts with a history, not a pile of staged files")
        self.assertEqual(git(base, "status", "--porcelain").stdout.strip(), "")
        self.assertIn("harness-kit", git(base, "remote").stdout,
                      "without the kit remote the base can never receive a fix")

        profile = (base / "profile.md").read_text(encoding="utf-8")
        self.assertIn("**Language:** Русский", profile)

        wiring = (self.home / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("BEGIN HARNESS-KIT", wiring)
        self.assertIn("@%s/AGENTS.md" % base, wiring,
                      "the global entry points at the one contract, not at a copied rule list")

    def test_running_it_twice_does_not_stack_a_second_wiring_block(self):
        self.install()
        self.install()
        wiring = (self.home / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertEqual(wiring.count("BEGIN HARNESS-KIT"), 1)


class MigrationTests(unittest.TestCase):
    """The channel for a change replacement cannot express: a path in the person's space moving."""

    BASE_MANIFEST = MANIFEST

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def declare(self, *lines):
        body = "migrations:\n" + "".join("  - %s\n" % line for line in lines) if lines else "migrations: []\n"
        write(self.root, ".engine-manifest.yml", self.BASE_MANIFEST + "\n" + body)

    def test_a_declared_move_is_carried_out(self):
        self.declare("move pointers -> knowledge/pointers")
        write(self.root, "pointers/stack.md", "theirs\n")
        carried = migrate_lib.run(self.root)
        self.assertEqual(len(carried), 1)
        self.assertFalse((self.root / "pointers").exists())
        self.assertEqual((self.root / "knowledge/pointers/stack.md").read_text(), "theirs\n")

    def test_running_it_again_does_nothing(self):
        # Convergence is the whole design: every update re-runs every declaration, so a base at
        # any version — including one dark for a year — lands in the same place.
        self.declare("move pointers -> knowledge/pointers")
        write(self.root, "pointers/stack.md", "theirs\n")
        migrate_lib.run(self.root)
        self.assertEqual(migrate_lib.run(self.root), [])

    def test_a_base_that_never_had_the_old_path_is_untouched(self):
        self.declare("move pointers -> knowledge/pointers")
        self.assertEqual(migrate_lib.run(self.root), [])
        self.assertFalse((self.root / "knowledge/pointers").exists())

    def test_it_refuses_to_overwrite_what_the_person_already_has(self):
        self.declare("move pointers -> knowledge/pointers")
        write(self.root, "pointers/stack.md", "old\n")
        write(self.root, "knowledge/pointers/stack.md", "newer, theirs\n")
        with self.assertRaises(migrate_lib.MigrationRefused):
            migrate_lib.run(self.root)
        self.assertEqual((self.root / "knowledge/pointers/stack.md").read_text(), "newer, theirs\n")
        self.assertTrue((self.root / "pointers/stack.md").exists())

    def test_it_refuses_to_reach_into_the_kits_own_space(self):
        # Replacement and retirement already own that; a move there is an authoring mistake and
        # would fight the checkout that runs beside it.
        self.declare("move rules -> knowledge/rules")
        write(self.root, "rules/canon.md", "kit\n")
        with self.assertRaises(migrate_lib.MigrationRefused):
            migrate_lib.run(self.root)
        self.assertTrue((self.root / "rules/canon.md").exists())

    def test_a_verb_from_a_newer_kit_stops_the_run(self):
        # Silently skipping it would leave the kit believing a change landed that never did.
        self.declare("reshape knowledge/_index.md")
        with self.assertRaises(migrate_lib.MigrationRefused) as refusal:
            migrate_lib.run(self.root)
        self.assertIn("once more", str(refusal.exception))

    def test_a_note_rides_with_the_move(self):
        self.declare("move pointers -> knowledge/pointers | your own notes may name the old place")
        write(self.root, "pointers/stack.md", "theirs\n")
        carried = migrate_lib.run(self.root)
        self.assertIn("may name the old place", carried[0].note)

    def test_dry_run_moves_nothing(self):
        self.declare("move pointers -> knowledge/pointers")
        write(self.root, "pointers/stack.md", "theirs\n")
        self.assertEqual(len(migrate_lib.run(self.root, dry_run=True)), 1)
        self.assertTrue((self.root / "pointers/stack.md").exists())


class ReleaseGateTests(unittest.TestCase):
    """The authoring gates, on a repository shaped like the kit."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        sys.path.insert(0, str(KIT_ROOT / "tools"))
        import importlib
        self.gate = importlib.import_module("check_kit")
        self.failures = []

    def fail_collector(self, message, why=""):
        self.failures.append(message)

    def test_an_edited_seed_that_already_shipped_fails_the_release(self):
        write(self.root, "VERSION", "1.0.0\n")
        write(self.root, "seed.md", "as released\n")
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "release")
        write(self.root, "seed.md", "edited after the release\n")
        self.gate.check_seeds_unchanged(self.root, ["seed.md"], "main", self.fail_collector)
        self.assertEqual(len(self.failures), 1)
        self.assertIn("seed", self.failures[0])

    def test_a_seed_added_since_the_release_is_fine(self):
        write(self.root, "VERSION", "1.0.0\n")
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "release")
        write(self.root, "new-seed.md", "arrived after\n")
        self.gate.check_seeds_unchanged(self.root, ["new-seed.md"], "main", self.fail_collector)
        self.assertEqual(self.failures, [], "seeding delivers a seed that is merely new")

    def test_nothing_is_frozen_before_the_first_release(self):
        write(self.root, "seed.md", "as committed\n")  # no VERSION at the ref
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "unreleased")
        write(self.root, "seed.md", "still being written\n")
        self.gate.check_seeds_unchanged(self.root, ["seed.md"], "main", self.fail_collector)
        self.assertEqual(self.failures, [])

    def test_the_kits_own_notes_in_the_persons_space_fail_the_release(self):
        # There is no extraction step: a clone carries the whole repository, so anything the kit's
        # author left under activities/ or knowledge/ lands in every base as though it were theirs.
        write(self.root, "activities/_index.md", "the seed\n")
        write(self.root, "activities/my-work-log.md", "the author's own notes\n")
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "kit")
        self.gate.check_person_space_ships_pristine(
            self.root, ["activities/_index.md"], ["activities/"], self.fail_collector)
        self.assertEqual(len(self.failures), 1)
        self.assertIn("my-work-log.md", self.failures[0])

    def test_the_seed_itself_is_allowed_to_ship(self):
        write(self.root, "activities/_index.md", "the seed\n")
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "kit")
        self.gate.check_person_space_ships_pristine(
            self.root, ["activities/_index.md"], ["activities/"], self.fail_collector)
        self.assertEqual(self.failures, [])


class ReleaseGateWiringTests(unittest.TestCase):
    """The gate as an author actually runs it — a check that exists but is not wired runs never."""

    GATE_MANIFEST = """version: 1.0.0

kit_remote: https://example.invalid/kit

engine:
  - rules/
  - VERSION
  - AGENTS.md
  - CLAUDE.md
  - .engine-manifest.yml
  - .claude-plugin/
  - tools/check_kit.py
  - tools/update.py
  - tools/lib/

template:
  - seed.md

exclude: []

migrations: []

retired: []
"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        write(self.root, ".engine-manifest.yml", self.GATE_MANIFEST)
        write(self.root, "VERSION", "1.0.0\n")
        write(self.root, ".claude-plugin/plugin.json", '{"version": "1.0.0"}\n')
        write(self.root, "rules/canon.md", "the rule\n")
        write(self.root, "AGENTS.md", "canon:\n@rules/canon.md\n")
        write(self.root, "CLAUDE.md", "@AGENTS.md\n")
        write(self.root, "seed.md", "as released\n")
        install_tools(self.root)
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "release 1.0.0")

    def gate(self, *args):
        return subprocess.run(
            [sys.executable, str(self.root / "tools" / "check_kit.py"), *args],
            capture_output=True, text=True, cwd=str(self.root))

    def test_a_coherent_kit_passes(self):
        done = self.gate("--authoring")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_editing_a_seed_that_already_shipped_fails_the_release(self):
        write(self.root, "seed.md", "edited after the release\n")
        done = self.gate("--authoring")
        self.assertEqual(done.returncode, 1)
        # Not the bare word "seed": the fixture's file IS `seed.md`, so half the gate's other
        # failures name it too and would satisfy a substring check identically.
        self.assertIn("already exists on every base was edited", done.stderr)

    def test_a_rule_whose_name_hides_inside_another_is_still_caught(self):
        # The regression: `safety.md` is a substring of `git-safety.md`, so searching AGENTS.md for
        # the bare filename reported the rule as listed when nothing listed it. The gate said the
        # kit was ready to ship and the rule reached no runtime at all.
        write(self.root, "rules/git-canon.md", "the long one\n")
        write(self.root, "rules/canon.md", "the short one whose name hides in the long one\n")
        write(self.root, "AGENTS.md", "canon:\n@rules/git-canon.md\n")
        git(self.root, "add", "-A")
        done = self.gate()
        self.assertEqual(done.returncode, 1)
        self.assertIn("canon.md", done.stderr)

    def test_a_new_tool_declared_nowhere_fails_the_release(self):
        write(self.root, "tools/orphan.py", "print('reaches nobody')\n")
        git(self.root, "add", "-A")
        done = self.gate("--authoring")
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("orphan.py", done.stderr)

    def test_a_removal_with_no_retired_line_fails_the_release(self):
        # git ADDS and UPDATES on checkout and never deletes, so without the line the file lives
        # on every base forever, offering a contract nothing honours.
        released = git(self.root, "rev-parse", "HEAD").stdout.strip()
        (self.root / "rules" / "canon.md").unlink()
        write(self.root, "rules/other.md", "still here\n")
        write(self.root, "AGENTS.md", "canon:\n@rules/other.md\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "drop a rule without retiring it")
        done = self.gate("--authoring", "--since", released)
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("canon.md", done.stderr)

    def test_changing_a_kit_path_without_moving_version_fails_the_release(self):
        released = git(self.root, "rev-parse", "HEAD").stdout.strip()
        write(self.root, "rules/canon.md", "the rule, revised\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "revise the rule")
        done = self.gate("--authoring", "--since", released)
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("VERSION", done.stderr)

    def test_a_dead_section_pointer_fails_the_gate_as_an_author_runs_it(self):
        """Wired, not merely present. A check nobody calls runs never.

        Calling the function directly proves it works; only running the gate the way an author
        does proves it is reached — and detaching a check is invisible either way otherwise.
        """
        write(self.root, "rules/canon.md", "# The Rule\n\n## A Real Section\n\nbody\n")
        write(self.root, "AGENTS.md",
              'canon:\n@rules/canon.md\n\nSee `rules/canon.md` -> "A Section That Moved".\n')
        git(self.root, "add", "-A")
        done = self.gate()
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("cites a section", done.stderr)

    def test_the_kits_own_notes_in_the_persons_space_fail_the_release(self):
        write(self.root, ".engine-manifest.yml",
              self.GATE_MANIFEST.replace("exclude: []", "exclude:\n  - notes/"))
        write(self.root, "notes/my-work-log.md", "the author's own notes\n")
        git(self.root, "add", "-A")
        done = self.gate("--authoring")
        self.assertEqual(done.returncode, 1)
        self.assertIn("my-work-log.md", done.stderr)

    def test_a_migration_into_the_kits_own_space_fails_the_release(self):
        write(self.root, ".engine-manifest.yml",
              self.GATE_MANIFEST.replace("migrations: []",
                                         "migrations:\n  - move rules -> elsewhere"))
        done = self.gate("--authoring")
        self.assertEqual(done.returncode, 1)
        self.assertIn("kit's own space", done.stderr)

    def test_the_structural_half_stays_quiet_about_a_persons_own_files(self):
        # A person's base runs this half through /harness-doctor, where their own knowledge and
        # activities are exactly what is supposed to be there.
        write(self.root, ".engine-manifest.yml",
              self.GATE_MANIFEST.replace("exclude: []", "exclude:\n  - notes/"))
        write(self.root, "notes/their-thinking.md", "theirs\n")
        git(self.root, "add", "-A")
        done = self.gate()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)


class PortabilityGateTests(unittest.TestCase):
    """Every clause must fire on real code and stay silent on prose. A gate that cannot fail is
    indistinguishable from a codebase that is clean."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def findings(self, relpath, body, binary=False):
        target = self.root / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        if binary:
            target.write_bytes(body)
        else:
            target.write_text(body, encoding="utf-8")
        return portability.scan_file(self.root, relpath)

    def clauses(self, relpath, body, binary=False):
        return sorted({f.rule.clause for f in self.findings(relpath, body, binary)})

    # -- CP-2: bash 4 and GNU/BSD splits -------------------------------------
    def test_bash_four_builtins_are_caught(self):
        for line in ("mapfile -t x < f", "readarray -t x < f", "declare -A m",
                     'echo "${name^^}"', 'echo "${name,,}"'):
            self.assertIn("CP-2", self.clauses("a.sh", line + "\n"), line)

    def test_commands_whose_flags_differ_by_platform_are_caught(self):
        for line in ("readlink -f x", "sed -i s/a/b/ f", "stat -c %s f", "stat -f %z f",
                     "grep -P foo f"):
            self.assertIn("CP-2", self.clauses("a.sh", line + "\n"), line)

    def test_a_portable_equivalent_is_not_a_finding(self):
        clean = 'while IFS= read -r line; do :; done < f\ntr "a-z" "A-Z" < f\ngrep -E foo f\n'
        self.assertEqual(self.clauses("a.sh", clean), [])

    # -- CP-1: a path that exists on one machine ------------------------------
    def test_a_hardcoded_home_path_is_caught_in_shell_and_python(self):
        self.assertIn("CP-1", self.clauses("a.sh", 'cd /Users/someone/base\n'))
        self.assertIn("CP-1", self.clauses("a.py", 'p = "/home/someone/base"\n'))

    # -- CP-5: text decoded through whatever the platform defaults to ---------
    def test_python_text_io_without_an_encoding_is_caught(self):
        for line in ('t = p.read_text()', 't = path.read_text(errors="replace")',
                     'f = open(path)', 'f = open(path, "w")'):
            self.assertIn("CP-5", self.clauses("a.py", line + "\n"), line)

    def test_declared_encoding_and_binary_mode_are_not_findings(self):
        clean = ('t = p.read_text(encoding="utf-8")\n'
                 'f = open(path, "w", encoding="utf-8")\n'
                 'b = open(path, "rb")\n')
        self.assertEqual(self.clauses("a.py", clean), [])

    def test_powershell_reading_without_an_encoding_is_caught(self):
        self.assertIn("CP-5", self.clauses("a.ps1", '$t = Get-Content -Raw -LiteralPath $p\n'))
        self.assertEqual(self.clauses("a.ps1", '$t = Get-Content -Raw -Encoding UTF8 -LiteralPath $p\n'), [])

    def test_a_ps1_with_non_ascii_and_no_bom_is_caught(self):
        self.assertIn("CP-5", self.clauses("a.ps1", "Write-Host 'тире —'\n".encode("utf-8"), binary=True))
        with_bom = b"\xef\xbb\xbf" + "Write-Host 'тире —'\n".encode("utf-8")
        self.assertEqual(self.clauses("a.ps1", with_bom, binary=True), [])

    # -- CP-6: a native command under a stop-on-error shell -------------------
    def test_a_bare_native_call_in_powershell_is_caught(self):
        self.assertIn("CP-6", self.clauses("a.ps1", '$u = (git -C $Dest remote get-url origin)\n'))

    def test_the_helper_and_an_existence_check_are_not_findings(self):
        clean = ('$u = (Git-Q -C $Dest remote get-url origin)\n'
                 'Invoke-Native gh auth status\n'
                 '$has = [bool](Get-Command git -ErrorAction SilentlyContinue)\n')
        self.assertEqual(self.clauses("a.ps1", clean), [])

    # -- CP-3: line endings ---------------------------------------------------
    def test_crlf_is_caught_in_any_shipped_text(self):
        self.assertIn("CP-3", self.clauses("a.sh", b"echo hi\r\n", binary=True))

    # -- prose is never code --------------------------------------------------
    def test_a_comment_describing_a_banned_construct_is_not_a_finding(self):
        self.assertEqual(self.clauses("a.sh", "# never use mapfile or readlink -f here\n"), [])
        self.assertEqual(self.clauses("a.py", "# open(path) without an encoding is wrong\n"), [])

    def test_a_docstring_describing_a_banned_construct_is_not_a_finding(self):
        body = '"""Why open(path) is wrong.\n\nAlso never mapfile.\n"""\nx = 1\n'
        self.assertEqual(self.clauses("a.py", body), [])

    def test_a_hash_inside_a_string_is_not_a_comment(self):
        # Blanking from the first `#` regardless of quotes would hide the rest of the line.
        self.assertIn("CP-2", self.clauses("a.sh", 'echo "a # b"; mapfile -t x < f\n'))

    def test_markdown_prose_is_never_matched_but_a_tagged_fence_is(self):
        prose = "Never use `mapfile` — it is bash 4.\n"
        self.assertEqual(self.clauses("a.md", prose), [])
        fenced = "Example:\n\n```bash\nmapfile -t x < f\n```\n"
        self.assertIn("CP-2", self.clauses("a.md", fenced))
        untagged = "Example:\n\n```\nmapfile -t x < f\n```\n"
        self.assertEqual(self.clauses("a.md", untagged), [])

    # -- the escape -----------------------------------------------------------
    def test_an_inline_escape_with_a_reason_suppresses_the_finding(self):
        self.assertEqual(self.clauses("a.sh", "mapfile -t x < f  # portability-ok: linux-only probe\n"), [])
        above = "# portability-ok: linux-only probe\nmapfile -t x < f\n"
        self.assertEqual(self.clauses("a.sh", above), [])

    def test_an_escape_without_a_reason_does_not_suppress(self):
        self.assertIn("CP-2", self.clauses("a.sh", "mapfile -t x < f  # portability-ok:\n"))

    # -- scope ----------------------------------------------------------------
    def test_the_fixtures_are_not_scanned(self):
        self.assertEqual(self.clauses("tools/tests/fixture.sh", "mapfile -t x < f\n"), [])

    def test_tier_one_is_everything_the_manifest_ships(self):
        shipped = set(portability.shipped_paths(KIT_ROOT))
        self.assertIn("rules/cross-platform.md", shipped)
        self.assertIn("install.ps1", shipped)
        # Every template is tier 1, INCLUDING one seeded inside a directory listed under
        # exclude:. update.py seeds them all regardless of exclude, so calling them the person's
        # space here would let one manifest mean two different things and ship them unchecked.
        for entry in manifest_lib.read_section("template", KIT_ROOT):
            self.assertIn(entry, shipped, "a seeded template is not tier 1: %s" % entry)
        # The person's own space, minus those seeds, stays out.
        seeds = set(manifest_lib.read_section("template", KIT_ROOT))
        for entry in manifest_lib.read_section("exclude", KIT_ROOT):
            stray = [p for p in shipped if manifest_lib.covers([entry], p) and p not in seeds]
            self.assertEqual(stray, [], "the person's space is tier 2: %s" % entry)

    def test_a_build_artifact_inside_a_shipped_directory_is_not_shipped(self):
        # shipped_paths globs the filesystem, so a __pycache__ or a stray .venv would otherwise
        # be counted as kit content and could fail somebody's gate on a file no update carries.
        self.assertEqual([p for p in portability.shipped_paths(KIT_ROOT)
                          if "__pycache__" in p or ".venv" in p], [])

    def test_whole_file_rules_run_on_every_shipped_path_whatever_its_suffix(self):
        # .gitattributes is the file that ENFORCES LF and had no LF check of its own.
        self.assertIn("CP-3", self.clauses(".gitattributes", b"*.sh text\r\n", binary=True))
        self.assertIn("CP-3", self.clauses("tools/x.js", b"const a = 1;\r\n", binary=True))

    def test_shipped_javascript_is_checked_for_a_path_from_one_machine(self):
        self.assertIn("CP-1", self.clauses("tools/x.mjs", 'const base = "/home/someone/base";\n'))

    # -- what a regex could not see ------------------------------------------
    def test_a_call_that_nests_or_spans_lines_is_still_seen(self):
        for body in ('f = open(os.path.join(root, name))\n',
                     'f = open(\n    path,\n    "w",\n)\n',
                     't = p.write_text(json.dumps(d))\n'):
            self.assertIn("CP-5", self.clauses("a.py", body), body)

    def test_a_clustered_or_long_form_flag_is_still_the_same_flag(self):
        for line in ("sed -E -i '' f", "sed -ie s/a/b/ f", "grep -Pq foo f", "readlink -fn x",
                     "declare -Ax m", "sed --in-place s/a/b/ f", "grep --perl-regexp x f",
                     "stat --format=%s f"):
            self.assertIn("CP-2", self.clauses("a.sh", line + "\n"), line)

    def test_a_native_call_reached_through_a_variable_or_splat_is_still_native(self):
        for line in ("git $Arguments", "git @gitArgs", "git.exe status"):
            self.assertIn("CP-6", self.clauses("a.ps1", line + "\n"), line)

    def test_a_helper_named_in_a_message_does_not_disarm_the_line_beside_it(self):
        body = 'Write-Host "see Get-Command docs"; git push\n'
        self.assertIn("CP-6", self.clauses("a.ps1", body))

    def test_a_powershell_message_naming_a_command_is_not_a_call(self):
        self.assertEqual(self.clauses("a.ps1", 'Write-Host "then run git push yourself"\n'), [])

    def test_a_hardcoded_windows_path_is_caught_and_a_regex_escape_is_not(self):
        self.assertIn("CP-1", self.clauses("a.ps1", '$d = "C:\\Users\\someone\\base"\n'))
        self.assertEqual(self.clauses("a.ps1", "$rx = [regex]'(?m)^- Language:.*$'\n"), [])
        self.assertEqual(self.clauses("a.sh", "printf 'imports it:\\n'\n"), [])

    def test_a_continued_line_is_read_as_one_command(self):
        self.assertEqual(self.clauses("a.ps1", '$t = Get-Content `\n  -Raw -Encoding UTF8 $p\n'), [])

    def test_a_one_line_docstring_and_a_help_constant_are_prose(self):
        for body in ('"""Why open(path) is wrong."""\nx = 1\n',
                     'HELP = """usage:\n  tool --root /home/someone/base\n  open(path)\n"""\n',
                     'r"""Matches /home/someone style paths."""\nx = 1\n'):
            self.assertEqual(self.clauses("a.py", body), [], body)

    def test_the_escape_has_to_be_a_comment(self):
        # An escape a string literal can trigger is the opposite of loud: it never reads as an
        # exemption to anyone reviewing the line.
        body = 'echo "portability-ok: data" ; mapfile -t x < f\n'
        self.assertIn("CP-2", self.clauses("a.sh", body))

    def test_a_wider_fence_and_a_nested_one_are_documents_not_code(self):
        wrapped = "````markdown\n```bash\nmapfile -t x < f\n```\n````\n"
        self.assertEqual(self.clauses("a.md", wrapped), [])
        quoted = "```text\n```bash\nmapfile -t x < f\n```\n"
        self.assertEqual(self.clauses("a.md", quoted), [])

    # -- the binding between a clause and what enforces it --------------------
    def test_a_gate_rule_citing_an_undefined_clause_fails_the_kit(self):
        """The direction the release gate had no test for.

        A rule table can invent an id, and the failure it prints then points at a contract nobody
        wrote — the person reading it has a regex and nothing to look up.
        """
        rules = portability.LINE_RULES
        invented = portability.Rule("CP-99", "shell", r"\bnothing\b", "invented", "nothing")
        portability.LINE_RULES = rules + (invented,)
        self.addCleanup(setattr, portability, "LINE_RULES", rules)
        self.assertIn("CP-99", portability.clauses())
        failures = []
        check_kit.check_clause_ids(KIT_ROOT, lambda m, w="": failures.append(m))
        self.assertTrue(any("CP-99" in m for m in failures), failures)

    def test_a_clause_nothing_enforces_fails_the_kit(self):
        """Enforcement drifting out from under a written clause is the silent half.

        The rule still reads as guarded, the release still passes, and the only evidence is a
        check that no longer exists.
        """
        rules = portability.LINE_RULES
        portability.LINE_RULES = tuple(r for r in rules if r.clause != "CP-6")
        self.addCleanup(setattr, portability, "LINE_RULES", rules)
        failures = []
        check_kit.check_clause_ids(KIT_ROOT, lambda m, w="": failures.append(m))
        self.assertTrue(any("CP-6" in m for m in failures), failures)

    def test_a_clause_the_tests_carry_instead_of_the_scanner_is_still_enforced(self):
        # Two mechanisms can hold a clause. [CP-4] — installer twins in lockstep — is not
        # expressible as a pattern over one file, so the test suite carries it, and the gate has
        # to count that as enforcement rather than demand a scanner rule for everything.
        self.assertNotIn("CP-4", portability.clauses())
        failures = []
        check_kit.check_clause_ids(KIT_ROOT, lambda m, w="": failures.append(m))
        self.assertEqual(failures, [])

    # -- release gates a content scanner cannot express ----------------------
    def test_retiring_a_file_from_inside_a_shipped_directory_is_allowed(self):
        """The case the section exists for, which the gate made impossible to satisfy.

        Without a `retired:` line it failed for the removal; with one it failed for coverage —
        from the same manifest state, so retiring anything out of `rules/` or `doctrine/` could
        not be shipped. The fear does not hold: `git checkout <ref> -- <dir>` writes what the ref
        has and never recreates a file the ref lacks.
        """
        failures = []
        check_kit.check_retired(KIT_ROOT, ["doctrine/"], [], ["knowledge/"],
                                ["doctrine/gone.md"], lambda m, w="": failures.append(m))
        self.assertEqual(failures, [],
                         "retiring from inside a shipped directory must be expressible")

    def test_a_path_that_is_both_shipped_on_its_own_and_retired_fails(self):
        failures = []
        check_kit.check_retired(KIT_ROOT, ["doctrine/gone.md"], [], [],
                                ["doctrine/gone.md"], lambda m, w="": failures.append(m))
        self.assertTrue(any("listed on its own" in m for m in failures), failures)

    def test_a_second_canon_list_is_caught_wherever_it_sits(self):
        """The check knew about one file; a second list is a second truth wherever it lives.

        `CLAUDE.md` is the likely place and was the only one watched. A list copied into a README
        or a doctrine page drifts exactly the same way, and the person goes on believing a rule
        applies.
        """
        for where in ("README.md", "doctrine/kit-ownership.md", "CLAUDE.md"):
            fake = Path(self.tmp.name) / where.replace("/", "_")
            shutil.copytree(KIT_ROOT, fake, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            target = fake / where
            target.write_text(target.read_text(encoding="utf-8")
                              + "\n@rules/safety.md\n@rules/grounding.md\n@rules/communication.md\n",
                              encoding="utf-8")
            failures = []
            check_kit.check_canon_listed_once(fake, lambda m, w="": failures.append(m))
            self.assertTrue(any("restates the canon list" in m for m in failures),
                            "a second list in %s was not caught: %s" % (where, failures))

    def test_the_gate_agrees_with_the_updater_about_an_empty_engine_section(self):
        """Two tools, one manifest, opposite verdicts is worse than either being wrong alone.

        `update.py` learned that `engine: []` is a legitimate base and the gate did not, so the
        base `/harness-doctor` runs the gate on was told its manifest was unsafe while the
        updater exited 0 on the same file.
        """
        import re as _re
        for body, expect_failure in ((("engine: []\n\n"), False), ("", True)):
            fake = Path(self.tmp.name) / ("declared" if not expect_failure else "missing")
            shutil.copytree(KIT_ROOT, fake, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            manifest = fake / ".engine-manifest.yml"
            text = _re.sub(r"^engine:\n(  - .*\n|  #.*\n|\n)*", body,
                           manifest.read_text(encoding="utf-8"), count=1, flags=_re.M)
            manifest.write_text(text, encoding="utf-8")
            failures = []
            engine = manifest_lib.read_section("engine", fake)
            if not engine and not manifest_lib.declares_section("engine", fake):
                failures.append("no engine: section")
            self.assertEqual(bool(failures), expect_failure,
                             "engine: %r declared=%s" % (body, not expect_failure))

    def test_the_manifests_own_version_is_a_third_mirror_and_is_held_to_it(self):
        # It drifted freely while the doctrine, the doctor's list and the manifest's own header
        # all promised it was checked against the other two.
        fake = Path(self.tmp.name) / "drifted"
        shutil.copytree(KIT_ROOT, fake, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        manifest = fake / ".engine-manifest.yml"
        manifest.write_text(manifest.read_text(encoding="utf-8")
                            .replace("version: 0.2.0", "version: 9.9.9", 1), encoding="utf-8")
        failures = []
        check_kit.check_versions(fake, lambda m, w="": failures.append(m))
        self.assertTrue(any("manifest says version" in m for m in failures), failures)

    def test_a_pointer_into_a_renamed_section_fails_the_kit(self):
        """The one defect `present-not-history` forbids that only eyes could catch.

        A citation from a remembered heading rots the first time a file is rewritten — and
        rewriting a rule whole is what that same rule requires — after which it points
        confidently at the wrong paragraph.
        """
        fake = Path(self.tmp.name) / "kit"
        shutil.copytree(KIT_ROOT, fake, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        target = fake / "rules/device-sync.md"
        target.write_text(
            target.read_text(encoding="utf-8").replace(
                "## Two questions decide your behaviour — not the name of the device",
                "## What decides your behaviour", 1), encoding="utf-8")
        failures = []
        check_kit.check_section_references(fake, lambda m, w="": failures.append(m))
        self.assertTrue(any("cites a section" in m for m in failures), failures)

    def test_a_pointer_at_a_missing_file_fails_the_kit(self):
        fake = Path(self.tmp.name) / "kit2"
        shutil.copytree(KIT_ROOT, fake, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        (fake / "ARCHITECTURE.md").write_text(
            'See `rules/nonexistent.md` -> "Some Heading".\n', encoding="utf-8")
        failures = []
        check_kit.check_section_references(fake, lambda m, w="": failures.append(m))
        self.assertTrue(any("does not exist" in m for m in failures), failures)

    def test_every_pointer_the_kit_ships_resolves_today(self):
        failures = []
        check_kit.check_section_references(KIT_ROOT, lambda m, w="": failures.append(m))
        self.assertEqual(failures, [])

    def test_a_path_listed_twice_in_one_section_fails_the_release(self):
        # Silent otherwise: the path count the update reports goes up, the work does not, and an
        # author adding an entry that is already there reads the higher number as it landing.
        failures = []
        check_kit.check_no_double_listing(["rules/", "README.md", "README.md"], [],
                                          lambda m, w="": failures.append(m))
        self.assertTrue(any("twice under engine" in m for m in failures), failures)
        clean = []
        check_kit.check_no_double_listing(
            list(manifest_lib.read_section("engine", KIT_ROOT)),
            list(manifest_lib.read_section("template", KIT_ROOT)),
            lambda m, w="": clean.append(m))
        self.assertEqual(clean, [])

    def test_a_fork_that_kept_the_upstream_address_fails_the_release(self):
        """Fork the kit, forget `kit_remote:`, and every base you set up goes upstream.

        Each update reconciles a base's kit remote to whatever the manifest declares — the same
        mechanism that makes moving the kit possible — so the omission is silent and permanent
        after one line of output nobody reads twice.
        """
        fork = Path(self.tmp.name) / "fork"
        shutil.copytree(KIT_ROOT, fork, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        subprocess.run(["git", "-C", str(fork), "init", "-q", "-b", "main"], check=True)
        subprocess.run(["git", "-C", str(fork), "remote", "add", "origin",
                        "https://github.com/someone/their-fork"], check=True)
        failures = []
        check_kit.check_kit_remote_is_this_repository(fork, lambda m, w="": failures.append(m))
        self.assertTrue(any("kit_remote:" in m for m in failures), failures)
        # The kit itself declares its own address, so it passes.
        clean = []
        check_kit.check_kit_remote_is_this_repository(KIT_ROOT, lambda m, w="": clean.append(m))
        self.assertEqual(clean, [])

    def test_a_shipped_tool_missing_from_the_catalogue_fails_the_release(self):
        failures = []
        engine = list(manifest_lib.read_section("engine", KIT_ROOT)) + ["tools/nowhere.py"]
        check_kit.check_kit_tools_are_catalogued(KIT_ROOT, engine,
                                                 lambda m, w="": failures.append(m))
        self.assertTrue(any("nowhere.py" in m for m in failures), failures)
        # And the kit as it stands catalogues everything it ships.
        clean = []
        check_kit.check_kit_tools_are_catalogued(
            KIT_ROOT, list(manifest_lib.read_section("engine", KIT_ROOT)),
            lambda m, w="": clean.append(m))
        self.assertEqual(clean, [])

    def test_a_shell_tool_with_no_twin_fails_the_release(self):
        """[CP-4] The fault a content scanner cannot see.

        Portable bash is still bash: PowerShell cannot run it, and reading the file will never
        say so — check_portability.py would report it clean.
        """
        failures = []
        check_kit.check_kit_tools_run_everywhere(
            KIT_ROOT, ["tools/helper.sh"], lambda m, w="": failures.append(m))
        self.assertTrue(any("helper.sh" in m for m in failures), failures)
        paired = []
        check_kit.check_kit_tools_run_everywhere(
            KIT_ROOT, ["tools/helper.sh", "tools/helper.ps1"],
            lambda m, w="": paired.append(m))
        self.assertEqual(paired, [])

    def test_the_kit_it_ships_today_is_clean(self):
        self.assertEqual([str(f) for f in portability.scan(KIT_ROOT)], [])


# PowerShell variables that exist without anyone assigning them: automatic variables, and the
# scope prefixes that look like one ($script:Root).
POWERSHELL_AUTOMATIC = frozenset({
    "true", "false", "null", "_", "psitem", "args", "input", "home", "pwd", "pid", "host",
    "error", "matches", "lastexitcode", "myinvocation", "psscriptroot", "pscommandpath",
    "psversiontable", "erroractionpreference", "outputencoding", "profile", "foreach",
    "executioncontext", "script", "global", "local",
})


class WindowsInstallerTests(unittest.TestCase):
    """Static checks on install.ps1 — no PowerShell here, so these guard what a read can prove.

    Each one stands for a failure that cannot be caught any other way in this environment, and
    each was a real defect before it was a test.
    """

    def setUp(self):
        self.path = KIT_ROOT / "install.ps1"
        self.raw = self.path.read_bytes()
        self.text = self.raw.decode("utf-8-sig")

    def test_it_carries_a_utf8_bom(self):
        # Windows PowerShell 5.1 decodes a BOM-less .ps1 through the system ANSI code page, so
        # the script's own em dashes become mojibake — including the one inside a negated
        # character class, which then stops excluding what it was written to exclude.
        self.assertTrue(self.raw.startswith(b"\xef\xbb\xbf"))

    def test_every_file_read_declares_utf8(self):
        # Without -Encoding, 5.1 reads through the ANSI code page and a read-modify-write cycle
        # permanently corrupts the person's profile.md.
        self.assertNotIn("Get-Content -Raw -LiteralPath", self.text)
        self.assertNotIn("Get-Content -Raw -Path", self.text)

    def test_no_native_command_runs_outside_the_helper(self):
        # git and gh write ordinary progress to stderr; under $ErrorActionPreference = 'Stop'
        # that aborts the installer on a perfectly healthy machine.
        offenders = [
            line.strip() for line in self.text.splitlines()
            if re.search(r"(^|[ (\t])(git|gh) ", line)
            and "Git-Q" not in line and "Invoke-Native" not in line
            and "Get-Command" not in line and not line.strip().startswith("#")
        ]
        self.assertEqual(offenders, [])

    def test_it_refuses_a_non_interactive_run_like_bash_does(self):
        # The gate has to be CALLED, not merely defined. Asserting the name appears is satisfied
        # by the function header alone — and a deleted call site is how this stopped working once.
        calls = [line.strip() for line in self.text.splitlines()
                 if line.strip() == "Require-Answers"]
        self.assertEqual(len(calls), 1, "install.ps1 defines Require-Answers but never calls it")
        self.assertIn("HARNESS_ANSWERS_ON_STDIN", self.text)
        shell = (KIT_ROOT / "install.sh").read_text(encoding="utf-8")
        self.assertIn("HARNESS_ANSWERS_ON_STDIN", shell)
        self.assertTrue(re.search(r"^require_answers\s*$", shell, re.M),
                        "install.sh defines require_answers but never calls it")

    def test_every_variable_it_reads_is_one_it_set(self):
        """A deletion that overshoots is invisible until a stranger's machine runs the script.

        bash has `set -u` and stops on the spot; PowerShell substitutes $null and carries on, so
        an over-wide edit surfaces as `You cannot call a method on a null-valued expression`
        several steps later — on Windows, where nobody here can see it. This is that check.
        """
        code = "\n".join(line for line in self.text.splitlines()
                          if not line.strip().startswith("#"))
        bound = {m.lower() for m in re.findall(r"\$([A-Za-z_]\w*)\s*(?:=|\+=)", code)}
        bound |= {m.lower() for m in
                  re.findall(r"foreach\s*\(\s*\$([A-Za-z_]\w*)\s+in\b", code, re.I)}
        for params in re.findall(r"^\s*(?:function\s+[\w-]+\s*|param\s*)\(([^)]*)\)",
                                 code, re.M | re.I):
            bound |= {m.lower() for m in re.findall(r"\$([A-Za-z_]\w*)", params)}
        used = {m.lower() for m in re.findall(r"\$(?!env:)([A-Za-z_]\w*)", code)}
        self.assertEqual(sorted(used - bound - POWERSHELL_AUTOMATIC), [])

    def test_it_finds_the_kit_remote_the_way_the_manifest_declares_it(self):
        """[CP-4] the twins must agree on WHICH remote is the kit's, not just that one exists.

        Matching the name as a substring calls the person's own base `harness-kit` — the very
        name this installer suggests for it — and rewrites their `origin`, after which nothing
        can save their work anywhere.
        """
        self.assertTrue("kit_remote" in (KIT_ROOT / "install.sh").read_text(encoding="utf-8"),
                        "install.sh no longer reads kit_remote from the manifest")
        self.assertTrue("kit_remote" in self.text,
                        "install.ps1 does not read kit_remote from the manifest")
        self.assertTrue("-match 'harness-kit'" not in self.text,
                        "install.ps1 identifies the kit remote by name, not by address")

    def test_line_endings_are_lf(self):
        # .gitattributes forces LF; a CRLF checkout of the bash twin breaks bash outright, and
        # the two files are meant to stay byte-comparable in this respect.
        self.assertNotIn(b"\r\n", self.raw)

    def test_both_installers_ask_the_same_questions(self):
        """[CP-4] a mechanism with a platform twin moves in lockstep."""
        shell = (KIT_ROOT / "install.sh").read_text(encoding="utf-8")
        for question in ("Where should your base live?", "What should the base folder be called?",
                         "What language should the agent talk to you in?", "Do you use Claude Code?",
                         "Move it inside the base?", "Set that up now?", "Your name", "Your email"):
            self.assertIn(question, shell, "install.sh lost: %s" % question)
            self.assertIn(question, self.text, "install.ps1 lost: %s" % question)

    def test_both_doctors_check_the_same_things(self):
        shell = (KIT_ROOT / "install.sh").read_text(encoding="utf-8")
        in_shell = set(re.findall(r'check "([^"]*)"', shell)) - {"label"}
        in_windows = set(re.findall(r'Check "([^"]*)"', self.text))
        # The one allowed asymmetry: bash hard-requires python3 at the top instead of checking.
        in_windows.discard("python3 available (needed to catch up automatically)")
        self.assertEqual(in_shell, in_windows)


class ShippedKitTests(unittest.TestCase):
    """The kit in this working tree is coherent — the same gate a release runs."""

    def test_structural_gate_passes(self):
        done = subprocess.run(
            [sys.executable, str(KIT_ROOT / "tools" / "check_kit.py")],
            capture_output=True, text=True, cwd=str(KIT_ROOT),
        )
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_every_rule_is_listed_once_in_the_one_contract(self):
        rules = sorted(p.name for p in (KIT_ROOT / "rules").glob("*.md"))
        contract = (KIT_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        bridge = (KIT_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        for name in rules:
            self.assertIn(name, contract, "%s is silently not in force" % name)
            self.assertNotIn("@rules/%s" % name, bridge, "the canon list must exist once")

    def test_the_canon_list_tells_the_agent_to_repair_it(self):
        # The list is the one place the canon can be got wrong, and on a person's base nobody runs
        # the release gate. So the instruction itself has to close the hole: a rule on disk that
        # the list omits still binds, and the session that notices repairs it.
        contract = (KIT_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("not named above is a rule the list has LOST", contract)
        # And that adopting one is a decision, not a step: a file that simply appeared in
        # `rules/` is a claim on every future session that nobody made.
        self.assertIn("Confirm before you adopt one", contract)
        self.assertIn("index", contract)

    def test_safety_and_git_safety_do_not_restate_each_other(self):
        # Two rules over one subject drift. git-safety owns git; safety owns everything else and
        # each names the other rather than repeating it.
        git_rule = (KIT_ROOT / "rules" / "git-safety.md").read_text(encoding="utf-8")
        safety = (KIT_ROOT / "rules" / "safety.md").read_text(encoding="utf-8")
        self.assertIn("rules/safety.md", git_rule)
        self.assertIn("rules/git-safety.md", safety)
        self.assertNotIn("--force", safety, "the force list has one home, and it is git-safety")

    def test_declared_paths_exist(self):
        for entry in manifest_lib.read_section("engine", KIT_ROOT):
            self.assertTrue((KIT_ROOT / entry.rstrip("/")).exists(), entry)
        for entry in manifest_lib.read_section("template", KIT_ROOT):
            self.assertTrue((KIT_ROOT / entry).exists(), entry)


if __name__ == "__main__":
    unittest.main()
