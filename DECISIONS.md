# Decisions — the kit's own durable choices

> Why harness-kit is built the way it is: what was chosen, what else was considered, and why this
> one. Kit-owned, so an update carries it to everyone and it never freezes at somebody's clone date.
>
> The PERSON's decisions live in their own `knowledge/decisions.md`, which no update touches. Two
> files because they have two owners — a kit fact in a person's file is a copy no update can ever
> correct (`doctrine/kit-ownership.md`).
>
> **Present-not-history EXCEPTION** (`rules/present-not-history.md`): the evolution and rationale of
> a decision IS the content here. Everywhere else states only the current state and links here.

## 2026-08-30 — Portable scope is read from the manifest, not judged

**Chosen:** `rules/cross-platform.md` derives its two tiers from `.engine-manifest.yml`. Tier 1 is
`engine:` plus `template:` — exactly what an update writes onto somebody else's disk — held to the
letter and gated by `tools/check_portability.py`. Tier 2 is everything the person wrote, held to the
spirit and never gated.

`template:` beats `exclude:` where they overlap. A seed that lands inside the person's space is
still something the kit ships: `update.py` seeds every template regardless of `exclude:`, so reading
the overlap the other way would let one manifest mean two different things to its two readers — and
the files it ships would reach strangers unchecked. Where a seed lands says nothing about who wrote
it.

**Alternatives considered:** a hand-kept list of "files that must be portable"; a marker comment in
each file declaring its tier; holding the whole repository to one standard.

**Why:** the distinction that matters is already recorded, and recording it twice is two truths that
diverge. A second list would need updating in the same edit as the manifest and would silently not
be; a marker comment puts the answer in the file being judged, which is exactly where a wrong answer
is least visible. Holding everything to one standard is the failure both directions: gate the
person's own scratch script and the gate becomes noise they route around, exempt the kit's installer
and the rule stops covering the only files that reach a stranger.

The consequence worth naming: adding a path to `engine:` silently widens what the gate checks. That
is intended — the manifest entry IS the decision to ship it — but it means a release can fail on a
file the author never thought of as shipped. That failure is correct and is the point.

## 2026-08-30 — Canon clauses have IDs, not section numbers

**Chosen:** the machine-checkable clauses of `rules/cross-platform.md` are named `[CP-1]`..`[CP-6]`
in the prose, cited by every rule in `tools/lib/portability.py`, and bound in both directions by
`check_clause_ids` in `check_kit.py`: a clause the canon defines that no mechanism enforces fails,
and a gate rule citing a clause nobody wrote fails.

**Alternatives considered:** citing section headings; citing section numbers; citing nothing and
letting each gate message stand alone.

**Why:** a gate has to be able to say which promise was broken, or the person reading the failure
has only a regex and no contract. Headings and numbers both move — `present-not-history.md` requires
rewriting a rule whole, so paragraphs are expected to move — and a citation that rots points
confidently at the wrong paragraph, which is worse than none. An ID is a name the rewrite carries
along.

The half that is easy to miss is the reverse direction. Enforcement drifting out from under a clause
is the failure nobody notices: the rule still reads as guarded, the gate still passes, and the only
evidence is a check that no longer exists. Binding both ways makes deleting a rule from the scanner
a release failure until the clause is deleted from the canon too.

**Not generalized further on purpose.** Only `cross-platform.md` carries IDs today, because only its
clauses are machine-checkable. A rule about judgement gains nothing from a citable name and would
gain a maintenance obligation.

## 2026-08-30 — No symlinks anywhere in the kit

**Chosen:** neither installer creates a symbolic link. Global agent wiring is a text block written
into the runtime's own entry point (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, Cursor user rules)
naming the base by path; everything else is a copy.

**Alternatives considered:** linking the entry points at the base, which is what the kit did;
linking on POSIX and copying on Windows; keeping the link and documenting the Git Bash environment
variable that makes it real.

**Why:** a symlink is four different objects. Git Bash writes a text stub containing a path unless
`MSYS=winsymlinks:nativestrict` is set, so the file looks right and reads as garbage. Windows needs
Developer Mode or elevation to create one at all. A dangling link is invisible to PowerShell's
`Test-Path`, so a repair step reports the target missing and creates it beside the broken link.
`Remove-Item` on a directory link deletes the directory it points at. Each of those is a silent
half-install on a machine the author cannot see, and the person hits it as "my agent stopped knowing
about my base" with nothing to read.

The thing given up is real and small: an edit to a linked file used to be live everywhere at once,
and a copy has to be rewritten by the updater. That is what the updater is for — it replaces kit
paths wholesale on every run — so the property was already being delivered by another mechanism.
A platform-agnostic kit does not get to depend on the one filesystem primitive that means something
different on each platform.

## 2026-08-23 — Safety is a sibling of git-safety, and authority does not relax it

**Chosen:** `rules/safety.md` — a hot rule covering irreversible and outward-facing actions that
are not git's: reading is free, look at the target before acting, deletions are confirmed, changing
anything outside the base needs approval, an external system is never touched without confirmation,
and an approval covers only what it covered. It names `git-safety.md` for the git half and is named
by it; neither repeats the other.

**Alternatives considered:** folding these into `git-safety.md`; leaving them scattered across
`harness-stewardship.md` and `working-method.md`, which is where they were.

**Why:** the discriminator in `harness-stewardship.md` already said "external or irreversible → ask"
and then never said what that meant, so it was a rule an agent could believe it was following while
deleting something. Folding it into git-safety would put two subjects in one file and make the
force list harder to find; scattering is what we had, and scattered safety is read as advisory.

The part worth arguing: an agent that owns a base holds the owner's authority
(`rules/device-sync.md`), so the asking steps become deciding steps — but three things do not
relax. Look-first binds because it is not a courtesy, it is how you discover the instruction was
written blind. Scope binds because authority over a base is not authority over everything the base
can reach. And an outward-facing action is never made free by the absence of a witness — the
absence is exactly what makes it unreviewable, which is why the autonomous owner records it in the
save message instead.

## 2026-08-23 — Offering discipline, but no catalog of capabilities

**Chosen:** the concierge pillar in `rules/harness-stewardship.md` gains how to offer — by
judgement, never by keyword; silence beats an offer that adds ceremony to work that did not need
it; one line, never a menu. No catalog file listing what the agent can do.

**Alternatives considered:** a `tool-suggestions.md`-style rule carrying a table of capabilities,
which is what the harness this was taken from does and does well.

**Why:** the table works there because one person maintains it against the skills they installed.
In a kit it would be a second source of truth for something the runtime already knows exactly — the
agent's own capabilities are in its context, and a shipped list would be wrong on the first base
that installs anything. The kit's own canon forbids precisely this. What generalises is not the
catalog but the trigger: the discipline moved, the table did not.

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

**What replacement and retirement still cannot express, and what carries it instead:** a path in
the person's space that must move is declared under `migrations:`; the kit's own address is
reconciled from the manifest on every update, so moving the kit is staged rather than sudden; and
global agent wiring is detected and reported. What remains genuinely out of reach is content
INSIDE the person's files, and the frozen kit-half of a seed — both in `KNOWN-LIMITS.md`.

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

## 2026-08-23 — Migrations are declared data, convergent, and have one verb

**Chosen:** a `migrations:` section in the manifest, currently one verb — `move <from> -> <to>`,
optionally carrying a note for the person. It runs after the checkout on every update, is
idempotent by construction, and refuses a verb it does not recognise. No ordered chain, no ledger.
Alongside it, two reconciliations that are not migrations at all: the kit's remote is set to the
address the manifest publishes, and stale global agent wiring is reported.

**Alternatives considered:** the ordered chain with `structural`/`heal` kinds and a ledger that the
engine this kit is modelled on uses; putting the logic in `update.py` as code; doing nothing and
forbidding the kit from ever moving anything in the person's space.

**Why:** the updater replaces itself mid-run while its old copy is already in memory, so code added
to it takes effect one update late — the manifest is re-read from disk after the checkout, so data
lands in the same run it ships in. A ledger needs a valid starting point that a base cloned long
ago has never had, and an ordered chain is strictly worse for a base that has been dark for a year;
re-running idempotent declarations converges from any version. One verb because a move is the case
that actually exists, and refusing an unknown verb rather than skipping it means a kit that adds a
second one never silently believes a change landed. Doing nothing was the previous position, and it
made "the kit must never rename anything a person owns" a permanent constraint rather than a choice.

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
