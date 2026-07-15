# Single Source of Truth (HARD RULE)

One fact — one place — one owner. Applies to ANY artifact: docs, a task, code, a knowledge note, a
mapping, a convention. Any project, any session.

- **SoT.** Each fact has one canonical place. Needed elsewhere → link, not a copy.
- **DRY.** Tempted to copy → link. A duplicate = two sources of truth that will diverge.
- **SRP.** Each module / document / section / skill has one responsibility and one owner. Don't smear
  responsibility across files.
- **The home of a fact — by the object it's about (SRP for knowledge; analogy — OOP).** A fact about
  the object lives in that object's home. A process / use-case artifact (how WE apply the object)
  describes ITS OWN thing and **links** to the object's home — like an OOP client references, doesn't
  copy internals. Three layers, always separate:
  - **Object-in-itself** (how it's built) → its own home (durable subsystem → its knowledge home;
    external tool → its tool home).
  - **Automation over the object** (a callable verb — script / wrapper) → its own catalog + narrative.
  - **Process / use-case** (how we apply it) → a topic domain, **by link** to the object's home.
  Anti-pattern: an external tool's field IDs / auth / API mechanics inside a process doc or skill
  instead of a link to the tool's home.

  **Where to put ANY fact — one question:** "about the object itself / our process with it / a
  callable automation over it?" → **object's home** / **topic domain by link** / **tool**. Map of
  homes → `knowledge/_index.md`; moving a fact → doctrine/harness-edit-checklist.md.

Check before creating any artifact: "does this fact already live somewhere? am I linking or copying?".
Copying → stop, justify to the person. Conscious explicit exceptions allowed.

## Home boundary — base vs project repo

> Applies if your setup has a planning base plus separate project repos (this etalon: a base
> `harness/` alongside sibling `projects/`, each an independent repo). Single flat project → ignore.

Decide **scope** first, then nature. **Order matters — cross-cutting / general first, else the fact
settles in one repo and becomes invisible to others:**

1. **A relation / contract BETWEEN projects** (even if it names one's code element) → **base**.
2. **Externally observable behaviour / role / contract of a component** → **base** cross-cutting home.
3. **A general practice applicable to MANY projects** → **base** engineering knowledge. ⚠️ dev-only ≠
   automatically the repo. Test by applicability: "many projects — or specific to THIS one?" → many →
   base; this one → repo.
4. **Only about ONE project's code / implementation** (its code element, a dev trap in its code, a
   repo-specific convention) → **the repo's own `.claude/`**, filed by the nature of the fact.
5. **Not clear** → **ask the person**. Don't guess.

**Home is by the nature of the fact, NOT where the session is open:** in a repo but cross-project →
base; in the base but about one repo's internals → the repo. Repo not cloned locally → write to the
base cross-cutting home with `<!-- internal, move to repo when cloned -->`.
