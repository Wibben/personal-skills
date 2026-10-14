---
name: config-cleanup
description: "Audit and clean up the user's Claude Code directory (~/.claude and ~/.claude.json): stale lock files, old shell snapshots, the skills trash, config entries for deleted folders, one-off permission rules, a default model that contradicts CLAUDE.md, outdated model names and prices in CLAUDE.md, and memory hygiene. Reports first, edits config only with approval, and never deletes files itself. Use when the user asks to clean up, tidy, audit, or review their ~/.claude, Claude Code settings, or memories."
---

# Claude Code cleanup

A script takes the inventory. You add the judgment that a script cannot
make. Keep the run cheap: read only the files that the inventory points at.

## Rules

- **Report first.** Change nothing until the user approves the plan.
- **Never delete files yourself.** Give the user one `!` command to run.
  Auto mode blocks irreversible deletion, and the user must see the list
  first.
- **Edit config only with approval**, with the Edit tool, one change at a
  time. Use `inventory.py --prune-projects` for `~/.claude.json`, because
  Claude Code writes that file constantly and a hand edit can collide with
  it.
- **Never touch** session transcripts (`projects/*/*.jsonl`), `file-history/`,
  `backups/`, `history.jsonl`, `sessions/`, `session-env/`, `plugins/`, or
  `skills/synced/`. Claude Code prunes or manages these itself.
- **Do not delete a memory** unless the user agrees. A memory that looks
  stale can hold the only record of a decision.

## Process

1. **Take the inventory.**

   ```bash
   python3 -I <skill-dir>/scripts/inventory.py
   ```

   It reports files to delete and config entries for missing folders. It
   also reports one-off permission rules, the default model, memory links
   and indexes, and the `CLAUDE.md` lines that name a model or a price.

2. **Add judgment** on these points only:
   - **Settings against `CLAUDE.md`.** Read `~/.claude/CLAUDE.md` and
     `~/.claude/settings.json`. Flag each setting that contradicts a rule.
     For example, a default model with `[1m]` while `CLAUDE.md` says to avoid
     1M context.
   - **Current models and prices.** For the `CLAUDE.md` lines the inventory
     lists, get current model names and prices from the `claude-api` skill.
     Never use prices from memory.
   - **Memories.** Read each `MEMORY.md` index, not every memory file. Open a
     memory file only when its index line suggests one of these:
     - it is stale, for example a finished task or a dated session note
     - it duplicates another memory
     - an installed skill already covers it
   - **Permissions.** With `defaultMode: bypassPermissions`, allow rules have
     no effect. Say so, and still offer to delete the one-off rules.
   - **Rules that a setting could enforce.** Prose in `CLAUDE.md` is a
     request. Claude Code enforces a setting or a hook. Flag each rule that a
     setting covers, for example a rule about commit trailers, which the
     `attribution` setting controls. Check the exact setting key with the
     `claude-code-guide` agent before you propose it. Remove the prose rule
     only after the setting is in place.
   - **Size and scope.** If the inventory flags `CLAUDE.md` as over 200
     lines, suggest sections to move. A section can move into a skill, which
     loads on demand, or into a rule file with `paths:`, which loads only for
     matching files. For each rule file without `paths:`, ask whether it
     applies to every session.
   - **Outdated instructions in `CLAUDE.md`** (text written for older
     models, rules that contradict each other): suggest
     `/claude-api prompt-audit` instead of auditing it here.
   - **Frequent permission prompts**: suggest `/fewer-permission-prompts`.
   - **Installed skills**: suggest `/skill-doctor`, which finds skills that
     never fire and shows what each one costs in context.

3. **Report** in three groups:
   - **Delete** — the `!` command from the inventory, with one line per kind
     of file.
   - **Change** — each proposed edit: the file, the old value, the new value,
     and the reason.
   - **Leave** — what you checked and are not changing, and why.

4. **Apply the approved changes.** Run `--prune-projects` if the user
   approved it. Make the other edits with the Edit tool. Then run the
   inventory again and check that the approved items are gone.

5. **Say what needs a new session.** A changed default model or a changed
   `CLAUDE.md` takes effect in the next session.
