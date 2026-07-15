# App UI Rules

*Product/dashboard surfaces: Linear-style restraint, mechanical hierarchy, utility copy — nothing campaign-style.*

Default approach: **"Linear-style restraint"** — calm surface hierarchy, strong typography and spacing, few colors, dense but readable, minimal chrome.

## Structure
- Primary workspace + navigation + secondary context/inspector.
- One clear accent for action or state.
- Cards only when the card IS the interaction (task card, kanban item, etc.).

## Avoid in App UI
- Dashboard-card mosaics as default layout.
- Thick borders on every region.
- Decorative gradients behind routine product UI.
- Multiple competing accent colors.
- Ornamental icons that don't improve scanning.

## Utility Copy (dashboards, admin, tools)
- Headings say what the area IS or what the user CAN DO: "Selected KPIs", "Plan status", "Search metrics".
- No aspirational hero lines, metaphors, or campaign-style language.
- **Litmus check**: if an operator scans only headings, labels, and numbers, can they understand the page?

## Hierarchy — combinatorial signals
Hierarchy is not declarative («make it strong») — it's mechanical. Five signals you combine:

- **Size** — largest = most important. Similar sizes flatten hierarchy.
- **Color** — saturated brand color = primary action. Muted = supporting. Light gray = de-emphasized.
- **Weight** — bold for headlines, regular for body. Everything bold = nothing stands out.
- **Position** — top-left first (LTR languages). Primary content in prime real estate, never buried bottom-right.
- **Density** — loose spacing AROUND important elements signals «pay attention». Tight = supporting.

**Combine for strongest effect:**
- Primary action = large + bold + brand color + prominent position + loose spacing around it
- Fine print = small + light + neutral + tight + tucked
- Reversed signals (cramped CTA, brightest fine print) = critical bug

**5-second test:** a first-time user should understand the screen's main action within 5 seconds. If the eye has to hunt — hierarchy is wrong. Run this mentally before shipping.

## State visibility (non-trivial — separate from the loading/empty/error catalog)
Selected tab, active page, current filter, chosen option must be **visually distinct**. If everything looks the same, the user can't tell where they are or what they've selected. This is about *current* state, always visible — distinct from `reference/interaction-states.md`.
