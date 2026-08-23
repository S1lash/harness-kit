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

# Two ways in. A fresh copy of the kit becomes a NEW base. A folder whose profile.md already
# carries a recorded language IS a base — the person is setting it up on another device, and
# nothing about their content or their history may be touched.
$ExistingBase = $false
$SrcProfile = Join-Path $Src "profile.md"
if ((Test-Path $SrcProfile) -and ((Get-Content -Raw -LiteralPath $SrcProfile) -match 'the agent converses with you in this language')) {
  $ExistingBase = $true
}

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
# 2. where + name  (or: recognise a base that already exists)
# ---------------------------------------------------------------------------
$InPlace = $false
if ($ExistingBase) {
  $Dest = $Src
  $InPlace = $true
  Say "This is already your base — I'll set this device up to use it and leave your"
  Say "content and history alone."
  Say ""
} else {
  $Root = Ask "Where should your base live? (a folder that will contain it)" $HomeDir
  $Root = [System.IO.Path]::GetFullPath(($Root -replace '^~', $HomeDir))
  $Name = Ask "What should the base folder be called?" "harness"
  $Dest = Join-Path $Root $Name

  Say ""
  Say "Plan:"
  Say "  base -> $Dest"
  Say "  everything you build lives inside it, in $(Join-Path $Dest 'projects')"
  Say ""

  if ($Dest -eq $Src) {
    $InPlace = $true
    Say "You're installing in place (the base stays right here)."
  } elseif (Test-Path $Dest) {
    if (-not (AskYes "  $Dest already exists. Copy the base into it anyway?" "N")) {
      Fail "Nothing changed. Re-run and pick a different name or location."
    }
  }
}

$Projects = Join-Path $Dest "projects"

# ---------------------------------------------------------------------------
# 3. place the base
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

# An earlier layout kept projects beside the base, where a phone or a second machine can
# never see them. Bring them in.
$LegacyProjects = Join-Path (Split-Path -Parent $Dest) "projects"
if ((Test-Path $LegacyProjects) -and ($LegacyProjects -ne $Projects)) {
  Say ""
  Say "  Found $LegacyProjects outside your base. Anything there is invisible to your"
  Say "  phone and to your other computers, because only the base travels."
  if (AskYes "  Move it inside the base?" "Y") {
    Get-ChildItem -Force -LiteralPath $LegacyProjects | ForEach-Object {
      $target = Join-Path $Projects $_.Name
      if (Test-Path $target) {
        Say "  kept in place (already inside the base): $($_.Name)"
      } else {
        Move-Item -LiteralPath $_.FullName -Destination $target
        Say "  moved inside the base: $($_.Name)"
      }
    }
    if (-not (Get-ChildItem -Force -LiteralPath $LegacyProjects)) {
      Remove-Item -LiteralPath $LegacyProjects
      Say "  removed the now-empty $LegacyProjects"
    }
  }
}

$ProfileFile = Join-Path $Dest "profile.md"
if (-not (Test-Path $ProfileFile)) { Fail "profile.md not found in the base at $ProfileFile — the base looks incomplete." }

# ---------------------------------------------------------------------------
# 4. language -> profile.md
# ---------------------------------------------------------------------------
Say ""
if ($ExistingBase) {
  $m = [regex]::Match((Get-Content -Raw -LiteralPath $ProfileFile), '(?m)^- \*\*Language:\*\* ([^\r\n—]+)')
  $Lang = if ($m.Success) { $m.Groups[1].Value.Trim() } else { "English" }
  Say "Keeping the language your base already uses: $Lang"
} else {
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
}

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
# 6. keeping the base — history, identity, and the copy that follows the person
# ---------------------------------------------------------------------------
Say ""
$GitOn = $false
$RemoteSet = $false
$AgentMustCreateRepo = $false
$hasGit = [bool](Get-Command git -ErrorAction SilentlyContinue)

if ($hasGit) {
  $GitOn = $true

  # The kit's own history is never destroyed. If this folder came from the kit, its origin is
  # moved aside so 'origin' is free for the person's own copy — and so updates to the kit can
  # still be fetched later from a remote that is clearly not theirs.
  if (Test-Path (Join-Path $Dest ".git")) {
    $KitUrl = (git -C $Dest remote get-url origin 2>$null)
    if ($KitUrl -and $KitUrl -match 'harness-kit') {
      git -C $Dest remote remove origin 2>$null
      git -C $Dest remote remove harness-kit 2>$null
      git -C $Dest remote add harness-kit $KitUrl
      Say "  kept your history; the kit it came from is now remembered separately."
    }
  } else {
    git -C $Dest init -q
    $KitUrl = (git -C $Src remote get-url origin 2>$null)
    if ($KitUrl) { git -C $Dest remote add harness-kit $KitUrl 2>$null }
    Say "  your base now keeps its own history (so nothing you do is ever lost)."
  }

  # Saving needs a name to save under. Asked once, stored for this base only.
  if (-not (git -C $Dest config user.name 2>$null) -or -not (git -C $Dest config user.email 2>$null)) {
    Say ""
    Say "  Every save is stamped with a name, so you can tell your own work apart later."
    $GitName = Ask "  Your name" $env:USERNAME
    $GitEmail = Ask "  Your email" ""
    git -C $Dest config user.name $GitName
    if ($GitEmail) { git -C $Dest config user.email $GitEmail }
  }

  git -C $Dest add -A 2>$null

  # The one question that actually matters to the person.
  Say ""
  Say "  Your base can live in one private place online. That is what lets you pick up"
  Say "  on your phone what you did on your computer, and the other way round. It is"
  Say "  private — only you can see it."
  if (git -C $Dest remote get-url origin 2>$null) {
    $RemoteSet = $true
    Say "  Already set up — leaving it as it is."
  } elseif (AskYes "  Set that up now?" "Y") {
    $hasGh = [bool](Get-Command gh -ErrorAction SilentlyContinue)
    if ($hasGh) { gh auth status *> $null; $ghReady = ($LASTEXITCODE -eq 0) } else { $ghReady = $false }
    if ($ghReady) {
      $RepoName = Ask "    What should it be called?" (Split-Path -Leaf $Dest)
      gh repo create $RepoName --private --source $Dest --remote origin *> $null
      if ($LASTEXITCODE -eq 0) {
        $RemoteSet = $true
        Say "    created a private place for your base and connected it."
      } else { $AgentMustCreateRepo = $true }
    } else { $AgentMustCreateRepo = $true }
    if ($AgentMustCreateRepo) {
      Say "    I can't create it from here — your AI agent will do it in a moment."
    }
  } else {
    Say "  Skipped. Your base stays on this machine only: your phone and your other"
    Say "  computers will not see any of it until this is set up."
  }
} else {
  Say "git is not installed, so your base cannot follow you between devices yet."
  Say "Install git, then re-run this."
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
Check "projects/ inside the base" (Test-Path $Projects)
Check "projects index present" (Test-Path (Join-Path $Dest "projects/_index.md"))
Check "keeping-in-step tool present" (Test-Path (Join-Path $Dest "tools/sync.py"))
Check "sessions start by catching up" (Test-Path (Join-Path $Dest ".claude/settings.json"))
Check "python3 available (needed to catch up automatically)" ([bool](Get-Command python3 -ErrorAction SilentlyContinue))
if ($GitOn) { Check "your base has a private place online" ([bool](git -C $Dest remote get-url origin 2>$null)) }
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
Say "Your projects:  $Projects   (inside your base, so they travel with it)"
Say "Talks to you:   $Lang"
Say ""
Say "What this means in plain terms:"
Say "  - Launch your AI agent from your base folder and just talk to it."
Say "  - It already knows how you want it to work (the canon is wired in)."
Say "  - You never manage folders — the agent files knowledge and work for you."
if ($RemoteSet) {
  Say "  - Everything is kept in one private place online, so your phone and your"
  Say "    computer show the same thing. The agent saves it for you and will ask"
  Say "    before it does."
}
if ($AgentMustCreateRepo) {
  Say ""
  Say "ONE STEP LEFT — for the AI agent reading this, not for the person:"
  Say "  Create a PRIVATE repository for this base using your GitHub access, set it as"
  Say "  'origin' in $Dest, and send the base to it. This is also the first check that"
  Say "  your GitHub access works — if it does not, say so plainly and offer the"
  Say "  alternative. Then run: python3 `"$Dest/tools/sync.py`" status"
}
Say ""
Say "Personalize one file when you like: $ProfileFile"
Say ""
