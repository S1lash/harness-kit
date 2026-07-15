# Direction: Editorial

*Delta only — inherits bans, contracts, and mode rules from `_base.md`. Fonts/hex/beziers below
are perishable examples (`_base.md` → "The perishability guard"), not canon.*

## A saturated lane — read before selecting

`_catalog.md` excludes editorial-serif-default from the auto-selection candidate set by default
(dossier §1a/§3c, `bans.json`'s font-selection note). The combination of display serif + italic
accents + small-caps mono labels + hairline ruled separators is no longer a distinctive choice —
it's the single most common AI-generated "sophisticated" template, as recognizable now as the
cream+terracotta lane. **Use this direction only when the brief genuinely demands magazine
treatment** (a publication, a long-form content product, a brand whose actual voice is editorial)
— never as the fallback "make it feel premium" choice. `minimalist.md` already covers the
sans-body/serif-headline pairing for briefs that want restraint without the magazine apparatus;
reach for editorial only when the content itself is the product (articles, essays, long-form
reading), not when a serif headline is just decorating a SaaS landing page.

If selected, this direction must differentiate hard from the cliché above — see "What NOT to do"
below before building anything.

## Identity

Magazine/broadsheet discipline applied with genuine editorial mechanics — multi-column text,
running heads, pull quotes, drop caps, footnote/attribution conventions — not merely "a serif
font on a landing page." The test: does this page behave like something with an editor and a
production schedule, or does it just borrow a serif for gravitas? If removing the serif wouldn't
change how the page is structured, it isn't actually editorial.

## Type

- **Body**: a text-optimized serif built for extended reading at length — not a display serif
  pressed into body duty. The contrast axis is *reading register* (body serif vs sans apparatus),
  not size.
- **Apparatus** (bylines, captions, folios, running heads, section labels): a plain sans, small,
  quiet — functional typography, not another decorative layer.
- **Explicitly avoid** the italic-for-emphasis + small-caps-mono-label combination as a reflexive
  pairing — pick one apparatus register and use it consistently rather than stacking three
  typographic signals (italic, small-caps, mono) to signal "editorial."
- **Seed examples** (perishable, verify against `bans.json` — several obvious display serifs are
  already banned there): a genuine text-serif with real reading-weight variants, not a display cut
  scaled down.

## Color

- Restrained, closer to print: off-white or cream stock **checked against the AI-cream tell**
  (`bans.json` — OKLCH L 0.84–0.97, C<0.06) before locking, ink-dark body text (never pure black),
  one accent reserved for rare editorial marks (a rule, a pull-quote mark, a section flag) — not
  spent on UI chrome.

## Shape & space

- **Genuine multi-column text** where the mode allows it (long-form article bodies) — this is
  structural, not decorative, and is the actual differentiator from a single-column page with a
  serif headline.
- Rule weight varies by function: a heavy rule divides major sections, a hairline separates
  metadata — **not** hairlines-everywhere as blanket texture (that flat overuse is exactly what
  makes the cliché recognizable).
- Drop caps and pull quotes are structural devices reserved for genuinely long content — using
  them on a three-paragraph landing page is the tell, not the technique itself.

## Motion personality

Understated, print-adjacent — page-turn-adjacent transitions between sections, subtle fades on
reveal, nothing that competes with the reading experience. Pull timing from the shared motion
reference's "state change" tier; editorial is not the direction to reach for spring-physics or
orchestrated entrance sequences (that's `soft.md`).

## Signature technique

Genuine running-head/folio apparatus: a persistent header showing section/issue/page context that
updates as the reader moves through the content (via scroll-driven state or section observers),
behaving like an actual publication's running head rather than a static logo bar. This is
structural and functional — it does real work identifying where the reader is — which is what
separates it from decorative "magazine-style" labeling.

## What NOT to do

- Don't stack display-serif + italic + mono small-caps labels + ruled separators as a reflexive
  bundle — that bundle *is* the saturated lane this file exists to avoid.
- Don't use editorial apparatus (drop caps, pull quotes, running heads) on short-form content where
  they have no functional job — decoration without function is exactly the anti-pattern the
  direction system exists to prevent.
- Don't default here when the brief says "premium" or "sophisticated" without more — check the
  candidate set in `_catalog.md` first; premium doesn't automatically mean editorial.
