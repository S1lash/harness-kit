# Making one base work across a computer, a phone, and an agent

Status: waves 1 and 2 landed. Wave 3 open.

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

## Done — wave 2

- ✅ `.engine-manifest.yml` — the path-ownership contract, machine-readable, four categories.
- ✅ `tools/update.py` + `/harness-update` — replacement rather than merge, retirement sweep,
  self-heal, and post-conditions that refuse to call a no-op a success. Verified end to end against
  a throwaway base built from the pre-wave-1 state: kit paths replaced, retired commands dropped,
  the person's own index rows, profile and project untouched, second run idempotent.
- ✅ `VERSION` + the daily version check at session start.
- ✅ One canon list. `AGENTS.md` is the contract, `CLAUDE.md` imports it, the installers point every
  runtime at `AGENTS.md`. The parity check is gone with the duplicate that made it necessary.
- ✅ `tools/check_kit.py` — the author-side gate, every check verified red and green: a removal
  without a retirement, a retired path still shipping, a version mirror out of step, a rule missing
  from the list, the list restated in `CLAUDE.md`, a path owned twice, a tool declared nowhere, a
  corrupt manifest that would otherwise pass by having nothing to check.
- ✅ Update verified across unrelated git histories — the `install.sh` copy path, where a base
  shares no commit with the kit.

## Done — the machinery proves itself

- ✅ `tools/tests/` — 29 tests over the manifest reader, the `*/` coverage rule, the retirement
  guard, the updater end to end against a real remote (replacement, retirement, idempotence,
  dry-run, refusals), and `sync.py`. Every one was mutation-checked: the code was broken on purpose
  and the suite had to catch it. That found the one test guarding a real past bug testing the wrong
  shape of it — it passed against the very mutation it existed to stop, and now does not.

## Verified by audit, not only by hand

Four independent reviews (two on the Windows installer, one adversarial probe of the no-migrations
decision, one cold-start walkthrough) plus the first real execution of `install.sh`. Everything they
found that could be closed, was; the rest is below. The suite is at 45 tests, each mutation-checked.

## Open


- **`install.ps1` is fixed but still never executed.** No PowerShell in the environment it was
  written in. Seven static tests guard what a read can prove — BOM, encoding, native-call routing,
  prompt and doctor parity — but nothing here can prove it runs. One run on a real Windows machine
  remains the outstanding item.
- **A template's kit-maintained half is frozen at the person's clone date.** `tools/_index.md`
  carries kit rows that no update can refresh. Either those rows move to an engine file the
  template links to, or the constraint stays and the rows must never need to change.
- **Migrations are deliberately not ported** — and the caveat is now stated in `DECISIONS.md`
  rather than implied: replacement plus retirement cannot express a template's frozen half, a
  rename inside the person's own space, or anything outside the tracked tree (the kit's own
  remote, its release branch, the global agent wiring). Until a channel exists the kit must not
  change any of those. The engine this copies runs an ordered chain with
  `structural` and `heal` kinds and a ledger. Retirement covers removals, which is every case the
  kit has today; a migration runner would be a subsystem shipped to every person with nothing to
  run. Port it the first time an update needs to reshape something inside the person's own space —
  that is the trigger, and until then it is dead weight that must still be maintained.
- **Not covered by tests:** the diverged-merge and offline paths of `sync.py`, and `--self-heal`.
  They need either a second remote or a severed network in the fixture; both are worth adding.
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
