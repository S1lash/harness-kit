# Cross-platform parity — Windows + macOS + Linux (HARD RULE)

Something that works only on the machine it was written on is a silent breakage: it surfaces
later, on somebody else's setup, as "it doesn't work for me". Any project, any session.

**Two tiers, and the manifest already decides which one a path is in — there is nothing to label.**

- **Tier 1 — what the kit ships.** Every path `.engine-manifest.yml` lists under `engine:` or
  `template:` lands on machines you will never see: Windows under Git Bash or PowerShell, macOS
  with its system **bash 3.2**, Linux. Tier 1 is not a judgement call. A `template:` entry sitting
  inside a directory the manifest also lists under `exclude:` is still tier 1 — the update seeds it
  onto every base, and where the seed lands says nothing about who wrote it. The clauses carrying an
  id below are machine-enforced — `python3 tools/check_portability.py` fails a release on any.
- **Tier 2 — what the person writes for themselves.** Their own tools, their own projects: it has
  to work where they run it, and that is the whole requirement. **The moment such a thing is handed
  to anyone else** — shipped in the kit, published, sent, deployed — **it becomes tier 1 and pays
  tier 1's price.** That transition is the judgement to get right; "it will probably stay local" is
  how tier 2 code ends up in front of a stranger.

## The clauses

- **[CP-1] Paths resolve, never hardcode.** Python → `pathlib` / `os.path`; no baked-in `C:\...` or
  `/Users/...`; no assumption about `/` versus `\`. Account for case sensitivity and `~`-expansion.
- **[CP-2] Shell stays bash-3.2-safe and Git-Bash-safe.** No `mapfile` / `readarray`, no
  `declare -A`, no `${var^^}` / `${var,,}`. Portable commands only — no `sed -i` (the GNU/BSD
  argument split), no `readlink -f`, no `stat -c` / `stat -f`, no `grep -P`.
- **[CP-3] Line endings are LF**, enforced by `.gitattributes`. A CRLF `.sh` or `.py` from a
  Windows checkout breaks bash and python outright.
- **[CP-4] A mechanism with a platform twin moves in lockstep.** `install.sh` ↔ `install.ps1`, and
  the same for hooks and wiring: edit one, edit the other in the same change, or state the
  limitation. Enforced by the tests, which compare the prompts and health checks of both halves.
- **[CP-5] Text is UTF-8, declared at every read and write.** Windows defaults both to a legacy
  code page, so an undeclared read-modify-write silently corrupts every non-ASCII character it
  touches — and a script whose own literals are non-ASCII needs whatever marker its interpreter
  requires to parse itself correctly.
- **[CP-6] A native command's ordinary output is not an error.** `git` and `gh` write progress to
  stderr, and a shell configured to stop on error turns that into an abort mid-run. Route native
  calls through one helper that relaxes the setting for the call and restores it.

## The rest of parity

- **Per-agent install wiring is part of it.** Wiring touches each agent runtime's own global config
  — Claude Code, Codex, Cursor, whatever comes next — each with its own loading and path mechanics.
  Whatever install does for one, it does for the others in lockstep, or states the limitation.
  Wiring only the runtime you happen to use leaves the rest silently unconfigured.
- **Readiness check:** "will this behave the same on a Windows machine, on plain macOS bash 3.2,
  under every runtime the person wired?" No, or don't know → bring it to parity, or mark the
  limitation and propose an equivalent. "Works on my machine" is not the criterion, and neither is
  "the gate passed" — the gate checks the clauses it can, not the ones it cannot.

Why: parity failures are invisible to whoever writes them and obvious to whoever receives them.
That asymmetry is the whole reason this is a hard rule and not a preference.
