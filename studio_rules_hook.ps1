# Generic data-driven studio hook. Registered for UserPromptSubmit and Stop by tools/sync_claude_setup.ps1 (usage: -Event UserPromptSubmit | Stop).
# Rules live in studio_rules.json next to this script. ASCII only (PowerShell 5.1).
# - UserPromptSubmit: strips diacritics from the owner's prompt, applies the rules, injects the matching texts, arms the retro gate (flag 'correction')
#   and logs corrections to ~/.claude/studio_corrections.log; a correction that repeats an earlier one is escalated ("build a hook / audit, not prose").
# - Stop: the retro gate. If a correction was detected this session and the skills repo (skills/, AGENTS.md, STUDIO-BRAIN-DIGEST.md, studio_rules.json)
#   has neither a new commit nor uncommitted changes since the correction, finishing is blocked (max 2 times) so the lesson is written down.
param([string]$Event = 'UserPromptSubmit')
[Console]::InputEncoding = [Text.Encoding]::UTF8
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$raw = [Console]::In.ReadToEnd()
$j = $null
try { $j = $raw | ConvertFrom-Json } catch { exit 0 }
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$rulesPath = Join-Path $here 'studio_rules.json'
if (-not (Test-Path -LiteralPath $rulesPath)) { exit 0 }
$rules = (Get-Content -LiteralPath $rulesPath -Raw | ConvertFrom-Json).rules

$sid = 'nosession'
if ($j.session_id) { $sid = [string]$j.session_id }
$statePath = Join-Path ([IO.Path]::GetTempPath()) ('studio_state_' + ($sid -replace '[^A-Za-z0-9_-]', '') + '.json')
$state = @{ correction = $false; head = ''; blocks = 0; log = @() }
if (Test-Path -LiteralPath $statePath) { try { $o = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json; $state.correction = [bool]$o.correction; $state.head = [string]$o.head; $state.blocks = [int]$o.blocks } catch {} }
function Save-State { try { ($state | ConvertTo-Json -Depth 4) | Set-Content -LiteralPath $statePath -Encoding ASCII } catch {} }

$repo = ''
$repoFile = Join-Path $here 'studio_repo.txt'
if (Test-Path -LiteralPath $repoFile) { $repo = (Get-Content -LiteralPath $repoFile -Raw).Trim() }
function Get-RepoHead { if ($repo -and (Test-Path -LiteralPath $repo)) { try { (& git -C $repo rev-parse HEAD 2>$null | Select-Object -First 1) } catch { '' } } else { '' } }
function Get-RepoDirty { if ($repo -and (Test-Path -LiteralPath $repo)) { try { @(& git -C $repo status --porcelain -- skills AGENTS.md STUDIO-BRAIN-DIGEST.md studio_rules.json 2>$null).Count } catch { 0 } } else { 0 } }

function Remove-Diacritics([string]$s) {
  $d = $s.Normalize([Text.NormalizationForm]::FormD)
  $sb = New-Object Text.StringBuilder
  foreach ($c in $d.ToCharArray()) { if ([Globalization.CharUnicodeInfo]::GetUnicodeCategory($c) -ne [Globalization.UnicodeCategory]::NonSpacingMark) { [void]$sb.Append($c) } }
  return $sb.ToString().Replace([string][char]0x0111, 'd').Replace([string][char]0x0110, 'D').ToLowerInvariant()
}

if ($Event -eq 'UserPromptSubmit') {
  $prompt = ''
  if ($j.prompt) { $prompt = [string]$j.prompt }
  if (-not $prompt) { exit 0 }
  $norm = Remove-Diacritics $prompt
  $out = New-Object Collections.Generic.List[string]
  foreach ($r in @($rules)) {
    if ($r.event -ne 'UserPromptSubmit') { continue }
    if ($norm -match $r.match) {
      if ($r.inject) { [void]$out.Add([string]$r.inject) }
      if ($r.flag -eq 'correction') {
        if (-not $state.correction) { $state.head = Get-RepoHead }
        $state.correction = $true
        $state.blocks = 0
        # repeat detection: significant tokens shared with earlier corrections
        $logPath = Join-Path $env:USERPROFILE '.claude\studio_corrections.log'
        $tokens = @($norm -split '[^a-z0-9]+' | Where-Object { $_.Length -ge 5 } | Select-Object -Unique)
        $repeat = $false
        if (Test-Path -LiteralPath $logPath) {
          foreach ($line in (Get-Content -LiteralPath $logPath -Tail 200)) {
            $ln = @($line -split '[^a-z0-9]+' | Where-Object { $_.Length -ge 5 } | Select-Object -Unique)
            $shared = @($tokens | Where-Object { $ln -contains $_ }).Count
            if ($shared -ge 4) { $repeat = $true; break }
          }
        }
        try { Add-Content -LiteralPath $logPath -Value (($norm -replace '\s+', ' ').Substring(0, [Math]::Min(400, $norm.Length))) -Encoding ASCII } catch {}
        if ($repeat) { [void]$out.Add('REPEAT CORRECTION: the owner already corrected something very similar before. Prose rules failed. Build an ENFORCEABLE mechanism now (audit script that fails, hook rule in studio_rules.json, build-time check) and prove it with a dry run.') }
      }
    }
  }
  Save-State
  if ($out.Count -gt 0) { ($out -join "`n") }
  exit 0
}

if ($Event -eq 'Stop') {
  if ($j.stop_hook_active) { exit 0 }
  if (-not $state.correction) { exit 0 }
  $head = Get-RepoHead
  $dirty = Get-RepoDirty
  if (($head -and $head -ne $state.head) -or $dirty -gt 0) { $state.correction = $false; $state.blocks = 0; Save-State; exit 0 }
  if ($state.blocks -ge 2) { $state.correction = $false; Save-State; exit 0 }
  $state.blocks = $state.blocks + 1
  Save-State
  $reason = 'RETRO GATE: the owner corrected you or asked for a standing rule in this session, but the skills repo (Unity-AI-Instructions: skills/, AGENTS.md, STUDIO-BRAIN-DIGEST.md, studio_rules.json) has no new commit or change. Write the lesson into the matching generic skill / digest / audit rule, run publish.bat, then finish. If nothing reusable was learned, say so in one line.'
  (@{ decision = 'block'; reason = $reason } | ConvertTo-Json -Compress)
  exit 0
}
exit 0
