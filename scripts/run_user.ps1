param(
    [Parameter(Mandatory = $true)]
    [string]$User,

    [int]$Concurrency = 5,

    [int]$MinScore = 45
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

Set-Location $repoRoot
python .\ParallelCrawler.py --user $User --concurrency $Concurrency --min-score $MinScore
