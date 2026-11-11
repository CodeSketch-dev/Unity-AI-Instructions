# One-time setup of Meshy AI Studio on a new machine.
#   powershell -ExecutionPolicy Bypass -File setup.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

python -m pip install -r requirements.txt

# Decoder (third-party meshy-ai-to-stl): cloned here, never committed (see .gitignore).
$vendor = Join-Path $PSScriptRoot "docs\vendor\meshy-ai-to-stl"
if (-not (Test-Path $vendor)) {
    New-Item -ItemType Directory -Force (Split-Path $vendor) | Out-Null
    git clone https://github.com/ChesterTheCatt/meshy-ai-to-stl.git $vendor
}
powershell -ExecutionPolicy Bypass -File (Join-Path $vendor "setup-vendor.ps1")

python -m pytest -q
Write-Host "`nNext: put accounts in a .txt (email|password or email|password|recovery_email|totp_secret) and call the import_accounts MCP tool, then register the MCP server (README.md)."
