# Decisions — durable choices with rationale (ADR home)

> Home-by-object: a decision is knowledge, so it lives here. Each entry records a durable choice —
> **what was chosen · alternatives considered · why this one**. Append-only; entries accrete, they
> aren't rewritten.
>
> **Present-not-history EXCEPTION** (rules/present-not-history.md): the evolution and rationale of a
> decision IS the content here. This is the one place "why we chose X over Y" is kept — everywhere
> else states only the current chosen state and links here for the why.

## 2026-08-23 — The base is one repository, and everything built lives inside it

**Chosen:** a single repository whose root is the base. `projects/` sits inside it. A project moves
to its own repository only when the person asks, and `projects/_index.md` records that.

**Alternatives considered:** projects as a sibling folder outside the base (the previous layout);
git submodules; symlinks into separate repositories.

**Why:** a session opened from a fresh clone — a phone, a web session, an agent on a server — gets
exactly one repository and nothing else. Anything outside it does not exist there. Submodules leave
a non-technical owner stranded in a detached checkout the first time anything moves, and symlinks
survive neither a clone nor Windows. The cost is accepted knowingly: one history for the base and
the apps together, and a project cannot be made public without the base.

## 2026-08-23 — The base has one branch

**Chosen:** the person's base carries a single long-lived branch and no others. Branch-per-change
discipline stays, but only for repositories of code.

**Alternatives considered:** the general branch-first rule applied everywhere, as before.

**Why:** a branch is invisible on a phone and meaningless to someone who does not know the word.
Every extra branch in the base is a future "why is my phone showing something different", and the
person cannot diagnose it. Merges in the base are markdown the agent can read and reconcile, so the
protection a branch buys is not needed here.

## 2026-08-23 — Saving is proposed, not requested

**Chosen:** the agent brings the base up to date silently at session start, and proposes saving in
one plain sentence at the end of a chunk of work. After the first yes it keeps saving silently for
that session. Where nobody is in the loop, it saves on its own.

**Alternatives considered:** save only when the person asks (the previous rule); save fully
automatically with no consent at all.

**Why:** the owner of a base does not know the words for any of this and will not ask. Asking every
time is nagging; never asking takes the decision away from them. Splitting the two directions
resolves it — bringing changes in is not a choice anybody would make differently, so it is not a
question; sending work out is visible to them and stays theirs to allow. On a surface whose copy is
destroyed when the session ends, an unsaved session is simply lost work, which is what makes the
proposal urgent rather than polite.

## 2026-08-23 — The kit stays updatable; the line is drawn by path

**Chosen:** paths are owned either by the kit or by the person (`doctrine/kit-ownership.md`). An
update replaces kit paths wholesale and never touches person paths. The kit's own remote is kept as
`harness-kit`; `origin` is the person's private copy. Installing never deletes history.

**Alternatives considered:** fork-and-own with no upstream at all (the previous stance); merging
updates from an upstream remote.

**Why:** the kit is handed to people who will not track its repository and cannot resolve a merge
overlap in a file they did not write. Replacing a known set of paths turns an update into an
ordinary save in their own base — reversible, explainable, and impossible to conflict. Deleting
history at install destroyed the only link back to the kit and, on a second device, the person's
own past.
