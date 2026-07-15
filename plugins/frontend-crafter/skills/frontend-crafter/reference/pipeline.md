# Pipeline Reference (machinery)

The mechanical detail behind `SKILL.md`'s pipeline steps — provenance classification, target-path
resolution, the `design_plan` schema, and the verify flow. `SKILL.md` is the spine; this file is
what each step actually does when it needs more than a one-line summary.

## 1. Provenance classification — precedence order

Computed in INTAKE before anything else. **First match wins:**

1. **Explicit target path in the request** → use it directly, skip inference.
2. **Target/CWD contains `.crafter/`** → **resume**. Provenance is inferred from the sidecar's
   presence, never asked — a `.crafter/` folder is unambiguous proof this project was built by
   this skill before.
3. **CWD is a code repo** (`package.json` OR a `src/` directory OR ≥2 recognizable component
   files present) **AND** the request's verb is edit-class («улучши / добавь / переделай / fix /
   restyle») → **improve-existing**.
4. **Request matches a create-pattern** («сделай / создай / make … сайт / лендинг / презу / site /
   landing про X») **with no repo signal present** → **greenfield**.
5. **Figma/HTML/URL export provided as input** → **handoff-export**.
6. **Ambiguous** — a repo is present but the verb is create-class, or the request is vague with no
   clear signal either way («сделай красиво») → **ASK one clarifying line, do not guess.** Example:
   *«Ты в репозитории — улучшить существующую страницу или сделать новый сайт с нуля?»* This is a
   direct application of the owner's HARD RULE «понять намерение прежде действия» — a wrong
   provenance guess burns the whole downstream pipeline (wrong crawl-vs-seed choice, wrong sidecar
   behavior), so the one-line question is cheap insurance against an expensive silent mistake.

## 2. Greenfield target-path resolution

Subject → slug (translit to ASCII, kebab-case) → `{projects_home}/{slug}`. `projects_home` reads
from `~/.frontend-crafter/config.json`, defaulting to the generic `path.join(os.homedir(),
'frontend-crafter-projects')` — never a hardcoded personal path (that would leak into a
shared/distributed plugin). Collision check against both the registry (`~/.frontend-crafter/
projects.jsonl`) and the filesystem: if the slug already exists, either suffix it (`-2`) or offer
to resume the existing project instead — never silently overwrite. No automatic `git init` — VCS
setup is left to the user (`auto_git_init: false` by default, config-overridable).

## 3. Full-auto vs veto-gate rule

- **No wishes stated AND provenance unambiguous** → emit a non-blocking plan summary and proceed
  straight to BUILD in the same turn. The plan is still shown (so the commitment is inspectable),
  it just doesn't block execution waiting for a response.
- **Any wish, any ambiguity, or an explicit «покажи план сначала»** → **block** and wait for the
  user to respond auto / tweak one axis / veto one axis before building.

This asymmetry exists because a clear, unambiguous request costs the user nothing to auto-proceed
on (they can still veto after seeing the summary), while an ambiguous or wish-laden request risks
building the wrong thing entirely if the pipeline guesses instead of confirming.

## 4. Wish parsing & axis pinning

Explicit keywords in the request are **hard pins per axis**, not soft signals the auto-direction
logic can override:

- Aesthetic keyword («минималистично», «брутально», «editorial») → pins `direction`.
- Motion keyword («плавный скролл», «без анимаций», «живой») → pins `motion` / `MOTION_INTENSITY`.
- Palette/type keyword («тёплый терракот», «моно-шрифт») → pins that specific axis.

**Rules:** auto-direction (`directions/_catalog.md`) fills **only unpinned** axes. The
anti-repetition bias from `design-memory.jsonl` fires **only on unpinned** axes — a pinned choice
is the user's explicit intent and is never second-guessed by a recency heuristic. `design_plan`
marks every axis `[pinned | auto | bias-adjusted]` so a later veto is meaningful — the user can
distinguish "I said this" from "the engine picked this," which matters because vetoing a `pinned`
axis is a real correction while vetoing an `auto` axis is just steering.

## 5. `design_plan` — canonical schema

`.crafter/design-plan.md` — one field set, referenced by every downstream step (BUILD reads it
literally; VERIFY compares the built artifact against it via vision; REFINE verbs read/mutate it):

```
subject, provenance, mode, build_stack
register            (brand | product)
direction           {name, source: pinned|auto|bias}
dials               {variance:1-10, motion:1-10, density:1-10}   (reference/dials.md)
palette             {named OKLCH tokens; fg/bg pairs listed for contrast lint}
type                {display, body, mono?, source}
motion_thesis       (2-3 intentional motions)
signature           (the one memorable element)
content_plan        (section → job)
```

**Sizing by provenance:**
- **Greenfield / ambiguous** → the full block above.
- **Improve-existing** → a one-line **delta**: what changes, what's explicitly preserved. Not the
  full schema re-stated — improve-existing inherits the existing system's values for anything not
  named in the delta.
- **Handoff** → an **audit-list** — what was extracted from the export and what violated a
  contract/ban, not a from-scratch design commitment.

The plan is always emitted regardless of provenance; only its *size* adapts.

## 6. Auto-direction selection rubric

Lives in `directions/_catalog.md` as the executable rubric; summarized here for cross-reference.
Deterministic and logged — never a self-reported "I rolled the dice" claim with no verifiable
trail:

1. **Subject-signal → candidate direction set** (illustrative, not closed): artisan/food/craft/
   local → {soft, editorial}; fintech/dev-tool/dashboard → {minimalist, app}; edgy/music/dev-
   culture → {brutalist}; luxury/fashion → {editorial, soft}. Subject with no clear signal → all
   directions are candidates.
2. **Register gate** — a brand-register brief widens the candidate set; a product-register brief
   narrows it toward minimalist/app-appropriate directions.
3. **Exclude saturated lanes** — drop candidates that default to the editorial-serif-cluster or
   cream+terracotta cluster (`anti-slop.md` §1) unless the brief explicitly demands them.
4. **Anti-repetition** — drop candidates matching the recent-N directions logged for *similar*
   briefs in `design-memory.jsonl`. Applies only to unpinned axes (§4 above).
5. **Tie-break** — a deterministic hash of the brief string, modulo the finalist count, picks the
   winner. The index is **logged to `design-memory.jsonl`** — reproducible and auditable, not a
   model self-report of "I picked randomly" (which can't be verified or reproduced).
6. **Governance** — adding a genuinely new direction (a 5th, 6th, ...) is an owner-only action; a
   new direction file must carry a base+delta structure and pass a golden-brief eval before it's
   added to the candidate set — prevents ad-hoc taste drift accumulating silently over time.

## 7. Default build stack per mode (D8)

| Mode | Default stack |
|---|---|
| landing | Static HTML/CSS + vanilla JS, unless the project already dictates a framework. |
| presentation | Static HTML/CSS + vanilla JS. |
| component | Static HTML/CSS + vanilla JS, unless building into an existing framework-based design system. |
| app-ui | The project's existing framework, React as the default when none is established. |

A framework-based build (app-ui, or any mode where the project already has a framework) requires a
**dev-server bootstrap step before screenshot** in the verify flow (§8) — the static-file path
skips this because there's nothing to serve beyond opening the file directly.

## 8. Verify flow — detail

Runs after BUILD, before delivery:

1. **`scripts/lint.mjs` — always, even fully headless.** Reads `bans.json`, blocks on any
   `severity: block` violation. Includes **token-pair contrast**: the WCAG ratio computed on the
   fg/bg token pairs declared in `design_plan.md` — pure JS, no rendering needed, so this check
   never has a "no browser" gap.
2. **If Chrome MCP (or equivalent browser automation) is present:**
   - Navigate to the built page, screenshot.
   - **(a) Two-image vision-diff** against `.crafter/snapshots/{last}.png` — regression check
     ("did the hero break") judged by comparing the new render to the stored baseline via vision,
     since there's no pixel-diff script; this is the honest substitute for automated visual
     regression tooling.
   - **(b) Vision-vs-intent** — compare the rendered page against `design_plan.md`'s stated
     commitment (does it actually look like what was planned).
   - **Dual-pass in dark mode** if the dark-mode contract fired for this build (`reference/
     contracts/dark-mode.md`) — run (a) and (b) again against the dark variant.
   - Save the new frame to `.crafter/snapshots/` for the next resume's regression baseline.
3. **If no browser is available:** fall back to **static-critique** — 4 subagents run in parallel
   (`procedures/polish-pass.md`): (1) hierarchy/rhythm, (2) AI-slop visual (patterns readable from
   source), (3) a11y-static (landmarks, heading order, `label for`, tabindex — everything
   statically checkable), (4) copy/editorial (em-dash judgment, cliché tics, product-language per
   `copy.md`). This is the **honest floor** — snapshot regression and text-on-image contrast are
   genuinely unavailable without rendering, and the pipeline says so explicitly rather than
   implying parity with the browser-present path.

Aggregate lint findings + review findings into one list → prioritize (blocker / quality / polish,
per `procedures/polish-pass.md`'s triage) → fix → re-verify affected checks.

## 9. `context.mjs` contract (improve-existing / resume)

The load-bearing script behind non-greenfield provenance:

- **Mode A — resume** (`.crafter/` present): read `design-system.md` + `state.json`, then
  **drift-check** — diff the recorded token values against a live crawl of the actual CSS in the
  repo. On a `crafter_version` mismatch in `state.json`, warn and force a full re-crawl rather than
  trusting the stale sidecar.
- **Mode B — improve-existing** (no sidecar yet): crawl-target ladder, first source that yields
  usable tokens wins: (1) CSS custom properties (`--*`), (2) `tailwind.config.*` `theme.extend`,
  (3) CSS-in-JS theme objects, (4) inline hex/rgb frequency scan as the last resort. If none yield
  anything, **degrade to a muted greenfield auto-direct**, explicitly flagged in the delta plan
  ("no existing system found — proposing one") rather than silently pretending a system was found.
  Also extracts the **theming mechanism** in use (`darkMode: class|media`, a `next-themes`
  provider, `data-theme` attribute convention) so any new dark-mode work matches the existing
  approach instead of introducing a second, parallel mechanism.
- **Write ownership:** `context.mjs` owns Tier-2 I/O (`projects.jsonl` upsert, `design-
  memory.jsonl` append, registry self-heal) and reads Tier-1 sidecar content. The agent — not the
  script — writes Tier-1 sidecar files (`design-system.md`, `design-plan.md`, `decisions.md`,
  `snapshots/`) directly via the Write tool after BUILD/VERIFY.
