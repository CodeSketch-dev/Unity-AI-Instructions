param(
  [Parameter(Mandatory=$true)][string]$Repo,
  [Parameter(Mandatory=$true)][string]$ClaudeHome,
  [switch]$NoProjects
)
$ErrorActionPreference = 'Stop'
$utf8 = New-Object Text.UTF8Encoding $false

# ---------- 1. user-level settings.json: UI gate hook + un-hide UI skills ----------
$settingsPath = Join-Path $ClaudeHome 'settings.json'
$hookScript = Join-Path $ClaudeHome 'pipeline-hooks\hooks\ui_gate_reminder.ps1'
$cmd = 'powershell -NoProfile -ExecutionPolicy Bypass -File "' + $hookScript + '"'
if (Test-Path $settingsPath) {
  $fi = Get-Item -LiteralPath $settingsPath
  if ($fi.Length -gt 5MB) {
    $bigBak = $settingsPath + '.corrupt-' + (Get-Date -Format yyyyMMddHHmmss)
    Write-Host ("settings.json is " + $fi.Length + " bytes (corrupt); moving to " + $bigBak + " and restoring from the first backup")
    Move-Item -LiteralPath $settingsPath -Destination $bigBak
    $good = $settingsPath + '.before-ai-instructions'
    if (Test-Path $good) { Copy-Item -LiteralPath $good -Destination $settingsPath } else { [IO.File]::WriteAllText($settingsPath, '{}', $utf8) }
  }
  $raw = [IO.File]::ReadAllText($settingsPath, $utf8)
  if ([string]::IsNullOrWhiteSpace($raw)) { $s = [pscustomobject]@{} } else { $s = $raw | ConvertFrom-Json }
  $bak = $settingsPath + '.before-ai-instructions'
  if (-not (Test-Path $bak)) { Copy-Item -LiteralPath $settingsPath -Destination $bak }
} else { $s = [pscustomobject]@{} }

if (-not ($s.PSObject.Properties.Name -contains 'hooks')) { $s | Add-Member -NotePropertyName hooks -NotePropertyValue ([pscustomobject]@{}) }
if (-not ($s.hooks.PSObject.Properties.Name -contains 'UserPromptSubmit')) { $s.hooks | Add-Member -NotePropertyName UserPromptSubmit -NotePropertyValue @() }
$have = $false
foreach ($e in @($s.hooks.UserPromptSubmit)) { foreach ($h in @($e.hooks)) { if ($h.command -like '*ui_gate_reminder*') { $have = $true; if ($h.command -ne $cmd) { $h.command = $cmd } } } }
if (-not $have) {
  $entry = [pscustomobject]@{ hooks = @([pscustomobject]@{ type = 'command'; command = $cmd }) }
  $s.hooks.UserPromptSubmit = @($s.hooks.UserPromptSubmit) + $entry
}
# PreToolUse: one-time UI reminder when a UI-looking file/prefab is about to change (backs up the prompt router; never blocks)
$editScript = Join-Path $ClaudeHome 'pipeline-hooks\hooks\ui_edit_reminder.ps1'
$editCmd = 'powershell -NoProfile -ExecutionPolicy Bypass -File "' + $editScript + '"'
if (-not ($s.hooks.PSObject.Properties.Name -contains 'PreToolUse')) { $s.hooks | Add-Member -NotePropertyName PreToolUse -NotePropertyValue @() }
$haveEdit = $false
foreach ($e in @($s.hooks.PreToolUse)) { foreach ($h in @($e.hooks)) { if ($h.command -like '*ui_edit_reminder*') { $haveEdit = $true; if ($h.command -ne $editCmd) { $h.command = $editCmd } } } }
if (-not $haveEdit) {
  $entry = [pscustomobject]@{ matcher = 'Edit|Write|MultiEdit|NotebookEdit|mcp__.*(prefab|gameobject).*'; hooks = @([pscustomobject]@{ type = 'command'; command = $editCmd; timeout = 10 }) }
  $s.hooks.PreToolUse = @($s.hooks.PreToolUse) + $entry
}
# Observation hooks: plan creation (PreToolUse on update_plan) and screenshots / test runs / console reads (PostToolUse) feed skill routing automatically.
$obsScript = Join-Path $ClaudeHome 'pipeline-hooks\hooks\skill_observe_hook.ps1'
$obsCmd = 'powershell -NoProfile -ExecutionPolicy Bypass -File "' + $obsScript + '"'
function Register-ObserveHook($settings, [string]$event, [string]$matcher) {
  if (-not ($settings.hooks.PSObject.Properties.Name -contains $event)) { $settings.hooks | Add-Member -NotePropertyName $event -NotePropertyValue @() }
  $found = $false
  foreach ($e in @($settings.hooks.$event)) { foreach ($h in @($e.hooks)) { if ($h.command -like '*skill_observe_hook*') { $found = $true; if ($h.command -ne $obsCmd) { $h.command = $obsCmd }; if ($e.matcher -ne $matcher) { $e.matcher = $matcher } } } }
  if (-not $found) {
    $entry = [pscustomobject]@{ matcher = $matcher; hooks = @([pscustomobject]@{ type = 'command'; command = $obsCmd; timeout = 15 }) }
    $settings.hooks.$event = @($settings.hooks.$event) + $entry
  }
}
# SessionStart: re-inject the studio brain digest (owner rules) at startup / resume / clear / compact, so a restart or a fresh pull of the AI instructions always loads them.
$brainScript = Join-Path $ClaudeHome 'pipeline-hooks\hooks\studio_brain_digest.ps1'
$brainCmd = 'powershell -NoProfile -ExecutionPolicy Bypass -File "' + $brainScript + '"'
if (-not ($s.hooks.PSObject.Properties.Name -contains 'SessionStart')) { $s.hooks | Add-Member -NotePropertyName SessionStart -NotePropertyValue @() }
$haveBrain = $false
foreach ($e in @($s.hooks.SessionStart)) { foreach ($h in @($e.hooks)) { if ($h.command -like '*studio_brain_digest*') { $haveBrain = $true; if ($h.command -ne $brainCmd) { $h.command = $brainCmd } } } }
if (-not $haveBrain) {
  $entry = [pscustomobject]@{ matcher = 'startup|resume|clear|compact'; hooks = @([pscustomobject]@{ type = 'command'; command = $brainCmd; timeout = 10 }) }
  $s.hooks.SessionStart = @($s.hooks.SessionStart) + $entry
}
# Data-driven studio rules hook (studio_rules.json): detects owner corrections / automation gaps on UserPromptSubmit and enforces the retro gate on Stop
# (finishing is blocked until the lesson is written into the skills repo). studio_repo.txt tells the hook where the skills repo clone lives on this machine.
$rulesScript = Join-Path $ClaudeHome 'pipeline-hooks\hooks\studio_rules_hook.ps1'
try { [IO.File]::WriteAllText((Join-Path $ClaudeHome 'pipeline-hooks\hooks\studio_repo.txt'), $Repo, (New-Object Text.UTF8Encoding($false))) } catch {}
function Register-RulesHook($settings, [string]$event) {
  $cmdLine = 'powershell -NoProfile -ExecutionPolicy Bypass -File "' + $rulesScript + '" -Event ' + $event
  if (-not ($settings.hooks.PSObject.Properties.Name -contains $event)) { $settings.hooks | Add-Member -NotePropertyName $event -NotePropertyValue @() }
  $found = $false
  foreach ($e in @($settings.hooks.$event)) { foreach ($h in @($e.hooks)) { if ($h.command -like '*studio_rules_hook*') { $found = $true; if ($h.command -ne $cmdLine) { $h.command = $cmdLine } } } }
  if (-not $found) {
    $entry = [pscustomobject]@{ hooks = @([pscustomobject]@{ type = 'command'; command = $cmdLine; timeout = 15 }) }
    $settings.hooks.$event = @($settings.hooks.$event) + $entry
  }
}
Register-RulesHook $s 'UserPromptSubmit'
Register-RulesHook $s 'Stop'
Register-ObserveHook $s 'PreToolUse' '.*update_plan.*'
Register-ObserveHook $s 'PostToolUse' 'mcp__ai-game-developer__(screenshot|tests-run|console-get-logs).*|mcp__Claude_Browser__computer'
# Enforcement hooks (skill_enforce_hook.ps1): PostToolUse tracking, Stop/SubagentStop gate, SubagentStart UI contract.
$enfScript = Join-Path $ClaudeHome 'pipeline-hooks\hooks\skill_enforce_hook.ps1'
$enfCmd = 'powershell -NoProfile -ExecutionPolicy Bypass -File "' + $enfScript + '"'
function Register-EnforceHook($settings, [string]$event, [string]$matcher) {
  if (-not ($settings.hooks.PSObject.Properties.Name -contains $event)) { $settings.hooks | Add-Member -NotePropertyName $event -NotePropertyValue @() }
  $found = $false
  foreach ($e in @($settings.hooks.$event)) { foreach ($h in @($e.hooks)) { if ($h.command -like '*skill_enforce_hook*') { $found = $true; if ($h.command -ne $enfCmd) { $h.command = $enfCmd } } } }
  if (-not $found) {
    $entry = [pscustomobject]@{ hooks = @([pscustomobject]@{ type = 'command'; command = $enfCmd; timeout = 15 }) }
    if ($matcher) { $entry | Add-Member -NotePropertyName matcher -NotePropertyValue $matcher }
    $settings.hooks.$event = @($settings.hooks.$event) + $entry
  }
}
Register-EnforceHook $s 'PostToolUse' 'Skill|Edit|Write|MultiEdit|NotebookEdit|mcp__ai-game-developer__.*'
Register-EnforceHook $s 'Stop' ''
Register-EnforceHook $s 'SubagentStop' ''
Register-EnforceHook $s 'SubagentStart' ''
# Ink audit notifier: hands the agent the misaligned UI the Unity watcher found while the user plays (silent and free when nothing is pending).
$inkScript = Join-Path $ClaudeHome 'pipeline-hooks\hooks\ink_audit_notify.ps1'
$inkCmd = 'powershell -NoProfile -ExecutionPolicy Bypass -File "' + $inkScript + '"'
function Register-InkHook($settings, [string]$event, [string]$matcher) {
  if (-not ($settings.hooks.PSObject.Properties.Name -contains $event)) { $settings.hooks | Add-Member -NotePropertyName $event -NotePropertyValue @() }
  $found = $false
  foreach ($e in @($settings.hooks.$event)) { foreach ($h in @($e.hooks)) { if ($h.command -like '*ink_audit_notify*') { $found = $true; if ($h.command -ne $inkCmd) { $h.command = $inkCmd } } } }
  if (-not $found) {
    $entry = [pscustomobject]@{ hooks = @([pscustomobject]@{ type = 'command'; command = $inkCmd; timeout = 10 }) }
    if ($matcher) { $entry | Add-Member -NotePropertyName matcher -NotePropertyValue $matcher }
    $settings.hooks.$event = @($settings.hooks.$event) + $entry
  }
}
Register-InkHook $s 'PostToolUse' 'mcp__ai-game-developer__.*|Bash|Read|Edit|Write'
Register-InkHook $s 'UserPromptSubmit' ''
Register-InkHook $s 'Stop' ''
# Fail loudly if an installed hook script does not parse (a silent parse error once disabled the whole skill router).
foreach ($hs in @($hookScript, $brainScript, $rulesScript, $editScript, $obsScript, $inkScript, (Join-Path $ClaudeHome 'pipeline-hooks\hooks\skill_router_lib.ps1'), $enfScript)) {
  if (Test-Path -LiteralPath $hs) {
    $errs = $null; $tok = $null
    [void][Management.Automation.Language.Parser]::ParseFile($hs, [ref]$tok, [ref]$errs)
    if ($errs -and $errs.Count -gt 0) { Write-Host ("ERROR: hook script does not parse: " + $hs + " -> " + $errs[0].Message) -ForegroundColor Red; $hookParseFailed = $true }
    elseif (([IO.File]::ReadAllBytes($hs) | Where-Object { $_ -gt 127 } | Measure-Object).Count -gt 0) { Write-Host ("WARNING: hook script is not ASCII (PowerShell 5.1 may misread it): " + $hs) -ForegroundColor Yellow }
  }
}
$removed = @()
if ($s.PSObject.Properties.Name -contains 'skillOverrides') {
  foreach ($p in @($s.skillOverrides.PSObject.Properties)) {
    if ($p.Name -match '^(ui-|unity-ui$|mobile-hud-layout$|world-canvas-ui$|hotbar-inventory$|shop-skin-preview$)') { $s.skillOverrides.PSObject.Properties.Remove($p.Name); $removed += $p.Name }
  }
}
[IO.File]::WriteAllText($settingsPath, ($s | ConvertTo-Json -Depth 30), $utf8)
Write-Host ("settings.json: UserPromptSubmit UI-gate hook ok; un-hid {0} UI skills" -f $removed.Count)

if ($NoProjects) { exit 0 }

# ---------- 2. Unity projects: CLAUDE.md + .claude/ai-instructions.md + .claude/skills ----------
function Find-UnityProjects([string]$root, [int]$maxDepth) {
  $q = New-Object 'System.Collections.Generic.Queue[object]'
  $q.Enqueue(@($root, 0))
  while ($q.Count -gt 0) {
    $it = $q.Dequeue(); $d = $it[0]; $lvl = $it[1]
    if (Test-Path -LiteralPath (Join-Path $d 'ProjectSettings\ProjectVersion.txt')) { $d; continue }
    if ($lvl -ge $maxDepth) { continue }
    Get-ChildItem -LiteralPath $d -Directory -ErrorAction SilentlyContinue |
      Where-Object { $_.Name -notmatch '^(\.|Library$|Temp$|Logs$|Backup~|node_modules$|Packages$|Assets$)' } |
      ForEach-Object { $q.Enqueue(@($_.FullName, ($lvl + 1))) }
  }
}
$roots = @((Split-Path -Parent $Repo))
$pl = Join-Path $Repo 'data/projects.txt'
if (Test-Path $pl) {
  foreach ($l in Get-Content -LiteralPath $pl) { $t = $l.Trim(); if ($t -and -not $t.StartsWith('#') -and (Test-Path -LiteralPath $t)) { $roots += $t } }
}
$projects = @()
foreach ($r in ($roots | Select-Object -Unique)) { $projects += @(Find-UnityProjects $r 3) }
$projects = $projects | Where-Object { $_ -and ($_.TrimEnd('\') -ne $Repo.TrimEnd('\')) } | Select-Object -Unique

$agents = Join-Path $Repo 'AGENTS.md'
$skills = Join-Path $Repo 'skills'
$gate = @'
<!-- ai-instructions:begin (managed by Unity-AI-Instructions/sync.bat - do not edit) -->
@.claude/ai-instructions.md
UI work gate (always on): for ANY Unity UI task (button, text, label, popup, shop, tab, HUD, icon, prefab layout) FIRST load skill `ui-always` and the skills it names, follow them, and verify centring (<=1px) and text autofit/outline by script before reporting done. Read the reference game directly (MCP) when matching it. Never skip this, never wait for the user to remind you.
Skill routing (always on): at the start of every task match it against `.claude/skills/INDEX.md` (and the router hook hints) and load the matching skills with the Skill tool; apply them without being asked, drop them when the step ends.
Graphify: if `graphify-out/` exists and is fresh, prefer `graphify query/path/explain` over Read/Grep; fall back silently when missing or stale. Never install, never start the watcher yourself.
<!-- ai-instructions:end -->
'@
$giBegin = '# >>> ai-instructions managed ignore (Unity-AI-Instructions/sync.bat; rewritten on every sync, do not edit) >>>'
$giEnd = '# <<< ai-instructions managed ignore <<<'
function Get-ManagedIgnoreLines([string]$R) {
  # $R = Unity project path relative to the git root ('sub/' with trailing slash), or '' when the root is the Unity folder.
  $l = New-Object 'System.Collections.Generic.List[string]'
  $l.Add('# AI-synced files (skills, instruction copy): never push')
  $l.Add('/' + $R + '.claude/'); $l.Add('/' + $R + 'CLAUDE.local.md')
  $l.Add('/' + $R + 'Assets/_AiQa/'); $l.Add('/' + $R + 'Assets/_AiQa.meta')
  $l.Add('# Tool output and scratch folders: generated, never push')
  foreach ($d in 'Temp*/', 'output/', 'outputs/', 'work/', 'backup*/', '.agents/', '.publish-backup/') { $l.Add('/' + $d); if ($R) { $l.Add('/' + $R + $d) } }
  foreach ($d in 'graphify-out/', '.omc/', '__pycache__/', '.pytest_cache/') { $l.Add($d) }
  $l.Add('*.bak'); $l.Add('*.orig'); $l.Add('*.rej')
  $l.Add('# Generated docs (research dumps, staging copies, reports, QA screenshots/media); hand-written .md docs stay trackable')
  $docRoots = @('docs/'); if ($R) { $docRoots += ($R + 'docs/') }
  foreach ($b in $docRoots) {
    foreach ($d in 'research/', 'staging/', 'screenshots/', 'reports/', 'qa/', 'shots/', 'captures/') { $l.Add('/' + $b + $d) }
    foreach ($e in 'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'mov', 'webm', 'zip') { $l.Add('/' + $b + '**/*.' + $e) }
  }
  return $l.ToArray()
}
function Write-ManagedBlock([string]$path, [string[]]$lines) {
  $existing = ''
  if (Test-Path -LiteralPath $path) { $existing = [IO.File]::ReadAllText($path) }
  $nl = "`n"; if ($existing -match "`r`n") { $nl = "`r`n" }
  $block = ($giBegin + "`n" + ($lines -join "`n") + "`n" + $giEnd) -replace "`r?`n", $nl
  $re = '(?s)' + [regex]::Escape($giBegin) + '.*?' + [regex]::Escape($giEnd)
  if ($existing -match $re) { $new = [regex]::Replace($existing, $re, { param($m) $block }) }
  elseif ($existing.Length -eq 0) { $new = $block + $nl }
  else { $new = $existing.TrimEnd() + $nl + $nl + $block + $nl }
  if ($new -ne $existing) {
    $dir = Split-Path -Parent $path
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    [IO.File]::WriteAllText($path, $new, $utf8); return $true
  }
  return $false
}
function Ensure-ProjectIgnore([string]$proj) {
  # The Unity project's own .gitignore: append ONLY the missing private-file lines (never rewrite or reorder what the owner wrote). Present lines are left alone.
  $gi = Join-Path $proj '.gitignore'
  if (-not (Test-Path -LiteralPath $gi)) { return }
  $raw = [IO.File]::ReadAllText($gi)
  $have = @($raw -split "`r?`n" | ForEach-Object { $_.Trim() })
  $want = '/.claude/', '/CLAUDE.local.md', '/Assets/_AiQa/', '/Assets/_AiQa.meta'
  $missing = @($want | Where-Object { ($have -notcontains $_) -and ($have -notcontains $_.TrimStart('/')) })
  if ($missing.Count -eq 0) { return }
  $nl = "`n"; if ($raw -match "`r`n") { $nl = "`r`n" }
  $add = $nl + '# AI-Instructions private files (synced by Unity-AI-Instructions/sync.bat, never push)' + $nl + ($missing -join $nl) + $nl
  [IO.File]::WriteAllText($gi, $raw.TrimEnd() + $nl + $add, $utf8)
  Write-Host ('  project .gitignore: added ' + ($missing -join ' '))
}
function Update-ManagedIgnore([string]$proj) {
  $root = $proj.TrimEnd('\')
  while ($root -and -not (Test-Path -LiteralPath (Join-Path $root '.git'))) {
    $parent = Split-Path -Parent $root
    if (-not $parent -or $parent -eq $root) { $root = $null; break }
    $root = $parent
  }
  if (-not $root) { Write-Host '  ignore: no git repository above this project, skipped'; return }
  if (-not (Test-Path -LiteralPath (Join-Path $root '.git') -PathType Container)) { Write-Host '  ignore: .git is not a folder (worktree), skipped'; return }
  $rel = ''
  if ($proj.TrimEnd('\') -ne $root) { $rel = ($proj.TrimEnd('\').Substring($root.Length).TrimStart('\') -replace '\\', '/') + '/' }
  $lines = Get-ManagedIgnoreLines $rel
  # root differs from the Unity folder: managed block in the root .gitignore; same folder: local-only .git/info/exclude (the project's own .gitignore is never edited)
  if ($rel) { $target = Join-Path $root '.gitignore' } else { $target = Join-Path $root '.git\info\exclude' }
  if (Write-ManagedBlock $target $lines) { Write-Host ("  ignore block updated: " + $target) }
}
foreach ($p in $projects) {
  $cl = Join-Path $p '.claude'
  New-Item -ItemType Directory -Force -Path $cl | Out-Null
  Copy-Item -LiteralPath $agents -Destination (Join-Path $cl 'ai-instructions.md') -Force
  # Private by design: the managed block lives in CLAUDE.local.md (personal, git-ignored), never in the shared CLAUDE.md,
  # so teammates get a clean repo and only machines that cloned + ran sync.bat load the studio skills.
  $cm = Join-Path $p 'CLAUDE.local.md'
  $block = $gate
  if (Test-Path -LiteralPath (Join-Path $p 'AGENTS.md')) { $block = $gate -replace '@\.claude/ai-instructions\.md', "@AGENTS.md`n@.claude/ai-instructions.md" }
  $txt = ''
  if (Test-Path -LiteralPath $cm) {
    $txt = [IO.File]::ReadAllText($cm)
    if ($txt -match '(?s)<!-- ai-instructions:begin.*?<!-- ai-instructions:end -->') { $new = [regex]::Replace($txt, '(?s)<!-- ai-instructions:begin.*?<!-- ai-instructions:end -->', { param($m) $block }) }
    else { $new = $block + "`n`n" + $txt }
  } else { $new = $block + "`n" }
  if ($new -ne $txt) { [IO.File]::WriteAllText($cm, $new, $utf8) }
  # migrate: strip the old managed block from the shared CLAUDE.md so it is no longer a modified tracked file
  $shared = Join-Path $p 'CLAUDE.md'
  if (Test-Path -LiteralPath $shared) {
    $sraw = [IO.File]::ReadAllText($shared)
    $sre = '(?s)<!-- ai-instructions:begin.*?<!-- ai-instructions:end -->(\r?\n){0,2}'
    if ($sraw -match $sre) {
      $snew = [regex]::Replace($sraw, $sre, '')
      if ($snew.Trim().Length -eq 0) { Remove-Item -LiteralPath $shared -Force; Write-Host ('  removed empty shared CLAUDE.md (block moved to CLAUDE.local.md): ' + $p) }
      else { [IO.File]::WriteAllText($shared, $snew, $utf8); Write-Host ('  moved managed block from CLAUDE.md to CLAUDE.local.md: ' + $p) }
    }
  }
  # repo layout skills\<group>\<skill>; the project install stays FLAT (.claude\skills\<skill>)
  $skillDest = Join-Path $cl 'skills'
  foreach ($g in @(Get-ChildItem -Directory -LiteralPath $skills)) { foreach ($s in @(Get-ChildItem -Directory -LiteralPath $g.FullName)) { if (Test-Path -LiteralPath (Join-Path $s.FullName 'SKILL.md')) { & robocopy $s.FullName (Join-Path $skillDest $s.Name) /E /XD __pycache__ /NFL /NDL /NJH /NJS /NP | Out-Null } } }
  # Automatic UI audit tooling (skill ui-ink-audit): Editor-only scripts go to Assets/_AiQa/Editor of every Unity project that has uGUI/TMP; nobody copies files by hand.
  $qaSrc = Join-Path $Repo 'data\templates\unity-editor\AiQa'
  $manifest = Join-Path $p 'Packages\manifest.json'
  if ((Test-Path -LiteralPath $qaSrc) -and (Test-Path -LiteralPath (Join-Path $p 'Assets')) -and (Test-Path -LiteralPath $manifest) -and ([IO.File]::ReadAllText($manifest) -match 'com\.unity\.(ugui|textmeshpro)')) {
    $qaDst = Join-Path $p 'Assets\_AiQa\Editor'
    New-Item -ItemType Directory -Force -Path $qaDst | Out-Null
    # migrate: remove older hand-copied versions (same file names) so only one watcher runs
    Get-ChildItem -LiteralPath (Join-Path $p 'Assets') -Recurse -Depth 6 -Filter 'Qa_Ink*.cs' -ErrorAction SilentlyContinue |
      Where-Object { $_.Name -in @('Qa_InkDump.cs', 'Qa_InkWatcher.cs', 'Qa_InkFix.cs') } |
      Where-Object { $_.FullName -notlike '*\_AiQa\*' } | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force; Remove-Item -LiteralPath ($_.FullName + '.meta') -Force -ErrorAction SilentlyContinue; Write-Host ("  AiQa: removed old copy " + $_.FullName) }
    foreach ($f in Get-ChildItem -LiteralPath $qaSrc -Filter '*.cs.txt') {
      $target = Join-Path $qaDst ($f.Name -replace '\.txt$', '')
      $new = [IO.File]::ReadAllText($f.FullName)
      if (-not (Test-Path -LiteralPath $target) -or ([IO.File]::ReadAllText($target) -ne $new)) { [IO.File]::WriteAllText($target, $new, $utf8); Write-Host ("  AiQa installed: " + $target) }
    }
  }
  # Keep AI-managed files and tool junk out of git. Never touches the Unity project's own .gitignore.
  Ensure-ProjectIgnore $p
  Update-ManagedIgnore $p
  # Lint-Triggered Skills: engine + PostToolUse hook, project-local (.claude/ is git-ignored above)
  try { & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Repo 'tools\sync\install_project_lint.ps1') -Repo $Repo -Project $p | Out-Null; if ($LASTEXITCODE -ne 0) { Write-Host '  lint install FAILED (exit code ' + $LASTEXITCODE + ')' -ForegroundColor Yellow } } catch { Write-Host ("  lint install failed: " + $_.Exception.Message) -ForegroundColor Yellow }
  Write-Host ("project synced: " + $p)
}
if (-not $projects) { Write-Host 'no Unity projects found next to the repo (add roots to data/projects.txt)' }
exit 0
