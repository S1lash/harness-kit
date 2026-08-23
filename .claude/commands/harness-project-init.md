---
description: Give a project the home an agent needs to open it cold — AGENTS.md contract, the CLAUDE.md bridge, and its own knowledge and decisions. Run it when a project is born, and on any project that still lacks one. The person never asks for this; you do it because they will never notice it missing.
---

# /harness-project-init

Write (or repair) a project's own contract. Shape, sections, and the write-only-what-the-code-
cannot-tell-you filter: `doctrine/project-home.md`. When to do it unasked:
`rules/harness-stewardship.md`.

## Steps

1. **Find the project.** Named in the request, or the one being worked on. Not in
   `projects/_index.md` → add its row in this same pass; the index is how any later session knows
   the project exists at all.
2. **Get oriented, and keep what it cost you.** Read enough to answer the five sections — entry
   points, how it runs, what it talks to, what looks fragile. Every question you had to answer by
   reading is a line worth writing; you are paying that price once so nobody pays it again.
3. **Ask only what reading cannot answer.** The "why does this exist / who is it for / what would
   be lost" question is usually one of them, and it is the section that matters most. Ask it in
   one plain sentence, in their language — never "shall I create documentation?".
4. **Write the files:**
   - `AGENTS.md` — the five sections, under 200 lines, present tense.
   - `CLAUDE.md` — `@AGENTS.md`, plus anything genuinely Claude-specific underneath.
   - `<project>/.claude/knowledge/_index.md` — the map, empty is fine; it grows as facts appear.
   - `<project>/.claude/decisions.md` — every choice already made that you had to reconstruct. Reconstructing
     it a second time is the cost this file removes.
5. **Apply the filter before saving.** Walk each line: *"if this code changes next quarter, does
   this become a lie?"* Yes → replace it with the pointer and the reason. A directory listing, a
   dependency list, an architecture paragraph restated from the source: cut them. The code owns
   those.
6. **Save** (`rules/device-sync.md`) — in the base, propose it in one line; in a project that has
   its own repository, the repository's own rules apply (`rules/git-safety.md`).

## Repairing rather than creating

A project that already has a contract → **read it against the code first**. Wrong lines are the
work; missing sections come second. Never rewrite a section that is still true just to make the
file look uniform.

## Not this command

- A durable fact that is about the person or spans projects → the base, by
  `rules/sot-dry-srp.md`. This command is only the project's own half.
- A repeatable procedure the project needs → a skill (`/harness-add-skill`), not another section
  in the contract.
