# Typography Reference

Covers the type-scale mechanics and, separately, the font **selection** method — `bans.json`'s
font list is exclusion-only and answers "what NOT to pick"; this file answers "how to pick."

## 1. The 5-size modular scale

Pick one ratio and generate the whole scale from it — never hand-pick individual sizes.

| Ratio | Name | Use when |
|---|---|---|
| 1.25 | Major third | Product/app register — restrained, many text levels needed in a dense UI |
| 1.333 | Perfect fourth | Balanced default — works for most landing/brand work |
| 1.5 | Perfect fifth | Brand-register, high-drama editorial or hero-led pages |

Generate 5 sizes from a base (`1rem`) by repeated multiplication in both directions (down for
caption/small, up for headings). Avoid a muddy middle cluster — a scale with both `14px` and
`15px` and `16px` present has no real steps at that zone; if two sizes round to visually
indistinguishable values, cut one.

## 2. Pairing on the contrast axis

Two typefaces (display + body) should differ on at least one clear axis — never two faces that
are "almost the same" (two similar geometric sans, or two similar slab serifs). Contrast axes to
pick from: serif vs sans, geometric vs humanist, wide vs condensed, high-contrast-strokes vs
mono-weight, display-only-personality vs highly-legible-workhorse. Pairing on **weight alone**
(same face, just bold vs regular) is not real pairing — it's one typeface doing two jobs, which is
sometimes the right call (see §6) but is a distinct decision, not the default.

## 3. Fluid type — `clamp()` discipline

```css
font-size: clamp(2.5rem, 6vw, 5rem);
```

- **The max must be ≤ 2.5× the min.** A wider ratio breaks browser zoom — a user who zooms to 200%
  expects the text to actually get bigger; an oversized `clamp()` max means the viewport-relative
  middle term dominates and zoom has little visible effect.
- **Hero/display text ceiling: ≤ 6rem** regardless of viewport width. Beyond that, headlines start
  wrapping unpredictably and the "impact" gained is marginal past a certain size.
- Fluid `clamp()` scales belong to **brand register** (§ below); **product register uses fixed
  `rem` values**, not fluid clamp — a dashboard's heading shouldn't resize with viewport the way a
  landing hero does; consistency across screen sizes matters more than drama there.

## 4. Line length, line-height, text-wrap

- Body measure: **45–75 characters**, target `max-width: 65ch`.
- Heading line-height: **1.1–1.2** (tight, since headlines are short and benefit from compactness).
- Body line-height: **1.5–1.7** (loose enough for comfortable paragraph reading).
- `text-wrap: balance` on headings (h1–h3) — prevents a lonely single word wrapping to its own
  line. `text-wrap: pretty` on body/prose — improves the last-line-of-paragraph orphan behavior.
  **Never apply either on `*`** — both have a performance cost proportional to element count and
  are only meaningful on short text blocks.

## 5. Light-on-dark bumps

Light text on a dark background needs measurable adjustment beyond just flipping the color — see
`color.md` §6 for the accompanying weight drop (400→350):

- **Line-height:** add **+0.05 to +0.1** over the light-mode value.
- **Letter-spacing:** add **+0.01em to +0.02em**.

Both compensate for the same perceptual effect (light-on-dark halation makes text look slightly
heavier/tighter than it measures) — apply both together, not one or the other.

## 6. Metric-matched `@font-face` fallback recipe

Prevent layout shift (CLS) and FOIT/FOUT flash by matching the fallback system font's metrics to
the webfont, so the fallback occupies near-identical space before the webfont loads:

```css
@font-face {
  font-family: "BrandFont Fallback";
  src: local("Arial");  /* or the closest-metric system font */
  size-adjust: 105%;        /* scale fallback to match webfont's average glyph width */
  ascent-override: 90%;     /* match webfont's ascent for baseline alignment */
  descent-override: 22%;
  line-gap-override: 0%;
}

body {
  font-family: "BrandFont", "BrandFont Fallback", system-ui, sans-serif;
}
```

Compute `size-adjust`/`ascent-override`/`descent-override` values from the actual webfont's metrics
(tools like Fontaine or manual comparison of glyph bounding boxes) — the numbers above are
illustrative, not universal defaults; every font pairing needs its own computed values.

## 7. Font selection recipe (the positive method)

`bans.json`'s font list is **exclusion only** — it tells you what's saturated, never what to pick.
Picking anything merely "not on the list" without a method still regresses toward another safe
default. The method:

1. **Read the active direction's seed suggestions** in `directions/{name}.md` — each direction
   carries a short list of example typefaces that suit its register, explicitly marked as
   perishable examples, not canon (a direction file that hard-codes "the" font for its lane just
   becomes tomorrow's ban-list entry).
2. **Prefer a lesser-known face within the right category** over the most obvious name in that
   category. For a geometric sans, that means passing over the handful of faces everyone reaches
   for first and picking one a step further down the familiarity curve that still fits the
   direction. Same logic for humanist sans and for distinctive modern serifs.
3. **Pair on the contrast axis** (§2) — verify the display/body pairing actually differs on a
   real axis, not just in name.
4. **Verify against `bans.json`** — the pick must not appear in the banned list (mechanically
   checked by `lint.mjs`, but verify before committing to the plan, not after building).
5. **Log the pick** — direction, chosen display font, chosen body font — to
   `design-memory.jsonl` (`reference/pipeline.md`). Auto-direction reads this log to bias away
   from repeating the same pick across unrelated projects, the same way it biases away from
   repeating a palette hue (`color.md` §7). This is what keeps the font choice from becoming a new
   personal default over many projects even though no single choice broke a rule.

Selection is per-direction, not global — a brutalist direction and a soft/editorial direction pull
from different seed lists in `directions/*.md`; there's no one "good font" independent of the
aesthetic it's serving.
