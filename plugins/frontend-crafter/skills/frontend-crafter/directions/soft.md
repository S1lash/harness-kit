# Direction: Soft

*Delta only — inherits bans, contracts, and mode rules from `_base.md`. Fonts/hex/beziers below
are perishable examples (`_base.md` → "The perishability guard"), not canon.*

## Identity

Reads as a well-funded agency build — polished, considered, physically tactile without tipping
into glassmorphism cliché. Three internal vibe archetypes, **pick one per build, state it in
`design_plan.signature`**:

- **Ethereal Glass** — light, airy, translucent surfaces used deliberately (not the flat
  glassmorphism-default `bans.json` flags — the difference is restraint and purpose, not the
  technique itself).
- **Editorial Luxury** — closer to `minimalist.md`'s density but warmer, more generous motion,
  fashion-adjacent pacing.
- **Soft Structuralism** — geometric confidence softened at the edges; structure is still visible,
  but every corner is eased.

These are flavors of the same underlying system (shared type/motion mechanics below), not three
unrelated directions — the delta between them is mostly palette temperature and motion pacing, not
structure.

## Type

- A distinctive sans with real character (not a generic grotesque) for the primary voice, paired
  with a light-weight companion for secondary/supporting text — the contrast axis here is *weight*
  more than *family*, unlike minimalist's sans/serif split.
- **Seed examples** (perishable, verify against `bans.json`): Geist or Clash Display-class sans
  for primary, a light sans (Phosphor-icon-adjacent weight logic) for secondary. Follow
  `reference/type.md`'s selection method rather than reaching for the same pairing every time —
  this direction is at real risk of becoming its own tell if the same two faces recur.

## Color

- Palette skews warm-neutral with one confident accent; avoid the cream+terracotta saturated lane
  by name (dossier §1a/§3c) — soft does not mean "beige agency template." Verify seed backgrounds
  against `bans.json`'s cream tell the same way `minimalist.md` does.
- Depth comes from layered surface lightness (subtle elevation steps), not from drop-shadows piled
  on top of flat color — shadows here are soft and directional, part of the Double-Bezel signature
  below, not decorative afterthoughts.

## Shape & space

- Radius scale is generous and consistent — this is the one direction where rounding *is* part of
  the signature, so the scale must be deliberate (e.g. a 3–4 step scale from small controls to
  large containers) rather than one flat "rounded-xl everywhere" value.
- Spacing is calm, not cramped — mid-to-low `VISUAL_DENSITY` (3–6), enough room for the
  Double-Bezel nesting to read clearly.

## Motion personality

**Spring-physics reveals** — entrances carry weight and settle, not linear fades. Seed:
`translate-y-16 blur-md opacity-0` resolving over 800ms+ on entrance, using a custom bezier (seed:
`cubic-bezier(0.32, 0.72, 0, 1)` — direction-specific, distinct from the shared "state change"
curves used elsewhere) rather than a generic ease. Hover/interactive states stay snappy and
short — the weight is reserved for entrances and major state transitions, not every hover, per the
shared motion reference's frequency table (high-frequency interactions stay light regardless of
direction).

## Signature technique

**The Double-Bezel** — nested shells with concentric, proportionally-related border radii: an
outer container and an inner surface share a center point but scale their radii together (e.g.
outer 24px containing an inset with 16px, not an arbitrary mismatch). This is what makes soft
outputs read as "someone thought about the corners" rather than "rounded-lg on everything." Apply
it to the direction's one or two most prominent containers — a hero card, a primary panel — not
uniformly to every box, or it stops being a signature and becomes wallpaper.
