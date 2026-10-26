# Commits and pushes

- **Never push without explicit permission.** This includes `git push`, a
  force push, pushing tags, and opening or updating a pull request. Ask
  each time: permission for one push does not cover the next push.
  Permission to commit never includes permission to push.
- **Commit only with permission.** Before each `git commit`, find the user
  message that allows it.
  - The user can give blanket permission for the session, for example "you
    can commit as you go". It lasts until the session ends or the user
    takes it back. It does not cover pushes.
  - "Execute phase N" (or "stage N") allows one commit for that phase.
  - A green check, a finished stage, or "this is ready" is not permission.
- When there is no permission, leave the work uncommitted and say that it
  is ready to commit.
- For the commit-message format, load the `coding-standards` skill.
