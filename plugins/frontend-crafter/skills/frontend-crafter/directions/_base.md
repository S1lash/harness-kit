# Direction Base — the shared spine

*Every file in `directions/` is a DELTA on top of this base. Read this once per session, then
read only the single direction file that was selected (`_catalog.md` owns selection).*

## Why directions exist

The model's default output — absent a committed choice — regresses to the mean of its training
distribution. That mean has a name: warm cream + high-contrast serif + terracotta; near-black +
one acid accent; broadsheet hairline-rules + zero radius. These aren't bad aesthetics, they're
just *everyone's* aesthetic when nobody chooses. A named, pre-committed direction is the fix: it
gives the model a specific enough target that hedging toward the safe average becomes impossible.

**The durable principle:** commit to a named direction before writing a line of code. The default
IS the slop — not because any single default choice is ugly, but because "no choice" and "the AI
average" are the same output.

## What a direction file contains (and what it doesn't)

Each `directions/{name}.md` is a delta: it states only what's specific to that direction —
type pairing, palette approach, radius/shape logic, motion personality, one signature technique.
It does **not** restate:
- **Bans** — `bans.json` is the single mechanical ban list (fonts, regex rules, contrast minimums).
  A direction file never repeats a banned font or re-derives a contrast minimum; it points here.
- **Contracts** — performance, a11y, forms, dark-mode, security, CSS architecture live in
  `reference/contracts/*.md` and apply identically regardless of direction.
- **Mode rules** — landing/app-ui/component structure lives in `reference/modes/*.md`. A direction
  answers "what does this look like," not "what sections does a landing page need."
- **Motion mechanics** — durations, easing curves, the frequency table for "should this animate
  at all" live in the motion reference set. A direction states its motion *personality*
  (e.g. "invisible" vs "spring-physics") and picks values from that shared vocabulary, it doesn't
  re-derive timing theory.

If a rule would read the same in two direction files, it belongs in this base or in a shared
reference file, not copied into both. Two files stating the same ban is the exact drift this
architecture exists to prevent (dossier §4e, §4c caveat).

## The perishability guard

Every exact font name, hex value, and cubic-bezier in a direction file is a **perishable example**
of a durable principle, not the principle itself, and not canon:

- "Pair a macro grotesque with a micro monospace" is durable. "Neue Montreal + JetBrains Mono" is
  this month's illustration of it.
- "Never absolute black, use a warm-tinted charcoal" is durable. "`#111111`" is one value that
  satisfies it.
- "Custom ease-out curves, never CSS built-ins" is durable. The specific bezier control points are
  a snapshot.

Treat every concrete value in these files as a **seed suggestion**, swappable the moment it starts
reading as its own tell (exactly what happened to editorial-serif — see `editorial.md`). When
selecting a font or hex, follow the *shape* of the example (its role, its contrast axis, its
temperature) rather than copying it verbatim run after run — `reference/type.md` (S6) is the
positive selection method; this file only tells you the values are examples, not the recipe.
Log the actual pick to `design-memory.jsonl` so repetition across projects is visible and
correctable — this is what makes the perishability guard enforceable rather than aspirational.

## How a direction is invoked

A direction is selected by `_catalog.md`'s rubric — pinned by the user's own words, or chosen by
the subject-signal → candidate-set → register-gate → anti-repetition → tie-break pipeline. Once
selected, its file is the *only* aesthetic-direction content loaded into context for that build.
Never load two direction files into the same build — a direction is a committed choice, not a
blend (`SHAPE_CONSISTENCY_LOCK` / `COLOR_CONSISTENCY_LOCK` apply per-direction, never averaged
across two).

## Structure every direction file follows

1. **Identity** — one or two sentences naming what makes this direction unmistakable, and (where
   the direction has more than one internal archetype) which one to pick and why you don't mix them.
2. **Type** — role pairing (display/body/mono), the contrast axis between roles, seed font examples
   (perishable).
3. **Color** — palette approach (not a fixed hex list to copy) + seed values (perishable),
   temperature rule, what color is spent on.
4. **Shape & space** — radius scale, border logic, spacing personality.
5. **Motion personality** — the felt quality of movement (invisible / spring-physics / none), with
   concrete durations/easing drawn from the shared motion reference, not reinvented.
6. **Signature technique** — the one memorable, direction-specific move that makes output from this
   direction recognizable at a glance.

Everything else — bans, contracts, mode structure — is inherited silently from this base and the
shared reference files.
