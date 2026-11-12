# Usage: powershell -NoProfile -File skill_route.ps1 "<one-line task>"  -> prints the matched skill names (router data), for subagents/tools without a prompt hook. ASCII only.
param([Parameter(Position = 0, ValueFromRemainingArguments = $true)][string[]]$Task)
$text = ($Task -join ' ')
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$json = @{ prompt = $text } | ConvertTo-Json -Compress
$out = $json | & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $here 'ui_gate_reminder.ps1')
try {
  $ctx = ($out | ConvertFrom-Json).hookSpecificOutput.additionalContext
  $m = [regex]::Match($ctx, 'Matched skills[^:]*: ([^.]+)\.')
  if ($m.Success) { 'Matched skills: ' + $m.Groups[1].Value } else { 'No strong skill match; use skills/INDEX.md' }
  if ($ctx -match 'UI TASK') { 'UI TASK: read ui-always first, then measure centring and take a Play screenshot.' }
} catch { 'router unavailable; read skills/INDEX.md' }
