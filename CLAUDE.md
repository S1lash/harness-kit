# CLAUDE.md — Claude Code entry

@AGENTS.md

## Claude Code specifics

- **Commands** live in `.claude/commands/` — `/harness-sync`, `/harness-update`, `/harness-doctor`,
  `/harness-init`, `/harness-add-skill`, `/harness-project-init`. That directory belongs to the kit
  and an update replaces it: anything you author for this person goes to `.claude/skills/`, which
  is theirs and is never touched. The same split holds for settings: `.claude/settings.json` is
  the kit's, `.claude/settings.local.json` is this machine's and is never carried anywhere.
- **`.claude/settings.json`** catches the base up at session start and checks once a day whether the
  kit has a newer version. If neither ran — another runtime, a machine without python — do both
  yourself: `rules/device-sync.md` is the contract, the hook is only a convenience.
