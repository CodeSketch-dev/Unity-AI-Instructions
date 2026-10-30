# PreToolUse hook (Edit|Write|MultiEdit|NotebookEdit and Unity MCP asset/prefab/gameobject tools): once per session, when a UI-looking file or
# prefab is about to change, inject a reminder to load ui-always and measure. ASCII only. Never blocks (always exit 0).
[Console]::InputEncoding = [Text.Encoding]::UTF8
$raw = [Console]::In.ReadToEnd()
try { $j = $raw | ConvertFrom-Json } catch { exit 0 }
$tool = [string]$j.tool_name
$target = ''
try { $target = [string]$j.tool_input.file_path } catch {}
if (-not $target) { try { $target = [string]$j.tool_input.assetPath } catch {} }
if (-not $target) { try { $target = ($j.tool_input | ConvertTo-Json -Compress -Depth 4) } catch {} }
$isUi = ($target -match '(?i)\.prefab|popup|shop|hud|button|label|iap|gem_|_ui|[/\\]ui[/\\]|toast|tab_|card|icon|currency') -or ($tool -match '(?i)gameobject-component|assets-prefab|gameobject-modify')
if (-not $isUi) { exit 0 }
$sid = [string]$j.session_id
if (-not $sid) { $sid = 'nosession' }
$marker = Join-Path ([IO.Path]::GetTempPath()) ('ui_edit_reminder_' + ($sid -replace '[^A-Za-z0-9_-]', '') + '.flag')
if (Test-Path -LiteralPath $marker) { exit 0 }
try { Set-Content -LiteralPath $marker -Value '1' -Encoding ascii } catch {}
$m = 'UI edit detected. If skill ui-always (and ui-icon-label-layout, ui-center-alignment, ui-text-tmp, ui-button-anatomy) is not loaded in this session, load it NOW before this edit: icon + text/price = one centred HorizontalLayoutGroup, UI_TextAutoFit, press anim, then measure dx/dy <= 1 px and look at a Play screenshot before reporting done. Also keep vibe-coding-guardrails in mind.'
$o = @{ hookSpecificOutput = @{ hookEventName = 'PreToolUse'; additionalContext = $m } }
$o | ConvertTo-Json -Depth 5 -Compress
exit 0
