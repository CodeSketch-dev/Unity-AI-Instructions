# Publish skill/instruction updates: lint + index + router -> sync (live locally) -> commit -> pull -> (conflict: keep upstream, save my commits as a patch) -> sync -> push.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish.ps1 [-Message "skills: ..."] [-NoPush]
# Exit codes: 0 ok, 2 conflict (upstream taken, local commits saved under .publish-backup\<timestamp>, re-apply them then run again), 1 other error.
param([string]$Message = '', [switch]$NoPush)
$ErrorActionPreference = 'Continue'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo
function Step($t) { Write-Host ("== " + $t) -ForegroundColor Cyan }
function Run-Sync { Step 'sync.bat'; & cmd.exe /c ('"' + (Join-Path $repo 'sync.bat') + '" /nopause /nopull') | Select-Object -Last 6 }

# 1. lint / index / router (needs python; skipped with a note when missing)
Step 'lint, index, router'
$py = (Get-Command python -ErrorAction SilentlyContinue)
if ($py) {
  & python tools\skill_index.py skills | Set-Content -Encoding utf8 skills\INDEX.md
  & python tools\build_skill_router.py skills skill_router.json
  $lint = & python tools\skill_lint.py skills 2>&1
  $lint | Select-Object -Last 3
} else { Write-Host 'python not found: skipped lint/index/router (committed router/index are used)' -ForegroundColor Yellow }

# 2. live locally first
Run-Sync

# 3. commit
Step 'commit'
$trailer = "`n`nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
git add -A
$dirty = git status --porcelain
if ($dirty) {
  if (-not $Message) { $Message = 'skills: update ' + (Get-Date -Format 'yyyy-MM-dd HH:mm') + ' (' + $env:COMPUTERNAME + ')' }
  git commit -q -m ($Message + $trailer)
  Write-Host ('committed: ' + $Message)
} else { Write-Host 'nothing to commit' }

# 4. pull (rebase). Conflict -> keep upstream, save my commits for re-applying.
Step 'pull'
git fetch -q origin
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
$upstream = "origin/$branch"
$ahead = [int](git rev-list --count "$upstream..HEAD" 2>$null)
$behind = [int](git rev-list --count "HEAD..$upstream" 2>$null)
Write-Host ("ahead=$ahead behind=$behind")
if ($behind -gt 0) {
  $ts = Get-Date -Format 'yyyyMMdd-HHmmss'
  $bk = Join-Path $repo (".publish-backup\" + $ts)
  if ($ahead -gt 0) { New-Item -ItemType Directory -Force -Path $bk | Out-Null; git format-patch -q -o $bk "$upstream..HEAD" | Out-Null }
  git pull --rebase -q origin $branch
  if ($LASTEXITCODE -ne 0) {
    Write-Host 'CONFLICT while rebasing: discarding my local commits, taking upstream.' -ForegroundColor Red
    git rebase --abort 2>$null
    git reset --hard $upstream | Out-Null
    Write-Host ("My commits were saved as patches in: " + $bk) -ForegroundColor Yellow
    Write-Host 'Re-apply them on top of upstream (merge both intents, e.g. git am --3way or by hand), then run publish again.' -ForegroundColor Yellow
    Run-Sync
    exit 2
  }
  Run-Sync
}

# 5. push
if (-not $NoPush -and $ahead -gt 0 -or (-not $NoPush -and $dirty)) {
  Step 'push'
  git push -q origin $branch
  if ($LASTEXITCODE -ne 0) { Write-Host 'push failed' -ForegroundColor Red; exit 1 }
  Write-Host 'pushed'
}
exit 0
