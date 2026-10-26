#!/usr/bin/env python3
"""Set up a Claude Code session: make the personal skills available, and keep their rules.

Runs as a SessionStart hook at startup and on --resume. It has three jobs:

  skills  Every skill in the personal-skills repository must be available,
          from claude.ai (~/.claude/skills/synced/) or installed locally.
          The hook links a missing skill into ~/.claude/skills from a clone
          of the repository. It removes its own link when a claude.ai copy
          arrives. It reports a claude.ai copy that differs from the
          repository, because only a new upload can update that copy.
  rules   Each file in the repository's plugins/setup-session/rules/ folder
          is kept as ~/.claude/rules/setup-session-<name>.md. The hook leaves
          a rule file that was edited by hand, and reports it.
  settings  Each value in required-settings.json is merged into
          ~/.claude/settings.json at every session start. A list gets the
          missing entries. Any other value is overwritten. Other settings
          stay.

The clone is in $CLAUDE_PLUGIN_DATA and is refreshed at most once a day.
Rules and settings come from the clone, so a change reaches every machine
without a new plugin upload. The hook never fails the session: problems become
warnings.

Usage: setup_session.py [--check]   (--check reports, and changes nothing)
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

NAME = "setup-session"
REPO = os.environ.get("SETUP_SESSION_REPO", "https://github.com/Wibben/personal-skills.git")
REFRESH_S = 24 * 3600
GIT_TIMEOUT_S = 40
FOOTER = re.compile(rf"\n<!-- {NAME} sha256=(?P<hash>[0-9a-f]+)[^>]*-->\n?\Z")


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def git(*args):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    try:
        subprocess.run(["git", *map(str, args)], check=True, capture_output=True, text=True,
                       timeout=GIT_TIMEOUT_S, env=env)
    except subprocess.CalledProcessError as error:
        lines = (error.stderr or "").strip().splitlines()
        raise OSError(lines[-1] if lines else f"git {args[0]} failed") from None
    except subprocess.TimeoutExpired:
        raise OSError(f"git {args[0]} took longer than {GIT_TIMEOUT_S} s") from None


def refresh(clone):
    """Clone the repository, or update the clone if it is older than a day."""
    stamp = clone.with_name(clone.name + ".fetched")
    if (clone / ".git").is_dir():
        if stamp.exists() and time.time() - stamp.stat().st_mtime < REFRESH_S:
            return
        git("-C", clone, "fetch", "--quiet", "--depth", "1", "origin", "HEAD")
        git("-C", clone, "reset", "--quiet", "--hard", "FETCH_HEAD")
    else:
        # Clone beside the target, then move it, so a failed clone leaves nothing behind.
        partial = clone.with_name(clone.name + ".partial")
        shutil.rmtree(partial, ignore_errors=True)
        shutil.rmtree(clone, ignore_errors=True)
        clone.parent.mkdir(parents=True, exist_ok=True)
        git("clone", "--quiet", "--depth", "1", REPO, partial)
        os.replace(partial, clone)
    stamp.touch()


def skill_files(root):
    return {p.relative_to(root): p for p in root.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts
            and not any(part.startswith(".") for part in p.relative_to(root).parts)}


def same_skill(a, b):
    """True when two skill folders hold the same files, byte for byte."""
    files_a, files_b = skill_files(a), skill_files(b)
    return files_a.keys() == files_b.keys() and all(files_a[k].read_bytes() == files_b[k].read_bytes() for k in files_a)


def sync_skills(config, clone, project, write):
    """Return (changes, warnings)."""
    changes, warnings = [], []
    user_dir, source_dir = config / "skills", clone / "skills"
    names = sorted(d.name for d in source_dir.iterdir() if (d / "SKILL.md").is_file())
    for name in names:
        source, local = source_dir / name, user_dir / name
        ours = local.is_symlink() and local.resolve() == source.resolve()
        synced = [d for d in (user_dir / "synced").glob(f"*/{name}") if (d / "SKILL.md").is_file()]
        if synced:
            if ours:
                if write:
                    local.unlink()
                changes.append(f"removed the local link for {name}, because claude.ai now has it")
            if not any(same_skill(copy, source) for copy in synced):
                warnings.append(f"the claude.ai copy of {name} differs from the repository: upload the new version")
            continue
        if ours or (local / "SKILL.md").is_file() or (project / ".claude" / "skills" / name / "SKILL.md").is_file():
            continue
        if local.is_symlink() or local.exists():
            warnings.append(f"{local} exists but holds no SKILL.md, so {name} was not installed")
            continue
        if write:
            user_dir.mkdir(parents=True, exist_ok=True)
            local.symlink_to(source)
        changes.append(f"installed {name}")
    # Remove links of ours whose skill has left the repository.
    for link in (user_dir.iterdir() if user_dir.is_dir() else []):
        if link.is_symlink() and Path(os.readlink(link)).parent == source_dir and link.name not in names:
            if write:
                link.unlink()
            changes.append(f"removed {link.name}, because it is no longer in the repository")
    return changes, warnings


def sync_rules(config, rules_dir, write):
    """Return (changes, warnings, the text of the rules that changed)."""
    changes, warnings, changed = [], [], []
    target_dir = config / "rules"
    wanted = {f"{NAME}-{f.stem}.md": f.read_text().rstrip("\n") + "\n" for f in sorted(rules_dir.glob("*.md"))}
    present = {p.name: p for p in target_dir.glob(f"{NAME}-*.md")} if target_dir.is_dir() else {}

    def unchanged_by_hand(path):
        text = path.read_text()
        match = FOOTER.search(text)
        return match and digest(text[:match.start()]) == match["hash"], match and match["hash"]

    for name, body in wanted.items():
        path = target_dir / name
        if name in present:
            clean, recorded = unchanged_by_hand(path)
            if not clean:
                warnings.append(f"{path} was edited by hand, so it was not updated: move the edit into the repository")
                continue
            if recorded == digest(body):
                continue
        if write:
            target_dir.mkdir(parents=True, exist_ok=True)
            footer = f"<!-- {NAME} sha256={digest(body)} (managed: edit the rules in the personal-skills repository) -->\n"
            tmp = path.with_name(path.name + ".tmp")
            tmp.write_text(body + "\n" + footer)
            os.replace(tmp, path)
        changes.append(f"{'updated' if name in present else 'added'} the rule {name}")
        changed.append(body)
    for name, path in present.items():
        if name not in wanted:
            if unchanged_by_hand(path)[0]:
                if write:
                    path.unlink()
                changes.append(f"removed the rule {name}")
            else:
                warnings.append(f"{path} is no longer in the repository but was edited by hand, so it was kept")
    return changes, warnings, changed


def merge(current, required, prefix=""):
    """Merge required into current, in place. Return a description of each change."""
    changes = []
    for key, value in required.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            if not isinstance(current.get(key), dict):
                current[key] = {}
            changes += merge(current[key], value, f"{name}.")
        elif isinstance(value, list):
            if not isinstance(current.get(key), list):
                current[key] = []
            missing = [entry for entry in value if entry not in current[key]]
            current[key] += missing
            changes += [f"added {json.dumps(entry)} to {name}" for entry in missing]
        elif current.get(key) != value:
            current[key] = value
            changes.append(f"set {name} to {json.dumps(value)}")
    return changes


def sync_settings(config, required_file, write):
    """Return (changes, warnings)."""
    # Resolve a symlink, so a settings.json kept in a dotfiles repository stays a link.
    path = (config / "settings.json").resolve()
    try:
        settings = json.loads(path.read_text()) if path.exists() else {}
    except ValueError:
        return [], [f"{path} is not valid JSON, so the required settings were not applied"]
    changes = merge(settings, json.loads(required_file.read_text()))
    if changes and write:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n")
        os.replace(tmp, path)
    return [f"{change} in settings.json" for change in changes], []


def run(check, project):
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    data = Path(os.environ.get("CLAUDE_PLUGIN_DATA") or Path.home() / ".cache" / NAME)
    plugin_root = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).resolve().parent.parent)
    clone = data / "personal-skills"
    changes, warnings, changed_rules, skills_changed = [], [], [], False
    if not check:
        try:
            refresh(clone)
        except OSError as error:
            fallback = "; using the copy on this machine" if (clone / "skills").is_dir() else ""
            warnings.append(f"could not update the skills repository ({error}){fallback}")
    if (clone / "skills").is_dir():
        more, warn = sync_skills(config, clone, project, write=not check)
        changes += more
        warnings += warn
        skills_changed = bool(more)
    else:
        warnings.append(f"no copy of {REPO} on this machine, so the skills were not checked")
    # Rules from the clone are newer than the plugin's own copy.
    rules_dir = next((d for d in (clone / "plugins" / NAME / "rules", plugin_root / "rules") if d.is_dir()), None)
    if rules_dir:
        more, warn, changed_rules = sync_rules(config, rules_dir, write=not check)
        changes += more
        warnings += warn
    required_file = next((f for f in (clone / "plugins" / NAME / "required-settings.json",
                                      plugin_root / "required-settings.json") if f.is_file()), None)
    if required_file:
        more, warn = sync_settings(config, required_file, write=not check)
        changes += more
        warnings += warn
    return changes, warnings, changed_rules, skills_changed


def main(argv):
    check = "--check" in argv
    try:
        hook_input = {} if check or sys.stdin.isatty() else json.loads(sys.stdin.read() or "{}")
    except ValueError:
        hook_input = {}
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or hook_input.get("cwd") or os.getcwd())
    try:
        changes, warnings, changed_rules, skills_changed = run(check, project)
    except OSError as error:
        changes, warnings, changed_rules, skills_changed = [], [f"setup failed: {error}"], [], False

    if check:
        print("\n".join([f"needed: {c}" for c in changes] + [f"warning: {w}" for w in warnings]) or "all set")
        return
    output = {}
    if changes or warnings:
        message = f"{NAME}: " + "; ".join(changes + warnings) + "."
        output["systemMessage"] = message.replace(str(Path.home()), "~")
    specific = {}
    if skills_changed:
        specific["reloadSkills"] = True
    if changed_rules:
        # Rules can load before this hook writes them, so give this session the new text too.
        specific["additionalContext"] = (f"The {NAME} hook changed these rules in ~/.claude/rules/. "
                                         "They apply from now on:\n\n" + "\n\n".join(changed_rules))
    if specific:
        output["hookSpecificOutput"] = {"hookEventName": "SessionStart", **specific}
    if output:
        print(json.dumps(output))


if __name__ == "__main__":
    main(sys.argv[1:])
