# Layout Reference

Spacing, rhythm, and structural mechanics — the token discipline that keeps a page from feeling
"random" even when no one consciously notices the scale behind it.

## 1. The 4pt base scale

Every spacing value is a multiple of 4px. Canonical stops:

```
4, 8, 12, 16, 24, 32, 48, 64, 96
```

Any spacing value outside this set (`padding: 7px 15px`, `margin: 18px`, `gap: 13px`) is a smell —
either it snaps to the nearest scale value or, if a genuinely new increment is needed, it becomes
a named token added to the scale deliberately, never an inline one-off. A single `17px` or `22px`
in an otherwise 8/16/24 design is the tell of an "invented" value that should be hunted down and
removed.

## 2. `gap` over margin

Prefer `gap` (flex/grid) for spacing between siblings over margin on individual children:

- Margin-based spacing requires either margin on every child except the last (fiddly `:not(:last-
  child)` selectors) or margin-collapse workarounds.
- `gap` is declared once on the parent, applies uniformly, and doesn't collapse unpredictably
  against adjacent elements outside the flex/grid context.
- Reserve margin for spacing a single element away from its *unrelated* neighbors (e.g., pushing a
  whole section away from the one above it), not for rhythm within a repeated list.

## 3. Flex-1D / Grid-2D

Pick the layout primitive by dimensionality of the actual problem:

- **Flexbox** for one-dimensional layout — a row or a column where items flow and wrap along one
  axis (nav bars, button groups, a single card's internal stack).
- **Grid** for two-dimensional layout — anything that needs explicit row AND column control
  simultaneously (page-level layout, card grids, dashboard panels).
- Common responsive card-grid pattern: `grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))`
  — auto-fits as many columns as fit at a minimum width, collapses to fewer/wider columns on
  narrow viewports without a media query.
- Using Grid for something that's really one-dimensional (a single row of nav links) adds
  unnecessary axis-control complexity; using Flexbox for something that's really two-dimensional
  (trying to align a card grid's rows AND columns with flex-wrap) produces misaligned rows the
  moment content heights vary — that misalignment is the actual bug behind "why don't my cards
  line up," and the fix is switching primitives, not tweaking flex properties further.

## 4. The squint test

Blur your vision (physically squint, or blur a screenshot) and check what still reads. If the
intended primary element doesn't stand out as the clear brightest/largest/most-isolated shape once
detail is gone, hierarchy is carried by content (words) rather than by structure (size, contrast,
isolation) — and structure is what a scanning eye actually uses first. Run this before shipping any
hero or dashboard-summary layout.

## 5. Size-ratio discipline

- **Strong hierarchy: size ratio ≥ 3:1** between a primary element and the next-most-prominent
  element it's competing with visually (e.g., hero headline vs body copy, primary stat vs
  secondary stats).
- **Weak/flat hierarchy: ratio < 2:1** — two elements this close in size read as equally
  important, which is only correct when they genuinely are (e.g., a symmetric two-column feature
  comparison). Anywhere one element is meant to lead, a sub-2:1 ratio is a bug, not a subtlety.

## 6. Rhythm from varied spacing

Uniform spacing everywhere flattens the page into one undifferentiated scroll — rhythm comes from
*varying* spacing to signal grouping, at two distinct scales:

- **Within a group** (related items — a card's internal elements, a form's fields): **8–12px.**
  Tight enough that the eye reads them as one unit.
- **Between sections** (unrelated blocks — end of one section, start of the next): **48–96px.**
  Loose enough that the eye registers a full break before starting to read the next block.

The gap between these two numbers (12 vs 48) *is* the rhythm — a page where every gap is
somewhere in the middle (24-32px used for both within-group and between-section spacing) has no
perceptible rhythm at all, because nothing distinguishes "these belong together" from "these are
different sections."

## 7. Semantic z-index scale

Never inline arbitrary z-index numbers (`z-index: 9999`, `z-index: 47`). Define a small named
scale and reference it everywhere a stacking context is needed:

```css
--z-base: 0;
--z-dropdown: 10;
--z-sticky: 20;
--z-overlay: 30;
--z-modal: 40;
--z-toast: 50;
--z-tooltip: 60;
```

The specific numbers matter less than the property: every stacking layer has exactly one named
token, new UI reuses the existing token for its layer type rather than inventing a new number, and
the scale is defined once at the top of the design system, not discovered ad hoc per-component.
