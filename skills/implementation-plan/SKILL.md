---
name: implementation-plan
description: "Write, refine, and execute a staged implementation plan for a software change: firmware, drivers, host tools, libraries, services, web front ends, or scripts. Produces a plan file with work items (tickets or a task list), current state, ordered stages that each end on a verifiable check, verification, files to reference, and questions for the user that are folded back in. Use when the user asks for an implementation plan, a staged plan, or a plan for a ticket, or asks to execute one stage by stage."
argument-hint: "<goal> [ticket IDs] [files to read first]"
---

# Implementation plan

This skill defines how to write an implementation plan and how to execute
it. These rules tell you how to write the plan. They are not content for
the plan, so do not copy them into it.

The examples in this file come from one imagined change to a self-hosted
trip planner: share links that hide prices from viewers.

## Workflow

1. **Collect the inputs.** The user gives a goal and, optionally, ticket IDs
   and the files to read first. If the goal is missing, ask for it. If the
   files are missing, find them yourself and list what you read in the plan.
2. **Create tickets, if the user asks.** If the user wants tickets and a
   tracker tool is available (Jira, GitHub Issues, Linear), create them
   first. Give each one the type and parent that the user states. Write
   a short description yourself where the title makes it obvious. Use the
   user's text where it carries design intent. The returned IDs go into the
   plan's work-items table. Without a tracker, use a task list.
3. **Read the sources in full before you write anything.** Do not guess the
   names of functions, types, config fields, routes, registers, or
   endpoints. Read them, and read the configs and scripts that the sources
   use.
4. **Write the plan** in the shape in [Plan shape](#plan-shape), and save it
   as `<id>_<topic>_plan.md`. `<id>` is the main ticket ID, or a short slug
   when there is no ticket. Put it in the project's plans folder if one
   exists, or else at the repository root. The plan ends with a Questions
   section. A plan is a local working file, not a document (see
   [Plans are not documents](#plans-are-not-documents)).
5. **The user answers the questions in the file**, one at a time. Move each
   answer into the section it changes, then delete the question (see
   [Questions](#8-questions--draft-only)).
6. **Iterate on the plan.** The user will push back on sections that are
   too long, that repeat, or that disagree with each other. This often
   changes the stages themselves, not only the wording.
7. **Review the plan in a fresh context**, once, before the first stage
   runs. Start one subagent with only the plan file and the repository, and
   ask it to review the plan as a staff engineer would. It reports
   contradictions between sections, missing preconditions, a **Green:** line
   that cannot be checked, and a stage that depends on a later stage. A
   reviewer without the drafting conversation sees what the author context
   misses. Fold its findings in as in step 5, and tell the user what changed.
8. **Execute stage by stage.** The user may say "phase" for a stage. The two
   words mean the same thing. Each stage ends on its **Green:** check.
   - "Execute stage N" allows one commit for that stage, after its green
     run. Follow-up fixes to the stage stay uncommitted until the user asks.
   - Steps 4 to 7 are discussion. Commit nothing during them.
   - **Keep the context clean.** After a failed attempt, rewind and
     re-prompt with what you learned. Do not pile corrections on top of
     the failure. Before a compaction, give it a focus
     (`/compact keep stage 3 and the open failure, drop the exploration`).
     Use a subagent for searches where only the conclusion matters.
   - **A new stage can start in a new session.** The plan is written to run
     from a cold start, so a long stage does not have to carry the context of
     the previous one.
9. **Retire the plan when the work is done.** Move everything that must
   survive into the spec, the design doc, or the project's guidelines. Then
   ask the user before you delete the plan.

The plan must work from a cold start. A new session with only the plan and
the repository must be able to continue the work.

## Plan shape

The plan has these sections, in this order. Each section starts with its
job: the question it answers for the reader.

### 1. Title and goal

`# <id>: <goal>`, then one paragraph: what changes, for whom, and how a
reader knows it is done.

### 2. Work items

Job: make the mapping from work items to stages clear before any prose.

- **With tickets** — a linked `Ticket | Type | Title` table. List related
  tickets that already exist too, marked as existing.
- **Without tickets** — a table of `Task | Title`, with stable IDs (`T1`,
  `T2`, …). Stages refer to these IDs the same way they refer to tickets.

> Example:
>
> | Ticket | Type | Title |
> |---|---|---|
> | [#41](…) | Feature | Share links that hide prices from viewers |
> | [#37](…) | Feature (existing) | Calendar feed token |

### 3. Where we are

Job: show a reader who has no context what already works, what does not, and
what the new work can reuse.

Four parts:

1. **State matrix.** Put the features or variants on one axis, and the
   layers or implementations on the other. Each cell says `works` (and names
   what makes it work), `stub`, `empty shell`, or `new`. A cell that does not
   work names its work item.
2. **What passes today.** The exact tests or runs that pass before any change,
   and the command that runs them. Every stage must keep them passing.
3. **Why it is not a simple change.** A numbered list of the obstacles, each
   one tied to a work item.
4. **What to build on.** Existing functions, types, config keys, routes,
   components, files, and earlier work that solves a similar problem.

> Example (obstacle): "**A share link shows everything.** `GET /share/:token`
> looks up one token and returns the whole trip, prices included. Nothing
> limits what a viewer sees. → #41."
>
> Example (build on): "The server's budget rollup is the only place costs are
> totalled. A viewer response drops the rollup's price fields. It does not
> compute totals of its own."

### 4. Staging

Job: the part of the plan that gets executed. Stages run in order, and you
can check each one on its own.

**Opening lines.** Before the first stage, state what is true for all of
them:

- Where each stage's green run happens.
- Which tests that already exist will cover the new work. Extending them is
  better than adding new ones, so say if there are no new test files.
- How a run picks a variant (a config field, a flag, a feature flag). Every
  stage uses that one way.
- Which doc files must be updated before a stage counts as done.

**Each stage** — `### Stage N — <work item>: <what it enables>`:

- Put groundwork and refactors first, before the features that need them.
  When the order matters, give the reason in one line.
- When a stage both refactors working code and adds new code, split it into
  **Step Na** and **Step Nb**, each with a green run. Then a failure belongs
  to one of them. Say what each step does.
- Each bullet names a real thing: a file, function, type, field, route,
  component, or config key. Not a vague intention.
- **List the preconditions.** Say what must already be true before the check
  runs, even if an earlier stage said it too.
- Write each design decision in the stage it affects, with its reason in one
  line.
- Finish with **Green:** followed by the exact result that a reader can see.

> Example: "**Green:** `npm run check` passes, and the share endpoint test
> shows that a viewer link returns the trip with no price field in any
> activity."

### 5. Verification

Job: make "is it green?" a mechanical check, not a judgement call.

- **Environment.** Where the checks run: a browser, a container, a service, a
  simulator, or a board. List the traps: settings that drift, environments
  that give wrong results for this work, extra arguments a run needs, and
  limits on parallel runs.
- **Commands.** List the build command, the quick command for one stage,
  and the full command that runs everything. Say how to choose a variant
  without editing a config file.
- **What to check per run.** A `Check | Pattern | Applies to` table, run
  against a named log or report. One row covers the error output that must
  *not* appear.
- **What a clean exit does not prove.** Name the check that would catch a
  test that did no work. Name the check that is the *only* proof for a case
  with nothing to compare.
- **Every iteration, not only the last.** A final check shows that the last
  operation worked. Where a run repeats N times, name the count that must
  equal N.
- **Keep the checks in step with the code.** If a change edits output that a
  check searches for, the same change updates the check.
- **Do not blame flakiness** until runs one at a time show it.

Add the checks that fit the domain:

| Domain | Typical checks |
|---|---|
| Firmware, drivers, hardware | Build for the target. Run on a simulator, an FPGA, or a board. Check counters, status registers, and the test log. Check that fault and assert messages do not appear. |
| Libraries and host tools | Unit tests. Integration tests against a real or recorded device or service. Sanitizers (ASan, UBSan) for C and C++. Type checks for Python. |
| Services and back ends | Unit and integration tests. A local run with real requests. Schema migrations on a fresh database and on an upgraded one. |
| Web front ends | Type check, lint, and unit tests. Run the app in a browser and exercise the changed flow. An accessibility check on changed views. |
| Debug and validation scripts | Run against a known-good case and a known-bad case. The bad case must fail. |

> Example row: `| Prices hidden | no "cost" key in the viewer response | public link |`
>
> Example: "A viewer response has no price to compare, so the absent-field
> check **is** the whole proof. A test that passes on a trip with no
> activities proves nothing. Seed the test trip with priced activities."

### 6. Files to reference

Job: let a new session start work without exploring the tree again.

Group by layer, in the order the work touches them: database and schema,
shared types, server, front end, scripts, tests, docs, and conventions. For
firmware work, the layers are firmware, shared interfaces, drivers, and host
tools. One line per entry: the path, then the symbols or the role that make
it matter.

> Example: "`server/routes/share.ts` — `GET /share/:token`, token lookup,
> response shape"

### 7. Coding practices

Job: say how to write the code while you execute the stages.

- Name the `coding-standards` skill files that apply, from the kinds of file
  the plan touches. Always `general.md`. Then, for example, `web.md`, or
  `c-cpp.md` and `firmware.md`, or `python.md` and `validation.md`.
- Do not copy those rules into the plan. Add only rules that are specific to
  this plan, such as a naming scheme for new tokens, or a file the plan must
  not touch.
- If `coding-standards` is not installed, write the general rules out in
  this section.

### 8. Questions — draft only

Job: collect the decisions that only the user can make, get them answered in
the plan file, and move each answer into the body. Only a draft has this
section.

1. **Draft.** The last section of the plan is `## Questions`. Number the
   questions in the order of the stages they affect, so the user can answer
   from the top.
2. **Answer.** The user writes each answer under its question, one at a time.
3. **Fold.** Move each answer into the section it affects, written as a
   decision (not "the user said"). Delete the question. When the last
   question goes, the section goes too.

A question must change the work. These earn a question:

- a choice between designs that are materially different
- a scope decision: is the deliverable X, or X and Y
- a fact about hardware, an external system, or intent that the code does
  not show

These do not earn a question: facts in the source, choices with an obvious
default (state your pick and move on), and matters of taste.

Write each question so that one word can answer it: state the choice, the
trade-off in one clause, and your own preference.

> Example: "**Link scope** — one share token with a hide-prices flag, or
> separate public and private tokens? One token is simpler, but revoking it
> ends both views. I prefer separate tokens."

Folding is more than pasting. An answer often invalidates something earlier
in the plan. Re-order stages if the answer changes a dependency. Update the
**Green:** lines it touches. Delete each concept it retires. When an answer
contradicts an earlier assumption, say so plainly: that correction is the
useful part.

## Plans are not documents

A plan is a local working file. It is finished and deleted. The spec and the
design docs are not.

- **Ignore plans in git.** Add `*_plan.md` to `.gitignore`, with the user's
  approval, if it is not there. Ignoring the pattern, not only leaving the
  file unadded, stops a `git add -A` from committing a stale plan.
- **Nothing tracked refers to a plan.** No doc, comment, or commit message
  links to a `*_plan.md`. A reference to a file that no longer exists is
  worse than no reference.
- **A plan is not a backup.** A plan that outlives its work starts to
  contradict the spec. Anything in it that must survive moves into the spec
  or the design doc before the plan is deleted.
- **A plan does not refer to files that do not exist.** Name only files that
  exist, or that a stage in the plan creates.

## Conventions

Apply these while you draft, and again on the final pass.

- **Put each decision in the stage it changes.** A general "decisions"
  section collects everything and helps nobody. Keep one only for three or
  more items that apply to every stage.
- **Open questions mean a draft.** The finished plan has no Questions
  section.
- **Say "do not" only for real temptations.** Warn against X only when
  something in the plan makes X look like the right move.
- **Decide the details.** Pick the interface, the value, and the name instead
  of listing options. Write the exact output that the verification section
  looks for, so the plan and the check match.
- **Mark untested assumptions, and tell the implementer to stop.** If a
  stage relies on untested behaviour, say what it assumes. If the
  assumption turns out false, the implementer must **stop and ask**, not redesign.
  > Example: "The exchange-rate provider quotes each rate per one unit of the
  > trip's base currency. If it quotes the inverse, **stop and ask**."
- **Write down the invariant the design relies on.** Readers do not guess
  the property that everything quietly depends on.
  > Example: "Migrations run on every start. They are the only thing that
  > changes the schema, so a fresh install and an upgraded one have the same
  > tables."
- **Reuse first.** Use the helpers, fixtures, tests, and scripts that
  exist before you add new ones. If several stages need the same check,
  write one shared helper.
- **Give each reason once**, in the place that needs it, not in every
  section.
- **Read the whole plan again at the end.** Editing creates contradictions,
  so search for them. Each **Green:** line needs a matching row in the
  verification table. Nothing that an edit deleted may still appear in a
  later stage.

### Style

- Markdown, wrapped at about 80 columns.
- Use tables for matrices and mappings, and bullets for stage work. Use
  prose only for reasoning that does not fit in a bullet.
- Code font for every file, function, type, config key, route, and command.
- Bold the labels a reader scans for: **Green:**, **Step Na**, and the names
  of obstacles.

### Prose

Write every sentence of the plan with the `asd-ste100` skill, in
STE-flavored mode. If that skill is not installed, apply at least these
rules:

- one term for one concept, defined once
- at most 20 words in an instruction and 25 in a description
- active voice and present tense, with the actor named by role
- the condition before the instruction
- no Latin abbreviations, no semicolons, and no clutter words
- headings in sentence case
