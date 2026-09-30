<#
.SYNOPSIS
    Launcher script for Auto Answer in Windows PowerShell.

.DESCRIPTION
    Runs the Auto Answer screen scanner and question solver using the Python environment.

.EXAMPLE
    .\run.ps1
    Runs in interactive watch mode.

.EXAMPLE
    .\run.ps1 snip
    Opens the snipping tool to drag and select the emulator area.

.EXAMPLE
    .\run.ps1 hud
    Opens the floating HUD window.

.EXAMPLE
    .\run.ps1 test-sample
    Runs the AI against the sample question image.
#>

param (
    [Parameter(Position=0, ValueFromRemainingArguments=$true)]
    [string[]]$AppArgs
)

# Find python executable
$pythonExe = $null

if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExe = "py -3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExe = "python"
} else {
    Write-Host "[!] Python not found on PATH. Please ensure Python is installed." -ForegroundColor Red
    exit 1
}

# Run main.py with passed arguments
$cmd = "$pythonExe main.py $($AppArgs -join ' ')"
Invoke-Expression $cmd
