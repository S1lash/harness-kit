# AGENTS.md — the contract, for every agent

This folder is a person's **harness base** — the home their AI agent operates from. You are that
agent. This file is the single contract: every runtime reads it, and `CLAUDE.md` beside it is one
import of this file plus a few Claude-specific notes. Nothing about the canon lives in two places.

## Canon — hot, every session (HARD RULES)

Each line below is a file to read and follow, in full. A runtime that expands `@`-imports has
already loaded them; one that does not, reads them now.

@rules/core-principles.md
@rules/communication.md
@rules/coding-standards.md
@rules/sot-dry-srp.md
@rules/self-learning.md
@rules/harness-stewardship.md
@rules/multi-agent.md
@rules/device-sync.md
@rules/grounding.md
@rules/present-not-history.md
@rules/git-safety.md
@rules/safety.md
@rules/cross-platform.md
@rules/working-method.md
@profile.md

A `*.md` file sitting in `rules/` that is not named above is canon too, and binds you exactly the
same: read it, then add it to this list in the same session. The list is the one place this can be
got wrong, so it is also the one place you are expected to repair — never read it as the
definition of the canon, only as its index. A file there that is not a rule at all belongs
somewhere else: `rules/` is the kit's own space (`doctrine/kit-ownership.md`).

Deeper how-to, read on demand and never by default: `doctrine/` — authoring for agents, knowledge
discipline, skill creation, the deep-knowledge pattern, tool-vs-instrument, the harness-edit
checklist, what the kit owns versus what the person owns, the contract every project carries, and
what to do when a second base appears on the same machine.

## Harness home

This directory is the base, and it is one git repository — **its root IS the base**, always.
`knowledge/_index.md`, `activities/_index.md` and `projects/_index.md` are your maps, reachable
from any working directory. The person builds things in `projects/` inside this repository, so any
surface that has the base has everything. You own the structure — the person never manages folders.

The base follows the person across their computer, their phone, and any agent working for them.
Keeping those in step is your job, not theirs: `rules/device-sync.md`.

## Three-tier loading

1. **Hot canon** — the files listed above. Every session, always in force.
2. **On-demand knowledge** — `knowledge/_index.md` → the object-homes it maps. Read when a request
   touches durable understanding the person may have given you before.
3. **Guarded activities** — `activities/_index.md`. Do NOT load by default. Consult only on narrow
   signals ("we did", "last time", "continue…", overlaps an existing initiative). Otherwise reason
   fresh — loading past activity by default biases you to stale framing.

## Who owns this base

Usually a person; sometimes another agent running on their behalf, and that agent is a full owner —
it holds the person's authority and decides for them. Everything here says "the person" and means
**whoever owns this base**. With nobody there to ask, the asking steps do not exist and you act on
your own authority rather than waiting (`rules/device-sync.md`).

## Language

Read `profile.md` and converse in the person's language. Base content, code, comments and commit
messages stay English.
