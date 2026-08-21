$ErrorActionPreference='Stop'

$repo=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$cli=Join-Path $repo 'apexforge\apexforge_cli.py'
$py='C:\Users\corte\.venvs\apexforge-p39\Scripts\python.exe'

if(-not (Test-Path -LiteralPath $cli -PathType Leaf)){throw 'STOP: apexforge_cli.py missing'}
if(-not (Test-Path -LiteralPath $py -PathType Leaf)){throw 'STOP: Python venv missing'}

$candidates=@(
'apexforge\fixtures\p11_1b\manifest_entry',
'examples\T1Demo',
'examples\P11Validation'
)

$project=$null
$relativeProject=$null
foreach($relative in $candidates){
    $candidate=Join-Path $repo $relative
    if(-not (Test-Path -LiteralPath $candidate -PathType Container)){continue}
    if(-not (Test-Path -LiteralPath (Join-Path $candidate 'apexforge.json') -PathType Leaf)){continue}
    if(@(Get-ChildItem -LiteralPath $candidate -Recurse -File -Filter '*.apex').Count -eq 0){continue}
    $gitPath=$relative.Replace('\','/')
    $tracked=@(git -C $repo ls-files -- "$gitPath/**")
    if($LASTEXITCODE -ne 0 -or $tracked.Count -eq 0){continue}
    $project=$candidate
    $relativeProject=$gitPath
    break
}
if($null -eq $project){throw 'STOP: no tracked repository-resident .apex acceptance project found'}

function Get-ProjectSnapshot {
    param([string]$Root)
    return @(
        Get-ChildItem -LiteralPath $Root -Recurse -File |
        Sort-Object FullName |
        ForEach-Object {
            $relative=$_.FullName.Substring($Root.Length).TrimStart('\').Replace('\','/')
            "$relative=$((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)"
        }
    )
}

$gitBefore=@(git -C $repo status --porcelain=v1 --untracked-files=all)
$projectBefore=@(Get-ProjectSnapshot -Root $project)

$tmp1=Join-Path $env:TEMP 'apexforge_p11_11f_tap_check_1.txt'
$tmp2=Join-Path $env:TEMP 'apexforge_p11_11f_tap_check_2.txt'

Push-Location -LiteralPath $project
try {
    & $py $cli tap-check . *> $tmp1
    $exit1=$LASTEXITCODE
    & $py $cli tap-check . *> $tmp2
    $exit2=$LASTEXITCODE
} finally {
    Pop-Location
}

if($exit1 -ne 0){Get-Content -LiteralPath $tmp1; throw "STOP: first PowerShell tap-check exited $exit1"}
if($exit2 -ne 0){Get-Content -LiteralPath $tmp2; throw "STOP: repeated PowerShell tap-check exited $exit2"}

$out1=[IO.File]::ReadAllText($tmp1)
$out2=[IO.File]::ReadAllText($tmp2)
Remove-Item -LiteralPath $tmp1,$tmp2 -Force -ErrorAction SilentlyContinue

if($out1 -ne $out2){throw 'STOP: PowerShell tap-check output was nondeterministic'}
if($out1 -notmatch '(?m)^TAP CHECK\r?$'){throw 'STOP: TAP CHECK report header missing'}
if($out1 -notmatch '(?m)^Mode: observational\r?$'){throw 'STOP: observational mode missing'}
if($out1 -notmatch '(?m)^Entries: 0\r?$'){throw 'STOP: expected zero-entry CLI ledger missing'}

$categories=@(
'active-directives',
'compiler-transformations',
'semantic-changes',
'authority-intervention',
'optimization-decisions',
'continuity-effects',
'narrative-state-changes',
'convergence-rulings',
'air-lowering',
'runtime-results'
)
$positions=@()
foreach($category in $categories){
    $needle="  ${category}: 0"
    $index=$out1.IndexOf($needle,[StringComparison]::Ordinal)
    if($index -lt 0){throw "STOP: missing coverage row $needle"}
    $positions += $index
}
for($i=1;$i -lt $positions.Count;$i++){
    if($positions[$i] -le $positions[$i-1]){throw 'STOP: coverage rows not in canonical order'}
}
if($out1 -notmatch 'Zero counts mean no observed TAP evidence, not a negative semantic result\.'){
    throw 'STOP: zero-count semantics explanation missing'
}

$projectAfter=@(Get-ProjectSnapshot -Root $project)
$gitAfter=@(git -C $repo status --porcelain=v1 --untracked-files=all)

if(($projectBefore -join "`n") -ne ($projectAfter -join "`n")){throw 'STOP: PowerShell tap-check mutated real .apex project files'}
if(($gitBefore -join "`n") -ne ($gitAfter -join "`n")){throw 'STOP: PowerShell tap-check changed repository status'}

Write-Host 'POWERSHELL_INVOCATION=apexforge_cli.py tap-check .'
Write-Host "REAL_APEX_PROJECT=$relativeProject"
Write-Host 'FIRST_EXIT=0'
Write-Host 'SECOND_EXIT=0'
Write-Host 'OUTPUT_DETERMINISM=PASS'
Write-Host 'COVERAGE_ROWS=10'
Write-Host 'COVERAGE_ORDER=ROADMAP_ORDER'
Write-Host 'ZERO_COUNTS=UNOBSERVED_NOT_NEGATIVE_RESULT'
Write-Host 'PROJECT_BYTE_MUTATION=NONE'
Write-Host 'REPOSITORY_STATUS_MUTATION=NONE'
Write-Host 'P11_11F_POWERSHELL_REAL_APEX_ACCEPTANCE=PASS'