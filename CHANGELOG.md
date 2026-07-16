# Changelog

The sanctioned history home for this repo (the one place `present-not-history` allows a record of
change — like `knowledge/decisions.md` for decisions). The canon itself always describes the
present; evolution is logged here.

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
