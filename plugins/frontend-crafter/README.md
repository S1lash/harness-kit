# frontend-crafter

A Claude Code plugin that turns a plain-language request — *"make a landing page for X"*,
*"улучши эту страницу"*, *"сделай презу-лендинг"* — into distinctive, production-grade frontend UI.
It pushes hard against templated AI-slop: it commits to a design **direction**, emits an inspectable
**plan** you can veto, builds with real **contracts** (performance, accessibility, forms, dark-mode,
security), and **verifies** the result visually.

## What makes it different

- **Request-first.** You describe what you want; it designs. Refinement is conversational
  (*"смелее"*, *"тише"*, *"добавь motion"*, *"поменяй акцент"*).
- **Provenance-aware.** Greenfield (new site), improve-existing (edits your repo in its own style),
  or handoff (productionize a Figma/HTML export) — each is a first-class path.
- **Anti-slop by construction.** A menu of committed aesthetic directions, a quantified ban list,
  and a deterministic direction-selection rubric — the default *is* the slop, so it refuses to default.
- **Motion depth.** A real animation craft engine (easing curves, timing, springs) plus a standalone
  `motion-review` skill that audits and names motion.
- **Honest enforcement.** Mechanically-checkable rules (banned fonts, viewport bugs, token-pair
  contrast) run as a real lint that works even headless; taste is judged by a pluggable visual loop.
- **Longevity.** Every project keeps a local `.crafter/` design system + plan + snapshots, so you can
  resume and maintain it months later.

## Install

```
/plugin marketplace add <git-url-of-this-repo>
/plugin install frontend-crafter
```

Then just ask for a design in any project or a fresh directory.

**Private repo?** The repo owner grants you access first — as a repository collaborator, or via a
read-only deploy token — before you run `/plugin marketplace add`. Access to the plugin = access to
the repo.

## Update

```
/plugin update frontend-crafter
```

Versions follow semver; a major bump signals a breaking change, a minor/patch is additive.

## Recommended: disable the official `frontend-design` skill

This plugin absorbs and extends the official Anthropic `frontend-design` skill's philosophy. If both
are active they double-activate on design requests. Disable the official one while this is installed.

## Configuration

On first build, `~/.frontend-crafter/config.json` is created with sensible defaults. Notable keys:

- `projects_home` — where new projects are scaffolded (default `~/frontend-crafter-projects`).
- `hook_enabled` — turn on the optional post-write lint hook (default `false`).
- `auto_git_init` — `git init` new projects (default `false`).

Your project state lives in two places: a per-project `.crafter/` sidecar (moves with the project)
and the global `~/.frontend-crafter/` registry (survives plugin updates).

## Structure

```
skills/frontend-crafter/   the request-first pipeline (SKILL.md) + reference/ + directions/ + contracts/
skills/motion-review/      standalone motion audit + vocabulary
scripts/                   lint.mjs (mechanical gate) · context.mjs (existing-system crawl + persistence)
```

## Credits

A synthesis — see `ATTRIBUTION.md`.

MIT — see `LICENSE`.
