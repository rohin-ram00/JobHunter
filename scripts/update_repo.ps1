$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot

Set-Location $repoRoot

Write-Host ""
Write-Host "======================================="
Write-Host "      JOBHUNTER AUTO UPDATE"
Write-Host "======================================="
Write-Host ""

try {

    Write-Host "[1/4] Pulling latest repository..."
    git pull origin main

    Write-Host ""
    Write-Host "[2/4] Staging files..."
    git add .

    Write-Host ""
    Write-Host "[3/4] Creating commit..."

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

    git commit -m "Auto update $timestamp" 2>$null

    if ($LASTEXITCODE -ne 0) {

        Write-Host ""
        Write-Host "No changes detected."

    }
    else {

        Write-Host ""
        Write-Host "Commit created."

    }

    Write-Host ""
    Write-Host "[4/4] Pushing to GitHub..."
    git push origin main

    Write-Host ""
    Write-Host "======================================="
    Write-Host " Repository successfully updated"
    Write-Host "======================================="
    Write-Host ""

}
catch {

    Write-Host ""
    Write-Host "======================================="
    Write-Host " UPDATE FAILED"
    Write-Host "======================================="
    Write-Host ""

    Write-Host $_

}

pause