# Shared skill routing (ASCII only). Dot-source: . "$PSScriptRoot\skill_router_lib.ps1"; Get-RoutedSkills $text $max
# Scores free text (English or Vietnamese) against every skill in skill_router.json (built by tools/build_skill_router.py).
# Returns @{ strong = bool; names = string[]; closest = string }. Matches are capped at 5. strong = best score >= 6.
# Negative triggers: a skill's optional "x" list (frontmatter `not:`) subtracts 3 per phrase found in the prompt.
function Get-RoutedMatch([string]$text, [int]$max = 5) {
  $max = [Math]::Max(1, [Math]::Min($max, 5))
  $res = [pscustomobject]@{ strong = $false; names = @(); closest = ''; top = 0 }
  $router = Join-Path $PSScriptRoot 'skill_router.json'
  if (-not (Test-Path -LiteralPath $router) -or [string]::IsNullOrWhiteSpace($text)) { return $res }
  try {
    $rj = Get-Content -Raw -LiteralPath $router | ConvertFrom-Json
    $norm = $text.ToLowerInvariant().Normalize([Text.NormalizationForm]::FormD)
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
      if ($sk.PSObject.Properties['x'] -and $sc -gt 0) { foreach ($w in $sk.x) { if ($ascii -like ('*' + $w + '*')) { $sc -= 3 } } }
      if ($sc -ge 3) { $scored.Add([pscustomobject]@{ n = $sk.n; sc = $sc }) }
    }
    $top = @($scored | Sort-Object sc -Descending | Select-Object -First $max)
    if ($top.Count -gt 0) {
      $res.names = @($top | ForEach-Object { $_.n })
      $res.strong = ($top[0].sc -ge 6)
      $res.closest = $top[0].n; $res.top = $top[0].sc
    }
  } catch {}
  return $res
}

# Hint text for hooks: names when strong, else 'no strong match; closest: X', else empty.
function Get-RoutedHint([string]$text, [int]$max = 5) {
  $m = Get-RoutedMatch $text $max
  if ($m.names.Count -eq 0) { return '' }
  if ($m.strong) { return ($m.names -join ', ') }
  return 'no strong match; closest: ' + $m.closest
}

# Backwards compatible: names only (now capped at 5, negative triggers applied).
function Get-RoutedSkills([string]$text, [int]$max = 10) {
  return @((Get-RoutedMatch $text $max).names)
}

function Get-RoutedSkillsLegacy([string]$text, [int]$max = 10) {
  $router = Join-Path $PSScriptRoot 'skill_router.json'
  if (-not (Test-Path -LiteralPath $router) -or [string]::IsNullOrWhiteSpace($text)) { return @() }
  try {
    $rj = Get-Content -Raw -LiteralPath $router | ConvertFrom-Json
    $norm = $text.ToLowerInvariant().Normalize([Text.NormalizationForm]::FormD)
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
    return @($scored | Sort-Object sc -Descending | Select-Object -First $max | ForEach-Object { $_.n })
  } catch { return @() }
}
