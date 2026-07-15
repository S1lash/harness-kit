# Improve-Existing — walkthrough

*Run `context.mjs`, consume its token/theming output, produce a DELTA plan (never from-scratch), apply respecting the existing system.*

Fires when INTAKE (`SKILL.md` step 0, precedence rule 3) classifies provenance as improve-existing: CWD
is a code repo (`package.json` OR `src/` OR ≥2 component files) AND the request verb is edit-class
(«улучши / добавь / переделай / fix / restyle»). This is the mode where auto-direction is **suppressed**
— the existing design vocabulary is the ground truth, not a fresh direction pick.

## 1. Run `scripts/context.mjs` — mandatory, first step

Invoke with `{ projectPath, provenance: "improve-existing", mode }`.

The script crawls the existing codebase down a **ladder of crawl-targets**, first match wins:
1. CSS custom properties (`--*`) — the strongest signal, use these as-is.
2. `tailwind.config.*` `theme.extend` — second choice when no CSS custom properties exist.
3. CSS-in-JS theme objects — third choice.
4. Inline hex/rgb frequency scan — last resort, infers a palette from repetition.

It also extracts the **theming mechanism** — `darkMode: class|media`, a `next-themes` provider,
`data-theme` attribute usage — so any dark-mode work added later plugs into the *existing* mechanism
instead of introducing a second, parallel one.

**Zero-token fallback:** if the crawl finds nothing usable, degrade to a *muted* greenfield auto-direct
— but this MUST be flagged explicitly in the delta plan ("no existing system found — proposing one"),
never silently treated as if tokens were found.

## 2. Consume the output

`context.mjs` returns:
```
{ tokens: { color, type, space, radius }, theming, conventions, drift: [], confidence }
```
- `tokens` seeds every design decision from here on — don't re-derive a palette or type pairing from
  scratch when `tokens.color`/`tokens.type` are populated.
- `conventions` (naming patterns, component structure already in use) governs how new code is written —
  match the existing pattern, don't introduce a competing one.
- `drift` is empty on a first run (it's populated on **resume**, when a `.crafter/` sidecar already
  exists and the live code has diverged from what was recorded). On a fresh
  improve-existing run with no sidecar, ignore this field.
- `confidence` reflects how far down the crawl-target ladder the script had to go — surface a low
  confidence to the user rather than silently proceeding as if the tokens were certain.

## 3. Produce a DELTA plan, not a from-scratch plan

Per the `design_plan` sizing rule, improve-existing gets the smallest plan format: a
**one-line delta** stating what changes and what's preserved — not the full greenfield block. Example
shape: *"Change: add a settings drawer using the existing `--surface`/`--accent` tokens and card
convention. Preserve: nav structure, type scale, spacing scale — untouched."*

Do not re-litigate axes the existing system already answers (font, palette, radius, spacing scale) —
those are inherited, not re-decided. Only the axes genuinely introduced by this request (new component,
new section, new state) go through GROUND & AUTO-DIRECT-equivalent reasoning, and even then, biased
toward matching the existing direction rather than introducing a new one.

## 4. Apply, respecting the existing system

- New code follows `conventions` from step 2 — same naming, same component structure, same utility
  patterns already in the repo.
- New tokens (if genuinely needed) are added alongside the existing token set, not as a parallel system
  — extend `tokens.color`/`tokens.type`, don't shadow them.
- Contracts (`reference/contracts/*.md`) still apply in full — improve-existing does not relax
  accessibility, performance, or forms requirements just because it's touching less surface area.

## 5. Dual-pass verify if dark mode is touched

If this change adds or touches dark-mode-relevant surfaces, the VERIFY step (`SKILL.md` step 4) runs
its screenshot/vision pass **twice** — once in light, once in dark — using the theming mechanism
identified in step 1 to actually toggle the mode (not a CSS override hack). This prevents shipping a
change that looks right in light mode only because dark mode was never rendered.

## Output

`context.mjs` owns writing Tier-2 state (`~/.frontend-crafter/projects.jsonl` upsert,
`design-memory.jsonl` append, registry self-heal). The agent — not the script — writes the Tier-1
sidecar content (`design-system.md`, `design-plan.md`, `decisions.md`, `snapshots/`) directly via the
Write tool after BUILD/VERIFY complete.
