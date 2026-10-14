# Personal skills

A collection of Claude Code skills. Each folder in `skills/` is one skill: a
`SKILL.md` file, plus the references and scripts that it loads when needed.

| Skill | Use it for | Works best with |
|---|---|---|
| [`asd-ste100`](skills/asd-ste100/SKILL.md) | Writing or rewriting technical prose: docs, plans, PR descriptions, commit messages, comments. ASD-STE100, Zinsser, Google developer style, and Canadian spelling. | — |
| [`coding-standards`](skills/coding-standards/SKILL.md) | Writing and reviewing code. General rules, plus files for C and C++, firmware, Python, web, shell, debug scripts, and validation scripts. Includes a code-review procedure. | `asd-ste100` |
| [`implementation-plan`](skills/implementation-plan/SKILL.md) | Writing a staged implementation plan, answering its questions, and executing it stage by stage. | `asd-ste100`, `coding-standards` |
| [`update-skills`](skills/update-skills/SKILL.md) | Pulling changes from the projects and files that skills came from, and reviewing skills for a newer model. Works on this repository only, so it is not installed. It loads from `.claude/skills/` when you work here. | — |
| [`claude-cleanup`](skills/claude-cleanup/SKILL.md) | Auditing and tidying `~/.claude`: stale files, dead config entries, one-off permissions, settings that contradict `CLAUDE.md`, outdated prices, and memory hygiene. Install with `--user`. | — |

The skills refer to each other by name, but each one works alone. Where a
skill depends on another one, it carries a short fallback.

## Importing the skills

### Instructions for Claude

If a user asks you to import skills from this repository, do this:

1. **Choose the target.**
   - If the current project has a `.claude/` directory, install into
     `<project>/.claude/skills/`.
   - Otherwise, install into `~/.claude/skills/`.
   - If the user names a target, use it.
   - `claude-cleanup` always goes into `~/.claude/skills/`
     (`install.sh --user claude-cleanup`), because it works on the user's
     own Claude Code directory, not on a project.
2. **Choose the skills.** Install all of them unless the user names some.
   `update-skills` is never installed: it works on this repository only.
   Tell the user if a skill they picked works best with one they did not.
3. **Run the installer** from the project directory:

   ```bash
   <this-repo>/install.sh                        # auto target, all skills
   <this-repo>/install.sh --user                 # force ~/.claude/skills
   <this-repo>/install.sh --project . coding-standards
   ```

   By default the installer symlinks into `~/.claude/skills`, so a
   `git pull` here updates the skills. It copies into a project, because a
   project's `.claude/` is often committed and a symlink to a personal path
   breaks for everyone else. `--copy` and `--link` override this.
4. **Resolve conflicts with the user.** Exit code 2 means a skill with the
   same name already exists and differs. Show the user the difference
   (`diff -r`), and rerun with `--force` only if they agree.
5. **Report** what was installed, where, and in which mode. If a new skill
   does not show up in the running session, start a new one.

### Manual install

Copy or symlink a folder from `skills/` into `~/.claude/skills/` or
`<project>/.claude/skills/`. Leave out `update-skills`. Run `./install.sh --help` for the options.

## Adding a skill

1. Create `skills/<name>/SKILL.md` with `name` and `description` in the
   front matter. The description decides when Claude loads the skill, so it
   names the tasks and the trigger phrases.
2. Keep `SKILL.md` short. Move detail that is needed only sometimes into
   `references/`, and deterministic checks into `scripts/` (standard library
   only, so the skill has no install step).
3. Add a row to the table in this README.
4. Add the skill to `manifest.json`, with a source for anything it takes
   from elsewhere (see `skills/update-skills/SKILL.md`, mode 3).

## Sources and updates

`manifest.json` records where each skill came from: GitHub projects, local
files, web pages, and books. It also records the model each skill was last
reviewed for. The `update-skills` skill uses it to pull upstream changes and
to review skills for a newer model. Sources that are private files on one
machine go in `manifest.local.json`, which git ignores.

## Licence

MIT, in `LICENSE`. Third-party content keeps its own licence. The sources and
their copyright holders are in `THIRD_PARTY_NOTICES.md`.
