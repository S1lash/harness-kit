# Dark Mode Contract

Fires only when dark mode is requested or the existing app supports it.

## Foundation (non-negotiable)
- `<meta name="color-scheme" content="light dark">` in `<head>` — **mandatory** for FOUC prevention. Without it, the page flashes white before CSS loads.
- `color-scheme: light dark` on `:root` or `html` — **mandatory**. Never on `body` only (scrollbar and form controls won't adapt).
- Always respect system preference by default — never hardcode `color-scheme: light` or `dark` as initial state.

## Color Tokens
- Use `light-dark()` CSS function for color tokens that auto-adapt:
  ```css
  :root {
    color-scheme: light dark;
    --surface: light-dark(#fafafa, #121212);
    --text: light-dark(#18181b, #e4e4e7);
  }
  ```
- Define `prefers-color-scheme` media query as fallback for browsers without `light-dark()`.
- `oklch()` values work well with `light-dark()` — same hue/chroma, different lightness per mode.

## Toggle UX
- Two-state only: system preference / forced opposite. Never expose three states (light / dark / system) — causes UX confusion.
- Persist choice in `localStorage`, apply via inline `<script>` in `<head>` to prevent flash.

## Known Bugs
- Safari: `prefers-color-scheme` doesn't follow parent `color-scheme` inside iframes — pass theme via URL param or `postMessage`.
- Never animate/transition `scrollbar-color` (WebKit rendering bug). Must pair `scrollbar-color` with `scrollbar-width` on macOS.
