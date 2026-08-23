# A project carries its own contract

> Every project the person builds gets a small home of its own — the minimum an agent needs to
> open it cold and be useful in the first minute. The hot trigger (when you write one) is in
> `rules/harness-stewardship.md`; this file is the shape and the discipline.
> A project's facts belong to the project, not to the base (`rules/sot-dry-srp.md`).

## Why this is yours and not the person's

They will never write it. They will not know it is missing, and they will not connect a bad
session to its absence — they will just notice the agent being slow, wrong, or asking things it
was told last week. The first minute in a project is where that is decided, and on a phone, a
fresh clone, or a headless run there is no history to lean on: only what is written down.

## The shape

```
projects/<name>/
├── AGENTS.md              the contract — every runtime reads this one
├── CLAUDE.md              one line: @AGENTS.md  (plus anything Claude-specific below it)
└── .claude/
    ├── knowledge/_index.md   durable facts about this project's internals
    └── decisions.md          why it is built this way
```

**`AGENTS.md` is the single source; `CLAUDE.md` imports it.** Claude Code reads `CLAUDE.md` and
not `AGENTS.md`, while other runtimes read the reverse — so the bridge is an import, never a
second copy. A nested `CLAUDE.md` loads by itself the moment an agent reads a file in that folder,
which is exactly when it is needed and never before.

A project living in its own repository has the same shape at its own root, and its row in
`projects/_index.md` says where that is.

## What goes in `AGENTS.md` — five sections, nothing else

Under 200 lines. Longer stops being read.

1. **What this is, and why it exists.** One paragraph. What it does, who it is for, what would be
   lost if it disappeared. This is the section people skip and agents need most: without it every
   later judgement call is a guess.
2. **How to run it, test it, and ship it.** The exact commands, and what "working" looks like.
3. **What you cannot see from the code.** Which parts are load-bearing, what depends on what, what
   an outsider would break by touching it.
4. **Traps.** Each one: what goes wrong, and what to do instead. A trap that cost a session once
   costs it every session until it is written here.
5. **Where the rest lives.** A pointer to `<project>/.claude/knowledge/` and `<project>/.claude/decisions.md` — not a
   summary of them.

## The filter — write only what the code cannot tell you

Directory listings, dependency lists, an architecture overview restated from the source, a
function's signature: the code is the source of truth for all of it, and a copy here is wrong the
moment the code moves. **Keep what a fresh reading of the code would not reveal** — the reasons,
the conventions that differ from the tool's defaults, the invariants, the traps.

Test before writing a line: *"if this code changes next quarter, does this line become a lie?"*
Yes → write the pointer and the reason instead (`rules/self-learning.md`, the snapshot test).

## Keeping it true

- **A project is born → its contract is written in the same unit of work.** Not "once it settles":
  the reasons are clearest while the decision is being made and are gone a week later.
- **A change makes a line wrong → fix it in that change.** A contract with three stale lines gets
  believed and acted on; that is worse than no contract at all.
- **A trap you just hit goes in.** You paid for it once — that is the whole point.
- **Present tense only** (`rules/present-not-history.md`). What is true now, never what it used to
  be. History lives in git.
