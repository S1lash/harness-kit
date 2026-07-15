# Make Tweakable — live design controls

*Expose 3-8 live controls over the shipped design via a hidden panel driven by CSS custom properties.*

Fires whenever the user wants a live-tweakable design (explicit request), and by default for any
multi-variation deliverable (`procedures/generate-variations.md` — tweakable defaults are baked into
that ladder even when not separately requested).

## What to expose

Pick 3-8 controls covering the axes most likely to matter for this design — not every possible knob:

- **Color** — primary/accent color (swap the `--accent` token; don't wire every color independently).
- **Font** — display font pairing, picked from 2-3 alternatives that still pass `bans.json`.
- **Density** — spacing scale multiplier (tight / default / loose), driving the `--space-*` tokens.
- **Layout variant** — if the deliverable has structural alternatives (e.g. sidebar-left vs top-nav).
- **Headline copy** — when copy strategy is genuinely in question, not for every string on the page.
- **Radius** — sharp / soft / rounded, driving a single `--radius` token.

Never expose more than 8 — past that the panel itself becomes the design problem, and the point (fast
comparison) is lost.

## Mechanism

- **CSS custom properties** for every exposed control. The control updates the property; every
  consumer of that property updates live, with zero JS beyond the property write.
  ```css
  :root {
    --accent: oklch(55% 0.18 250);
    --radius: 0.5rem;
    --space-unit: 8px;
  }
  ```
- **Floating panel, bottom-right, titled "Tweaks".** Collapsed/hidden by default — the design must look
  completely finished with the panel closed. Opening it is an explicit, discoverable action (small
  toggle button), never an overlay that appears unprompted.
- **No build step required to see a change** — every control is a plain DOM event handler flipping a
  custom property via `element.style.setProperty()` or a class toggle mapped to a property block.
  Keep it vanilla JS even in a React/framework project; the tweak panel is a dev/review affordance, not
  shipped product surface.

## Scope discipline

The tweak panel is a review tool, not a feature. It ships in the deliverable during the design
conversation (so the user can compare live) but is explicitly **out of scope for production** unless
the user asks for it as a real feature (e.g. a genuine theme picker). Flag this distinction in the
final summary so it isn't accidentally shipped to production believing it's finished UI.
