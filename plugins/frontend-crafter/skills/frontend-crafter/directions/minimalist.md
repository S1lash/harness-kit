# Direction: Minimalist

*Delta only — inherits bans, contracts, and mode rules from `_base.md`. Fonts/hex/beziers below
are perishable examples (`_base.md` → "The perishability guard"), not canon.*

## Identity

Premium utilitarian, document-style. Reads like a well-typeset paper or a Swiss product manual —
the confidence comes from restraint and precision, not from having nothing left to hide behind.
This is the direction where a wrong micro-decision (a slightly-too-black text color, an inline
one-off spacing value) is nakedly visible, because there's nothing else competing for attention.

## Type

- **Body**: a clean, humanist or geometric sans — the workhorse.
- **Headline**: an editorial serif, used sparingly, as the one voice-carrying accent against the
  sans body/mono metadata. This is the direction's contrast axis (sans body vs serif display),
  not a serif-everywhere aesthetic.
- **Micro**: a technical mono for metadata, timestamps, labels — same role as in `brutalist.md`
  but quieter, smaller, less structural.
- **Seed examples** (perishable): Geist Sans / SF Pro-family for body, a distinctive editorial
  serif (Lyon, Instrument-class — verify against `bans.json`, several obvious choices here are
  already banned) for headline, Geist Mono for micro. Treat these as illustrations of the role
  pairing, not a shopping list — `reference/type.md` governs actual selection.

## Color

- **Never absolute black.** Body text is a warm-tinted charcoal (seed: `#111111`-class value),
  line-height opened to `1.6` to compensate for the added density of near-black-on-light reading.
- **Warm bone background**, not stark white — a seed in the `#F7F6F3`-class range. Verify any
  cream/bone background against `bans.json`'s AI-cream tell (OKLCH L 0.84–0.97, C<0.06) before
  locking it — minimalist and the saturated cream+terracotta lane can overlap if the palette isn't
  checked.
- **Color is a scarce resource.** One accent, used for exactly one purpose (usually interactive
  state), everywhere else the palette is neutral. This is the direction's version of
  `COLOR_CONSISTENCY_LOCK` — the accent's job is singular and consistent across every surface.

## Shape & space

- Radius is small and consistent, or absent — never the direction's signature move (that's
  `soft.md`'s territory). Structure reads through spacing and type hierarchy, not through rounded
  containers.
- Generous whitespace, document-like margins (45–75ch measure), rhythm from varied section spacing
  rather than decoration. Low `VISUAL_DENSITY` dial (1–4) is the default here unless the mode
  (app-ui) pulls it tighter.

## Motion personality

**Invisible motion** — movement that a user would struggle to describe afterward, because it
never called attention to itself. Fade + translate, roughly 600ms, on entrance; hover states are
transform/opacity only, nothing playful. No springs, no bounce, no orchestrated sequences. Pull
exact easing curves from the shared motion reference's "state change" tier rather than inventing
new ones — the point is restraint, not a new curve.

## Signature technique

Document-grade micro-typography discipline as the signature, not a single visual flourish:
consistent baseline grid, deliberate `text-wrap: balance` on headlines and `pretty` on body,
disciplined widow/orphan control, and a measured column width that never varies mid-page. The
"signature" here is that nothing looks improvised — every spacing and type decision reads as
intentional because it repeats exactly, everywhere, without exception.
