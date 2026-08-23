# What this kit cannot do yet

> Kit-owned and honest. A limit that is written down is one an agent can work around and a person
> can decide about; one that is not is a surprise on somebody else's machine.

- **`install.ps1` has never been executed.** It was audited line by line and every fault found was
  fixed, and seven tests in `tools/tests/` guard what a read can prove — the byte-order mark, the
  file encodings, that no native command runs outside the error-handling helper, and that its
  prompts and health checks match the shell installer's exactly. None of that proves it runs. One
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
