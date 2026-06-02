param(
    [Parameter(Mandatory = $true)]
    [string]$User,

    [int]$Concurrency = 5,

    [int]$MinScore = 45,

    [switch]$SkipPull,

    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
$venvPip = Join-Path $repoRoot ".venv\Scripts\pip.exe"

function Resolve-Tool {
    param(
        [string[]]$Names,
        [string[]]$FallbackPaths,
        [string]$InstallMessage
    )

    foreach ($name in $Names) {
        $command = Get-Command $name -ErrorAction SilentlyContinue

        if ($command) {
            return $command.Source
        }
    }

    foreach ($path in $FallbackPaths) {
        if (Test-Path $path) {
            return $path
        }
    }

    throw $InstallMessage
}

Set-Location $repoRoot

if (-not $SkipPull) {
    $git = Resolve-Tool `
        -Names @("git") `
        -FallbackPaths @(
            "C:\Program Files\Git\cmd\git.exe",
            "C:\Program Files\Git\bin\git.exe",
            "C:\Program Files (x86)\Git\cmd\git.exe"
        ) `
        -InstallMessage "Git was not found. Install Git from https://git-scm.com/downloads and reopen PowerShell."

    & $git pull origin main
}

if (-not (Test-Path $venvPython)) {
    $python = Resolve-Tool `
        -Names @("python", "py") `
        -FallbackPaths @() `
        -InstallMessage "Python was not found. Install Python from https://www.python.org/downloads/ and tick 'Add Python to PATH'."

    if ((Split-Path -Leaf $python) -eq "py.exe") {
        & $python -3 -m venv .venv
    }
    else {
        & $python -m venv .venv
    }
}

if (-not $SkipInstall) {
    & $venvPip install -r requirements.txt
    & $venvPython -m playwright install chromium
}

& $venvPython .\ParallelCrawler.py --user $User --concurrency $Concurrency --min-score $MinScore
