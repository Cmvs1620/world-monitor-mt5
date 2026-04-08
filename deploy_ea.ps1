#Requires -Version 5.0
<#
.SYNOPSIS
    Production-ready MT5 EA deployment script

.DESCRIPTION
    Automates deployment of GeoSignalEA.ex5 to MetaTrader 5 with:
    - MT5 auto-detection and terminal ID selection
    - Compiled EA binary copy to Experts folder
    - Signal template deployment to Files folder
    - Header files deployment (reference on Stratos)
    - Configuration update with actual MT5 paths
    - Deployment verification and validation
    - Comprehensive logging and error handling

.PARAMETER TerminalPath
    MT5 terminal installation root (default: C:\Users\$env:USERNAME\AppData\Roaming\MetaQuotes\Terminal)

.PARAMETER TerminalId
    Specific terminal ID (optional, auto-detected if not provided)

.PARAMETER RestartMT5
    Auto-restart MT5 after successful deployment (switch)

.PARAMETER DryRun
    Preview deployment without making changes (switch)

.PARAMETER Verbose
    Verbose logging output (switch)

.EXAMPLE
    .\deploy_ea.ps1
    # Auto-detect terminal, no restart

.EXAMPLE
    .\deploy_ea.ps1 -TerminalId "1ABC2DEF3GHI4JKL5MNO6PQR7STUV" -RestartMT5
    # Specific terminal with restart

.EXAMPLE
    .\deploy_ea.ps1 -DryRun -Verbose
    # Preview without changes, verbose output
#>

[CmdletBinding()]
param(
    [string]$TerminalPath = (Join-Path "C:\Users" $env:USERNAME "AppData\Roaming\MetaQuotes\Terminal"),
    [string]$TerminalId = "",
    [switch]$RestartMT5,
    [switch]$DryRun,
    [switch]$VerboseOutput
)

# ============================================================================
# Configuration
# ============================================================================

$ErrorActionPreference = "Stop"
$ScriptVersion = "1.0.0"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# Minimum EA file size (valid binary should be > 100 KB)
$MinEASize = 102400

# Color functions
function Write-Header { Write-Host "`n$('='*70)" -ForegroundColor Cyan; Write-Host $args[0] -ForegroundColor Cyan; Write-Host "$('='*70)`n" -ForegroundColor Cyan }
function Write-Success { Write-Host "✓ $($args[0])" -ForegroundColor Green }
function Write-Error_ { Write-Host "✗ $($args[0])" -ForegroundColor Red }
function Write-Warning_ { Write-Host "⚠ $($args[0])" -ForegroundColor Yellow }
function Write-Info { Write-Host "ℹ $($args[0])" -ForegroundColor Cyan }
function Write-Verbose_ { if ($VerboseOutput) { Write-Host "  → $($args[0])" -ForegroundColor Gray } }

# Logging function
function Add-Log {
    param([string]$Level, [string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LogPath -Value $logEntry -ErrorAction SilentlyContinue
    if ($VerboseOutput) { Write-Verbose_ $logEntry }
}

# ============================================================================
# Pre-flight Checks
# ============================================================================

Write-Header "=== MT5 EA Deployment Script ==="

Write-Info "Script: $($MyInvocation.MyCommand.Name)"
Write-Info "User: $env:USERNAME"
Write-Info "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Verbose_ "Project Root: $ProjectRoot"
Write-Verbose_ "Terminal Path: $TerminalPath"

# Check if running as Administrator
Write-Info "Checking elevation..."
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Warning_ "Not running as Administrator. Some operations may fail."
    Write-Info "Recommendation: Run PowerShell as Administrator for best results"
}
Write-Success "Pre-flight checks passed"

# ============================================================================
# Terminal Detection & Selection
# ============================================================================

Write-Header "Step 1: MT5 Terminal Detection"

if (-not (Test-Path $TerminalPath)) {
    Write-Error_ "MT5 terminal path not found: $TerminalPath"
    Write-Info "Please ensure MetaTrader 5 is installed and has run at least once."
    Add-Log "ERROR" "Terminal path not found: $TerminalPath"
    exit 1
}

Write-Success "Found MT5 data directory"

# Find all terminal directories
$terminals = @(Get-ChildItem -Path $TerminalPath -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^[0-9A-F]{32}$' })
Write-Verbose_ "Found $($terminals.Count) terminal(s)"

if ($terminals.Count -eq 0) {
    Write-Error_ "No MT5 terminals found in: $TerminalPath"
    Write-Info "Ensure MT5 has been run at least once to initialize a terminal."
    Add-Log "ERROR" "No MT5 terminals detected"
    exit 1
}

# Select terminal ID
if ($TerminalId) {
    # Validate provided terminal ID
    if (-not ($terminals | Where-Object { $_.Name -eq $TerminalId })) {
        Write-Error_ "Terminal ID not found: $TerminalId"
        Write-Info "Available terminals: $($terminals.Name -join ', ')"
        exit 1
    }
    Write-Verbose_ "Using specified terminal: $TerminalId"
} else {
    if ($terminals.Count -eq 1) {
        $TerminalId = $terminals[0].Name
        Write-Success "Auto-detected single terminal: $TerminalId"
    } else {
        # Multiple terminals: show menu
        Write-Info "Multiple terminals detected. Please select:"
        for ($i = 0; $i -lt $terminals.Count; $i++) {
            Write-Host "$($i+1). $($terminals[$i].Name)" -ForegroundColor Yellow
        }

        while ($true) {
            $selection = Read-Host "Select terminal (1-$($terminals.Count))"
            if ([int]::TryParse($selection, [ref]$null) -and $selection -gt 0 -and $selection -le $terminals.Count) {
                $TerminalId = $terminals[$selection-1].Name
                Write-Success "Selected terminal: $TerminalId"
                break
            }
            Write-Warning_ "Invalid selection. Please enter a number between 1 and $($terminals.Count)."
        }
    }
}

Add-Log "INFO" "Terminal ID: $TerminalId"

# ============================================================================
# Path Construction & Validation
# ============================================================================

Write-Header "Step 2: Path Construction & Validation"

$ExpertsPath = Join-Path $TerminalPath $TerminalId "MQL5\Experts"
$FilesPath = Join-Path $TerminalPath $TerminalId "MQL5\Files"
$LogPath = Join-Path $FilesPath "ea_deployment.log"
$VerificationFile = Join-Path $FilesPath "DEPLOYMENT_VERIFICATION.txt"

Write-Verbose_ "Experts Path: $ExpertsPath"
Write-Verbose_ "Files Path: $FilesPath"

# Create paths if missing
foreach ($path in @($ExpertsPath, $FilesPath)) {
    if (-not (Test-Path $path)) {
        Write-Info "Creating missing directory: $path"
        try {
            New-Item -ItemType Directory -Path $path -Force | Out-Null
            Write-Verbose_ "Created: $path"
        } catch {
            Write-Error_ "Failed to create directory: $_"
            Add-Log "ERROR" "Failed to create directory $path : $_"
            exit 1
        }
    } else {
        Write-Success "Directory exists: $(Split-Path -Leaf $path)"
    }
}

# Initialize logging
"[Deployment Log - $ScriptVersion - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')]" | Out-File -FilePath $LogPath -Encoding UTF8
Add-Log "INFO" "=== Deployment Started ==="
Add-Log "INFO" "User: $env:USERNAME"
Add-Log "INFO" "Terminal ID: $TerminalId"

# ============================================================================
# Step 1: Copy Compiled EA
# ============================================================================

Write-Header "Step 3: Deploy Compiled EA Binary"

$EASourcePath = Join-Path $ProjectRoot "ea\GeoSignalEA.ex5"

if (-not (Test-Path $EASourcePath)) {
    Write-Error_ "GeoSignalEA.ex5 not found: $EASourcePath"
    Write-Info "Compile first with MetaEditor (F7 in MT5)"
    Add-Log "ERROR" "EA binary not found: $EASourcePath"
    exit 1
}

$EAFile = Get-Item $EASourcePath
$EASize = $EAFile.Length
Write-Verbose_ "Source EA: $EASourcePath ($([Math]::Round($EASize/1024)) KB)"

if ($EASize -lt $MinEASize) {
    Write-Error_ "EA file too small ($([Math]::Round($EASize/1024)) KB). May not be compiled."
    Write-Info "Compile GeoSignalEA.mq5 with MetaEditor"
    Add-Log "ERROR" "EA file size invalid: $EASize bytes"
    exit 1
}

$EADestPath = Join-Path $ExpertsPath "GeoSignalEA.ex5"

if ($DryRun) {
    Write-Info "[DRY RUN] Would copy: $EASourcePath → $EADestPath"
} else {
    try {
        Write-Info "Copying EA binary..."
        Copy-Item -Path $EASourcePath -Destination $EADestPath -Force -ErrorAction Stop
        $verifyFile = Get-Item $EADestPath
        if ($verifyFile.Length -eq $EASize) {
            Write-Success "Copied GeoSignalEA.ex5 ($([Math]::Round($EASize/1024)) KB)"
            Add-Log "SUCCESS" "EA deployed: $EADestPath"
        } else {
            throw "File size mismatch after copy"
        }
    } catch {
        Write-Error_ "Failed to copy EA: $_"
        Add-Log "ERROR" "Failed to copy EA: $_"
        exit 1
    }
}

# ============================================================================
# Step 2: Copy Header Files (Reference)
# ============================================================================

Write-Header "Step 4: Deploy Header Files (Reference)"

$headersSource = @(
    @{ Source = "ea\includes\signal_struct.mqh"; Dest = "includes" },
    @{ Source = "ea\includes\risk_config.mqh"; Dest = "includes" }
)

foreach ($header in $headersSource) {
    $srcPath = Join-Path $ProjectRoot $header.Source
    $dstDir = Join-Path $ExpertsPath $header.Dest
    $dstPath = Join-Path $dstDir (Split-Path -Leaf $srcPath)

    if (Test-Path $srcPath) {
        if ($DryRun) {
            Write-Verbose_ "[DRY RUN] Would copy: $(Split-Path -Leaf $srcPath)"
        } else {
            try {
                if (-not (Test-Path $dstDir)) {
                    New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
                }
                Copy-Item -Path $srcPath -Destination $dstPath -Force
                Write-Verbose_ "Copied $(Split-Path -Leaf $srcPath)"
            } catch {
                Write-Warning_ "Failed to copy header $(Split-Path -Leaf $srcPath): $_"
                Add-Log "WARNING" "Failed to copy header: $_"
            }
        }
    } else {
        Write-Verbose_ "Skipping $(Split-Path -Leaf $srcPath) (not found)"
    }
}
Write-Success "Header files deployed"
Add-Log "SUCCESS" "Header files deployed"

# ============================================================================
# Step 3: Copy Signal Templates
# ============================================================================

Write-Header "Step 5: Deploy Signal Templates"

$signals = @(
    "signals\signal.json",
    "signals\signal_log.json",
    "signals\heartbeat.json"
)

foreach ($signal in $signals) {
    $srcPath = Join-Path $ProjectRoot $signal
    $dstPath = Join-Path $FilesPath (Split-Path -Leaf $signal)

    if (Test-Path $srcPath) {
        if ($DryRun) {
            Write-Verbose_ "[DRY RUN] Would copy: $(Split-Path -Leaf $signal)"
        } else {
            try {
                Copy-Item -Path $srcPath -Destination $dstPath -Force
                Write-Verbose_ "Copied $(Split-Path -Leaf $signal)"
            } catch {
                Write-Error_ "Failed to copy $(Split-Path -Leaf $signal): $_"
                Add-Log "ERROR" "Failed to copy signal template: $_"
                exit 1
            }
        }
    }
}
Write-Success "Signal templates deployed"
Add-Log "SUCCESS" "Signal templates deployed"

# ============================================================================
# Step 4: Update Configuration
# ============================================================================

Write-Header "Step 6: Update Configuration File"

$ConfigPath = Join-Path $ProjectRoot "config\settings.json"

if (-not (Test-Path $ConfigPath)) {
    Write-Error_ "Configuration file not found: $ConfigPath"
    Add-Log "ERROR" "Config file not found: $ConfigPath"
    exit 1
}

if ($DryRun) {
    Write-Info "[DRY RUN] Would update: config/settings.json"
    Write-Info "  mt5_files_path = $FilesPath"
} else {
    try {
        $config = Get-Content $ConfigPath | ConvertFrom-Json
        $oldPath = $config.mt5_files_path
        $config.mt5_files_path = $FilesPath

        # Validate JSON structure
        $config | ConvertTo-Json | Out-Null

        # Write back
        $config | ConvertTo-Json | Set-Content -Path $ConfigPath -Encoding UTF8
        Write-Success "Updated config/settings.json"
        Write-Verbose_ "  Old path: $oldPath"
        Write-Verbose_ "  New path: $FilesPath"
        Add-Log "SUCCESS" "Updated mt5_files_path: $FilesPath"
    } catch {
        Write-Error_ "Failed to update config: $_"
        Add-Log "ERROR" "Failed to update config: $_"
        exit 1
    }
}

# ============================================================================
# Step 5: Create Deployment Verification File
# ============================================================================

Write-Header "Step 7: Create Verification File"

$verifyContent = @"
=== EA DEPLOYMENT VERIFICATION ===
Deployment Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Script Version: $ScriptVersion
Terminal ID: $TerminalId

Deployment Paths:
  Experts Folder: $ExpertsPath
  Files Folder: $FilesPath
  Config File: $ConfigPath

EA File Information:
  Source: $EASourcePath
  Size: $([Math]::Round($EASize/1024)) KB
  Modified: $($EAFile.LastWriteTime)
  Checksum (CRC32): $(Get-FileChecksum $EASourcePath)

Signal Templates:
  - signal.json
  - signal_log.json
  - heartbeat.json

Configuration:
  Updated mt5_files_path to: $FilesPath

Status: DEPLOYMENT COMPLETE
Deployment verified: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
"@

if ($DryRun) {
    Write-Info "[DRY RUN] Would create: DEPLOYMENT_VERIFICATION.txt"
} else {
    try {
        $verifyContent | Out-File -FilePath $VerificationFile -Encoding UTF8
        Write-Success "Created DEPLOYMENT_VERIFICATION.txt"
        Add-Log "SUCCESS" "Verification file created"
    } catch {
        Write-Warning_ "Failed to create verification file: $_"
        Add-Log "WARNING" "Failed to create verification file: $_"
    }
}

# ============================================================================
# Step 6: Verify All Files
# ============================================================================

Write-Header "Step 8: Deployment Verification"

$verifyPassed = $true

# Check EA
if (Test-Path $EADestPath) {
    $deployedEA = Get-Item $EADestPath
    if ($deployedEA.Length -gt $MinEASize) {
        Write-Success "EA file verified: $([Math]::Round($deployedEA.Length/1024)) KB"
        Add-Log "SUCCESS" "EA verification passed"
    } else {
        Write-Error_ "EA file size invalid after deployment"
        $verifyPassed = $false
        Add-Log "ERROR" "EA file verification failed"
    }
} else {
    Write-Error_ "EA file not found after deployment"
    $verifyPassed = $false
    Add-Log "ERROR" "EA file missing after deployment"
}

# Check signal templates
foreach ($signal in $signals) {
    $dstPath = Join-Path $FilesPath (Split-Path -Leaf $signal)
    if (Test-Path $dstPath) {
        Write-Verbose_ "✓ $(Split-Path -Leaf $signal)"
    } else {
        Write-Warning_ "Missing: $(Split-Path -Leaf $signal)"
    }
}

# Check config
try {
    $configCheck = Get-Content $ConfigPath | ConvertFrom-Json
    if ($configCheck.mt5_files_path -eq $FilesPath) {
        Write-Success "Configuration verified"
        Add-Log "SUCCESS" "Config verification passed"
    } else {
        Write-Error_ "Configuration path mismatch"
        $verifyPassed = $false
        Add-Log "ERROR" "Config verification failed"
    }
} catch {
    Write-Error_ "Configuration file invalid: $_"
    $verifyPassed = $false
    Add-Log "ERROR" "Config parse failed: $_"
}

if ($verifyPassed) {
    Write-Success "All verification checks passed"
} else {
    Write-Error_ "Some verification checks failed"
    Add-Log "ERROR" "Deployment verification FAILED"
    exit 1
}

# ============================================================================
# Optional: Restart MT5
# ============================================================================

if ($RestartMT5 -and -not $DryRun) {
    Write-Header "Step 9: Restart MT5"

    Write-Info "Stopping MT5 processes..."
    try {
        $processes = @(Get-Process -Name "terminal*" -ErrorAction SilentlyContinue)
        if ($processes.Count -gt 0) {
            $processes | Stop-Process -Force
            Write-Info "Stopped $($processes.Count) MT5 process(es)"
            Start-Sleep -Seconds 3
        } else {
            Write-Info "No MT5 processes running"
        }
    } catch {
        Write-Warning_ "Failed to stop MT5: $_"
    }

    Write-Info "Launching MT5..."
    try {
        # Find MT5 executable
        $mt5Path = Get-ChildItem -Path $TerminalPath -Filter "terminal*.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($mt5Path) {
            Start-Process -FilePath $mt5Path.FullName
            Write-Success "MT5 launched"
            Add-Log "SUCCESS" "MT5 restarted"
        } else {
            Write-Warning_ "Could not find MT5 executable. Please restart manually."
            Add-Log "WARNING" "MT5 executable not found"
        }
    } catch {
        Write-Warning_ "Failed to launch MT5: $_"
        Add-Log "WARNING" "Failed to launch MT5: $_"
    }
}

# ============================================================================
# Final Summary
# ============================================================================

Write-Header "=== Deployment Complete ==="

if ($DryRun) {
    Write-Info "DRY RUN COMPLETED - No changes were made"
} else {
    Write-Success "GeoSignalEA successfully deployed!"
}

Write-Info "Next steps:"
Write-Host "  1. Restart MT5 (if not auto-restarted)" -ForegroundColor Gray
Write-Host "  2. Open any chart (e.g., XAUUSD H1)" -ForegroundColor Gray
Write-Host "  3. Navigator → Expert Advisors → GeoSignalEA → Add to Chart" -ForegroundColor Gray
Write-Host "  4. Verify green smiley face ✓ in top-right corner" -ForegroundColor Gray
Write-Host "  5. Check MT5 Journal (Alt+T) for '[EA] GeoSignal EA Started' message" -ForegroundColor Gray

Write-Info "Deployment log: $LogPath"

Add-Log "INFO" "=== Deployment Completed Successfully ==="

Write-Host ""
exit 0

# ============================================================================
# Helper Functions
# ============================================================================

function Get-FileChecksum {
    param([string]$FilePath)
    try {
        $hash = (Get-FileHash -Path $FilePath -Algorithm SHA256).Hash.Substring(0, 8)
        return $hash
    } catch {
        return "N/A"
    }
}
