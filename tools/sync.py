#!/usr/bin/env python3
"""Keep the base in step across every surface it is opened from.

Mechanics only: report the state of the base and take the SAFE action for that state.
Judgement — whether to ask the person, and how to say it to them — lives in
rules/device-sync.md. This script never forces, never rebases, and never discards a side.

Modes
  session-start   Safe sync-in for a session opening: fast-forward only when the copy is
                  clean and strictly behind. Prints the state and the required next action;
                  always exits 0 so a session never fails to start because of it.
  status          Print the state. Changes nothing.
  pull            Explicit sync-in, including a merge when both sides moved.
  save "<why>"    Stage everything, record it, sync, and send it out.
"""

import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
NETWORK_TIMEOUT_SECONDS = 90
UNSAVED_SAMPLE_SIZE = 8
PREFIX = "[harness-sync]"


class GitError(Exception):
    """A git invocation that the caller is expected to report, not swallow."""


def git(*args, timeout=None):
    """Run git in the base. Returns (returncode, stdout, stderr), all stripped."""
    try:
        done = subprocess.run(
            ["git", "-C", str(BASE)] + list(args),
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 124, "", "timed out after %ss" % timeout
    except FileNotFoundError:
        raise GitError("git is not installed on this machine")
    # stdout keeps its leading whitespace: porcelain status encodes state in columns 1-2.
    return done.returncode, done.stdout.rstrip("\n"), done.stderr.strip()


def git_ok(*args, timeout=None):
    code, out, _ = git(*args, timeout=timeout)
    return out if code == 0 else None


def remote_is_public(url):
    """True only when a check actually came back saying public.

    Unknown is not private. `gh` may be absent or signed out, and a base whose visibility cannot
    be established is reported as unchecked rather than assumed safe — asserting "private" on the
    evidence that a URL exists is what let a fork of a public repository read as fine.
    """
    try:
        probe = subprocess.run(
            ["gh", "repo", "view", url, "--json", "visibility", "-q", ".visibility"],
            capture_output=True, text=True, timeout=NETWORK_TIMEOUT_SECONDS)
    except (OSError, subprocess.SubprocessError):
        return False
    return probe.returncode == 0 and probe.stdout.strip().lower() == "public"


def read_state():
    """Everything the caller needs to decide, gathered in one place."""
    state = {
        "base": str(BASE),
        "is_repo": git_ok("rev-parse", "--is-inside-work-tree") == "true",
        "enclosing": None,
        "nested_repos": [],
        "remote_public": False,
        "untracked_branch": None,
        "branch": None,
        "remote_url": None,
        "upstream": None,
        "unsaved": [],
        "ahead": 0,
        "behind": 0,
        "offline": False,
        "identity": True,
        "detached": False,
        "branches": 1,
        "unreadable": None,
    }
    if not state["is_repo"]:
        return state

    # Being INSIDE a repository is not the same as BEING one. A base with no `.git` of its own,
    # sitting anywhere under another repository, makes git walk up and answer for that one — so
    # every command here operates on somebody else's repository, and `save` stages and pushes its
    # entire worktree. Nothing in the output would say so on its own: the base path printed is
    # the one the person expects.
    toplevel = git_ok("rev-parse", "--show-toplevel")
    if toplevel and Path(toplevel).resolve() != BASE.resolve():
        state["enclosing"] = toplevel
        return state

    branch = git_ok("rev-parse", "--abbrev-ref", "HEAD")
    state["detached"] = branch == "HEAD"
    state["branch"] = None if state["detached"] else branch
    state["remote_url"] = git_ok("remote", "get-url", "origin")
    state["upstream"] = git_ok("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    state["identity"] = bool(git_ok("config", "user.email")) and bool(git_ok("config", "user.name"))

    listing = git_ok("for-each-ref", "--format=%(refname:short)", "refs/heads/") or ""
    state["branches"] = len([line for line in listing.splitlines() if line.strip()])

    code, porcelain, err = git("status", "--porcelain")
    if code != 0:
        # A failed `status` used to read as a CLEAN base: `git_ok` returns None for both, and
        # `or ""` then made "cannot tell" indistinguishable from "nothing to save". The
        # session-start path would go on to fast-forward on that reading.
        state["unreadable"] = err.strip() or "git could not read this base"
        return state
    state["unsaved"] = [line[3:] for line in porcelain.splitlines() if line]

    # A project that is its own repository is committed as a gitlink: the base records a commit
    # id and none of the content, so a clone — the phone — gets an empty directory. Nothing about
    # the save says so, which is exactly the silent divergence this whole rule exists to prevent.
    # "Private" was asserted once, at creation, and never checked again. A base whose remote was
    # already configured, or one whose repository is a fork of a public one (a fork is always
    # public), pushes the person's whole life somewhere anyone can read — while every check in
    # the kit reports a private place online, on the sole evidence that a URL exists.
    if state["remote_url"]:
        state["remote_public"] = remote_is_public(state["remote_url"])

    projects = BASE / "projects"
    if projects.is_dir():
        state["nested_repos"] = sorted(
            "projects/%s" % child.name for child in projects.iterdir()
            if child.is_dir() and (child / ".git").exists())
    return state


def refresh_remote_counts(state):
    """Fetch, then fill in how far apart the two sides are. Offline is a state, not a failure."""
    if not state["remote_url"]:
        return
    code, _, _ = git("fetch", "--quiet", "origin", timeout=NETWORK_TIMEOUT_SECONDS)
    if code != 0:
        state["offline"] = True
        return
    state["upstream"] = git_ok("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    # A branch with no tracking configured used to leave both counters at zero, so `status`,
    # `session-start` and `pull` all reported "in step" while the remote was genuinely ahead —
    # and a read-only session never self-corrects, because nothing pushes to be refused. The
    # same-named remote branch answers the question perfectly well.
    reference = state["upstream"]
    if not reference and state["branch"]:
        candidate = "origin/%s" % state["branch"]
        if git_ok("rev-parse", "--verify", "--quiet", candidate):
            reference = candidate
            state["untracked_branch"] = candidate
    if not reference:
        return
    counts = git_ok("rev-list", "--left-right", "--count", "%s...HEAD" % reference)
    if counts:
        behind, ahead = counts.split()
        state["behind"], state["ahead"] = int(behind), int(ahead)


def describe(state, action_taken, directive):
    lines = ["%s base: %s" % (PREFIX, state["base"])]
    if not state["is_repo"]:
        lines.append("state: this folder is not tracked at all — nothing can travel between surfaces")
        lines.append("YOU MUST: %s" % directive)
        return "\n".join(lines)

    if state["unreadable"]:
        lines.append("state: UNREADABLE — git could not report on this base")
        lines.append("       %s" % state["unreadable"])
        lines.append("YOU MUST: %s" % directive)
        return "\n".join(lines)

    if state["enclosing"]:
        lines.append("state: NOT ITS OWN — this base has no history of its own and sits inside")
        lines.append("       %s" % state["enclosing"])
        lines.append("       Saving here would write into that project and send it wherever it goes.")
        lines.append("YOU MUST: %s" % directive)
        return "\n".join(lines)

    lines.append("branch: %s" % (state["branch"] or "DETACHED — not on a branch"))
    if state["remote_url"]:
        lines.append("remote: %s" % state["remote_url"])
    else:
        lines.append("remote: NONE — this base exists on this machine only")

    if state["unsaved"]:
        sample = ", ".join(state["unsaved"][:UNSAVED_SAMPLE_SIZE])
        more = "" if len(state["unsaved"]) <= UNSAVED_SAMPLE_SIZE else ", +%d more" % (
            len(state["unsaved"]) - UNSAVED_SAMPLE_SIZE)
        lines.append("unsaved here: %d (%s%s)" % (len(state["unsaved"]), sample, more))
    else:
        lines.append("unsaved here: none")

    if state["offline"]:
        lines.append("sync: could not reach the remote (offline or no access)")
    elif not state["upstream"] and not state["untracked_branch"]:
        lines.append("sync: this branch is not linked to the remote yet")
    elif state["ahead"] and state["behind"]:
        lines.append("sync: both sides moved (%d here, %d elsewhere)" % (state["ahead"], state["behind"]))
    elif state["behind"]:
        lines.append("sync: %d change(s) elsewhere are not here yet" % state["behind"])
    elif state["ahead"]:
        lines.append("sync: %d change(s) here have not gone out yet" % state["ahead"])
    else:
        lines.append("sync: in step with the remote")

    if state["untracked_branch"]:
        lines.append("note: this branch is not linked to the remote, so the comparison is "
                     "against %s" % state["untracked_branch"])
    if state["remote_public"]:
        lines.append("       ^ PUBLIC — anyone can read everything saved here")
    if state["nested_repos"]:
        lines.append("projects kept separately: %s" % ", ".join(state["nested_repos"]))
        lines.append("       their contents do NOT travel with this base — a clone gets an "
                     "empty folder")
    if state["branches"] > 1:
        lines.append("branches: %d — a base has one; the extra ones are invisible on a phone"
                     % state["branches"])
    if not state["identity"]:
        lines.append("identity: git has no name/email set — saving will fail until it does")
    if action_taken:
        lines.append("action taken: %s" % action_taken)
    lines.append("YOU MUST: %s" % directive)
    return "\n".join(lines)


def directive_for(state):
    """The next action rules/device-sync.md requires for this state."""
    if not state["is_repo"]:
        return ("tell the person their base is not being kept anywhere and offer to set that up "
                "(plain language — no git words)")
    if state["unreadable"]:
        return ("STOP — do not save or pull. git cannot read this base, so nothing here can be "
                "trusted, and an empty answer would read as 'nothing to save'. Show the person "
                "the reason above in their words and fix it before anything else")
    if state["enclosing"]:
        return ("STOP — do not save. This base has no history of its own and sits inside another "
                "project's, so everything here would be saved into THAT project and sent wherever "
                "it goes. Tell the person their base was never set up as its own thing, in their "
                "words, and set it up before saving anything")
    if state["detached"]:
        return "put the base back on its single branch before doing anything else"
    if not state["remote_url"]:
        return ("tell the person their base lives only on this machine, so their phone and other "
                "computers cannot see any of it, and offer to fix that")
    if not state["identity"]:
        return "ask the person for the name and email to save under, then set them for this base"
    if state["untracked_branch"] and (state["ahead"] or state["behind"]):
        return ("the base is out of step AND this branch is not linked to the remote, so nothing "
                "will notice on its own next time. Link it (git branch --set-upstream-to=%s), "
                "then run 'pull' — and say to the person only what changed, never the mechanics"
                % state["untracked_branch"])
    if state["unsaved"] and state["behind"]:
        return ("do NOT pull. Say what is unsaved here, propose saving it first, then bring the "
                "rest in")
    if state["ahead"] and state["behind"]:
        return "run 'pull' to put both sides together, resolve anything overlapping by reading it"
    if state["behind"]:
        return "run 'pull' to bring the base up to date, then say nothing about it"
    if state["remote_public"]:
        return ("STOP — do not save. The one place this base lives online is PUBLIC, so "
                "everything in it is readable by anyone. Tell the person plainly, in their "
                "words, and make it private before anything else is sent out")
    if state["nested_repos"]:
        return ("save as normal, then tell the person once, in their words, that what is inside "
                "%s is kept on its own and does not travel with the base — so it will not be on "
                "their phone. Offer to set that up separately"
                % ", ".join(state["nested_repos"]))
    if state["unsaved"] or state["ahead"]:
        return ("propose saving at the end of this chunk of work — earlier if this copy will not "
                "survive the session")
    return "nothing — the base is in step; say nothing about it"


def mode_status(mutate_when_safe):
    state = read_state()
    if not state["is_repo"]:
        print(describe(state, None, directive_for(state)))
        return 0
    refresh_remote_counts(state)

    action = None
    if (mutate_when_safe and not state["unsaved"] and state["behind"] and not state["ahead"]
            and state["upstream"] and not state["offline"]):
        code, _, err = git("merge", "--ff-only", "@{u}", timeout=NETWORK_TIMEOUT_SECONDS)
        if code == 0:
            action = "brought the base up to date (%d change(s))" % state["behind"]
            state["behind"] = 0
        else:
            action = "could not bring the base up to date: %s" % err
    print(describe(state, action, directive_for(state)))
    return 0


def mode_pull():
    state = read_state()
    if state["unreadable"] or state["enclosing"] or not state["is_repo"] or not state["remote_url"]:
        print(describe(state, None, directive_for(state)))
        return 1
    if state["unsaved"]:
        print(describe(state, None,
                       "do NOT pull — there is unsaved work here. Propose saving it first."))
        return 1

    refresh_remote_counts(state)
    if state["offline"]:
        print(describe(state, None, "tell the person you could not reach their saved copy right now"))
        return 1
    if not state["behind"]:
        print(describe(state, "nothing to bring in", directive_for(state)))
        return 0

    # `--no-rebase` is a `git pull` flag, not a `git merge` one: passing it here made git print
    # its usage and fail, so putting two sides together never worked at all.
    code, _, err = git("merge", "--no-edit", "@{u}", timeout=NETWORK_TIMEOUT_SECONDS)
    if code != 0:
        if "unrelated histories" in err:
            # Not a conflict between two versions of one thing — two different bases pointed at
            # one place. Merging them would union somebody's real base with a blank one, so it
            # is refused and named instead.
            print("%s this machine holds a DIFFERENT base from the one saved online — they share "
                  "no history at all." % PREFIX)
            print("YOU MUST: tell the person, in their words, that this computer was set up as a "
                  "new base rather than as a copy of theirs, so the two are not the same thing. "
                  "Offer to start this machine again from their saved one. Never merge them "
                  "blindly and never force.")
            return 1
        conflicts = git_ok("diff", "--name-only", "--diff-filter=U") or err
        print("%s overlapping changes in:\n%s" % (PREFIX, conflicts))
        print("YOU MUST: resolve these by reading what they mean, then save. Never discard a side, "
              "never force.")
        return 1

    state = read_state()
    refresh_remote_counts(state)
    print(describe(state, "put both sides together", directive_for(state)))
    return 0


def push_refusal_directive(err):
    """A refusal the person cannot read is worse than none — translate the known ones."""
    text = err.lower()
    if "gh007" in text or "private email address" in text:
        return ("their work is safe here but was turned away because the address it is stamped "
                "with is private. Offer to stamp saves with the hidden address their account "
                "provides instead — '<username>@users.noreply.github.com' — set it for this base, "
                "and try again. Do not make them go and change a setting.")
    if "authentication" in text or "could not read username" in text or "403" in text:
        return ("their work is safe here but the private place online would not accept it, "
                "because this machine is not signed in to it. Say that plainly and offer to set "
                "the sign-in up.")
    if "non-fast-forward" in text or "fetch first" in text or "rejected" in text:
        return ("something arrived from another device between reading and sending. Bring it in "
                "and send again — never force.")
    return ("tell the person their work is safe on this machine but has not reached their other "
            "devices, and why, in their words")


def mode_save(message):
    state = read_state()
    # Refuse before anything is staged: `git add -A` here would stage the enclosing repository's
    # whole worktree, and the push that follows would send it wherever that repository goes.
    if (state["unreadable"] or state["enclosing"] or state["remote_public"]
            or not state["is_repo"]):
        print(describe(state, None, directive_for(state)))
        return 1
    if not state["identity"]:
        print(describe(state, None, directive_for(state)))
        return 1

    if state["unsaved"]:
        code, _, err = git("add", "-A")
        if code != 0:
            print("%s could not stage: %s" % (PREFIX, err))
            return 1
        staged = git_ok("diff", "--cached", "--name-only") or ""
        count = len([line for line in staged.splitlines() if line])
        code, _, err = git("commit", "-m", message)
        if code != 0:
            print("%s could not record the change: %s" % (PREFIX, err))
            return 1
        print("%s recorded %d file(s)" % (PREFIX, count))

    if not state["remote_url"]:
        print(describe(read_state(), "recorded on this machine", directive_for(read_state())))
        return 0

    state = read_state()
    refresh_remote_counts(state)
    if state["offline"]:
        print(describe(state, "recorded on this machine; could not send it out",
                       "tell the person it is safe here but has not reached their other devices yet"))
        return 1
    if state["behind"] and mode_pull() != 0:
        return 1

    args = ["push"]
    if not read_state()["upstream"]:
        branch = read_state()["branch"]
        args += ["--set-upstream", "origin", branch]
    code, _, err = git(*args, timeout=NETWORK_TIMEOUT_SECONDS)
    if code != 0:
        print("%s could not send it out: %s" % (PREFIX, err))
        print("YOU MUST: %s" % push_refusal_directive(err))
        return 1

    final = read_state()
    print(describe(final, "saved and sent out", "say one short line that it is saved — nothing more"))
    return 0


def main(argv):
    mode = argv[1] if len(argv) > 1 else "status"
    try:
        if mode == "session-start":
            return mode_status(mutate_when_safe=True)
        if mode == "status":
            return mode_status(mutate_when_safe=False)
        if mode == "pull":
            return mode_pull()
        if mode == "save":
            if len(argv) < 3 or not argv[2].strip():
                print("%s save needs a message saying WHY this change exists" % PREFIX)
                return 2
            return mode_save(argv[2])
    except GitError as exc:
        print("%s %s" % (PREFIX, exc))
        return 0 if mode == "session-start" else 1

    print(__doc__)
    return 2


if __name__ == "__main__":
    code = main(sys.argv)
    # A session must never fail to open because of this script.
    sys.exit(0 if sys.argv[1:2] == ["session-start"] else code)
