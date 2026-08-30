# CLAUDE.md — Claude Code entry

@AGENTS.md

## Claude Code specifics

- **Commands** live in `.claude/commands/` — `/harness-sync`, `/harness-update`, `/harness-doctor`,
  `/harness-init`, `/harness-add-skill`, `/harness-project-init`. That directory belongs to the kit
  and an update replaces it: anything you author for this person goes to `.claude/skills/`, which
  is theirs and is never touched. The same split holds for settings: `.claude/settings.json` is
  the kit's, `.claude/settings.local.json` is this machine's and is never carried anywhere.
- **`.claude/settings.json`** catches the base up at session start and checks once a day whether the
  kit has a newer version. **You can tell whether it ran: its output is in this session's context.**
  Nothing from `sync.py` there means it did not run — another runtime, or a machine where the name
  `python3` resolves to nothing (common on Windows, where a python.org install registers `python`
  and `py` but no `python3`). Then do both yourself, first thing: `rules/device-sync.md` is the
  contract and the hook is only a convenience. A hook that silently does not fire looks exactly
  like a base that was already up to date.
