#!/usr/bin/env bash
# Install skills from this repository into a project or the user's ~/.claude.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skills_dir="$repo_dir/skills"

usage() {
    cat <<EOF
Usage: $(basename "$0") [--user | --project DIR] [--copy | --link] [--force] [SKILL ...]

Installs the named skills (default: all) into a skills directory.

Target (default: ./.claude/skills if ./.claude exists, else ~/.claude/skills):
  --user          ~/.claude/skills
  --project DIR   DIR/.claude/skills

Mode (default: --link for --user, --copy for a project):
  --link          symlink each skill to this repository, so 'git pull' updates it
  --copy          copy each skill, so the project does not depend on this path

  --force         replace a skill that already exists and differs
  --list          list the available skills and exit

Exit 2 if any skill already exists and differs, unless --force is given.
EOF
}

target="" mode="" force=0 names=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --user) target="$HOME/.claude/skills"; shift ;;
        --project) target="$(cd "$2" && pwd)/.claude/skills"; shift 2 ;;
        --copy) mode=copy; shift ;;
        --link) mode=link; shift ;;
        --force) force=1; shift ;;
        --list) ls "$skills_dir"; exit 0 ;;
        -h|--help) usage; exit 0 ;;
        -*) usage >&2; exit 1 ;;
        *) names+=("$1"); shift ;;
    esac
done

if [[ -z "$target" ]]; then
    if [[ -d "$PWD/.claude" && "$PWD" != "$HOME" && "$PWD" != "$repo_dir" ]]; then
        target="$PWD/.claude/skills"
    else
        target="$HOME/.claude/skills"
    fi
fi
if [[ -z "$mode" ]]; then
    [[ "$target" == "$HOME/.claude/skills" ]] && mode=link || mode=copy
fi
if [[ ${#names[@]} -eq 0 ]]; then
    for dir in "$skills_dir"/*/; do
        names+=("$(basename "$dir")")
    done
fi

mkdir -p "$target"
echo "Installing to $target ($mode)"
conflicts=0
for name in "${names[@]}"; do
    source="$skills_dir/$name"
    dest="$target/$name"
    if [[ ! -f "$source/SKILL.md" ]]; then
        echo "  $name: no such skill" >&2
        exit 1
    fi
    if [[ -L "$dest" && "$(readlink "$dest")" == "$source" ]]; then
        echo "  $name: already linked"
        continue
    fi
    if [[ -e "$dest" || -L "$dest" ]]; then
        if [[ ! -L "$dest" ]] && diff -rq "$source" "$dest" >/dev/null 2>&1; then
            [[ "$mode" == copy ]] && { echo "  $name: already up to date"; continue; }
        elif [[ $force -eq 0 ]]; then
            echo "  $name: CONFLICT, $dest exists and differs (compare it, then rerun with --force)"
            conflicts=1
            continue
        fi
        rm -rf "$dest"
    fi
    if [[ "$mode" == link ]]; then
        ln -s "$source" "$dest"
    else
        cp -R "$source" "$dest"
    fi
    echo "  $name: installed"
done
[[ $conflicts -eq 0 ]] || exit 2
