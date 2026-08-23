---
description: Set up a base for the person. Runs the installer (or its steps by hand) — where + name, their language, which agents, and the private place their base lives so it reaches their phone — then creates that place with your GitHub access if the installer could not, and runs the health check. For a person who handed you this repo and said "install".
---

# /harness-init

The person cloned this and wants it set up. Do it for them — never make them learn the structure.
This is the runnable form of the installer plus the one step only you can do.

## Steps

1. **Load your contract** — read `AGENTS.md` (and `CLAUDE.md` if you are Claude Code). The canon in
   `rules/` is your standard; it must be hot.
2. **Run the installer** — `./install.sh` (macOS / Linux / Git-Bash) or `install.ps1` (Windows). No
   shell available → perform its steps conversationally. It:
   - recognises whether this is a **new base** or **their existing base arriving on another
     device**, and in the second case touches neither their content nor their history;
   - asks **where** to place the base and **what to name** it; everything they build lives in
     `projects/` **inside** it, so any surface that has the base has all of it;
   - asks their **language** → writes it to `profile.md`. From then on you converse in that
     language; base content, code, and commits stay English;
   - asks **which agents** they use → wires the canon into each one's global entry point so it is
     hot from any folder;
   - sets up **the private place their base lives online**, which is what makes their phone and
     their computer show the same thing;
   - runs the health check.
3. **Create that private place if the installer could not.** It will say so explicitly. Use your
   GitHub access to create a **private** repository, set it as `origin`, and send the base to it.
   Treat this as the first real test of that access: if you do not have it, say so plainly in their
   language, say what it costs them (their phone will not see anything they do here), and offer the
   alternative rather than leaving it half-done.
4. **Confirm what you set up**, in their language, in plain words. Then work normally — you own this
   structure now, and keeping their devices in step is your job (`rules/device-sync.md`).

## Not this command

- Adding a capability → `/harness-add-skill`.
- Checking health later → `/harness-doctor`.
- Devices showing different things → `/harness-sync`.
