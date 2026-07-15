# Dials Reference (pre-build)

The three pre-build DIALS convert "make it nice" into an explicit numeric commitment recorded in
`design_plan`, before any code is written. **Distinct from post-build refinement verbs** — see §4.

## 1. Why dials, not vague taste

A numeric dial, set and recorded before building, is auditable — the finished design can be
checked against the stated intent ("did an 8/10 VISUAL_DENSITY page actually come out dense?").
A vague intention like "make it feel premium" can't be checked against anything; it just gets
whatever the model produces by default, and there's no way to tell after the fact whether the
result matches what was actually wanted. Dials are set during GROUND & AUTO-DIRECT
(`reference/pipeline.md` step 1) and persisted in `.crafter/design-plan.md`.

## 2. The three dials — each 1-10

### DESIGN_VARIANCE

How far the layout departs from a predictable, symmetric grid.

| Band | Range | Characteristics |
|---|---|---|
| Predictable | 1–3 | Symmetrical 12-column grid, equal paddings across sections, centered compositions. |
| Offset | 4–7 | Deliberate asymmetry within a controlled system — `margin-top: -2rem` overlaps between sections, varied aspect ratios across media, mixed left/center/right alignment used purposefully. |
| Asymmetric | 8–10 | Structural asymmetry as the organizing principle — masonry layouts, `grid-template-columns: 2fr 1fr 1fr`, massive intentional empty zones (`padding-left: 20vw`). |

### MOTION_INTENSITY

How much of the interaction surface carries motion, and how advanced the technique.

| Band | Range | Characteristics |
|---|---|---|
| Static | 1–3 | `:hover`/`:active` state changes only — no transitions beyond instant color/opacity swaps. |
| Fluid CSS | 4–7 | `transition: all 0.3s cubic-bezier(...)` on interactive elements, cascading delay sequences on entrance, transform/opacity-only animation throughout — the default band for most product work. |
| Advanced | 8–10 | Scroll-triggered reveals, parallax, `animation-timeline`-driven or JS-scroll-library-driven (GSAP ScrollTrigger or equivalent) sequences — reserved for brand-register pages where motion itself is part of the pitch. |

Cross-reference `motion.md` for the actual craft (easing, duration, purpose) at whatever intensity
band is set here — the dial sets *how much* motion exists; `motion.md` governs *how good* each
individual animation is regardless of band.

### VISUAL_DENSITY

How much information/whitespace per viewport.

| Band | Range | Characteristics |
|---|---|---|
| Art-gallery | 1–3 | Generous vertical rhythm, `py-32`–`py-48`-scale section padding, few elements per viewport, whitespace itself carries meaning. |
| Daily-app | 4–7 | Comfortable working density, `py-16`–`py-24`-scale padding — the default band for most product/dashboard UI. |
| Cockpit | 8–10 | Tight, information-dense — 1px dividing lines rather than card boundaries, `font-mono` for tabular numeric data, minimal padding, built for a power user who values density over breathing room. |

## 3. Defaults per mode × direction

Dials are auto-set from the resolved mode and direction (`directions/_catalog.md`) unless the
brief pins one explicitly (`reference/pipeline.md` §wish parsing). Starting points:

| Mode / register | VARIANCE default | MOTION default | DENSITY default |
|---|---|---|---|
| Landing / brand register, expressive direction (brutalist, soft/editorial) | 6–8 | 5–7 | 2–4 |
| Landing / brand register, restrained direction (minimalist) | 3–5 | 3–5 | 3–5 |
| App UI / product register | 2–4 | 3–4 | 5–7 |
| Presentation (deck sub-mode) | 2–4 | 4–6 | 2–3 |
| Component (isolated, register depends on host) | inherit from host system if known, else 3–5 | 3–5 | 4–6 |

These are starting points, not hard defaults that override a pinned axis or a clear directional
signal from the brief — a brutalist direction with a brief that explicitly asks for restraint
still gets a lower VARIANCE than the table default, because the pin (S2 in `pipeline.md`) always
wins over the mode×direction starting point.

## 4. Distinct from post-build refinement verbs

Pre-build dials and post-build verbs (`bolder` / `quieter` / `distill` / `overdrive` — see
`reference/pipeline.md` step 5 REFINE) operate on different lifecycles and are never conflated:

- **Dials commit intent before the first line of code is written.** They're an input to BUILD.
- **Verbs push an existing, already-built artifact** in a direction, conversationally, after the
  design exists. `bolder` doesn't set DESIGN_VARIANCE to a higher number and rebuild from scratch —
  it amplifies the specific hierarchy/pacing choices already present in the finished design.

A request like "make it more asymmetric" **before** BUILD is a dial adjustment (bump
DESIGN_VARIANCE, note it as pinned, proceed to build). The same request **after** a design exists
is a `bolder`/`vary`-class refinement verb acting on the built artifact. The distinction is purely
about lifecycle stage, not about the words used to express the request.
