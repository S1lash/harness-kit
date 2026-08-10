# Self-Learning Protocol (solo)

> How the agent captures durable knowledge and routes it to its one home. A **rail of thinking, not
> a classifier**. Decide "whether to save and where" by **method**, not a table row. Solo mode:
> auto-save silently, notify in one line. Never ask "should I save this?".

## When to capture

**Reactive** — the person corrects you ("no, use X"), confirms a non-obvious approach ("yes,
exactly"), or chooses between alternatives with a rationale.

**Proactive** — during work, auto-save: a *discovery* (how something actually behaves vs docs), a
*pattern* (same approach 2+ times), a *gotcha* (surprising / caused a retry), an *architecture
insight* (a design choice / dependency not documented). Archetypes that train *what matters*, not a
closed list.

Silent ≠ careless: before saving re-check — durable abstraction (not a task particular)? right SoT
home? After an "ok", re-check the fact and home yourself ("yes" ≠ being right).

## Method — whether to save and where

First: the **canon question** (rules/sot-dry-srp.md → home-by-object): about the object itself / our
process with it / a callable automation over it? → object's home / a topic domain **by link** / a
tool. Then in order:

1. **Durable abstraction or a task particular?** Particular / temporary / a value-from-a-source →
   NOT into knowledge. Only reusable, outlives-the-task material goes in. Run the noise filter.
2. **One SoT home, by the object.** One canonical place; needed elsewhere → a link, not a copy.
   - Save **moves** a fact → delete the old spot completely (no tombstone-stub), rewrite inbound
     links in lockstep, `grep` of the old path = 0 (doctrine/harness-edit-checklist.md).
   - Home file exists → read it and **write into the right place**, don't blindly rewrite whole. Two
     facts diverge → reconcile to what's true NOW, don't append "was / became".
3. **Scope → home:** durable understanding worth reusing → `knowledge/` (matching domain + a line in
   its `_index`); work-history worth surviving sessions (a plan, research, a named multi-session
   effort) → `activities/` (doctrine/knowledge-discipline.md). For preferences, split by durability:
   - **A durable presentation / identity / communication preference** (who the person is, how they
     want information presented) → `profile.md` — the grown identity / calibration layer, hot every
     session.
   - **A raw in-the-moment correction** → `corrections.jsonl` (agent-managed, append-only, invisible
     to the person — the agent reads it to stay consistent; the person never edits it). A signal that
     recurs and proves durable is distilled from here INTO `profile.md`.
   - **Never the agent runtime's own memory store.** It is scratch, invisible to every other runtime
     and (in Claude Code) to every other folder — `rules/multi-agent.md`.
4. **Deep systemic knowledge** (a subsystem's model, flow, behaviour) → Model + Method + Pointer, not
   Snapshot (doctrine/deep-knowledge-pattern.md). A flat snapshot goes stale and breaks on an
   unfamiliar case.

## Request to add to knowledge — critical gate (reactive)

"Add this pattern / example / case" is **NOT a command to execute**, but an entry into a critical
gate: the harness protects knowledge quality. First move is to **evaluate, not add** (first match
stops):

1. **Already covered?** → decline gently, show what covers it (DRY).
2. **Similar but not 1:1?** → **extend the existing one** (Reuse before invent).
3. **Narrow / one-off / a hack?** Doesn't generalize → not canon. At most a reference marked "an
   example, not an etalon".
4. **Durable, reusable, genuinely new, not covered?** → add by the method above.

**Always justify** (added / extended / declined why). The person can override, but the harness
**first pushes back with a reason**: knowledge quality > the wish to add.

## Noise filter — what NOT to save

- **Code snapshot (the main filter — every save).** Values owned by code / config: field numbers,
  enum members, method names / signatures, predicate expressions, SQL, line numbers. Code is their
  SoT; copy them and the note **lies** when the code changes.
  - **Snapshot test:** "if this code / config changes next quarter, does the note become wrong?" If
    yes — save a **pointer** (which file / class / method owns the truth, by name) + the **durable
    why** (a decision / naming convention / invariant / non-obvious cross-file mechanism).
  - **A method / class name as a POINTER is OK.** "Logic of X lives in `FooService.handle`" is a
    pointer (where to look). A snapshot is the body / signature / value. Don't drop a useful pointer
    out of fear of the filter.
- **Unverified inference is a hypothesis, not knowledge.** Inferred from reading code / "it compiled"
  but not confirmed by a run / test / source → belongs in the task, not standing knowledge; a wrong
  hypothesis actively misleads. Especially infra facts (which DB, what's cached, protocol, port) —
  verify against config / code in full.
- **Task-specific / a hack / a special case — not canon** (biases the model toward it). Needed as a
  reference → one line, explicitly "an example from task X — NOT an etalon".
- **Ticket-context notes inside a fact** — noise and bias; history lives in git.
- Standard language / framework behaviour in official docs. One-off debugging steps. Things already
  captured elsewhere.

## End-of-session extraction

Before ending a meaningful session (architecture, research, planning, debugging — not a quick Q&A),
scan for uncaptured corrections, confirmations, decisions, discoveries. Route via the method above.
