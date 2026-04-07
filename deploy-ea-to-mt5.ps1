#!/usr/bin/env pwsh
#Requires -Version 5.0

<#
.SYNOPSIS
    Deploys GeoSignalEA.ex5 to MetaTrader 5 Experts folder

.DESCRIPTION
    This script automates the deployment of the compiled GeoSignal Expert Advisor
    to the MT5 Experts directory on Windows.

    Prerequisites:
    - GeoSignalEA.ex5 must exist in the ea/ folder
    - MetaTrader 5 must be installed
    - User must have write permissions to MT5 data folder

.PARAMETER EASourcePath
    Path to the compiled GeoSignalEA.ex5 file (default: ./ea/GeoSignalEA.ex5)

.PARAMETER RestartMT5
    If $true, automatically restart MT5 after deployment (requires MT5 to be open)

.PARAMETER VerifyOnly
    If $true, only verify file existence without copying

.EXAMPLE
    .\deploy-ea-to-mt5.ps1
    # Deploy EA from default location

.EXAMPLE
    .\deploy-ea-to-mt5.ps1 -RestartMT5 $true
    # Deploy and restart MT5

.EXAMPLE
    .\deploy-ea-to-mt5.ps1 -VerifyOnly $true
    # Check if EA file exists without deploying
#>

param(
    [Parameter(Mandatory = $false)]
    [string]$EASourcePath = (Join-Path $PSScriptRoot "ea" "GeoSignalEA.ex5"),

    [Parameter(Mandatory = $false)]
    [bool]$RestartMT5 = $false,

    [Parameter(Mandatory = $false)]
    [bool]$VerifyOnly = $false
)

# Enable error handling
$ErrorActionPreference = "Stop"

function Write-Header {
    param([string]$Message)
    Write-Host "`n$('='*60)" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "$('='*60)`n" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Yellow
}

# ============================================================================
# Main Script
# ============================================================================

Write-Header "GeoSignal EA Deployment Script"

# Check if source file exists
Write-Info "Checking source file: $EASourcePath"
if (-not (Test-Path $EASourcePath)) {
    Write-Error "Source file not found: $EASourcePath"
    exit 1
}

$sourceFile = Get-Item $EASourcePath
Write-Success "Source file found ($('{0:N0}' -f $sourceFile.Length) bytes)"

if ($VerifyOnly) {
    Write-Success "Verification complete. File is ready for deployment."
    exit 0
}

# Find MT5 installation
Write-Info "Locating MetaTrader 5 installation..."
$appDataPath = $env:APPDATA
$mt5Path = Join-Path $appDataPath "MetaQuotes" "Terminal"

if (-not (Test-Path $mt5Path)) {
    Write-Error "MT5 not found in standard location: $mt5Path"
    Write-Info "Please ensure MetaTrader 5 is installed and has been run at least once."
    exit 1
}

Write-Success "Found MT5 data directory: $mt5Path"

# Find terminal ID (usually first subdirectory)
$terminals = Get-ChildItem -Path $mt5Path -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^[0-9A-F]{32}$' }

if ($terminals.Count -eq 0) {
    Write-Error "No MT5 terminal found in $mt5Path"
    exit 1
}

if ($terminals.Count -gt 1) {
    Write-Info "Multiple MT5 terminals found. Using first one."
}

$terminalId = $terminals[0].Name
$expertsPath = Join-Path $mt5Path $terminalId "MQL5" "Experts"

Write-Success "Terminal ID: $terminalId"
Write-Success "Experts path: $expertsPath"

# Verify experts folder exists
if (-not (Test-Path $expertsPath)) {
    Write-Error "Experts folder not found at: $expertsPath"
    Write-Info "Creating Experts folder..."
    New-Item -ItemType Directory -Path $expertsPath -Force | Out-Null
    Write-Success "Experts folder created."
}

# Copy file
$destPath = Join-Path $expertsPath "GeoSignalEA.ex5"
Write-Info "Copying EA to: $destPath"

try {
    Copy-Item -Path $EASourcePath -Destination $destPath -Force
    Write-Success "EA deployed successfully!"
}
catch {
    Write-Error "Failed to copy file: $_"
    exit 1
}

# Verify copy
$destFile = Get-Item $destPath
Write-Success "Verified: $('{0:N0}' -f $destFile.Length) bytes at $destPath"

# Optional: Restart MT5
if ($RestartMT5) {
    Write-Header "Restarting MetaTrader 5"

    # Kill MT5 processes
    Write-Info "Stopping MT5..."
    Get-Process -Name "terminal64" -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process -Name "terminal32" -ErrorAction SilentlyContinue | Stop-Process -Force

    Start-Sleep -Seconds 3

    # Start MT5 again
    Write-Info "Starting MT5..."
    $mt5Exe = Get-ChildItem -Path (Join-Path $mt5Path ".." ".." "MetaTrader 5") -Filter "terminal*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1

    if ($mt5Exe) {
        Start-Process -FilePath $mt5Exe.FullName
        Write-Success "MT5 started. EA will be loaded when MT5 opens."
    }
    else {
        Write-Info "Could not find MT5 executable. Please restart MT5 manually."
    }
}
else {
    Write-Info "MT5 not restarted. Please restart MetaTrader 5 manually for the EA to be loaded."
}

Write-Header "Deployment Complete"
Write-Success "GeoSignalEA is ready for deployment to a chart."
Write-Info "Next steps:"
Write-Info "  1. Restart MT5 if not already done"
Write-Info "  2. Open View → Navigator (Ctrl+N)"
Write-Info "  3. Expand 'Expert Advisors' and find 'GeoSignalEA'"
Write-Info "  4. Right-click → 'Add to Chart'"
Write-Info "  5. Verify green smiley face appears in chart corner"
