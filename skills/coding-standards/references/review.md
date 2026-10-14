# Code review procedure

Use this procedure for every review: a PR, a branch, a commit, or a diff in
the working tree. A partial review misses the regressions that matter, so do
every step.

## 1. Trace every logic path

Walk each changed function branch by branch. Look for:

- a branch that no longer handles a case that it handled before
- an error path that is dropped, swallowed, or now returns success
- a new condition with no `else`, where the `else` case can happen
- a loop whose first or last iteration behaves differently

## 2. Find every site of a rename

When the change renames or removes a name, search the whole repository for
the old name. A name can be a function, a symbol, a field, a config key, or
a log string. Check each hit:

- code, including tests
- comments, docstrings, READMEs, and design docs
- string-based references that the compiler does not check: dynamic
  dispatch, reflection, serialized keys, command-line flags, and grep
  patterns in scripts

## 3. Show every behaviour change in a refactor

For a refactor, compare the old and the new behaviour side by side. List
each difference. Then judge each one on its merits:

- Do not assume that a difference is a regression. A refactor can fix a bug
  or tighten a check on purpose.
- Do not assume that a difference is intended. Surface it and ask the
  author.
- If the commit message calls the change a "rename" or a "refactor" but it
  changes behaviour, flag the message. A reader of `git log` will not look
  for a behaviour change in a commit called "rename".

## 4. Check that docs match code

Compare the documentation with what the code does:

- READMEs, design docs, and examples that the code references
- doc comments and docstrings on changed functions, including parameter
  descriptions and return values
- renamed symbols that docs still mention
- behaviour that a doc describes and the code no longer has

Flag each mismatch, with the doc location and the code location.

## 5. Check against the standards

Check the changed lines against `general.md` and the domain files for the
files the change touches. Cite the rule in each finding.

## Writing the findings

- Order findings by severity: wrong behaviour first, then missing coverage,
  then stale docs, then style.
- Each finding gives the file and line, what is wrong, a concrete case that
  shows it, and the rule or reason.
- Say "I am not sure" when you are not sure. Do not state a guess about a
  behaviour change as a fact.
