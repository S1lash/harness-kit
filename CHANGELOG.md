# Changelog

The sanctioned history home for this repo (the one place `present-not-history` allows a record of
change — like `knowledge/decisions.md` for decisions). The canon itself always describes the
present; evolution is logged here.

## 2026-08-10

Two silent-divergence holes, surfaced while wiring this base onto a machine that runs two agents
side by side:

- Add `rules/multi-agent.md` (hot canon): the base is the shared memory across agent runtimes and
  an agent's private store is scratch, never a home; a canon change reaches every wired agent in
  the same edit; capabilities differ between runtimes, canon does not. Nothing previously said that
  a durable fact left in a runtime's own memory is invisible to the other runtimes — and, in Claude
  Code, to every other folder.
- `rules/self-learning.md`: route away from the runtime's own memory store explicitly, by link to
  the rule above.
- `commands/doctor.md` + `install.sh` health check: verify canon parity — every file in `rules/` is
  named in both hand-maintained lists (`CLAUDE.md`, `AGENTS.md`). A rule listed for one agent and
  missing for another was previously undetectable, and reads as in-force when it is not.

## 2026-07-16

Fixes surfaced while building a personal harness on this canon:

- Add root `LICENSE` (MIT) — `README.md` referenced it but it was missing.
- `rules/cross-platform.md`: the installer pair is `install.sh` / `install.ps1`, not
  `setup.sh` / `setup.ps1`.
- `install.sh`: state the `python3` prerequisite in the header — it is required on every platform,
  Git Bash included, and the script hard-fails without it.

## 2026 — initial

Published: a cloneable, de-anonymized personal harness for working with AI agents — canon (`rules/`),
authoring doctrine (`doctrine/`), self-learning, session-surviving knowledge and activities, a
concierge stance, cross-agent install (Claude Code / Codex / Cursor), and a bundled
`frontend-crafter` plugin.
