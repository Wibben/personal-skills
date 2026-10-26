# setup-session

A plugin that sets up each Claude Code session the same way on every
machine. Claude.ai syncs uploaded skills to every machine, but not rules,
and not skills that you only installed locally. This plugin fills both
gaps.

## What it does at startup

A `SessionStart` hook runs `hooks/setup_session.py`:

1. **Gets the skills repository.** It clones
   https://github.com/Wibben/personal-skills into the plugin's data folder,
   and refreshes the clone at most once a day.
2. **Makes every skill available.** For each skill in `skills/`:

   | Where the skill is | What the hook does |
   |---|---|
   | claude.ai (`~/.claude/skills/synced/`) | Nothing. If the copy differs from the repository, it warns: upload the new version |
   | `~/.claude/skills/` or the project's `.claude/skills/` | Nothing |
   | Nowhere | Links it into `~/.claude/skills/` from the clone, so later updates arrive with the daily refresh |

   It removes a link it made when claude.ai starts to supply that skill,
   or when the skill leaves the repository. It never touches a skill that
   it did not install.
3. **Keeps the rules.** Each file in `rules/` becomes
   `~/.claude/rules/setup-session-<name>.md`, which Claude Code loads in
   every session. A footer holds a hash, so the hook can tell a hand edit
   and leaves that file alone. The rules come from the clone, so a rule
   change reaches every machine without a new plugin upload.
4. **Enforces the required settings.** It merges `required-settings.json`
   into `~/.claude/settings.json` at every startup. A list, such as
   `permissions.ask`, gets the entries that are missing. Any other value is
   overwritten. Your other settings stay. If you remove a required entry by
   hand, the next session adds it again. To change a required setting, edit
   `required-settings.json` in the repository.

When it installs a skill, the hook asks Claude Code to re-scan skills
(`reloadSkills`), so the skill works in the same session. When it changes a
rule, it adds the new rule text to the session too. The hook needs `git` and
`python3`. It never fails the session: problems show as one warning line.

## Rules

- `rules/skills.md` tells Claude when to load each skill. For example, load
  `asd-ste100` before the first reply and before any technical writing, and
  load `coding-standards` before code changes and commits. When you add a
  skill to the repository, add it to that table too.
- `rules/git.md`: never push without explicit permission, and commit only
  with permission. Blanket permission to commit for one session is allowed.

Rules come from this public repository, so keep internal names and private
details out of them.

## Required settings

`required-settings.json` makes these rules more than instructions:

- `permissions.ask` makes Claude Code ask before an action that reaches
  other people or loses work. The actions are a `git push`, any `gh`
  command, a `git reset --hard` or `git clean`, and an MCP tool whose name
  has `send`, `create`, `update`, `edit`, or `delete` in it. These patterns
  are broad on purpose, so some commands that only read also ask. They are not a security boundary: a
  script or a git alias that pushes does not match.
- `attribution` removes the Claude attribution from commits and pull
  requests.

## Commands

```bash
python3 -I hooks/setup_session.py --check    # report what it would change; no network, no writes
claude --plugin-dir plugins/setup-session    # try the plugin in a session
```

The hook finds its clone in `$CLAUDE_PLUGIN_DATA`, which Claude Code sets
only when it runs the hook. For `--check`, set it to the plugin's data
folder. For the plugin from claude.ai, that folder is
`~/.claude/plugins/data/setup-session-synced`.

Set `SETUP_SESSION_REPO` to use a different repository, for example a fork
or a local path for testing.
