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

    def test_a_seed_added_after_their_clone_still_reaches_them(self):
        # The gap this closes: templates never sync, so a seed introduced after somebody cloned
        # reached them never — while the canon arriving in the same update named it as if it
        # were there. Absent is created; present is left exactly alone.
        (self.base / "seed.md").unlink()
        done = run_update(self.base)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual((self.base / "seed.md").read_text(), "pristine seed\n")
        self.assertIn("a seed this base never received", done.stdout)

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

    def test_status_on_a_clean_base_asks_for_nothing(self):
        done = self.run_sync("status")
        self.assertIn("unsaved here: none", done.stdout)

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
        source = (KIT_ROOT / "tools" / "sync.py").read_text(encoding="utf-8")
        # Look for them as passed ARGUMENTS, not as words: the file explains in prose that it
        # never rebases, and a prose ban must not read as a violation of itself.
        for banned in ('"--force"', '"-f"', '"--hard"', '"rebase"', '"--force-with-lease"'):
            self.assertNotIn(banned, source,
                             "%s disables the protection that makes divergence recoverable" % banned)

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

    def test_a_base_whose_manifest_is_unreadable_refuses_rather_than_doing_nothing(self):
        done = run_update(self.base)
        self.assertEqual(done.returncode, 2)
        self.assertIn("no kit paths", done.stderr)
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
        self.assertIn("Require-Answers", self.text)
        self.assertIn("HARNESS_ANSWERS_ON_STDIN", self.text)
        self.assertIn("HARNESS_ANSWERS_ON_STDIN", (KIT_ROOT / "install.sh").read_text(encoding="utf-8"))

    def test_line_endings_are_lf(self):
        # .gitattributes forces LF; a CRLF checkout of the bash twin breaks bash outright, and
        # the two files are meant to stay byte-comparable in this respect.
        self.assertNotIn(b"\r\n", self.raw)

    def test_both_installers_ask_the_same_questions(self):
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

    def test_declared_paths_exist(self):
        for entry in manifest_lib.read_section("engine", KIT_ROOT):
            self.assertTrue((KIT_ROOT / entry.rstrip("/")).exists(), entry)
        for entry in manifest_lib.read_section("template", KIT_ROOT):
            self.assertTrue((KIT_ROOT / entry).exists(), entry)


if __name__ == "__main__":
    unittest.main()
