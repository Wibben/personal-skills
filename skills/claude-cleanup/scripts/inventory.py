#!/usr/bin/env python3
"""Inventory a Claude Code user directory for the claude-cleanup skill.

Reports, and never deletes:

  files     stale IDE locks, old shell snapshots, the skills trash folder,
            and failed-telemetry files older than 7 days
  config    ~/.claude.json project entries whose folder no longer exists
  perms     one-off permission rules (exact commands with literal paths)
  model     the default model, flagged when it selects a 1M context
  memory    broken [[links]], index lines that point to missing files, and
            memory files missing from MEMORY.md
  claudemd  model names and prices in CLAUDE.md, for a currency check, and
            a CLAUDE.md longer than 200 lines
  rules     rule files with no paths: front matter (they load every session)

The only change it can make is --prune-projects, which removes the config
entries for missing folders from ~/.claude.json. Everything else is a report.

Usage: inventory.py [--json] [--prune-projects] [--claude-dir DIR] [--config FILE]
"""

import argparse
import json
import os
import re
import shlex
import sys
import time
from pathlib import Path

TELEMETRY_MAX_AGE_S = 7 * 24 * 3600
CLAUDE_MD_MAX_LINES = 200
MODEL_MENTION = re.compile(r"\b(?:Opus|Sonnet|Haiku|Fable|Mythos)\s+\d+(?:\.\d+)?\b|\bclaude-[a-z]+-[\d-]+\b")
PRICE_MENTION = re.compile(r"\$\d+(?:\.\d+)?\s*/\s*M\b|\$\d+(?:\.\d+)?/MTok|per million", re.IGNORECASE)
LINK = re.compile(r"\[\[([^\]]+)\]\]")
INDEX_ENTRY = re.compile(r"\]\(([^)]+\.md)\)")


class Inventory:
    def __init__(self):
        parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
        parser.add_argument("--json", action="store_true", help="print the report as JSON")
        parser.add_argument("--prune-projects", action="store_true",
                            help="remove ~/.claude.json entries for folders that no longer exist")
        parser.add_argument("--claude-dir", type=Path, default=Path.home() / ".claude")
        parser.add_argument("--config", type=Path, default=Path.home() / ".claude.json")
        self.args = parser.parse_args()
        self.root = self.args.claude_dir
        self.report = {"delete": [], "config": [], "perms": [], "model": [], "memory": [],
                       "claudemd": [], "claudemd_lines": 0, "rules": [], "sizes": {}}

    def run(self):
        self.check_files()
        self.check_config()
        self.check_settings()
        self.check_memory()
        self.check_claude_md()
        self.check_rules()
        self.check_sizes()
        if self.args.json:
            print(json.dumps(self.report, indent=2))
        else:
            self.print_report()

    def check_files(self):
        """Collect files that Claude Code leaves behind and does not prune."""
        for lock in sorted((self.root / "ide").glob("*.lock")):
            if lock.stem.isdigit() and not self.pid_running(int(lock.stem)):
                self.report["delete"].append({"path": str(lock), "why": "IDE lock for a process that is not running"})
        snapshots = sorted((self.root / "shell-snapshots").glob("*.sh"), key=lambda p: p.stat().st_mtime)
        for snapshot in snapshots[:-1]:
            self.report["delete"].append({"path": str(snapshot), "why": "shell snapshot older than the newest one"})
        trash = self.root / "skills" / ".trash"
        if trash.is_dir():
            self.report["delete"].append({"path": str(trash), "why": "deleted-skills trash folder"})
        now = time.time()
        for event in (self.root / "telemetry").glob("1p_failed_events.*"):
            if now - event.stat().st_mtime > TELEMETRY_MAX_AGE_S:
                self.report["delete"].append({"path": str(event), "why": "failed-telemetry file older than 7 days"})

    def pid_running(self, pid):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def check_config(self):
        """Find project entries in ~/.claude.json whose folder is gone, and prune them on request."""
        if not self.args.config.is_file():
            return
        config = json.loads(self.args.config.read_text())
        missing = [path for path in config.get("projects", {}) if not os.path.isdir(path)]
        self.report["config"] = missing
        if missing and self.args.prune_projects:
            for path in missing:
                del config["projects"][path]
            mode = self.args.config.stat().st_mode & 0o777
            temporary = self.args.config.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(config, indent=2))
            os.chmod(temporary, mode)
            os.replace(temporary, self.args.config)
            self.report["config_pruned"] = True

    def check_settings(self):
        """Flag one-off permission rules and a default model with a 1M context."""
        for name in ("settings.json", "settings.local.json"):
            path = self.root / name
            if not path.is_file():
                continue
            settings = json.loads(path.read_text())
            rules = settings.get("permissions", {}).get("allow", [])
            seen = set()
            for rule in rules:
                if rule in seen:
                    self.report["perms"].append({"file": name, "rule": rule, "why": "duplicate"})
                seen.add(rule)
                why = self.one_off_reason(rule)
                if why:
                    self.report["perms"].append({"file": name, "rule": rule, "why": why})
            model = settings.get("model")
            if model:
                self.report["model"].append({"file": name, "model": model,
                                             "one_m_context": "[1m]" in model})

    def one_off_reason(self, rule):
        """Return why a Bash rule looks like a one-off, or None."""
        match = re.fullmatch(r"Bash\((.*)\)", rule, re.DOTALL)
        if not match or "*" in match.group(1):
            return None
        command = match.group(1)
        if re.search(r"(?:^|\s)['\"]?(?:/|~/)", command):
            return "exact command with a literal path"
        try:
            words = shlex.split(command)
        except ValueError:
            words = command.split()
        if len(words) >= 3 or any(c in command for c in "|\"'"):
            return "exact command with literal arguments"
        return None

    def check_memory(self):
        """Check each project's memory folder for broken links and index drift."""
        for memory in sorted((self.root / "projects").glob("*/memory")):
            files = {p.name: p.read_text(errors="replace") for p in memory.glob("*.md") if p.name != "MEMORY.md"}
            project = memory.parent.name
            if not files and not (memory / "MEMORY.md").exists():
                continue
            names = {self.slug(Path(name).stem) for name in files}
            for text in files.values():
                found = re.search(r"^name:\s*(.+)$", text, re.MULTILINE)
                if found:
                    names.add(self.slug(found.group(1).strip().strip("'\"")))
            for name, text in files.items():
                for link in LINK.findall(text):
                    if self.slug(link) not in names:
                        self.report["memory"].append({"project": project, "file": name,
                                                      "issue": f"[[{link}]] matches no memory "
                                                               "(fine if it marks a memory not yet written)"})
            index = memory / "MEMORY.md"
            listed = set(INDEX_ENTRY.findall(index.read_text())) if index.exists() else set()
            for entry in sorted(listed - set(files)):
                self.report["memory"].append({"project": project, "file": "MEMORY.md",
                                              "issue": f"index points to missing {entry}"})
            for name in sorted(set(files) - listed):
                self.report["memory"].append({"project": project, "file": name,
                                              "issue": "not listed in MEMORY.md"})

    def slug(self, name):
        return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

    def check_claude_md(self):
        """List lines in the user CLAUDE.md that name a model or a price."""
        path = self.root / "CLAUDE.md"
        if not path.is_file():
            return
        lines = path.read_text().splitlines()
        self.report["claudemd_lines"] = len(lines)
        for number, line in enumerate(lines, 1):
            if MODEL_MENTION.search(line) or PRICE_MENTION.search(line):
                self.report["claudemd"].append({"line": number, "text": line.strip()[:160]})

    def check_rules(self):
        """List rule files that load into every session because they have no paths: filter."""
        for rule in sorted((self.root / "rules").rglob("*.md")):
            text = rule.read_text(errors="replace")
            front = re.match(r"---\n(.*?)\n---", text, re.DOTALL)
            if not front or not re.search(r"^paths:", front.group(1), re.MULTILINE):
                self.report["rules"].append({"path": str(rule), "lines": len(text.splitlines())})

    def check_sizes(self):
        for child in sorted(self.root.iterdir()):
            if child.is_dir():
                total = sum(f.stat().st_size for f in child.rglob("*") if f.is_file() and not f.is_symlink())
                self.report["sizes"][child.name] = total

    def print_report(self):
        report = self.report
        print(f"# Claude Code cleanup inventory: {self.root}\n")
        print("## Files to delete (run the command below; this script deletes nothing)")
        for item in report["delete"]:
            print(f"- {item['path']} ({item['why']})")
        if report["delete"]:
            print("\n```\n! rm -rf " + " ".join(shlex.quote(i["path"]) for i in report["delete"]) + "\n```")
        else:
            print("- none")
        print(f"\n## Config entries for missing folders ({self.args.config})")
        for path in report["config"] or ["none"]:
            print(f"- {path}")
        if report.get("config_pruned"):
            print("- pruned")
        elif report["config"]:
            print("- prune with: inventory.py --prune-projects")
        print("\n## One-off permission rules")
        for item in report["perms"]:
            print(f"- {item['file']}: {item['rule']} ({item['why']})")
        if not report["perms"]:
            print("- none")
        print("\n## Default model")
        for item in report["model"] or [{"file": "", "model": "not set", "one_m_context": False}]:
            flag = "  <- 1M context: compare with CLAUDE.md cost rules" if item["one_m_context"] else ""
            print(f"- {item['file']}: {item['model']}{flag}")
        print("\n## Memory")
        for item in report["memory"] or [{"project": "", "file": "", "issue": "no issues"}]:
            print(f"- {item['project']}/{item['file']}: {item['issue']}")
        print("\n## CLAUDE.md lines that name a model or a price (check they are current)")
        for item in report["claudemd"] or [{"line": "-", "text": "none"}]:
            print(f"- {item['line']}: {item['text']}")
        size = report["claudemd_lines"]
        print(f"- CLAUDE.md length: {size} lines" + ("  <- over 200: move detail into skills or rules" if size > CLAUDE_MD_MAX_LINES else ""))
        print("\n## Rule files without a paths: filter (load into every session)")
        for item in report["rules"]:
            print(f"- {item['path']} ({item['lines']} lines)")
        if not report["rules"]:
            print("- none")
        print("\n## Sizes")
        for name, size in sorted(report["sizes"].items(), key=lambda kv: -kv[1]):
            if size >= 50_000:
                    print(f"- {name}: {size / 1e6:.1f} MB")


if __name__ == "__main__":
    Inventory().run()
