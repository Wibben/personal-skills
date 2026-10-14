# Shell scripts

Read `general.md` first. If the script decides pass or fail, read
`validation.md` too.

## When to use shell

- **Shell is for gluing commands together.** When a script needs data
  structures, parsing, or more than about 100 lines of logic, write it in
  Python instead.

## Safety

- **Start every Bash script with `set -euo pipefail`.** If a command is
  allowed to fail, say so at that line (`|| true`) with a comment that says
  why.
- **Quote every expansion**: `"$var"`, `"$@"`, `"$(command)"`.
- **`[[ … ]]`** for tests in Bash.
- **`mktemp`** for temporary files and directories, and a `trap` that
  removes them on exit.
- **Do not parse `ls`.** Use a glob or `find -print0` with `xargs -0`.
- **Run `shellcheck`** and fix what it finds, or disable a single check on
  one line with a reason.

## Structure

- **Functions for repeated steps**, with `local` variables.
- **A usage message** for `-h`, and for a wrong number of arguments.
- **Absolute or script-relative paths.** Resolve the script's directory with
  `"$(dirname "${BASH_SOURCE[0]}")"`. Do not depend on the caller's
  current directory.

## Output

- **Print the elapsed time of a long step.** Set `SECONDS=0` at the start of
  the step and print `elapsed ${SECONDS}s` at the end.
- **Print one fixed-format line per result** that a later script or a human
  can search for. See `validation.md`.
