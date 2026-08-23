# What the kit owns, what the person owns

> A base is one repository holding two things at once: the kit (the shared standard, the same in
> every fork) and the person's own life (their knowledge, their work, the things they build). This
> file draws the line between them. Read it before replacing anything wholesale — an update, a
> repair, a migration — and before putting a person's fact anywhere near a kit path.

## The two halves

**Kit-owned — replaceable in full, identical in every fork.** Nothing personal is ever written
here, because an update overwrites it:

| Path | |
|---|---|
| `rules/` | the canon |
| `doctrine/` | on-demand authoring meta, this file included |
| `tools/` | the kit's own executables |
| `.claude/commands/` | the kit's commands |
| `.claude/settings.json` | the session wiring |
| `install.sh` · `install.ps1` | the installers |
| `AGENTS.md` · `CLAUDE.md` | the entry points |
| `README.md` · `CHANGELOG.md` · `LICENSE` | the kit's own description |
| `.claude-plugin/` | the plugin manifests |

**Person-owned — never touched by anything but the person and their agent.** An update reads these
and changes nothing:

| Path | |
|---|---|
| `profile.md` | who they are |
| `knowledge/` | their durable understanding |
| `activities/` | their ongoing work |
| `projects/` | the things they build |
| `pointers/` | their domain pointers |
| `corrections.jsonl` | the agent's record of their corrections |
| `.claude/settings.local.json` | this machine's own settings |
| anything else they created | theirs by default |

**Default when a path is in neither list: it is the person's.** A kit path is kit-owned only by
being named above.

## What this buys, and the rules that follow from it

- **An update is a replacement, not a merge.** Kit paths are swapped for the new version's, person
  paths are untouched, and the result is one ordinary save in their base — reversible like any
  other. Nobody is ever asked to resolve an overlap in a file they did not write.
- **Never put a person's fact in a kit path.** It survives exactly until the next update. A fact
  about how *they* work goes to `profile.md`; anything else routes by
  `rules/sot-dry-srp.md`. The one personal file inside the kit half is `profile.md`, and it is
  personal by design.
- **Never put kit content in a person path.** A copy of a rule under `knowledge/` is a second
  source of truth that no update will ever reach.
- **The kit's own remote is `harness-kit`, never `origin`.** `origin` is the person's private copy
  of their base. A base set up from the kit keeps both, so an update has somewhere to come from and
  a save has somewhere to go, with no way to confuse the two.
