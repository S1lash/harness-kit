# Cross-platform parity — Windows + macOS + Linux (HARD RULE)

Any harness change — a skill, script, tool, hook, path, symlink, command in a doc — must work on every
platform a fork runs on: Windows, macOS, Linux. An artifact that works only on the author's machine is
a silent breakage surfacing only when someone else finds "it doesn't work for me". Any project, any
session.

- **Paths — cross-platform.** Python → `pathlib` / `os.path`, no hardcoded `/` or `\`, no baked-in
  `C:\...` / `/Users/...` (resolve from config). Account for case sensitivity and `~`-expansion.
- **Runtime — available to all.** Default for scripts is Python 3; Node is fine; pure bash only where
  a shell is guaranteed. Keep shell bash-3.2-safe AND Git-Bash-safe (no `mapfile` / `readarray`, no
  `declare -A`, no `${var^^}` / `${var,,}`; portable commands only — no `sed -i ''` vs `sed -i` split,
  no `readlink -f`, no `stat -f|-c`, no `grep -P`).
- **Line endings — LF, enforced by `.gitattributes`.** A CRLF `.sh` / `.py` from a Windows checkout
  breaks bash and python.
- **Parity of mechanisms in lockstep.** A shell mechanism with a platform equivalent (`install.sh` ↔
  `install.ps1`) — edit one, edit the other in the same change; same for hooks and symlinks.
- **Per-agent install wiring is part of parity.** Install / wiring touches per-agent global config for
  each agent runtime the person uses — Claude Code (`~/.claude/`), Codex, Cursor, others — each with
  its own rules-loading / path / symlink mechanics. Whatever install does for one runtime, it does for
  the others in lockstep, or states the limitation. Don't wire only your own agent and leave the rest
  silently unconfigured.
- **Readiness check:** "will this work on someone else's Windows machine the same, on plain macOS bash
  3.2, under every agent runtime the person wired?" No / don't know → bring to parity or mark the
  limitation and propose an equivalent. "Works on my Mac" is NOT the criterion.

Why: an artifact for one platform (or one agent runtime) is a silent hole surfacing only for a user on
another setup. Parity is a hard gate, not a wish.
