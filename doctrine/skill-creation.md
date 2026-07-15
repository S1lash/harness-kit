# Skill-creation checklist

> On-demand authoring meta. Read when authoring or modifying a skill.

## Required sections

- [ ] **Description** — what the skill does, when to use it (2-3 lines).
- [ ] **Arguments** — input parameters.
- [ ] **Preconditions** — start-time state the skill reads at runtime (not `@`-include).
- [ ] **Skill-bundled context** — `@knowledge/...` includes for each piece of workflow knowledge
      the skill needs (see "Loading" below).
- [ ] **Workflow** — numbered steps with explicit confirmation points.
- [ ] **Self-learning** — thin skill (default): a link to rules/self-learning.md + an instruction
      to update the skill on corrections. A skill that owns a knowledge domain carries its own
      domain routing and delegates the general tree. Not sure → thin.

## The add-skill critical gate (before authoring anything)

The person asks for a skill — this is **NOT a command to execute**, it's an entry into
evaluation (working-method.md → intent). Reclarify intent, then (first match stops):

1. **Already have one?** An existing skill covers this → reuse it, show which. Don't breed a
   duplicate.
2. **Close but missing a nuance?** → **extend / adjust the existing skill**, don't write a new
   one (Reuse before invent).
3. **Narrow / one-off?** Doesn't generalize → not a skill; do it inline, save nothing durable, or
   a one-line reference.
4. **Genuinely new + reusable?** → create it.

**Always justify** (reused / extended / declined / created, and why). The harness pushes back
with a reason before executing; the person can override.

## Confirmation points

At least one point where the agent waits for confirmation before an action with side effects
(creating a task, a commit, sending a message).

## Helper script (when needed)

A step that must be **deterministic, cheap, testable** (resolution, parsing, path/manifest
assembly, filtering) → a helper script; leave the LLM the **semantics and judgment**. The
script does mechanics, the model does meaning. Home: `tools/{skill}/`, runtime Python 3, stdlib,
self-contained, cross-platform (`pathlib`, no hardcoded paths). The skill does NOT repeat the
helper's logic — the SoT of the logic is the script. **Deterministic ≠ error-free**: the
consumer checks the helper's output against the raw source, doesn't trust it blindly.

## Conventions

- **Present only, not history** (rules/present-not-history.md): no "used to be / became",
  changelog lines, issue / phase tags in prose. Describe how it should be now.
- **Rails, not frames**: the skill teaches to think "what matters for THIS task". Tables marked
  open / illustrative; examples with a domain-agnostic caveat. Deep systemic knowledge by
  doctrine/deep-knowledge-pattern.md.
- **Self-sufficient — no backward ADR references** (chase-bait): name a constraint by name, not
  by an ADR number.

## Self-check "Rails, not frames"

- [ ] **Each table** — a closed classifier or an open illustration? A closed taxonomy where the
      task needs judgment → rewrite into a method-question + mark the table open. A closed set (a
      catalog of what exists) is legitimate.
- [ ] **Each example** — has a domain-agnostic caveat ("illustrates a principle, not a template
      to copy")?
- [ ] **Deep systemic knowledge** documented by Model + Method + Pointer, not a flat snapshot?
- [ ] **Extracted = only data, not rails** — only large content / output schemas extracted;
      thinking rails (gates, modes, dialogue grammar, state/resume) stay inline? A reusable rail
      extracted only with 2+ real consumers?
- [ ] **A skill with judgment is a co-designer, not a generator** — proposes + justifies, the
      choice is the person's / the task's? A purely mechanical skill (thin wrapper, scaffolding)
      is legitimately a generator.
- [ ] **Jargon unpacked** — would anyone understand it?
- [ ] **Home of a fact by the object** — the skill does NOT embed an external tool's mechanics
      (field IDs, curl/REST/SDK, auth), those are in the tool's home; the skill links.
- [ ] **Cross-platform** — any script / path / hook / symlink / command works on every platform
      and agent runtime (rules/cross-platform.md).
- [ ] **Link to the home-SoT, not a neighbouring consumer skill.**

## Loading knowledge files — three layers

| Layer | What | Who loads |
|---|---|---|
| **Hot** (auto-load via the base `CLAUDE.md`) | Needed BEFORE choosing a skill or to interpret speech | base `CLAUDE.md` via `@` |
| **Skill-bundled** | A skill's workflow context | the skill via `@knowledge/...` |
| **Index** | Reference, read on demand | an explicit `Read` when the topic surfaces |

Skill-bundled is your main pattern: in the skill body, at the phase where the context is needed:
`Load <what>: @knowledge/<domain>/<file>.md`. The `@`-include is resolved at launch — more
reliable than "the model will read it itself", cheaper than keeping it hot for all sessions.
Anti-patterns: adding `@knowledge/foo.md` hot "just in case"; adding it to a skill that never
uses foo; relying on "the model will read it itself" for critical workflow context.

## Acceptance — before "done"

A skill is a prompt the model will execute. "Written" ≠ "works".

- **Run it end-to-end** on a real case — not "read it, looks right".
- **A fresh agent = the self-sufficiency test:** execute the skill in a sub-agent with NO context
  of this session — only the skill text. Can't execute without guessing → under-specified.
- **Adversarially test the deterministic parts:** empty input, whitespace, unicode junk, typos,
  ambiguity, missing file — no crashes, no silent wrong outputs.
- **Degradation of every branch:** spell out the degenerate sub-case, or give one fallback rule
  (a method, not a matrix). Don't describe only the happy path.
- **Stale local state:** a skill deciding by LOCAL state ("already there?") reconciles with the
  source of truth BEFORE concluding "new".
- **An expensive run — not blind:** surface the cost + validate on a proof slice (1-2 units)
  first.

## Registration

Register the command under `commands/` (+ a helper under `tools/{skill}/` if you added one). If the
decision to add the skill embodies a non-trivial choice, record it in `knowledge/decisions.md` (a
mechanical thin skill needs none).
