# Multi-Variation Work

*Producing 3 (max 5-6) design variations that are substantively different, in one file, with a recommendation.*

Triggered when the user asks for «options», «alternatives», «different takes», «show me a few».

## Defaults
- **3 variations** unless specified. Ceiling 5-6 — beyond that the user can't hold them in mind.
- Confirm what's being varied (single screen / component / whole flow) and **which axis** matters most (visuals / layout / interaction / tone).

## Ladder: basic → refined → bold
- **V1 — by the book.** Matches existing patterns. The «safe» option that proves you took the brief seriously.
- **V2 — refined.** Same structure as V1, 1-2 axes pushed (bolder type, more confident layout, more expressive color). Often the user's actual pick.
- **V3 — novel.** Genuinely different layout, metaphor, or interaction. Stretches the conversation; surfaces preferences the user didn't know they had.
- **Cover both ends.** All-safe wastes their time. All-wild looks like you ignored the brief.

## Substantive variation, not cosmetic
A variation is not «same design with a different blue». Each variation must differ on something the user can articulate in one sentence: layout, hierarchy, what's primary vs secondary, density, interaction approach, copy strategy. If two variations are too close — drop one.

## One file, many variants
**Never produce `v1.html` / `v2.html` / `v3.html`.** Use one file with side-by-side variants visible OR a tweak panel that toggles between them. Comparison is the whole point — scattered files defeat it.

## Tweakable defaults
Even when the user didn't ask for tweaks, expose **3-8 controls** for obvious axes of variation (primary color, font, density, layout variant, headline copy). Floating panel bottom-right titled «Tweaks», completely hidden when off (design must look final without chrome). CSS custom properties for visual tokens — they update everything live. Full mechanism: `procedures/make-tweakable.md`.

## Annotate + recommend
Each variation gets a one-line caption stating its intent. End with a clear recommendation — designer offers an opinion, doesn't hedge with «all options are equally good».
