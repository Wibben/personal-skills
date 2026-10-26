#!/usr/bin/env python3
"""Track and pull upstream changes for skills listed in the repo's manifest.json.

Sources that point at private files on this machine go in manifest.local.json,
which git ignores. The script reads both files and writes each source back to
the file it came from.

Commands:
  status [SKILL]                 compare each source with its recorded state
  diff SKILL [--source NAME]     show upstream changes since the recorded commit
  merge SKILL [--source NAME]    three-way merge upstream changes into vendored files
  record SKILL [--source NAME]   mark a source as synced at its current state
  review SKILL --model MODEL     record that a skill was reviewed for a model

Source kinds: "git" (a repository), "local" (a file on this machine, tracked
by its SHA-256, with a snapshot so diff can show changes), "web" (pages to re-read by hand), and "reference" (a book or
standard, nothing to pull). Only git sources in "vendored" mode can be merged.
merge writes conflict markers into a file it cannot merge cleanly. record
never runs on its own: run it after the user approves the merged result.

Usage: upstream.py [--repo DIR] COMMAND ...
"""

import argparse
import datetime
import difflib
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

CACHE = Path.home() / ".cache" / "personal-skills" / "upstream"
SNAPSHOTS = Path.home() / ".cache" / "personal-skills" / "snapshots"


class Upstream:
    def __init__(self):
        parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
        parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[4],
                            help="the skills repository (default: the one this script is in)")
        commands = parser.add_subparsers(dest="command", required=True)
        status = commands.add_parser("status")
        status.add_argument("skill", nargs="?")
        for name in ("diff", "merge", "record"):
            command = commands.add_parser(name)
            command.add_argument("skill")
            command.add_argument("--source", help="source name (default: every source of the skill)")
        review = commands.add_parser("review")
        review.add_argument("skill")
        review.add_argument("--model", required=True, help="model ID the skill was reviewed for")
        self.args = parser.parse_args()
        self.manifest_path = self.args.repo / "manifest.json"
        if not self.manifest_path.is_file():
            parser.error(f"no manifest.json in {self.args.repo}; pass --repo")
        self.manifest = json.loads(self.manifest_path.read_text())
        self.local_path = self.args.repo / "manifest.local.json"
        self.local = json.loads(self.local_path.read_text()) if self.local_path.is_file() else {"skills": {}}

    def run(self):
        getattr(self, "command_" + self.args.command)()

    def selected_sources(self):
        """Yield (skill, source) pairs that the command line selects."""
        skills = self.manifest["skills"]
        names = [self.args.skill] if self.args.skill else list(skills)
        for skill in names:
            if skill not in skills:
                sys.exit(f"unknown skill {skill!r}; known: {', '.join(skills)}")
            private = self.local["skills"].get(skill, {}).get("sources", [])
            for source in skills[skill]["sources"] + private:
                if getattr(self.args, "source", None) in (None, source["name"]):
                    yield skill, source

    def git(self, *args, cwd=None):
        result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            sys.exit(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
        return result.stdout

    def remote_head(self, source):
        output = self.git("ls-remote", source["repo"], source.get("ref", "HEAD"))
        return output.split()[0] if output else None

    def checkout(self, source):
        """Return a cached partial clone of the source, fetched to its latest state."""
        directory = CACHE / re.sub(r"[^A-Za-z0-9._-]+", "_", source["repo"].split("://")[-1])
        if not directory.is_dir():
            directory.parent.mkdir(parents=True, exist_ok=True)
            self.git("clone", "--quiet", "--filter=blob:none", "--no-checkout", source["repo"], str(directory))
        self.git("fetch", "--quiet", "origin", source.get("ref", "HEAD"), cwd=directory)
        return directory, self.git("rev-parse", "FETCH_HEAD", cwd=directory).strip()

    def local_hash(self, source):
        path = Path(source["path"]).expanduser()
        return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

    def command_status(self):
        for skill, source in self.selected_sources():
            label = f"{skill} <- {source['name']} ({source['kind']}, {source['mode']})"
            if source["kind"] == "git":
                head = self.remote_head(source)
                state = "up to date" if head == source["commit"] else \
                    f"BEHIND: recorded {source['commit'][:7]}, upstream {head[:7] if head else 'missing'}"
            elif source["kind"] == "local":
                current = self.local_hash(source)
                state = "source file missing" if current is None else \
                    "up to date" if current == source["sha256"] else "CHANGED since last sync"
            elif source["kind"] == "web":
                state = f"re-read by hand (last synced {source.get('synced', 'never')})"
            else:
                state = "static reference"
            print(f"{label}: {state}")
        for skill, entry in self.manifest["skills"].items():
            if not self.args.skill or skill == self.args.skill:
                review = entry.get("model_review", {})
                print(f"{skill}: last model review {review.get('model', 'never')} on {review.get('date', '-')}")

    def command_diff(self):
        for skill, source in self.selected_sources():
            print(f"=== {skill} <- {source['name']}")
            if source["kind"] == "local":
                self.diff_local(source)
                continue
            if source["kind"] != "git":
                print(f"{source['kind']} source: nothing to diff")
                continue
            directory, head = self.checkout(source)
            paths = list(source.get("files", {})) or source.get("paths", [])
            if head == source["commit"]:
                print("up to date")
                continue
            print(self.git("log", "--oneline", f"{source['commit']}..{head}", "--", *paths, cwd=directory))
            print(self.git("diff", f"{source['commit']}..{head}", "--", *paths, cwd=directory))
            added = self.git("diff", "--name-only", "--diff-filter=A", f"{source['commit']}..{head}", cwd=directory)
            if added.strip():
                print("Files added upstream (not tracked by the manifest):\n" + added)

    def diff_local(self, source):
        """Show a local source's changes against the snapshot taken when it was recorded."""
        path = Path(source["path"]).expanduser()
        snapshot = SNAPSHOTS / source["sha256"]
        if not path.is_file():
            print(f"{source['path']}: source file missing")
        elif self.local_hash(source) == source["sha256"]:
            print("up to date")
        elif not snapshot.is_file():
            print(f"{source['path']} changed, but no snapshot of the recorded version exists. "
                  f"Compare it by hand with {', '.join(source.get('local_files', []))}.")
        else:
            print("".join(difflib.unified_diff(snapshot.read_text().splitlines(True), path.read_text().splitlines(True),
                                               "recorded", source["path"])))

    def command_merge(self):
        for skill, source in self.selected_sources():
            if source["kind"] != "git" or source["mode"] != "vendored":
                print(f"{skill} <- {source['name']}: not a vendored git source; use diff and fold changes in by hand")
                continue
            directory, head = self.checkout(source)
            # update-skills itself lives in .claude/skills, the others in skills/.
            skill_dir = next((d for d in (self.args.repo / "skills" / skill, self.args.repo / ".claude" / "skills" / skill)
                              if d.is_dir()), self.args.repo / "skills" / skill)
            for upstream_path, local_path in source["files"].items():
                print(f"{skill}/{local_path}: {self.merge_file(directory, source['commit'], head, upstream_path, skill_dir / local_path)}")

    def merge_file(self, directory, base_commit, head, upstream_path, local):
        """Merge one file three ways: local edits, the recorded base, and upstream head."""
        theirs = self.show(directory, head, upstream_path)
        if theirs is None:
            return "DELETED upstream; local copy kept"
        base = self.show(directory, base_commit, upstream_path) or ""
        ours = local.read_text() if local.is_file() else ""
        if theirs == base:
            return "unchanged upstream"
        if ours == base:
            local.write_text(theirs)
            return "updated (no local edits)"
        work = CACHE / "merge"
        work.mkdir(parents=True, exist_ok=True)
        (work / "base").write_text(base)
        (work / "theirs").write_text(theirs)
        result = subprocess.run(["git", "merge-file", "-p", "-L", "local", "-L", "recorded upstream",
                                 "-L", "new upstream", str(local), str(work / "base"), str(work / "theirs")],
                                capture_output=True, text=True)
        local.write_text(result.stdout)
        return "merged cleanly" if result.returncode == 0 else f"CONFLICTS: {result.returncode}, resolve the markers"

    def show(self, directory, commit, path):
        result = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=directory, capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else None

    def command_record(self):
        today = datetime.date.today().isoformat()
        for skill, source in self.selected_sources():
            if source["kind"] == "git":
                source["commit"] = self.remote_head(source)
            elif source["kind"] == "local":
                source["sha256"] = self.local_hash(source)
                if source["sha256"]:
                    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
                    (SNAPSHOTS / source["sha256"]).write_bytes(Path(source["path"]).expanduser().read_bytes())
            elif source["kind"] != "web":
                continue
            source["synced"] = today
            print(f"{skill} <- {source['name']}: recorded as synced on {today}")
        self.save()

    def command_review(self):
        entry = self.manifest["skills"].get(self.args.skill)
        if entry is None:
            sys.exit(f"unknown skill {self.args.skill!r}")
        entry["model_review"] = {"model": self.args.model, "date": datetime.date.today().isoformat()}
        print(f"{self.args.skill}: reviewed for {self.args.model}")
        self.save()

    def save(self):
        self.manifest_path.write_text(json.dumps(self.manifest, indent=2) + "\n")
        if self.local["skills"]:
            self.local_path.write_text(json.dumps(self.local, indent=2) + "\n")


if __name__ == "__main__":
    Upstream().run()
