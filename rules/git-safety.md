# Git Safety (HARD RULE)

Any project, any session. Destructiveness that is not git's — deletions, external systems, acting
outside the base, the scope of an approval — lives in `rules/safety.md`; this file is the git half
and does not repeat it.

## `--force` / `-f` forbidden without explicit approval

- **ANY git operation with `--force` / `-f` / `--hard` requires the person's EXPLICIT
  in-the-moment approval.** Covered: `push --force`(`-with-lease`), `worktree remove --force`,
  `clean -f`/`-fd`, `checkout --force`/`-f`, `reset --hard` (on uncommitted work), `branch -D` with
  loss of unmerged work, and any other `--force` flag.
- **Why:** `--force` disables git's protection → **silent, irreversible data loss** (uncommitted
  WIP, unmerged branches) — exactly what git normally won't let you erase.
## Discarding uncommitted work needs the same approval as `--force`

`git checkout -- <path>`, `git restore <path>` and `git stash drop` carry no scary flag and are
not refused by git, yet they destroy uncommitted work exactly as irreversibly as `--hard` does —
which is what makes them worse: nothing announces the loss, and the file simply reads as it did
before the work existed. Treat them as the force list above: the person's explicit approval in the
moment, or a commit first.

**Breaking something on purpose — a mutation check, a "does this test actually fail" experiment —
is committed BEFORE it is broken, never reverted afterwards.** Reverting is the moment the
unrelated work sitting beside it disappears.

- **The default is NON-force.** Run the plain variant. Git refused because something is protected (a
  dirty worktree, an unmerged branch) — that is a STOP signal, not an obstacle to bypass: show the
  person the reason (e.g. `git status` of the target), decide together.

## Saving work — the base is proposed, a code repository is asked

- After every file create / edit / delete → `git add` the affected paths, and verify with
  `git status --short`.
- **In the person's base** (the harness repo itself, `projects/` included): saving is proactive.
  You propose it in one plain sentence, and after their first yes you keep saving silently for the
  rest of the session; with nobody in the loop you save on your own. The base has one branch and no
  others. Full contract: `rules/device-sync.md`.
- **In a repository of code** (a project that was moved to its own repo, someone else's repo):
  commit and push only when asked, and never work directly on the default branch for a non-trivial
  change — branch first.
- All file deletions are confirmed with the person before running.

## Commits

- Format: a short imperative-mood subject. Explain WHY, not WHAT.
- Language: English only — commit messages, PR titles / descriptions, code comments.
- No assistant-authorship marks (rules/communication.md).
