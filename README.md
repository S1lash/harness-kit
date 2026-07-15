# harness-kit

**A better base for working with your AI agent.** Clone it once and it becomes yours —
the agent runs the structure, you just talk and work. A way of working, refined over years,
made cloneable and de-anonymized: a canon of hard rules, self-learning, knowledge that
survives sessions, and a concierge stance — built in from the first minute.

**What it is, in plain language → https://share.s1lash.com/harness-kit**

- Solo, cross-agent (Claude Code / Codex / Cursor), domain-agnostic.
- Fork-and-own: no upstream, no updates to chase. From the clone on, it's yours to grow.
- The structure is for the *agent*. You never file, sort, or organize anything.

---

## Quickstart (for a person)

1. **Clone it into a folder you name** — pick a place and a name you'll recognize; you'll
   launch your AI agent from there.
   ```bash
   git clone <this-repo-url> my-base    # name it whatever you like
   ```
2. **Tell your agent: "install this."** It asks a few plain questions — where, your
   language, which agents you use, whether to use git — and wires everything up. Then you
   just work.

That's the whole onboarding. You don't need to understand the structure below — the agent
does.

---

## For the agent receiving "install this"

You have been handed this repository by a person who said **"install"** (or similar). Do the
setup for them — do not make them learn the structure. Steps:

1. **Read `AGENTS.md`** (and `CLAUDE.md` if you are Claude Code) — that is your operating
   contract. The canon in `rules/` is your standard and minimum quality bar; load it.
2. **Run the installer** for the person's platform — `./install.sh` (macOS / Linux /
   Git-Bash) or `install.ps1` (Windows) — OR perform its steps conversationally if a shell
   is unavailable. The installer:
   - asks **where** to place the base and **what to name** it (this clone is `harness/`;
     a sibling `projects/` is created beside it for their apps);
   - asks the person's **language** and records it in `profile.md` — from then on you
     **converse with them in that language**, while all base content, code, and commits
     stay in English;
   - asks **which agents** they use and wires this canon into each one's global entry point
     (Claude `~/.claude/`, Codex, Cursor) so it is hot from any folder;
   - asks about **git** (default yes; a remote is a separate opt-in) — if declined, touch
     nothing git until asked;
   - runs a **health check** (`/harness:doctor`).
3. **Confirm** in plain language what you set up. Then work normally — you now own this
   structure: route facts to their homes, keep it healthy, grow it as the person works.
   Never push the structural burden back onto them.

New session later? `CLAUDE.md` / `AGENTS.md` load the canon automatically; consult
`knowledge/_index.md` on demand and `activities/_index.md` only on narrow "we did / last
time / continue" signals — never load history by default.

---

## What's inside

| Path | What it is |
|---|---|
| `rules/` | The canon — 11 hard-rule files, loaded hot every session. Your standard. |
| `doctrine/` | On-demand authoring meta — deep-knowledge, edit-checklist, skill-creation gate, knowledge/activities discipline, tool-vs-instrument. |
| `knowledge/` | Durable understanding. Ships empty with the routing & growth discipline. |
| `activities/` | Work that survives sessions. Agent-maintained index + strict anti-bias rule. |
| `tools/` | Executable automation (scripts, CLIs, the MCP wrapper). Ships empty. |
| `plugins/frontend-crafter/` | Bundled: an anti-slop frontend-design skill, ready to use. |
| `profile.md` | The one personal file — *who you are*, grown carefully by the agent. Not a habit tracker. |
| `install.sh` · `install.ps1` | The conversational, cross-platform installer. |
| `AGENTS.md` · `CLAUDE.md` | Cross-agent and Claude entry points. |

---

## License

See `LICENSE`. Bundled `plugins/frontend-crafter/` carries its own license and attribution.
