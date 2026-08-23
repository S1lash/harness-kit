# Projects — index

> The things the person builds. They live in `projects/` **inside this base**, so any surface that
> has the base has them too — their computer, their phone, an agent working on their behalf.
> The agent maintains this index; the person never curates it.
> Where a fact about a project belongs: `../rules/sot-dry-srp.md` (home boundary).

## Active

_(none yet — a row per project as they appear)_

<!-- one row per project:
| Project | What it is | Lives in |
|---|---|---|
| `<name>/` | one line | this base |
| `<name>/` | one line | its own repository — <url> |
-->

## Where a project lives

**Default: inside this base**, as `projects/<name>/`. One repository means one thing to keep in
step, and every surface gets the project for free.

**Its own repository** only when the person asks for it — they want to publish it, share it with
someone, or hand it to a team. Then this index is the record of that: the row names where it lives,
and the base keeps everything *about* the project that is not its code. A project in its own
repository is not present in every session, so nothing in the base may quietly assume it is there
(`../rules/sot-dry-srp.md`).

A project's own conventions, code traps, and implementation notes live in
`projects/<name>/.claude/` — beside the code they describe, wherever that code lives.
