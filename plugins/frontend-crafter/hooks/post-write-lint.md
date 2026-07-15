# Optional hook — post-write lint (OFF by default)

frontend-crafter runs `lint.mjs` as an **explicit verify step** in the pipeline, so this hook is
**not required**. It is offered for people who want the mechanical gate to fire automatically on
every design-file write. It is **off by default** and, when enabled, is
**scoped** to design extensions so it never fires on `.md` / `.py` / config files.

## Enable it

Set `hook_enabled: true` in `~/.frontend-crafter/config.json`, then add this to your
`~/.claude/settings.json` (adjust the plugin path if your install differs):

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "f=\"$CLAUDE_TOOL_FILE_PATH\"; case \"$f\" in *.html|*.css|*.jsx|*.tsx|*.vue|*.svelte) node \"$CLAUDE_PLUGIN_ROOT/scripts/lint.mjs\" \"$f\" ;; esac"
          }
        ]
      }
    ]
  }
}
```

Only `.html/.css/.jsx/.tsx/.vue/.svelte` writes trigger the lint; everything else is a no-op. The
hook is a thin wrapper around the same `lint.mjs` the pipeline already runs — enabling it changes
*when* the gate fires, never *what* it checks.
