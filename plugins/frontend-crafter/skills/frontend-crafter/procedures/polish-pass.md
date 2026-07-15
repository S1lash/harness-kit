# Polish Pass — Final Gate Before Delivery

*The no-browser verify floor: 4 parallel static-critique subagents, aggregated, prioritized, re-verified.*

Run before shipping any design, in every provenance. This is the mandatory floor even when no browser
is available for screenshot/vision verification (`SKILL.md` step 4) — it is not a
substitute for the browser-based verify flow when Chrome MCP is present, it is the part of verify that
never depends on rendering.

## Launch 4 review subagents concurrently

Single message, multiple Agent calls, each scoped to the file(s) just finished. Each subagent reads
code only — no screenshot, no rendering.

### 1. Hierarchy & rhythm
- Primary/secondary/tertiary differentiation present and legible from the markup alone.
- The five signals combined, not just declared: size, color, weight, position, density
  (`reference/modes/app-ui.md` → Hierarchy — combinatorial signals).
- Spacing snaps to the defined scale (`--space-xs` … `--space-2xl`); hunt for one-off values
  (`padding: 7px 15px`, `gap: 13px`) — a single off-scale value is the smell of an invented inline.
- Type snaps to the defined type scale; same off-scale hunt for font sizes.
- Repetition with strategic breaks — not everything the same size/weight, not everything different.
- Alignment: consistent edges, no near-misses.

### 2. AI-slop visual (banned patterns readable from code)
- Purple gradients on white, card-grid-as-hero, safe-neutrals-everywhere, cookie-cutter rounded
  corners on every element.
- Banned fonts present in the CSS/markup (`bans.json` is the SoT list — check against it, don't
  re-derive from memory).
- Pure `#000000`/`#FFFFFF` where Zinc-950/Off-Black or a softened white token should be.
- Random invented colors not defined as a token (`--background`, `--surface`, `--primary-text`,
  `--muted-text`, `--accent`).
- `LABEL // YEAR` heading conventions, bouncing-chevron scroll cues, "Scroll to explore" filler.
- Emoji-as-decoration, hand-drawn/generic SVG illustration standing in for real content.

### 3. A11y-static (statically checkable subset — full contract: `reference/contracts/accessibility.md`)
- Landmarks: all content inside `<header>`/`<main>`/`<nav>`/`<footer>`/`<aside>`, nothing floating
  outside.
- Heading order: `<h1>`–`<h6>` sequential, no skipped levels, no styled-div fake headings.
- `<label for="id">` present with correct association on every form field — never `placeholder` or
  `title` standing in as the accessible name.
- `tabindex`: no positive values anywhere; only `0` or `-1`.
- Redundant ARIA (`<ul role="list">`, `<button role="button">`) flagged and removed.
- Native elements preferred over ARIA re-implementations (`<dialog>` vs custom modal div, `<button>`
  vs `<div role="button">`).
- **Not covered here** (needs rendering, belongs to the browser-based verify flow when available):
  live contrast ratios on rendered colors, text-on-image/gradient contrast, focus-visible ring
  appearance, forced-colors-mode rendering. Token-pair contrast IS static and is covered by
  `scripts/lint.mjs`, not this subagent.

### 4. Copy / editorial
- Em-dash misuse in body/editorial copy (short UI strings get a `lint.mjs` warn instead — this
  subagent covers prose, not labels).
- Cliché AI-copy tics: "Elevate", "Seamless", "Unleash", "Next-Gen", "Empower", "Revolutionize".
- Product-language check: copy describes what the product does, not design commentary about itself.
- Fabricated data: any metric, percentage, testimonial, or "Trusted by N teams" claim not sourced
  from the user — flag every instance, no exceptions. Cross-check against `bans.json`.
- Headline carries the meaning; supporting copy is one short sentence, not a paragraph.
- Full copy contract: `reference/copy.md`.

## Litmus checklist each subagent judges against

**Hero** (subagent 1 + 2)
- If removing the hero image, does the page still work? If yes → image too weak.
- If hiding the nav, does the brand disappear? If yes → hierarchy too weak.
- Does hero fit in one viewport on desktop AND mobile?

**Overall** (subagent 1 + 2)
- Is the brand/product unmistakable in the first screen?
- Is there one strong visual anchor?
- Can the page be understood by scanning headlines only?
- Does each section have exactly one job?
- Are cards actually necessary? (try removing card treatment)
- Would the design feel premium if all decorative shadows were removed?
- Is this distinguishable from generic AI output?

**Integrity** (subagent 2 + 4)
- Zero fabricated numbers, percentages, or testimonials. Any data either came from the user or is an
  obvious `[placeholder]`.
- No `#000000`, no `h-screen`, no `100vw`, no `@import` in CSS, no Inter/Roboto/Arial.
- Loading, empty, and error states exist for every data-driven surface.
- All images load (no dead Unsplash); `alt` set; `width`/`height` set to prevent CLS.

**Accessibility** (subagent 3)
- All content inside landmark elements. Heading hierarchy sequential, no skipped levels.
- `:focus-visible` rings on all interactive elements — none removed without replacement (rendering-
  dependent verification, flag as "verify in browser" if no browser available).
- Modals use `<dialog>.showModal()`, not custom focus traps.
- Form fields have `<label for>`. Errors announced via `aria-live`.
- No positive `tabindex` values.

## Failure Patterns to Reject

Any subagent finding one of these is an automatic blocker or quality flag, not a judgment call:
- Generic SaaS card grid as first impression
- Beautiful image with weak brand presence
- Strong headline with no clear action
- Busy imagery behind text making it unreadable
- Sections that repeat the same mood statement
- Carousel with no narrative purpose
- App UI made of stacked cards instead of layout
- Inter/Roboto/Arial anywhere in the design
- Purple-on-white color scheme
- Cookie-cutter rounded corners on everything
- No motion at all on a visually-led page
- Fake metrics / testimonials / logos to look "trusted"
- "SYSTEM // 2024"-style AI typography
- Circular spinner covering a whole section instead of skeleton
- `h-screen` on a hero causing mobile jump
- `100vw` causing horizontal scrollbar on pages with vertical scroll
- Missing empty/error states on data-driven screens
- `@import` in CSS creating render-blocking chains
- LCP image with `loading="lazy"` or injected via JS
- `innerHTML` with user/API/LLM content instead of `textContent`
- Forms without `autocomplete` attributes (password manager can't help)
- Dark mode without `<meta name="color-scheme">` causing FOUC
- Focus outlines removed with no replacement
- Custom modal/dialog without using native `<dialog>` element
- Positive `tabindex` values breaking natural tab order

## After agents return

1. **Aggregate** all findings into one list.
2. **Deduplicate** — multiple agents will flag the same issue (e.g. a removed focus ring shows up in
   both the a11y-static and hierarchy subagents); merge into one entry, don't report it twice.
3. **Prioritize** into three buckets:
   - **Blockers** — a11y failures, broken contrast, removed focus rings, missing labels, fabricated
     data, banned fonts/colors present. Fix all, no exceptions.
   - **Quality** — slop tropes, broken hierarchy, missing interaction states. Fix all.
   - **Polish recommendations** — subtler tone shifts, spacing tightening. Apply when in scope; flag
     when out of scope for this pass.

## Re-verify after fixes

Did contrast fixes wash out the brand color? Did focus rings overlap neighbors? Did hierarchy
adjustments make the primary CTA actually feel primary? If anything looks off — fix or flag. This is a
second, lighter pass over the specific lines touched by the fix, not a full re-run of all 4 subagents.

## Final summary format

Brief, structured. Do not recap what the user just watched you do.

```
Verdict: ready | ready-pending-decisions | needs-more-iteration
Blockers fixed: N
Quality fixed: N
Polish applied: N (of M flagged)
Open decisions for sign-off: [...]
Out-of-scope notes: [...]
Honest gaps (no browser available): [snapshot-regression unavailable | text-on-image contrast unverified | ...]
```

The "Honest gaps" line only appears when no browser was available — never silently imply full-parity
verification happened when it didn't.
