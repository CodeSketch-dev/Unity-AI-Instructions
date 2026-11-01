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
foreach ($hs in @($hookScript, $editScript, $obsScript, $inkScript, (Join-Path $ClaudeHome 'pipeline-hooks\hooks\skill_router_lib.ps1'), $enfScript)) {
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
$pl = Join-Path $Repo 'projects.txt'
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
Graphify (always on): at session start load skill `graphify-workflow`: bootstrap Graphify if missing (install, build graph, single watcher), restart a dead watcher, and prefer `graphify query/path/explain` over reading code; never ask the user.
<!-- ai-instructions:end -->
'@
foreach ($p in $projects) {
  $cl = Join-Path $p '.claude'
  New-Item -ItemType Directory -Force -Path $cl | Out-Null
  Copy-Item -LiteralPath $agents -Destination (Join-Path $cl 'ai-instructions.md') -Force
  $cm = Join-Path $p 'CLAUDE.md'
  $block = $gate
  if (Test-Path -LiteralPath (Join-Path $p 'AGENTS.md')) { $block = $gate -replace '@\.claude/ai-instructions\.md', "@AGENTS.md`n@.claude/ai-instructions.md" }
  if (Test-Path -LiteralPath $cm) {
    $txt = [IO.File]::ReadAllText($cm)
    if ($txt -match '(?s)<!-- ai-instructions:begin.*?<!-- ai-instructions:end -->') { $new = [regex]::Replace($txt, '(?s)<!-- ai-instructions:begin.*?<!-- ai-instructions:end -->', { param($m) $block }) }
    else { $new = $block + "`n`n" + $txt }
  } else { $new = $block + "`n" }
  if ($new -ne $txt) { [IO.File]::WriteAllText($cm, $new, $utf8) }
  & robocopy $skills (Join-Path $cl 'skills') /E /XD __pycache__ /NFL /NDL /NJH /NJS /NP | Out-Null
  # Automatic UI audit tooling (skill ui-ink-audit): Editor-only scripts go to Assets/_AiQa/Editor of every Unity project that has uGUI/TMP; nobody copies files by hand.
  $qaSrc = Join-Path $Repo 'templates\unity-editor\AiQa'
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
  Write-Host ("project synced: " + $p)
}
if (-not $projects) { Write-Host 'no Unity projects found next to the repo (add roots to projects.txt)' }
exit 0
