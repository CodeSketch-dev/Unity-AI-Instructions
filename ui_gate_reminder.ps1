# UserPromptSubmit hook (skill router): maps the user's prompt to the skills that must be loaded,
# so skills are applied automatically even when listed as name-only. ASCII only; Vietnamese via \u escapes.
[Console]::InputEncoding = [Text.Encoding]::UTF8
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$raw = [Console]::In.ReadToEnd()
$prompt = ''
try { $prompt = ($raw | ConvertFrom-Json).prompt } catch {}
if (-not $prompt) { $prompt = '' }

$ui = '(?i)button|text\b|label|popup|shop|\btab|icon|\bui\b|hud|prefab|canvas|align|font|tmp|atlas|settings|banner|layout|price|pulse|anim\b|animation|currency bar|gem\b|cash\b|sprite|card\b|toast|panel|n\u00fat|ch\u1eef|b\u1ea3ng|giao di\u1ec7n|c\u0103n'
$routes = @(
 @{ re='(?i)\bads?\b|reward(ed)?|interstitial|admob|applovin|qu\u1ea3ng c\u00e1o'; s='ads-popup-flow ads-layer-generic monetization-integration native-ad-beside-popup' },
 @{ re='(?i)\biap\b|purchase|gem pack|cash pack|in-app'; s='iap-catalog unity-iap-port monetization-integration' },
 @{ re='(?i)econom|income|progression|rebirth|balance|kinh t\u1ebf|c\u00e2n b\u1eb1ng'; s='economy-progression-design economy-loop-archetypes auto-balance-game' },
 @{ re='(?i)\bbots?\b|\bnpc|enemy|enemies|boss|chase'; s='bots-as-players bot-brain-waypoints bot-path-follow-smoothing npc-bots-and-enemies simple-boss-patrol-chase' },
 @{ re='(?i)combat|damage|health|hit detection|\battack'; s='combat-health-status combat-hit-detection-rule' },
 @{ re='(?i)camera|third.person|freelook|occlu'; s='freelook-third-person-camera camera-occlusion-fade intro-camera-flyover' },
 @{ re='(?i)audio|sfx|music|ambience|\u00e2m thanh'; s='game-audio-system sfx-variation-ducking ambience-layers' },
 @{ re='(?i)perf|fps|draw call|batch|profil|lag\b|optimi|atlas|t\u1ed1i \u01b0u'; s='mobile-perf-audit profiling-evidence world-batching-culling device-tier-policy token-efficient-workflow' },
 @{ re='(?i)\bsave\b|persist|data block|playerprefs|l\u01b0u'; s='data-persistence-facts save-and-crash-safety data-block-template' },
 @{ re='(?i)tutorial|h\u01b0\u1edbng d\u1eabn'; s='tutorial-phase-system' },
 @{ re='(?i)pause|offline|settings popup'; s='settings-pause-offline gameplay-pause-input-gate' },
 @{ re='(?i)skin|character|rig\b|animator|emote|nametag|avatar'; s='character-skin-system character-rig-and-animation-contract character-emotes-nametags cosmetic-slot-providers modular-avatar-parts' },
 @{ re='(?i)\bpets?\b|\begg|hotbar|inventory|backpack|loot|rarity'; s='hotbar-inventory item-data-driven-behavior loot-rarity-tables recipe-add-skin-or-item' },
 @{ re='(?i)quest|achievement|daily|retention|timer|event'; s='recipe-quests-achievements recipe-retention-timers static-bus-events' },
 @{ re='(?i)minigame|scene flow|scene load|boot'; s='minigame-registration recipe-add-minigame scene-flow-loading boot-sequence-setup' },
 @{ re='(?i)\bpool|spawn|\bvfx|particle|\bfx\b'; s='pool-everything pooled-ranked-fx vfx-budget-rules vfx-material-recipes currency-spread-fx' },
 @{ re='(?i)shader|material|lighting|urp|bake|vertex color'; s='one-material-world-shader mobile-urp-lighting-baseline vertex-color-baking scene-optimizer-bake' },
 @{ re='(?i)\bmesh|merge|combine|procedural'; s='mesh-merge-baker mesh-scene-combiner procedural-mesh-generator' },
 @{ re='(?i)joystick|touch|input|kcc|movement|jump|climb|ladder|obby|checkpoint|respawn|teleport'; s='mobile-input-controls kcc-character-controller kcc-advanced-movement ladder-climb checkpoint-respawn teleporter-pad' },
 @{ re='(?i)locali[sz]|language|glyph|ng\u00f4n ng\u1eef'; s='localization-pipeline ui-localization' },
 @{ re='(?i)analytics|log event'; s='analytics-events-taxonomy' },
 @{ re='(?i)\bbuild\b|\bapk|\baab\b|release|projectsettings'; s='mobile-build-release unity-batch-build projectsettings-baseline' },
 @{ re='(?i)\bbug|error|exception|null ref|console|crash|debug|l\u1ed7i'; s='unity-debugging unity-log-triage' },
 @{ re='(?i)\btest|\bqa\b|playtest|validat|verify|ki\u1ec3m tra'; s='qa-playmode-smoke qa-editmode-validators qa-static-checks unity-qa-playtest senior-tester rule-qa-verdicts' },
 @{ re='(?i)clone|reference|\bport\b|copy asset|knife|steal|gi\u1ed1ng'; s='reference-port rule-port-not-invent asset-transfer-closure game-clone-recon ui-clone clone-ip-safety' },
 @{ re='(?i)\bmcp\b|editor tool|builder|prefab|scene'; s='unity-mcp-workflow editor-tool-authoring rule-editor-tool-safety editor-lane-single-writer unity-fast-iteration' },
 @{ re='(?i)subagent|agent team|parallel'; s='agent-team-protocol multi-agent-coexistence' },
 @{ re='(?i)singleton|factory|scriptable|config|state machine'; s='factory-singleton-template mono-singleton-template config-and-factory-authoring config-driven-feature state-machine-template' },
 @{ re='(?i)async|unitask|cancel'; s='async-cancellation' },
 @{ re='(?i)zone|biome|level design|world canvas|world label'; s='zone-level-design world-label-recipes world-canvas-ui culling-group-distance' },
 @{ re='(?i)polish|juice|game feel'; s='game-feel-polish gameplay-polish-recipes' }
)
$set = New-Object 'System.Collections.Generic.List[string]'
foreach ($r in $routes) { if ($prompt -match $r.re) { foreach ($n in $r.s.Split(' ')) { if (-not $set.Contains($n)) { $set.Add($n) } } } }
# Data-driven routing over EVERY skill (tools/build_skill_router.py builds skill_router.json from the skills' own names/descriptions/triggers),
# so new skills are picked up automatically. Vietnamese is matched after diacritics are stripped.
$router = Join-Path $PSScriptRoot 'skill_router.json'
if (Test-Path -LiteralPath $router) {
  try {
    $rj = Get-Content -Raw -LiteralPath $router | ConvertFrom-Json
    $norm = $prompt.ToLowerInvariant().Normalize([Text.NormalizationForm]::FormD)
    $sbn = New-Object Text.StringBuilder
    foreach ($ch in $norm.ToCharArray()) { if ([Globalization.CharUnicodeInfo]::GetUnicodeCategory($ch) -ne 'NonSpacingMark') { [void]$sbn.Append($ch) } }
    $ascii = $sbn.ToString().Replace([string][char]0x0111, 'd')
    $extra = ''
    foreach ($vp in $rj.vi.PSObject.Properties) { if ($ascii -match ('(?<![a-z])' + [regex]::Escape($vp.Name) + '(?![a-z])')) { $extra += ' ' + $vp.Value } }
    $tokens = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($mm in [regex]::Matches(($ascii + ' ' + $extra), '[a-z][a-z0-9]{2,}')) { [void]$tokens.Add($mm.Value) }
    $scored = New-Object 'System.Collections.Generic.List[object]'
    foreach ($sk in $rj.skills) {
      $sc = 0
      foreach ($w in $sk.w) { if ($tokens.Contains($w)) { $sc += 3 } }
      foreach ($w in $sk.t) { if ($ascii -like ('*' + $w + '*')) { $sc += 3 } }
      foreach ($w in $sk.d) { if ($tokens.Contains($w)) { $sc += 1 } }
      if ($sc -ge 3) { $scored.Add([pscustomobject]@{ n = $sk.n; sc = $sc }) }
    }
    foreach ($x in ($scored | Sort-Object sc -Descending | Select-Object -First 12)) { if (-not $set.Contains($x.n)) { $set.Add($x.n) } }
  } catch {}
}
$isUi = $prompt -match $ui

$m = 'Skill router: before acting, load (Skill tool, or Read .claude/skills/<name>/SKILL.md) the skills that match this task. Skills are never optional and the user will not ask for them. Always keep skill vibe-coding-guardrails in mind (inspect before assuming, narrow searches, verify before claiming).'
if ($isUi) { $m += ' UI TASK: FIRST load ui-always (it names the required UI skills), then measure centring (<=1px), text autofit and black outline by script + screenshot before saying done.' }
if ($set.Count -gt 0) { $m += ' Matched skills (load the ones the current step needs, drop them when the step ends): ' + (($set | Select-Object -First 18) -join ', ') + '.' }
$m += ' New feature or behavior change: superpowers brainstorming first. Bug: systematic-debugging first. Always finish with done-means-wired + verification-before-completion.'
$o = @{ hookSpecificOutput = @{ hookEventName = 'UserPromptSubmit'; additionalContext = $m } }
$o | ConvertTo-Json -Depth 5 -Compress
exit 0
