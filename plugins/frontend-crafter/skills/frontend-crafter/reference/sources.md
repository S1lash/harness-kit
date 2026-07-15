# Live-Source Registry

Real code/spec sources to fetch **on demand**, keyed to a concrete trigger — never fetched
speculatively, never at skill-load time. Inspiration galleries are handled separately (§3) — they
are encoded as a taxonomy the skill reasons from, not fetched.

## 1. Live sources — pull real code/spec on trigger

| Source | What it is | When to pull |
|---|---|---|
| **Motion.dev** (`motion.dev`) | Official docs for Motion (formerly Framer Motion), the JS/React animation library. Real API reference. | Implementing any real React/JS animation that needs the actual current API surface — prefer this over relying on trained-in knowledge of the library, since APIs shift. |
| **Transitions.dev** (`transitions.dev`) | Ready-made page/element CSS+JS transitions with copyable code. | Need a specific transition (page transition, reveal, hover effect) as working code rather than building it from the motion vocabulary from scratch. |
| **Magicui** (`magicui.design`) | React + Tailwind + Motion animated components, shadcn-compatible. | Need a ready animated component — marquee, bento grid, shimmer effect, hero effect — rather than hand-building one. |
| **Smoothui** (`smoothui.dev`) | React + Tailwind + Motion animated UI components. | Polished micro-interaction components (similar trigger to Magicui — check both when the need is a drop-in animated component). |
| **ui.unlumen.com** | React + TypeScript + Tailwind + Motion component registry, installable via `shadcn` CLI. | Need a production-grade component installable directly into an existing shadcn-based project via `shadcn add`. |
| **Bklit** (`bklit.com`) | React chart / data-visualization component library + a visual "studio" export tool. Not a gallery — a real code source. | Building charts, dashboards, or any data-viz surface. |
| **hugeicons.com** | Large icon library (free + pro tiers), available as SVG, React components, or a package. | Need a consistent icon set, or a specific icon not covered by the default icon library (`SKILL.md`'s tech-stack default is Lucide — reach for hugeicons when Lucide doesn't have the needed glyph or a more distinctive icon set fits the direction). |
| **design.md ecosystem** (`design.md`, `getdesign.md`, `designmd.me`) | `DESIGN.md` — a plain-markdown design-system spec format (color/type/spacing/component tokens) that AI coding agents read to generate on-brand UI. `getdesign.md` hosts 300+ ready specs; `designmd.me` generates one from a URL. **The single most agent-native source in this list** — it's a format built specifically for this kind of pipeline to consume. | **Start of any build where a design system needs to be established or extracted from a reference.** Check `getdesign.md` for an existing spec matching the brief's direction before hand-deriving one from scratch; use a URL→spec generator when the brief references an existing site's system directly. |

## 2. Reference, not code-dump

| Source | What it is | When to pull |
|---|---|---|
| **component.gallery** | Cross-design-system reference — shows the same component (e.g. "date picker") as implemented across many established design systems, with naming and anatomy links. | "What's this component actually called" or "how do established systems structure X" — a naming/anatomy lookup, not a source of copy-paste code. |

## 3. Inspiration galleries — encoded as taxonomy, NOT live-fetched

These are live JS single-page apps or auth-walled catalogs — an agent fetch returns an empty shell,
not usable content. Their value is captured by encoding the *design-direction taxonomy* they
represent into `directions/*.md`, so the skill reasons from "what good looks like in this
category" without needing to fetch the site itself:

| Site | Category | What it informs |
|---|---|---|
| motionsites.ai | Motion-forward web | Feeds the motion taxonomy (`motion.md`) — what "great animation feel" looks like as a category, not individual examples to copy. |
| curated.design | Broad web design direction | General mood-setting reference for kicking off a visual direction. |
| landing.love | Landing pages | Marketing/landing layout archetypes — informs `reference/modes/landing.md`. |
| saaspo.com | SaaS sites & sections | B2B/SaaS pricing/feature/hero pattern taxonomy. |
| navbar.gallery | Navbars | Header/nav design taxonomy — component-sliced, maps directly to a skill category. |
| cta.gallery | CTA sections | CTA block design taxonomy — component-sliced. |
| appmotion.design | UI/app interaction animation | Feeds the motion taxonomy alongside motionsites.ai. |
| rebrand.gallery | Brand & rebrand showcases | Brand-system/identity mood reference — informs brand-register work. |
| mobbin.com | Mobile app UI + UX flow patterns | Real-world UX flow reference — primarily the *human's* research tool during a brief conversation, not something the agent fetches mid-pipeline. |
| Relic.so | Presumed curated design/landing gallery (unconfirmed — returns 403 to automated fetches) | Same category as the other galleries if it is one; treat as human-only regardless, since it hard-blocks agent access. |

**Highest-value taxonomy seeds** (because they're already sliced by component or page-type, which
maps cleanly onto this skill's own categories): navbar.gallery, cta.gallery, landing.love,
saaspo.com, rebrand.gallery. motionsites.ai + appmotion.design specifically feed the motion
taxonomy in `motion.md`. mobbin.com is explicitly the human's research surface, not the agent's —
don't attempt to fetch it as a pipeline step.

## 4. Wiring principle

The dividing line between §1 (live fetch) and §3 (taxonomy-only) is **fetchability, not
usefulness** — every gallery in §3 would be genuinely useful to fetch if it were fetchable; the
reason they're not wired as live sources is that a live SPA or auth wall returns nothing an agent
can use. If any of these sites later exposes a static, agent-fetchable surface (a public API, a
static export, a documented scraping-friendly mode), it moves from §3 to §1 — the categorization is
about current technical access, not a permanent judgment about the source's value.
