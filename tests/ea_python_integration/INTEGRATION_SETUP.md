# Integration Test Setup & Environment Validation

## Overview

This guide walks through prerequisites, environment validation, and setup before running the end-to-end integration test.

## Prerequisites Checklist

### Python Engine (Mac)

- [ ] Signal engine code cloned to `/root/signal-engine/`
- [ ] Python 3.8+ installed: `python3 --version`
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] WorldMonitor API accessible: `curl https://worldmonitor-api/events`
- [ ] Claude API key configured: `echo $ANTHROPIC_API_KEY`
- [ ] signals/ directory exists: `mkdir -p signals logs`
- [ ] config/settings.json exists with MT5 Files path

### MT5 Expert Advisor (Stratos Windows)

- [ ] MetaTrader 5 installed and running
- [ ] GeoSignal EA compiled and deployed to chart
- [ ] Account properly linked (demo or real)
- [ ] EA properties configured:
  - [ ] DEBUG_MODE = true (for testing)
  - [ ] SIGNAL_FILE_PATH set to MT5 Files folder
  - [ ] EA_TRADING_ENABLED = true
- [ ] MetaTrader 5 MQL5/Files folder accessible
- [ ] Journal accessible (View → Journal)
- [ ] Sufficient account balance (at least $1000 for testing)

### Network & File Sharing

- [ ] Mac and Stratos can ping each other
- [ ] SMB share configured (Mac can mount Stratos drive)
- [ ] OR manual copy method established
- [ ] Network latency acceptable: `ping -c 4 stratos.example.com`

---

## Part 1: Environment Validation

### Step 1a: Verify Python Engine

```bash
# Check Python installation
python3 --version
# Expected: Python 3.8.x or higher

# Check required packages
python3 -c "import anthropic, requests, json; print('✓ All packages installed')"

# Check API key
echo "ANTHROPIC_API_KEY is set: $([ -n "$ANTHROPIC_API_KEY" ] && echo 'YES' || echo 'NO')"

# Check directory structure
ls -la /root/signal-engine/
# Should show: config/, logs/, signals/, run.py, requirements.txt

# Verify WorldMonitor API connectivity
curl -s https://worldmonitor-api/events | head -20
# Should return JSON event data
```

**Expected Output:**
```
Python 3.9.13
✓ All packages installed
ANTHROPIC_API_KEY is set: YES
config   logs   signals   run.py   requirements.txt
[{"event_id": "evt_xyz...", "name": "..."}]
```

### Step 1b: Verify MT5 Expert Advisor

1. Open MetaTrader 5
2. Check EA is deployed to a chart
   - View → Toolbox → Expert Advisors
   - Should see "GeoSignal EA" running
3. Check EA properties
   - Right-click chart → Expert Advisors → GeoSignal EA → Properties
   - Verify:
     - DEBUG_MODE = true
     - SIGNAL_FILE_PATH = correct path
     - EA_TRADING_ENABLED = true
     - MIN_CONFIDENCE = 0.50 (or lower for testing)
4. Check account details
   - Terminal → Account
   - Verify balance > $1000 and margin available

### Step 1c: Verify Network Connectivity

```bash
# From Mac:
ping -c 4 stratos.example.com
# Expected: 4 packets, <50ms latency

# Test SMB share mount
mount | grep smb
# Should show mounted Stratos drive

# Test file permissions
touch /Volumes/Stratos/test.txt && rm /Volumes/Stratos/test.txt
# Should succeed without permission errors
```

---

## Part 2: Signal File Synchronization Setup

Choose one method:

### Option A: Manual Copy Method

**When to use:** Quick testing, low frequency signals, minimal automation

**Steps:**

1. Identify source and destination paths:
   ```
   Source:      ~/signal-engine/signals/signal.json
   Destination: C:\Users\<user>\AppData\Roaming\MetaTrader 5\MQL5\Files\signal.json
   ```

2. Mount Stratos SMB share (if not already mounted):
   ```bash
   # Mac:
   open smb://stratos.example.com/c$
   # Enter credentials when prompted
   ```

3. Copy signal.json manually:
   ```bash
   # Quick copy:
   cp ~/signal-engine/signals/signal.json "/Volumes/Stratos/Users/<user>/AppData/Roaming/MetaTrader 5/MQL5/Files/"
   ```

4. Verify copy:
   ```bash
   # Check modification time:
   stat ~/signal-engine/signals/signal.json
   stat "/Volumes/Stratos/Users/<user>/AppData/Roaming/MetaTrader 5/MQL5/Files/signal.json"
   # Times should be similar (within 5 seconds)
   ```

### Option B: Automated Sync Script

**When to use:** Continuous testing, frequent signals, automated pipeline

**Setup:**

1. Create sync configuration:
   ```bash
   cd /root/signal-engine
   ```

2. Run sync script:
   ```bash
   python tests/ea_python_integration/sync_signal_to_mt5.py \
     --mt5-path "/Volumes/Stratos/Users/<user>/AppData/Roaming/MetaTrader 5/MQL5/Files" \
     --watch 300 \
     --verbose
   ```

3. Expected output:
   ```
   [14:23:55] Sync script started
   [14:23:55] Monitoring signals/signal.json for changes
   [14:23:56] Change detected (size: 1234 bytes)
   [14:23:56] Syncing to MT5 Files folder...
   [14:23:56] ✓ Synced 1 signal (evt_abc123)
   [14:24:06] Change detected (size: 1456 bytes)
   [14:24:06] Syncing to MT5 Files folder...
   [14:24:06] ✓ Synced 1 signal (evt_def456)
   ```

4. Let run in background:
   ```bash
   # Terminal session 2:
   python tests/ea_python_integration/sync_signal_to_mt5.py \
     --mt5-path "/Volumes/Stratos/..." \
     --watch 300 &
   ```

---

## Part 3: Configuration Files

### Python Engine Config (config/settings.json)

Create or update `config/settings.json`:

```json
{
  "api_settings": {
    "worldmonitor_api_url": "https://worldmonitor-api",
    "anthropic_api_key": "${ANTHROPIC_API_KEY}",
    "poll_interval_seconds": 10
  },
  "file_paths": {
    "signal_file": "signals/signal.json",
    "heartbeat_file": "signals/heartbeat.json",
    "log_file": "logs/engine.log",
    "signals_csv": "logs/signals.csv",
    "mt5_files_path": "/Volumes/Stratos/Users/<user>/AppData/Roaming/MetaTrader 5/MQL5/Files"
  },
  "trading_parameters": {
    "min_confidence": 0.50,
    "max_position_size_lots": 0.5,
    "risk_percent_per_trade": 2.0,
    "max_daily_loss_dollars": 500
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

**Key settings for testing:**
- `poll_interval_seconds: 10` (fast polling for testing)
- `min_confidence: 0.50` (low bar to generate signals)
- `max_position_size_lots: 0.5` (safe for testing)

### MT5 EA Properties

In MetaTrader 5, right-click chart → GeoSignal EA → Properties:

```
[Inputs]
DEBUG_MODE:              ✓ Checked
SIGNAL_FILE_PATH:        C:\Users\<user>\AppData\Roaming\MetaTrader 5\MQL5\Files
HEARTBEAT_FILE_PATH:     C:\Users\<user>\AppData\Roaming\MetaTrader 5\MQL5\Files
POLL_INTERVAL_SECONDS:   60
EA_TRADING_ENABLED:      ✓ Checked
MIN_CONFIDENCE:          0.50
MIN_MARGIN_DOLLARS:      500
MAX_POSITION_SIZE:       0.5
MAX_DAILY_LOSS_DOLLARS:  500

[Expert]
✓ Allow automated trading
✓ Allow DLL imports (if using)
```

---

## Part 4: MT5 Configuration Verification

### Check MT5 Account Setup

1. Terminal window → Account tab
   - Verify account number
   - Check balance (should be > $1000)
   - Check margin available
   - Verify account type (demo/real)

2. Terminal window → Symbols tab
   - Add symbols you plan to trade: EURUSD, GBPUSD, USDJPY
   - Right-click symbol → Show in MarketWatch (if not visible)

3. Journal setup
   - View → Journal
   - Filter available
   - Check "Expert Advisors" category to see EA logs

4. File access verification
   - Navigate to: MQL5/Files folder via MetaTrader
   - File → Open Data Folder
   - Should open folder where signal.json will be placed
   - Verify you can read/write files here

### Verify File Paths in EA

Check that EA can find signal.json:

1. In MT5 Journal, watch for messages like:
   ```
   [14:23:56] GeoSignal EA: Looking for signal at C:\...\MQL5\Files\signal.json
   [14:23:56] GeoSignal EA: File found, size: 1234 bytes
   ```

2. If not found:
   ```
   [14:23:56] GeoSignal EA: ERROR: Signal file not found at C:\...\MQL5\Files\signal.json
   ```
   → Check that sync/copy is working, verify file path matches exactly

---

## Part 5: Network & File Access Testing

### Test SMB Connectivity

```bash
# Mac: List Stratos MT5 Files folder
ls "/Volumes/Stratos/Users/<user>/AppData/Roaming/MetaTrader 5/MQL5/Files/"

# Mac: Test write permission
touch "/Volumes/Stratos/Users/<user>/AppData/Roaming/MetaTrader 5/MQL5/Files/test.json"
rm "/Volumes/Stratos/Users/<user>/AppData/Roaming/MetaTrader 5/MQL5/Files/test.json"

# Expected: No permission errors
```

### Test File Sync Latency

1. On Mac, create test signal.json:
   ```bash
   cat > signals/signal.json << 'EOF'
   {
     "timestamp": "2026-04-07T14:23:56.123Z",
     "signals": [
       {
         "event_id": "test_001",
         "symbol": "EURUSD",
         "action": "BUY",
         "confidence": 0.75,
         "reason": "Test signal"
       }
     ]
   }
   EOF
   ```

2. Copy/sync to Stratos:
   ```bash
   # Manual:
   cp signals/signal.json "/Volumes/Stratos/Users/<user>/AppData/Roaming/MetaTrader 5/MQL5/Files/"
   
   # Or use sync script
   ```

3. Verify on Stratos:
   ```
   # On Windows (Stratos):
   type "C:\Users\<user>\AppData\Roaming\MetaTrader 5\MQL5\Files\signal.json"
   # Should match Mac content
   ```

4. Check latency:
   ```bash
   # Mac - note time before copy
   date; cp signals/signal.json "/Volumes/Stratos/..."
   
   # Windows - note time when file appears
   # Should be <5 seconds
   ```

---

## Part 6: Pre-Test Checklist

Run this before starting the E2E test:

```bash
# Terminal 1 (Mac):
[ ] Python 3.9+ installed
[ ] ANTHROPIC_API_KEY exported
[ ] WorldMonitor API accessible
[ ] signals/ and logs/ directories exist
[ ] config/settings.json configured
[ ] config/settings.json has correct MT5 path

# Terminal 2 (Windows/Stratos):
[ ] MetaTrader 5 running
[ ] GeoSignal EA deployed and running
[ ] Account balance > $1000
[ ] EA properties: DEBUG_MODE=true, EA_TRADING_ENABLED=true
[ ] Journal visible (View → Journal)
[ ] MQL5/Files folder accessible

# Network:
[ ] Mac ↔ Stratos ping < 50ms
[ ] SMB share mounted
[ ] File permissions verified (can read/write)
[ ] sync_signal_to_mt5.py script available or manual copy ready

# Logging:
[ ] logs/engine.log will be created at runtime
[ ] logs/signals.csv will be created at runtime
[ ] MT5 Journal visible and filterable
```

---

## Part 7: Troubleshooting Setup Issues

| Issue | Diagnosis | Fix |
|-------|-----------|-----|
| Python module not found | `pip list` doesn't show module | `pip install -r requirements.txt` |
| ANTHROPIC_API_KEY not set | `echo $ANTHROPIC_API_KEY` is empty | `export ANTHROPIC_API_KEY="sk-..."` |
| WorldMonitor API unreachable | `curl` times out or 403 | Check VPN, API endpoint, API key |
| MT5 file path incorrect | EA says "file not found" | Verify exact path in EA properties matches sync destination |
| SMB mount permission denied | Can't read Stratos drive | Check network credentials, firewall, SMB enabled on Stratos |
| File sync not working | signal.json doesn't appear on Stratos | Check file permissions, SMB share, drive space |

---

## Ready to Test?

Once all checkboxes pass:

1. Open 3-4 terminal windows
2. Keep one for Python engine (logs visible)
3. Keep one for sync script (if using automated)
4. Keep one for monitoring signal.json updates
5. Keep MT5 visible with Journal tab open

Then proceed to: **E2E_TEST_PROCEDURE.md**
