# Harness Kit installer — Windows PowerShell (lockstep twin of install.sh).
# Same prompts, same wiring. Run in PowerShell:  powershell -ExecutionPolicy Bypass -File .\install.ps1
#

$ErrorActionPreference = 'Stop'

# Every `git` and `gh` call below is a NATIVE command, and native commands write ordinary
# progress to stderr — "LF will be replaced by CRLF", "No such remote", "does not have any
# commits yet". Under $ErrorActionPreference = 'Stop' each of those becomes a terminating
# error (and on PowerShell 7.3+ so does any non-zero exit code), so the installer would abort
# midway through setting up git on a perfectly healthy machine. Run every native call through
# this helper, which relaxes the preference for the duration and hands back the output.
function Invoke-Native {
  $eap = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try { & $args[0] @($args[1..($args.Count - 1)]) 2>$null } finally { $ErrorActionPreference = $eap }
}
function Git-Q { Invoke-Native git @args }

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
# Every answer is read from stdin. With nothing attached — an agent running this in its own
# shell — every read returns empty and takes the default, so the script finishes, prints "your
# base is ready", and has asked the person nothing at all. That output is indistinguishable from
# a real install, which is what makes it dangerous rather than merely wrong.
function Require-Answers {
  if (-not [Console]::IsInputRedirected) { return }
  if ($env:HARNESS_ANSWERS_ON_STDIN) { return }
  Say ""
  Say "STOP: this is not an interactive terminal, so nobody can answer the questions."
  Say "  Nothing has been changed."
  Say ""
  Say "  If you are an AI agent: ask the person each question yourself and perform the"
  Say "  steps conversationally — that is the supported path. If you genuinely have the"
  Say "  answers already, pass them on stdin and set HARNESS_ANSWERS_ON_STDIN=1 so the"
  Say "  choice is explicit. Never let this script take defaults nobody chose."
  exit 1
}

function Fail($m) { Say ""; Say "STOP: $m"; exit 1 }

# Idempotent managed-block upsert (mirror of upsert_block in install.sh).
function Upsert-Block($target, $marker, $block) {
  $begin = "<!-- BEGIN $marker -->"
  $end   = "<!-- END $marker -->"
  $managed = "$begin`n" + ($block.TrimEnd("`n")) + "`n$end"
  $old = ""
  # -Encoding UTF8 is not optional on Windows PowerShell 5.1: without it this reads the file
  # through the system ANSI code page, so every em dash comes back as mojibake and is written
  # straight back out — silently corrupting a file the person never asked us to rewrite.
  if (Test-Path -LiteralPath $target) { $old = Get-Content -Raw -Encoding UTF8 -LiteralPath $target }
  if (-not $old) { $old = "" }
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

$HomeDir = $HOME
$Src = Split-Path -Parent $MyInvocation.MyCommand.Path

# The address the kit ships from, read from the manifest rather than guessed from a name. A
# person whose own base repository is called "harness-kit" — the name this installer suggests
# for it — would otherwise have their own `origin` mistaken for the kit's and moved aside,
# after which nothing they do can be saved anywhere.
$KitAddress = ""
$ManifestPath = Join-Path $Src ".engine-manifest.yml"
if (Test-Path -LiteralPath $ManifestPath) {
  $m = [regex]::Match((Get-Content -Raw -Encoding UTF8 -LiteralPath $ManifestPath),
                      '(?m)^kit_remote:[ \t]*(\S+)')
  if ($m.Success) { $KitAddress = $m.Groups[1].Value }
}

# Same-Repo <url-a> <url-b> -> $true when they name the same repository (mirror of same_repo
# in install.sh): a trailing .git or slash and letter case are noise, not a difference.
function Same-Repo($a, $b) {
  if (-not $a -or -not $b) { return $false }
  $na = ($a -replace '\.git$', '' -replace '/$', '').ToLower()
  $nb = ($b -replace '\.git$', '' -replace '/$', '').ToLower()
  return ($na -eq $nb)
}

# Two ways in. A fresh copy of the kit becomes a NEW base. A folder whose profile.md already
# carries a recorded language IS a base — the person is setting it up on another device, and
# nothing about their content or their history may be touched.
Require-Answers

$ExistingBase = $false
$SrcProfile = Join-Path $Src "profile.md"
if ((Test-Path $SrcProfile) -and ((Get-Content -Raw -Encoding UTF8 -LiteralPath $SrcProfile) -match 'the agent converses with you in this language')) {
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
  # Resolve against the SHELL's location. [System.IO.Path]::GetFullPath uses the .NET process
  # directory, which does not follow Set-Location — an answer of "." would land the base in
  # whatever folder PowerShell happened to start in, commonly System32.
  if ($Root.StartsWith('~')) { $Root = $HomeDir + $Root.Substring(1) }
  $Root = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Root)
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
  $CopiedNames = @()
  Get-ChildItem -Force -LiteralPath $Src | Where-Object { $exclude -notcontains $_.Name } | ForEach-Object {
    $script:CopiedNames += $_.Name
    # Copy the CONTENTS into the destination folder, not the folder into it: `Copy-Item -Recurse`
    # onto an existing directory produces `rules\rules`, which is the merge case bash handles
    # with dirs_exist_ok=True.
    $d = Join-Path $Dest $_.Name
    if ($_.PSIsContainer) {
      if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
      Copy-Item -Path (Join-Path $_.FullName '*') -Destination $d -Recurse -Force
    } else {
      Copy-Item -LiteralPath $_.FullName -Destination $d -Force
    }
  }
  # Prune the artifacts the copy may have carried in — and ONLY under the names it copied.
  # Sweeping all of $Dest deleted whatever was already there: the bash twin filters at copy
  # time (`shutil.ignore_patterns`) and never touches a pre-existing file, so a sweep here was
  # both a [CP-4] break and a deletion nobody confirmed (rules/safety.md).
  foreach ($copied in $CopiedNames) {
    $under = Join-Path $Dest $copied
    if (-not (Test-Path -LiteralPath $under)) { continue }
    Get-ChildItem -LiteralPath $under -Recurse -Force -Directory -Include '__pycache__', '.venv', '.git' -ErrorAction SilentlyContinue |
      Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $under -Recurse -Force -File -Include '*.log', '.DS_Store' -ErrorAction SilentlyContinue |
      Remove-Item -Force -ErrorAction SilentlyContinue
  }
  Say "  copied base -> $Dest"
}

if (-not (Test-Path $Projects)) {
  New-Item -ItemType Directory -Path $Projects -Force | Out-Null
  Say "  created $Projects"
}

# An earlier layout kept projects beside the base, where a phone or a second machine can
# never see them. Bring them in.
# Only when the folder is recognisably a former harness `projects/`, and never on the strength
# of its name: with this installer's own defaults the path is the person's ordinary `projects`
# folder, and absorbing it moved unrelated work into a repository that is then pushed.
$LegacyProjects = Join-Path (Split-Path -Parent $Dest) "projects"
if ((Test-Path $LegacyProjects) -and ($LegacyProjects -ne $Projects) -and
    (Test-Path (Join-Path $LegacyProjects "_index.md"))) {
  Say ""
  Say "  Found $LegacyProjects — an earlier harness left it there, outside your base."
  Say "  Anything in it is invisible to your phone and your other computers."
  Say "  It holds:"
  Get-ChildItem -Force -LiteralPath $LegacyProjects | Select-Object -First 20 |
    ForEach-Object { Say "    $($_.Name)" }
  if (AskYes "  Move it inside the base?" "N") {
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
      # Left in place on purpose: an empty directory is not permission to delete it, and this
      # one is outside the base (rules/safety.md).
      Say "  $LegacyProjects is now empty; left in place — it is outside your base"
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
  $m = [regex]::Match((Get-Content -Raw -Encoding UTF8 -LiteralPath $ProfileFile), '(?m)^- \*\*Language:\*\* ([^\r\n—]+)')
  $Lang = if ($m.Success) { $m.Groups[1].Value.Trim() } else { "English" }
  Say "Keeping the language your base already uses: $Lang"
} else {
  Say "Your agent talks to YOU in your language. The base content stays"
  Say "English (it's the shared standard, and code is always English), but"
  Say "the agent will converse, explain, and ask you things in whatever"
  Say "language you pick here."
  $Lang = Ask "What language should the agent talk to you in?" "English"

  $txt = Get-Content -Raw -Encoding UTF8 -LiteralPath $ProfileFile
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

# ---- Claude Code -----------------------------------------------------------
$ClaudeWired = $false
if (AskYes "Do you use Claude Code?" "Y") {
  $ClaudeWired = $true
  $ClaudeDir = Join-Path $HomeDir ".claude"
  if (-not (Test-Path $ClaudeDir)) { New-Item -ItemType Directory -Path $ClaudeDir -Force | Out-Null }
  $block = @"
## Harness Kit — global canon (managed by install.ps1; do not edit between the markers)

**HARNESS HOME:** ``$Dest``
This is your operating base. ``$Dest/knowledge/_index.md`` (durable knowledge) and
``$Dest/activities/_index.md`` (ongoing work) are reachable from any working directory, every session.

Read this and follow it, every session. It carries the canon and imports it:
@$Dest/AGENTS.md

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
    $KitUrl = (Git-Q -C $Dest remote get-url origin)
    if (Same-Repo $KitUrl $KitAddress) {
      Git-Q -C $Dest remote remove origin | Out-Null
      Git-Q -C $Dest remote remove harness-kit | Out-Null
      Git-Q -C $Dest remote add harness-kit $KitUrl | Out-Null
      Say "  kept your history; the kit it came from is now remembered separately."
    }
  } else {
    Git-Q -C $Dest init -q | Out-Null
    # Name the branch `main` before the first commit. `git init` still defaults to `master` on
    # many installs, and a base on `master` pushed to a repository whose default is `main` ends
    # up with two branches — which is exactly how a phone cloning the default branch finds
    # nothing there (rules/device-sync.md: the base has one branch).
    Git-Q -C $Dest symbolic-ref HEAD refs/heads/main | Out-Null
    $KitUrl = (Git-Q -C $Src remote get-url origin)
    if ($KitUrl) { Git-Q -C $Dest remote add harness-kit $KitUrl | Out-Null }
    Say "  your base now keeps its own history (so nothing you do is ever lost)."
  }

  # Saving needs a name to save under. Asked once, stored for this base only.
  if (-not (Git-Q -C $Dest config user.name) -or -not (Git-Q -C $Dest config user.email)) {
    Say ""
    Say "  Every save is stamped with a name, so you can tell your own work apart later."
    Say "  Both are needed: without them nothing you do here can be recorded at all,"
    Say "  and none of it would reach your phone or another computer."
    $defaultName = if ($env:USERNAME) { $env:USERNAME } else { "me" }
    $defaultMail = "$defaultName@$([System.Net.Dns]::GetHostName())"
    $GitName = Ask "  Your name" $defaultName
    $GitEmail = Ask "  Your email" $defaultMail
    # Guarded: with an empty value PowerShell drops the argument and `git config user.name`
    # becomes the two-token READ form — it prints the setting instead of setting it, and the
    # question comes back on every future run.
    if ($GitName)  { Git-Q -C $Dest config user.name $GitName }
    if ($GitEmail) { Git-Q -C $Dest config user.email $GitEmail }
  }

  Git-Q -C $Dest add -A | Out-Null
  # Leave the base with a history, not with a pile of staged files and no commit: `git log`
  # fails on a repo with none, and the first send-out has nothing to send.
  $hasCommit = (Git-Q -C $Dest log -1 --format=%H)
  $hasStaged = (Git-Q -C $Dest diff --cached --name-only)
  if (-not $hasCommit -and $hasStaged) { Git-Q -C $Dest commit -q -m "Start this base" | Out-Null }

  # The one question that actually matters to the person.
  Say ""
  Say "  Your base can live in one private place online. That is what lets you pick up"
  Say "  on your phone what you did on your computer, and the other way round. It is"
  Say "  private — only you can see it."
  if (Git-Q -C $Dest remote get-url origin) {
    $RemoteSet = $true
    Say "  Already set up — leaving it as it is."
  } elseif (AskYes "  Set that up now?" "Y") {
    $hasGh = [bool](Get-Command gh -ErrorAction SilentlyContinue)
    if ($hasGh) { Invoke-Native gh auth status | Out-Null; $ghReady = ($LASTEXITCODE -eq 0) } else { $ghReady = $false }
    if ($ghReady) {
      $RepoName = Ask "    What should it be called?" (Split-Path -Leaf $Dest)
      Invoke-Native gh repo create $RepoName --private --source $Dest --remote origin | Out-Null
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
Check "kit updater present" (Test-Path (Join-Path $Dest "tools/update.py"))
Check "kit/person path contract present" (Test-Path (Join-Path $Dest ".engine-manifest.yml"))
Check "sessions start by catching up" (Test-Path (Join-Path $Dest ".claude/settings.json"))
# Resolving the name proves nothing on Windows: `python3.exe` is an App Execution Alias that
# opens the Microsoft Store, and a real python.org install ships `python.exe` and `py.exe` with
# no `python3` at all. Ask it for its version and see whether anything answers.
#
# `python3` is checked ON ITS OWN, because that is the literal name .claude/settings.json runs
# at session start — a JSON hook cannot try three names. Accepting `python` here instead would
# report OK on a machine where the hook can never fire, and the person would be told their base
# catches up by itself while it silently never does.
$pythonWorks = $false
$out = Invoke-Native 'python3' '--version'
if ($LASTEXITCODE -eq 0 -and $out) { $pythonWorks = $true }
Check "python3 available (needed to catch up automatically)" $pythonWorks
if (-not $pythonWorks) {
  $alternative = ""
  foreach ($candidate in @(@('python', '--version'), @('py', '-3', '--version'))) {
    $out = Invoke-Native @candidate
    if ($LASTEXITCODE -eq 0 -and $out) { $alternative = $candidate[0]; break }
  }
  if ($alternative) {
    Say "       python is installed here as '$alternative', not as 'python3'."
    Say "       Your base will NOT catch up on its own at session start — your agent has to do"
    Say "       it, and it knows to. To fix it properly, install Python from python.org (which"
    Say "       registers 'python3') or add a 'python3' alias on your PATH."
  }
}
if ($GitOn) {
  # Checked, not assumed: without history nothing here can travel, and every other OK line
  # above would read as though it could.
  Check "your work here is being recorded" ([bool](Git-Q -C $Dest log -1 --format=%H))
  # Named for what was actually established: an origin that was already there was never checked,
  # and calling it "private" because a URL exists is the assertion that hid a public one.
  $OriginUrl = Git-Q -C $Dest remote get-url origin
  $Visibility = ""
  if (Get-Command gh -ErrorAction SilentlyContinue) {
    $Visibility = (Invoke-Native gh repo view $OriginUrl --json visibility -q .visibility)
  }
  if ("$Visibility".Trim().ToLower() -eq "public") {
    Say "  MISS the place your base lives online is PUBLIC — anyone can read it"
    $script:DocOk = $false
  } elseif ("$Visibility".Trim().ToLower() -eq "private") {
    Check "your base has a private place online" $true
  } else {
    Check "your base has a place online (privacy not verified from here)" ([bool]$OriginUrl)
  }
}
Check "your language recorded in profile.md" ((Get-Content -Raw -Encoding UTF8 -LiteralPath $ProfileFile) -match 'Language:')

# Canon completeness: every rule file is named in the ONE list that carries the canon to every
# runtime. A rule missing there is silently not in force (rules/multi-agent.md). Done in pure
# PowerShell so the check still runs on a machine without python3.
$contractPath = Join-Path $Dest "AGENTS.md"
if (Test-Path $contractPath) {
  $contract = Get-Content -Raw -Encoding UTF8 -LiteralPath $contractPath
  $missing = @()
  Get-ChildItem -Path (Join-Path $Dest "rules") -Filter '*.md' -ErrorAction SilentlyContinue | ForEach-Object {
    if ($contract -notmatch [regex]::Escape($_.Name)) { $missing += $_.Name }
  }
  if ($missing.Count -eq 0) {
    Check "canon complete (every rule listed in AGENTS.md)" $true
  } else {
    Say "  MISS canon complete: $($missing -join ', ') not listed in AGENTS.md"
    $script:DocOk = $false
  }
} else {
  Check "canon complete (every rule listed in AGENTS.md)" $false
}
if ($ClaudeWired) {
  $gcm = Join-Path $HomeDir ".claude/CLAUDE.md"
  if ((Test-Path $gcm) -and ((Get-Content -Raw -Encoding UTF8 -LiteralPath $gcm) -match 'BEGIN HARNESS-KIT')) {
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
