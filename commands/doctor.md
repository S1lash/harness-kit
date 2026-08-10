---
description: Report-only health check of this base. Verifies the canon is wired hot into every agent's global entry point and named identically on each, the knowledge/activities/tools indexes exist, every local MCP server is wrapped, profile.md has a language, and the sibling projects/ exists. Reports PASS / WARN / FAIL and fixes nothing.
---

# /harness:doctor

Self-check of this base. Reads state, reports findings, **fixes nothing** — the agent or the
relevant flow fixes what it surfaces.

## Checks (each → PASS / WARN / FAIL)

1. **Canon is hot.** The agent's global entry point (Claude `~/.claude/CLAUDE.md`, Codex
   `~/.codex/AGENTS.md`, Cursor user rules) imports/points at this base's `rules/` and names
   the harness home path. FAIL if the canon would not load from an arbitrary folder.
2. **Canon parity across agents.** The file list in `rules/`, the `@rules/...` list in
   `CLAUDE.md`, and the canon list in `AGENTS.md` name the same set. Any rule present in one
   and missing from another is a FAIL naming the file and the surface that lacks it — that
   rule is silently not in force for at least one runtime (`rules/multi-agent.md`).
3. **Indexes present.** `knowledge/_index.md`, `activities/_index.md`, `tools/_index.md`
   exist and parse.
4. **MCP wrapped.** Every local MCP server (Docker / npx / native) in the agent's MCP config
   routes through `tools/mcp-wrapper.js`. An unwrapped local server is a FAIL
   (`doctrine/tool-vs-instrument.md`). Remote / SSE / URL servers are exempt.
5. **Profile ready.** `profile.md` exists and has a `Language:` value.
6. **Workspace shape.** A sibling `projects/` exists beside this base.
7. **No drift.** Anything the canon requires but the base lacks (a rule file missing, a dead
   pointer) → WARN with the specific gap.

## Output

A short PASS/WARN/FAIL list in the person's language, then a one-line verdict. Never mutate.
