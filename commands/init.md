---
description: Set up this freshly-cloned base for the person. Runs the conversational installer (or its steps by hand) — asks where + name, their language, which agents, git — wires the canon into each agent's global entry point, creates the sibling projects/, runs doctor. For a person who handed you this repo and said "install".
---

# /harness:init

The person cloned this base and wants it set up. Do it for them — never make them learn the
structure. This is the runnable form of the installer + the "For the agent" section of
`README.md`.

## Steps

1. **Load your contract** — read `AGENTS.md` (and `CLAUDE.md` if you are Claude Code). The
   canon in `rules/` is your standard; it must be hot.
2. **Run the installer** — `./install.sh` (macOS / Linux / Git-Bash) or `install.ps1`
   (Windows). If no shell is available, perform its steps conversationally. It:
   - asks **where** to place the base and **what to name** it (this clone is `harness/`; a
     sibling `projects/` is created beside it);
   - asks the person's **language** → writes it to `profile.md`. From then on you converse
     in that language; base content, code, and commits stay English;
   - asks **which agents** they use → wires the canon into each one's global entry point
     (Claude `~/.claude/`, Codex, Cursor) so it is hot from any folder;
   - asks about **git** (default yes; remote is a separate opt-in) — declined → touch
     nothing git;
   - runs the health check.
3. **Confirm in plain language** (their language) what you set up. Then work normally — you
   own this structure now.

## Not this command

- Adding a capability → `/harness:add-skill`.
- Checking health later → `/harness:doctor`.
