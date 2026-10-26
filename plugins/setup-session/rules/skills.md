# Use the personal skills

The personal skills hold the user's standards. A skill's rules apply only
after the skill loads. Load the skill with the Skill tool before you start
the work, also for a small task. Load each skill once per session: it stays
in context after it loads. A skill name can have a prefix, for example
`anthropic-skills:asd-ste100`. A name with a prefix is the same skill.

| Skill | Load it before you |
|---|---|
| `asd-ste100` | write your first reply in a session, and before you write any technical English: replies, status reports, specs, plans, docs, READMEs, PR descriptions, commit messages, code comments, docstrings, error messages, and prompts for other agents. Use STE-flavoured mode for explanations and Strict mode for procedures |
| `coding-standards` | write, change, or review code, and before each commit. It sets when to commit and the format of the commit message |
| `implementation-plan` | write, refine, or execute an implementation plan |
| `colour-scheme` | choose colours for a web page, a UI, an artifact, or a slide deck |
| `config-cleanup` | audit or clean up `~/.claude` |

If a skill in this table is not available, tell the user once, and then
continue without it.
