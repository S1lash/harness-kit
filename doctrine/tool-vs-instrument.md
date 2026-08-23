# Tools, Instruments & the MCP layer

> On-demand authoring meta. The extension layer skills stand on. Three nouns, kept apart by
> home-by-object (rules/sot-dry-srp.md). Shipped empty — this is the mechanism, not content;
> the person's actual tools and integrations accrue here over time, routed by the agent.

## Three nouns — skill / tool / instrument (and process)

- **Skill** — a *described procedure* the agent follows (trigger → workflow → gates). It
  reasons. Home: `doctrine/skill-creation.md` for how to build one.
- **Tool** — *executable code the agent invokes*: a script, a CLI, an MCP server, a wrapper.
  It does one mechanical thing deterministically; it has no judgement. Home: `tools/`.
- **Instrument** — an *external system* the harness integrates with (an editor, an API, a
  service) — specifically **how it behaves** (its quirks, contracts, gotchas). Home:
  `knowledge/instruments/{name}.md` (it's a knowledge theme by home-by-object).
- **Process** — *how you use* a tool/instrument in your own flow. Home: the relevant
  knowledge/skill, **by link** to the tool/instrument — never inlining its mechanics.

Rule of thumb: **if it reasons → skill; if it runs → tool; if it's an outside system →
instrument.** A skill *invokes* tools and *consults* instrument-knowledge; a tool never
invokes a skill.

## Skills decompose into tools + instruments — by default

A skill does **not** inline mechanical logic or an external system's wire-details. It
**leans on** the layer below: it calls a `tools/` script for the mechanical work and
consults `knowledge/instruments/{x}.md` for how the external system behaves.

```
skill  ──invokes──▶  tools/{name}          (the deterministic doing)
   │   ──consults──▶ knowledge/instruments/ (how the outside system behaves)
   └── reuse before invent: lean on the layer below, don't re-implement it
```

So `doctrine/skill-creation.md`'s gate carries a decomposition step: **before inlining, ask
"can this stand on an existing (or a new) tool / instrument instead?"** Decomposition is the
default, monolithic skills the exception. This keeps each mechanical fact in one home and
skills thin.

## Tools live in `tools/`, catalogued in `tools/_index.md`

- Scripts are **cross-platform** (rules/cross-platform.md): Python-first or Node, `pathlib`
  / portable paths, no hardcoded home paths, parity across OSes.
- Every tool gets a row in `tools/_index.md` so the agent knows what exists and how to
  invoke it — the person never hunts for a tool, the agent orients from the catalog.

## The MCP layer — wrap every local server

Every local MCP server (Docker, npx, native binary) is wrapped by `tools/mcp-wrapper.js` to
prevent zombie processes/containers when the session exits. This is **not optional** — an
unwrapped local MCP server is a defect `/harness-doctor` flags.

- Wrap it in the agent's MCP config by routing the command through the wrapper:
  ```
  Before:  "command": "docker",  "args": ["run", "-i", "--rm", ...]
  After:   "command": "node",    "args": ["<harness>/tools/mcp-wrapper.js", "docker", "run", "-i", "--rm", ...]
  ```
- **Remote / SSE / URL servers have no local child process — not wrapped.**
- The wrapper is vendored in this harness's own `tools/` — it never reaches into another
  harness to find one (a harness is self-contained; a sibling's path can move or be absent).
- `MCP_WRAPPER_DEBUG=1` in a server's `env` logs wrapper lifecycle for debugging.
