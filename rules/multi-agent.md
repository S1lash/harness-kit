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

The canon has one source — `rules/` — and several surfaces that carry it to a runtime. Two of those
surfaces are maintained by hand and will not update themselves:

| Surface | How it updates |
|---|---|
| `rules/*.md` | the source — you edit it |
| `CLAUDE.md` — the `@rules/...` list | **by hand, in the same change** |
| `AGENTS.md` — the canon list | **by hand, in the same change** |
| Global entry points (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, Cursor user rules) | derived — `install.sh` regenerates them; the Claude block enumerates `rules/`, the others point at `AGENTS.md` |

- **Add, rename, or remove a rule → update both hand-maintained lists in the same unit of work**,
  and re-run `install.sh` when the wiring itself changed (adding a file to `rules/` does not need it;
  moving the base does).
- **A rule that reaches one agent and not another is worse than no rule** — the person believes it is
  in force, and half the time it is not. Partial landing is not a small omission; it is a hole the
  next session inherits blind.
- **Say which surfaces you touched** when you change canon. One line, not a report.
- **Verify, don't assume:** the file list in `rules/`, the `@`-list in `CLAUDE.md`, and the canon
  list in `AGENTS.md` name the same set. `/harness-doctor` checks this; so can you, by eye.

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

Why: the person's leverage comes from one accumulating base, not from several agents each half-
remembering. The moment memory or canon forks per runtime, the base stops being a source of truth and
becomes two opinions — and nothing in the system will announce that it happened.
