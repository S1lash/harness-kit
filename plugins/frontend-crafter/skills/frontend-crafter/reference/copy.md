# Copy Reference — Writing in Design

Words are design material, not an afterthought filled in once the layout is done. Copy quality is
as load-bearing as spacing or color — a well-composed page with generic copy still reads as a
template.

## 1. Words are design material

Treat copy decisions with the same deliberation as a spacing or color decision — a headline's
exact wording, a button's exact label, an error message's exact phrasing are all design choices,
not "content that goes in later." Copy is written *during* design, in the same pass as layout, not
handed off to a separate content step after the visual system is locked.

## 2. Product language, not design commentary

Every user-facing string describes what the product does or what the user can do — never how the
interface itself is built or organized. "Selected KPIs", "Plan status", "Search metrics" describe
the thing; "Widget Panel", "Content Block 3", "Info Card" describe the implementation. The test:
would a user who has never seen the codebase understand the label purely from using the product?
If a label only makes sense to whoever built the page, it's design commentary leaking into the UI.

## 3. Active voice

Write instructions and descriptions in active voice — the user or the system does something,
rather than something being done. "Save your changes" not "Your changes can be saved"; "We
couldn't process your payment" not "Payment processing was unsuccessful." Passive voice adds
distance and hedging exactly where clarity matters most (errors, calls to action).

## 4. Name by what users control, not how the system is built

Label controls and sections by the outcome or object the user is manipulating, not by internal
naming. "Notifications" not "Preference Flags"; "Team members" not "User Records"; "Billing" not
"Subscription Object". This is the copy-level instance of the same principle as §2 — the interface
vocabulary should match the user's mental model of the product, not the engineering model
underneath it.

## 5. The 3-part error formula

Every error message states, in order:

1. **What went wrong** — specific, not generic ("Card declined" not "Something went wrong").
2. **Why, if knowable** — the actual cause when it can be surfaced safely ("Your card expired last
   month").
3. **How to fix it** — the concrete next action ("Update your payment method" with a direct link
   to do so, not just "please try again").

A message with only part 1 ("Something went wrong") leaves the user with no path forward. A
message with all three turns a failure into a solvable moment.

## 6. Errors don't apologize

Skip "Oops!", "Sorry about that!", "We're bummed too" — these add words without adding
information and read as filler wrapped around the one thing the user actually needs (what to do
next). State the problem and the fix plainly. This isn't about being cold; a calm, clear, specific
error is more reassuring than a chirpy one that doesn't explain anything.

## 7. Empty screens are an invitation, not a dead end

An empty state is the first thing a new user or a freshly-cleared view shows — treat it as an
onboarding moment, not a failure state to apologize for. Structure: one sentence explaining what
this space *will* hold once populated + one clear action to populate it. "No projects yet — create
your first one to get started" with a visible create button, not a flat "No data" label sitting
alone in the middle of an empty container. See `interaction-states.md` §5 for the full state-
catalog requirement this belongs to.

## 8. One term, forever

Once a concept has a name in the product, use that exact name everywhere — never alternate
between synonyms for the same thing across screens ("Workspace" on one page, "Project" on another,
referring to the same object). Synonym-drift is invisible to whoever wrote each individual screen
in isolation and confusing to a user encountering the product as a whole. When introducing a new
term, check whether an existing term for the same concept already exists elsewhere in the product
before coining a second one.

## 9. Editing discipline

If cutting a portion of the copy on a section makes it stronger, keep cutting — most first-draft
copy is over-written relative to what the layout and hierarchy already communicate visually.
Headlines carry the primary meaning; supporting copy is one short sentence, not a paragraph
restating the headline in different words. Cut repetition between sections — if two sections are
making variations of the same point, one of them is unnecessary.

## 10. What NOT to write (cross-reference `bans.json` + `anti-slop.md`)

- Fabricated data of any kind — no invented metrics, uptime numbers, user counts, testimonials, or
  logos the user didn't supply. Real data or an explicit `[placeholder]`, flagged.
- Banned copy tics (`bans.json`) — "Elevate", "Seamless", "Unleash", "Next-Gen", "Empower",
  "Revolutionize", "Supercharge", "Game-Changer" and equivalents — these are AI-default filler that
  say nothing specific about the actual product.
- `LABEL // YEAR` heading conventions ("SYSTEM // 2024") — a stylistic tic, not real typography or
  real information.
- Banned UX filler phrases — "Scroll to explore", "Swipe down" paired with a bouncing chevron.
  Good content and clear affordances pull users forward without instructional captions telling them
  to scroll.
