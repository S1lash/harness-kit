# Discovery Questions — pinning an ambiguous brief

*Ask before drawing: audience, scope, format, and variation intent, whenever the brief doesn't already answer them.*

Fires when INTAKE (`SKILL.md` step 0) resolves provenance to greenfield or handoff-export but the brief itself is too thin to seed a `design_plan` — vague subject, no register signal, no scope boundary. Not every greenfield build needs this: a brief that already states audience, page count, and tone skips straight to GROUND & AUTO-DIRECT.

## When to ask vs when to proceed
- Request names a subject and a format clearly enough to infer register and scope → **proceed**, don't manufacture questions for their own sake.
- Request is genuinely underdetermined on one or more axes below → **ask, in one batch**, not one question at a time.

## Question set (ask only the axes that are actually unresolved)

**Audience**
- Who lands on this page — a specific buyer persona, technical evaluators, general public?
- Are they cold traffic (need convincing) or already-interested (need information)?

**Scope**
- One page or a small site (how many distinct pages/sections)?
- Is this the whole product surface, or one flow inside a larger existing app?

**Format**
- Landing page, app UI, standalone component, or presentation? (Format changes which mode ruleset applies — `reference/modes/*.md`.)
- Any format constraint already decided — framework, existing design system, must-match brand?

**Variations**
- One direction, or should this launch with 2-3 options to choose between? (Routes to `procedures/generate-variations.md` if yes.)
- Is there a competitor/reference site the user wants to differentiate from or partially mirror?

## After answers land
Fold the answers directly into GROUND (`SKILL.md` step 1) — audience and scope inform register (brand vs product) and content plan; format confirms the mode; variation intent routes to the multi-variation procedure. Don't re-ask what the brief already told you.
