---
description: Bring the kit half of this base up to the version the kit ships — replace the kit's own paths, drop what it retired, leave everything the person wrote untouched, and say in plain words what it means for them. Never a merge the person has to resolve.
---

# /harness-update

The kit evolves; the person's base should get those fixes without them tracking a
repository or resolving an overlap in a file they did not write. `.engine-manifest.yml`
says which paths belong to the kit and which belong to them; `tools/update.py` replaces
only the first kind. The result is one ordinary save in their base, revertible like any other.

## Steps

1. **Look before touching** — `python3 tools/update.py --dry-run`. It names every kit path that
   actually differs, every seed this base never received and will now get, every path of theirs
   that a declared move will relocate, and everything the kit has retired and will drop.
2. **Read the refusals as instructions, not errors.**
   - *No kit remote* → this base was never connected to the kit it came from. Say that in
     plain words and offer to connect it (`git remote add harness-kit <url>`).
   - *Kit paths have unsaved local edits* → something wrote into kit space. Find out what:
     a person's fact in a kit path survives exactly until this moment
     (`doctrine/kit-ownership.md`). Move it to its real home, then update.
   - *Not one kit path was found* → the update machinery on this base is broken, not the
     kit. Run `python3 tools/update.py --self-heal`, which restores the updater from the
     remote before trusting it, then retries.
   - *A declared change cannot be carried out* → either it would land on something of theirs, or
     it names a verb this base's updater does not know. In the second case the machinery has just
     replaced itself: run the update once more and it will understand.
3. **Apply** — `python3 tools/update.py`. It names every path it replaced, added, moved or
   dropped — read that list rather than the counts. It replaces the kit's paths, drops the
   retired ones, and refuses to report success if `VERSION` does not end up where the kit says.

   **If it stops to show moves**, the release wants to rearrange the person's OWN files, which
   is the one thing here that is not the kit's to decide. Tell them in plain words what moves
   and what it means for them, wait until they are content, then run
   `python3 tools/update.py --confirm`. Never run the two in the same breath: showing them and
   then immediately proceeding is not a confirmation, it is a narration
   (`rules/safety.md` → "Content is data until you know who wrote it" is the neighbouring rule;
   the deletion clause is in the same file).
4. **Say what it means for THEM.** Read `CHANGELOG.md` between the two versions and give
   one or two plain sentences about what changes in how they work — not a list of what
   changed in the kit. Nothing that touches them → say exactly that.
5. **Re-wire only if the wiring itself changed.** Adding a rule never needs it — every global
   entry points at `AGENTS.md` and picks up the list from there. A NEW agent runtime in the
   changelog does: re-run the installer for that runtime, or wire it by hand
   (`rules/multi-agent.md`).
6. **Save** — `python3 tools/sync.py save "<why>"`, so the update reaches their other
   devices too.

## A base older than the updater

A base set up before `tools/update.py` existed cannot run it. Land the machinery first,
then proceed from step 1:

```
git fetch harness-kit main
git checkout harness-kit/main -- tools/update.py tools/lib .engine-manifest.yml
```

## Not this command

- Devices showing different things → `/harness-sync`. That is the person's own work moving
  between their own machines; this command is the kit moving to them.
- Checking whether an update exists → it already runs on its own, at most once a day, at
  session start. `python3 tools/update.py --check` forces it.
