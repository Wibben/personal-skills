# Validation and test scripts

A validation script decides pass or fail. Examples: unit tests, integration
tests, regression runs, hardware validation scripts, and scripts that run a
whole test matrix. Read `general.md` and the file for the script's language
first.

## The verdict

- **The exit code is the verdict.** Exit 0 only on pass. Every failure path
  exits non-zero, including a crash, a timeout, and a missing input.
- **No trivial pass.** A test must fail if it did no work.
  - Comparing two empty results passes and proves nothing. Seed the input
    with real data: a trip with priced activities, a buffer with a known
    pattern.
  - When an operation repeats N times, check that it ran N times. A check
    on the final state proves only that the last run worked.
  - A test that skips every case is not a pass. Report it as skipped.
- **Check the evidence, not only the exit code.** Name the value, count, or
  log line that proves the behaviour. Where there is nothing to compare,
  that check *is* the whole proof, and a zero or empty value is a failure.
- **Check that errors are absent too.** Search the output for known error
  messages, assertion failures, and warnings, and fail if any appear.

## Log lines that scripts read

- **Fix the format of each evidence line** and treat it as an interface. For
  example: `RESULT share_viewer: PASS (trips=3, price_fields=0)`.
- **Change the line and its readers in the same commit.** Before you change a
  log line, search the gate scripts for the old text. A stale pattern fails a
  good run. A pattern that matches nothing passes a bad run.

## Reproducibility

- **Log every input that changes the result**: the seed, the configuration,
  the target, and the build or commit ID.
- **Select variants through configuration or arguments**, through one
  mechanism for the whole suite. Do not invent a new override per test.
- **Reuse the existing test vehicles.** Add a mode or a parameter to an
  existing test before you create a new test directory.
- **Every wait has a timeout**, and a timeout is a failure with a message that
  says what the script was waiting for.

## Failures

- **No flake attribution without a serial re-run.** Do not blame
  concurrency, flakiness, or the environment until runs that are serialized
  one at a time show it. "Flaky" ends the investigation. "Unexplained" keeps
  the run.
- **Keep the artifacts of a failed run**: the log, the configuration, and
  the seed. Print their location.
- **The failure message names the check, the expected value, and the actual
  value.**
