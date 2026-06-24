#Requires -Version 5.1
<#
.SYNOPSIS
  Build and start the MarketMind API via Docker Compose, then verify health.

.USAGE
  .\scripts\deploy_marketmind.ps1
  .\scripts\deploy_marketmind.ps1 -ApiToken "your-long-random-token"

.PRECHECKS
  - Docker Desktop running
  - Port 8000 free (or change compose mapping)
#>
param(
    [string]$ApiToken = $env:MARKETMIND_API_TOKEN
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> MarketMind deploy starting in $Root"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "docker not found. Install Docker Desktop first."
}

if ($ApiToken) {
    $env:MARKETMIND_API_TOKEN = $ApiToken
    Write-Host "==> MARKETMIND_API_TOKEN set for this session"
} else {
    Write-Host "WARN: MARKETMIND_API_TOKEN not set — API will be open on localhost only."
}

Write-Host "==> docker compose build"
docker compose build
if ($LASTEXITCODE -ne 0) { throw "docker compose build failed" }

Write-Host "==> docker compose up -d"
docker compose up -d
if ($LASTEXITCODE -ne 0) { throw "docker compose up failed" }

$healthUrl = "http://127.0.0.1:8000/health"
$deadline = (Get-Date).AddSeconds(60)
$ok = $false
while ((Get-Date) -lt $deadline) {
    try {
        $resp = Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 5
        if ($resp.status -eq "ok") { $ok = $true; break }
    } catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $ok) {
    docker compose logs --tail 50 api
    throw "Health check failed at $healthUrl"
}

Write-Host "==> Health OK: $($resp | ConvertTo-Json -Compress)"

Write-Host "==> Running deploy verification"
python "$Root\scripts\verify_marketmind_deploy.py"
if ($LASTEXITCODE -ne 0) { throw "Deploy verification failed" }

Write-Host "==> Operator readiness (API)"
python "$Root\scripts\check_operator_readiness.py" --api
if ($LASTEXITCODE -ne 0) { throw "Operator readiness check failed" }

Write-Host "==> Deploy complete. Data volume: marketmind-data | Logs volume: marketmind-logs"
