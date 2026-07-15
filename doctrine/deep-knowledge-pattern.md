# Deep-knowledge pattern: Model + Method + Pointer, not Snapshot

> On-demand authoring meta. Read when documenting deep systemic knowledge (a subsystem's
> model, a flow, a behaviour) so it doesn't go stale and grows on its own. Behavioural parent
> — "Rails, not frames".

## When to apply

Knowledge fits this pattern when it has **all** of these traits:
- **The model is stable, the specifics are volatile** — the concept is stable, the values
  (enums, names, thresholds, lists) change over time.
- **The truth lives in a source** — code, a wiki, a config — maintained not by us or not here.
- **Needed by several contexts / roles** — including those without code access.
- **It will be extended** — coverage grows; it can't be "closed" in one act.

**Doesn't fit** (hold as an ordinary note): a one-off task fact, a temporary workaround, a pure
procedure (a skill).

## The four parts

1. **Model (the stable core — the rails).** How the subsystem is built conceptually: entities,
   relations, invariants, principle of operation. Doesn't change when a new enum value is added.
   One home (SoT/SRP) — the model in one file, others link.
2. **Method (how to derive the current truth — a rail).** How, for an **unfamiliar** case, to
   find a fact that isn't in the doc yet. This is the main value: the doc need not know
   everything — it teaches how to find out. From code: the entry points (which classes / grep
   patterns / where the enums live). Without code: where the truth is (a wiki page, the person
   who owns the area, this model).
3. **Pointer (SoT — not a snapshot).** A link to the source of truth for volatile values: a
   short path in code and/or a wiki page. **Whole lists of enums / values are not copied** — a
   copy is a hidden snapshot that diverges from the source. Format: `(code: <short path/class>;
   no access → wiki <page>)`.
4. **Catalog (extensible, optional).** If the knowledge = a set of same-shaped facts, keep an
   **open illustrative table**, seeded with a few rows. Mark it: "an illustration of the method,
   not a classifier; SoT is the source; the list is open." Every row is checkable by the Method.

## Anti-patterns

- ❌ **A frozen snapshot** — copied a list of values "for convenience". Goes stale; two sources
  of truth. → Pointer, not snapshot.
- ❌ **A brittle lookup table** — a closed table as the only source. Breeds lookup-behaviour,
  breaks on the unfamiliar. → Model + Method; the table only as an open illustration.
- ❌ **Narrow one-off tuning** — documented exactly your case, no model / method. → derive the
  Model + Method, your case = a seed row.
- ❌ **Three homes of one entity** — the definition in a glossary, in the domain doc, and here.
  → one deep home, the rest link.

## How it grows

Through the self-learning method. Only a **durable abstraction** goes into a deep doc: a new
model invariant, a new nuance of the method, a new catalog row (derived by the Method, not
guessed). Particular / temporary / a value-from-a-source — not here. After agreement re-check
yourself ("yes" ≠ being right): is the fact durable, is this the right home.
