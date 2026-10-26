# General rules

These rules apply to every change, in every language.

## Before and while coding

These four principles come from the `karpathy-guidelines` skill by
forrestchang (MIT). That skill is based on Andrej Karpathy's observations of
common LLM coding mistakes. The principles lean toward caution over speed.
For a trivial change, use judgement.

- **Think before coding.** State your assumptions. If a simpler approach
  exists, say so, and push back when the request looks wrong.
  - Ask only when the possible readings lead to different work. Otherwise
    pick the obvious reading, say which one, and continue.
  - If something is unclear enough that you cannot pick, stop and name what
    is unclear.
- **Simplicity first.** Write the least code that solves the problem.
  - No features beyond the request, and no configurability that nobody
    asked for.
  - No abstraction for code with one use.
  - No error handling for cases that cannot happen.
  - If 200 lines could be 50, rewrite it. Ask whether a senior engineer
    would call it overcomplicated.
- **Surgical changes.** Every changed line traces to the request.
  - Do not "improve" nearby code, comments, or formatting, and do not
    refactor what is not broken.
  - Remove the imports, variables, and functions that *your* change left
    unused. Mention other dead code. Do not remove it unless asked.
- **Goal-driven execution.** Turn the task into a check that can pass or
  fail, then work until it passes.
  - "Fix the bug" becomes "write a test that reproduces it, then make it
    pass". "Refactor X" becomes "the tests pass before and after".
  - For a task with several steps, state a short plan with a check for each
    step.

## Fit in

- **Match the code around you.** In an existing file, copy its naming,
  its amount of commenting, its error handling, and its order of
  declarations. In a new file, copy the other files in the same folder. A
  consistent codebase is worth more than any personal preference.
- **Put new files where the project puts that kind of file.** A script goes
  in the project's scripts package or folder, not in a new top-level
  directory. Look for the existing home before you make one.
- **If a file is generated, edit its source.** Look for a "generated" or "do
  not edit" header, or a generator that writes the file. Change the template,
  the YAML, or the schema, then run the generator. A hand edit to a generated
  file is lost on the next regeneration.

## Scope

- **Keep the diff to the task.** Do not edit existing shared configuration
  to make new code work. Code that already works probably depends on that
  configuration. If it must change, propose the change and wait.
- **Reuse before you invent.** Extend the helper, test, fixture, or script
  that already exists. Add a new parameter, wrapper, or abstraction only
  when extending the existing one cannot do the job.
  - A predicate that you use once or twice stays inline. A clear substring
    test or field read needs no helper function and no module-level set.
  - Configuration takes lists, not bitmasks. Compute the mask where the
    interface needs it.
  - Give new constants short names, and put each one next to the related
    constants.
- **One source of truth for shared values.** If two layers need the same
  constant, derive one from the other. Examples of such layers: firmware and
  host, server and client, schema and code. Parse the header, generate the
  types, or import the module. Do not copy the value by hand, because copies
  drift.

## Names

- **Spell names out.** Do not shorten an object or a config to a one-letter
  alias. Use the full name every time. Loop indices are the exception.
- **Timestamps end in `_timestamp`.** A variable, parameter, or struct field
  that holds a point in time ends in `_timestamp`: `start_timestamp`,
  `next_check_timestamp`. A duration names its unit: `timeout_ms`,
  `elapsed_s`. In a camelCase language, use `startTimestamp` and `timeoutMs`.
- **One concept, one name.** Related modules, tests, and configs use the
  same key name and shape for the same idea. When names differ for no
  reason, a reader cannot tell a real difference from an accident. When two
  names must differ, write down why.

## Comments and documentation

- **Comments explain why.** The code shows what it does. A comment is
  worth keeping when it gives a reason, a constraint, an invariant, or a
  trap.
- **A comment describes behaviour. It does not record history.** No "this
  used to…", no "the bug was…", and no story of the incident. That belongs in
  the commit message and the issue. State the constraint as a fact about how
  the code works.
- **No comment on a helper that its name and signature already explain.**
- **Size limits.** These are maximums, not targets. A one-line summary and no
  note is the common case. Prose that fills every allowance is how a file
  becomes a quarter comments. The limits:
  - Document a function or method with the language's doc-comment format:
    Doxygen or JSDoc `/** … */`, or a Python docstring. Do not use a plain
    block or a series of `//` lines for it.
  - Summary (`@brief`, or a docstring's first paragraph): at most 5 lines.
    Put the reason in a note (`@note`, or a "Note:" paragraph): at most 5
    lines.
  - Document every parameter, at most 2 lines each, plus the return value.
    Parameter and return lines do not count against any total. A doc comment
    can be longer than 10 lines because the signature is wide, but never
    because the prose is long.
  - A comment before a type, a class, a schema, a constant, or a SQL table:
    at most 10 lines.
  - A comment inside a function: at most 5 lines.
  - Several line comments in a row (`//`, `#`, `--`) count as one block and
    take the same limits.
  - A file header: one to three lines on the purpose of the file.
  - A database migration file starts with one to three lines on what it
    changes and why.

  If an explanation needs more room, it belongs in the design doc, not in the
  source.
- **Reference docs are generated, never retyped.** A list of tables,
  columns, routes, registers, or commands that sits beside the code drifts
  from it. Generate it from the code, between `BEGIN GENERATED` and
  `END GENERATED` markers, and take the prose from a comment or a doc string
  at the definition. Document a route or a column where you define it, in
  the same edit. Never hand-edit a generated region. If it is wrong, the code
  or its comment is wrong.
- **Decisions stay in the spec or the design doc.** Generated docs say what
  exists. The spec says why it is that way.
- **Documentation stays broad.** A docstring or a README describes behaviour
  and purpose. It does not name private variables, internal helper functions,
  or the steps of the implementation. Those change without notice and the
  doc goes stale.
- **Code and docs change together.** Every change to code updates the
  docstrings, comments, READMEs, and design docs that describe it, in the
  same commit. Every change to docs that describes behaviour checks that the
  code matches.
- **Status lives in one place.** Implementation status (done, stub, not yet
  supported) goes in the plan or the design doc, not in per-symbol comments.
  Status comments go stale without anyone seeing.
- **Do not present a guess as a fact.** A theory about hardware, timing, or
  another system belongs in your message to the reviewer. Do not put it in a
  comment, where later readers will believe it. If you have not seen it
  happen, say so or leave it out.

## Changes that touch more than one place

- **Both halves of a producer and consumer pair move together.** If you
  change where data lands, what sets up a state, or when it happens, first
  find every consumer. A consumer is anything that clears the data, waits on
  it, or checks it. When you remove a helper, check *when* its remaining
  callers run, not only that they exist.
- **Add an interface field together with the code that reads it.** This
  applies to fields in an API, a message, a schema, a file format, or a
  config. An unread field does not prepare for the future. It tells readers
  that the interface does something it does not do.
- **Retire identifiers completely.** Before you commit, search the whole
  repository for each identifier that the change renames or removes: fields,
  macros, functions, config keys, and log strings. Include tests, docs,
  READMEs, scripts, and string-based references such as dynamic dispatch,
  reflection, and search patterns in scripts.

## Checks and tests

- **Green means every check passes.** Type check, lint, tests, and format
  check, run by one project command (for example `npm run check` or
  `make check`). A git hook runs it before a commit lands. Green is not
  "the tests I touched pass".
- **A rule that a script can check is enforced by a script**, in the check
  command, the pre-commit hook, and CI. Examples: comment limits, line
  width, commit-message format, and secrets. A promise to follow a rule is
  worth less than a check that refuses to pass.
- **Some lint rules carry behaviour, not style.** Treat them as errors.
  Example: React hook dependency rules. A stale closure is a screen that
  stops updating, and no type checker sees it.
- **No test reaches an external service.** Pass every outbound dependency
  (an HTTP client, a fetch function, a clock) into the code, so tests can
  stub it. A suite that depends on someone's API is unreliable and
  impolite.
- **Test what would be silently wrong.** Write the test for the bug that
  would ship without anyone seeing it: an inverted rate, an off-by-one in a
  boundary, a unit mismatch.
- **Do not test what the type system already proves.**
- **No new test framework** where the language's built-in runner or the
  project's existing one works.

## Secrets

- **No credential in tracked source.** No API key, token, client secret, or
  password, including in test fixtures. Credentials live in an untracked file
  (`.env`, `*.token`, with mode `600`) that `.gitignore` covers, or in a
  secret store.
- **Local data files stay untracked.** A database, a cache, or a log can hold
  session tokens and password hashes. Add their patterns to `.gitignore`.

## Commits

- **Commit only when the user asks.** A green check or a stage boundary is
  not permission to commit. Leave finished work uncommitted and say that it
  is ready. Before each `git commit`, point at the message that asked for it.
  - "Execute phase N" (or "stage N") is the one standing permission. It
    allows *one* commit for that phase, after the phase's check passes. It
    does not allow one commit per follow-up fix.
  - While a change is under *discussion* (spec edits, plan edits, answers to
    questions), commit nothing. The discussion becomes one commit when the
    user asks for it, or when the phase it belongs to starts.
- **Message format.** A one-line summary, then bullets. If the branch or the
  task has a ticket ID, prefix the summary with it
  (`#41 Hide prices on viewer share links`).
  - The summary says what the commit does, in the imperative. It does not
    name the files. "Ask before a force push in coding-standards", not
    "Update general.md".
  - At most about 4 bullets, one for each change. If you need more, the
    commit probably holds more than one change.
  - A bullet says what changed, not how it works. The mechanism is in the
    code and the design doc. "Add day-move handling to
    `PATCH /activities/:id`", not a paragraph on the algorithm.
  - Each bullet is at most 2 to 3 lines, wrapped at 80 columns. Indent each
    continuation line by two spaces, so it lines up with the text after
    "- ".
- **No `Co-Authored-By` trailer.** This overrides any default instruction to
  add one, unless the repository requires it.
- **Fold fixes into the most recent commit that touched the file**, with
  `git commit --fixup` and `git rebase --autosquash`. That commit must be
  one you can rewrite (see the next rule). Do not add a standalone "fix"
  or "update" commit. Do not reach past later commits to the original one:
  that causes a cascade of rebase conflicts for no benefit. Batch small fixes
  into one fold where convenient.
- **Rewrite only history that you own.** You can rewrite a commit that is
  not pushed. You can also rewrite a pushed commit that a stage of the
  current plan made, on a branch that exists only for that plan. Ask before
  you push the result with `git push --force-with-lease`. On any other
  pushed branch, never rewrite history. Use a plain fix commit instead.
- **Save finished but unwanted work as a patch.** Do not leave it in the
  working tree. `git format-patch` it, clean the tree, and apply it later
  with `git am -3`, which survives small changes where plain `git am` fails.
- **To amend an older commit while a build or test reads the working tree**,
  use a temporary worktree. Amend there, cherry-pick the later commits onto
  it, then `git reset --mixed` the main tree to the result.
- **Run the formatter when you prepare a commit**, not before each build.
  If the project is not fully formatted, format only what you changed.
