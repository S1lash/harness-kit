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
- `.claude/commands/harness-doctor.md` + `install.sh` health check: verify canon parity — every file in `rules/` is
  named in both hand-maintained lists (`CLAUDE.md`, `AGENTS.md`). A rule listed for one agent and
  missing for another was previously undetectable, and reads as in-force when it is not.

## 2026-08-11

- `rules/working-method.md`: add "Presenting a design" — a design ships as a self-contained HTML
  artifact over a textual SoT, generated diagrams are for the person's own reading while anything
  shown to someone else is hand-authored inline SVG, and a standalone HTML file declares
  `charset=utf-8` or non-ASCII text reaches the reader as mojibake. Three traps that cost a rebuild
  each time they are met fresh.

## 2026-08-24

The kit can now reach the people running it, and a project can be opened cold.

- Add `.engine-manifest.yml` — the source of truth for which paths belong to the kit and which
  belong to the person, in four categories: `engine:` (replaced by an update), `template:` (seeded
  once, never touched again), `exclude:` (the person's, and the default for anything unlisted), and
  `retired:` (deleted from every base on every update). `doctrine/kit-ownership.md` keeps the
  judgement and no longer restates the lists.
- Add `tools/update.py` + `/harness-update`: an update REPLACES the kit's paths rather than merging
  them, so nobody resolves an overlap in a file they did not write. It refuses to report success
  when it resolved nothing or when `VERSION` did not land — a broken update and an up-to-date base
  are otherwise indistinguishable — and `--self-heal` restores the updater from the remote before
  trusting it, since the updater ships through the update it performs. A version check runs at most
  once a day at session start.
- `retired:` carries its first three entries: the commands that moved to `.claude/commands/`. A
  removal that is not retired never propagates, because the updater copies what the kit HAS and
  cannot express what it no longer has.
- Add `VERSION`, mirrored by `version:` in the manifest and `.claude-plugin/plugin.json`.
- Add `doctrine/project-home.md` and its hot trigger in `rules/harness-stewardship.md`: every
  project carries `AGENTS.md` with a `CLAUDE.md` importing it, plus its own `<project>/.claude/knowledge/`
  and `<project>/.claude/decisions.md`. Written when the project is born, repaired when it goes stale, and
  never containing what the code itself already says. `/harness-project-init` writes or repairs one.
  The person is never asked for it: they will not notice it missing, and a cold session pays for
  its absence every time.

## 2026-08-23

One base, working the same from a computer, a phone, and an agent running on a server. The pieces
that made those three diverge silently, closed together:

- `projects/` moved **inside** the base. A session opened from a fresh clone gets one repository;
  anything beside it does not exist there. `projects/_index.md` maps them, including a project the
  person deliberately gave its own repository. `rules/sot-dry-srp.md` home boundary and the
  installers follow.
- Add `rules/device-sync.md` (hot canon): one repository, one branch; bring changes in silently
  because nobody would choose a stale base; propose saving in one plain sentence and then stop
  asking for the session; never a git word in front of the person. Behaviour keyed to whether the
  working copy survives and whether there is anybody to ask — so an agent that owns a base is the
  same rule, not an exception. An agent owner holds the person's authority and decides for them:
  it saves on its own, small and often because concurrent writers are normal, and puts what it
  would have said out loud into the save message.
- `rules/git-safety.md`: saving is proactive in the person's base and asked in a repository of
  code; branch-first applies to code, not to the base.
- `tools/sync.py` holds the mechanics and `.claude/settings.json` runs its safe part at session
  start; `/harness-sync` is the manual entry point. The script never forces, never rebases, and
  refuses to pull over unsaved work.
- Commands moved to `.claude/commands/` so a fresh clone carries them with nothing installed; the
  plugin manifest points at the same files.
- Installers: two ways in — a new base, or an existing base arriving on another device, which
  touches neither content nor history. Installing never deletes `.git`; the kit's own remote is
  kept as `harness-kit` so `origin` belongs to the person. The private copy online is set up by
  default (it is what makes a phone possible), and a `projects/` folder left outside the base is
  offered a move in.
- Add `doctrine/kit-ownership.md`: which paths an update may replace and which it must never touch.
  This replaces the previous fork-and-own stance in `README.md`.

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
