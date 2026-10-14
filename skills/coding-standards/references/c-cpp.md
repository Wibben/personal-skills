# C and C++

Read `general.md` first. For code that runs on bare metal or a
microcontroller, read `firmware.md` too.

## Both languages

- **`#include` lines carry no trailing comment.** Anyone can see what a
  header supplies, and the note goes stale.
- **Include what you use.** Each file includes the headers for the symbols it
  uses. Do not rely on a transitive include.
- **Doxygen for every function comment** (`/** … */` with `@brief`,
  `@param`, `@return`, and `@note`), within the limits in `general.md`. Put
  the comment on the declaration in the header for a public function, and on
  the definition for a `static` function.
- **Fixed-width types for anything with a layout**: registers, wire formats,
  file formats, shared memory, and ABI structs. Use `uint32_t`, not
  `unsigned long`.
- **Check layout at compile time.** For each struct that crosses a boundary,
  add a `static_assert` on `sizeof` and on the `offsetof` of each field the
  other side reads.
- **No undefined behaviour.** Watch for these:
  - signed overflow
  - a shift by the width of the type or more
  - unaligned access through a cast pointer
  - type punning through a pointer cast (use `memcpy`, or a union in C)
  - a read of uninitialized memory
- **Check every return value** that can report failure. If you ignore one on
  purpose, cast it to `(void)` and say why.
- **`const` by default** for pointers to data the function does not change,
  and for file-scope tables.
- **`sizeof` the object, not the type**: `memset(&cfg, 0, sizeof(cfg))`.
- **Prefer an `enum`, a `static inline` function, or a `const` value** to a
  macro. A macro stays only where the language needs one: include guards,
  conditional compilation, and token pasting.
- **Build warning-clean** at the project's warning level. Do not add a pragma
  that silences a warning without a comment that says why the warning is
  wrong.

## C

- **Unwind errors with one exit path.** `goto cleanup` with labels in reverse
  order of acquisition is acceptable and often clearest.
- **`static` for every function and file-scope object that is not part of
  the interface.**
- **Bounded string functions.** `snprintf`, not `sprintf`. Check its return
  value for truncation where truncation matters.

## C++

- **Rule of zero.** Hold resources in RAII types (`std::unique_ptr`,
  containers, project handle types), so the class needs no destructor, copy,
  or move code of its own. No raw `new` or `delete`.
- **`enum class`**, not plain `enum`, for new enumerations.
- **`override`** on every overriding function. `final` where a class is not
  designed for derivation.
- **`std::array`, `std::span`, and `std::string_view`** in place of a raw
  pointer and a length.
- **Pass by `const&`** for a large input, by value for a small one or one you
  move from.
- **No exceptions or RTTI** where the project builds without them. Follow the
  project's error type (status codes, `std::expected`, or a result type).
- **Mark single-argument constructors `explicit`.**
