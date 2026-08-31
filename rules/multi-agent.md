# Multi-Agent Parity (HARD RULE)

This base is the shared home for **every** agent runtime the person uses — Claude Code, Codex,
Cursor, whatever comes next. They differ in tools; they must not differ in canon, in where facts
live, or in what they know. The person should never have to think about which agent they are in.
Hot: loaded every session, single-agent setups included.

## The base is the memory; an agent's private store is scratch

Every runtime keeps a private store the others cannot read — Claude Code writes per-working-directory
memory under `~/.claude/projects/`, Codex and Cursor keep their own. This is not a shared brain: it
is invisible across runtimes, and in Claude Code's case invisible across folders too, so it silos
even a person who uses exactly one agent.

- **A private store is never the home of anything durable.** It holds the current session's
  scratch. Everything that outlives the session is routed by `rules/self-learning.md` into the
  base — `knowledge/`, `activities/`, `profile.md` — where every agent reads it.
- **Find a durable fact sitting in a private store → promote it** to its proper home and tell the
  person in one line. Leaving it there is a silent divergence: two agents that quietly know
  different things, with no duplicate anywhere to notice.
- **Resume from the base, not from recall.** Continuing work started in another runtime (or another
  folder) → read `activities/`. "I don't remember" is not a state to reason from; the base is where
  the state actually is.

## A canon change reaches every wired agent in the same edit

The canon has one source — `rules/` — and exactly ONE hand-maintained list of it: the canon
section of `AGENTS.md`. Every other surface derives from that list rather than repeating it, so a
rule cannot be in force for one runtime and absent for another:

| Surface | How it updates |
|---|---|
| `rules/*.md` | the source — you edit it |
| `AGENTS.md` — the canon list | **by hand, in the same change**. The only list. |
| `CLAUDE.md` | derived — one import of `AGENTS.md`, plus Claude-only notes. Nothing to keep in step. |
| Global entry points (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`) | derived — the installers point each at `AGENTS.md`. Adding a rule never requires re-running them. |
| Cursor user rules | derived, but written **by hand once**: Cursor has no scriptable global rules file, so the installers produce a snippet to paste. It points at `AGENTS.md`, so it too survives a rule being added — but a base whose owner never pasted it is canon-free in Cursor, and nothing detects that. |

- **Add, rename, or remove a rule → update the list in `AGENTS.md` in the same unit of work.**
  Re-run `install.sh` only when the wiring itself changed (the base moved, a new runtime).
- **Never restate the canon anywhere else.** A second list is not redundancy, it is a second truth:
  it drifts silently and the person goes on believing a rule is in force. That is why there is one.
- **A rule that reaches one agent and not another is worse than no rule.** Partial landing is not a
  small omission; it is a hole the next session inherits blind.
- **Say which surfaces you touched** when you change canon. One line, not a report.
- **Verify, don't assume:** the file list in `rules/` and the list in `AGENTS.md` name the same
  set. A rule on disk that the list omits still binds — read it and repair the list in the same
  session. The list is an index, never the definition.
  `python3 tools/check_kit.py` proves it, in any runtime; `.claude/commands/harness-doctor.md` is the procedure that reports it (a command in Claude Code, a file to follow elsewhere).

## Different capabilities, identical canon

Runtimes differ in what they can *do* — skills, slash commands, MCP servers, sandbox rules. Nothing
about that changes what is *true*: the canon binds all of them, facts route to the same homes, and
knowledge written by one is read by the others.

- **Missing a capability is not permission to improvise.** Name which runtime does the thing, capture
  whatever the person just told you so it is not lost, and say so in one line. A silent workaround
  that half-does the job is the failure mode — it looks like success and corrupts the home it wrote to.
- **Read is almost never the constrained side.** Any runtime can read the base and answer from it;
  asymmetry usually lives in writing and in tooling. Don't decline to *look* something up because
  the current agent lacks a tool for *changing* it.
- **What one runtime does automatically, the others do by hand — and the hand is yours.** Two
  things are wired for Claude Code alone and for nobody else:
  - **Catching the base up, and checking for a newer kit.** `.claude/settings.json` runs both at
    session start. In any other runtime nothing does, so you run
    `python3 tools/sync.py session-start` first thing and
    `python3 tools/update.py --check` about once a day. Neither is optional: a base that never
    catches up and a base that is current look identical from inside the session.
  - **The slash commands.** `/harness-sync`, `/harness-update`, `/harness-doctor`,
    `/harness-init`, `/harness-project-init`, `/harness-add-skill` are files under
    `.claude/commands/`, and only Claude Code turns them into commands. Every one is a procedure
    written in plain English — read the file and carry it out. The capability is the procedure,
    not the slash.
- **A repeatable procedure has one registration point today, and it is Claude's.**
  `rules/harness-stewardship.md` tells every runtime to turn a recurring task into a skill, and
  `doctrine/skill-creation.md` registers it at `.claude/skills/<name>/SKILL.md`, which only
  Claude Code discovers. Write it there anyway — it is a readable procedure in every runtime and
  the person's own capability home — and say once that it is invocable in Claude Code and a file
  to follow elsewhere. Do not invent a parallel home for it: a second one is a second truth.

Why: the person's leverage comes from one accumulating base, not from several agents each half-
remembering. The moment memory or canon forks per runtime, the base stops being a source of truth and
becomes two opinions — and nothing in the system will announce that it happened.
