# UserPromptSubmit hook (skill router): maps the user's prompt to the skills that must be loaded,
# so skills are applied automatically even when listed as name-only. ASCII only; Vietnamese via \u escapes.
[Console]::InputEncoding = [Text.Encoding]::UTF8
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$raw = [Console]::In.ReadToEnd()
$prompt = ''
try { $prompt = ($raw | ConvertFrom-Json).prompt } catch {}
if (-not $prompt) { $prompt = '' }

$ui = '(?i)button|text\b|label|popup|shop|\btab|icon|\bui\b|hud|prefab|canvas|align|font|tmp|atlas|settings|banner|layout|price|currency bar|nút|chữ|bảng|giao diện|căn'
$routes = @(
 @{ re='(?i)\bads?\b|reward(ed)?|interstitial|admob|applovin|quảng cáo'; s='ads-popup-flow ads-layer-generic monetization-integration native-ad-beside-popup' },
 @{ re='(?i)\biap\b|purchase|gem pack|cash pack|in-app'; s='iap-catalog unity-iap-port monetization-integration' },
 @{ re='(?i)econom|income|progression|rebirth|balance|kinh tế|cân bằng'; s='economy-progression-design economy-loop-archetypes auto-balance-game' },
 @{ re='(?i)\bbots?\b|\bnpc|enemy|enemies|boss|chase'; s='bots-as-players bot-brain-waypoints bot-path-follow-smoothing npc-bots-and-enemies simple-boss-patrol-chase' },
 @{ re='(?i)combat|damage|health|hit detection|\battack'; s='combat-health-status combat-hit-detection-rule' },
 @{ re='(?i)camera|third.person|freelook|occlu'; s='freelook-third-person-camera camera-occlusion-fade intro-camera-flyover' },
 @{ re='(?i)audio|sfx|music|ambience|âm thanh'; s='game-audio-system sfx-variation-ducking ambience-layers' },
 @{ re='(?i)perf|fps|draw call|batch|profil|lag\b|optimi|atlas|tối ưu'; s='mobile-perf-audit profiling-evidence world-batching-culling device-tier-policy token-efficient-workflow' },
 @{ re='(?i)\bsave\b|persist|data block|playerprefs|lưu'; s='data-persistence-facts save-and-crash-safety data-block-template' },
 @{ re='(?i)tutorial|hướng dẫn'; s='tutorial-phase-system' },
 @{ re='(?i)pause|offline|settings popup'; s='settings-pause-offline gameplay-pause-input-gate' },
 @{ re='(?i)skin|character|rig\b|animator|emote|nametag|avatar'; s='character-skin-system character-rig-and-animation-contract character-emotes-nametags cosmetic-slot-providers modular-avatar-parts' },
 @{ re='(?i)\bpets?\b|\begg|hotbar|inventory|backpack|loot|rarity'; s='hotbar-inventory item-data-driven-behavior loot-rarity-tables recipe-add-skin-or-item' },
 @{ re='(?i)quest|achievement|daily|retention|timer|event'; s='recipe-quests-achievements recipe-retention-timers static-bus-events' },
 @{ re='(?i)minigame|scene flow|scene load|boot'; s='minigame-registration recipe-add-minigame scene-flow-loading boot-sequence-setup' },
 @{ re='(?i)\bpool|spawn|\bvfx|particle|\bfx\b'; s='pool-everything pooled-ranked-fx vfx-budget-rules vfx-material-recipes currency-spread-fx' },
 @{ re='(?i)shader|material|lighting|urp|bake|vertex color'; s='one-material-world-shader mobile-urp-lighting-baseline vertex-color-baking scene-optimizer-bake' },
 @{ re='(?i)\bmesh|merge|combine|procedural'; s='mesh-merge-baker mesh-scene-combiner procedural-mesh-generator' },
 @{ re='(?i)joystick|touch|input|kcc|movement|jump|climb|ladder|obby|checkpoint|respawn|teleport'; s='mobile-input-controls kcc-character-controller kcc-advanced-movement ladder-climb checkpoint-respawn teleporter-pad' },
 @{ re='(?i)locali[sz]|language|glyph|ngôn ngữ'; s='localization-pipeline ui-localization' },
 @{ re='(?i)analytics|log event'; s='analytics-events-taxonomy' },
 @{ re='(?i)\bbuild\b|\bapk|\baab\b|release|projectsettings'; s='mobile-build-release unity-batch-build projectsettings-baseline' },
 @{ re='(?i)\bbug|error|exception|null ref|console|crash|debug|lỗi'; s='unity-debugging unity-log-triage' },
 @{ re='(?i)\btest|\bqa\b|playtest|validat|verify|kiểm tra'; s='qa-playmode-smoke qa-editmode-validators qa-static-checks unity-qa-playtest senior-tester rule-qa-verdicts' },
 @{ re='(?i)clone|reference|\bport\b|copy asset|knife|steal|giống'; s='reference-port rule-port-not-invent asset-transfer-closure game-clone-recon ui-clone clone-ip-safety' },
 @{ re='(?i)\bmcp\b|editor tool|builder|prefab|scene'; s='unity-mcp-workflow editor-tool-authoring rule-editor-tool-safety editor-lane-single-writer unity-fast-iteration' },
 @{ re='(?i)subagent|agent team|parallel'; s='agent-team-protocol multi-agent-coexistence' },
 @{ re='(?i)singleton|factory|scriptable|config|state machine'; s='factory-singleton-template mono-singleton-template config-and-factory-authoring config-driven-feature state-machine-template' },
 @{ re='(?i)async|unitask|cancel'; s='async-cancellation' },
 @{ re='(?i)zone|biome|level design|world canvas|world label'; s='zone-level-design world-label-recipes world-canvas-ui culling-group-distance' },
 @{ re='(?i)polish|juice|game feel'; s='game-feel-polish gameplay-polish-recipes' }
)
$set = New-Object 'System.Collections.Generic.List[string]'
foreach ($r in $routes) { if ($prompt -match $r.re) { foreach ($n in $r.s.Split(' ')) { if (-not $set.Contains($n)) { $set.Add($n) } } } }
$isUi = $prompt -match $ui

$m = 'Skill router: before acting, load (Skill tool, or Read .claude/skills/<name>/SKILL.md) the skills that match this task. Skills are never optional and the user will not ask for them.'
if ($isUi) { $m += ' UI TASK: FIRST load ui-always (it names the required UI skills), then measure centring (<=1px), text autofit and black outline by script + screenshot before saying done.' }
if ($set.Count -gt 0) { $m += ' Matched skills (load the ones the current step needs, drop them when the step ends): ' + (($set | Select-Object -First 14) -join ', ') + '.' }
$m += ' New feature or behavior change: superpowers brainstorming first. Bug: systematic-debugging first. Always finish with done-means-wired + verification-before-completion.'
$o = @{ hookSpecificOutput = @{ hookEventName = 'UserPromptSubmit'; additionalContext = $m } }
$o | ConvertTo-Json -Depth 5 -Compress
exit 0
