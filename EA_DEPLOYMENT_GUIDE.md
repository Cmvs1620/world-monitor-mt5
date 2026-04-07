# GeoSignal Expert Advisor - Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the compiled GeoSignal Expert Advisor (GeoSignalEA.ex5) to MetaTrader 5 on Windows.

## Prerequisites
- Windows Stratos machine with MetaTrader 5 installed
- MetaEditor (included with MT5) to compile source if needed
- Administrator access to the MT5 installation directory

## Source Files
The EA consists of the following MQL5 components:
- **ea/GeoSignalEA.mq5** - Main Expert Advisor (514 lines)
- **ea/includes/signal_struct.mqh** - Signal/Result structures
- **ea/includes/risk_config.mqh** - Risk parameters and configuration

All files are syntactically valid and ready for compilation/deployment.

## Compilation (if needed on Stratos)

If GeoSignalEA.ex5 is not yet compiled, follow these steps:

1. **Open MetaEditor:**
   - In MT5, click Tools → MetaEditor (or press F4)

2. **Open the source file:**
   - File → Open
   - Navigate to: `C:\path\to\World monitor claude\ea\GeoSignalEA.mq5`

3. **Verify includes are accessible:**
   MetaEditor will look for includes in:
   - `C:\path\to\World monitor claude\ea\includes\` (project-relative)
   - MT5 standard library (e.g., `Trade\Trade.mqh`)

4. **Compile:**
   - Press F5 or Tools → Compile
   - Check the "Toolbox" tab at the bottom for compilation results
   - Success: Green "0 error(s)" message appears

5. **Locate compiled binary:**
   - The .ex5 file will be generated at:
   ```
   C:\Users\[USERNAME]\AppData\Roaming\MetaQuotes\Terminal\[TERMINAL_ID]\MQL5\Experts\GeoSignalEA.ex5
   ```

## Deployment Steps

### Step 1: Locate MT5 Experts Folder

**Method A: Using MT5 UI**
- In MT5, click: File → Open Data Folder
- Navigate to: `MQL5 → Experts`
- Copy the full path from the address bar

**Method B: Using PowerShell**
```powershell
$terminal_path = "$env:APPDATA\MetaQuotes\Terminal"
Get-ChildItem $terminal_path
```

The path will be: `C:\Users\[USERNAME]\AppData\Roaming\MetaQuotes\Terminal\[TERMINAL_ID]\MQL5\Experts`

### Step 2: Copy Compiled EA

```powershell
# Set variables
$source = "C:\path\to\World monitor claude\ea\GeoSignalEA.ex5"
$destination = "$env:APPDATA\MetaQuotes\Terminal\[TERMINAL_ID]\MQL5\Experts\GeoSignalEA.ex5"

# Copy file
Copy-Item -Path $source -Destination $destination -Force

# Verify
Get-Item $destination | Format-List FullName, Length, LastWriteTime
```

Expected output: File size should be > 100KB, timestamp should be recent.

### Step 3: Restart MT5

- **Close MT5 completely** (File → Exit or Ctrl+Q)
- Wait 5 seconds
- **Open MT5 again**

This forces MT5 to reload the Experts folder and register the new EA.

### Step 4: Deploy EA to Chart

1. **Open a trading chart:**
   - Click "New Chart" or use an existing chart (e.g., XAUUSD, H1 timeframe)

2. **Open Navigator panel:**
   - Click View → Navigator (or press Ctrl+N)
   - In the Navigator, expand "Expert Advisors"

3. **Add EA to chart:**
   - Right-click "GeoSignalEA" in the Navigator
   - Click "Add to Chart"
   - A dialog "GeoSignal EA - Inputs" will appear

4. **Configure input parameters (optional):**
   - **EA_ENABLED**: Set to `true` to enable the EA
   - **EA_TRADING_ENABLED**: Set to `false` initially (testing mode)
   - **POLL_INTERVAL_SECONDS**: 60 (checks signal.json every 60 seconds)
   - **SIGNAL_FILE_PATH**: "signal.json" (reads from MT5 Files folder)
   - **DEBUG_MODE**: Set to `true` to see debug messages in Journal
   - Other parameters can use defaults

5. **Click "Next" then "Finish"**

### Step 5: Verify EA is Running

**Success indicators:**
- A **green smiley face ✓** appears in the top-right corner of the chart
- Journal tab (Alt+T) shows messages:
  ```
  [EA] GeoSignal EA Started
  [EA] Signal file path: signal.json
  ```

**If sad face ✗ appears (EA error):**
- Check Journal tab for error messages
- Ensure "Allow automated trading" is enabled:
  - Tools → Options → Expert Advisors tab
  - Check: "Allow Live Trading", "Allow DLL imports", "Allow automated trading"
- Check that signal.json exists in the MT5 Files folder

## Signal File Location

The EA reads trade signals from:
```
C:\Users\[USERNAME]\AppData\Roaming\MetaQuotes\Terminal\[TERMINAL_ID]\MQL5\Files\signal.json
```

The Python engine writes signals here, and the EA polls every 60 seconds (configurable).

## Input Parameters Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| EA_ENABLED | true | Enable/disable the EA |
| EA_TRADING_ENABLED | false | Allow actual trade execution (false = demo mode) |
| POLL_INTERVAL_SECONDS | 60 | How often EA checks signal.json |
| MAX_CONCURRENT_POSITIONS | 5 | Max open positions |
| RISK_PER_TRADE_PERCENT | 2.0 | Risk per trade (% of account) |
| MAX_DAILY_LOSS_PERCENT | 10.0 | Stop trading if daily loss exceeds this |
| SIGNAL_FILE_PATH | signal.json | Path to signal file in MT5 Files folder |
| DEBUG_MODE | false | Enable verbose logging to Journal |

## Troubleshooting

### EA not appearing in Navigator
- Ensure file is copied to correct Experts folder
- Restart MT5 (close and reopen)
- Check file permissions (should be readable)

### EA loads but shows sad face ✗
- Check Journal tab (Alt+T) for errors
- Enable "Allow automated trading" in Tools → Options
- Verify signal.json exists in MT5 Files folder
- Check risk thresholds haven't been exceeded

### EA not reading signal.json
- Verify SIGNAL_FILE_PATH matches actual file location
- File must be in MT5 Files folder, not root
- Check Python engine is writing to correct path
- Enable DEBUG_MODE to see file read attempts in Journal

### EA executing wrong signals
- Verify signal.json has correct structure (see signal_struct.mqh)
- Check confidence thresholds in risk_config.mqh
- Review Journal for skipped signals and reasons

## Rollback

To disable or remove the EA:

1. **Disable on chart:**
   - Right-click EA in Navigator → "Delete from Chart"

2. **Remove binary (optional):**
   - Delete from Experts folder
   - Restart MT5

3. **Keep source for reference:**
   - Source files (*.mq5) remain in the project folder

## Next Steps

After successful deployment:
1. Test with EA_TRADING_ENABLED = false (demo mode)
2. Monitor Journal for signal reading and execution
3. Verify signal.json is being written by Python engine
4. Once stable, set EA_TRADING_ENABLED = true for live trading

---

**Created**: 2026-04-07
**Status**: Ready for deployment to Windows Stratos
