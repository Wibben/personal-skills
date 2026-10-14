# Canadian English spelling

Canadian spelling mixes British and American forms. The references are the
*Canadian Oxford Dictionary* and *The Canadian Style* (Government of Canada).
`scripts/style-check.py` checks the common pairs in this file.

## Which variant to use

Decide once per document, before you write or rewrite anything:

1. **New document** — use Canadian spelling.
2. **Existing document with American spelling and no Canadian spelling** —
   keep American spelling. Do not convert the document.
3. **Existing document with Canadian spelling and no American spelling** —
   keep Canadian spelling.
4. **Existing document with both** — use the majority variant (Canadian on a
   tie). Fix the minority words only in the text you touch, and tell the user
   that the document is mixed.

For source code, the document is the file: decide from the comments and
docstrings in that file. For a commit message or a PR description, use
Canadian spelling.

Run `scripts/style-check.py FILE` to see which variant a document uses. The
first line of output names the variant.

## Never change

- Code: identifiers, API names, keywords, CSS properties (`color`,
  `text-align: center`), config keys, CLI flags, and file names.
- Literal strings that the reader must type or match: UI labels, log lines,
  error messages quoted from a program.
- Proper nouns and product names ("World Health Organization", "Center for
  Internet Security").
- Direct quotations and titles of cited works.

## Canadian forms

| Pattern | Canadian | American |
|---|---|---|
| -our | colour, behaviour, favour, honour, labour, neighbour, flavour, harbour, rumour, vapour, endeavour | color, behavior, … |
| -re | centre, fibre, litre, metre (unit), theatre, calibre, manoeuvre | center, fiber, … |
| doubled L before a suffix | travelled, cancelled, labelled, modelled, signalling, levelled, fuelled, totalled, channelling, counsellor | traveled, canceled, … |
| -ence (noun) | defence, offence, pretence, licence (noun) | defense, offense, … |
| -ise (verb) / -ice (noun) | practise (verb), practice (noun), license (verb), licence (noun) | practice, license (both) |
| -ogue | catalogue, dialogue, analogue, prologue | catalog, dialog, … |
| other | grey, cheque (bank), jewellery | gray, check, jewelry |

## Where Canadian matches American

Do not change these to British forms:

- **-ize and -yze**: organize, realize, optimize, analyze, paralyze.
- **program** for every sense, including "a television program".
- **tire, curb, aluminum, draft, plow, skeptic, artifact, aging.**
- **meter** for a measuring device ("a gas meter"). "Metre" is only the unit.
- **check** for every sense except the bank instrument.

## Words to watch

- **Licence / license.** The noun is "licence" ("a software licence"). The
  verb is "license" ("we license the code"). Keep the spelling of a licence
  name or file: `LICENSE`, "MIT License".
- **Practice / practise.** The noun is "practice" ("best practice"). The verb
  is "practise".
- **Dialogue / dialog.** Use "dialogue" in prose. A UI element called a
  "dialog" in the product keeps its product spelling, in code font or bold.
- **Analogue / analog.** Use "analogue" in prose. Keep "analog" where it is
  part of a part name, a signal name, or a quoted standard.
- **-our derivatives.** Some keep the "u" and some drop it. Keep it in
  "colourful", "honourable", "favourite", and "behavioural". Drop it in
  "honorary", "humorous", "laborious", and "vigorous".
