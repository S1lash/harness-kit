# Motion Reference

The single source of truth for animation decisions: whether to animate, how fast, what easing,
what technique, and how to keep it performant and accessible. Synthesizes emil-design-eng +
impeccable's `animate.md`. `bans.json` enforces the mechanical subset (transform/opacity-only,
`prefers-reduced-motion`); this file is the craft layer lint can't check.

## 1. Should it animate at all — the frequency test

Run every candidate animation through frequency **before** designing it. Frequency of exposure
determines tolerance for motion, not taste:

| Frequency | Examples | Verdict |
|---|---|---|
| 100+/day | Keyboard shortcuts, toggles, rapid repeated actions | **No animation.** Motion on a high-frequency action becomes friction the user pays every single time. |
| Tens/day | Hover states, nav transitions, tab switches | Reduce or remove. If kept, keep it under 150ms and imperceptible as "an animation." |
| Occasional | Modals, drawers, toasts, dropdowns | Standard treatment — this is where most of the vocabulary below applies. |
| Rare / first-time | Onboarding, empty-state illustrations, first-run reveals | Can delight — this is the one place a slower, more expressive motion earns its keep. |

**Never animate a keyboard-initiated action.** A user who pressed a shortcut already knows what
happened; a 200ms transition inserts latency between intent and result (the canonical failure is
Raycast animating window open on hotkey — removed after user complaints).

## 2. The purpose test

Every animation must serve one of five purposes. If it doesn't, cut it:

1. **Spatial consistency** — where did this element come from / go to (origin-aware popovers, shared-element transitions).
2. **State indication** — something changed (checked, loading, expanded).
3. **Explanation** — how does this relate to what triggered it (a drawer sliding from the edge that opened it).
4. **Feedback** — confirms the action registered (button press, submit).
5. **Preventing jarring change** — softens an otherwise instant layout shift.

"It only looks cool" is not a purpose. If an animation is purely decorative **and** falls in a
tens-or-more/day frequency bucket, remove it — decoration doesn't survive repeated exposure.

## 3. Easing

Match the easing family to what's physically happening:

| Motion type | Easing |
|---|---|
| Entering the screen | ease-out |
| Moving or morphing between two states | ease-in-out |
| Hover response | ease |
| Constant-speed / looping | linear |
| Unclear / default case | ease-out |

**Never use built-in CSS easing keywords for real UI** — `ease`, `ease-in-out` as browser defaults
read as generic. Define custom curves as tokens and reuse them everywhere:

```css
--ease-out:    cubic-bezier(0.23, 1, 0.32, 1);
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);
```

Three interchangeable production ease-out curves (impeccable) — no bounce, deliberately
restrained ("bounce easing reads as dated and tacky" outside of true spring physics):

```css
--ease-out-smooth:   cubic-bezier(0.25, 1, 0.5, 1);   /* default */
--ease-out-snappy:   cubic-bezier(0.22, 1, 0.36, 1);  /* quicker perceived response */
--ease-out-confident: cubic-bezier(0.16, 1, 0.3, 1);  /* decisive, larger movements */
```

**Never ease-in on UI.** Ease-in starts slow and accelerates — the animation is sluggish exactly
during the window the user is watching it (the first frames), then rushes to completion
unobserved. This is a hard flag in review, not a style preference.

## 4. Duration

Two overlapping tables — use impeccable's category buckets, cross-check against emil's component
examples:

**By purpose (impeccable):**

| Category | Duration | Examples |
|---|---|---|
| Instant feedback | 100–150ms | Button press, checkbox toggle, active state |
| State change | 200–300ms | Tab switch, filter apply, accordion |
| Layout change | 300–500ms | Panel resize, reflow, drag-drop settle |
| Entrance | 500–800ms | Modal/page-level reveal, first-run sequence |

**By component (emil):**

| Component | Duration |
|---|---|
| Button | 100–160ms |
| Tooltip | 125–200ms |
| Dropdown | 150–250ms |
| Modal / drawer | 200–500ms |

**Governing rules:**
- **UI stays under 300ms.** Past that threshold it reads as slow, not smooth, for anything
  triggered by direct interaction (buttons, toggles, dropdowns).
- **80ms is the "feels instant" threshold.** The brain buffers sensory input for roughly that
  long — anything at or under 80ms is perceived as immediate, not animated. Useful for the fastest
  feedback tier (press states).
- **Exit is faster than enter — target ~75% of the enter duration.** An element leaving the screen
  doesn't need the same care as one arriving; lingering exits feel laggy.
- **List/stagger cap:** 10 items × 50ms = 500ms max total stagger. Past that the last items feel
  disconnected from the trigger.
- **Hover scale range:** 1.02–1.05. Larger reads as cartoonish for a hover-only affordance.

## 5. Springs

Use springs, not duration/easing curves, when the element needs to feel "alive" or the gesture is
interruptible — drag, momentum-based dismissal, anything the user can grab mid-animation.

```js
{ type: "spring", duration: 0.5, bounce: 0.2 }
```

- Bounce range: **0.1–0.3.** Anything higher overshoots and reads as toy-like for production UI.
- Springs preserve velocity when interrupted — retargeting mid-gesture (user flicks again before
  settle) looks natural because the spring picks up from current velocity, not zero. A
  duration/easing tween snaps awkwardly on interruption; use springs for any interruptible
  interaction for exactly this reason.

## 6. Component-level principles

- **Buttons:** `:active { transform: scale(0.97) }` — a barely-perceptible press, not a bounce.
- **Never animate from `scale(0)`.** Nothing in the physical world grows from nothing at a point;
  it reads as a bug, not an entrance. Start at `scale(0.95)` + `opacity: 0` instead.
- **Popovers scale from their trigger, not the viewport center** — origin-aware animation.
  `transform-origin: var(--radix-popover-content-transform-origin)` (or equivalent from your
  popover primitive). Modals are the exception — they're not spatially anchored to a trigger, so
  center-scale is correct for them.
- **Tooltips skip their open delay on subsequent hovers** within a short window (moving between
  adjacent trigger elements) — only the first hover in a sequence pays the delay.
- **Transitions over keyframes for dynamic/interruptible UI.** Keyframe animations run to
  completion and don't retarget cleanly if state changes mid-flight; CSS/JS transitions (and
  springs) interrupt and retarget smoothly. Reserve keyframes for animations that are genuinely
  fire-and-forget (a one-shot confetti burst, a loading spinner).
- **Blur to mask imperfect transitions.** When a transition between two states can't be made
  perfectly smooth (e.g., text content changing mid-animation), add a brief `filter: blur(2px)` at
  the midpoint to visually mask the imperfection. Keep blur radius under ~20px — anything larger
  reads as a distinct effect rather than a mask.
- **`@starting-style` for entry animation of newly-inserted elements** (no JS needed to trigger the
  "from" state on mount):
  ```css
  dialog[open] {
    opacity: 1;
    transition: opacity 300ms var(--ease-out);
    @starting-style { opacity: 0; }
  }
  ```
  Pair with `transition-behavior: allow-discrete` when transitioning `display`.

## 7. Transform mechanics

- `translateY()` percentage values are relative to the element's **own** size, not the viewport —
  `translateY(100%)` moves an element exactly its own height, useful for slide-in-from-edge
  patterns without hardcoding pixel values.
- `scale()` scales all children proportionally, including their borders and text — for a card that
  should scale its shadow/border differently than its content, scale a wrapper, not the card
  itself.
- 3D transforms (`rotateX/Y`, `perspective`) need a `perspective` value on the parent to render
  depth; without it 3D rotation looks like a 2D squash.
- `transform-origin` defaults to the element center — set explicitly whenever the animation should
  pivot from an edge or a trigger point (see popover rule above).

## 8. `clip-path` techniques

GPU-accelerated, no extra DOM elements needed:

- **Hold-to-delete / progress reveal:** `inset(0 100% 0 0)` → `inset(0 0 0 0)`, animated on
  `mousedown`/`touchstart` hold, reversed on release before threshold.
- **Tab color transition:** clip a colored overlay layer with `inset()` synced to the active tab's
  bounding box instead of crossfading background colors.
- **Scroll image reveal:** `clip-path` driven by `animation-timeline: scroll()` — no IntersectionObserver needed.
- **Comparison sliders (before/after):** clip one image with a vertical `inset()` tied to a drag
  handle's x position. No extra DOM layer, fully GPU-composited.

## 9. Gesture / drag

- **Momentum-based dismissal:** compute velocity as `abs(distance) / elapsed_ms`; dismiss the
  element (rather than snap back) if velocity exceeds roughly **0.11 px/ms** at release, regardless
  of total distance traveled — a fast short flick should dismiss just as reliably as a slow long
  drag.
- **Damping at boundaries:** when a drag exceeds its natural range (rubber-band / overscroll),
  apply resistance proportional to overshoot distance rather than a hard stop — friction, not a
  wall.
- **Pointer capture:** call `setPointerCapture` on drag start so the gesture keeps receiving events
  even if the pointer leaves the element's bounding box mid-drag.
- **Multi-touch protection:** ignore a second touch point during an active single-finger drag
  gesture (guard against accidental pinch/second-finger interference).
- Prefer friction/damping over hard stops everywhere a drag can exceed its bounds — hard stops
  read as a bug, friction reads as physicality.

## 10. Performance

- **Animate only `transform` and `opacity`.** Every other property triggers layout or paint and
  stutters under load — enforced mechanically in `bans.json`, restated here because it's the
  single highest-impact motion rule.
- **CSS custom properties inherit down the tree** — updating a `--swipe` custom property to drive a
  transform forces recalculation on every element that references it. Update the `transform`
  property directly on the dragged element instead of routing drag state through a CSS variable
  when performance matters (many list items, high-frequency drag updates).
- **Framer Motion's `x`/`y`/`scale` shorthand props are NOT hardware-accelerated** the same way a
  literal `transform` string is — under load (long lists, low-end devices), pass a full
  `transform: translate(...) scale(...)` string instead of the convenience props.
- **CSS animations beat JS animations under main-thread load** — CSS animations (and the Web
  Animations API) run on the compositor thread and keep animating even while JS is busy; a
  `requestAnimationFrame` loop stalls the moment the main thread is blocked. Prefer CSS/WAAPI for
  anything that must stay smooth during heavy JS work (data fetch, large re-render).
- **Web Animations API (WAAPI)** is the right tool when you need CSS-grade performance but
  programmatic control (dynamic durations, `Animation.finished` promises, `getAnimations()` for
  DOM-removal sequencing) — reach for it before a full JS animation library.

## 11. Accessibility

- **`prefers-reduced-motion: reduce` means fewer animations, not zero.** Drop movement (translate,
  scale-based motion, parallax, scroll-linked effects) but keep opacity/color transitions — a
  fade communicates state change without vestibular trigger. Full removal of all transition loses
  the "state changed" signal entirely; that's over-correction, not compliance.
- **Gate hover-only motion behind `@media (hover: hover) and (pointer: fine)`.** Touch devices fire
  synthetic hover on tap — a hover animation without this guard triggers on every tap on mobile,
  which reads as a bug (delayed/sticky response).

## 12. Stagger and cohesion

- **Stagger delay range: 30–80ms** between items. Below 30ms it reads as simultaneous; above 80ms
  the sequence feels sluggish. Cap total stagger at ~500ms (§4).
- Stagger is decorative, never load-bearing — content must be fully usable/interactable before its
  stagger delay completes; never gate interactivity on animation finish.
- **Cohesion**: easing, duration, and the visual design should feel like they belong to the same
  system. A snappy 150ms interaction paired with a soft bouncy spring on an adjacent element breaks
  the illusion of one coherent product. Review animations with fresh eyes the next day and in
  slow-motion (2–5× via DevTools) — problems that are invisible at full speed become obvious slow.

## 13. Asymmetric timing

Deliberate, high-stakes actions get **slow, linear** timing that the user must consciously wait
out (hold-to-delete over ~2s, linear — no easing, so the wait feels consistent and fair). System
responses to that action snap back fast (~200ms ease-out) — the asymmetry itself communicates
"this was a big decision, this was just a UI update."

## 14. Review checklist (issue → fix)

Use this as the mechanical pass in `procedures/polish-pass.md`'s motion sub-check, or standalone
motion review:

| Issue found | Fix |
|---|---|
| `transition: all` | Specify exact properties (transform, opacity only) |
| `scale(0)` on entrance | `scale(0.95)` + `opacity: 0` |
| `ease-in` on any UI element | Swap to `ease-out` |
| Popover/tooltip scaling from center, anchored to a trigger | `transform-origin` set to trigger position |
| Keyboard-triggered action animated | Remove the animation entirely |
| Any UI transition over 300ms | Reduce to 150–250ms range |
| Hover animation with no `hover`/`pointer` media guard | Add `@media (hover:hover) and (pointer:fine)` |
| Keyframe animation on rapidly-retriggerable state | Convert to transition or spring |
| Framer Motion `x`/`y`/`scale` shorthand in a high-load context | Full `transform` string |
| Enter and exit using identical duration | Exit ≈ 75% of enter duration |
| Multiple elements appearing with zero stagger | Add 30–80ms stagger, cap total ~500ms |
| No `prefers-reduced-motion` handling | Add — reduce movement, keep opacity/color |

## 15. Debugging

- Slow motion 2–5× via browser DevTools playback rate before judging any animation as "done."
- Chrome DevTools **Animations panel** to inspect actual timing/easing being applied, not just the
  authored CSS (catches cascade overrides).
- Verify on a real low-end device, not just a fast dev machine — jank that's invisible on an M-series
  laptop is common on mid-range Android hardware.

## Vocabulary — naming a felt description

When a request names a motion feeling ("make it feel more alive", "like it's snapping into place")
rather than a mechanism, translate to the precise term before implementing. Categories: Entrances/
Exits, Sequencing/Timing, Movement/Transforms, Transitions Between States, Scroll, Feedback/
Interaction, Easing, Springs, Looping/Ambient, Polish/Effects, Performance. Notable terms worth
knowing by name: **origin-aware animation** (§6), **morph** vs **crossfade** vs
**shared-element-transition** (three distinct techniques for "A becomes B"), **rubber-banding**
(§9 damping), **layout animation** (auto-animating position/size changes on reflow, e.g. FLIP),
**direction-aware transition** (slide direction depends on navigation direction, e.g. tab order),
**scroll-driven** (`animation-timeline: scroll()`/`view()`), **anticipation** (a tiny counter-
motion before the main motion, e.g. squash before a jump), **follow-through** (secondary elements
settle slightly after the primary motion stops), **squash & stretch**, **asymmetric easing** (§13),
**perceptual duration** (how long something *feels* vs its actual ms value — denser/larger motion
feels slower at the same duration), **number ticker** (animated digit rollover), **tabular numbers**
(`font-variant-numeric: tabular-nums` — prevents layout shift on changing digits), **line drawing**
(SVG `stroke-dasharray`/`stroke-dashoffset` reveal), **text morph** (character-level transition
between two strings). When a request is ambiguous, name the best-match term back to the user
before building — it confirms intent and teaches the vocabulary for next time.

## Review posture

When explicitly asked to review motion (not build it): default to **flagging, not approving** —
approval must be justified per-animation, not assumed. Score against: justified motion (§2),
frequency-appropriate (§1), responsive easing (§3), sub-300ms UI (§4), origin & physicality (§6),
interruptibility (§5/§9), GPU-only properties (§10), accessibility (§11), asymmetric timing (§13),
cohesion (§12). Output a findings table (issue → fix → reasoning) plus an explicit verdict —
Block or Approve — never a hedge.
