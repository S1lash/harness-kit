# Landing Page Rules

*Narrative-driven marketing pages: one composition per section, one job each, copy that earns its place.*

## Narrative Sequence (default)
1. **Hero** — establish identity and promise
2. **Support** — one concrete feature, offer, or proof point
3. **Detail** — atmosphere, workflow, product depth, or story
4. **Social proof** — establish credibility
5. **Final CTA** — convert interest into action

## Hero Rules
- **One composition**: the first viewport reads as one unified piece, not a dashboard.
- **Full-bleed**: hero image runs edge-to-edge. No inset, side-panel, rounded, tiled, or floating hero images.
- **Hero budget**: brand + one headline + one short sentence + one CTA group + one dominant image. Nothing else.
- **No hero overlays**: no floating badges, promo stickers, info chips, callout boxes on hero media.
- **No hero cards**: cards never appear in the hero section.
- **Brand test**: if the first viewport could belong to another brand after removing the nav, branding is too weak.
- **Canonical full-bleed rule**: hero runs edge-to-edge with no inherited page gutters. Constrain only the inner text/action column.
- **Viewport budget**: combined header + hero must fit within initial viewport. When using `100vh`/`100svh`, subtract persistent UI: `calc(100svh - var(--header-height))`.

## Section Rules
- **One job per section**: each section has one purpose, one headline, usually one supporting sentence.
- **No cards by default**: use sections, columns, dividers, lists, media blocks. Cards only when they contain a user interaction. If removing border/shadow/background/radius doesn't hurt understanding — it's not a card.
- **Real visual anchor**: imagery shows product, place, atmosphere, context. Decorative gradients don't count.
- **Reduce clutter**: no pill clusters, stat strips, icon rows, boxed promos, schedule snippets, multiple competing text blocks.

## Copy Rules
- Write in product language, not design commentary.
- Headline carries the meaning. Supporting copy: one short sentence.
- Cut repetition between sections. No filler.
- **Editing principle**: if deleting 30% of the copy improves the page, keep deleting.
