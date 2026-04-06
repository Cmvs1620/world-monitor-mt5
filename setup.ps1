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
            Write-Host "✓ Python $version found" -ForegroundColor Green
            $pythonExists = $true
        }
    } catch {}

    if (-not $pythonExists) {
        Write-Host "Installing Python 3.11..." -ForegroundColor Cyan
        winget install --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements -e
        Write-Host "✓ Python installed" -ForegroundColor Green
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
        Write-Host "✓ Git $gitVersion found" -ForegroundColor Green
        $gitExists = $true
    } catch {}

    if (-not $gitExists) {
        Write-Host "Installing Git..." -ForegroundColor Cyan
        winget install --id Git.Git --accept-package-agreements --accept-source-agreements -e
        Write-Host "✓ Git installed" -ForegroundColor Green
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
        Write-Host "  ✓ Created $dir/" -ForegroundColor Gray
    }
}

# 4. Create __init__.py files
Write-Host "  Creating Python package structure..." -ForegroundColor Gray
foreach ($dir in @("engine", "bridge")) {
    $initFile = Join-Path $ProjectRoot $dir "__init__.py"
    if (-not (Test-Path $initFile)) {
        "" | Out-File -FilePath $initFile -Encoding UTF8
        Write-Host "  ✓ Created $dir/__init__.py" -ForegroundColor Gray
    }
}

# 5. Create Virtual Environment
Write-Host "`n[4/6] Creating Python virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path (Join-Path $ProjectRoot "venv"))) {
    python -m venv (Join-Path $ProjectRoot "venv")
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✓ Virtual environment exists" -ForegroundColor Green
}

# Activate venv
$venvActivate = Join-Path $ProjectRoot "venv\Scripts\Activate.ps1"
& $venvActivate

# 6. Install Python Dependencies
Write-Host "`n[5/6] Installing Python dependencies..." -ForegroundColor Yellow
$reqFile = Join-Path $ProjectRoot "requirements.txt"
if (Test-Path $reqFile) {
    pip install --upgrade pip setuptools wheel -q
    pip install -r $reqFile -q
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "⚠ requirements.txt not found, skipping pip install" -ForegroundColor Yellow
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
$signal_json | Set-Content $signal_json
$signalTemplate | Out-File -FilePath $signal_json -Encoding UTF8
Write-Host "  ✓ Created signals/signal.json template" -ForegroundColor Gray

$signalLog = Join-Path $ProjectRoot "signals\signal_log.json"
"[]" | Out-File -FilePath $signalLog -Encoding UTF8
Write-Host "  ✓ Created signals/signal_log.json" -ForegroundColor Gray

$heartbeat = Join-Path $ProjectRoot "signals\heartbeat.json"
@{
    last_run = [datetime]::UtcNow.ToString("o")
    status = "initializing"
    next_run = $null
} | ConvertTo-Json | Out-File -FilePath $heartbeat -Encoding UTF8
Write-Host "  ✓ Created signals/heartbeat.json" -ForegroundColor Gray

# Create CSV Headers
Write-Host "  Creating CSV logs..." -ForegroundColor Gray
"timestamp,symbol,action,volume,entry_price,stop_loss,take_profit,pnl,status,event_id" | Out-File -FilePath (Join-Path $ProjectRoot "logs\trades.csv") -Encoding UTF8
"timestamp,event_id,classification,confidence,symbol,action,volume,rationale,status" | Out-File -FilePath (Join-Path $ProjectRoot "logs\signals.csv") -Encoding UTF8
"" | Out-File -FilePath (Join-Path $ProjectRoot "logs\errors.log") -Encoding UTF8
Write-Host "  ✓ Created logs/ files" -ForegroundColor Gray

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
    Write-Host "  ⚠ Created .env template - FILL IN YOUR KEYS" -ForegroundColor Yellow
} else {
    Write-Host "  ✓ .env exists (not overwriting)" -ForegroundColor Gray
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
Write-Host "  ✓ Created config/settings.json template" -ForegroundColor Gray

Write-Host "`n=== Setup Complete ===" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Edit .env with your API keys" -ForegroundColor Gray
Write-Host "  2. Edit config/settings.json → set mt5_files_path" -ForegroundColor Gray
Write-Host "  3. Run: python validate.py" -ForegroundColor Gray
Write-Host "`nActivate venv next time with:" -ForegroundColor Cyan
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
