# Direction: Brutalist

*Delta only — inherits bans, contracts, and mode rules from `_base.md`. Fonts/hex/beziers below
are perishable examples (`_base.md` → "The perishability guard"), not canon.*

## Identity

Raw, structural, unapologetically loud. Two internal archetypes — **pick exactly one, never mix
them within a build**:

- **Industrial Brutalism** — Swiss print grid pushed to its structural limit: exposed grid lines,
  massive type as architecture, print-shop material honesty (paper-stock off-whites, ink-black,
  one alarm-red accent).
- **Tactical Telemetry** — HUD/terminal-coded: monospace-forward, data-dense, CRT/scanline
  texture, reads like instrumentation rather than print.

Mixing the two reads as indecision, not range — the SHAPE_CONSISTENCY_LOCK applies at the
archetype level, not just the token level. State the pick in `design_plan.signature` before
building.

## Type

- **Macro display**: a neo-grotesque at extreme scale — `clamp(4rem, 10vw, 15rem)`, tight tracking
  (`-0.03em` to `-0.06em`), tight leading (`0.85`–`0.95`). Type isn't decorating the layout, it
  *is* the layout.
- **Micro monospace**: a technical mono for labels, metadata, captions, nav — the deliberate
  contrast axis against the macro display. Never a third family.
- **Seed examples** (perishable, verify against `bans.json` before use): a heavy neo-grotesque in
  the Akzidenz/Helvetica-successor lineage for display; any technical mono with real character
  (not a generic system mono) for the micro layer. Follow `reference/type.md`'s selection method
  rather than reusing the same two faces every build.

## Color

- Industrial Brutalism seed palette: off-white paper stock, near-black ink, one alarm accent
  (e.g. `#F4F4F0` / `#050505` / `#E61919`) — these are illustrative OKLCH-equivalent values, not
  fixed hex to copy verbatim.
- Tactical Telemetry seed palette: darker ground, phosphor/terminal accent (green, amber, or cyan
  depending on subject), same near-black structural ink.
- **Zero gradients, zero soft-shadow, zero translucency.** Color blocks are flat and hard-edged —
  any softening reads as a different direction entirely (this is the direction's own version of
  `bans.json`'s pure-black rule inverted: near-black is *correct* here, but it must be flat, not
  glassy).

## Shape & space

- **Zero border-radius everywhere.** No exceptions, no "just this one card" — a single rounded
  corner breaks the entire premise (`SHAPE_CONSISTENCY_LOCK`).
- Structural borders are thick, visible, load-bearing — not decorative hairlines. Grid lines are
  meant to be seen, not hidden.
- Spacing is asymmetric and confident: massive empty zones next to dense clusters, not evenly
  distributed padding. This pairs with a high `DESIGN_VARIANCE` dial (8–10).

## Motion personality

Motion is mechanical and abrupt, not fluid — cuts and hard reveals over easing when it appears at
all. When it does animate, keep it in the shared motion reference's fast tier (sub-200ms UI
feedback) and favor `clip-path`/opacity cuts over smooth transform easing; a soft ease-out reads
as a different direction bleeding in. Reduced-motion users lose the CRT/scanline flicker entirely,
not just slow it down — those effects are decorative, never load-bearing.

## Signature technique

Texture as material honesty: CRT scanlines or halftone dot patterns applied via CSS gradients or
inline SVG filters (`feTurbulence`/pattern tiles), not photographic overlays. Applied sparingly —
usually to one hero surface or background field, never tiled across every card, or the texture
stops reading as a deliberate signature and starts reading as noise.
