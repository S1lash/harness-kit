# Git Safety (HARD RULE)

Any project, any session.

## `--force` / `-f` forbidden without explicit approval

- **ANY git operation with `--force` / `-f` / `--hard` requires the person's EXPLICIT
  in-the-moment approval.** Covered: `push --force`(`-with-lease`), `worktree remove --force`,
  `clean -f`/`-fd`, `checkout --force`/`-f`, `reset --hard` (on uncommitted work), `branch -D` with
  loss of unmerged work, and any other `--force` flag.
- **Why:** `--force` disables git's protection → **silent, irreversible data loss** (uncommitted
  WIP, unmerged branches) — exactly what git normally won't let you erase.
- **The default is NON-force.** Run the plain variant. Git refused because something is protected (a
  dirty worktree, an unmerged branch) — that is a STOP signal, not an obstacle to bypass: show the
  person the reason (e.g. `git status` of the target), decide together.

## Stage changes, commit only when asked

- After every file create / edit / delete → `git add` the affected paths. As the last step of any
  task touching files, run `git add <paths>` and verify with `git status --short`.
- Add new files to tracking, but **do not commit or push unless the person asks**.
- Never work directly on the default branch for a non-trivial change — branch first.
- All file deletions are confirmed with the person before running.

## Commits

- Format: a short imperative-mood subject. Explain WHY, not WHAT.
- Language: English only — commit messages, PR titles / descriptions, code comments.
- No assistant-authorship marks (rules/communication.md).
