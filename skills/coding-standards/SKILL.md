---
name: coding-standards
description: "Personal coding standards for writing, refactoring, and reviewing code across the stack: C and C++, firmware and embedded code, Python, JavaScript, TypeScript, TSX, HTML, CSS, shell, debug scripts, and validation or test scripts. Covers comments and docstrings, commits, scope control, reuse, naming, and a code-review procedure. Use when writing or changing code, when executing an implementation plan, or when reviewing a diff, PR, or commit."
---

# Coding standards

These rules describe how to write and review code. They apply in every
language. Each domain file adds the rules for one part of the stack.

## How to use this skill

1. Read `references/general.md`. It applies to every change.
2. Read the domain file for each kind of file that the change touches:

   | Files touched | Read |
   |---|---|
   | `*.c`, `*.h`, `*.cpp`, `*.hpp`, `*.cc` | `references/c-cpp.md` |
   | Code that runs on a microcontroller, a DSP, a RISC-V core, or bare metal. Also boot code, drivers, linker scripts, and register maps. | `references/firmware.md` (and `c-cpp.md`) |
   | `*.py` | `references/python.md` |
   | `*.js`, `*.jsx`, `*.ts`, `*.tsx`, `*.html`, `*.css`, `*.scss` | `references/web.md` |
   | `*.sh`, `*.bash`, `Makefile` recipes, CI job scripts | `references/shell.md` |
   | A tool that reads or writes system state to diagnose a problem | `references/debug-scripts.md` |
   | A test, a regression script, a script that runs a test matrix, or anything that decides pass or fail | `references/validation.md` |

   A file can be in more than one row. A Python validation script takes
   `python.md` and `validation.md`.
3. **The surrounding code wins.** Where a rule here and the conventions of
   the file or folder disagree, follow the file. Where the project has a
   written style guide, a linter config, or a `CLAUDE.md`, those win too.
   Mention the conflict to the user once. Do not argue it in the code.
4. Write prose (comments, docstrings, commit messages, docs) with the
   `asd-ste100` skill if it is installed.

## Reviewing code

To review a diff, a PR, or a commit, follow `references/review.md`. Then
check the changed lines against the files from step 2. A review finding cites
the rule it breaks, so the author can tell a standard from a preference.

## User interaction

- Do not remind the user to rebuild generated binaries (`*.bin`, `*.hex`,
  `*.elf`, and similar). The user rebuilds them when they decide to.
- Do not print intermediate data (parsed tables, raw records, decoded
  structures) in a tool's output unless the user asks for it.
