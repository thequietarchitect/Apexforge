[CmdletBinding()]
param(
    [ValidateSet("all", "p7", "p8", "p9", "p10")]
    [string]$Phase = "all",

    [switch]$ListOnly,

    [string]$RepositoryRoot
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $scriptPath = $MyInvocation.MyCommand.Path

    if ([string]::IsNullOrWhiteSpace($scriptPath)) {
        throw "Unable to determine the PowerShell script location."
    }

    $RepositoryRoot = Split-Path -Parent $scriptPath
}

$RepositoryRoot = (Resolve-Path -LiteralPath $RepositoryRoot).Path
$harnessPath = Join-Path $RepositoryRoot "apexforge\regression_harness.py"

if (-not (Test-Path -LiteralPath $harnessPath -PathType Leaf)) {
    throw "Python regression harness not found: $harnessPath"
}

$arguments = @(
    $harnessPath,
    "--repository-root",
    $RepositoryRoot,
    "--phase",
    $Phase
)

if ($ListOnly) {
    $arguments += "--list"
}

Write-Host "Running ApexForge regression harness..."
Write-Host "Repository: $RepositoryRoot"
Write-Host "Phase:      $Phase"
Write-Host ""

& py @arguments
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    throw "ApexForge regression harness failed with exit code $exitCode."
}

Write-Host ""
Write-Host "ApexForge regression harness passed."
exit 0