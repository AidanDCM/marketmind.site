#Requires -Version 5.1
<#
.SYNOPSIS
  Stop the MarketMind API container and document rollback steps.

.USAGE
  .\scripts\rollback_marketmind.ps1
  .\scripts\rollback_marketmind.ps1 -KeepVolumes

.NOTES
  This stops the running container. To roll back CODE, check out a prior git SHA
  and re-run deploy_marketmind.ps1. Database and logs persist in Docker volumes
  unless you pass -RemoveVolumes (destructive).
#>
param(
    [switch]$KeepVolumes = $true,
    [switch]$RemoveVolumes
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> Stopping MarketMind API"
docker compose down
if ($LASTEXITCODE -ne 0) { throw "docker compose down failed" }

if ($RemoveVolumes) {
    Write-Host "==> Removing volumes marketmind-data and marketmind-logs (DESTRUCTIVE)"
    docker volume rm marketmind-site_marketmind-data marketmind-site_marketmind-logs 2>$null
    docker volume rm marketmind_data marketmind_logs 2>$null
} elseif (-not $KeepVolumes) {
    Write-Host "WARN: -KeepVolumes is default; data preserved in Docker volumes."
}

Write-Host @"

Rollback checklist:
  1. git log --oneline -10          # find last known-good commit
  2. git checkout <sha> -- .        # restore code (or git switch <branch>)
  3. python -m pytest -q            # verify locally before redeploy
  4. .\scripts\deploy_marketmind.ps1

Data backup (before destructive rollback):
  docker run --rm -v marketmind-site_marketmind-data:/data -v ${PWD}:/backup alpine \
    tar czf /backup/marketmind-data-backup.tgz -C /data .

Logs backup:
  docker run --rm -v marketmind-site_marketmind-logs:/logs -v ${PWD}:/backup alpine \
    tar czf /backup/marketmind-logs-backup.tgz -C /logs .

"@
