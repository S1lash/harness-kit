# CSS Architecture

## Cascade Layers
- Use `@layer` for explicit cascade priority zones when building from scratch:
  ```css
  @layer reset, base, theme, components, utilities;
  ```
- Declared upfront — order of `@layer` declarations determines priority, not source order.
- Use `:where()` within layers to keep specificity intentional, not incidental.

## Modern Selectors
- `:has()` for parent-based-on-child-state styling — eliminates JS class toggling for many patterns (e.g., `form:has(:invalid)`, `.card:has(img)`).
- `:is()` or `:where()` instead of duplicating selector lists. `:is()` takes highest specificity of its arguments; `:where()` is always zero specificity.
- `@scope` for component-scoped styles without specificity race conditions — prefer over deep `:not()` chains.

## Layout Patterns
- **Anchor positioning** for tooltips, popovers, dropdowns spatially tethered to a trigger: `anchor-name` + `position-anchor` + `position-area`. Feature-detect with `@supports (anchor-name: --x)`.
- **Subgrid** for aligning grandchildren to grandparent grid tracks (e.g., card content aligning across a card grid).
- Never `grid-auto-flow: dense` on interactive content — it breaks keyboard tab order.
- `popover` attribute for non-modal transient UI (menus, tooltips); `<dialog>.showModal()` for modals.

## Global Rules
- Never global resets on `*` — breaks web components and low-priority layers.
- Forced Colors Mode: `@media (forced-colors: active)` fallbacks. Never rely on `box-shadow` for borders (invisible in FCM).
