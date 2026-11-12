# Install the lint engine into one Unity project and register the PostToolUse hook (project-local, git-ignored files only).
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File tools\install_project_lint.ps1 -Repo <this repo> -Project <unity project>
# Writes <Project>\.claude\lint\ (without tests) and <Project>\.claude\settings.local.json (hook entry, idempotent). ASCII only (PowerShell 5.1).
param(
  [Parameter(Mandatory=$true)][string]$Repo,
  [Parameter(Mandatory=$true)][string]$Project
)
$ErrorActionPreference = 'Stop'
$utf8 = New-Object Text.UTF8Encoding $false
$src = Join-Path $Repo 'lint'
$cl = Join-Path $Project '.claude'
$dst = Join-Path $cl 'lint'
if (-not (Test-Path -LiteralPath $src)) { Write-Host 'lint source missing'; exit 1 }
New-Item -ItemType Directory -Force -Path $dst | Out-Null
& robocopy $src $dst /MIR /XD tests __pycache__ /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { Write-Host 'robocopy failed'; exit 1 }

$settingsPath = Join-Path $cl 'settings.local.json'
$cmd = 'python "$CLAUDE_PROJECT_DIR/.claude/lint/run_lint.py" --hook'
if (Test-Path -LiteralPath $settingsPath) {
  $raw = [IO.File]::ReadAllText($settingsPath, $utf8)
  if ([string]::IsNullOrWhiteSpace($raw)) { $s = [pscustomobject]@{} } else { $s = $raw | ConvertFrom-Json }
} else { $s = [pscustomobject]@{} }
if (-not ($s.PSObject.Properties.Name -contains 'hooks')) { $s | Add-Member -NotePropertyName hooks -NotePropertyValue ([pscustomobject]@{}) }
if (-not ($s.hooks.PSObject.Properties.Name -contains 'PostToolUse')) { $s.hooks | Add-Member -NotePropertyName PostToolUse -NotePropertyValue @() }
$have = $false
foreach ($e in @($s.hooks.PostToolUse)) { foreach ($h in @($e.hooks)) { if ($h.command -like '*lint/run_lint.py*') { $have = $true; if ($h.command -ne $cmd) { $h.command = $cmd } } } }
if (-not $have) {
  $entry = [pscustomobject]@{ matcher = 'Edit|Write|MultiEdit'; hooks = @([pscustomobject]@{ type = 'command'; command = $cmd; timeout = 10 }) }
  $s.hooks.PostToolUse = @($s.hooks.PostToolUse) + $entry
}
[IO.File]::WriteAllText($settingsPath, ($s | ConvertTo-Json -Depth 12), $utf8)
Write-Host ('lint installed: ' + $dst)
