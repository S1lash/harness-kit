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

## 2026-08-23

The canon layer, closing three holes that were each a rule believing itself enforced:

- Add `rules/safety.md` — irreversible and outward-facing actions that are not git's. The
  discriminator in `harness-stewardship.md` had been pointing at a list that did not exist. It also
  reconciles with `device-sync.md`: an agent that owns a base decides instead of asking, but
  look-first, scope, and the ban on unwitnessed outward-facing actions do not relax — the absence
  of a witness is what makes such an action unreviewable, so it goes into the save message instead.
- **The canon list repairs itself.** `AGENTS.md` now tells the agent that a rule on disk the list
  omits still binds: read it and fix the list in the same session, and never read the list as the
  definition of the canon. The release gate already caught a missing entry for the author; on a
  person's base nobody runs it, and the instruction is what closes that half.
- The concierge pillar gains **how to offer** a capability — by judgement, never by keyword, and
  silence over an offer that adds ceremony to work that did not need it. Deliberately without a
  catalog of capabilities: the runtime already knows its own, and a shipped list would be wrong on
  the first base that installs anything.


Two things the kit could not do, and the gates that keep them from coming back:

- **`migrations:` — a change replacement cannot express.** A path in the person's own space that has
  to move is now declared as manifest data, carried after the checkout, idempotent so every base
  converges from any version, and refused outright if it reaches into the kit's own space or would
  land on something the person already has. A verb an older updater does not know stops the run
  instead of being skipped. Alongside it: the kit's own address is reconciled from the manifest on
  every update, so moving the kit is staged a release ahead rather than breaking the only channel
  that could repair it; and global agent wiring that no longer names the base is reported.
- **Seeds are thin, and the freeze is now visible at authoring time.** A `template:` file is created
  when missing but never rewritten, so its kit-maintained half was frozen at each person's clone
  date — silently. Every index seed now carries only the person's own rows plus one pointer, with
  the kit's half moved into engine files (`tools/_kit.md` is the first), and
  `check_kit.py --authoring` fails a release that edits a seed which already shipped.
- **The kit ships its own person-space pristine.** There is no extraction step — a clone carries the
  whole repository — so the kit's own working notes under `activities/` would have landed in every
  base as though the person had written them. They are gone, `KNOWN-LIMITS.md` carries what they
  said, and a gate fails any release that puts them back.
- Everything that describes the kit was brought back in step with it in the same change: the
  README now lists the engine files it never mentioned, the tool catalogue is documented as the two
  files it became, the plugin manifests name all six commands, the edit checklist asks whose a path
  is before anything else, and both the installer's flow docs say what happens when nobody is there
  to answer its questions. The kit's own working notes are gone from the person's space.
- The suite is at 65 tests, every one mutation-checked. That found two gates that were tested as
  functions but never as wired, so the gate is now also exercised end to end the way an author runs
  it.


What four independent audits and a first real run of the installers found, and what closed:

- **The Windows installer could not have worked.** Native `git` output aborted it under a
  stop-on-error preference; file reads decoded through the ANSI code page and written back as
  mojibake corrupted `profile.md`; and the script's own non-ASCII literals were mis-parsed for want
  of a byte-order mark. Also fixed: `Remove-Item` on a directory symlink could take the canon with
  it, a dangling link was never repaired, a merge copy nested `rules/rules`, paths resolved against
  the wrong directory, an empty username silently skipped the git identity, and the `python3` check
  was wrong in both directions. Seven static tests now stand in for the interpreter this
  environment does not have.
- **Both installers refuse a run nobody can answer.** With no interactive terminal every prompt
  took its default and the script still printed "your base is ready" — output indistinguishable
  from a real install. Supplying answers now has to be declared.
- **The shell installer, run for the first time**, left the base on `master` with no commit: pushed
  to a repository whose default is `main`, that is two branches, and a phone cloning the default
  one finds nothing. It now starts on `main` with one commit and a clean tree.
- **A seed added after somebody cloned reached them never**, while the canon arriving in the same
  update named it as though it were there — `projects/_index.md` is a live instance. A template
  that is missing is now created; one that exists is still never touched.
- **Putting two sides together never worked at all**: the merge passed `--no-rebase`, a `git pull`
  flag, so git printed its usage and failed. Two different bases pointed at one place are now named
  as that rather than reported as a file conflict.
- **The kit's own address is repo content now.** It was only ever in one machine's git config, so a
  phone told to "reconnect the kit remote" had nothing to reconnect to. It also stops an installer
  from stripping the origin of anyone whose own repository is called harness-kit.
- **The kit's own decisions moved to `DECISIONS.md`.** They were sitting in the person's
  `knowledge/decisions.md` — kit content in a person's path, frozen at their clone date, which is
  the thing `doctrine/kit-ownership.md` forbids.
- An update now names every path it replaced, added or dropped rather than counting them; `sync.py`
  reports a base carrying more than one branch; `/harness-update` says when re-wiring is needed.


One base, working the same from a computer, a phone, and an agent running on a server. The pieces
that made those three diverge silently, closed together:

The kit can now reach the people running it, and a project can be opened cold:

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

One canon list instead of two, and a gate that catches a bad release before anyone runs it:

- `AGENTS.md` is now the single contract every runtime reads, carrying the one hand-maintained
  canon list; `CLAUDE.md` is one import of it plus Claude-only notes. The parity check existed only
  because the list was written twice — the duplicate is gone, so is the class of drift where a rule
  is in force for one runtime and silently absent for another. The installers point every runtime's
  global entry at `AGENTS.md`, so adding a rule never requires re-running them.
- `.claude/skills/` is declared the person's own capability home. `.claude/commands/` beside it is
  the kit's and is replaced on update: a skill authored there would vanish at the next update,
  silently.
- Add `tools/tests/` — 29 tests over the manifest reader, the retirement guard, the updater driven
  end to end against a real git remote, and `sync.py`. Each was mutation-checked by breaking the
  code on purpose; that caught the regression test for a real past bug testing the wrong shape of
  it, passing against the very mutation it existed to stop. What was verified by hand once now
  re-runs, and `/harness-doctor` runs it on any base.
- Add `tools/check_kit.py`. Its structural half runs on any base and is what `/harness-doctor`
  calls; `--authoring` adds the release checks — a removal without a `retired:` line, a retired path
  that still ships, a tool declared nowhere, kit paths changed without `VERSION` moving, `VERSION`
  moved without `CHANGELOG.md`. Every one of them is a mistake that otherwise surfaces only on
  somebody else's machine.

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

## 2026-08-30

The platform layer: the cross-platform rule stops depending on somebody remembering it.

- `rules/cross-platform.md` rewritten. Scope is no longer a judgement call — tier 1 is exactly what
  `.engine-manifest.yml` ships (`engine:` + `template:`, minus `exclude:`) and is held to the letter
  because it reaches machines nobody here will ever see; tier 2 is the person's own space, held to
  the spirit. Its clauses are named `[CP-1]`..`[CP-6]` rather than numbered by position: a gate that
  cites "section 2.2" is wrong the first time a paragraph moves, and a contract that can be cited
  from code has to have a name that does not drift.
- Add `tools/lib/portability.py` and `tools/check_portability.py` — the machine-checkable half of
  those clauses, run over tier 1 by `check_kit.py` and therefore by `/harness-doctor` on any base.
  Rules match code and never prose: comments and docstrings are blanked, markdown is read only
  inside language-tagged fences, so the rule file that *lists* every banned construct is not itself
  a finding. The one escape is an inline `portability-ok: <reason>` with the reason mandatory —
  there is no allowlist file, because an exemption nobody reads is how a rule quietly stops
  applying.
- `check_kit.py` binds clause IDs in both directions: a clause the canon defines that nothing
  enforces, and a gate rule citing a clause nobody wrote, are both failures. Neither was previously
  visible, and the first is the shape of a rule everyone believes is guarded.
- The symlink machinery is gone from `install.sh` and `install.ps1`. It was the one mechanism that
  could not be made to behave the same on all three platforms — Git Bash writes a text stub unless
  an environment variable is set, a dangling link is invisible to `Test-Path`, and `Remove-Item` on
  a directory link deletes through it — and nothing in the kit needed it. A copy is understood by
  everyone; a link that is a file on one platform is not.

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
