---
description: Report-only health check of this base. Verifies the canon is wired hot and named identically for every agent, the indexes exist, the base can actually reach the person's other devices, the kit half is updatable and portable, every local MCP server is wrapped, and profile.md has a language. Reports PASS / WARN / FAIL and fixes nothing.
---

# /harness-doctor

Self-check of this base. Reads state, reports findings, **fixes nothing** — the agent or the
relevant flow fixes what it surfaces.

## Checks (each → PASS / WARN / FAIL)

1. **Canon is hot.** The canon reaches you in this session. On a machine the person installed on,
   that is the agent's global entry point (Claude `~/.claude/CLAUDE.md`, Codex `~/.codex/AGENTS.md`,
   Cursor user rules) naming this base. In a session that starts from a fresh clone of the base,
   `CLAUDE.md` at the repo root carries it and no global wiring exists — that is PASS, not FAIL.
2. **Canon complete, and listed once.** Every file in `rules/` appears in the canon list in
   `AGENTS.md` — the one hand-maintained list. A rule missing there is a FAIL naming it: it is
   silently not in force for every runtime. A second copy of the list anywhere else is also a FAIL
   — it drifts, and the person goes on believing a rule applies (`rules/multi-agent.md`).
   `python3 tools/check_kit.py` proves both.
3. **The base is one thing.** The repository root is the base root, `projects/` is inside it, and
   nothing important sits outside. A `projects/` folder beside the base instead of inside is a FAIL:
   nothing there can ever reach the person's phone.
4. **The base can reach their other devices.** Run `python3 tools/sync.py status`. No remote at all
   is a FAIL — their base exists on one machine only. A remote reported **PUBLIC** is a FAIL
   before anything else: everything the person has ever saved is readable by anyone, and the kit
   asserted "private" only once, at creation. A visibility it could not establish is reported as
   unverified, never as private. Unsaved work or changes that never went out
   is a WARN with what is sitting here. More than one branch is a WARN
   (`rules/device-sync.md`).
5. **The machinery still works.** `python3 -m unittest discover -s tools/tests` passes. A failure
   here is a FAIL naming the test: something in this base's own tooling is broken, and it will
   surface as a lost save or a silently empty update rather than as an error.
6. **Sessions catch up on their own.** `.claude/settings.json` runs `tools/sync.py` at session
   start, and `python3` is available to run it. Missing either is a WARN, not a FAIL — the canon
   still requires you to do it by hand.
7. **Every project has a contract.** Each directory under `projects/` has `AGENTS.md`, a
   `CLAUDE.md` importing it, and its own `.claude/`. A project without one is a WARN naming it —
   the next session that opens it starts blind (`doctrine/project-home.md`). Each is also a row in
   `projects/_index.md`; a project missing from the index is the same WARN.
8. **The kit half can still be updated.** `.engine-manifest.yml` and `VERSION` exist, the
   `harness-kit` remote is configured, and `version:` in the manifest matches `VERSION` and
   `.claude-plugin/plugin.json`. A base with no kit remote can never receive a fix — FAIL. A
   version mismatch between the three is a FAIL: the updater's own post-condition will refuse the
   next update.
9. **The kit half still runs everywhere.** `python3 tools/check_portability.py`. Every file the
   kit ships is checked against the machine-checkable clauses of `rules/cross-platform.md` — a
   bash 4 builtin, a GNU-only flag, a hardcoded path from one machine, text read without an
   encoding, a native command that a stop-on-error PowerShell turns into a crash. A finding here is
   a FAIL naming the file, line and clause: something in a kit path was edited into a shape that
   works on this machine and nowhere else, and it will be replaced at the next update anyway.
10. **Every pointer lands somewhere.** `python3 tools/check_kit.py` also resolves each
    reference naming a document and a section inside it, in every kit-owned file. A citation from a
    remembered heading rots on the first rewrite and then points confidently at the wrong
    paragraph, which is worse than no pointer (`rules/present-not-history.md`). A break is a FAIL
    naming both ends.
11. **Nothing personal sits in a kit path.** Spot-check the paths the manifest lists under
    `engine:` for anything the person or their agent wrote — it survives exactly until the next
    update (`doctrine/kit-ownership.md`). Any find is a FAIL naming the file and its real home.
12. **Indexes present.** `knowledge/_index.md`, `activities/_index.md`, `tools/_index.md`,
    `tools/_kit.md` and `projects/_index.md` exist and parse.
13. **MCP wrapped.** Every local MCP server (Docker / npx / native) in the agent's MCP config routes
    through `tools/mcp-wrapper.js`. An unwrapped local server is a FAIL
    (`doctrine/tool-vs-instrument.md`). Remote / SSE / URL servers are exempt.
14. **Profile ready.** `profile.md` exists and has a `Language:` value.
15. **No drift.** Anything the canon requires but the base lacks (a rule file missing, a dead
    pointer, a person's fact sitting in a kit-owned path — `doctrine/kit-ownership.md`) → WARN with
    the specific gap.

## Output

A short PASS/WARN/FAIL list in the person's language, then a one-line verdict. Never mutate.
