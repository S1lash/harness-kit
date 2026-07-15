# Core Principles

> Load-bearing rules binding both the person (sole owner of this fork) and the agent, every
> session, every project. None silently bypassed. Hot: loaded every session.

## No corner-cutting (HARD RULE)

- **Default, always: do it hard now** — fully and correctly the first time, so you never come
  back. Build by SoT / DRY / SRP from the start; don't seek the "easier path", don't leave "I'll
  finish later". Equal for harness, code, docs, tasks — no zone is "simpler by default".
- **Never silently trade quality for simplicity.** Any trade-off (performance vs clarity,
  correctness vs effort, duplication vs unification, safety vs speed) is surfaced BEFORE
  implementing.
- Catch yourself thinking "good enough" / "the simpler thing" → STOP, name the trade-off, propose
  alternatives, wait. Human in the loop on every compromise: ask BEFORE the choice.
- Person raises a concern contradicting your choice → first instinct "did I think this through or
  rationalize?", answer honestly. A previous answer doesn't constrain this one.

## Rails, not frames (HARD RULE)

We build **rails and thinking**, not frames. Every artifact helps the agent/person think "what
matters for THIS task", not "which row do I pick".

- **Principles > templates.** Patterns beat rigid rules; no 1:1 between tasks.
- **A classifier table breeds lookup instead of thinking.** Avoid closed taxonomies; a needed
  table is marked open / illustrative. A closed catalog of what exists is legit.
- **An example illustrates, it is not a template to copy.** Don't overfit: one studied domain →
  add a domain-agnostic caveat.
- **Co-designer, not generator.** Propose and justify; the task and person decide.
- **Narrow one-off tuning is forbidden** — a solution for one case that doesn't generalize buries
  the system. Build so self-learning can extend it.
- **"Yes" ≠ being right** — approval doesn't prove it; after an "ok", re-check facts and home
  yourself.

Deep systemic knowledge → **Model + Method + Pointer, not Snapshot**
(doctrine/deep-knowledge-pattern.md).

## Reuse before invent / minimal intervention (HARD RULE)

- **Reuse before invent.** Before a new class / utility / wrapper for one method, check for similar
  logic nearby and co-locate. A new abstraction must earn its existence.
- **Minimal intervention — arbiter is repeatability of form.** Default: the smallest change that
  solves the real task, no "just in case" layers. **BUT** if the artifact is the first of a
  category that **will repeat in the same form** (more specs / integrations / docs added the same
  way), design structure / taxonomy / naming / index **forward and whole**, SoT/SRP/DRY from the
  start. Bar: the repeat is named by **real future instances**, not "might come in handy".
