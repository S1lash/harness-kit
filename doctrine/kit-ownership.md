# What the kit owns, what the person owns

> A base is one repository holding two things at once: the kit (the shared standard, identical in
> every fork) and the person's own life. **Which path is which is declared in
> `.engine-manifest.yml` at the base root — that file is the source of truth and this one is not.**
> Read this before replacing anything wholesale, before putting a person's fact anywhere near a kit
> path, and before adding a path to either half.

## The four categories, and what each one means for you

The manifest's own header defines them precisely. What they oblige you to do:

- **engine** — the kit. An update replaces these wholesale. **Never write a person's fact here**;
  it survives exactly until the next update, and nothing will announce that it is gone.
- **template** — seeds. They ship under their live names and an update never touches them again.
  A file carrying both a spec the kit maintains and rows the person accumulates belongs here.
  Adding one to `engine:` instead is how a person loses their own index.
- **exclude** — the person's space, listed for readability. **The default for a path named nowhere
  is already "the person's"** — a path is the kit's only by being listed.
- **retired** — what the kit dropped. Every update deletes these from every base. Adding a path
  here is how a removal actually reaches the people running it.

## The rules that follow

- **An update is a replacement, not a merge.** Nobody is ever asked to resolve an overlap in a
  file they did not write. That property is the whole reason the split exists, and it holds only
  while the two halves stay disjoint.
- **Never put a person's fact in a kit path.** Route it by `rules/sot-dry-srp.md`. The one personal
  file inside the kit half is `profile.md`, and it is a `template:` precisely so an update cannot
  reach it.
- **Never put kit content in a person path.** A copy of a rule under `knowledge/` is a second
  source of truth that no update will ever correct.
- **Remove a kit path → list it under `retired:` in the same change.** A removal that is not
  retired never propagates: the updater copies what the kit HAS and cannot express what it no
  longer has, so the file sits on every base forever, offering a contract nothing honours.
  Retiring something the PERSON produced is not a sweep's decision — the updater refuses it
  outright, and rightly.
- **Add a kit path → list it under `engine:` in the same change.** An unlisted new file reaches
  nobody: it is not copied on update, and it is the person's by default.
- **Inside `.claude/`, the two halves sit side by side.** `.claude/commands/` and
  `.claude/settings.json` are the kit's and are replaced on update; `.claude/skills/` and
  `.claude/settings.local.json` are the person's and are never touched. Author a capability for
  this person under `.claude/skills/` — putting it in `.claude/commands/` loses it at the next
  update, silently.
- **The kit's remote is `harness-kit`, never `origin`.** `origin` is the person's private copy of
  their base. A base set up from the kit keeps both, so an update has somewhere to come from and a
  save has somewhere to go, with no way to confuse the two.
- **`version:` in the manifest is the kit's version**, mirrored into `VERSION` and
  `.claude-plugin/plugin.json`. All three move in the same edit, or the updater's own
  post-condition fails the next update it runs.

## Shipping a release

`main` of the kit's repository IS the release channel: every base points its `harness-kit` remote
at it, and anything landing there reaches everyone on their next update. Nothing half-finished goes
to `main`.

Before shipping, run `python3 tools/check_kit.py --authoring`. It fails on every mistake that would
otherwise only surface on somebody else's machine, where nobody can see it and they cannot diagnose
it:

- a declared path that does not exist, or one owned by two sections at once;
- a file removed from inside a kit directory without a `retired:` line — git ADDS and UPDATES on
  checkout and never deletes, so without that line the file lives on every base forever;
- a retired path that still ships, which would be restored and deleted on every single update;
- a tool in `tools/` declared nowhere, which therefore reaches nobody;
- a rule missing from the one canon list, or that list restated in `CLAUDE.md`;
- kit paths changed without `VERSION` moving (nobody's daily check notices), or `VERSION` moved
  without `CHANGELOG.md` (the update has nothing to tell them).

The structural half of the same gate runs on any base and is what `/harness-doctor` calls.
