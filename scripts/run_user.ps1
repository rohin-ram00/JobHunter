param(
    [Parameter(Mandatory = $true)]
    [string]$User,

    [int]$Concurrency = 5,

    [int]$MinScore = 45,

    [switch]$SkipPull,

    [switch]$SkipInstall,

    [switch]$Quiet,

    [switch]$NoMerge
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

$crawlerArgs = @(".\ParallelCrawler.py", "--user", $User, "--concurrency", $Concurrency, "--min-score", $MinScore)

if ($Quiet) {
    $crawlerArgs += "--quiet"
}

if ($NoMerge) {
    $crawlerArgs += "--no-merge"
}

& $venvPython $crawlerArgs

if (-not $NoMerge -and -not $SkipPull) {
    $jobDataBank = Join-Path $repoRoot "data" "JobDataBank.ods"
    
    if (Test-Path $jobDataBank) {
        $git = Resolve-Tool `
            -Names @("git") `
            -FallbackPaths @(
                "C:\Program Files\Git\cmd\git.exe",
                "C:\Program Files\Git\bin\git.exe",
                "C:\Program Files (x86)\Git\cmd\git.exe"
            ) `
            -InstallMessage "Git was not found."

        Write-Host "`nChecking for JobDataBank.ods changes..."
        $status = & $git status --porcelain
        
        if ($status -match "data/JobDataBank.ods" -or $status -match "data\\JobDataBank.ods") {
            Write-Host "Changes detected in JobDataBank.ods. Committing and merging..."
            & $git add "data/JobDataBank.ods"
            & $git commit -m "Auto-update JobDataBank.ods from $User run $(Get-Date -Format 'yyyy-MM-dd HHmmss')"
            Write-Host "Changes committed successfully."
        }
        else {
            Write-Host "No changes in JobDataBank.ods."
        }
    }
}