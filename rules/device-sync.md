# One Base, Many Surfaces (HARD RULE)

> The base is a single git repository, and that repository is the ONLY thing carrying state between
> the person's computer, their phone, and any autonomous agent working on their behalf. Anything not
> saved into it exists on exactly one surface and is invisible everywhere else. Hot: loaded every
> session. Sibling of `rules/multi-agent.md` — same argument, other axis: that rule says the base is
> the memory across agent RUNTIMES, this one says it is the memory across SURFACES.

## The shape that makes this work

- **One repository.** The repo root IS the base. `projects/` lives inside it, so a surface that has
  the base has everything. A project deliberately moved to its own repository is a row in
  `projects/_index.md` — never a silent assumption that it is there.
- **One branch.** The base has a single long-lived branch and no others. A branch is invisible on a
  phone and unexplainable to someone who does not know the word; every extra branch is a future
  "why is my phone showing something different". Branch-per-change discipline belongs to
  repositories of code (`rules/git-safety.md`), not here.
- **Never `--force`, for any of this** (`rules/git-safety.md`). Divergence is resolved by merging
  and by reading the content — never by overwriting one side.

## Two questions decide your behaviour — not the name of the device

1. **Does this working copy survive the session?** No → everything unsaved is destroyed when the
   session ends.
2. **Is somebody in the loop right now?** No → there is nobody to ask, and nobody to burden.

|  | someone present | nobody present |
|---|---|---|
| **copy survives** | their computer, a terminal | a scheduled run on a durable machine |
| **copy is destroyed** | phone / web session | an autonomous agent on a server, a CI-style run |

The owner of a base may be a person or another agent. The rules below say "the person" and mean
**whoever owns this base**; when nobody is present, the asking step does not exist and you save on
your own.

## Sync-in — automatic, silent, never a question

At the start of every session, before the thing they asked for, bring the base up to date. Do not
ask: nobody would choose to work from a stale base, and making them decide it is exactly the
structural burden `rules/harness-stewardship.md` forbids.

- Clean copy, behind → bring it current, say nothing.
- Already current → say nothing.
- **Unsaved work from a previous session is sitting there → do NOT pull.** That one IS a real
  choice: say what is unsaved, propose saving it first, then sync.
- Both sides moved → merge and resolve by content (you understand what these files mean), then say
  in one sentence what you reconciled. Never force, never drop a side.

## Save-out — proposed once, then done silently

- **Propose in one plain sentence at the end of a meaningful chunk** — not after every file, and
  not only at the very end. Say what you are saving and what it buys them: *"I've written down what
  we decided about the deploy — save it now so it's on your phone too?"*
- **After the first yes, stop asking for the rest of the session.** The consent is to the pattern,
  not to each file. Keep saving and drop one short line ("saved"). Asking again is nagging.
- **Where the copy is destroyed, propose EARLY** — as soon as something durable exists, not at the
  end. Declined → say once, plainly, what it costs (*"then this stays only here and disappears when
  you close it"*), then respect it and do not repeat.
- **Nobody in the loop → save without asking.** There is no one to consent, and unsaved still means
  destroyed.
- The saved message itself is English, imperative, and says WHY (`rules/git-safety.md`).

## What the person never sees

They do not know these words and do not need to: commit, push, pull, branch, merge, rebase, remote,
origin, conflict. Say what happened in terms of their world:

- not "pulled 3 commits from origin/main" → "picked up what you did on your computer";
- not "your branch has diverged" → "there were changes here and on your computer — I put them
  together";
- not "nothing to commit" → say nothing at all.

Use a git word only if they used it first. Asked *"why is my phone showing something different?"*,
the answer is never a lesson about git — it is "there's work on your computer that was never saved;
save it there and it appears here", plus doing it for them when you are on that machine.

## Mechanism

`tools/sync.py` holds the mechanics (what state the base is in, and the safe action for that state);
this rule holds the judgement. On Claude Code a `SessionStart` hook runs the sync-in step for you.
A runtime without hooks, or a machine where the hook cannot run, changes nothing about the
contract — you do it yourself, in the same order.

Why: the person's whole leverage is that one base follows them everywhere. The moment one surface
holds work the others cannot see, the base stops being one thing — and nothing announces it. They
just discover, days later, that their phone is wrong and stop trusting any of it.
