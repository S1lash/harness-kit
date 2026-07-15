# Accessibility Contract (WCAG 2.2 AA — build-time, not afterthought)

## Structure & Semantics
- All content inside landmarks (`<header>`, `<main>`, `<nav>`, `<footer>`, `<aside>`). No content floating outside.
- `<h1>`–`<h6>` in sequential hierarchy — never skip levels, never fake headings with styled divs.
- Prefer native HTML over ARIA: `<button>` over `<div role="button">`, `<dialog>` over custom modals, `<nav>` over `<div role="navigation">`.
- Never redundant ARIA (`<ul role="list">`, `<button role="button">`).
- `<label for="id">` with explicit association — never `placeholder` or `title` as the accessible name.
- Use `aria-disabled` over `disabled` when the element must remain focusable (e.g., tooltip on disabled button explaining why).

## Focus & Keyboard
- `:focus-visible` for custom focus rings — **never remove outline without replacement**. This is a blocker, not a suggestion.
- Never positive `tabindex` values — they break natural tab order. Only `0` (add to flow) or `-1` (programmatic focus).
- Custom interactive elements: `Enter` → `keydown`, `Space` → `keyup` (matches native `<button>` behavior).
- Skip links for long pages: anchor to `<main>` with `tabindex="-1"` on target.
- Never alter focus flow with CSS reordering (`order`, `grid` placement) without matching DOM order.

## Modals & Dialogs
- Use `<dialog>.showModal()` — automatically traps focus and makes outside content inert. **Never implement custom focus traps** for native modal dialogs.
- Use `inert` attribute on background content for custom drawer/overlay patterns.

## Color & Contrast
- 4.5:1 for normal text, 3:1 for large text (≥18pt / ≥14pt bold) and UI component boundaries/icons.
- Never color as the sole state indicator (error = red + icon + text, not just red).
- `prefers-contrast: more` — test that the design doesn't break under forced high contrast.
- `@media (forced-colors: active)` fallbacks — never rely on `box-shadow` for borders in Forced Colors Mode.

## Live Regions
- `aria-live="assertive"` only for critical/time-sensitive announcements (data loss, session timeout). Everything else `"polite"`.
- Debounce frequent updates to live regions. One centralized region per urgency level.

## Motion
- `prefers-reduced-motion: reduce` wrapping all animations — no exceptions.
- Never exceed 3 flashes per second.

## Images & Media
- All images have meaningful `alt` text (or `alt=""` if purely decorative).
- `rem`/`em` for font sizes — never `px` for user-facing text (breaks browser zoom).

## Typographic Readability
- Body text max ~65 characters (`max-w-[65ch]`).
- `text-wrap: balance` for headlines, `text-wrap: pretty` for body text — never apply either on `*`.
