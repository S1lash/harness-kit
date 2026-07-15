# Presentation Rules

*Slide decks and scroll-narrative presentations: two sub-modes, chosen by cue, stated in `design_plan` for veto.*

## Two sub-modes

### `deck`
- Hard slide boundaries, 16:9 aspect ratio, one-idea-per-slide.
- **Keyboard-primary navigation**: arrow keys / `Space` advance and retreat, `Home`/`End` jump to first/last slide. Keyboard is the primary interaction — mouse/click/scroll are secondary affordances, not the other way around.
- **PDF export = one slide per page.** Two supported paths:
  1. Chrome-MCP `print-to-PDF` — reuse the same browser session used for the verify pass.
  2. `@media print` stylesheet with `break-after: page` on each slide container, as a no-browser fallback.

### `scroll`
- Continuous smooth-scroll, landing-style narrative arc.
- **Optional soft `scroll-snap`** per section (`scroll-snap-type: y proximity`, not `mandatory` — mandatory snap fights the user on fast scrolls and trackpad flicks).
- **PDF export = print stylesheet pagination** (`@media print` page-break rules honoring natural content flow, not forced one-section-per-page).

## Disambiguation rule
Classify from cues in the request, **first match wins**:
- Deck cues («слайды», «презентация», «PPT», "slides", "deck") → `deck`.
- Scroll cues («плавный скролл», «секции», «лендинг», "smooth scroll", "sections", "landing") → `scroll`.
- **Both present** (e.g. «сделай презу-лендинг с плавным скроллом») → `scroll` **with soft scroll-snap**, and state this resolution explicitly in `design_plan` so the choice is visible for veto.

Record the chosen sub-mode and the cue that triggered it in `design_plan` — this is a disambiguation the owner may want to override, not a silent default.

## Accessibility cross-reference

Keyboard navigation in `deck` mode **MUST** be layered on top of the contract in
`reference/contracts/accessibility.md`, not built as a parallel system:
- **Focus management** — advancing a slide moves focus to the new slide's heading (or a `tabindex="-1"` container) so screen-reader users land in the right place, matching the Skip Links pattern in the accessibility contract.
- **Skip-to-section** — long `scroll` presentations get a skip link to `<main>`, same as any long page.
- **ARIA announcements** — slide changes in `deck` mode announce via a `aria-live="polite"` region (e.g. "Slide 4 of 12: Pricing"). Never `assertive` — a slide change isn't a critical/time-sensitive event per the accessibility contract's Live Regions rule.
- **Keyboard nav is additive, never a replacement for tab order.** Arrow-key slide advance must not hijack `Tab`/`Shift+Tab` — a user tabbing through interactive elements on a slide must retain normal tab order; arrow keys are a second, parallel navigation layer. No positive `tabindex`, same rule as the base contract.

## Speaker notes
- `deck` mode: speaker notes are an `aria-hidden="true"` block, visible only in `@media print` (or a dedicated presenter view), never announced to screen readers and never visible on-screen during normal presentation.
- `scroll` mode: no speaker-notes concept — omit entirely.
