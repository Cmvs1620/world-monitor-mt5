# mt5-geosignal Setup Script
# Run as Administrator: powershell -ExecutionPolicy Bypass -File setup.ps1

param(
    [switch]$SkipPython,
    [switch]$SkipGit,
    [switch]$SkipMT5Check
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== MT5 GeoSignal Environment Setup ===" -ForegroundColor Cyan

# 1. Python Installation
if (-not $SkipPython) {
    Write-Host "`n[1/6] Checking Python 3.11+..." -ForegroundColor Yellow
    $pythonExists = $false
    try {
        $version = python --version 2>&1
        if ($version -match "Python (3\.(1[1-9]|[2-9]\d))") {
            Write-Host "[OK] Python $version found" -ForegroundColor Green
            $pythonExists = $true
        }
    } catch {}

    if (-not $pythonExists) {
        Write-Host "Installing Python 3.11..." -ForegroundColor Cyan
        $wingetExists = $null -ne (Get-Command winget -ErrorAction SilentlyContinue)

        if ($wingetExists) {
            winget install --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements -e
        } else {
            Write-Host "winget not found, downloading Python directly..." -ForegroundColor Yellow
            $pythonInstaller = "$env:TEMP\python-3.11-installer.exe"
            $pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"

            Write-Host "Downloading Python 3.11.9..." -ForegroundColor Cyan
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller -ErrorAction Stop

            Write-Host "Running Python installer..." -ForegroundColor Cyan
            & $pythonInstaller /quiet InstallAllUsers=1 PrependPath=1 | Out-Null

            Remove-Item $pythonInstaller -Force

            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        }
        Write-Host "[OK] Python installed" -ForegroundColor Green
    }
} else {
    Write-Host "`n[1/6] Skipping Python (--SkipPython)" -ForegroundColor Yellow
}

# 2. Git Installation
if (-not $SkipGit) {
    Write-Host "`n[2/6] Checking Git..." -ForegroundColor Yellow
    $gitExists = $false
    try {
        $gitVersion = git --version 2>&1
        Write-Host "[OK] Git $gitVersion found" -ForegroundColor Green
        $gitExists = $true
    } catch {}

    if (-not $gitExists) {
        Write-Host "Installing Git..." -ForegroundColor Cyan
        $wingetExists = $null -ne (Get-Command winget -ErrorAction SilentlyContinue)

        if ($wingetExists) {
            winget install --id Git.Git --accept-package-agreements --accept-source-agreements -e
        } else {
            Write-Host "winget not found, downloading Git directly..." -ForegroundColor Yellow
            $gitInstaller = "$env:TEMP\git-installer.exe"
            $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"

            Write-Host "Downloading Git..." -ForegroundColor Cyan
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $gitUrl -OutFile $gitInstaller -ErrorAction Stop

            Write-Host "Running Git installer..." -ForegroundColor Cyan
            & $gitInstaller /SILENT /NORESTART | Out-Null

            Remove-Item $gitInstaller -Force

            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        }
        Write-Host "[OK] Git installed" -ForegroundColor Green
    }
} else {
    Write-Host "`n[2/6] Skipping Git (--SkipGit)" -ForegroundColor Yellow
}

# 3. Create Directory Structure
Write-Host "`n[3/6] Creating directory structure..." -ForegroundColor Yellow
$dirs = @("engine", "bridge", "signals", "logs", "config", "tests", "ea")
foreach ($dir in $dirs) {
    $path = Join-Path $ProjectRoot $dir
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-Host "  [OK] Created $dir/" -ForegroundColor Gray
    }
}

# 4. Create __init__.py files
Write-Host "  Creating Python package structure..." -ForegroundColor Gray
foreach ($dir in @("engine", "bridge")) {
    $initFile = Join-Path (Join-Path $ProjectRoot $dir) "__init__.py"
    if (-not (Test-Path $initFile)) {
        "" | Out-File -FilePath $initFile -Encoding UTF8
        Write-Host "  [OK] Created $dir/__init__.py" -ForegroundColor Gray
    }
}

# 5. Create Virtual Environment
Write-Host "`n[4/6] Creating Python virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path (Join-Path $ProjectRoot "venv"))) {
    python -m venv (Join-Path $ProjectRoot "venv")
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "[OK] Virtual environment exists" -ForegroundColor Green
}

# 6. Install Python Dependencies
Write-Host "`n[5/6] Installing Python dependencies..." -ForegroundColor Yellow
$reqFile = Join-Path $ProjectRoot "requirements.txt"
if (Test-Path $reqFile) {
    $venvPip = Join-Path $ProjectRoot "venv\Scripts\pip.exe"
    & $venvPip install -r $reqFile -q
    Write-Host "[OK] Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "[WARNING] requirements.txt not found, skipping pip install" -ForegroundColor Yellow
}

# 7. Create Signal JSON Templates
Write-Host "`n[6/6] Creating signal JSON templates..." -ForegroundColor Yellow

$signalTemplate = @{
    timestamp = [datetime]::UtcNow.ToString("o")
    event_id = ""
    classification = ""
    confidence = 0.0
    trade_signal = ""
    symbol = ""
    action = "HOLD"
    volume = 0
    stop_loss = 0.0
    take_profit = 0.0
    rationale = ""
} | ConvertTo-Json

$signal_json = Join-Path $ProjectRoot "signals\signal.json"
$signalTemplate | Out-File -FilePath $signal_json -Encoding UTF8
Write-Host "  [OK] Created signals/signal.json template" -ForegroundColor Gray

$signalLog = Join-Path $ProjectRoot "signals\signal_log.json"
"[]" | Out-File -FilePath $signalLog -Encoding UTF8
Write-Host "  [OK] Created signals/signal_log.json" -ForegroundColor Gray

$heartbeat = Join-Path $ProjectRoot "signals\heartbeat.json"
@{
    last_run = [datetime]::UtcNow.ToString("o")
    status = "initializing"
    next_run = $null
} | ConvertTo-Json | Out-File -FilePath $heartbeat -Encoding UTF8
Write-Host "  [OK] Created signals/heartbeat.json" -ForegroundColor Gray

# Create CSV Headers
Write-Host "  Creating CSV logs..." -ForegroundColor Gray
"timestamp,symbol,action,volume,entry_price,stop_loss,take_profit,pnl,status,event_id" | Out-File -FilePath (Join-Path $ProjectRoot "logs\trades.csv") -Encoding UTF8
"timestamp,event_id,classification,confidence,symbol,action,volume,rationale,status" | Out-File -FilePath (Join-Path $ProjectRoot "logs\signals.csv") -Encoding UTF8
"" | Out-File -FilePath (Join-Path $ProjectRoot "logs\errors.log") -Encoding UTF8
Write-Host "  [OK] Created logs/ files" -ForegroundColor Gray

# 8. Create .env template
Write-Host "  Creating .env template..." -ForegroundColor Gray
$envTemplate = @"
# API Keys
ANTHROPIC_API_KEY=your_key_here
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# MT5 Credentials
MT5_LOGIN=your_login_here
MT5_PASSWORD=your_password_here
MT5_SERVER=ActivTrades-Demo

# WorldMonitor (no key needed - public API)
WORLDMONITOR_API_URL=https://api.worldmonitor.app

# Debug
DEBUG=False
"@

$envFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $envFile)) {
    $envTemplate | Out-File -FilePath $envFile -Encoding UTF8
    Write-Host "  [WARNING] Created .env template - FILL IN YOUR KEYS" -ForegroundColor Yellow
} else {
    Write-Host "  [OK] .env exists (not overwriting)" -ForegroundColor Gray
}

# 9. Create settings.json template
Write-Host "  Creating settings.json..." -ForegroundColor Gray
$settingsTemplate = @{
    debug = $false
    log_level = "INFO"
    mt5_files_path = "C:\Users\your_username\AppData\Roaming\MetaQuotes\Terminal\your_terminal_id\MQL5\Files"
    worldmonitor_poll_interval_seconds = 300
    signal_expiry_seconds = 3600
    risk_per_trade_percent = 1.0
    max_concurrent_positions = 3
    telegram_enabled = $true
    telegram_alerts = @("TRADE_OPENED", "TRADE_CLOSED", "SIGNAL_GENERATED", "ERROR")
} | ConvertTo-Json

$settingsFile = Join-Path $ProjectRoot "config\settings.json"
$settingsTemplate | Out-File -FilePath $settingsFile -Encoding UTF8
Write-Host "  [OK] Created config/settings.json template" -ForegroundColor Gray

Write-Host "`n=== Setup Complete ===" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Edit .env with your API keys" -ForegroundColor Gray
Write-Host "  2. Edit config/settings.json → set mt5_files_path" -ForegroundColor Gray
Write-Host "  3. Run: python validate.py" -ForegroundColor Gray
Write-Host "`nActivate venv next time with:" -ForegroundColor Cyan
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
