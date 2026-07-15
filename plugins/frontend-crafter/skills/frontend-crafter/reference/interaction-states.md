# Interaction States Reference

Every interactive element and every data-driven surface has a defined set of states. Missing
states are the single most common gap between a prototype and production-grade UI — this file is
the checklist that closes it.

## 1. The 8 interactive states

Every interactive element (button, input, link, custom control) must define, or explicitly inherit,
all eight:

1. **Default** — resting state.
2. **Hover** — pointer over the element. **Keyboard users never see hover** — never rely on hover
   alone to communicate anything the keyboard-only path also needs (see Focus).
3. **Focus** — keyboard focus, via `:focus-visible`. Distinct from hover; both can be styled
   differently and often should be (hover is a hint, focus is a navigation requirement).
4. **Active** — mid-interaction (mouse/touch down, key pressed).
5. **Disabled** — not currently actionable. Prefer `aria-disabled` over the native `disabled`
   attribute when the element should remain focusable (e.g., so a tooltip can explain *why* it's
   disabled — a natively `disabled` element can't receive focus at all).
6. **Loading** — action in flight; the element should communicate this (spinner, disabled-look,
   text change) and typically also move to a disabled-equivalent state to prevent double-submit.
7. **Error** — the action or input failed validation. Field-level errors live under the field, not
   in a page-level banner.
8. **Success** — the action or input succeeded. Often transient (auto-dismisses or fades after a
   few seconds); don't rely on a success state as the only record of what happened for anything
   consequential.

`:focus-visible` spec: **2–3px outline, minimum 3:1 contrast against the adjacent background,
`outline-offset: 2px`.** Never remove an outline without a replacement — a blocker-severity issue,
not a style preference.

## 2. Undo beats confirmation dialogs

For reversible actions, prefer an **undo** affordance (a toast with an Undo button, a brief
grace-period delay before the action commits) over a blocking confirmation dialog. A confirmation
dialog interrupts every user for every action to protect against the rare mistaken click; undo
protects against the same mistake without taxing the common case. Reserve confirmation dialogs for
genuinely irreversible, high-consequence actions (permanent delete with no recovery path, financial
transactions) where even a brief undo window isn't a safe enough guarantee.

## 3. Skeletons beat spinners

- **Loading states default to skeleton placeholders** matching the final layout's dimensions (same
  approximate heights, same column widths) — this prevents the layout-shift jump when real content
  arrives and gives the user a preview of the page's structure while waiting.
- **Spinners are reserved for small, inline, indeterminate actions** — under roughly 24px, tucked
  next to the specific control that triggered them (a button's own loading spinner, an inline save
  indicator). A full-page or full-section spinner covering meaningful layout is a downgrade from a
  skeleton in every case where the final layout shape is knowable in advance.

## 4. Optimistic updates — low-stakes only

Optimistic UI (show the result before the server confirms) is appropriate for low-stakes,
easily-reversible actions — liking a post, toggling a checkbox, reordering a list. **Never use
optimistic updates for payments, irreversible deletes, or anything where a silent rollback after
a failed request would confuse or harm the user.** For those, wait for confirmation and show a
proper loading state instead.

## 5. State Catalog — required on every data surface

Every screen or component that renders data ships all of the following, not just the happy path:

- **Loading** — skeleton per §3, matching final layout dimensions.
- **Empty** — a composed illustration or composition + one sentence explaining what this will
  become + one action to populate it. Never a flat "No data" label with nothing else — an empty
  state is an invitation to act, not a dead end (see `copy.md` §"empty-screen-is-an-invitation").
- **Error** — inline, near the offending element or section. Message contains what went wrong and
  what to try next (`copy.md` §3-part error formula). Never a generic red banner with
  "Something went wrong" and no path forward.
- **Partial / stale** — where relevant: a small indicator + timestamp ("Showing cached data · 2m
  ago") so the user knows the data they're looking at might not be current.

Shipping only the happy-path state is the single most visible gap between a demo and production
software — the moment a user hits a cold cache, an empty account, or a failed request, the gap
becomes visible immediately.

## 6. Image and placeholder hygiene

- Never ship broken external image links — hotlinked third-party URLs rot silently over time.
- Safe placeholder sources: `picsum.photos/{w}/{h}` for photographic placeholders, local SVG
  assets for illustrations, `dicebear.com` for avatar placeholders, or genuinely in-repo images.
- Every `<img>` needs a meaningful `alt` (or `alt=""` if purely decorative), `loading="lazy"` below
  the fold, and `width`/`height` set to prevent layout shift (CLS) — the LCP image is the one
  exception (see `reference/contracts/performance.md` — it must NOT be lazy-loaded).

## 7. Modern platform primitives for state UI

- Native `<dialog>.showModal()` for modal states — automatic focus trap and inert background, no
  hand-rolled focus-trap logic.
- `inert` attribute on background content for custom non-modal overlays (drawers) where a native
  `<dialog>` doesn't fit.
- Popover API (`popover` attribute) for lightweight transient UI — menus, non-modal tooltips —
  where a full dialog is overkill.
- CSS Anchor Positioning (`anchor-name` / `position-anchor` / `position-area`) for tooltips and
  dropdowns that need to stay spatially tethered to their trigger across scroll/resize, without
  a JS positioning library. Feature-detect: `@supports (anchor-name: --x)`.
- Roving `tabindex` for composite widgets (toolbars, tab lists, listboxes) — one item in the group
  has `tabindex="0"`, the rest `tabindex="-1"`, and arrow keys move the roving focus — the standard
  pattern for keyboard navigation within a single composite control.
- Hit targets: minimum **44×44px** on any interactive element, touch or pointer.
