# Anti-Slop Reference

The quantified signatures of current AI-default design, and the mechanisms for staying off the
regress-to-mean path. `bans.json` is the machine-checkable subset (fonts, hex values, patterns);
this file is the taste-layer reasoning behind it, plus what's mechanically un-checkable.

## 1. The three named AI-default clusters

As of this writing, generative frontend output collapses toward one of three recognizable clusters
when no strong direction is imposed. Naming them is the first defense — a direction that happens
to land in one of these by default (not by deliberate choice) is a tell, not a decision:

1. **Warm cream + high-contrast serif + terracotta.** Background in the quantified cream range
   (`color.md` §4: `L 0.84–0.97, C < 0.06`), paired with a high-contrast display serif and a
   terracotta/burnt-orange accent. Originally an "editorial warmth" choice, now saturated to the
   point of being the *first* thing a viewer associates with AI-generated design.
2. **Near-black + single acid accent.** A near-black background (`L` under ~0.15) with one
   saturated accent — acid green or vermilion red — used sparingly. Reads as "modern dark SaaS" by
   default, but the specific near-black-plus-one-acid-accent combination is now itself a template,
   not a bold choice.
3. **Broadsheet hairline-rules + zero radius + dense columns.** An editorial/print-inspired layout
   with 1px hairline dividers, zero border-radius everywhere, and dense multi-column text blocks.
   Legitimate for a genuinely editorial brief, but defaulting to it because it "looks intentional"
   is the same failure mode as the other two clusters — a safe-looking choice standing in for an
   actual decision.

None of these three are permanently banned — a brief can genuinely call for any of them. The
failure is landing in one **by default**, without having actively considered and rejected the
other options. `directions/_catalog.md`'s auto-selection rubric explicitly excludes these as the
*default* pick and requires deliberate justification to choose one anyway.

## 2. The reflex-reject font list — context

`bans.json`'s font list is the enforced version; the reasoning behind each entry:

- **Inter/Roboto/Arial/system-font stacks** — the literal defaults of most design tools and
  frameworks; using them signals "didn't make a typography decision" rather than "made this
  decision."
- **The reflex-reject display-serif cluster** (Fraunces, Newsreader, Lora, Crimson, Playfair,
  Cormorant, Instrument Serif) — each individually distinctive when the trend started, now so
  common in AI-generated editorial-style output that the *category itself* (display serif + italic
  accents + mono labels + ruled separators) is a saturated lane, not just individual fonts within
  it. **This is the important second-order point:** even a font not literally on the ban list, if
  it's deployed in that same editorial-typographic formula (serif headline + italic pull-quote +
  monospace eyebrow + horizontal rule dividers), reads as the cluster regardless of which specific
  serif was used. The formula is the tell, not only the font name.
- **Space Grotesk/Space Mono, IBM Plex family** — the "modern technical" reflex pick, equally
  saturated from the opposite direction (geometric/technical instead of editorial).
- **DM Sans/Serif, Outfit, Plus Jakarta, Instrument** — the current "safe distinctive-looking sans"
  defaults; picked because they read as *more* considered than Inter while requiring zero actual
  research, which makes them exactly as templated in practice.

The durable lesson, not the perishable list: **the specific fonts will rotate as new "safe
distinctive" defaults emerge** (this has already happened once — yesterday's bold choice becomes
today's tell). `type.md` §7's selection *method* (prefer lesser-known within-category, log the
pick, bias against repetition) is what stays durable when the specific names age out; the list in
`bans.json` needs periodic revision, this reasoning doesn't.

## 3. "Name your lane" + the inverse test

Before committing to a direction, state it as a specific, describable lane — "brutalist tactical
telemetry", "soft editorial luxury", "minimalist document-style" — not a vague adjective ("clean",
"modern", "premium"). A direction vague enough to not have a name is a direction that hasn't
actually been chosen yet.

**Inverse test:** once a direction is named, describe the resulting design as a *competitor* or
outside observer would describe it, not as its own creator. If that outside description matches
"the modal/median landing page in this category right now" — restart. The test catches the failure
mode where a direction was consciously *named* but still executed toward the safe average within
that name (e.g., naming "brutalist" but then softening every genuinely brutalist choice until it's
indistinguishable from a slightly-bold SaaS page).

## 4. Eliminate AI statistical fingerprints — the durable principle

The true, durable heuristic is broader than any single banned mark: **eliminate the recognizable
statistical fingerprints of AI-generated text and design**, of which the em-dash is one instance,
not the whole rule. Treating em-dash-ban as an inviolable global law (rather than one symptom of
the broader fingerprint) misfires on legitimate editorial use where an em-dash is simply correct
punctuation. Apply judgment at the level of the actual principle — does this reads as a
statistical tell, in aggregate with everything else on the page — rather than a single mechanical
find-and-replace rule. `copy.md`'s editorial pass (`reference/pipeline.md` §verify, static-critique
subagent 4) makes this judgment on rendered/authored copy; short UI strings are still checked
mechanically by `lint.mjs` per `bans.json`, where a hard regex is cheap and low-risk of false
positive.

## 5. Absolute global bans (mechanical, `bans.json`-adjacent)

These read as templated regardless of direction — no brief justifies them by default:

- Side-stripe accent borders (a colored `border-left`/`border-right` on cards as the primary visual
  treatment) — the single most recognizable "AI card" tell.
- Gradient text (`background-clip: text` with a gradient fill) — was a genuine effect once, now a
  reflex applied regardless of whether the content or brand calls for it.
- Glassmorphism as a default treatment (translucent blur panels used because they look "modern",
  not because the layered-depth effect serves a real purpose).
- The hero-metric template (three stat tiles under a hero — "10,000+ users / 99.9% uptime / 24/7
  support" — near-universally fabricated data per `bans.json`'s `fabricatedData` rule, and
  templated even on the rare occasion the numbers are real).
- Identical repeated card grids with no visual differentiation between cards that represent
  different-importance content.
- Tiny uppercase "eyebrow" labels above every single heading, applied mechanically rather than
  where they earn their place (see the eyebrow-restraint discipline: an eyebrow on every third
  section at most, not every section).
- Numbered section markers (`01 / 02 / 03`) used as decoration rather than genuine sequence
  navigation.
- Text overflow at any breakpoint — a mechanical bug, not a taste call, but common enough in
  AI-generated output that it functions as a tell of insufficient testing.

## 6. Anti-invented-defect rule

When asked to "show iteration" or "explain what changed", don't invent a defect in an earlier
version to manufacture a narrative of improvement. If the prior version wasn't actually wrong,
say so — describe the real refinement (a genuine polish or a genuine direction change), not a
fabricated "this was broken, now it's fixed" story. Honesty about what actually changed is worth
more than a tidy before/after narrative.

## 7. Backgrounds & atmosphere — depth technique matched to direction

No flat single-color background by default — but the *technique* used to create depth must match
the committed direction, not be layered on indiscriminately:

- **Maximalist/brand-register directions** can carry elaborate atmospheric effects — gradient
  meshes, layered transparencies, dramatic shadows, grain overlays, decorative borders, custom
  cursors where genuinely appropriate to the brand's personality.
- **Minimal/restrained directions** get one precise textural detail rather than several competing
  ones — a single subtle grain, a single soft gradient wash — the discipline is *fewer, more
  deliberate* atmospheric choices, not zero.
- The failure mode in both directions is the same shape: applying an atmospheric technique because
  it's available/impressive rather than because the specific direction calls for it. A brutalist
  direction with a soft gradient mesh background is fighting itself regardless of how well-executed
  the gradient is — technique must serve the committed direction (§3), not exist independently of
  it.
