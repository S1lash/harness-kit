---
description: Bring the base in step with the person's other devices — pick up what changed elsewhere, and save and send out what changed here. Reports in plain language, never in git words.
---

# /harness-sync

Put this base back in step across every surface the person uses. The contract is
`rules/device-sync.md`; the mechanics are `tools/sync.py`. This command is the manual entry
point — the same thing you do on your own at the start of a session and after a chunk of work.

## Steps

1. **Read the state** — `python3 tools/sync.py status`. It reports the branch, whether anything
   here is unsaved, how far apart the two sides are, and the one action required.
2. **Do what it says**, following `rules/device-sync.md`:
   - behind, nothing unsaved → `python3 tools/sync.py pull`, then say nothing about it;
   - unsaved work here → propose saving it in one plain sentence, then
     `python3 tools/sync.py save "<why this change exists>"`;
   - both sides moved → `pull`, resolve anything overlapping by reading what it means, then save;
   - no remote at all → tell the person their base lives on this machine only, so their phone
     cannot see any of it, and offer to fix it.
3. **Report in one line, in their words.** Never "pulled / pushed / merged / branch" — say what
   happened to *their* things: "picked up what you did on your computer", "saved — it's on your
   phone now".

## Not this command

- The person asks why two devices disagree → same steps, but answer the question first: the
  usual cause is work left unsaved on the other machine.
- Setting the base up for the first time → `/harness-init`.
