# Decisions — durable choices with rationale (ADR home)

> Home-by-object: a decision is knowledge, so it lives here. Each entry records a durable choice —
> **what was chosen · alternatives considered · why this one**. Append-only; entries accrete, they
> aren't rewritten.
>
> **Present-not-history EXCEPTION** (rules/present-not-history.md): the evolution and rationale of a
> decision IS the content here. This is the one place "why we chose X over Y" is kept — everywhere
> else states only the current chosen state and links here for the why.

## 2026-08-23 — One canon list, in AGENTS.md; CLAUDE.md imports it

**Chosen:** `AGENTS.md` carries the canon list and is the contract every runtime reads.
`CLAUDE.md` is one `@AGENTS.md` import plus Claude-only notes. Installers point each runtime's
global entry at `AGENTS.md` rather than enumerating rules.

**Alternatives considered:** keeping full twins and checking them for parity, as before; making
`CLAUDE.md` the source and `AGENTS.md` the derived copy.

**Why:** the harness is agent-agnostic, so the agnostic file is the source and the runtime-specific
one is the adapter — not the other way round. The parity check existed only because we had written
the list twice; removing the duplicate removes the failure it was watching for, which is better
than watching for it. Claude Code reads `CLAUDE.md` and not `AGENTS.md`, and its own documented
answer to that is an import rather than a copy. A side effect worth having: relative imports resolve
from the file that contains them, so a global entry pointing at `AGENTS.md` picks up every rule
automatically and adding a rule no longer means re-running the installer anywhere.

## 2026-08-23 — An update replaces the kit's paths; it never merges

**Chosen:** `.engine-manifest.yml` declares every path as the kit's or the person's, and
`tools/update.py` checks out only the kit's from the `harness-kit` remote. Paths the kit dropped
are listed as `retired:` and deleted from every base on every update. Written in python rather than
shell.

**Alternatives considered:** merging from an upstream remote; a `.template`-suffix seed contract
extracted by a release step; a bash updater mirroring the engine this is modelled on.

**Why:** the people running this will not track the kit's repository and cannot resolve a merge
overlap in a file they did not write. Replacing a declared set of paths makes an update an ordinary
save in their own base — revertible, explainable, and unable to conflict. Retirement is the half a
copy cannot express: the updater copies what the kit HAS, so without it every file the kit ever
removed sits on every base forever, offering a contract nothing honours. The `.template` suffix and
its release step exist to extract a public skeleton out of a live private instance; this kit is
authored public, so its seeds ship pristine under their live names and the whole extraction step is
unnecessary. Python over shell because the engine it copies had to defend a python-to-bash boundary
against CRLF-mangled paths and Windows rewriting `<ref>:<path>` — both of which turned a broken
update into a silent success. Removing the boundary removes the class, and one file runs everywhere
a shell pair would have to be kept in step.

## 2026-08-23 — Every project carries its own contract, written by the agent

**Chosen:** each project has `AGENTS.md` (the contract), a `CLAUDE.md` importing it, and its own
`<project>/.claude/knowledge/` and `<project>/.claude/decisions.md`. The agent writes it when the project is born and
repairs it when it drifts, unasked. It holds only what the code cannot tell you.

**Alternatives considered:** relying on the base's knowledge home for project facts; twin
CLAUDE.md/AGENTS.md files; asking the person whether they want documentation.

**Why:** a project is opened cold — a phone, a fresh clone, a headless run — with no history to
lean on. The person will never write this, will not notice it missing, and will not connect a bad
session to its absence. Keeping project facts in the base instead scatters them away from the code
they describe and makes them invisible to anyone who has only the project. The import bridge rather
than twins because Claude Code reads `CLAUDE.md` and other runtimes read `AGENTS.md`, and two
copies of one contract drift. The what-the-code-cannot-tell-you filter is what keeps the file from
becoming a stale restatement of the layout, which is worse than nothing because it gets believed.

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
