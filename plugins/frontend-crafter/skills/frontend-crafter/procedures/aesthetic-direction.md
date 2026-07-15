# Aesthetic Direction — committing before hi-fi

*Pin type, color, density, radius, and direction as a deliberate commitment before drawing pixels — never drift into them mid-build.*

Fires during GROUND & AUTO-DIRECT (`SKILL.md` step 1g, greenfield/ambiguous provenance) — the highest-
leverage decision in the whole pipeline, made once, up front, and then held for the rest of the build.
Improve-existing skips this entirely (the existing system's tokens win, auto-direction
is suppressed); handoff-export skips it too (the export already decided).

## What gets committed, in order

1. **Register** — `brand` (the design IS the product — expressive, differentiated) vs `product` (the
   design SERVES the product — restrained, gets out of the way). Read from the brief's subject and
   audience; ambiguous → ask, don't guess.
2. **Direction** — one of the catalog entries in `directions/_catalog.md`, selected by the deterministic
   rubric there (subject-signal → candidate set → register gate → exclude saturated lanes →
   anti-repetition bias against `design-memory.jsonl` → tie-break hash, logged). Any direction keyword
   already pinned by the user skips the rubric entirely — it's a hard pin, not a
   suggestion to weigh.
3. **Type** — display + body pairing per the direction's seed suggestions in `directions/{name}.md`,
   verified against `bans.json`, logged to `design-memory.jsonl` for recency diversity. Full recipe:
   `reference/type.md`.
4. **Color** — OKLCH-seeded palette (named tokens, fg/bg pairs recorded for later contrast lint). Full
   recipe: `reference/color.md`.
5. **Density & radius** — set alongside the pre-build dials (`DESIGN_VARIANCE` / `MOTION_INTENSITY` /
   `VISUAL_DENSITY`, 1-10 each) per `reference/dials.md`. Density and radius follow the direction's
   defaults unless a wish pins them.

## Why this is a gate, not a suggestion

Every axis decided here gets written into `design_plan` with its source tag (`pinned` / `auto` /
`bias-adjusted`) before BUILD starts. Drifting into a font choice or an accent color
mid-build — instead of deciding it here — is exactly how a design ends up incoherent: three near-black
grays, two competing accents, a headline font picked in one component and abandoned in the next.
Committing once, in `design_plan`, and then building strictly against it is what keeps the whole surface
feeling like one system.

## Output

All five decisions land in `.crafter/design-plan.md` (schema: `reference/pipeline.md`)
before code generation begins. If the user vetoes an axis after seeing the plan, only that axis is
re-run through its rubric — the rest of the commitment stands.
