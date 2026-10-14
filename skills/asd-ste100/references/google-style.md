# Google Developer Documentation Style Guide — working summary

This file paraphrases the parts of the
[Google Developer Documentation Style Guide](https://developers.google.com/style)
that matter most for technical writing. It is a summary, not the guide. When a
rule here is unclear, read the linked page.

The guide is by Google and is licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). This file is an
adaptation: it paraphrases, shortens, and changes the guide as described in
this file.

Two departures from the guide apply in this skill:

- **Spelling.** The guide uses American spelling. This skill uses Canadian
  spelling unless the document already uses American spelling. See
  `canadian-english.md`.
- **Semicolons.** The guide allows semicolons. STE bans them (Rule 8.1), and
  STE wins. Write two sentences.

## Tone and content

- Be conversational and friendly, without being frivolous. No jokes, no
  exclamation marks, no emoji in technical text.
- Do not pre-announce. Do not write "This section describes…" or "In a future
  release…". Describe what exists.
- Write timeless text. Avoid "currently", "now", "new", "soon", "latest", and
  "at the time of writing". State a version or a date if the time matters.
  Changelogs and release notes are the exception.
- Write for a global audience. Avoid idioms, cultural references, and humour
  that does not translate.
- Write accessibly. Do not use "see" or "click here" as the only cue. Do not
  rely on colour or position alone to carry meaning.
- Use descriptive link text: "read the [installation guide](…)", not "[click
  here](…)" or a bare URL.
- Do not use "please", "simply", "easy", "just", or "obviously". They add
  nothing, and they insult a reader who finds the task hard.
- Use inclusive language: "allowlist" and "denylist", "primary" and "replica",
  "placeholder", "check" or "quick check". Avoid "whitelist", "blacklist",
  "master", "slave", "dummy", and "sanity check". Where a product name or an
  API forces the old term, put it in code font and do not use it in prose.

## Language and grammar

- **Second person.** Address the reader as "you" in user-facing docs. Use "we"
  only for the organization that wrote the doc, and sparingly.
  - In specs, plans, and design docs with several actors, name each actor by
    role ("the host", "the firmware", "the CI job"). "You" is ambiguous when
    there is more than one actor.
- **Active voice.** Make clear who does the action.
- **Present tense.** "The command returns", not "the command will return".
  Use the future only for something that happens later.
- **Condition before instruction.** "To delete the cache, run `make clean`."
  "If the port is down, restart the service."
- **Imperative for steps.** "Run the script", not "You should run the script".
- **Contractions.** Common contractions ("it's", "don't", "can't") are fine
  in conversational docs. Do not use them in Strict mode, and never use rare
  ones ("would've", "mustn't").
- **Pronouns.** Do not start a sentence with a bare "this" or "it" when the
  referent is unclear. Write "this command", "this value".
- **Abbreviations.** Spell out an abbreviation on first use, with the short
  form in parentheses. Skip this for widely known terms (API, CPU, URL, USB).
- **No Latin abbreviations.** Write "for example", "that is", "and so on",
  "through", "compared with", and "note" instead of "e.g.", "i.e.", "etc.",
  "via", "vs.", and "N.B.".
- **No "and/or".** Write "A, B, or both".
- **Directional words.** Write "preceding" and "following", not "above" and
  "below", when you refer to other content in the document.

## Formatting and organization

- **Headings** in sentence case, with no final period. Start a task heading
  with a bare verb ("Install the toolchain"). Start a concept heading with a
  noun ("Memory layout").
- **One H1** per document. Do not skip heading levels.
- **Lists.**
  - Numbered for a sequence, bulleted for everything else.
  - Use a description list (term, then description) for pairs of related
    data.
  - Introduce a list with a full sentence or a fragment that ends in a colon.
  - Keep items grammatically parallel. Start each with the same part of
    speech.
  - Use a list only for two or more items. Use a sentence for one.
  - End an item with a period if it is a full sentence. Otherwise use no
    punctuation.
- **Tables** for data with more than one dimension. Every table has a header
  row. Do not put long prose in a cell.
- **Serial comma.** "A, B, and C".
- **Code font** for code-related text: file names, paths, commands, flags,
  functions, classes, variables, config keys, literal values, environment
  variables, and HTTP status codes.
- **Code samples.** Put a command in a code block with a language tag. Do not
  include the shell prompt (`$`) in a command the reader copies. Show the
  output in a separate block.
- **Placeholders.** In code, use uppercase with underscores (`PROJECT_ID`).
  Explain every placeholder after the block.
- **UI elements** in bold, using the exact label: "Click **Save**".
- **Dates.** Use an unambiguous format: "October 14, 2026" in prose, or
  ISO 8601 (`2026-10-14`) in technical contexts. Never `10/14/26` or
  `14/10/26`. Canadian readers see both orders, so the numeric short form is
  ambiguous for them in particular.
- **Times.** Use the 24-hour clock in logs and technical text. Always state
  the time zone or offset.
- **Units.** Put a space between a number and its unit (`64 KiB`, `20 ms`).
  Use binary prefixes (KiB, MiB) where the value is a power of two.

## Numbers

- Spell out zero through nine. Use numerals for 10 and greater.
- Use numerals for any number, even under 10, in these cases:
  - versions, steps, pages, and chapters
  - technical quantities: memory, disk space, counts, limits, and units
  - a number in the same sentence as a number of 10 or greater
- Spell out a number that starts a sentence, or rewrite the sentence. A
  four-digit year at the start is acceptable.
- Use words such as "thousands" only for approximate amounts.

## Images

- Give every image alt text that states what the image shows.
- Use vector or high-resolution images where practical.
- Do not put text in an image when the text could be in the document.

## Sources

- [Highlights](https://developers.google.com/style/highlights)
- [Word list](https://developers.google.com/style/word-list)
- [Numbers](https://developers.google.com/style/numbers)
- [Inclusive language](https://developers.google.com/style/inclusive-documentation)
- [Timeless documentation](https://developers.google.com/style/timeless-documentation)
