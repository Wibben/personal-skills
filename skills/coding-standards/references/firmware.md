# Firmware and embedded code

Read `general.md` and `c-cpp.md` first. These rules add the constraints of
code that runs without an operating system, or on a small one.

## State

- **No dynamic allocation after initialization.** Size buffers at compile
  time or allocate them once during bring-up.
- **No recursion**, and no large arrays on the stack. Stack size is fixed and
  an overflow corrupts memory without an error.

## Hardware access

- **Access registers through the project's accessors** (read, write, and
  read-modify-write helpers). Do not dereference a raw `volatile` pointer in
  driver logic.
- **Use the register definitions the project already has**, generated or
  from the vendor (for example, CMSIS device headers or Zephyr devicetree
  macros). Do not type an address or an offset by hand, and do not add a
  wrapper macro that only one place uses.
- **Order matters.** Where a write must reach the device before a later
  access, use the barrier or fence the platform requires, and say why in one
  line.
- **Every poll loop has a timeout.** A loop that waits on a hardware bit
  stops after a bounded time or count, and reports which bit it was waiting
  on. Never spin forever.
- **Read-modify-write on a shared register** happens in a critical section,
  or uses the hardware's set and clear registers.

## Interrupts and concurrency

- **Keep interrupt handlers short.** Acknowledge, capture, signal, and
  return. No blocking calls, no logging to a slow device, no polling.
- **Data shared between a handler and the main loop** is `volatile` or
  atomic, and a multi-word update happens with interrupts masked or behind a
  lock.
- **State the owner.** For each shared region, one side writes and the other
  reads, or a written protocol says who owns it when.

## Interfaces with the host

- **Shared constants come from the firmware headers.** The host parses or
  generates them. Do not copy values by hand into host code.
- **A new field in a host and firmware frame lands with the code that reads
  it** (see `general.md`). Check `sizeof` and `offsetof` with a
  `static_assert` on the firmware side.
- **State byte order and packing** for every struct that crosses the
  boundary.

## Diagnostics

- **Log with the project's levels.** The default build prints only errors and
  milestones. A hot path does not log.
- **Counters over prints** for events that repeat. A counter that the host
  can read costs nothing when nobody looks.
- **Do not state hardware behaviour you have not observed** as fact in a
  comment (see `general.md`). Write "assumed", and name the test that would
  check it.
