# Tools — catalog

> Executable automation the agent invokes (scripts, CLIs, MCP wrappers). The agent maintains
> this catalog; the person never hunts for a tool. What a tool is vs a skill vs an instrument,
> and the decompose-by-default rule: `../doctrine/tool-vs-instrument.md`.
> All tools are cross-platform (`../rules/cross-platform.md`).

## Catalog

| Tool | What it does | Invoke |
|---|---|---|
| `mcp-wrapper.js` | Wraps a local MCP server so it can't leave zombie processes on exit. | `node tools/mcp-wrapper.js <command> <args…>` (in MCP config) |
| `sync.py` | Reports what state the base is in across the person's devices and takes the safe action for it. Never forces, never discards a side. | `python3 tools/sync.py status\|session-start\|pull\|save "<why>"` |

_(grows as the person adds scripts / CLIs. Each new tool → a row here. Skills lean on these
rather than inlining mechanical logic — see the decompose-by-default rule.)_
