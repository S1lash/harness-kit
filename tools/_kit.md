# The tools the kit ships

> Kit-owned, so every update carries the current list. The person's own tools are catalogued
> beside this, in `_index.md`, which no update touches.
> What a tool is versus a skill or an instrument: `../doctrine/tool-vs-instrument.md`.

| Tool | What it does | Invoke |
|---|---|---|
| `sync.py` | Reports what state the base is in across the person's devices and takes the safe action for it. Never forces, never discards a side. | `python3 tools/sync.py status\|session-start\|pull\|save "<why>"` |
| `update.py` | Brings the kit half of this base up to the version the kit ships: replaces kit paths, seeds what is missing, carries declared moves, drops what the kit retired. Never touches what the person wrote. | `python3 tools/update.py [--dry-run\|--check\|--self-heal]` |
| `check_kit.py` | Proves the kit half of a base is coherent. `--authoring` adds the release gates. | `python3 tools/check_kit.py [--authoring]` |
| `tests/` | Re-runs by machine what was once verified by hand. | `python3 -m unittest discover -s tools/tests` |
| `mcp-wrapper.js` | Wraps a local MCP server so it can't leave zombie processes on exit. | `node tools/mcp-wrapper.js <command> <args…>` (in MCP config) |
