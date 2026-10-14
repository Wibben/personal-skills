# Python

Read `general.md` first.

## Structure

- **A class owns the state of a tool.** Build a tool as a class that holds
  its state on the instance.
  - Use instance methods. Do not use `@staticmethod`. Use a module-level
    function only for a pure helper that another module also imports.
  - `__init__` parses arguments and runs any interactive prompts, so the
    object is ready to use when the constructor returns.
  - The `if __name__ == "__main__":` block constructs the object and calls
    one method.
- **Call other Python code in-process.** Import the other script as a module
  and call its functions. Do not run it with `subprocess`. Use `subprocess`
  only for programs that are not Python, or when you need process isolation.
- **Type hints** on every public function and method signature.
- **`pathlib.Path`** for paths, not string concatenation.
- **`argparse`** for command-line arguments. Every argument has `help` text.

## Errors

- **No bare `except:`**, and no `except Exception: pass`. Catch the exception
  you expect, and let the others propagate.
- **Context managers** (`with`) for files, locks, sockets, and devices.
- **Exit with a non-zero code on failure.** Raise, or call `sys.exit(1)`
  after you print the reason.

## Output

- **Print what the user needs, not what the code parsed.** Do not print
  intermediate data such as raw records or decoded tables unless the user
  asks for it, or a `--verbose` flag requests it.
- **Use the project's print helpers.** If the project provides coloured
  output helpers, reserve green for success and red for failure. Use a
  distinct, neutral colour for step headers and banners. A step header is
  not a success.
- **`logging`** for library code. `print` only in the tool's top-level output
  path.

## Comments and docstrings

- **Docstrings** in the format the project already uses (Google style if
  there is none). The limits in `general.md` apply: summary at most 5 lines,
  each `Args:` entry at most 2 lines.
- **A run of consecutive `#` lines is a block comment.** At most 10 lines
  before a function or class, and at most 5 lines inside a function body.
- **Docstrings describe behaviour**, not attribute names or the helper calls
  the method makes.

## Style

- **f-strings** for formatting. `%` formatting only in `logging` calls,
  where the arguments stay lazy.
- **Run the project's formatter and linter** (for example, `ruff` or `black`)
  at commit time, not before every run.
