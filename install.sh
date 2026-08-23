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
# keeps everything they build inside the base, then runs a quick health check.

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

# Two ways in. A fresh copy of the kit becomes a NEW base. A folder whose profile.md already
# carries a recorded language IS a base — the person is setting it up on another device, and
# nothing about their content or their history may be touched.
EXISTING_BASE=0
if [ -f "$SRC/profile.md" ] && grep -q 'the agent converses with you in this language' "$SRC/profile.md" 2>/dev/null; then
  EXISTING_BASE=1
fi

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
# 2. where + name  (or: recognise a base that already exists)
# ---------------------------------------------------------------------------
INPLACE=0
if [ "$EXISTING_BASE" -eq 1 ]; then
  DEST="$SRC"
  INPLACE=1
  say "This is already your base — I'll set this device up to use it and leave your"
  say "content and history alone."
  say ""
else
  ROOT="$(ask "Where should your base live? (a folder that will contain it)" "$HOME_DIR")"
  ROOT="$(python3 -c 'import os,sys; print(os.path.abspath(os.path.expanduser(sys.argv[1])))' "$ROOT")"
  NAME="$(ask "What should the base folder be called?" "harness")"
  DEST="$ROOT/$NAME"

  say ""
  say "Plan:"
  say "  base -> $DEST"
  say "  everything you build lives inside it, in $DEST/projects"
  say ""

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
fi

PROJECTS="$DEST/projects"

# ---------------------------------------------------------------------------
# 3. place the base
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

# An earlier layout kept projects beside the base, where a phone or a second machine can
# never see them. Bring them in.
LEGACY_PROJECTS="$(dirname "$DEST")/projects"
if [ -d "$LEGACY_PROJECTS" ] && [ "$LEGACY_PROJECTS" != "$PROJECTS" ]; then
  say ""
  say "  Found $LEGACY_PROJECTS outside your base. Anything there is invisible to your"
  say "  phone and to your other computers, because only the base travels."
  if ask_yes "  Move it inside the base?" "Y"; then
    python3 - "$LEGACY_PROJECTS" "$PROJECTS" <<'PY'
import os, shutil, sys
src, dest = sys.argv[1], sys.argv[2]
moved = []
for name in os.listdir(src):
    s, d = os.path.join(src, name), os.path.join(dest, name)
    if os.path.exists(d):
        print("  kept in place (already inside the base): " + name)
        continue
    shutil.move(s, d)
    moved.append(name)
if moved:
    print("  moved inside the base: " + ", ".join(moved))
if not os.listdir(src):
    os.rmdir(src)
    print("  removed the now-empty " + src)
PY
  fi
fi

PROFILE="$DEST/profile.md"
[ -f "$PROFILE" ] || fail "profile.md not found in the base at $PROFILE — the base looks incomplete."

# ---------------------------------------------------------------------------
# 4. language -> profile.md
# ---------------------------------------------------------------------------
say ""
if [ "$EXISTING_BASE" -eq 1 ]; then
  LANG="$(python3 - "$PROFILE" <<'PY'
import re, sys
txt = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r"^- \*\*Language:\*\* ([^\n—]+)", txt, re.M)
print(m.group(1).strip() if m else "English")
PY
)"
  say "Keeping the language your base already uses: $LANG"
else
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
fi

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
    printf 'Read this and follow it, every session. It carries the canon and imports it:\n'
    printf '@%s/AGENTS.md\n\n' "$DEST"
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
# 6. keeping the base — history, identity, and the copy that follows the person
# ---------------------------------------------------------------------------
say ""
GIT_ON=0
REMOTE_SET=0
AGENT_MUST_CREATE_REPO=0

if command -v git >/dev/null 2>&1; then
  GIT_ON=1

  # The kit's own history is never destroyed. If this folder came from the kit, its origin is
  # moved aside so 'origin' is free for the person's own copy — and so updates to the kit can
  # still be fetched later from a remote that is clearly not theirs.
  if [ -d "$DEST/.git" ]; then
    KIT_URL="$(git -C "$DEST" remote get-url origin 2>/dev/null || true)"
    case "$KIT_URL" in
      *harness-kit*)
        git -C "$DEST" remote remove origin 2>/dev/null || true
        git -C "$DEST" remote remove harness-kit 2>/dev/null || true
        git -C "$DEST" remote add harness-kit "$KIT_URL"
        say "  kept your history; the kit it came from is now remembered separately."
        ;;
    esac
  else
    git -C "$DEST" init -q
    # Name the branch `main` before the first commit. `git init` still defaults to `master` on
    # many installs, and a base on `master` pushed to a repository whose default is `main` ends
    # up with two branches — which is exactly how a phone cloning the default branch finds
    # nothing there (rules/device-sync.md: the base has one branch).
    git -C "$DEST" symbolic-ref HEAD refs/heads/main 2>/dev/null || true
    KIT_URL="$(git -C "$SRC" remote get-url origin 2>/dev/null || true)"
    if [ -n "$KIT_URL" ]; then
      git -C "$DEST" remote add harness-kit "$KIT_URL" 2>/dev/null || true
    fi
    say "  your base now keeps its own history (so nothing you do is ever lost)."
  fi

  # Saving needs a name to save under. Asked once, stored for this base only.
  if [ -z "$(git -C "$DEST" config user.name 2>/dev/null)" ] || [ -z "$(git -C "$DEST" config user.email 2>/dev/null)" ]; then
    say ""
    say "  Every save is stamped with a name, so you can tell your own work apart later."
    GIT_NAME="$(ask "  Your name" "${USER:-me}")"
    GIT_EMAIL="$(ask "  Your email" "")"
    git -C "$DEST" config user.name "$GIT_NAME"
    [ -n "$GIT_EMAIL" ] && git -C "$DEST" config user.email "$GIT_EMAIL"
  fi

  git -C "$DEST" add -A 2>/dev/null || true
  # Leave the base with a history, not with a pile of staged files and no commit: `git log`
  # fails on a repo with none, and the first send-out has nothing to send.
  if [ -z "$(git -C "$DEST" log -1 --format=%H 2>/dev/null)" ] && \
     [ -n "$(git -C "$DEST" diff --cached --name-only 2>/dev/null)" ]; then
    git -C "$DEST" commit -q -m "Start this base" 2>/dev/null || true
  fi

  # The one question that actually matters to the person.
  say ""
  say "  Your base can live in one private place online. That is what lets you pick up"
  say "  on your phone what you did on your computer, and the other way round. It is"
  say "  private — only you can see it."
  if [ -n "$(git -C "$DEST" remote get-url origin 2>/dev/null || true)" ]; then
    REMOTE_SET=1
    say "  Already set up — leaving it as it is."
  elif ask_yes "  Set that up now?" "Y"; then
    if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
      REPO_NAME="$(ask "    What should it be called?" "$(basename "$DEST")")"
      if gh repo create "$REPO_NAME" --private --source "$DEST" --remote origin >/dev/null 2>&1; then
        REMOTE_SET=1
        say "    created a private place for your base and connected it."
      else
        AGENT_MUST_CREATE_REPO=1
      fi
    else
      AGENT_MUST_CREATE_REPO=1
    fi
    if [ "$AGENT_MUST_CREATE_REPO" -eq 1 ]; then
      say "    I can't create it from here — your AI agent will do it in a moment."
    fi
  else
    say "  Skipped. Your base stays on this machine only: your phone and your other"
    say "  computers will not see any of it until this is set up."
  fi
else
  say "git is not installed, so your base cannot follow you between devices yet."
  say "Install git, then re-run this."
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
[ -d "$PROJECTS" ] && check "projects/ inside the base" 0 || check "projects/ inside the base" 1
[ -f "$DEST/projects/_index.md" ] && check "projects index present" 0 || check "projects index present" 1
[ -f "$DEST/tools/sync.py" ] && check "keeping-in-step tool present" 0 || check "keeping-in-step tool present" 1
[ -f "$DEST/tools/update.py" ] && check "kit updater present" 0 || check "kit updater present" 1
[ -f "$DEST/.engine-manifest.yml" ] && check "kit/person path contract present" 0 || check "kit/person path contract present" 1
[ -f "$DEST/.claude/settings.json" ] && check "sessions start by catching up" 0 || check "sessions start by catching up" 1
if [ "$GIT_ON" -eq 1 ]; then
  if [ -n "$(git -C "$DEST" remote get-url origin 2>/dev/null || true)" ]; then
    check "your base has a private place online" 0
  else
    say "  MISS your base has a private place online — it stays on this machine only"
    DOC_OK=0
  fi
fi

if grep -q "Language:" "$PROFILE" 2>/dev/null; then check "your language recorded in profile.md" 0; else check "your language recorded in profile.md" 1; fi

# Canon completeness: every rule file is named in the ONE list that carries the canon to
# every runtime. A rule missing there is silently not in force (rules/multi-agent.md).
PARITY_GAP="$(python3 - "$DEST" <<'PY'
import os, sys
base = sys.argv[1]
rules_dir = os.path.join(base, "rules")
names = sorted(f for f in os.listdir(rules_dir) if f.endswith(".md")) if os.path.isdir(rules_dir) else []
gaps = []
try:
    with open(os.path.join(base, "AGENTS.md"), "r", encoding="utf-8") as f:
        text = f.read()
except OSError:
    gaps.append("AGENTS.md missing")
    text = ""
gaps += ["%s not listed in AGENTS.md" % n for n in names if n not in text]
print("; ".join(gaps))
PY
)"
if [ -z "$PARITY_GAP" ]; then
  check "canon complete (every rule listed in AGENTS.md)" 0
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
say "Your projects:  $PROJECTS   (inside your base, so they travel with it)"
say "Talks to you:   $LANG"
say ""
say "What this means in plain terms:"
say "  - Launch your AI agent from your base folder and just talk to it."
say "  - It already knows how you want it to work (the canon is wired in)."
say "  - You never manage folders — the agent files knowledge and work for you."
if [ "$REMOTE_SET" -eq 1 ]; then
  say "  - Everything is kept in one private place online, so your phone and your"
  say "    computer show the same thing. The agent saves it for you and will ask"
  say "    before it does."
fi
if [ "$AGENT_MUST_CREATE_REPO" -eq 1 ]; then
  say ""
  say "ONE STEP LEFT — for the AI agent reading this, not for the person:"
  say "  Create a PRIVATE repository for this base using your GitHub access, set it as"
  say "  'origin' in $DEST, and send the base to it. This is also the first check that"
  say "  your GitHub access works — if it does not, say so plainly and offer the"
  say "  alternative. Then run: python3 \"$DEST/tools/sync.py\" status"
fi
say ""
say "Personalize one file when you like: $PROFILE"
say ""
