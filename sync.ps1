[CmdletBinding()]
param(
    [switch] $SkipPull
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = $PSScriptRoot
$sourcePath = Join-Path $repoRoot "AGENTS.md"

if (-not (Test-Path -LiteralPath $sourcePath))
{
    throw "Không tìm thấy file nguồn: $sourcePath"
}

if (-not $SkipPull)
{
    git -C $repoRoot pull --ff-only

    if ($LASTEXITCODE -ne 0)
    {
        throw "Không thể cập nhật repository bằng git pull --ff-only."
    }
}

function Install-InstructionFile
{
    param(
        [Parameter(Mandatory)]
        [string] $DestinationPath
    )

    $destinationDirectory = Split-Path -Parent $DestinationPath

    New-Item `
        -ItemType Directory `
        -Path $destinationDirectory `
        -Force | Out-Null

    if (Test-Path -LiteralPath $DestinationPath)
    {
        $sourceHash = (Get-FileHash -LiteralPath $sourcePath).Hash
        $destinationHash = (Get-FileHash -LiteralPath $DestinationPath).Hash

        if ($sourceHash -eq $destinationHash)
        {
            Write-Host "Đã đồng bộ sẵn: $DestinationPath"
            return
        }

        $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $backupPath = "$DestinationPath.backup-$timestamp"

        Copy-Item `
            -LiteralPath $DestinationPath `
            -Destination $backupPath

        Write-Host "Đã backup: $backupPath"
    }

    Copy-Item `
        -LiteralPath $sourcePath `
        -Destination $DestinationPath `
        -Force

    Write-Host "Đã cập nhật: $DestinationPath"
}

$codexPath = Join-Path $env:USERPROFILE ".codex\AGENTS.md"
$claudePath = Join-Path $env:USERPROFILE ".claude\CLAUDE.md"

Install-InstructionFile -DestinationPath $codexPath
Install-InstructionFile -DestinationPath $claudePath

function Install-Skills
{
    param(
        [Parameter(Mandatory)]
        [string] $DestinationRoot
    )

    $skillsSource = Join-Path $repoRoot "skills"

    if (-not (Test-Path -LiteralPath $skillsSource))
    {
        return
    }

    # Chi ghi de cac skill co trong repo; khong dong vao folder "synced" cua app.
    foreach ($skill in Get-ChildItem -LiteralPath $skillsSource -Directory)
    {
        $target = Join-Path $DestinationRoot $skill.Name

        if (Test-Path -LiteralPath $target)
        {
            Remove-Item -LiteralPath $target -Recurse -Force
        }

        New-Item -ItemType Directory -Path $DestinationRoot -Force | Out-Null
        Copy-Item -LiteralPath $skill.FullName -Destination $target -Recurse -Force
        Write-Host "Đã cập nhật skill: $target"
    }
}

Install-Skills -DestinationRoot (Join-Path $env:USERPROFILE ".claude\skills")
Install-Skills -DestinationRoot (Join-Path $env:USERPROFILE ".agents\skills")

Write-Host ""
Write-Host "Hoàn tất đồng bộ Codex và Claude."
Write-Host "Hãy mở session mới để instructions được nạp lại."