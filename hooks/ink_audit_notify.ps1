# Hook (PostToolUse / UserPromptSubmit / Stop): hands the agent the UI misalignments the Unity Qa_InkWatcher found while the user played.
# Reads <project>\Temp\InkAudit\pending.txt (written by the watcher), delivers it ONCE (moved to pending.sent.txt) and costs nothing when the file is absent.
# ASCII only.
$raw = [Console]::In.ReadToEnd()
$evt = ''; $cwd = (Get-Location).Path
try { $j = $raw | ConvertFrom-Json; $evt = $j.hook_event_name; if ($j.cwd) { $cwd = $j.cwd } } catch {}
$cands = @(Join-Path $cwd 'Temp\InkAudit\pending.txt')
foreach ($d in (Get-ChildItem -LiteralPath $cwd -Directory -ErrorAction SilentlyContinue)) { $cands += (Join-Path $d.FullName 'Temp\InkAudit\pending.txt') }
$file = $cands | Where-Object { Test-Path -LiteralPath $_ } | Sort-Object { (Get-Item -LiteralPath $_).LastWriteTime } -Descending | Select-Object -First 1
if (-not $file) { exit 0 }
$text = (Get-Content -LiteralPath $file -Raw -ErrorAction SilentlyContinue)
if (-not $text) { exit 0 }
Move-Item -LiteralPath $file -Destination ($file -replace 'pending\.txt$', 'pending.sent.txt') -Force -ErrorAction SilentlyContinue
$msg = "[InkAudit] The user is play-testing and the automatic UI audit found misaligned UI. Fix what is left on the SOURCE prefabs (skill ui-ink-audit; Qa_InkFix already applied what it could), then re-open the screen and confirm 0 fail. Do not ask the user.`n" + $text
if ($evt -eq 'Stop') { @{ decision = 'block'; reason = $msg } | ConvertTo-Json -Compress; exit 0 }
if (-not $evt) { $evt = 'PostToolUse' }
@{ hookSpecificOutput = @{ hookEventName = $evt; additionalContext = $msg } } | ConvertTo-Json -Compress -Depth 4
exit 0
