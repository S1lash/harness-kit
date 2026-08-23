# Making one base work across a computer, a phone, and an agent

Status: wave 1 landed. Waves 2 and 3 open.

## What this is about

The base is handed to people who are not engineers. They open it in a terminal, in the desktop app,
and on a phone, and they expect the same thing in all three. They will never say the words commit,
branch or merge — they will say "why is my phone showing something different". Everything below
exists to make that question rare and, when it happens, answerable in one sentence.

## Done — wave 1

- ✅ `projects/` moved inside the base; `projects/_index.md` is the map, including projects that
  were deliberately given their own repository.
- ✅ `rules/device-sync.md` — the contract: one repository, one branch, sync in silently, propose
  saving in plain language, never a git word in front of the person. Behaviour keyed to two
  questions (does this copy survive; is anybody in the loop) rather than to device names, so a
  headless agent on a server is covered by the same rule.
- ✅ `rules/git-safety.md` — saving is proactive in the base, asked in a repository of code;
  branch-first scoped to code. `rules/sot-dry-srp.md` — home boundary rewritten for one repository.
- ✅ `tools/sync.py` — the mechanics; `.claude/settings.json` — a session-start hook that runs the
  safe part of it; `/harness-sync` — the manual entry point.
- ✅ Commands moved to `.claude/commands/` so a fresh clone has them with no plugin installed; the
  plugin manifest points at the same files.
- ✅ Installers: two ways in (new base / existing base on another device), history never deleted,
  the kit's remote kept as `harness-kit`, the private copy set up by default, an identity to save
  under, and a migration for a `projects/` folder left outside.
- ✅ `doctrine/kit-ownership.md` — which paths an update may replace and which it must never touch.

## Open — wave 2

- The update channel itself: a version marker, `/harness-update` replacing kit-owned paths from a
  pinned version, and a cheap "there is a newer version" check folded into the sync run.
- `tools/sync.py` has no automated test. It is exercised by hand; the branches that matter
  (diverged, offline, no remote, no identity) deserve a harness.
- The installers' Windows half is not machine-verified — no PowerShell in the environment it was
  written in. It needs one run on a real Windows machine.

## Open — wave 3

- **Secret hygiene — a named debt, parked deliberately.** One repository plus proactive saving means
  everything in the base folder reaches the person's private copy without them doing anything. That
  is fine while the owner knows it. It is not fine for people who do not know that putting a file in
  a folder publishes it, and it is the blocking item before the base is handed to anyone who keeps
  server keys near it.
- Where infrastructure facts live and how a deploy is triggered — resolves into
  `knowledge/`, `tools/` and `projects/` by object rather than into one folder.
