# Direction Catalog — auto-selection rubric

*Deterministic, auditable, logged — not model self-report (dossier §4e's critique of the fake RNG
applies here: a step that isn't a real, reproducible computation isn't a real step). This file is
read whenever `direction` is unpinned in `design_plan` (S2); a pinned direction skips straight to
loading that direction's file.*

## The four directions

`brutalist` · `minimalist` · `soft` · `editorial` — each a `directions/{name}.md` delta on
`_base.md`. There is no separate "app" direction file: product-register briefs that would
intuitively reach for "an app aesthetic" resolve to `minimalist` narrowed by the register gate
(step 2 below) — restrained type, restrained motion, restrained color, exactly minimalist's
existing profile under the product register. Don't invent a fifth file to hold this; it's a
register variation of an existing direction, not a new aesthetic.

## Selection pipeline (run in order, first-to-last narrows the candidate set)

### 1. Subject-signal → candidate set

Illustrative and extensible — a starting map, not a closed classifier. Read the brief for
subject-domain signal and seed the initial candidate set:

| Subject signal | Candidate set |
|---|---|
| artisan / food / craft / local business | `{soft, editorial}` |
| fintech / dev-tool / dashboard / SaaS product | `{minimalist}` (register gate narrows further) |
| edgy / music / dev-culture / underground | `{brutalist}` |
| luxury / fashion / publication | `{editorial, soft}` |
| unknown / no clear signal | all four |

If the brief pins the direction explicitly (S2), skip this whole file and load that direction's
file directly — pinned axes never enter the candidate-set logic.

### 2. Register gate

`register` (`brand` | `product`, from `design_plan`) adjusts the set:
- **Brand** (design IS the product — landing, portfolio, campaign) widens the set: brutalist and
  soft become viable even for subjects that leaned minimalist, because the register itself
  tolerates and rewards a stronger stylistic commitment.
- **Product** (design SERVES the product — dashboards, admin, tools, data tables) narrows the set
  toward `minimalist`, regardless of what the subject-signal step suggested. A dashboard for an
  edgy music brand is still a dashboard first — apply the brutalist *touches* (accent color, one
  typographic choice) within a minimalist-disciplined structure rather than a full brutalist
  build. If narrowing would eliminate every candidate, keep `minimalist` as the floor.

### 3. Exclude saturated lanes

Drop candidates — or specific palette/type choices within a surviving candidate — that match a
named saturated AI lane (dossier §1a/§3c), unless the brief explicitly demands it:
- editorial-serif-default (display serif + italic + mono-labels + ruled-separators bundle) —
  `editorial.md` itself carries this warning; don't let it win the tie-break by default weight,
  only by genuine subject fit.
- cream `#F4F1EA`-class + terracotta — checked mechanically via `bans.json`'s AI-cream OKLCH range
  wherever `soft.md` or `editorial.md` palettes are being finalized.
- near-black + single acid accent as a reflexive "modern tech" default — if `brutalist`'s Tactical
  Telemetry archetype is chosen, make sure it's chosen for a reason (subject fit), not because it's
  the fastest way to look "techy."

### 4. Anti-repetition (unpinned axes only)

Read `design-memory.jsonl` (S9), scoped to briefs similar to the current one (`brief_gist`
matching). Drop any surviving candidate whose direction (and, within `soft`, whose vibe archetype)
matches the most recent N entries for similar briefs. This applies **only to unpinned axes** — a
user-pinned direction is never overridden by anti-repetition bias, only auto-selected ones.
If dropping the recent match would empty the candidate set, keep the least-recently-used
candidate instead of reintroducing the excluded one.

### 5. Tie-break

If more than one candidate survives steps 1–4: compute a deterministic hash of the brief string,
modulo the finalist count, to index into the (stably-ordered) finalist list. This must be a real
tool call or script execution, not the model performing arithmetic in its head and self-reporting
the result (dossier §4e — the exact failure mode of the fake RNG). **Log the resulting index and
the brief string to `design-memory.jsonl`** so the pick is reproducible and auditable after the
fact, and so future anti-repetition passes (step 4) have data to work from.

### 6. Governance

The four directions above are the full canonical set. A fifth (or further) direction is added only
by the owner, and only when it:
- carries a complete `_base.md`-conformant delta (identity, type, color, shape & space, motion
  personality, signature technique) — not a partial sketch;
- passes a golden-brief eval (S15) demonstrating it's reachable through the selection pipeline for
  a real subject signal, not just theoretically definable;
- doesn't overlap an existing direction closely enough that it's really a vibe-archetype variant
  (like `soft.md`'s three archetypes) rather than a genuinely new direction.

No ad-hoc taste drift — a direction added without going through this governance step is exactly
the DRY/consistency risk `_base.md` and this catalog exist to prevent.

## Inspiration-gallery taxonomy (reasoning aid, not a fetch target)

These galleries are encoded as *what good looks like per category* — they're JS SPAs the agent
generally can't fetch (dossier §5 Bucket A), so this table is memory, not a live source. Use it to
calibrate a direction's concrete choices against real precedent for the relevant slice, and to
know which category to reach for when reasoning about a specific section or component rather than
the whole page.

| Gallery | Category | Use when reasoning about |
|---|---|---|
| navbar.gallery | Navbars | Header/nav composition within any direction |
| cta.gallery | CTA sections | The final-CTA section's composition (any direction) |
| landing.love | Landing pages | Full-page narrative sequencing, mostly `soft`/`editorial`/brand-register `minimalist` |
| saaspo.com | SaaS sites & sections | Product-register `minimalist`, pricing/feature/hero patterns |
| rebrand.gallery | Brand & rebrand identity | Brand-register work across any direction, especially `brutalist`/`soft` |
| motionsites.ai / appmotion.design | Motion-forward sites / app interaction | Calibrating a direction's motion personality against real precedent |

`saaspo` and `navbar`/`cta` are already sliced by page/section type, which maps directly onto
mode + direction reasoning — pull them into thinking when a specific section composition feels
underspecified by the direction file alone, not as a substitute for the direction's own rules.
