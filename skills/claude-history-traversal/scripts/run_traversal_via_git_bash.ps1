param(
    [Parameter(Mandatory = $true)]
    [string]$Folder,
    [string]$Out = "claude-folder-history.json",
    [string]$Contains,
    [Nullable[int]]$Limit,
    [switch]$Brief,
    [string]$ClaudeRoot,
    [string]$GitBashPath,
    [string]$CondaShPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Test-NonEmpty {
    param([string]$Value)
    return -not [string]::IsNullOrWhiteSpace($Value)
}

function Convert-ToBashPath {
    param([string]$WindowsPath)
    $normalized = $WindowsPath -replace "\\", "/"
    if ($normalized -match "^([A-Za-z]):/(.*)$") {
        $drive = $Matches[1].ToLowerInvariant()
        $rest = $Matches[2]
        return "/$drive/$rest"
    }
    return $normalized
}

function Bash-Quote {
    param([string]$Value)
    $escaped = $Value.Replace("\", "\\")
    $escaped = $escaped.Replace('"', '\"')
    $escaped = $escaped.Replace('$', '\$')
    $escaped = $escaped.Replace('`', '\`')
    return '"' + $escaped + '"'
}

function Resolve-GitBashPath {
    param([string]$Override)
    if (Test-NonEmpty $Override) {
        if (-not (Test-Path -LiteralPath $Override)) {
            throw "Git Bash not found at override path: $Override"
        }
        return (Resolve-Path -LiteralPath $Override).Path
    }

    $candidates = @(
        "C:\Program Files\Git\bin\bash.exe",
        "C:\Program Files\Git\usr\bin\bash.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    throw "Unable to find Git Bash. Set -GitBashPath explicitly."
}

function Resolve-CondaShPath {
    param([string]$Override)
    if (Test-NonEmpty $Override) {
        if (-not (Test-Path -LiteralPath $Override)) {
            throw "conda.sh not found at override path: $Override"
        }
        return (Resolve-Path -LiteralPath $Override).Path
    }

    $user = $env:USERNAME
    $candidates = @(
        "C:\ProgramData\miniconda3\etc\profile.d\conda.sh",
        "C:\ProgramData\anaconda3\etc\profile.d\conda.sh",
        "C:\Users\$user\miniconda3\etc\profile.d\conda.sh",
        "C:\Users\$user\anaconda3\etc\profile.d\conda.sh"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    # conda is optional; plain python in Git Bash is used when absent.
    return $null
}

$gitBashExe = Resolve-GitBashPath -Override $GitBashPath
$condaShWin = Resolve-CondaShPath -Override $CondaShPath

$traversalScriptWin = Join-Path $PSScriptRoot "traverse_claude_history.py"
if (-not (Test-Path -LiteralPath $traversalScriptWin)) {
    throw "Traversal script not found: $traversalScriptWin"
}

$scriptBash = Convert-ToBashPath -WindowsPath $traversalScriptWin

$folderArg = $Folder -replace "\\", "/"
$outArg = $Out -replace "\\", "/"
$claudeRootArg = $null
if (Test-NonEmpty $ClaudeRoot) {
    $claudeRootArg = $ClaudeRoot -replace "\\", "/"
}

$pythonParts = @(
    "python $(Bash-Quote $scriptBash)",
    "--folder $(Bash-Quote $folderArg)",
    "--out $(Bash-Quote $outArg)"
)

if (Test-NonEmpty $Contains) {
    $pythonParts += "--contains $(Bash-Quote $Contains)"
}
if ($Limit -ne $null) {
    $pythonParts += "--limit $Limit"
}
if ($Brief) {
    $pythonParts += "--brief"
}
if (Test-NonEmpty $claudeRootArg) {
    $pythonParts += "--claude-root $(Bash-Quote $claudeRootArg)"
}

$pythonCommand = [string]::Join(" ", $pythonParts)
if ($condaShWin) {
    $condaShBash = Convert-ToBashPath -WindowsPath $condaShWin
    $bashCommand = "source $(Bash-Quote $condaShBash) && conda activate base && $pythonCommand"
    Write-Host "Using conda.sh: $condaShWin"
}
else {
    $bashCommand = $pythonCommand
    Write-Host "conda.sh not found; using plain python from Git Bash PATH"
}
Write-Host "Using Git Bash: $gitBashExe"
Write-Host "Command: $bashCommand"

& $gitBashExe -lc $bashCommand
exit $LASTEXITCODE
