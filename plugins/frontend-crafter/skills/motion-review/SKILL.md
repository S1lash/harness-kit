---
name: motion-review
description: >-
  Two capabilities for motion in interfaces. (1) REVIEW — audit existing animations/transitions
  like a senior motion-design reviewer: default posture is flagging, approval must be earned.
  Triggers on "review my animations", "is this smooth?", "это плавно?", "audit this motion",
  "check my transitions", "does this animation feel right". (2) NAME-THIS-MOTION — translate a
  vague felt description of a motion into its precise, industry-standard term. Triggers on
  "what's it called when...", "как называется когда...", "what's the term for this effect",
  "is there a name for this transition", "what do you call it when things...". Use for any
  request that asks to judge, fix, or name motion/animation/transition behavior in a UI.
---

# Motion Review

> **Relationship to the pipeline.** `frontend-crafter`'s VERIFY step **auto-applies** the REVIEW
> hard-flags + Ten Pillars below on any motion it builds (and `animate`/`delight` always self-review)
> — motion is never shipped unreviewed. This standalone skill is the **deep / explicit** path: a
> full audit of arbitrary existing animation code, or the NAME-THIS-MOTION lookup, on request. Both
> read the same craft SoT (`frontend-crafter/reference/motion.md`).

Two separable jobs live in this skill: **judging** motion that already exists (REVIEW mode) and
**naming** motion that's only been felt or described (NAME-THIS-MOTION mode). Detect intent from
the request — "review/audit/check/is this smooth" → REVIEW; "what's it called/is there a term/how
would I describe" → NAME-THIS-MOTION. If genuinely ambiguous, ask one line.

> **Shared source of truth.** This skill reads the `frontend-crafter` plugin's
> `reference/motion.md` as the canonical motion craft reference (durations, easing curves, spring
> config, performance rules) whenever it is present in the working tree. The Ten Pillars and hard
> flags below are this skill's own review lens applied on top of that shared reference — don't
> restate `reference/motion.md`'s content elsewhere; point to it.

---

## Mode 1 — REVIEW

### Posture

You are a senior motion-design reviewer, not a cheerleader. **The default verdict is a flag.**
Approval is not the neutral outcome — it has to be earned by the animation clearing every pillar
below. Silence on a violation is the failure mode this mode exists to prevent: don't wave through
something you didn't actually check against the pillars just because it "looks fine" at a glance.

Review at the level of actual behavior, not intent. "It's supposed to feel snappy" is not evidence
— the duration number, the easing curve, the animated property, and the trigger frequency are.

### The Ten Pillars

Score every animation against all ten. Any pillar failure is a candidate flag; multiple failures
on one animation raise the impact tier (see Verdict below).

1. **Justified motion** — every animation states a reason: spatial consistency, state indication,
   explanation of a change, feedback, or preventing a jarring cut. "Looks cool" is not a reason
   once the user has seen it more than a handful of times. No stated purpose → flag.
2. **Frequency-appropriate** — the more often a user triggers something, the less it should
   animate. 100+ times/day (keyboard shortcuts, toggles) → no animation. Tens of times/day
   (hovers, nav) → reduce or remove. Occasional (modals, drawers, toasts) → standard motion is
   fine. Rare / first-run → room for delight. Never animate keyboard-initiated actions.
3. **Responsive easing** — entrances use ease-out, moves/morphs use ease-in-out, hovers use ease,
   constant-speed motion uses linear. CSS built-in easings (`ease`, `ease-in-out`) are too weak for
   production feel — flag their use in favor of custom cubic-bezier curves. `ease-in` on anything
   UI-facing is a hard flag (see below) — it decelerates into stillness exactly when the user is
   watching, which reads as sluggish.
4. **Sub-300ms for UI** — button feedback 100–160ms, tooltip 125–200ms, dropdown 150–250ms,
   modal/drawer 200–500ms (drawers can run longer because they're spatial, not instantaneous
   feedback). Anything UI-classified above 300ms is a flag unless it's an explicitly page-load /
   brand entrance sequence, which lives outside this budget.
5. **Origin & physicality** — elements enter/exit from a physically plausible place. A popover
   scales from its trigger's transform-origin, not the viewport center. **Never animate an entry
   from `scale(0)`** — it reads as the element being born from nothing; start from `scale(0.95)`
   with `opacity:0` instead. Modals are the sanctioned exception (they're not trigger-anchored).
6. **Interruptibility** — an in-flight animation must be able to reverse or retarget cleanly if the
   user changes their mind mid-transition (closes a drawer that was opening, etc.). Prefer CSS
   transitions or springs over keyframes for anything the user can interrupt — keyframes commit to
   a fixed timeline and stutter or jump when cut short.
7. **GPU-only properties** — only `transform` and `opacity` are animated. Anything animating
   `width`, `height`, `top`, `left`, `margin`, or other layout-triggering properties forces
   layout/paint on every frame and is a hard flag regardless of how it looks in isolation.
8. **Accessibility** — `prefers-reduced-motion` is respected (reduce, don't necessarily eliminate —
   keep opacity/color transitions, drop translation/scale/parallax). Hover-triggered animation is
   gated behind `@media (hover:hover) and (pointer:fine)` so touch devices don't inherit a
   hover-only interaction as a stuck state.
9. **Asymmetric timing** — enter and exit are not mirror images. Exits run faster than entrances
   (~75% of the enter duration is a good default) because leaving should feel less demanding of
   attention than arriving. Deliberate, weighty actions (hold-to-delete) can run slow and linear;
   system responses to user input should snap.
10. **Cohesion** — easing, duration, and the visual language of the animation agree with each other
    and with the rest of the product's motion vocabulary. A bouncy spring next to a flat linear
    fade in the same view is a flag even if each animation is individually fine.

### Hard flags (always flag, no judgment call)

These are pattern-matchable violations — if you see them, flag them, don't debate whether this
instance is the exception:

| Hard flag | Why it's always wrong |
|---|---|
| `transition: all` | Animates properties nobody intended to animate (including layout ones); also slower than an explicit property list |
| Entry animated from `scale(0)` | Reads as materializing from nothing; use `scale(0.95)` + `opacity:0` |
| `ease-in` on UI-facing motion | Decelerates into stillness under direct observation — feels sluggish |
| Animation on keyboard-triggered or high-frequency (tens+/day) actions | Motion tax paid on every repetition of the most common interactions |
| Duration > 300ms on standard UI feedback | Outside the felt-instant-to-responsive budget; reserve for explicit entrance sequences |
| Centered/viewport-origin transform on a trigger-anchored element | Breaks spatial continuity between trigger and result |
| Animating a layout-triggering property (`width`, `height`, `top`, `left`, `margin`, `inset` outside of `clip-path`) | Forces layout thrash every frame; use `transform`/`clip-path` instead |
| No `prefers-reduced-motion` handling on any non-trivial motion | Excludes vestibular-disorder and motion-sensitive users entirely |

### Additional checklist (issue → fix)

Run this pass alongside the pillars — same review, different granularity:

| Issue | Fix |
|---|---|
| `transition: all` | Specify exact animated properties |
| `scale(0)` entry | `scale(0.95)` + `opacity: 0` |
| `ease-in` on UI | `ease-out` |
| Center-origin popover | `transform-origin` at trigger |
| Animation on keyboard action | Remove |
| Duration > 300ms (non-entrance) | 150–250ms |
| Hover animation, no media query | Add `@media (hover:hover) and (pointer:fine)` |
| Keyframes on interruptible/rapid UI | Transitions (or spring) instead |
| Framer Motion `x`/`y`/`scale` shorthand under load | Full `transform` string (shorthand isn't hardware-accelerated) |
| Enter and exit share one duration | Exit ≈ 75% of enter |
| Multiple elements appear together | Stagger 30–80ms, decorative only, never gating interactivity |

### Findings table format

Report every flagged animation in one table — this is the primary deliverable of REVIEW mode:

| # | Element / Animation | Issue | Fix | Reasoning |
|---|---|---|---|---|
| 1 | `.dropdown-menu` open | `transition: all 300ms ease` | `transition: transform 180ms cubic-bezier(0.23,1,0.32,1), opacity 180ms ease-out` | `all` risks animating layout props; 300ms exceeds the dropdown budget (150–250ms); default `ease` is too weak — needs a custom out-curve |
| 2 | Toast entry | `transform: scale(0)` → `scale(1)` | `scale(0.95)` + `opacity: 0` → `scale(1)` + `opacity: 1` | Materializing from `scale(0)` reads as birth-from-nothing; violates Pillar 5 |
| … | … | … | … | … |

### Verdict — impact tier + Block/Approve

Classify the overall finding set into one tier, then issue an explicit verdict — never leave it
implied:

- **Blocker** — hard flags present, or a pillar failure that actively harms usability/accessibility
  (missing reduced-motion on a parallax-heavy build, layout-property animation causing visible
  jank, keyboard-action animation). **Verdict: Block.** Ship blocked until fixed.
- **Quality** — pillar failures that degrade feel but don't break usability (wrong easing family,
  symmetric enter/exit, missing stagger, weak default CSS easing instead of custom curves).
  **Verdict: Approve with required follow-up** — can ship, but the fixes are not optional
  backlog, they're the next commit.
- **Polish** — cohesion nits, could-be-better timing, missed delight opportunity on a rare/first-run
  moment. **Verdict: Approve.** Note the suggestion, don't gate on it.

State the verdict as one explicit line at the end: `**Verdict: Block**` / `**Verdict: Approve with
required follow-up**` / `**Verdict: Approve**`. Never let the findings table stand without it —
the reader should not have to infer the call from the severity of the table rows.

---

## Mode 2 — NAME-THIS-MOTION

### How to use this mode

The user describes a feeling, not a term ("it kind of grows out of the button", "как называется
когда элементы появляются друг за другом со сдвигом"). Match the description to the closest term
in the glossary below, then answer in this format:

```
**<Best-match term>** — <one-line gloss, from the glossary below>

Close alternates:
- **<Alternate 1>** — <how it differs from the best match>
- **<Alternate 2>** — <how it differs from the best match>  (omit if there's only one alternate)
```

Lead with the single best match, not a menu — this is a lookup, not a brainstorm. Only include
alternates when they're genuinely close enough to be confusable (see the disambiguation notes at
the end of the glossary for the pairs that come up most).

### Glossary (~120 terms)

#### Entrances / Exits

- **Fade in/out** — opacity transition only, no movement or scale.
- **Slide in/out** — enters/exits by translating along one axis from off-canvas or off-element.
- **Scale in/out** — enters/exits by scaling from a smaller (or larger) size toward 100%.
- **Zoom in/out** — scale change combined with fade, usually more pronounced than a subtle scale-in.
- **Grow/shrink** — scale-based entrance/exit anchored to a specific origin point (see origin-aware
  animation), commonly used for popovers and menus.
- **Reveal** — content becomes visible via a clip or mask edge moving across it, not via opacity.
- **Wipe** — a directional reveal/hide using a hard edge (often `clip-path`) sweeping across the
  element.
- **Collapse/expand** — height or a clip-path animates to show/hide content, used for accordions.
- **Unfold** — an expand that also implies a spatial origin, like paper unfolding from a point.
- **Peel** — an exit where an element appears to lift and detach from a surface, often with a
  slight rotation.
- **Dissolve** — a fade that implies granularity or texture, not just opacity (often via blur + fade).
- **Materialize** — entrance implying the element assembles itself (opposite of the banned
  scale-from-0 "birth from nothing" pattern — materialize should use blur/opacity, not scale(0)).
- **Pop in** — a fast, slightly overshooting scale-in, typically spring-driven.
- **Cascading entrance** — multiple elements enter in sequence via stagger, not simultaneously.

#### Sequencing / Timing

- **Stagger** — successive elements start their (identical) animation with a small fixed delay
  between each, so a group appears to ripple in rather than pop together.
- **Choreography** — the deliberate ordering and timing relationship between multiple animations
  in one sequence (which element moves first, what waits for what).
- **Orchestration** — same as choreography at a larger scale — coordinating an entire page-load or
  multi-step flow's motion as one composed sequence.
- **Delay** — a fixed pause before an animation starts, distinct from duration.
- **Sequencing** — animations run one after another, each starting when the previous finishes.
- **Parallel animation** — multiple animations run simultaneously on different elements or
  properties.
- **Debounced animation** — an animation trigger waits for input to settle before firing, avoiding
  re-triggering on every rapid change.
- **Perceptual duration** — the felt length of an animation, which is not linear with its actual
  duration — easing curve and distance both change how long a motion "feels."
- **80ms threshold** — the rule of thumb that any state change completing within ~80ms reads as
  instantaneous because the brain buffers sensory input over that window; below it you don't need
  to animate at all.

#### Movement / Transforms

- **Translate** — pure positional movement along x/y/z, no scale or rotation.
- **Pan** — a translate applied to a larger canvas/background relative to a fixed viewport.
- **Rubber-banding** — content resists past its natural boundary with increasing friction, then
  snaps back — the iOS overscroll feel.
- **Overshoot** — motion goes slightly past its target value before settling, implying momentum
  (often spring-driven).
- **Bounce** — overshoot that oscillates more than once before settling; heavier-handed than a
  single overshoot.
- **Squash and stretch** — an object deforms (widens/flattens on impact, elongates on launch) to
  sell weight and elasticity; classic animation principle, used sparingly in UI (button press,
  drop-target landing).
- **Anticipation** — a small motion in the opposite direction before the main motion, to telegraph
  what's about to happen (a button dipping slightly before it launches something).
- **Follow-through** — secondary elements or parts continue moving briefly after the main motion
  stops, implying they're attached but not perfectly rigid.
- **Momentum** — motion continues after the triggering input ends, decelerating naturally (used in
  drag/swipe dismissal, calculated from velocity).
- **Damping** — the rate at which oscillation or overshoot decays to rest; higher damping settles
  faster with less bounce.
- **Inertia** — the sense that an element resists starting or stopping instantly, tying its motion
  to a simulated mass.
- **Origin-aware animation** — a transform's origin point (`transform-origin`) is set to match
  where the interaction physically started (the trigger element), not a fixed point like center.
- **Transform-origin** — the CSS property controlling the pivot point for `scale`/`rotate`
  transforms; central to origin-aware animation.

#### Transitions Between States

- **Crossfade** — two states swap by fading one out while fading the other in, simultaneously, with
  no shared identity between them.
- **Morph** — one shape/element transforms continuously into another, implying it's the *same*
  object changing form (not two objects swapping).
- **Shared-element transition** — an element that exists in both the "before" and "after" view is
  animated as a single continuous object moving/resizing between the two layouts (e.g. a thumbnail
  expanding into a detail view), rather than two independent elements crossfading.
- **Layout animation** — when a DOM/layout change occurs (item added/removed/reordered in a list),
  the *other* affected elements animate to their new positions instead of jumping — the reflow
  itself is what's animated, generally via FLIP technique.
- **FLIP technique** — First-Last-Invert-Play: measure an element's start and end position, apply
  an inverse transform to make it appear frozen at "first," then animate that transform away —
  achieves layout animation using only GPU-friendly transforms.
- **View transition** — a browser/framework-native API (`document.startViewTransition` /
  `animation-timeline`) that automatically crossfades or morphs between two DOM states without
  manual FLIP math.
- **Direction-aware transition** — the transition's direction (slide left vs. right, for example)
  is derived from the navigational direction the user took (forward vs. back), not fixed.
- **State machine transition** — a transition explicitly tied to named states (idle → loading →
  success/error), each with its own defined enter/exit motion, rather than one generic fade.

#### Scroll

- **Scroll-driven animation** — an animation's progress is tied directly to scroll position rather
  than to time (via `animation-timeline: scroll()` or a scroll-linked library), so it scrubs back
  and forth with the user.
- **Parallax** — background and foreground layers move at different rates during scroll, implying
  depth.
- **Scroll-triggered reveal** — an animation fires once when an element crosses a scroll threshold
  (e.g. enters the viewport), then plays independently of further scroll (time-driven, not
  scroll-driven).
- **Pinning / scroll-jacking** — an element is fixed in place while the page continues to scroll
  underneath or around it, often used to extend a scene across more scroll distance than its own
  height.
- **Sticky reveal** — an element becomes `position: sticky` and reveals or changes as it reaches
  the top/bottom of its container.
- **Scroll-snap** — the viewport snaps to defined points along the scroll axis rather than
  resting anywhere.
- **Scrubbing** — the scroll-driven equivalent of dragging a video timeline — animation progress
  is a direct, reversible function of scroll offset.

#### Feedback / Interaction

- **Micro-interaction** — a small, contained animation triggered by a single user action (like,
  toggle, save) that gives immediate feedback, usually under a second total.
- **Press state** — the visual/motion feedback while a control is actively held down, typically a
  slight scale-down (`scale(0.97)`) to imply physical depression.
- **Hover state** — feedback shown only while a pointer rests over an element; must be gated behind
  a hover-capability media query so it doesn't leak to touch devices.
- **Ripple** — feedback that expands outward from the point of contact, most associated with
  Material Design's touch feedback.
- **Shake / wiggle** — a rapid short back-and-forth rotation or translation used to signal an error
  or invalid input, borrowing the "no" head-shake gesture.
- **Pulse** — a rhythmic scale or opacity oscillation used to draw attention to an element without
  full-blown looping animation (e.g. a notification dot).
- **Nudge** — a small, single, non-repeating movement used to draw attention once (a subtle bounce
  on an unread item).
- **Haptic-adjacent motion** — visual motion designed to substitute for physical haptic feedback on
  devices without vibration, timed to feel like a "click" even though it's silent.
- **Drag feedback** — visual response while an element is being dragged (elevation/shadow increase,
  slight rotation, scale), distinct from the drop/release animation.
- **Elastic drag** — a drag interaction where the dragged element resists and stretches rather than
  moving 1:1 with the pointer, especially near boundaries (related to rubber-banding).

#### Easing

- **Ease-out** — starts fast, decelerates into the resting state; the default for anything
  entering or appearing, because it reads as arriving under its own momentum and settling.
- **Ease-in** — starts slow, accelerates toward the end; reads as sluggish when used on anything
  the user is actively watching respond to their input — reserve for exits the user isn't focused
  on, or avoid on UI entirely.
- **Ease-in-out** — slow start and slow end with acceleration in the middle; used for movement or
  morphing where the element is neither purely appearing nor disappearing.
- **Linear** — constant velocity throughout; correct for continuous/looping motion or for motion
  that should feel mechanical/deliberate rather than organic (e.g. a slow hold-to-delete fill).
- **Custom cubic-bezier** — an author-defined easing curve (four control points) used instead of
  the CSS keyword defaults, which are widely considered too weak/generic for production-feel UI.
- **Asymmetric easing** — the entrance and exit of the same element use *different* curves (and
  usually different durations), because arriving and leaving are not the same felt experience.
- **Standard/material easing** — a small named set of pre-defined curves (from a design system like
  Material Design) applied consistently across a product for cohesion.
- **Snappy easing** — an ease-out curve weighted toward finishing quickly, used for confident,
  low-latency-feeling system responses.

#### Springs

- **Spring animation** — motion modeled on a physical spring (mass, stiffness, damping) instead of
  a fixed duration/curve; naturally interruptible and re-targetable mid-flight.
- **Stiffness** — how strongly a spring pulls toward its target; higher stiffness = faster, snappier
  motion.
- **Damping** — how quickly a spring's oscillation settles; low damping = more visible bounce,
  high damping = a critically-damped, bounce-free settle.
- **Bounce (spring parameter)** — a normalized 0–1 parameter (in frameworks like Framer Motion)
  controlling how much overshoot a spring exhibits; subtle values (0.1–0.3) read as lively without
  being cartoonish.
- **Critically damped spring** — a spring tuned to reach its target as fast as possible with no
  overshoot at all — the "no bounce" spring, useful when bounce would look unserious.
- **Velocity-aware spring** — a spring that inherits the current velocity of an interrupted
  animation or gesture (like a released drag) so the motion continues naturally instead of
  snapping to a new curve.
- **Gesture-driven spring** — a spring whose target or velocity is continuously updated by an
  in-progress user gesture (drag, swipe), rather than fired once at a discrete trigger.

#### Looping / Ambient

- **Loop** — an animation that repeats indefinitely, typically used for loading indicators or
  ambient background motion.
- **Ambient animation** — continuous, low-attention motion in the background of an interface
  (subtle gradient drift, slow parallax) meant to add life without demanding focus.
- **Marquee** — text or content scrolls continuously and repeats seamlessly, usually to fit
  overflowing content in a fixed-width space.
- **Skeleton shimmer** — a loading placeholder with a light band sweeping across it to imply
  content is being fetched, preferred over a spinner for perceived-performance reasons.
- **Breathing animation** — a slow, subtle scale or opacity pulse suggesting something is "alive"
  or actively listening/recording (e.g. a voice-input indicator).
- **Spinner** — a looping rotation indicating indeterminate loading progress; generally the weakest
  option compared to a skeleton, which telegraphs the shape of the content to come.
- **Progress animation** — a determinate loop or fill that communicates how much of a task is
  complete, distinct from an indeterminate spinner.

#### Polish / Effects

- **Blur-to-mask** — deliberately blurring an element briefly during a transition (typically under
  ~20px) to visually hide an imperfect intermediate state, most useful on transitions that don't
  interpolate cleanly.
- **Number ticker / count-up** — a numeric value animates by incrementing/decrementing through
  intermediate values rather than jumping straight to the new number.
- **Tabular numbers** — a typographic technique (not itself motion, but load-bearing for good
  number tickers) where digits are fixed-width so a changing number doesn't visually jitter in
  width as it animates.
- **Text morph** — one string of text transitions into another via per-character or per-line
  animation, rather than a plain crossfade of the whole block.
- **Line drawing** — an SVG stroke appears to draw itself using `stroke-dashoffset` animation from
  fully-hidden to fully-visible.
- **Gradient animation** — a background or text gradient's position/angle animates, often used for
  ambient branding moments (loading states, hero accents).
- **Glow/highlight pulse** — a box-shadow or outline briefly intensifies to draw attention to a
  just-changed or newly-focused element.
- **Confetti / celebration burst** — a one-off, high-energy particle animation reserved for rare
  success/completion moments — the textbook example of motion earned by infrequency.
- **Cursor-follow effect** — an element's position or transform is driven continuously by pointer
  position rather than by a discrete trigger.

#### Performance

- **Compositor-only animation** — an animation restricted to `transform` and `opacity`, the only
  two properties the browser can animate purely on the GPU compositor thread without touching
  layout or paint.
- **Layout thrash** — repeated forced synchronous layout recalculation caused by animating
  layout-affecting properties (`width`, `top`, `margin`, etc.) every frame.
- **Paint** — the browser step (more expensive than compositing) triggered by properties like
  `box-shadow`, `background-color`, or `border` changing every frame.
- **Off-main-thread animation** — an animation (CSS transitions/animations, WAAPI) that continues
  running smoothly even if the JS main thread is busy, unlike animations driven by
  `requestAnimationFrame` or JS-computed styles.
- **WAAPI (Web Animations API)** — the browser-native JS API for driving animations with CSS-level
  performance while retaining programmatic control (play/pause/reverse/seek).
- **Hardware acceleration** — the animation runs on the GPU compositor; a common trap is that
  shorthand transform props in JS animation libraries (e.g. animating `x`/`y`/`scale` as separate
  values rather than a single `transform` string) can silently opt out of this.
- **Frame budget** — the ~16ms window per frame (at 60fps) an animation has to compute and render
  before it's visibly dropped; a common target figure for judging animation performance headlessly.

#### Principles to Know

- **12 principles of animation** — the classic Disney animation principles (squash & stretch,
  anticipation, follow-through, ease-in/ease-out, etc.) that still govern what reads as "alive"
  motion, adapted from film animation into UI.
- **Motion hierarchy** — the idea that not everything in a view should animate with equal weight;
  primary actions get more deliberate motion, secondary/ambient elements get less or none.
  Cohesion (Pillar 10) depends on this being consistent.
  - **Reduced motion (accessibility)** — the practice of honoring `prefers-reduced-motion` by
  reducing (not necessarily eliminating) movement-heavy animation, typically dropping
  translation/scale/parallax while keeping opacity/color changes.
- **Perceived performance** — the principle that well-placed motion (skeletons, optimistic UI,
  progress feedback) can make an interface *feel* faster even when actual load time is unchanged.
- **Motion as feedback vs. motion as decoration** — the core distinction this whole review posture
  is built on: motion earns its place by communicating something (state, causality, feedback);
  decoration-only motion is the default target for a flag.

### Disambiguation — close pairs

These are the pairs that get confused most often; use this when a felt description could map to
either.

- **Morph vs. crossfade vs. shared-element transition** — crossfade swaps two *unrelated* elements
  by opacity alone (no continuity implied). Morph implies *one* element continuously changes shape
  into another form. Shared-element transition is the layout-level version of morph: a single
  element that exists in two different layouts (list thumbnail → detail hero image) is animated as
  one continuous object moving/resizing between them, rather than two elements crossfading.
- **Layout animation vs. shared-element transition** — layout animation (via FLIP) is about
  *siblings* repositioning when one is added/removed/reordered in a list. Shared-element transition
  is about *one specific element* persisting across a navigation/view change. They often combine
  (a list reorders via layout animation while a clicked item becomes a shared-element transition
  into detail view) but describe different things.
- **Clip-path animation vs. mask** — both hide part of an element, but `clip-path` defines a hard
  geometric boundary (a shape with a crisp edge, GPU-cheap, good for wipes/reveals) while a CSS
  `mask` can use gradients/images for soft, partial-opacity edges (more expensive, better for
  feathered/gradient reveals). If the description involves a hard edge sweeping across → clip-path;
  if it involves a soft fade-out edge or an image-shaped cutout → mask.
- **Parallax vs. scroll-driven animation** — parallax is a specific *effect* (layers moving at
  different rates). Scroll-driven animation is the *mechanism* (any animation whose progress is
  tied to scroll position) — parallax is one thing you can build with that mechanism, but so are
  scroll-triggered reveals, scrubbing, and pinning.
- **Spring vs. easing curve** — an easing curve (`cubic-bezier`) always completes in a fixed,
  predetermined duration and cannot be interrupted mid-flight without a jump. A spring is
  physics-simulated, has no fixed duration (it settles when the physics says so), and can be
  smoothly interrupted/retargeted because it carries velocity. Reach for spring when the
  interaction is a live gesture (drag) or needs interruptibility; reach for an easing curve for
  deterministic, one-shot UI feedback.
- **Stagger vs. sequencing** — stagger applies the *same* animation to *multiple* elements with a
  small offset between starts (a group entrance). Sequencing chains *different* animations (or
  different elements' animations) so each one starts only when the prior finishes — a stagger is
  usually overlapping, sequencing usually is not.
- **Ripple vs. pulse** — ripple originates from a point of contact and expands outward once
  (touch/click feedback). Pulse is a rhythmic, often repeating, scale/opacity oscillation applied
  to the whole element to draw attention, not tied to a contact point.
