# Harness Kit installer — Windows PowerShell (lockstep twin of install.sh).
# Same prompts, same wiring. Run in PowerShell:  powershell -ExecutionPolicy Bypass -File .\install.ps1
#
# Symlink creation on Windows may require either Developer Mode enabled or an
# elevated (admin) shell. If it can't make the link, the canon is still wired
# via the entries written into your agent's global file.

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
function Say($m) { Write-Host $m }
# BOM-less UTF-8 write (mirrors the bash/python no-BOM output; Set-Content -Encoding UTF8
# emits a BOM on Windows PowerShell 5.1, which would diverge from install.sh).
function Write-Utf8NoBom($path, $text) {
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($path, $text, $enc)
}
function Ask($q, $def) {
  # Read-Host appends its own ": " — pass the prompt without a trailing colon to avoid a double colon.
  if ($def) { $p = "$q [$def]" } else { $p = "$q" }
  $a = Read-Host -Prompt $p
  if ([string]::IsNullOrWhiteSpace($a)) { return $def }
  return $a
}
function AskYes($q, $def) {
  if ($def -eq 'Y') { $hint = '[Y/n]' } else { $hint = '[y/N]' }
  $a = Read-Host -Prompt "$q $hint"
  if ([string]::IsNullOrWhiteSpace($a)) { $a = $def }
  return ($a -match '^(y|yes)$')
}
function Fail($m) { Say ""; Say "STOP: $m"; exit 1 }

# Idempotent managed-block upsert (mirror of upsert_block in install.sh).
function Upsert-Block($target, $marker, $block) {
  $begin = "<!-- BEGIN $marker -->"
  $end   = "<!-- END $marker -->"
  $managed = "$begin`n" + ($block.TrimEnd("`n")) + "`n$end"
  $old = ""
  if (Test-Path $target) { $old = Get-Content -Raw -LiteralPath $target }
  if ($old.Contains($begin) -and $old.Contains($end)) {
    $pre  = $old.Substring(0, $old.IndexOf($begin)).TrimEnd("`n")
    $post = $old.Substring($old.IndexOf($end) + $end.Length).TrimStart("`n")
    $new = ""
    if ($pre)  { $new += "$pre`n`n" }
    $new += $managed
    if ($post) { $new += "`n`n$post" } else { $new += "`n" }
  } else {
    if ($old.Trim()) { $new = $old.TrimEnd("`n") + "`n`n" + $managed + "`n" }
    else             { $new = $managed + "`n" }
  }
  $dir = Split-Path -Parent $target
  if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
  Write-Utf8NoBom $target $new
}

function Make-Symlink($targetPath, $linkPath) {
  if (Test-Path $linkPath) {
    $item = Get-Item $linkPath -Force
    if ($item.LinkType) { Remove-Item $linkPath -Force }
    else { Say "  note: $linkPath already exists and is not a link — leaving it, the @-imports still work."; return }
  }
  try {
    New-Item -ItemType SymbolicLink -Path $linkPath -Target $targetPath -Force | Out-Null
    Say "  linked $linkPath -> $targetPath"
  } catch {
    Say "  note: could not create the symlink $linkPath (Windows may need Developer Mode or an admin shell)."
    Say "        Not a problem — the canon is still wired via the entries written into your agent's global file."
  }
}

$HomeDir = $HOME
$Src = Split-Path -Parent $MyInvocation.MyCommand.Path

# ---------------------------------------------------------------------------
# 1. intro
# ---------------------------------------------------------------------------
Say ""
Say "==============================================================="
Say " Harness Kit — setup"
Say "==============================================================="
Say ""
Say "This folder is your BASE. Think of it as your AI agent's home:"
Say "you'll launch your agent from here, and it keeps your operating"
Say "principles, your knowledge, and your ongoing work in one place."
Say ""
Say "The generic canon (the rules/ and doctrine/ files) stays English"
Say "and untouched — it's the shared standard. Only ONE file is yours"
Say "to personalize: profile.md. This setup fills the first bits of it"
Say "for you and wires everything up. A few plain questions follow."
Say ""

# ---------------------------------------------------------------------------
# 2. where + name
# ---------------------------------------------------------------------------
$Root = Ask "Where should your base live? (a folder that will contain it)" $HomeDir
$Root = [System.IO.Path]::GetFullPath(($Root -replace '^~', $HomeDir))
$Name = Ask "What should the base folder be called?" "harness"
$Dest = Join-Path $Root $Name
$Projects = Join-Path $Root "projects"

Say ""
Say "Plan:"
Say "  base     -> $Dest"
Say "  projects -> $Projects   (created beside the base, for the things you'll build)"
Say ""

$InPlace = $false
if ($Dest -eq $Src) {
  $InPlace = $true
  Say "You're installing in place (the base stays right here)."
} elseif (Test-Path $Dest) {
  if (-not (AskYes "  $Dest already exists. Copy the base into it anyway?" "N")) {
    Fail "Nothing changed. Re-run and pick a different name or location."
  }
}

# ---------------------------------------------------------------------------
# 3. place the base + create projects sibling
# ---------------------------------------------------------------------------
if (-not $InPlace) {
  Say "Placing the base..."
  if (-not (Test-Path $Dest)) { New-Item -ItemType Directory -Path $Dest -Force | Out-Null }
  $exclude = @('.git', '.DS_Store', '__pycache__', '.venv')
  Get-ChildItem -Force -LiteralPath $Src | Where-Object { $exclude -notcontains $_.Name } | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $Dest -Recurse -Force
  }
  # prune ignored artifacts that may have slipped through nested dirs (mirror the bash ignore_patterns:
  # .venv / __pycache__ dirs and *.log / .DS_Store files, at every level, not just top-level)
  Get-ChildItem -Path $Dest -Recurse -Force -Directory -Include '__pycache__', '.venv' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
  Get-ChildItem -Path $Dest -Recurse -Force -File -Include '*.log', '.DS_Store' -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
  Say "  copied base -> $Dest"
}

if (-not (Test-Path $Projects)) {
  New-Item -ItemType Directory -Path $Projects -Force | Out-Null
  Say "  created $Projects"
}

$ProfileFile = Join-Path $Dest "profile.md"
if (-not (Test-Path $ProfileFile)) { Fail "profile.md not found in the base at $ProfileFile — the base looks incomplete." }

# ---------------------------------------------------------------------------
# 4. language -> profile.md
# ---------------------------------------------------------------------------
Say ""
Say "Your agent talks to YOU in your language. The base content stays"
Say "English (it's the shared standard, and code is always English), but"
Say "the agent will converse, explain, and ask you things in whatever"
Say "language you pick here."
$Lang = Ask "What language should the agent talk to you in?" "English"

$txt = Get-Content -Raw -LiteralPath $ProfileFile
$line = "- **Language:** $Lang — the agent converses with you in this language; code, comments, and identifiers stay English."
$rx = [regex]'(?m)^- \*\*Language:\*\*.*$'
if ($rx.IsMatch($txt)) {
  $txt = $rx.Replace($txt, { param($m) $line }, 1)
} else {
  $txt = $txt.TrimEnd("`n") + "`n`n" + $line + "`n"
}
Write-Utf8NoBom $ProfileFile $txt
Say "  set Language: $Lang in profile.md"

# ---------------------------------------------------------------------------
# 5. wire agents
# ---------------------------------------------------------------------------
Say ""
Say "Now let's connect your base to the AI agent(s) you use, so the canon"
Say "is active from ANY folder — you never have to point the agent at it."
Say ""

function Gen-RuleImports {
  $lines = @()
  Get-ChildItem -Path (Join-Path $Dest "rules") -Filter '*.md' | Sort-Object Name | ForEach-Object {
    $lines += "@$($_.FullName)"
  }
  return ($lines -join "`n")
}

# ---- Claude Code -----------------------------------------------------------
$ClaudeWired = $false
if (AskYes "Do you use Claude Code?" "Y") {
  $ClaudeWired = $true
  $ClaudeDir = Join-Path $HomeDir ".claude"
  if (-not (Test-Path $ClaudeDir)) { New-Item -ItemType Directory -Path $ClaudeDir -Force | Out-Null }
  Make-Symlink (Join-Path $Dest "rules") (Join-Path $ClaudeDir "harness-kit-rules")
  $block = @"
## Harness Kit — global canon (managed by install.ps1; do not edit between the markers)

**HARNESS HOME:** ``$Dest``
This is your operating base. ``$Dest/knowledge/_index.md`` (durable knowledge) and
``$Dest/activities/_index.md`` (ongoing work) are reachable from any working directory, every session.

Hot canon — loaded every session:
$(Gen-RuleImports)
@$Dest/profile.md

Full three-tier loading model: read ``$Dest/CLAUDE.md``.
Converse in the language set in ``$Dest/profile.md``; code, comments, and identifiers stay English.
"@
  Upsert-Block (Join-Path $ClaudeDir "CLAUDE.md") "HARNESS-KIT" $block
  Say "  wired the canon into $ClaudeDir\CLAUDE.md (active in every Claude Code session)."
}

# ---- Codex -----------------------------------------------------------------
if (AskYes "Do you use Codex (OpenAI Codex CLI)?" "N") {
  $CodexDir = Join-Path $HomeDir ".codex"
  if (-not (Test-Path $CodexDir)) { New-Item -ItemType Directory -Path $CodexDir -Force | Out-Null }
  $block = @"
## Harness Kit — global canon (managed by install.ps1; do not edit between the markers)

Your operating base ("harness home") is: $Dest

At the start of every session, read ``$Dest/AGENTS.md`` and the canon files it
lists under ``$Dest/rules/``. Follow that canon. Read ``$Dest/knowledge/_index.md``
on demand for durable knowledge; consult ``$Dest/activities/_index.md`` only on the
narrow signals it names. Converse in the language set in ``$Dest/profile.md``;
code, comments, and identifiers stay English.
"@
  Upsert-Block (Join-Path $CodexDir "AGENTS.md") "HARNESS-KIT" $block
  Say "  wired the canon into $CodexDir\AGENTS.md (Codex's global instructions)."
}

# ---- Cursor ----------------------------------------------------------------
if (AskYes "Do you use Cursor?" "N") {
  $CursorTxt = Join-Path $Dest "cursor-user-rules.txt"
  $c = @"
Your operating base ("harness home") is: $Dest
Read $Dest/AGENTS.md and the canon files it lists under $Dest/rules/ and follow that canon.
Read $Dest/knowledge/_index.md on demand; consult $Dest/activities/_index.md only on the narrow signals it names.
Converse in the language set in $Dest/profile.md; code, comments, and identifiers stay English.
"@
  Write-Utf8NoBom $CursorTxt $c
  Say "  Cursor has no scriptable GLOBAL rules file, so I wrote a ready-to-paste snippet:"
  Say "    $CursorTxt"
  Say "  MANUAL STEP: open Cursor -> Settings -> Rules -> 'User Rules', and paste that file's contents."
}

# ---- other -----------------------------------------------------------------
if (AskYes "Do you use another AI agent I should point at this base?" "N") {
  Say "  For any other agent, wire its GLOBAL / always-on instructions to read:"
  Say "    $Dest\AGENTS.md   (the cross-agent entry file — lists the canon in rules/)"
  Say "  Point that agent's persistent-instructions setting at that file and it will pick up the canon."
}

# ---------------------------------------------------------------------------
# 6. git
# ---------------------------------------------------------------------------
Say ""
$GitOn = $false
$hasGit = [bool](Get-Command git -ErrorAction SilentlyContinue)
if ($hasGit -and (AskYes "Track your base with git? (recommended — it's a safety net for your own history)" "Y")) {
  $GitOn = $true
  if (Test-Path (Join-Path $Dest ".git")) {
    if (AskYes "  This folder already has git history from the template. Start fresh with YOUR own history?" "Y") {
      Remove-Item -Recurse -Force (Join-Path $Dest ".git")
      git -C $Dest init -q
      Say "  started a fresh git repo for your base."
    } else { Say "  kept the existing git history." }
  } else {
    git -C $Dest init -q
    Say "  git repo created for your base."
  }
  git -C $Dest add -A 2>$null

  if (AskYes "  Also auto-create a git repo inside each NEW project you build under projects/?" "Y") {
    $ptxt = Get-Content -Raw -LiteralPath $ProfileFile
    $note = "- **Git:** track the base with git; auto-run ``git init`` inside each new project created under ``projects/``."
    if (-not $ptxt.Contains($note)) {
      $ptxt = $ptxt.TrimEnd("`n") + "`n`n" + $note + "`n"
      Write-Utf8NoBom $ProfileFile $ptxt
      Say "  recorded 'auto-init new projects' in profile.md (the agent honors it)."
    }
  }

  Say ""
  Say "  A REMOTE keeps a copy off your machine and syncs across your computers."
  if (AskYes "  Want your base on all your machines (add a remote now)?" "N") {
    $RemoteUrl = Ask "    Paste the git remote URL (e.g. git@github.com:you/your-base.git)" ""
    if ($RemoteUrl) {
      git -C $Dest remote remove origin 2>$null
      git -C $Dest remote add origin $RemoteUrl
      Say "    remote 'origin' set to $RemoteUrl"
      Say "    (nothing pushed yet — commit when you're ready, then: git -C `"$Dest`" push -u origin HEAD)"
    } else { Say "    no URL given — skipped the remote. You can add one later." }
  } else { Say "  no remote — your base stays local only. You can add one anytime." }
} else {
  Say "Skipping git — nothing git-related will be touched until you ask."
}

# ---------------------------------------------------------------------------
# 7. doctor — quick health check
# ---------------------------------------------------------------------------
Say ""
Say "Running a quick health check..."
$DocOk = $true
function Check($label, $ok) {
  if ($ok) { Say "  OK   $label" } else { Say "  MISS $label"; $script:DocOk = $false }
}
Check "canon rules present" (Test-Path (Join-Path $Dest "rules"))
Check "doctrine present" (Test-Path (Join-Path $Dest "doctrine"))
Check "knowledge index present" (Test-Path (Join-Path $Dest "knowledge/_index.md"))
Check "activities index present" (Test-Path (Join-Path $Dest "activities/_index.md"))
Check "cross-agent entry (AGENTS.md) present" (Test-Path (Join-Path $Dest "AGENTS.md"))
Check "Claude entry (CLAUDE.md) present" (Test-Path (Join-Path $Dest "CLAUDE.md"))
Check "projects/ folder beside the base" (Test-Path $Projects)
Check "your language recorded in profile.md" ((Get-Content -Raw -LiteralPath $ProfileFile) -match 'Language:')
if ($ClaudeWired) {
  $gcm = Join-Path $HomeDir ".claude/CLAUDE.md"
  if ((Test-Path $gcm) -and ((Get-Content -Raw -LiteralPath $gcm) -match 'BEGIN HARNESS-KIT')) {
    Check "Claude Code global wiring" $true
  } else {
    Check "Claude Code global wiring" $false
  }
}

# ---------------------------------------------------------------------------
# 8. summary
# ---------------------------------------------------------------------------
Say ""
Say "==============================================================="
if ($DocOk) { Say " Done. Your base is ready." } else { Say " Done, with a couple of items to check above (marked MISS)." }
Say "==============================================================="
Say ""
Say "Your base:      $Dest"
Say "Your projects:  $Projects"
Say "Talks to you:   $Lang"
Say ""
Say "What this means in plain terms:"
Say "  - Launch your AI agent from your base folder and just talk to it."
Say "  - It already knows how you want it to work (the canon is wired in)."
Say "  - You never manage folders — the agent files knowledge and work for you."
if ($GitOn) {
  Say "  - Your base is under git. Ask the agent to 'save my work' whenever you want a checkpoint."
}
Say ""
Say "Personalize one file when you like: $ProfileFile"
Say ""
