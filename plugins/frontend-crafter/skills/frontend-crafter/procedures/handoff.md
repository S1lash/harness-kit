# Handoff Mode — arriving with a template/export

*Extract tokens → audit against hard rules → productionize. Preserve composition; fix integrity.*

Triggered when input is an existing design artifact (Claude Design export, Figma handoff, `.html` prototype, screenshot + assets). The visual thesis is already decided — the job shifts from «invent» to «extract, audit, productionize».

## Two handoff intents — classify from the request verb (E2E finding, 2026-07)

Handoff is not always «keep the look, fix integrity». Read the verb:

- **Productionize** («доведи до прода», «почини», «clean up», «make it production-ready») — the
  DEFAULT below. Preserve the visual thesis; fix integrity only. `design_plan` = an **audit-list**.
- **Redesign / re-skin** («редизайн», «сделай новую версию», «в новом стиле», «redesign», «re-skin»)
  — the artifact's **visual direction is deliberately replaced**, but its content, structure,
  interactivity, and real data stay ground truth. Here **auto-direction runs** (pick a fresh
  direction via `directions/_catalog.md`), and `design_plan` is a **full block** (not an audit-list),
  stated for veto. Sections 1 (extract) + 5 (preserve content/structure/data) still apply; section 3
  (productionize) becomes «rebuild the visual layer in the new direction». Reuse the artifact's
  working interactive JS behavior — behavior is ground truth even when the skin changes.

If the artifact is already clean (no slop to fix) and the verb is redesign, the value is the new
direction — don't treat it as an integrity pass.

## 1. Extract tokens
Pull colors, fonts, radius, spacing, shadows out of inline styles into `globals.css` / `tailwind.config`. Never leave hardcoded hex values in components after handoff.

## 2. Audit against Hard Rules
Run the template through the Integrity litmus checklist (`procedures/polish-pass.md`) against `bans.json`. List violations explicitly: fabricated data, `h-screen`, pure `#000`, Inter/Roboto, generic serifs, missing `alt`, broken image URLs, missing error/empty states. Report before refactoring.

## 3. Productionize
Exports are prototypes, not production:
- Replace inline styles with tokens / utility classes.
- Add loading / empty / error states (prototypes ship only the happy path) — `reference/interaction-states.md`.
- Fix hard-rule violations from the audit.
- Swap broken image URLs for picsum / local assets.
- Add `prefers-reduced-motion` handling if motion is present.

## 4. Conflict rule
Frontend-crafter Hard Rules **always** beat exported styling. If the export uses pure `#000` or `h-screen`, translate to Zinc-950 / `min-h-[100dvh]` without asking. If the export uses Inter, replace with the nearest approved font (`reference/type.md`). Treat the export as intent, not as the final styling contract.

## 5. Preserve what works
Composition, hierarchy, copy, and visual anchor from the export are the ground truth. Don't re-design; only fix integrity and code quality.

## Sizing note
The `design_plan` emitted for a handoff-provenance build is an **audit-list** (not a full block or a delta line) — the violations found in step 2, each mapped to the fix applied in step 3.
