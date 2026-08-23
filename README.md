# harness-kit

**A better base for working with your AI agent.** Clone it once and it becomes yours —
the agent runs the structure, you just talk and work. A way of working, refined over years,
made cloneable and de-anonymized: a canon of hard rules, self-learning, knowledge that
survives sessions, and a concierge stance — built in from the first minute.

**What it is, in plain language → https://share.s1lash.com/harness-kit**

- Solo, cross-agent (Claude Code / Codex / Cursor), domain-agnostic.
- One base that follows you — the same thing on your computer, in your terminal, and on your
  phone. Keeping those in step is the agent's job, not yours.
- Yours from the clone on. The kit half stays updatable — `/harness-update` replaces it and
  drops what the kit retired — and everything you and your agent write is never touched
  (`.engine-manifest.yml` draws the line).
- The structure is for the *agent*. You never file, sort, or organize anything.

---

## Quickstart (for a person)

1. **Clone it into a folder you name** — pick a place and a name you'll recognize; you'll
   launch your AI agent from there.
   ```bash
   git clone <this-repo-url> harness    # name it whatever you like
   ```
   On Windows, open a terminal first and run it from there — so the window stays open and you
   can read what it says:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install.ps1
   ```
2. **Tell your agent: "install this."** It asks a few plain questions — where, your
   language, which agents you use — sets up the one private place your base lives online, and
   wires everything up. Then you just work.

From then on it is one base: everything you build lives inside it, and the agent keeps your
computer and your phone showing the same thing — it saves as you go and asks before it does.

That's the whole onboarding. You don't need to understand the structure below — the agent
does.

---

## For the agent receiving "install this"

You have been handed this repository by a person who said **"install"** (or similar). Do the
setup for them — do not make them learn the structure. Steps:

1. **Read `AGENTS.md`** — the contract every runtime reads, and the one place the canon is
   listed. (Claude Code reaches it through `CLAUDE.md`, which is one import of it.) The canon in
   `rules/` is your standard and minimum quality bar; load it.
2. **Ask the questions yourself, or run the installer.** It reads answers from a terminal, so
   running it from your own shell means nobody is there to answer — it stops rather than taking
   defaults nobody chose. Walk its steps conversationally, or pass the person's answers on stdin
   with `HARNESS_ANSWERS_ON_STDIN=1`. It is `./install.sh` (macOS / Linux / Git-Bash) or
   `install.ps1` (Windows), and it:
   - recognises whether this is a **new base** or **their existing base arriving on another
     device** — in the second case it touches neither their content nor their history;
   - asks **where** to place the base and **what to name** it. Everything they build lives in
     `projects/` **inside** the base, so any surface that has the base has all of it;
   - asks the person's **language** and records it in `profile.md` — from then on you
     **converse with them in that language**, while all base content, code, and commits
     stay in English;
   - asks **which agents** they use and wires this canon into each one's global entry point
     (Claude `~/.claude/`, Codex, Cursor) so it is hot from any folder;
   - sets up **the one private place their base lives online** — that is what makes their
     phone and their computer show the same thing;
   - runs a **health check** (`/harness-doctor`).
3. **Create that private place if the installer could not** — it says so explicitly. Use your
   GitHub access to create a **private** repository, set it as `origin`, and send the base to it.
   This is also the first real test of that access: if you do not have it, say so plainly and say
   what it costs them, rather than leaving it half-done.
4. **Confirm** in plain language what you set up. Then work normally — you now own this
   structure: route facts to their homes, keep it healthy, grow it as the person works.
   Never push the structural burden back onto them.

New session later? `CLAUDE.md` / `AGENTS.md` load the canon automatically; consult
`knowledge/_index.md` on demand and `activities/_index.md` only on narrow "we did / last
time / continue" signals — never load history by default. Every session opens by bringing the
base up to date and closes by offering to save it — `rules/device-sync.md` is the contract, and
you follow it whether or not the session-start hook ran.

---

## What's inside

| Path | What it is |
|---|---|
| `rules/` | The canon — 13 hard-rule files, loaded hot every session. Your standard. |
| `doctrine/` | On-demand authoring meta — deep-knowledge, edit-checklist, skill-creation gate, knowledge/activities discipline, tool-vs-instrument, kit-vs-person ownership, the contract every project carries. |
| `knowledge/` | Durable understanding. Ships empty with the routing & growth discipline. |
| `activities/` | Work that survives sessions. Agent-maintained index + strict anti-bias rule. |
| `projects/` | The things you build — **inside** the base, so they travel with it. Agent-maintained index. |
| `tools/` | Executable automation — what keeps your devices in step, what updates the kit half, and the tests that prove both still work. |
| `.claude/` | The session wiring: the catch-up hook and the kit's commands. |
| `plugins/frontend-crafter/` | Bundled: an anti-slop frontend-design skill, ready to use. |
| `profile.md` | The one personal file — *who you are*, grown carefully by the agent. Not a habit tracker. |
| `install.sh` · `install.ps1` | The conversational, cross-platform installer. |
| `AGENTS.md` | The contract every runtime reads — the canon list lives here and nowhere else. |
| `CLAUDE.md` | One import of `AGENTS.md` plus Claude-only notes. |
| `.engine-manifest.yml` | Which paths are the kit's and which are yours, what an update replaces, seeds, moves and drops. The one place that answers it. |
| `VERSION` | The kit version this base is on. |
| `DECISIONS.md` | Why the kit is built the way it is — what was chosen, what else was considered. |
| `KNOWN-LIMITS.md` | What the kit cannot do yet, stated plainly. |
| `CHANGELOG.md` | What changed between versions, read aloud to you by `/harness-update`. |

---

## License

See `LICENSE`. Bundled `plugins/frontend-crafter/` carries its own license and attribution.
