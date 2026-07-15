# Knowledge & Activities Discipline

> On-demand authoring meta. How knowledge is organized so it grows healthily over years with
> zero curation by the person (the agent owns this — rules/harness-stewardship.md → pillar A).
> Two stores: `knowledge/` (durable understanding) and `activities/` (work worth surviving
> sessions). Routing between them is in rules/self-learning.md; this file owns the *structure*
> and *lifecycle*.

## Knowledge routing + growth rule

Where a fact goes is decided by object (rules/sot-dry-srp.md). How the container is shaped grows
under need, never ahead of it — the same rail at every level:

- **Start flat:** `knowledge/{topic}.md`. While an area is 1-2 files, no folder.
- **2-3 files of one area** → promote it into a subdir `knowledge/{theme}/` (move files with
  `git mv`). Don't create a theme-folder for a single file — that is premature nesting (4 folders
  for 4 files = ceremony).
- **A theme grows to 3+ files** → add `knowledge/{theme}/_index.md` (a map of the theme); the
  root index then points at the theme, not each file.
- **The master `knowledge/_index.md` is an index-of-indexes** — it points at domains / themes,
  which point at their files. Keep it in sync with disk (a new file → a line in its nearest map);
  a fact that fits no theme is a signal it's either cross-cutting (a higher home) or needs a new
  theme (add it to the map, then place the fact).

Pick a theme name from the existing set before inventing a new one — cross-consistency matters so
the same kind of fact lands in the same place every session.

## Activities discipline

An **activity** is a tracked unit of work — a plan, research, a named initiative, a multi-session
effort. It is born ONLY when the work is worth surviving across sessions:

- **Born:** multi-session effort / a plan or design being built up / research being gathered / a
  named initiative the person will return to. NOT per-chat, NOT for a one-off answer, NOT for a
  quick task that finishes in the same session with nothing durable left over.
- **The agent creates / updates it silently** as work proceeds, and adds / updates **one row** in
  `activities/_index.md` (name, one-line status, last-touched). The person is told plainly what
  was tracked; they never manage the file or the index themselves.
- An activity doc legitimately records status "was ❌ → became ✅" (it's a progress tracker, the
  present-not-history exception in rules/present-not-history.md) — it is not loaded into
  production model context.

## Anti-bias trigger — do NOT load history by default

By default, **do not read activities / past history** at the start of a turn. Loading the person's
prior context every turn biases the agent toward what was already thought, instead of reasoning
fresh on the current request.

Consult `activities/_index.md` **only on narrow signals:**
- the person says "we did", "last time", "continue…", "where were we", "pick up X"
- you are about to start something that clearly **overlaps an existing activity** (the same named
  initiative / area)

When you do consult it, surface it: "Checked your activities — found a relevant one: …". Absent
those signals, treat each request on its own merits.

## Lifecycle

- **Active** → the agent keeps the doc + its index row current as work proceeds.
- **Done** → move the doc to `activities/_archive/`, but **the index row stays** (marked done) so
  it remains findable. Never delete the trail.
- **Promotion:** when an activity produces a durable, reusable output (a design that settled, a
  learned model, a convention), **promote that output into `knowledge/`** at its proper home — the
  activity keeps the work-history, `knowledge/` gets the distilled truth. Don't leave durable
  understanding buried in a progress tracker where it won't be found.
