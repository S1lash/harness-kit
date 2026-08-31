# What this kit cannot do yet

> Kit-owned and honest. A limit that is written down is one an agent can work around and a person
> can decide about; one that is not is a surprise on somebody else's machine.

- **Nothing here knows what a secret is, and the base pushes on its own.** `rules/device-sync.md`
  has the agent saving small and often — on its own authority where nobody is there to ask — into
  a repository that is private but is still a remote. A key, a token or a connection string
  written into `knowledge/` or a project note goes out with everything else, and no gate, rule or
  tool looks for one. The private-by-default repository is the only thing standing between that
  and a public leak, and "private" is a setting somebody can change later.

  This is a deliberate gap, not an oversight: secret hygiene is being designed separately. Until
  it lands, treat the base as somewhere secrets do not go, and say so plainly to anyone setting
  one up. A `.gitignore` entry for `.env` is NOT the fix and is deliberately absent — it would
  cover the one place a secret usually is not, and buy a false sense of protection for the many
  places it might be.
- **Deploying anything is out of scope.** The base holds what a person builds, and knows nothing
  about running it: no home for infrastructure facts (a VPS, a domain, an access path), no deploy
  flow, nothing that would let a non-technical person put a project online from their phone. That
  was in the original intent for this kit and is not in it. It is blocked on the same thing as
  the item above and for the same reason — infrastructure facts ARE credentials, mostly, so the
  home for them cannot be designed before the rule about what may be written down.
- **`install.ps1` has never been executed.** What stands behind it is a line-by-line audit and
  `WindowsInstallerTests` in `tools/tests/`, which guards what a read can prove — the
  byte-order mark, the file encodings, that no native command runs outside the error-handling
  helper, that every variable it reads is one it set, and that its prompts, health checks and
  kit-remote logic match the shell installer's exactly. None of that proves it runs. One
  run on a real Windows machine is the outstanding item.
- **A change to a seed reaches nobody who already has it.** `template:` files are created when
  missing and never rewritten, which is what keeps a person's own rows safe. So the kit's half of a
  seed is frozen at their clone date. Every seed is therefore kept thin, with anything the kit needs
  to keep current living in an engine file the seed links to, and `check_kit.py --authoring` fails a
  release that edits a seed which already shipped.
- **Content inside the person's own files cannot be reshaped.** `migrations:` carries a path that
  has to move; it has no verb for rewriting what is in a file, because that is the person's writing
  and only they or their agent should touch it. A kit change that needs it is the trigger to design
  that verb, not to improvise one.
- **Global agent wiring is reported, not repaired.** An update detects a runtime whose global entry
  no longer names this base and says so; re-running the installer for that runtime is a person's
  decision, because it writes outside the folder they chose.
- **`--self-heal` repairs an updater that still loads, not one that will not parse.** It is a
  mode inside `tools/update.py`, so a corruption severe enough to break the file — a half-written
  save, a merge conflict left in place — crashes before the flag is ever read, and the person sees
  a python traceback they cannot act on. The recovery for that case needs no python and no working
  updater: `git fetch harness-kit main` then
  `git checkout harness-kit/main -- tools/update.py tools/lib .engine-manifest.yml`. An agent
  present in the session runs it; the boundary is stated here because nothing in the traceback
  says which side of it you are on.
- **Nothing can guarantee a save before an ephemeral session is reclaimed.** A `SessionEnd` hook
  now saves whatever is still unsent, which covers the endings a session announces — closed,
  cleared, signed out. A container reclaimed on inactivity, a dropped connection, a crashed tab
  announce nothing, and no hook fires there; the documented budget for `SessionEnd` starts at 1.5
  seconds. So the rule carries the weight it always did: on a surface whose copy does not survive,
  save as you go rather than at the end. The hook is the floor under that habit, not a replacement
  for it — and in a runtime with no hooks at all, it is only the habit.
- **Two capabilities exist for Claude Code and for nobody else.** The session-start catch-up and
  the daily update check are `.claude/settings.json` hooks; the six `/harness-*` procedures are
  commands only there. `rules/multi-agent.md` now tells every other runtime to run the two scripts
  itself and to read the command files as procedures — but that is an instruction an agent
  follows, not a mechanism, and nothing detects a Codex session that never did. A skill has the
  same shape: `.claude/skills/<name>/SKILL.md` is a readable procedure everywhere and an invocable
  capability in one place.
- **Cursor is wired by hand, once.** It has no scriptable global rules file, so both installers
  write a ready-to-paste snippet and print a manual step. The snippet points at `AGENTS.md`, so a
  rule added later still reaches it — but a base whose owner never pasted it is canon-free in
  Cursor, and nothing detects that. Claude Code and Codex are wired automatically.
- **The portability gate reads code, so it can be fooled by code that hides.** It is a static
  scanner, and three shapes are deliberately out of reach rather than accidentally missed: a
  construct split mid-word across a shell continuation (`map\` + newline + `file`), a command name
  assembled at runtime from a variable, and a path built by string interpolation
  (`f"/home/{user}/base"` — usually not the hardcoded case at all). Chasing any of them would cost
  more precision than it buys, and the honest limit is that a green gate means "nothing recognisable
  is wrong", not "this is portable". A person's own review is still the outer layer.
- **A shipped file the tokenizer cannot parse falls back to line-by-line reading.** A `.py` that
  will not tokenize is a bigger problem than this gate, and it degrades to the weaker analysis
  rather than silently scanning nothing — but its docstrings are then matched as code, which shows
  up as false findings and not as silence. That is the intended direction to fail in.
- **Nothing runs the gates on its own.** There is no CI: the tests, `check_kit.py` and
  `check_portability.py` run when a person or an agent runs them, and the discipline that they get
  run before a release lives in `doctrine/kit-ownership.md` and in `/harness-doctor`. Every gate
  here is therefore only as good as the habit of invoking it, and a release pushed without one is
  refused by nothing.
- **`tools/mcp-wrapper.js` has no behavioural test.** It is the one shipped executable nothing
  exercises — the suite is python, and the wrapper only matters against a real MCP server holding
  a real child process. It is read by the portability scanner and by nothing else.
