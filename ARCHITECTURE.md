# How this kit is built

> A map of how the pieces connect. Every fact here has a home elsewhere, and this file links to
> it rather than restating it — what it adds is the shape you cannot see from inside any one
> file. Why each choice was made: `DECISIONS.md`. What it cannot do yet: `KNOWN-LIMITS.md`.

## The problem

An AI agent is useful in a session and amnesiac between them. The usual fixes each fail in the
same way — they hold state somewhere only one thing can read:

| Where state usually goes | Who cannot read it |
|---|---|
| the agent runtime's own memory | every other runtime, and in some runtimes every other folder |
| a chat history | any agent, any script, any other device |
| a notes app | the agent |
| the person's head | everything, eventually |

A harness base is the answer this kit implements: **one git repository that is the agent's home**,
holding both a shared standard and one person's accumulated work, readable by every runtime and
present on every device.

Git is not an implementation detail here. It is the only mechanism that already solves the four
things this needs at once — history, transport between devices, merge without a server, and a
line between what came from upstream and what is local. The person never sees it
(`rules/device-sync.md` → "What the person never sees").

## Three axes, one repository

The base has to stay the same thing along three independent axes. Each has a rule that states
the invariant and a mechanism that keeps it:

```
                    the SAME base, whichever …

  agent runtime ──────┐
  (Claude, Codex,     │
   Cursor, next)      │       rules/multi-agent.md  ─── one canon list in AGENTS.md
                      │
  surface ────────────┼──── one git repository ──── rules/device-sync.md ─── tools/sync.py
  (laptop, phone,     │
   terminal, server)  │
                      │
  point in time ──────┘       doctrine/kit-ownership.md ─── tools/update.py
  (cloned today or a
   year ago)
```

They are independent, and a break in any one is invisible from the other two. That is why each
gets its own hard rule rather than a shared paragraph: an agent reasoning about devices will not
notice that a rule reached Claude Code and not Codex.

## Layer 1 — the canon: one list, many readers

Every runtime loads its instructions from a different file. If each carried its own copy of the
canon, a rule would be in force for one agent and absent for another, with nothing to announce
it. So there is exactly **one hand-maintained list**, and everything else derives from it:

```
  rules/*.md            the rules themselves — one subject each
       ▲
       │ named by
       │
  AGENTS.md             THE list. Hand-maintained. The only one.
       ▲
       ├── CLAUDE.md                    one `@AGENTS.md` import + Claude-only notes
       └── ~/.claude/CLAUDE.md          written by install, points at this base
           ~/.codex/AGENTS.md           same
           Cursor user rules            same
```

What adding a rule costs, and when the installer has to be re-run at all, is stated once in
`rules/multi-agent.md` → "A canon change reaches every wired agent in the same edit". The shape
above is why that list can be short.

**The list repairs itself.** `AGENTS.md` tells the agent that a rule file it does not name is
canon anyway: read it, then fix the list in the same session. The list is an index, never the
definition — because the one thing that must never happen is a rule everybody believes is in
force while nothing loads it. `tools/check_kit.py` proves the two agree.

**How much of this a machine does depends on the runtime.** A runtime that expands `@`-imports
loads the canon as files; one that does not is *instructed* to read them and is trusted to. So the
arrows above are a wiring diagram in one case and an instruction in the other, and the gate proves
only that the list names every rule — never that anything read them. That is the honest ceiling on
"this rule is in force", and it is why the canon is small enough to be read in full.

**Three loading tiers**, because loading everything is as bad as loading nothing: hot canon every
session; `knowledge/` on demand; `activities/` only on narrow signals, since past activity loaded
by default biases the agent toward stale framing
(`doctrine/knowledge-discipline.md` → "Anti-bias trigger — do NOT load history by default").

## Layer 2 — ownership: one line, drawn by path

A base is one repository holding two things with different lifecycles: the kit, identical in
every fork and replaced on update, and the person's own life, which nothing may overwrite. Every
mechanism that has to tell them apart reads the same file:

```
  .engine-manifest.yml     ← the only answer to "whose path is this?"
       │
       ├─ through tools/lib/manifest.py ─┬── tools/update.py      replace, seed, move, drop
       │                                 ├── tools/lib/migrate.py · retire.py
       │                                 ├── tools/check_kit.py   is the declaration coherent
       │                                 └── tools/lib/portability.py   what ships must be portable
       │
       ├─ parsed directly ───────────────┬── install.sh     `kit_remote:`, by sed
       │                                 └── install.ps1    `kit_remote:`, by regex
       │
       └─ read as prose ─────────────────── the agent      where a new fact belongs
```

The installers cannot import a python library before python is known to exist, so `kit_remote:`
has three parsers in three languages that move in lockstep — a [CP-4] obligation
(`rules/cross-platform.md` → "The clauses"). Changing the manifest's scalar syntax is therefore a
change to all three.

Five categories — `engine:` `template:` `exclude:` `migrations:` `retired:` — each defined in the
manifest's own header, with the judgement that follows in `doctrine/kit-ownership.md` →
"The five categories, and what each one means for you".

The consequence worth naming: **the manifest entry IS the decision.** Listing a path under
`engine:` ships it, subjects it to the portability clauses, and makes it something an update
overwrites — all at once, with nothing else to remember and nothing to label.

## Layer 3 — the two engines

### Updating: replacement, never merge

An update must never hand the person a conflict. They did not write the kit's files and cannot
adjudicate a disagreement inside one. So kit paths are **replaced wholesale** from the kit remote,
and the line that makes this safe is Layer 2: nothing personal is ever written into a kit path
(`DECISIONS.md` → "2026-08-23 — An update replaces the kit's paths; it never merges").

The ordering is what makes it correct:

```
  resolve the kit            by the ADDRESS the manifest declares, name only as fallback
    ↓
  fetch
    ↓
  read the INCOMING manifest from the ref, before anything is replaced
    ↓
  refuse if dirty            a kit path with unsaved edits is a STOP, not an obstacle
    ↓                        (unless it already matches the ref — nothing there to lose)
  seed missing templates     what the INCOMING manifest declares, so a new seed lands now
    ↓
  replace kit paths          including paths THIS release adds to engine:
    ↓
  refuse if nothing resolved `resolved == 0` is a broken update, never an up-to-date base
    ↓
  migrate  ·  retire         independent passes; one refusing never cancels the other
    ↓
  verify                     VERSION reads what the kit ships, or nothing is claimed
```

Resolving by address rather than by name is what makes renaming the kit survivable: the remote's
name lives in each base's git config, which no manifest section reaches and no clone carries, so
it cannot be changed by shipping anything.

Two properties fall out of this shape:

- **Code takes effect one update late; a declaration lands the same run.** The updater ships
  through the update, so new *logic* only runs next time — which is precisely why moves and
  removals are declared as manifest data rather than written as code. For that to hold, every
  pass has to read the manifest being SHIPPED rather than the one the base still has; each place
  that read the local copy instead was a section arriving one release late while the dry-run
  promised it now. A base a year stale converges in one run.
- **Convergent, not sequential.** Migrations are idempotent and keep no ledger of what has been
  applied. A clone that sat untouched for a year has no valid position in an ordered chain; asking
  "is this already done?" of the filesystem always has an answer
  (`DECISIONS.md` → "2026-08-23 — Migrations are declared data, convergent, and have one verb").

`--self-heal` exists because the updater ships through the update: a base carrying a broken copy
cannot receive its own repair by the normal path. Its boundary — and the recovery for corruption
past it — is in `KNOWN-LIMITS.md`.

### Syncing: state in, state out

`tools/sync.py` holds the mechanics; `rules/device-sync.md` holds the judgement. The split that
matters is not "which device" but two questions — does this working copy survive the session, and
is anybody there to ask (`rules/device-sync.md` →
"Two questions decide your behaviour — not the name of the device"). An agent that owns a base is a **full owner**: it decides rather than
waiting, because there is nobody to defer to and unsaved still means lost.

What that judgement actually requires — when to ask, when to stop asking, and what never to say
to the person in git's words — is `rules/device-sync.md`, and only there. Copying an operative
consent model into a second file gives it two places to change and nothing to compare them.

**The base has two remotes, and they are not interchangeable.** `origin` is the person's own
private copy, the one that makes a phone possible, and `sync.py` is the only thing that pushes to
it. The kit's address is where `update.py` fetches from, and nothing ever pushes there. The
installer keeps both so an update has somewhere to come from and a save has somewhere to go, with
no way to confuse the two — and the updater resolves the kit by address precisely so a base that
named them unusually still updates from the right one.

## Layer 4 — the gates

Every mechanism above has a failure mode invisible to whoever causes it. The gates exist to make
those visible **here**, rather than on a machine nobody can see:

| Gate | Catches | Would otherwise surface as |
|---|---|---|
| `check_kit.py` (any base) | a rule missing from the list; a declared path that is not there; a retirement that contradicts itself; a clause nothing enforces; a pointer into a section that moved — and the portability scan, which it runs itself | a rule silently not in force; a citation aimed at the wrong paragraph |
| `check_kit.py --authoring` | what only the kit's own repository can know: a removal with no `retired:`; a tool declared nowhere or absent from `tools/_kit.md`; a version that did not move; a seed already shipped being edited; the person's space shipping non-empty; a shell tool with no twin; a fork pointing at upstream | somebody else's base, days later |
| `check_portability.py` | CP-1, CP-2, CP-3, CP-5, CP-6 over everything that ships. CP-4 is not expressible as a pattern over one file, so the tests and `check_kit.py` carry it | "it doesn't work on my machine" |
| `tools/tests/` | the machinery itself — including what a read can prove about `install.ps1` | a lost save, or an update that silently applies nothing |
| `/harness-doctor` | the state of one base, report-only | drift nobody looks for |

Two things are deliberate. **A green gate means "nothing recognisable is wrong", not "this is
correct"** — `KNOWN-LIMITS.md` names what each cannot see. And **a test that cannot fail proves
nothing**: changing any of this means breaking it on purpose and watching the gate catch it
(`doctrine/kit-ownership.md` → "Shipping a release").

## The invariants

Everything above is negotiable in its details. These are not — each one, broken, produces a
failure that announces itself only much later. What holds each one is named, because an invariant
guarded only by the current author's discipline should be read as exactly that:

1. **One list of the canon.** A second copy is a second truth that drifts silently.
   *Gated* — `check_kit.py`, on any base.
2. **The base is one repository, with one branch.** A branch is invisible on a phone; anything
   outside the repository does not exist on the next surface.
   *Reported, never enforced* — `sync.py` counts branches and `/harness-doctor` warns. Deliberate:
   a person mid-experiment has a reason, and refusing to sync would strand them.
3. **Nothing personal in a kit path; nothing of the kit's in a person path.** The first survives
   until the next update, the second can never be corrected by one.
   *Half gated* — the kit shipping into a person path fails a release. A person's edit already
   committed into a kit path is overwritten silently; only an UNSAVED one stops the update.
4. **An update replaces and never merges.** The person cannot adjudicate a conflict in a file
   they did not write.
   *Gated* — the tests refuse a merge, rebase, reset or stash verb anywhere in the updater.
5. **`--force` and its quiet equivalents need the person, in the moment.** They destroy exactly
   what git normally refuses to (`rules/git-safety.md`).
   *Gated for the python tools* — the installers are not scanned, because PowerShell's unrelated
   `-Force` on `New-Item` would make the scan useless.
6. **The structure is the agent's burden, never the person's.** A harness whose owner has to
   curate it becomes a chore and dies
   (`rules/harness-stewardship.md` → "The structure is for the AGENT, not the person (HARD RULE)").
   *Unmechanisable* — no gate can read this, and none pretends to.

## Where the seams are

For anyone extending this, these are the places designed to be extended, and what each costs:

- **A new rule** → a file in `rules/`, a line in `AGENTS.md`. Nothing else.
- **A new kit tool** → the file, an `engine:` line, a row in `tools/_kit.md`. It must run through
  an interpreter that exists on every platform (`doctrine/tool-vs-instrument.md`); the release
  gate refuses a shell tool with no twin.
- **A new manifest category** → the most expensive seam here, and the one with no safety net.
  `tools/lib/manifest.py` must list it, `update.py` must read it into the incoming set and run the
  pass, `check_kit.py` must gate it, and `portability.py` must count it if it ships files — plus
  the manifest header and `doctrine/kit-ownership.md`. And note what does NOT protect you: an
  unknown *verb* inside `migrations:` stops the run and says to update once more
  (`tools/lib/migrate.py`), but an unknown *category* is simply never matched, so an older updater
  ignores the whole section in silence. Design the category so that being ignored is safe.
- **A new seed under `template:`** → cheap to add and permanent to get wrong. A seed is created
  when missing and never rewritten, so whatever the kit puts in one is frozen at each person's
  clone date forever; `check_kit.py --authoring` fails a release that edits a seed which already
  shipped. Keep a seed to what will never need to change, and put anything that will into an
  `engine:` file the seed links to.
- **A new runtime** → a global entry point pointed at `AGENTS.md`, in both installers
  (`rules/cross-platform.md` → "The clauses", [CP-4]).
- **A new agent-facing command** → `.claude/commands/`, which the kit owns. Anything authored for
  one person goes to `.claude/skills/`, which no update touches.

What is *not* a seam: the split between kit and person is drawn by path and by path only. A
mechanism that needs a different line — ownership by source, several kits sharing one base — is a
change to this architecture, not a configuration of it.
