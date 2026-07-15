---
description: Report-only health check of this base. Verifies the canon is wired hot into the agent's global entry point, the knowledge/activities/tools indexes exist, every local MCP server is wrapped, profile.md has a language, and the sibling projects/ exists. Reports PASS / WARN / FAIL and fixes nothing.
---

# /harness:doctor

Self-check of this base. Reads state, reports findings, **fixes nothing** — the agent or the
relevant flow fixes what it surfaces.

## Checks (each → PASS / WARN / FAIL)

1. **Canon is hot.** The agent's global entry point (Claude `~/.claude/CLAUDE.md`, Codex
   `~/.codex/AGENTS.md`, Cursor user rules) imports/points at this base's `rules/` and names
   the harness home path. FAIL if the canon would not load from an arbitrary folder.
2. **Indexes present.** `knowledge/_index.md`, `activities/_index.md`, `tools/_index.md`
   exist and parse.
3. **MCP wrapped.** Every local MCP server (Docker / npx / native) in the agent's MCP config
   routes through `tools/mcp-wrapper.js`. An unwrapped local server is a FAIL
   (`doctrine/tool-vs-instrument.md`). Remote / SSE / URL servers are exempt.
4. **Profile ready.** `profile.md` exists and has a `Language:` value.
5. **Workspace shape.** A sibling `projects/` exists beside this base.
6. **No drift.** Anything the canon requires but the base lacks (a rule file missing, a dead
   pointer) → WARN with the specific gap.

## Output

A short PASS/WARN/FAIL list in the person's language, then a one-line verdict. Never mutate.
