# Enforcement of skill use (ASCII only; never throws). Events:
#  PostToolUse  - tracks per session: UI edits, ui skill loaded, layout audit run.
#  Stop / SubagentStop - blocks (max 2 times per session) when UI was edited but no layout audit ran afterwards.
#  SubagentStart - injects the UI contract into every subagent.
[Console]::InputEncoding = [Text.Encoding]::UTF8
$raw = [Console]::In.ReadToEnd()
try { $j = $raw | ConvertFrom-Json } catch { exit 0 }
$ev = [string]$j.hook_event_name
$tool = [string]$j.tool_name
$sid = [string]$j.session_id
if (-not $sid) { $sid = 'nosession' }
$state = Join-Path ([IO.Path]::GetTempPath()) ('skill_enforce_' + ($sid -replace '[^A-Za-z0-9_-]', '') + '.json')
function Load-State { if (Test-Path -LiteralPath $state) { try { return Get-Content -Raw -LiteralPath $state | ConvertFrom-Json } catch {} } return [pscustomobject]@{ uiedit = $false; uiskill = $false; audit = $false; blocks = 0 } }
function Save-State($s) { try { ($s | ConvertTo-Json -Compress) | Set-Content -LiteralPath $state -Encoding ascii } catch {} }
function Emit([string]$evName, [string]$text) { @{ hookSpecificOutput = @{ hookEventName = $evName; additionalContext = $text } } | ConvertTo-Json -Depth 5 -Compress }

if ($ev -eq 'PostToolUse') {
  $s = Load-State
  $inp = ''
  try { $inp = ($j.tool_input | ConvertTo-Json -Compress -Depth 6) } catch {}
  $uiPath = '(?i)\.prefab|popup|shop|hud|button|label|iap|currency|_ui|[/\\]ui[/\\]|toast|tab_|card|icon'
  $changed = $false
  if ($tool -eq 'Skill') { if ($inp -match '(?i)ui-always|ui-center-alignment|ui-layout-audit') { $s.uiskill = $true; $changed = $true } }
  elseif ($tool -match '^(Edit|Write|MultiEdit|NotebookEdit)$') { $fp = ''; try { $fp = [string]$j.tool_input.file_path } catch {}; if ($fp -match $uiPath -and $fp -notmatch '(?i)\.(md|ps1|json|txt|py|bat)$') { $s.uiedit = $true; $s.audit = $false; $changed = $true } }
  elseif ($tool -match '(?i)gameobject-(modify|component-(add|modify|destroy)|create|duplicate|set-parent)|assets-prefab-(save|create)|assets-modify') { $s.uiedit = $true; $s.audit = $false; $changed = $true }
  elseif ($tool -match '(?i)script-execute') {
    if ($inp -match '(?i)Qa_UiAudit|UiAudit|textBounds') { $s.audit = $true; $changed = $true }
    elseif ($inp -match '(?i)(sizeDelta|anchoredPosition|offsetMin|offsetMax|anchorMin|anchorMax|fontSize|localScale)\s*[+\-]?=') { $s.uiedit = $true; $s.audit = $false; $changed = $true }
  }
  if ($changed) { Save-State $s }
  exit 0
}
elseif ($ev -eq 'Stop' -or $ev -eq 'SubagentStop') {
  $s = Load-State
  $active = $false
  try { $active = [bool]$j.stop_hook_active } catch {}
  if ($s.uiedit -and -not $s.audit -and -not $active -and [int]$s.blocks -lt 2) {
    $s.blocks = [int]$s.blocks + 1
    Save-State $s
    $reason = 'UI was edited in this session but no layout audit ran afterwards. Before finishing: load ui-always (+ ui-center-alignment, ui-layout-audit), run the layout audit (Qa_UiAudit.Run on the changed screens: text centred in the free gap between neighbouring icons/buttons, no overlap, >= 6 px padding on all sides, ScrollRect margin >= 12 px, outline on every text, readable font size), fix every violation at its shared source, re-capture and look at the screenshot. If the edit had no visible UI effect, say so explicitly in your final message.'
    @{ decision = 'block'; reason = $reason } | ConvertTo-Json -Compress
  }
  exit 0
}
elseif ($ev -eq 'SubagentStart') {
  Emit 'SubagentStart' 'UI contract (mandatory for any UI work you do): first read ui-always and the skills it lists (ui-center-alignment, ui-icon-label-layout, ui-text-tmp, ui-text-autofit-system, ui-style-rules, ui-button-anatomy, ui-layout-audit) from the skills folder; text is centred in the free gap between neighbouring icons/buttons (not the parent frame), never overlaps, has padding on all 4 sides, every text has the black outline, ScrollRects keep a margin to the board; after ANY UI change run the layout audit (Qa_UiAudit) and a Play screenshot, fix violations at once, and list the skills you read plus the measured numbers in your report. Deliver your report before your turn limit.'
  exit 0
}
exit 0
