# Performance Contract

Every page ships fast. Performance is not a separate concern — it's part of craft. A beautiful page that loads in 4 seconds is a failed page.

## Critical Rendering Path
- Inline critical CSS in `<head>`, defer the rest via `<link rel="preload" as="style" onload>`.
- All non-critical scripts: `async` or `defer`. `type="module"` is deferred by default — use it.
- Never `@import` in CSS — creates sequential chains that delay CSSOM construction.
- Split CSS by media queries using the `media` attribute — non-matching sheets don't block render.
- `<link rel="preconnect">` for third-party origins (fonts, CDNs, analytics). `<link rel="dns-prefetch">` as fallback.

## Images (the #1 performance lever)
- **LCP image**: `fetchpriority="high"`, raw HTML (not JS-injected so preload scanner finds it), **never** `loading="lazy"`.
- All below-the-fold images: `loading="lazy"`.
- Always set `width` and `height` attributes — prevents CLS. Aspect-ratio in CSS as backup.
- Serve modern formats via `<picture>`: AVIF → WebP → JPEG fallback with `<source type>`.
- `srcset` + `sizes` required for responsive images — never serve a 2000px image to a 375px viewport.
- Don't overuse `fetchpriority="high"` — prioritization is zero-sum.

## Interaction Responsiveness (INP)
- Tasks exceeding 50ms block the main thread — break them up.
- Rule: <50ms → sync; 50–250ms → slice with `scheduler.yield()` (fallback: `setTimeout` promise); >250ms → Web Worker.
- Debounce `scroll`, `resize`, `input` handlers.
- **Batch DOM reads then DOM writes** — never interleave (causes layout thrashing).

## CSS Containment
- `content-visibility: auto` for off-screen sections on long pages. **Must** pair with `contain-intrinsic-size` using `auto` keyword.
- `contain: layout style paint` for isolated widgets (sidebars, cards, chat panels).

## Responsive

- Mobile-first. Responsive at sm/md/lg/xl breakpoints.
- Test hero composition at both desktop and mobile viewport mentally before shipping.
- **Never use `h-screen` / `100vh`** for full-height sections — iOS Safari jumps catastrophically when the URL bar hides. Use `min-h-[100dvh]` (or `100svh` when appropriate). If subtracting a persistent header, compose: `min-h-[calc(100dvh-var(--header-height))]`.
- **Never use `100vw`** for full-width — it ignores the scrollbar width and causes horizontal overflow. Use `width: 100%` or `dvw` units.
- Touch targets minimum 44×44px on interactive elements. Anything smaller fails on real hands.
- Scale type and spacing with `clamp()`, not breakpoint step-changes. Examples: `font-size: clamp(2.5rem, 6vw, 5rem)` for headlines, `padding-block: clamp(3rem, 8vw, 6rem)` for section gaps. Body text minimum `1rem` (`16px`) — never below. Never `vw` alone for font sizes — always `clamp(min, vw, max)`.
- Horizontal scroll on mobile = critical failure. Audit wide elements (tables, code blocks, inline-image hero) and define their mobile fallback explicitly.
- **Container queries** for component-level responsiveness: `container-type: inline-size` on wrapper, `@container` on children. Use `cqi`/`cqb` units for fluid typography scoped to container. Never `block-size` as `container-type`.
- **Logical properties** (`margin-inline`, `padding-block`, `inset-inline-start`) over physical properties when RTL support is possible. Costs nothing, enables everything.
