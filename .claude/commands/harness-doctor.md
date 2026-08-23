---
description: Report-only health check of this base. Verifies the canon is wired hot and named identically for every agent, the indexes exist, the base can actually reach the person's other devices, every local MCP server is wrapped, and profile.md has a language. Reports PASS / WARN / FAIL and fixes nothing.
---

# /harness-doctor

Self-check of this base. Reads state, reports findings, **fixes nothing** — the agent or the
relevant flow fixes what it surfaces.

## Checks (each → PASS / WARN / FAIL)

1. **Canon is hot.** The canon reaches you in this session. On a machine the person installed on,
   that is the agent's global entry point (Claude `~/.claude/CLAUDE.md`, Codex `~/.codex/AGENTS.md`,
   Cursor user rules) naming this base. In a session that starts from a fresh clone of the base,
   `CLAUDE.md` at the repo root carries it and no global wiring exists — that is PASS, not FAIL.
2. **Canon parity across agents.** The file list in `rules/`, the `@rules/...` list in `CLAUDE.md`,
   and the canon list in `AGENTS.md` name the same set. Any rule present in one and missing from
   another is a FAIL naming the file and the surface that lacks it — that rule is silently not in
   force for at least one runtime (`rules/multi-agent.md`).
3. **The base is one thing.** The repository root is the base root, `projects/` is inside it, and
   nothing important sits outside. A `projects/` folder beside the base instead of inside is a FAIL:
   nothing there can ever reach the person's phone.
4. **The base can reach their other devices.** Run `python3 tools/sync.py status`. No remote at all
   is a FAIL — their base exists on one machine only. Unsaved work or changes that never went out
   is a WARN with what is sitting here. More than one branch is a WARN
   (`rules/device-sync.md`).
5. **Sessions catch up on their own.** `.claude/settings.json` runs `tools/sync.py` at session
   start, and `python3` is available to run it. Missing either is a WARN, not a FAIL — the canon
   still requires you to do it by hand.
6. **Every project has a contract.** Each directory under `projects/` has `AGENTS.md`, a
   `CLAUDE.md` importing it, and its own `.claude/`. A project without one is a WARN naming it —
   the next session that opens it starts blind (`doctrine/project-home.md`). Each is also a row in
   `projects/_index.md`; a project missing from the index is the same WARN.
7. **The kit half can still be updated.** `.engine-manifest.yml` and `VERSION` exist, the
   `harness-kit` remote is configured, and `version:` in the manifest matches `VERSION` and
   `.claude-plugin/plugin.json`. A base with no kit remote can never receive a fix — FAIL. A
   version mismatch between the three is a FAIL: the updater's own post-condition will refuse the
   next update.
8. **Nothing personal sits in a kit path.** Spot-check the paths the manifest lists under
   `engine:` for anything the person or their agent wrote — it survives exactly until the next
   update (`doctrine/kit-ownership.md`). Any find is a FAIL naming the file and its real home.
9. **Indexes present.** `knowledge/_index.md`, `activities/_index.md`, `tools/_index.md`,
   `projects/_index.md` exist and parse.
10. **MCP wrapped.** Every local MCP server (Docker / npx / native) in the agent's MCP config routes
   through `tools/mcp-wrapper.js`. An unwrapped local server is a FAIL
   (`doctrine/tool-vs-instrument.md`). Remote / SSE / URL servers are exempt.
11. **Profile ready.** `profile.md` exists and has a `Language:` value.
12. **No drift.** Anything the canon requires but the base lacks (a rule file missing, a dead
   pointer, a person's fact sitting in a kit-owned path — `doctrine/kit-ownership.md`) → WARN with
   the specific gap.

## Output

A short PASS/WARN/FAIL list in the person's language, then a one-line verdict. Never mutate.
