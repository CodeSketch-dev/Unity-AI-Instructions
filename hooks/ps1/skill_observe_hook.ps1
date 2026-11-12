# PreToolUse (plan creation) + PostToolUse (screenshots, tests, console) hook: turns observations into automatic skill use.
# ASCII only. Never blocks (always exit 0). Output is additionalContext for the model.
[Console]::InputEncoding = [Text.Encoding]::UTF8
. "$PSScriptRoot\skill_router_lib.ps1"
$raw = [Console]::In.ReadToEnd()
try { $j = $raw | ConvertFrom-Json } catch { exit 0 }
$ev = [string]$j.hook_event_name
$tool = [string]$j.tool_name
$sid = [string]$j.session_id
if (-not $sid) { $sid = 'nosession' }
$sidSafe = ($sid -replace '[^A-Za-z0-9_-]', '')
$msg = ''

function Throttled([string]$key, [int]$seconds) {
  $f = Join-Path ([IO.Path]::GetTempPath()) ('skill_observe_' + $sidSafe + '_' + $key + '.flag')
  if (Test-Path -LiteralPath $f) { if (((Get-Date) - (Get-Item -LiteralPath $f).LastWriteTime).TotalSeconds -lt $seconds) { return $true } }
  try { Set-Content -LiteralPath $f -Value '1' -Encoding ascii } catch {}
  return $false
}

if ($ev -eq 'PreToolUse' -and $tool -like '*update_plan*') {
  $text = ''
  try { $text = (($j.tool_input.items | ForEach-Object { [string]$_.content }) -join ' . ') } catch {}
  $skills = Get-RoutedSkills $text 5
  if ($skills.Count -gt 0) {
    $hint = Get-RoutedHint $text 5
    if ($hint -like 'no strong match*') { $msg = 'Plan skill routing: ' + $hint + ' - read skills/INDEX.md for a better fit or proceed with the general rules; never invent a skill name.' }
    else { $msg = 'Plan skill routing: these plan steps match skills - load the ones each step needs BEFORE starting that step (no user prompt needed): ' + ($skills -join ', ') + '. Any UI step: ui-always first. Keep vibe-coding-guardrails in mind.' }
  }
}
elseif ($ev -eq 'PostToolUse') {
  $resp = ''
  try { $resp = ($j.tool_response | ConvertTo-Json -Compress -Depth 6) } catch { try { $resp = [string]$j.tool_response } catch {} }
  if ($tool -match '(?i)screenshot|computer|browser') {
    if (-not (Throttled 'shot' 120)) {
      $msg = 'Screenshot captured: inspect it NOW for UI defects (text off-centre vs neighbouring icons/buttons, overlap, clipped or tiny text, misaligned edges, leftover placeholder art). If you see any, immediately load ui-always + ui-center-alignment (+ ui-icon-label-layout / ui-text-tmp), fix the layout, re-measure and re-capture until it passes. Do not just report it and do not wait for the user.'
    }
  }
  elseif ($tool -match '(?i)tests-run') {
    if ($resp -match '(?i)"Status":"Failed"|FailedTests":[1-9]') {
      $skills = Get-RoutedSkills ($resp.Substring(0, [Math]::Min($resp.Length, 6000))) 6
      $msg = 'Test failures detected: do not just report them. For each failure decide: caused by your change (fix now with systematic-debugging) or pre-existing/balance (say which, with evidence). Skills suggested by the failing names: ' + ($skills -join ', ') + '. UI/prefab test failures: apply ui-always.'
    }
  }
  elseif ($tool -match '(?i)console-get-logs') {
    if ($resp -match '\[UIAudit\]') {
      $msg = 'UI AUDIT WARNINGS in the Console ([UIAudit]): the editor audit found layout defects on a popup. Do not just report them: load ui-always + ui-center-alignment, fix each violation at its shared source (prefab/builder), re-open the popup in Play and confirm the warning is gone.'
    }
    elseif ($resp -match '(?i)"LogType":"(Error|Exception)"') {
      $msg = 'Console errors present: triage with unity-log-triage / systematic-debugging, separate your own errors from MCP-tool script errors, fix root causes of game errors now.'
    }
  }
}
if (-not $msg) { exit 0 }
$o = @{ hookSpecificOutput = @{ hookEventName = $ev; additionalContext = $msg } }
$o | ConvertTo-Json -Depth 5 -Compress
exit 0
