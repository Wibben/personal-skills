# Debug scripts

A debug script reads state from a running system to explain a problem:
registers, memory, counters, logs, or the state of a service. Read
`general.md` and the file for the script's language first.

## Read-only by default

- **A debug script does not change the system unless a flag tells it to.**
  A write, a reset, or a clear needs an explicit flag (`--write`, `--reset`).
  Before the script changes anything, it prints what it will change.
- **Reading must not change state.** Know which registers clear on read and
  which FIFOs pop on read. Do not read them by default, or warn when you do.
- **Safe to run twice.** Two runs in a row give the same output if the system
  did not change.

## Output

- **Print values in the form the reader compares them in**: hex for
  addresses, registers, and bit fields, with the field names decoded. Decimal
  with units for counts and times.
- **Name every value.** Print the register or field name next to the raw
  value, so the output makes sense without the source.
- **Mark the abnormal.** Highlight a value that differs from its reset value,
  its expected value, or the previous run. Do not make the reader diff by
  eye.
- **No intermediate dumps by default.** Raw tables and parsed records go
  behind `--verbose`.
- **Say what was not read.** If a block was powered down or a read timed out,
  print that, not a zero.

## Structure

- **Reuse the project's access layer** (register accessors, device handles,
  the debug client). Do not open a second path to the hardware.
- **Import shared code as a module.** If another script already decodes a
  structure, import it. Do not copy the decoder.
- **Take the target as an argument**: device, core, chip, host, or port. Do
  not hard-code it.
- **A debug script that becomes useful stays.** Move it into the project's
  scripts folder with a usage message. Do not leave it in a scratch folder.
