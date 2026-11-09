# SessionStart hook (startup | resume | clear | compact): re-injects the owner's standing rules so every new session / restart / compaction
# starts with the studio brain loaded. Reads the installed digest + the live UI REFLEXES section of AGENTS.md. ASCII only (PowerShell 5.1).
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$digest = Join-Path $here 'STUDIO-BRAIN-DIGEST.md'
if (Test-Path -LiteralPath $digest) { Get-Content -LiteralPath $digest -Raw }
$agents = Join-Path $here 'AGENTS.md'
if (Test-Path -LiteralPath $agents) {
  $lines = Get-Content -LiteralPath $agents
  $out = @(); $on = $false
  foreach ($l in $lines) {
    if ($l -match '^## UI REFLEXES') { $on = $true }
    elseif ($on -and $l -match '^## ') { break }
    if ($on) { $out += $l }
  }
  if ($out.Count -gt 0) { "--- AGENTS.md: UI REFLEXES (live copy) ---"; $out }
}
"Project memory: read the project's AGENTS.md / CLAUDE.md, docs/owner-requests.md (OPEN rows) and docs/feedback-notes.md before acting."
