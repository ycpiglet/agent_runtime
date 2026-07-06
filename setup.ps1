# agent_runtime one-shot setup (Windows) — run from the repo root after clone:
#   .\setup.ps1
# If script execution is blocked:
#   powershell -ExecutionPolicy Bypass -File setup.ps1
$ErrorActionPreference = "Stop"

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
if (-not $py) {
    Write-Host "Python >= 3.10 is required: https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

& $py.Source scripts/bootstrap_dev_env.py --apply --ssh-push

if (Get-Command gh -ErrorAction SilentlyContinue) {
    gh auth status *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "GitHub CLI is not authenticated - starting 'gh auth login'..."
        gh auth login
    }
} else {
    Write-Host "GitHub CLI (gh) is not installed: https://cli.github.com (needed for issue/PR automation)"
}

Write-Host ""
Write-Host "setup: done. Details: docs/DEV-ENVIRONMENT.md"
