---
name: colour-scheme
description: "Build light and dark colour schemes for web pages, UIs, artifacts, and slide decks from Sanzo Wada's A Dictionary of Colour Combinations (348 curated palettes). Picks combinations at random, by a brand colour, or by colour name; derives full UI tokens (background, surfaces, text, accents, status) that pass WCAG contrast in both modes; chains related schemes for nested areas such as cards; writes an HTML preview; and outputs CSS custom properties or JSON. Use when the user asks for a colour scheme, palette, theme, light or dark mode colours, brand or accent colours, or colours for a page, artifact, or deck, or when you are about to choose UI colours yourself. Not for chart series colours: use dataviz for those."
metadata:
  version: "1.0"
---

# Colour scheme

Start every scheme from a combination in the book, not from colours you
invent. The script holds the data and the colour maths. Never load
`data/colors.json` into context: it costs about 20K tokens. Run the script
with `python3 -I <skill-dir>/scripts/scheme.py`.

## Process

1. **Find candidates.** Choose the command from what the user gives you:

   | The user gives | Command |
   |---|---|
   | Nothing, or "surprise me" | `random --count 5 [--size 3] [--seed N]` |
   | A brand or existing colour | `near "#3a6ea5" [--size 3]` |
   | A colour word or mood ("rose", "olive") | `search rose` |
   | Combination numbers | `show 176 43` |

   `--size` limits a search to combinations of 2, 3, or 4 colours. Three
   colours suit most UIs. Two give a calm, minimal scheme. Four suit
   illustration-heavy pages and decks. Chat cannot show colour, so do not
   draw swatches with Unicode blocks. When the user runs the script in a
   terminal (`! python3 … --swatches show 176`), it prints real colour
   blocks.

2. **Preview 3 to 5 candidates** and let the user choose:

   ```bash
   scheme.py preview 176 1 121 --random 2 -o <scratchpad>/colour-scheme-preview.html
   open <scratchpad>/colour-scheme-preview.html
   ```

   Each candidate shows a mock page and its cards in light and dark mode.
   A bare ID also adds a chained card of moderate strength. `ID:CARD`
   chooses the card scheme, and `ID:none` leaves it out. If the user is not
   there to choose, choose the candidate that best fits the content.

   Give each candidate a one-line reason based on what you can see:
   warm or cool, muted or saturated, high or low contrast between the
   colours, and how that fits the content. For example: "Muted and warm,
   with one cool accent: quiet enough for long reading." Do not use
   colour-psychology claims such as "blue builds trust".

3. **Chain schemes, if the design has distinct areas** (cards, a sidebar,
   callouts). Run `chain ID` to list combinations that share a colour with
   the page. The shared colour is the *bridge*. It becomes the card's
   heading and top-edge colour, which links the card to the page. The
   card's other colours give it its own character. Results go from
   `subtle` to `bold`.

4. **Build the tokens** in the format that the target needs:

   | Target | Command |
   |---|---|
   | Web page, artifact, or app CSS | `build 176 --card 194 --format css` |
   | Slide deck, map, or another tool | `build 176 --card 194 --format json` |

   Repeat `--card` for more chained schemes (named `card`, `card-2`, and
   so on). Add `--prefix cs-` if the token names would collide with
   existing CSS variables. `build` prints contrast warnings to stderr. If
   any appear, report them to the user.

5. **Apply the tokens.** Components use only `var(--…)`, never raw hex.
   Put `data-scheme="card"` on the element where a chained scheme starts.
   Everything inside it then uses the card's tokens. For Tailwind, map
   theme colours to the CSS variables instead of copying hex values.

## Rules for chaining

- Use no more than two levels: page → card. A third level, such as a chip
  inside a card, uses the card's `--surface-2`. It never gets a new scheme.
- All cards of one kind share one scheme. Use a second chained scheme only
  for a different kind of area, for example a callout as opposed to a
  content card.
- Use `subtle` or `moderate` for content cards, and `bold` for one feature
  area at most.
- A card scheme must share a colour with the page scheme. The script
  enforces this.

## Tokens

| Token | Use |
|---|---|
| `--bg`, `--surface`, `--surface-2` | Page or card background; raised areas; inset areas and chips |
| `--border`, `--edge` | Hairlines; the coloured top edge of a card |
| `--fg`, `--fg-muted`, `--heading` | Body text; secondary text; headings (the bridge colour in a card) |
| `--primary`, `--on-primary` | Main actions: primary button fill and its text |
| `--secondary`, `--on-secondary` | Secondary button fill and its text |
| `--accent`, `--on-accent` | Highlights: tags, selected states, one-off emphasis. The third colour; in a 2-colour scheme it equals `--secondary`, and in a card it is the bridge when the card has no third colour |
| `--link` | Links and primary-coloured text |
| `--success`, `--warning`, `--error` | Status text and outlines |
| `--c1` … `--c4` | The book's colours, unchanged, for decoration only: illustrations, hero blocks, slide shapes |

The roles come from the palette's chroma. The most saturated colour is
`--primary`, then `--secondary`, then `--accent`. The least saturated
colour tints the neutrals.

All text tokens pass 4.5:1 against every surface in their scheme, and
`--primary` passes 3:1 against the background. No derived token is pure
black or pure white. Fills, text, and surfaces are tinted toward the
palette. These checks pass for every combination and every chained option,
in both modes.

## Gotchas

- **The hex values change on purpose.** The book's colours are print
  colours, and many are pastel. The script keeps each hue but changes
  lightness to meet contrast targets, so `--accent` can be darker in light
  mode and lighter in dark mode than the source colour. Do not put the raw
  colour back. Use `--c1` … `--c4` when you need the exact source colour.
- **Dark mode is derived, not looked up.** Only 9 of the 159 colours are
  dark enough to be a background, so the script calculates dark surfaces
  from the palette's hues. Do not search the book for dark combinations.
- **`--c*` tokens can fail contrast.** Before you put text on one, run
  `contrast FG BG`. It also suggests the nearest passing colour with the
  same hue.
- **The CSS follows the artifact dark-mode format.** Tokens are on
  `:root`. Dark mode is under `prefers-color-scheme: dark`, guarded by
  `:root:not([data-theme="light"])`, and again under
  `:root[data-theme="dark"]`. The output works in an artifact without
  changes.
- **Colour names keep the dataset's spelling** ("Calamine BLue",
  "Cerulian Blue"). Do not correct them, because `search` uses them.
- **Chart colours are a separate task.** Use the dataviz skill for chart
  series colours. Use this skill for the colours around the charts.

## Source

The data comes from Sanzo Wada, *A Dictionary of Colour Combinations*
(1933–34), as compiled in
[mattdesl/dictionary-of-colour-combinations](https://github.com/mattdesl/dictionary-of-colour-combinations)
(MIT, `LICENSE-dictionary-of-colour-combinations`). Combination numbers
are the dataset's (1–348).
