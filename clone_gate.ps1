# Automation gates for Stop events (ASCII only; never throws). stdin = hook JSON. Prints a block decision JSON or nothing.
# Gate 1: clone / match-the-original task without frame extraction. Gate 2: delegated task failed and was swallowed.
# Gate 3: completion claim while docs/owner-requests.md still has OPEN / IN PROGRESS rows.
[Console]::InputEncoding = [Text.Encoding]::UTF8
$raw = [Console]::In.ReadToEnd()
try { $j = $raw | ConvertFrom-Json } catch { exit 0 }
if ($j.stop_hook_active) { exit 0 }
$sid = [string]$j.session_id; if (-not $sid) { $sid = 'nosession' }
$stateFile = Join-Path ([IO.Path]::GetTempPath()) ('clone_gate_' + ($sid -replace '[^A-Za-z0-9_-]', '') + '.json')
$st = @{ g1 = 0; g2 = 0; g3 = 0 }
if (Test-Path -LiteralPath $stateFile) { try { $o = Get-Content -Raw -LiteralPath $stateFile | ConvertFrom-Json; $st.g1 = [int]$o.g1; $st.g2 = [int]$o.g2; $st.g3 = [int]$o.g3 } catch {} }
function Block([string]$key, [string]$reason) { $st[$key] = $st[$key] + 1; try { ($st | ConvertTo-Json -Compress) | Set-Content -LiteralPath $stateFile -Encoding ascii } catch {}; (@{ decision = 'block'; reason = $reason } | ConvertTo-Json -Compress); exit 0 }
$tp = [string]$j.transcript_path
$userText = ''; $asstRaw = ''; $lastAsst = ''
if ($tp -and (Test-Path -LiteralPath $tp)) {
  foreach ($ln in (Get-Content -LiteralPath $tp -Tail 6000 -ErrorAction SilentlyContinue)) {
    if ($ln.Contains('"type":"user"')) { try { $o = $ln | ConvertFrom-Json; $c = $o.message.content; if ($c -is [string]) { $userText += ' ' + $c } else { foreach ($b in $c) { if ($b.type -eq 'text') { $userText += ' ' + [string]$b.text } } } } catch {} }
    elseif ($ln.Contains('"type":"assistant"')) { $asstRaw += $ln; try { $o = $ln | ConvertFrom-Json; foreach ($b in $o.message.content) { if ($b.type -eq 'text' -and $b.text) { $lastAsst = [string]$b.text } } } catch {} }
  }
}
$isRef = $userText -match '(?i)clone|giong game goc|game goc|ban goc|original|reference|video|ffmpeg|youtube|so frame|tach frame|giong 100|y het'
$ran = $asstRaw -match '(?i)clone_frames\.py|ffmpeg'
$claims = $lastAsst -match '(?i)da xong|hoan tat|da sua|da kiem|verified|done\b|completed|\u0111\u00e3 xong|ho\u00e0n t\u1ea5t|\u0111\u00e3 s\u1eeda|\u0111\u00e3 ki\u1ec3m'
if ($isRef -and -not $ran -and $st.g1 -lt 2) { Block 'g1' 'Reference/clone task but no frame extraction ran in this session. Follow skill clone-research-autonomy section 0 NOW, without asking: python -I clone_frames.py coarse|dense|moments (whole-video sheets, then dense/zoomed key moments), LOOK at the sheets, write SPEC/COVERAGE, compare with your Play recording. If you compared another way, say exactly how and show evidence paths. Never claim parity without it.' }
if ($asstRaw -match '(?i)codex_task|submit_task|create_task' -and $asstRaw -match '(?i)timed out|Request timed out' -and -not $ran -and $st.g2 -lt 1) { Block 'g2' 'A delegated task (Codex/hub) timed out in this session and no replacement work ran. Check the expected output files (ls); if missing, do the work yourself now with the deterministic tools (clone_frames.py, Play recorder) and tell the owner plainly that the delegation failed and what you did instead. Never report a delegated task as done or running without evidence on disk.' }
$cwd = [string]$j.cwd; $led = ''; $dir = $cwd
for ($i = 0; $i -lt 4 -and $dir; $i++) { $cand = Join-Path $dir 'docs\owner-requests.md'; if (Test-Path -LiteralPath $cand) { $led = $cand; break }; $dir = Split-Path -Parent $dir }
if ($led -and $claims -and $st.g3 -lt 1) {
  $open = @(Select-String -LiteralPath $led -Pattern '\|\s*(OPEN|IN PROGRESS)' -ErrorAction SilentlyContinue)
  if ($open.Count -gt 0) { Block 'g3' ('docs/owner-requests.md still has ' + $open.Count + ' OPEN / IN PROGRESS row(s) but your final message claims completion. Either finish them now (continue working, no questions) or state plainly in the final message which rows are NOT done and why. Close a row only with evidence (paths, numbers, screenshots).') }
}
exit 0
