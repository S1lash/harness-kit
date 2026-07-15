# Authoring for the agent-reader — a rule is a prompt

> On-demand authoring meta. How to write text the agent reads in hot context or as part of a
> skill (rules, hot knowledge, a skill body). The reader is the **agent, not a human**: every
> line competes for attention and tokens. Apply on ANY edit of a rule / hot knowledge. Parent —
> "Rails, not frames".

## The criterion of every line: does it change the agent's ACTION?

**Keep — earns the hot tokens:**
- **Imperative** — do / never / when→then. The core of the rule.
- **Discriminator** — a question / test by which the agent decides ("durable or a particular?",
  "copying or linking?", "about the object / the process / the automation?").
- **Generalizing "why"** — the reason that transfers the rule to an **unseen** case (a principle,
  an invariant, a failure mode). Always keep it: "never X **because Y**" transfers to an X' not
  in the rule; a bare imperative is brittle. This is the rail.
- **Conditional pointer** — see below.

**Cut / move / compress:**
- **Decorative "why"** — persuasion aimed at a human ("a form of respect", "so it doesn't get
  lost"). Doesn't change the agent's decision. Home — an ADR, not the rule.
- **Meta-comment** — "works together with the bullet below". The agent reads the neighbour anyway.
- **Hedging / softening** — a repeat of an already-implied exception.
- **A duplicate between rules** — SoT applies to rules too: one canon, the rest link.
- **Crumbs** — ticket context, "just in case", editorializing.

**Both lists illustrate one question, not a closed classifier.** A line of a new kind — judge it
by the same question, not by finding it in a list.

## Load-bearing "why" vs decorative — the test before cutting

Ask: **"remove this reason — does the agent get worse at deciding an UNFAMILIAR case?"** Yes →
keep (it's muscle / a rail). No, it only motivates a human → into an ADR or out (fat). Cut the
fat, not the muscle: terse-ification that strips the generalizing "why" turns rails into brittle
frames — a regression. "Make it shorter" is not the goal; signal density is.

## Pointer — a conditional trigger, not bait

The agent should not walk the pointer reflexively just because it's mentioned. Write it as a
**loading condition**: "when \<condition\> → read \<file\>", not a bare "see also \<file\>". A
bare "see X" provokes an extra fetch (tokens + latency). A pointer = **one line**, with a
condition, without retelling the home's content.
- ✗ "Details — `foo/_index.md`."
- ✓ "Writing to an external tool's config → first read `{tool}/_index.md` (field IDs, auth)."

**Provenance — forward, not backward.** An operational / routing doc (an `_index`, knowledge, a
skill — read by the WORKING agent for the task) does NOT carry a tail `→ ADR-NNN`: that is bait
for a chase. Name the constraint **by name** (it's in hot rules), not by an ADR number.
Provenance is held forward: the decision doc links decision→file. An author-doc (an authoring
checklist, ARCHITECTURE) may carry an ADR mark — it's read by the author, not the executor.

## Address the agent behaviorally, not with feelings

The reader is the agent — it isn't proud, motivated, afraid, or a "valued member". Write every
proactivity / standards instruction as a **behavioral obligation** ("surface uncertainty before
emitting a confident answer"), never an emotional appeal ("you care about quality", "take pride in
X"). A behavior transfers to an unseen case; a feeling doesn't. (Emotional appeal aimed at a human is
the decorative-"why" cut above — one level worse when aimed at the agent, since it grounds nothing.)

**Fix the design so the rule is obvious — don't defend it everywhere.** A rule that needs a loud
justification re-stated at every touchpoint to survive is a design smell: make the constraint the
clean default, state it crisply once at its home, reference it elsewhere. Defensive over-explanation
accreting at past-error sites is scar tissue — it drowns signal and smuggles history into
present-tense docs.

## SoT split: instruction-to-the-agent vs rationale-for-the-person

- **Rule / hot knowledge** = an instruction to the agent (imperative + discriminator +
  generalizing "why" + conditional pointer).
- **ADR (`knowledge/decisions.md`)** = human rationale (why decided, what rejected). A decorative "why"
  from a rule **moves here**, it isn't deleted — people read ADRs for the "why".

## Guard: don't evict from hot what's needed in work

**The method** (how to write / edit a rule) → on-demand (this file). But a **behavioural rule
applied in ordinary work** (code, a doc, a task) — stays HOT. Don't move into an on-demand home
what changes the agent's action in a daily task: won't be loaded → won't be followed. Move only
the authoring method and the decorative rationale.

## Capturing the "why" from intent

While eliciting intent (working-method.md), the agent uncovers the person's reasoning. A durable
"why" → capture it as a **rail / model** (deep-knowledge-pattern.md): save the reasoning, not
only the result-fact. That is how a flexible harness is built rather than a brittle reference — a
rule with a "why" transfers to a new case, a bare fact breaks on it.
