# Color Reference

OKLCH is the working color space for every palette this skill produces — perceptually uniform
lightness and chroma make the recipes below mechanical instead of guesswork. `bans.json` blocks
pure `#000`; this file is the full recipe, including the palette-seeding method that replaces a
generative script.

## 1. Why OKLCH, not HSL/hex

- Lightness (`L`) in OKLCH tracks *perceived* brightness — two colors with the same `L` and
  different hue actually look equally light. HSL's `L` doesn't have this property (pure yellow and
  pure blue at the same HSL lightness look very different in perceived brightness).
- Chroma (`C`) is a uniform saturation axis independent of hue — you can hold `C` constant and
  sweep hue to get a harmonious set, or hold hue and sweep `C` for a tint/shade ramp, and both
  operations behave predictably.
- Every browser shipping in the last several years supports `oklch()` natively in CSS — no runtime
  conversion needed.

```css
--brand:  oklch(55% 0.18 250);  /* deep blue */
--accent: oklch(55% 0.18 30);   /* matching warmth — same L/C, different hue */
```

## 2. The 60/30/10 weight rule

Distribute color coverage by area, not by palette-token count:

- **60%** — dominant neutral (background/surface).
- **30%** — secondary neutral or muted supporting color (cards, borders, secondary surfaces).
- **10%** — accent (primary actions, key state, the one thing that should pull the eye).

Total palette beyond neutrals: **2–4 named colors.** More than that and nothing reads as "the"
accent — hierarchy flattens. Fewer than 2 (a single accent with no secondary) is fine and often
correct for restrained/product-register work.

## 3. Tinted neutrals

Grays are never truly neutral in a finished palette — they carry a whisper of the brand hue so
the whole system feels like one material, not "gray + brand color pasted on top."

- Chroma range for tinted neutrals: **`C: 0.005–0.015`**, hue matched to the brand accent's hue.
- This is a *tint*, not a color — at this chroma range the neutral still reads as gray to the eye,
  but two different projects' "same" gray will look subtly different because they're tinted toward
  different brand hues. That subtlety is the point.
- Generic warm-gray or cool-gray (chosen without reference to the brand hue) is a tell — it means
  the neutral scale was picked from a default palette rather than derived from the brand.

```css
--gray-100: oklch(96% 0.008 250);  /* tinted toward the same 250° blue as --brand */
--gray-900: oklch(18% 0.012 250);
```

## 4. The quantified AI-cream tell

Warm cream backgrounds (`#F4F1EA`-family) are one of the three current AI-default clusters (see
`anti-slop.md`). The exact signature to avoid by default:

**`L: 0.84–0.97`, `C: < 0.06`** — a light, low-chroma warm neutral. This is not "cream is banned";
it's the specific quantified range that reads as templated when used as a large-surface
background without deliberate justification. If a brief genuinely calls for a warm paper-like
background (an editorial/print-adjacent direction), either push chroma or lightness outside this
band, or commit to it explicitly and pair it with other choices that break the rest of the AI-
default cluster (typography, accent color) so the page doesn't read as the *whole* template.

## 5. Contrast floors

- Body text: **≥ 4.5:1**
- Large text (≥18pt / ≥14pt bold) and UI component boundaries/icons: **≥ 3:1**
- **Placeholders: ≥ 4.5:1** — placeholder text is frequently under-contrasted because it's treated
  as "secondary," but it's still user-facing text a person needs to read to understand a field's
  expected input.
- `lint.mjs` checks token-pair contrast mechanically (declared fg/bg pairs in `design_plan`) —
  text-on-image or text-on-gradient contrast needs actual rendering and is a vision-tier check
  (`reference/pipeline.md` §verify).

## 6. Dark mode is a rebuild, not an inversion

Flipping lightness values (`L: 0.95` → `L: 0.05`) on the same hue/chroma pairing produces a
washed-out or muddy dark theme. Treat dark mode as its own design pass on the same token names:

- **Surface lightness needs its own depth ramp** — dark UIs read better with multiple distinct
  surface elevations (`L` steps like 0.14 / 0.18 / 0.22 for base/raised/overlay) rather than one
  flat dark background with borders doing all the separation work.
- **Desaturate accents in dark mode.** The same chroma that reads as vivid-but-controlled on a
  light background can look neon/oversaturated against a dark one — drop `C` by roughly 15–25%
  for accent colors in the dark variant.
- **Drop body font-weight** from 400 to ~350 (or the nearest available weight) in dark mode. Light
  text on a dark background at the same weight as dark text on light appears heavier/bolder due to
  a perceptual effect (light-on-dark halation) — see `type.md` §5 for the paired
  line-height/letter-spacing bump.
- Use `light-dark()` with the same OKLCH hue/chroma structure per token, different `L`/`C` per mode
  — see `reference/contracts/dark-mode.md` for the CSS mechanics.

## 7. Palette-seeding recipe — deriving a palette from the subject

When no brand palette exists (greenfield), derive OKLCH values from the subject's own materials
rather than picking a generic "nice" palette. This is the deterministic replacement for a
generative script — do it by reasoning, log the result.

1. **Name the subject's dominant real-world material or context** — the literal color of the
   thing the product is about. A coffee roastery's subject material is roasted beans (dark warm
   browns), not "warm and inviting" as an abstraction. A dev tool for logs is terminal/monospace
   culture (near-black, phosphor green or amber accents), not "techy blue."
2. **Extract a hue** from that material — not the most obvious/first-guess hue, the one that's
   actually characteristic. Roasted coffee is closer to hue ~40-50° (warm brown) than the cliché
   terracotta ~30°; a forest subject is closer to hue ~140-150° (true green) than the generic
   "nature" teal ~180°.
2a. **Check it isn't a saturated-lane default** — cross-reference `anti-slop.md`'s named clusters
    (warm cream + terracotta; near-black + acid accent; broadsheet zero-radius). If the derived
    hue lands in one of those clusters by coincidence, either push chroma/lightness to
    differentiate or pick the subject's *second*-most-characteristic material instead.
3. **Set brand `L`/`C`** for the primary accent: mid-lightness (`L: 0.45–0.65`) and moderate-to-high
   chroma (`C: 0.12–0.22`) for a confident accent; push `L` toward 0.7–0.85 and drop `C` toward
   0.05–0.10 for a muted/product-register accent.
4. **Derive the tinted-neutral hue from the same extracted hue** (§3) — this is what makes the
   whole palette feel unified rather than "brand color + generic UI gray."
5. **Derive a secondary color** (the 30% in 60/30/10) by rotating hue ±30-60° from the brand hue
   for a complementary/analogous relationship, holding `L`/`C` in a supporting (less saturated,
   often lighter or darker) range — or skip a secondary entirely for a restrained one-accent
   palette (valid, often correct for product register).
6. **Log the pick** — direction name, subject, extracted hue, and resulting token values — to
   `design-memory.jsonl` (per `reference/pipeline.md`) so future auto-directed palettes for
   similar briefs can bias away from repeating the exact same hue.

Worked example — a specialty tea shop (subject material: dried tea leaves, ceramic, steam):
hue ~75-90° (olive-green-to-warm-yellow tea-leaf range) for brand at `L:0.42 C:0.09` (a muted,
matte accent rather than a saturated "green = nature" cliché); tinted neutrals at hue 80,
`C:0.008-0.012`; no secondary accent — restrained one-color palette matching a calm product
register.
