# JavaScript, TypeScript, TSX, HTML, and CSS

Read `general.md` first.

## TypeScript and JavaScript

- **TypeScript in strict mode** where the project uses TypeScript. No `any`.
  Use `unknown` and narrow it. A type assertion (`as`) needs a reason.
- **`const` by default, `let` when you reassign, never `var`.**
- **`===` and `!==`**, never `==` or `!=`.
- **`async` and `await`** over `.then()` chains. Every promise is awaited,
  returned, or explicitly handled. No floating promises.
- **Validate data at the boundary.** Parse data from the network, storage, or
  the URL into a typed shape once, where it enters, and trust the type after
  that.
- **TSDoc or JSDoc (`/** … */`) for every exported function, hook, and
  component**, within the limits in `general.md`. An internal helper whose
  name and signature say everything needs no comment.
- **`@param` and `@returns` only for meaning the name and type do not
  carry**: units, valid ranges, direction of a conversion. A `@param` that
  restates the type ("`tripId` — the trip ID") is noise. Leave it out.
- **Document React props on the props `interface`**, one line per field
  where the name is not enough. Not in a `@param` list.
- **Named exports** over default exports, unless the framework requires a
  default (for example, a route or page file).

## React and TSX

- **Function components and hooks.** Follow the rules of hooks: call hooks at
  the top level, in the same order every render.
- **Derive, do not sync.** Compute a value from props and state during render.
  Do not copy it into state with `useEffect`.
- **Stable `key`s** from the data's identity, never from the array index for a
  list that can reorder.
- **Keep components small.** Split a component when it handles more than one
  concern, not when it reaches a line count.

## HTML and accessibility

- **Semantic elements first**: `button`, `a`, `nav`, `main`, `label`, `table`.
  A `div` with a click handler is not a button.
- **Every input has a label.** Every meaningful image has `alt` text, and a
  decorative image has `alt=""`.
- **Everything works from the keyboard**, with a visible focus indicator.
- **ARIA only when no native element fits.** Wrong ARIA is worse than none.
- **Do not carry meaning by colour alone.**

## CSS

- **Follow the project's approach** (CSS modules, utility classes, or styled
  components). Do not mix in a second one.
- **Design tokens or variables** for colours, spacing, and type sizes. No new
  magic values.
- **No inline `style`** unless the value is computed at run time.

## Security

- **Never put untrusted data into HTML** through `innerHTML`,
  `dangerouslySetInnerHTML`, or string-built markup. If you must render HTML,
  sanitize it with the project's sanitizer.
- **No secrets in client code.** Anything the browser loads, the user can
  read.

## Dependencies and tooling

- **Do not add a dependency** for something the platform or an existing
  dependency already does. A new dependency needs a reason in the commit
  message.
- **Run the project's linter and formatter** (for example, ESLint and
  Prettier) at commit time.
- **Exempt hand-wrapped prose from the formatter.** A formatter that reflows
  a spec makes thousand-line diffs that hide the real edits. List the spec in
  `.prettierignore`, and enforce its line width with a separate script.
- **Sort utility classes with the formatter plugin** (for example,
  `prettier-plugin-tailwindcss`), so a duplicate shows up in a diff.
