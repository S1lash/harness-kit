# More than one base on one machine

> Read when a second base appears — a base for work beside a base for life, a product's own base
> beside the person's, an agent's base beside the one it serves. The kit assumes ONE base
> everywhere else, and that assumption is correct until the day it silently is not.
>
> The rule this serves is `rules/sot-dry-srp.md` → "Home boundary — the base vs a project"; this
> file is the same boundary one level up, between two bases rather than between a base and a
> project.

## The failure this prevents

Every agent runtime has exactly one global entry point. Two bases on one machine therefore share
it, and the moment they do, the tempting move is to copy: *"just the branch convention"*, *"just
the one rule about deploys"*, *"only two lines"*. Each copy is a second home for a fact the other
base owns, and it will diverge — quietly, because nothing compares them and neither base knows the
other exists.

The damage is not the duplication. It is that the person then gets a **confidently wrong answer**
from the base that holds the stale copy, with no way to tell which of the two was right.

## Route, never absorb

**A base never holds a fact another base owns. It holds a POINTER to where that fact lives, and
the instruction to go there.**

- **Route on the signal, not on the folder you happen to be in.** The question decides which base
  answers it, not the working directory. A question about work, asked from the personal base,
  is answered by opening the work base — not from memory and not from a copy.
- **Never answer from recall across a boundary.** "I remember how that repo does it" is the
  failure mode: what you remember is the last time you read it, and a pointer exists precisely
  because that is not good enough.
- **Copying one line is the whole failure, not a small version of it.** There is no size at which
  a copy is safe: the smallest one is the one nobody thinks to check.
- **Each base keeps its own canon.** Two bases sharing a machine do not merge their rules. They
  are separate standards that happen to be neighbours, and a rule of one binds the other only if
  it is written there too, on purpose.

## The shape of a pointer

Thin, global, and content-free. A pointer that starts explaining is a copy that has not finished
becoming one yet.

```markdown
# <Name> — where it lives (thin global pointer)

> Signpost only — no canon, no details here. Details load when you enter that base;
> it carries its own contract and canon. This file exists so any session, from
> anywhere, knows <Name> exists and where to go.

- **`<path to the base>`** — what it is, in one line. What kinds of question it
  answers. Enter it for those; its own entry file orients you.

Rule of thumb: <the one-line signal that decides between this base and here>.
Don't answer <Name> questions from memory — open the base.
```

Where it goes: `rules/`, as an ordinary hot rule, because the routing decision has to be made
before you know you needed it. Keep it to a screen. If a pointer grows past that, what grew is
almost certainly a fact that belongs in the base it points at.

## What the kit does not solve yet

The manifest draws ownership **by path**, and that is enough for one kit and one person. It cannot
express two products sharing one base, ownership by source rather than by location, or a kit whose
own descendant is itself a kit for somebody else. Those need a different line, not a longer list
of paths — a change to `ARCHITECTURE.md`'s Layer 2, not a configuration of it.

Until then, a second base is a second repository with its own manifest, and the two are connected
by pointers and by nothing else. That is a limitation, and it is also the honest version: two
bases that route to each other stay correct, while two bases that share files silently stop being
two things anyone can reason about.
