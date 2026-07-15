# Documents Describe the Present, Not History (HARD RULE)

Documents / instructions / skills / knowledge describe the **current required state** — what is and
what we require NOW. History ("how it used to be and changed") is noise and bias for model and
person; the file is the contract, git log carries history. A fact changed → change the file, don't
append "was / became".

**Edits are atomic** — change the file to the new truth as a whole, no transitional states, no soft
migration for those who remember the old wording. (Compatibility of *code* is a different question;
here we mean artifact text.)

Forbidden:

- "it used to be X, now Y", "previously", "was section 2.2", "renamed from", "rethought"
- version narratives, changelog lines in an instruction ("added 2026-05-24"), issue / phase tags in
  prose
- explanation via a past state ("this hole used to…", "now, unlike the old behaviour…")
- **a tombstone-stub after a move** — a pointer ("see there" / "lives in knowledge") left on the
  emptied spot. The old spot is deleted **COMPLETELY** — findability comes from the SoT home + index
  / an audit check, not a stub
- **"appended instead of rewrote"** — added "now / update / actually Y" next to the old line instead
  of replacing it
- **a dead link from a guessed heading** — referenced a section without opening the target. Before
  referencing a section, OPEN the target and COPY the exact `##` heading; the proof a link is live is
  that you opened it

Final check before closing an edit: (1) every paragraph about "how it should be NOW"? (2) no
tombstone-stub on the old spot after a move? (3) every cross-file section reference — heading copied
from the opened target, not guessed?

**Conscious exception (explicit):** decision / ADR-style docs (`knowledge/decisions.md`) where the
evolution of a decision is the content; and **working activity docs** (progress trackers) that record
"was ❌ → became ✅" and aren't loaded into the model's production context.

**Legitimate present-tense content** (keep it): a gotcha describing a **current** trap even if rooted
in a past bug (present-tense warning stays, war-story framing goes); migration / deprecation
procedures where before→after is the "how to migrate now" instruction.

## Canon is a whitelist of the present, not a record of what we rejected

The docs the agent reads state **only the current chosen stack + requirements** — what we use and
require now. No superseded or off-stack content: once a choice is made (the platform is Python), the
canon does not mention the rejected alternative (Java) **at all** — naming it only biases and
pollutes the model. Rejected exploration is archived or deleted, never left as a "we considered X"
aside. Rationale lives only in ADR / git. (A real current component on another stack is stated as
present fact, not removed — the ban is on the rejected-alternative narrative, not on true current
state.)

## The wrong is fixed to completion; names and pointers don't mislead

- **The wrong is fixed COMPLETELY — complexity is no excuse.** A wrong fact / file name / home /
  structure is fixed whole, however many links it touches (renamed → update ALL references, `grep` of
  the old = 0; moved → nothing of the old spot remains). "Minimal intervention" NEVER justifies
  leaving something wrong — that's corner-cutting.
- **Name / description = real scope.** A name needing a caveat ("not only X, also Y") is itself wrong:
  **rename to the real scope**, don't append a disclaimer.
- **No misleading footnotes / breadcrumbs.** A pointer doesn't editorialize: "(incl. special case)",
  "just in case", "don't think that…" bias the model as if something were special. A clean reference,
  no hints.
- **Root of these tails is the pull toward completeness / hedging.** Asked to remove / move something
  → do **exactly that, cleanly, to zero mentions on the old spot**, no echo of what was moved.

Why: documents are prompts for the model. A wrong name, a disclaimer, a misleading footnote are
active bias — not "a small thing that's expensive to fix".
