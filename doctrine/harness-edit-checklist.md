# Checklist for a harness edit / moving a fact

> On-demand authoring meta. Read when **adding** a new fact (§0), when **moving / merging** a
> fact between homes, and before an edit that touches links. Closing the edit — walk the whole
> list. This is the **verification rail**: each item closes a failure that has already happened
> (dead links from guessed headings, inline tool mechanics, tombstones, under-verification).

## 0. Where to put it (for a new fact)

- **Canon question** (rules/sot-dry-srp.md → home-by-object): about the **object itself** → the
  object's home; about **our process** with it → a topic domain **by link**; about **a callable
  automation** over it → a tool. Full map — `knowledge/_index.md`.
- **Already lives somewhere?** `grep` the fact's name across `knowledge/` `rules/` → link, don't
  copy. A copy = future drift.
- **A value from code / config** (a field ID, a signature, SQL, an enum)? → a pointer to the
  source, not a snapshot (rules/self-learning.md → noise filter).
- **Writing / editing the text of a rule or hot knowledge**? → apply
  doctrine/authoring-for-agents.md: the reader is the agent, a line stays only if it changes its
  action.

## 1. Anti-dead-link (reference only what you actually opened)

- Before referencing a section of another file (`file → "..."`) — **OPEN the target file and
  COPY the exact heading**. Don't guess or reconstruct the section name from memory.
- The proof a link is live is that you **opened** it, not that it "looks plausible".

## 2. Move — atomic, no tombstones

- The old spot is deleted **COMPLETELY**. A stub "see there / lives in knowledge / moved" is
  forbidden (rules/present-not-history.md). Findability comes from the SoT home + index, not a
  stub.
- All tool mechanics (curl / REST / field IDs / SDK call / auth) went into the tool's home; only
  a **link** remains in the process doc / skill. "Keep minimal" ≠ "leave some mechanics" — for
  tool mechanics the minimum is zero, a link.
- No "was / became" in the artifact itself (history — git log + ADR).

## 3. Grep-closure (proof, not faith)

- `grep -rn '<old-path>' knowledge/ rules/` = **0** (except ADR history). Run it, be sure.
- All inbound links to the moved thing rewritten **in lockstep**: `@`-includes in skills,
  pointers, backstops, self-learning.
- Touched a block that must stay identical across paired files → the edit is identical in both +
  any sync check passes.

## 4. Reading source

- If the moved fact was read through a tool / fetch — the content is **complete, not truncated**
  (no `…`, no pagination, no cutoff). A truncated read as a source of truth is not to be trusted
  (rules/grounding.md).
