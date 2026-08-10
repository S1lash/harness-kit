#!/usr/bin/env bash
# Harness Kit installer — conversational, plain-language, cross-platform.
# Runs on macOS, Linux, and Git Bash on Windows. Bash 3.2-safe:
# no mapfile / declare -A / ${var^^} / sed -i portability traps / readlink -f.
# Non-trivial logic is delegated to python3 for portability — so python3 is a
# prerequisite on every platform, Git Bash included (install it first there).
#
# What it does: places this base where you want it, names it, records the
# language you want the agent to talk to you in, wires the canon into every
# AI agent you use so it's active from any folder, optionally sets up git,
# creates a sibling projects/ folder, then runs a quick health check.

set -u

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

say()  { printf '%s\n' "$1"; }
ask()  { # ask "Question" "default" -> echoes the answer (default on empty)
  _q="$1"; _def="${2:-}"
  if [ -n "$_def" ]; then
    printf '%s [%s]: ' "$_q" "$_def" >&2
  else
    printf '%s: ' "$_q" >&2
  fi
  IFS= read -r _ans
  if [ -z "$_ans" ]; then _ans="$_def"; fi
  printf '%s' "$_ans"
}
ask_yes() { # ask_yes "Question" "Y|N default" -> returns 0 for yes, 1 for no
  _q="$1"; _def="${2:-Y}"
  case "$_def" in Y|y) _hint="[Y/n]";; *) _hint="[y/N]";; esac
  printf '%s %s: ' "$_q" "$_hint" >&2
  IFS= read -r _a
  if [ -z "$_a" ]; then _a="$_def"; fi
  case "$_a" in Y|y|yes|Yes|YES) return 0;; *) return 1;; esac
}
fail() { say ""; say "STOP: $1"; exit 1; }

command -v python3 >/dev/null 2>&1 || fail "python3 is required and was not found. Install Python 3, then re-run this script."

# Absolute directory this script lives in (the source base), portable (no readlink -f).
SRC="$(cd "$(dirname "$0")" && pwd)"

# Portable managed-block upsert: keeps an idempotent block between markers.
# Re-running the installer replaces the block instead of appending a duplicate.
upsert_block() { # upsert_block <target_file> <marker_name> <content_file>
  python3 - "$1" "$2" "$3" <<'PY'
import os, sys
target, marker, content_file = sys.argv[1], sys.argv[2], sys.argv[3]
begin = "<!-- BEGIN %s -->" % marker
end   = "<!-- END %s -->" % marker
with open(content_file, "r", encoding="utf-8") as f:
    block = f.read().rstrip("\n")
managed = begin + "\n" + block + "\n" + end
old = ""
if os.path.exists(target):
    with open(target, "r", encoding="utf-8") as f:
        old = f.read()
if begin in old and end in old:
    pre  = old.split(begin, 1)[0].rstrip("\n")
    post = old.split(end, 1)[1].lstrip("\n")
    new = (pre + "\n\n" if pre else "") + managed + ("\n\n" + post if post else "\n")
else:
    new = (old.rstrip("\n") + "\n\n" if old.strip() else "") + managed + "\n"
d = os.path.dirname(os.path.abspath(target))
if d and not os.path.isdir(d):
    os.makedirs(d)
with open(target, "w", encoding="utf-8") as f:
    f.write(new)
PY
}

make_symlink() { # make_symlink <target> <link_path>
  _target="$1"; _link="$2"
  if [ -L "$_link" ]; then
    rm -f "$_link"
  elif [ -e "$_link" ]; then
    say "  note: $_link already exists and is not a link — leaving it, the @-imports below still work."
    return 0
  fi
  if ln -s "$_target" "$_link" 2>/dev/null; then
    say "  linked $_link -> $_target"
  else
    say "  note: could not create the symlink $_link (on Windows this can need admin rights)."
    say "        Not a problem — the canon is still wired via the entries written into your agent's global file."
  fi
}

HOME_DIR="${HOME:-$USERPROFILE}"

# ---------------------------------------------------------------------------
# 1. intro
# ---------------------------------------------------------------------------
say ""
say "==============================================================="
say " Harness Kit — setup"
say "==============================================================="
say ""
say "This folder is your BASE. Think of it as your AI agent's home:"
say "you'll launch your agent from here, and it keeps your operating"
say "principles, your knowledge, and your ongoing work in one place."
say ""
say "The generic canon (the rules/ and doctrine/ files) stays English"
say "and untouched — it's the shared standard. Only ONE file is yours"
say "to personalize: profile.md. This setup fills the first bits of it"
say "for you and wires everything up. A few plain questions follow."
say ""

# ---------------------------------------------------------------------------
# 2. where + name
# ---------------------------------------------------------------------------
ROOT="$(ask "Where should your base live? (a folder that will contain it)" "$HOME_DIR")"
ROOT="$(python3 -c 'import os,sys; print(os.path.abspath(os.path.expanduser(sys.argv[1])))' "$ROOT")"
NAME="$(ask "What should the base folder be called?" "harness")"
DEST="$ROOT/$NAME"
PROJECTS="$ROOT/projects"

say ""
say "Plan:"
say "  base     -> $DEST"
say "  projects -> $PROJECTS   (created beside the base, for the things you'll build)"
say ""

INPLACE=0
if [ "$DEST" = "$SRC" ]; then
  INPLACE=1
  say "You're installing in place (the base stays right here)."
else
  if [ -e "$DEST" ]; then
    if ask_yes "  $DEST already exists. Copy the base into it anyway?" "N"; then :; else
      fail "Nothing changed. Re-run and pick a different name or location."
    fi
  fi
fi

# ---------------------------------------------------------------------------
# 3. place the base + create projects sibling
# ---------------------------------------------------------------------------
if [ "$INPLACE" -eq 0 ]; then
  say "Placing the base..."
  python3 - "$SRC" "$DEST" <<'PY'
import shutil, sys, os
src, dest = sys.argv[1], sys.argv[2]
ignore = shutil.ignore_patterns(".git", ".DS_Store", "__pycache__", "*.log", ".venv")
if os.path.isdir(dest):
    # merge copy into existing dir
    for name in os.listdir(src):
        if name in (".git", ".DS_Store", "__pycache__", ".venv"):
            continue
        s = os.path.join(src, name); d = os.path.join(dest, name)
        if os.path.isdir(s):
            shutil.copytree(s, d, ignore=ignore, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)
else:
    shutil.copytree(src, dest, ignore=ignore)
print("  copied base -> " + dest)
PY
fi

if [ ! -d "$PROJECTS" ]; then
  mkdir -p "$PROJECTS"
  say "  created $PROJECTS"
fi

PROFILE="$DEST/profile.md"
[ -f "$PROFILE" ] || fail "profile.md not found in the base at $PROFILE — the base looks incomplete."

# ---------------------------------------------------------------------------
# 4. language -> profile.md
# ---------------------------------------------------------------------------
say ""
say "Your agent talks to YOU in your language. The base content stays"
say "English (it's the shared standard, and code is always English), but"
say "the agent will converse, explain, and ask you things in whatever"
say "language you pick here."
LANG="$(ask "What language should the agent talk to you in?" "English")"

python3 - "$PROFILE" "$LANG" <<'PY'
import sys, re
path, lang = sys.argv[1], sys.argv[2]
with open(path, "r", encoding="utf-8") as f:
    txt = f.read()
line = "- **Language:** %s — the agent converses with you in this language; code, comments, and identifiers stay English." % lang
# Replace the placeholder Language bullet if present, else insert under the presentation section.
pat = re.compile(r"^- \*\*Language:\*\*.*$", re.M)
if pat.search(txt):
    txt = pat.sub(line, txt, count=1)
else:
    txt = txt.rstrip("\n") + "\n\n" + line + "\n"
with open(path, "w", encoding="utf-8") as f:
    f.write(txt)
print("  set Language: %s in profile.md" % lang)
PY

# ---------------------------------------------------------------------------
# 5. wire agents
# ---------------------------------------------------------------------------
say ""
say "Now let's connect your base to the AI agent(s) you use, so the canon"
say "is active from ANY folder — you never have to point the agent at it."
say ""

TMP_BLOCK="$(python3 -c 'import tempfile,sys; print(tempfile.mkstemp(suffix=".md")[1])')"
cleanup() { rm -f "$TMP_BLOCK" 2>/dev/null; }
trap cleanup EXIT

gen_rule_imports() { # emits one @<abs-path> line per rule file
  for f in "$DEST"/rules/*.md; do
    [ -e "$f" ] || continue
    printf '@%s\n' "$f"
  done
}

# ---- Claude Code -----------------------------------------------------------
CLAUDE_WIRED=0
if ask_yes "Do you use Claude Code?" "Y"; then
  CLAUDE_WIRED=1
  CLAUDE_DIR="$HOME_DIR/.claude"
  mkdir -p "$CLAUDE_DIR"
  make_symlink "$DEST/rules" "$CLAUDE_DIR/harness-kit-rules"
  {
    printf '## Harness Kit — global canon (managed by install.sh; do not edit between the markers)\n\n'
    printf '**HARNESS HOME:** `%s`\n' "$DEST"
    printf 'This is your operating base. `%s/knowledge/_index.md` (durable knowledge) and\n' "$DEST"
    printf '`%s/activities/_index.md` (ongoing work) are reachable from any working directory, every session.\n\n' "$DEST"
    printf 'Hot canon — loaded every session:\n'
    gen_rule_imports
    printf '@%s/profile.md\n' "$DEST"
    printf '\n'
    printf 'Full three-tier loading model: read `%s/CLAUDE.md`.\n' "$DEST"
    printf 'Converse in the language set in `%s/profile.md`; code, comments, and identifiers stay English.\n' "$DEST"
  } > "$TMP_BLOCK"
  upsert_block "$CLAUDE_DIR/CLAUDE.md" "HARNESS-KIT" "$TMP_BLOCK"
  say "  wired the canon into $CLAUDE_DIR/CLAUDE.md (active in every Claude Code session)."
fi

# ---- Codex -----------------------------------------------------------------
if ask_yes "Do you use Codex (OpenAI Codex CLI)?" "N"; then
  CODEX_DIR="$HOME_DIR/.codex"
  mkdir -p "$CODEX_DIR"
  {
    printf '## Harness Kit — global canon (managed by install.sh; do not edit between the markers)\n\n'
    printf 'Your operating base ("harness home") is: %s\n\n' "$DEST"
    printf 'At the start of every session, read `%s/AGENTS.md` and the canon files it\n' "$DEST"
    printf 'lists under `%s/rules/`. Follow that canon. Read `%s/knowledge/_index.md`\n' "$DEST" "$DEST"
    printf 'on demand for durable knowledge; consult `%s/activities/_index.md` only on the\n' "$DEST"
    printf 'narrow signals it names. Converse in the language set in `%s/profile.md`;\n' "$DEST"
    printf 'code, comments, and identifiers stay English.\n'
  } > "$TMP_BLOCK"
  upsert_block "$CODEX_DIR/AGENTS.md" "HARNESS-KIT" "$TMP_BLOCK"
  say "  wired the canon into $CODEX_DIR/AGENTS.md (Codex's global instructions)."
fi

# ---- Cursor ----------------------------------------------------------------
if ask_yes "Do you use Cursor?" "N"; then
  CURSOR_TXT="$DEST/cursor-user-rules.txt"
  {
    printf 'Your operating base ("harness home") is: %s\n' "$DEST"
    printf 'Read %s/AGENTS.md and the canon files it lists under %s/rules/ and follow that canon.\n' "$DEST" "$DEST"
    printf 'Read %s/knowledge/_index.md on demand; consult %s/activities/_index.md only on the narrow signals it names.\n' "$DEST" "$DEST"
    printf 'Converse in the language set in %s/profile.md; code, comments, and identifiers stay English.\n' "$DEST"
  } > "$CURSOR_TXT"
  say "  Cursor has no scriptable GLOBAL rules file, so I wrote a ready-to-paste snippet:"
  say "    $CURSOR_TXT"
  say "  MANUAL STEP: open Cursor -> Settings -> Rules -> 'User Rules', and paste that file's contents."
fi

# ---- other -----------------------------------------------------------------
if ask_yes "Do you use another AI agent I should point at this base?" "N"; then
  say "  For any other agent, wire its GLOBAL / always-on instructions to read:"
  say "    $DEST/AGENTS.md   (the cross-agent entry file — lists the canon in rules/)"
  say "  Point that agent's persistent-instructions setting at that file and it will pick up the canon."
fi

# ---------------------------------------------------------------------------
# 6. git
# ---------------------------------------------------------------------------
say ""
GIT_ON=0
if command -v git >/dev/null 2>&1 && ask_yes "Track your base with git? (recommended — it's a safety net for your own history)" "Y"; then
  GIT_ON=1
  if [ -d "$DEST/.git" ]; then
    if ask_yes "  This folder already has git history from the template. Start fresh with YOUR own history?" "Y"; then
      rm -rf "$DEST/.git"
      git -C "$DEST" init -q
      say "  started a fresh git repo for your base."
    else
      say "  kept the existing git history."
    fi
  else
    git -C "$DEST" init -q
    say "  git repo created for your base."
  fi
  git -C "$DEST" add -A 2>/dev/null || true

  if ask_yes "  Also auto-create a git repo inside each NEW project you build under projects/?" "Y"; then
    python3 - "$PROFILE" <<'PY'
import sys
path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    txt = f.read()
note = "- **Git:** track the base with git; auto-run `git init` inside each new project created under `projects/`."
if note not in txt:
    txt = txt.rstrip("\n") + "\n\n" + note + "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)
    print("  recorded 'auto-init new projects' in profile.md (the agent honors it).")
PY
  fi

  say ""
  say "  A REMOTE keeps a copy off your machine and syncs across your computers."
  if ask_yes "  Want your base on all your machines (add a remote now)?" "N"; then
    REMOTE_URL="$(ask "    Paste the git remote URL (e.g. git@github.com:you/your-base.git)" "")"
    if [ -n "$REMOTE_URL" ]; then
      git -C "$DEST" remote remove origin 2>/dev/null || true
      git -C "$DEST" remote add origin "$REMOTE_URL"
      say "    remote 'origin' set to $REMOTE_URL"
      say "    (nothing pushed yet — commit when you're ready, then: git -C \"$DEST\" push -u origin HEAD)"
    else
      say "    no URL given — skipped the remote. You can add one later."
    fi
  else
    say "  no remote — your base stays local only. You can add one anytime."
  fi
else
  say "Skipping git — nothing git-related will be touched until you ask."
fi

# ---------------------------------------------------------------------------
# 7. doctor — quick health check
# ---------------------------------------------------------------------------
say ""
say "Running a quick health check..."
DOC_OK=1
check() { # check "label" 0|1
  if [ "$2" -eq 0 ]; then say "  OK   $1"; else say "  MISS $1"; DOC_OK=0; fi
}

[ -d "$DEST/rules" ] && check "canon rules present" 0 || check "canon rules present" 1
[ -d "$DEST/doctrine" ] && check "doctrine present" 0 || check "doctrine present" 1
[ -f "$DEST/knowledge/_index.md" ] && check "knowledge index present" 0 || check "knowledge index present" 1
[ -f "$DEST/activities/_index.md" ] && check "activities index present" 0 || check "activities index present" 1
[ -f "$DEST/AGENTS.md" ] && check "cross-agent entry (AGENTS.md) present" 0 || check "cross-agent entry (AGENTS.md) present" 1
[ -f "$DEST/CLAUDE.md" ] && check "Claude entry (CLAUDE.md) present" 0 || check "Claude entry (CLAUDE.md) present" 1
[ -d "$PROJECTS" ] && check "projects/ folder beside the base" 0 || check "projects/ folder beside the base" 1

if grep -q "Language:" "$PROFILE" 2>/dev/null; then check "your language recorded in profile.md" 0; else check "your language recorded in profile.md" 1; fi

# Canon parity: every rule file is named in BOTH hand-maintained lists, so no rule is
# silently in force for one agent and absent for another (rules/multi-agent.md).
PARITY_GAP="$(python3 - "$DEST" <<'PY'
import os, sys
base = sys.argv[1]
rules_dir = os.path.join(base, "rules")
names = sorted(f for f in os.listdir(rules_dir) if f.endswith(".md")) if os.path.isdir(rules_dir) else []
gaps = []
for entry, path in (("CLAUDE.md", os.path.join(base, "CLAUDE.md")),
                    ("AGENTS.md", os.path.join(base, "AGENTS.md"))):
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        gaps.append("%s missing" % entry)
        continue
    for name in names:
        if name not in text:
            gaps.append("%s not listed in %s" % (name, entry))
print("; ".join(gaps))
PY
)"
if [ -z "$PARITY_GAP" ]; then
  check "canon parity (every rule listed for every agent)" 0
else
  say "  MISS canon parity: $PARITY_GAP"
  DOC_OK=0
fi

if [ "$CLAUDE_WIRED" -eq 1 ]; then
  if [ -f "$HOME_DIR/.claude/CLAUDE.md" ] && grep -q "BEGIN HARNESS-KIT" "$HOME_DIR/.claude/CLAUDE.md" 2>/dev/null; then
    check "Claude Code global wiring" 0
  else
    say "  MISS Claude Code global wiring"
    DOC_OK=0
  fi
fi

# ---------------------------------------------------------------------------
# 8. summary
# ---------------------------------------------------------------------------
say ""
say "==============================================================="
if [ "$DOC_OK" -eq 1 ]; then
  say " Done. Your base is ready."
else
  say " Done, with a couple of items to check above (marked MISS)."
fi
say "==============================================================="
say ""
say "Your base:      $DEST"
say "Your projects:  $PROJECTS"
say "Talks to you:   $LANG"
say ""
say "What this means in plain terms:"
say "  - Launch your AI agent from your base folder and just talk to it."
say "  - It already knows how you want it to work (the canon is wired in)."
say "  - You never manage folders — the agent files knowledge and work for you."
if [ "$GIT_ON" -eq 1 ]; then
  say "  - Your base is under git. Ask the agent to 'save my work' whenever you want a checkpoint."
fi
say ""
say "Personalize one file when you like: $PROFILE"
say ""
