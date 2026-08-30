# What this kit cannot do yet

> Kit-owned and honest. A limit that is written down is one an agent can work around and a person
> can decide about; one that is not is a surprise on somebody else's machine.

- **`install.ps1` has never been executed.** It was audited line by line and every fault found was
  fixed, and `WindowsInstallerTests` in `tools/tests/` guards what a read can prove — the
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
