# Integration Test Troubleshooting Guide

## Quick Diagnosis Matrix

| Symptom | Root Cause | Diagnosis | Fix |
|---------|-----------|-----------|-----|
| Python engine won't start | Missing config or API key | Check logs/engine.log | Set ANTHROPIC_API_KEY, verify config/settings.json |
| "0 events fetched" | WorldMonitor API unreachable | Curl API directly | Check VPN, API key, network connectivity |
| signal.json not updating | Python polling stopped | Check Python console, logs | Restart Python engine, check for exceptions |
| EA not reading signal | File path incorrect | Check MT5 EA properties | Verify exact path matches sync destination |
| Trade not executing | Risk gate blocked | Check MT5 Journal for "FAILED" | Review risk parameters, account balance |
| heartbeat.json not created | EA file write permission | Check MT5 Files folder access | Verify folder is writable by MT5 process |
| High latency (>5min) | Polling interval too long | Check run.py POLL_INTERVAL_SECONDS | Set to 10 for testing (not 300) |
| signal_id mismatch | Python/EA losing sync | Compare signal.json vs heartbeat.json | Check event_id generation consistency |

---

## Issue 1: Python Engine Won't Start

### Symptoms
- Python exits immediately with error
- No output or "Command not found"
- Error message mentions missing module or config

### Diagnosis

```bash
# Check Python version
python3 --version

# Check required packages
python3 -c "import anthropic, requests, json"

# Check config file
ls -la config/settings.json

# Check API key
echo $ANTHROPIC_API_KEY

# View full error
python run.py 2>&1 | head -20
```

### Root Causes & Fixes

**Case 1: Module not found**
```
Error: ModuleNotFoundError: No module named 'anthropic'
```
Fix:
```bash
pip install -r requirements.txt
pip install anthropic requests
```

**Case 2: Config file missing**
```
Error: FileNotFoundError: [Errno 2] No such file or directory: 'config/settings.json'
```
Fix:
```bash
mkdir -p config
cat > config/settings.json << 'EOF'
{
  "api_settings": {
    "worldmonitor_api_url": "https://worldmonitor-api",
    "anthropic_api_key": "${ANTHROPIC_API_KEY}",
    "poll_interval_seconds": 10
  },
  "file_paths": {
    "signal_file": "signals/signal.json",
    "mt5_files_path": "/Volumes/Stratos/Users/..."
  }
}
EOF
```

**Case 3: API key not set**
```
Error: KeyError: 'ANTHROPIC_API_KEY'
```
Fix:
```bash
export ANTHROPIC_API_KEY="sk-..."
# Verify:
echo $ANTHROPIC_API_KEY
```

**Case 4: Wrong Python version**
```
Error: SyntaxError: f-strings require Python 3.6+
```
Fix:
```bash
python3.9 run.py  # Use Python 3.9 explicitly
# Or: brew install python@3.9
```

---

## Issue 2: "0 events fetched" / API Errors

### Symptoms
```
[14:23:55] INFO - Fetching events from WorldMonitor API...
[14:23:55] ERROR - API request failed: 403 Forbidden
```

OR

```
[14:23:55] INFO - Fetching events from WorldMonitor API...
[14:23:56] WARNING - No new events (got 0)
```

### Diagnosis

```bash
# Test API connectivity
curl -v https://worldmonitor-api/events

# Test with headers (if API key required)
curl -H "Authorization: Bearer $API_KEY" https://worldmonitor-api/events

# Check network
ping worldmonitor-api
traceroute worldmonitor-api

# Check firewall
lsof -i :443  # See if HTTPS is open
```

### Root Causes & Fixes

**Case 1: API endpoint wrong or changed**
```
Error: Connection refused / 404 Not Found
```
Fix:
```bash
# Verify correct endpoint in config/settings.json:
cat config/settings.json | grep worldmonitor_api_url

# Update if needed:
# "worldmonitor_api_url": "https://worldmonitor-api" (check exact URL)
```

**Case 2: API authentication failed**
```
Error: 403 Forbidden / 401 Unauthorized
```
Fix:
```bash
# Check API key validity
curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" https://worldmonitor-api/events

# If using API token, regenerate in platform dashboard
# Then: export ANTHROPIC_API_KEY="new_token"
```

**Case 3: Network/VPN issue**
```
Error: Connection timeout / No route to host
```
Fix:
```bash
# Check VPN connection
scutil -r worldmonitor-api  # Should return "Reachable via WiFi"

# Check DNS
nslookup worldmonitor-api
dig worldmonitor-api

# Restart network:
# Mac: System Preferences → Network → Wi-Fi → Disconnect → Reconnect
```

**Case 4: API temporarily down / no new events**
```
Got 0 events in last 300 seconds (normal during quiet periods)
```
Fix:
```bash
# Wait 5 minutes for new events to arrive
# OR test with curl to see if API returns any data at all:
curl -s https://worldmonitor-api/events | jq '.[] | .event_id' | head -5

# If no results, API may have no events
# This is normal - wait or check if API is live
```

---

## Issue 3: signal.json Not Updating

### Symptoms
```bash
# No changes in signal.json over 2+ minutes
cat signals/signal.json
# Same content as before
stat signals/signal.json  # Modification time unchanged
```

### Diagnosis

```bash
# Check if Python is still running
ps aux | grep run.py

# Check for errors in logs
tail -50 logs/engine.log | grep ERROR

# Check if signal file is locked/permissions
ls -la signals/signal.json
lsof signals/signal.json

# Watch for updates
watch -n 2 'cat signals/signal.json | jq .timestamp'
```

### Root Causes & Fixes

**Case 1: Python engine crashed**
```
Error: Process terminated, exit code 1
```
Fix:
```bash
# Check logs for last error
tail -20 logs/engine.log

# Restart engine
python run.py

# If keeps crashing, check:
# - API connectivity
# - File permissions on signals/
# - Disk space: df -h
```

**Case 2: API not returning events**
See Issue 2 above (API connectivity)

**Case 3: Signal file locked by another process**
```
Error: Permission denied writing to signals/signal.json
```
Fix:
```bash
# Check what's locking the file
lsof signals/signal.json

# Kill interfering process
kill -9 <PID>

# Verify permissions
chmod 644 signals/signal.json
chmod 755 signals/
```

**Case 4: Polling interval too long**
```
# If POLL_INTERVAL_SECONDS = 300, updates only every 5 minutes
```
Fix:
```bash
# For testing, set to 10 seconds in run.py:
POLL_INTERVAL_SECONDS = 10

# Restart Python engine
python run.py
```

---

## Issue 4: signal.json Not Syncing to MT5 / File Transfer Failed

### Symptoms
```bash
# signal.json on Mac is updated, but not on Stratos
stat ~/signal-engine/signals/signal.json  # Modified 14:23:56
stat "/Volumes/Stratos/.../signal.json"   # Modified 14:20:00 (old)
```

OR sync script shows error:
```
[14:23:56] ERROR: Permission denied writing to MT5 folder
```

### Diagnosis

```bash
# Check if Stratos drive is mounted
mount | grep Stratos
df | grep Stratos

# Check source file exists
ls -la signals/signal.json

# Try manual copy
cp signals/signal.json "/Volumes/Stratos/Users/..." 2>&1

# Check target folder permissions
ls -la "/Volumes/Stratos/Users/.../MQL5/Files/"

# Test write access
touch "/Volumes/Stratos/Users/.../MQL5/Files/test.txt"
rm "/Volumes/Stratos/Users/.../MQL5/Files/test.txt"
```

### Root Causes & Fixes

**Case 1: SMB share not mounted**
```
Error: No such file or directory: /Volumes/Stratos/...
```
Fix:
```bash
# Mount Stratos drive
open smb://stratos.example.com/c$
# or
mount_smbfs //username:password@stratos.example.com/c$ /Volumes/Stratos

# Verify mount
mount | grep smb
```

**Case 2: MT5 Files path incorrect**
```
Error: Cannot stat path
```
Fix:
```bash
# Find correct path on Stratos:
# Windows: Start → File Explorer → AppData → Roaming → MetaTrader 5 → MQL5 → Files
# Or: C:\Users\<username>\AppData\Roaming\MetaTrader 5\MQL5\Files

# Update config/settings.json with exact path:
"mt5_files_path": "/Volumes/Stratos/Users/<username>/AppData/Roaming/MetaTrader 5/MQL5/Files"

# Verify with Mac:
ls -la "/Volumes/Stratos/Users/<username>/AppData/Roaming/MetaTrader 5/MQL5/Files"
```

**Case 3: Permission denied**
```
Error: Permission denied
```
Fix:
```bash
# Check folder permissions on Stratos
ls -la "/Volumes/Stratos/.../MQL5/Files"
# Should show: drwxrwxrwx (755 or 777)

# If not writable, fix on Windows:
# Right-click folder → Properties → Security → Edit → Add your user
# Give Full Control

# From Mac, try again:
cp signals/signal.json "/Volumes/Stratos/.../MQL5/Files/"
```

**Case 4: Disk full on Stratos**
```
Error: No space left on device
```
Fix:
```bash
# Check disk usage on Stratos
df -h C:  # Windows equivalent

# On Stratos: free up space or use different drive
# Then retry sync
```

**Case 5: Network timeout**
```
Error: Operation timed out
```
Fix:
```bash
# Check network latency
ping -c 4 stratos.example.com

# If > 100ms, may be slow network
# Check SMB mount status
mount | grep smb

# Remount if stale:
umount /Volumes/Stratos
mount_smbfs //username:password@stratos.example.com/c$ /Volumes/Stratos
```

---

## Issue 5: EA Not Reading Signal / "File Not Found"

### Symptoms (MT5 Journal)
```
[14:23:57] GeoSignal EA: ERROR: Signal file not found
[14:23:57] GeoSignal EA: Looking for: C:\...\signal.json
[14:23:57] GeoSignal EA: File doesn't exist, will try again next cycle
```

### Diagnosis

1. In MT5, check EA properties:
   - Right-click chart → Properties → GeoSignal EA
   - Note SIGNAL_FILE_PATH value

2. On Windows, verify file exists:
   ```cmd
   dir "C:\Users\<user>\AppData\Roaming\MetaTrader 5\MQL5\Files\signal.json"
   ```

3. Check file size:
   ```bash
   stat "/Volumes/Stratos/.../signal.json"
   # Should show: Size: 500-5000 bytes
   # NOT 0 bytes
   ```

### Root Causes & Fixes

**Case 1: Path in EA properties is wrong**
```
EA looking for: C:\Users\admin\...\signal.json
But file is at: C:\Users\username\...\signal.json (different user!)
```
Fix:
```
1. Find actual MT5 Files folder:
   File → Open Data Folder (in MT5)
   Note the path shown

2. Update EA properties:
   Right-click chart → Properties → GeoSignal EA
   Set SIGNAL_FILE_PATH to exact path shown in step 1

3. Save and restart EA
```

**Case 2: File never synced from Mac**
```
File doesn't exist on Stratos yet
```
Fix:
```bash
# On Mac, verify file exists and has recent timestamp:
ls -la signals/signal.json
stat signals/signal.json

# Manually copy to test:
cp signals/signal.json "/Volumes/Stratos/.../signal.json"

# Check on Stratos:
dir "C:\Users\...\MQL5\Files\signal.json"

# Then restart sync script or run again
```

**Case 3: File exists but EA can't read it**
```
EA says file exists but fails to parse JSON
```
Fix:
```bash
# On Mac, verify signal.json is valid JSON:
cat signals/signal.json | jq .
# Should not error

# If error, fix Python output to ensure valid JSON
# Check logs/engine.log for JSON write errors

# On Stratos, check file permissions:
# File → Properties → Security → Ensure MT5 process can read

# Restart EA:
# Right-click chart → Expert Advisors → GeoSignal EA (remove)
# Right-click chart → Expert Advisors → GeoSignal EA (attach)
```

**Case 4: signal.json is empty or zero bytes**
```
File exists but size: 0 bytes
```
Fix:
```bash
# Python is creating empty file, not writing content
# Check Python logs:
tail -50 logs/engine.log | grep -i "write\|json"

# Restart Python engine:
Ctrl+C in Python terminal
python run.py

# Verify signal.json gets content:
watch -n 2 'ls -la signals/signal.json'
# Size should grow from 0 to 1000+
```

---

## Issue 6: Trade Not Executing / Risk Gate Blocked

### Symptoms (MT5 Journal)
```
[14:23:57] GeoSignal EA: Signal received - BUY EURUSD (confidence: 0.92)
[14:23:57] GeoSignal EA: Risk check: confidence OK
[14:23:57] GeoSignal EA: Risk check: position limit OK
[14:23:57] GeoSignal EA: Risk check FAILED: Daily loss exceeded
[14:23:57] GeoSignal EA: Signal held - will retry next cycle
```

OR no execution at all:
```
[14:23:57] GeoSignal EA: Signal received - BUY EURUSD
[14:23:57] GeoSignal EA: ... (silence, no risk checks logged)
```

### Diagnosis

```bash
# Check risk gate settings in EA:
# Right-click chart → Properties → GeoSignal EA
# Review: MIN_CONFIDENCE, MIN_MARGIN_DOLLARS, MAX_POSITION_SIZE, MAX_DAILY_LOSS

# Check account status in MT5:
# Terminal → Account tab
# Note: Balance, Free Margin, Daily Profit/Loss

# Check existing positions:
# Terminal → Trades tab
# Count open positions per symbol
```

### Root Causes & Fixes

**Case 1: Confidence score too low**
```
Signal confidence: 0.45
Min confidence gate: 0.50
Result: BLOCKED
```
Fix:
```bash
# In run.py, lower minimum confidence for testing:
min_confidence = 0.40  # Changed from 0.50

# Restart Python engine
python run.py

# Or in EA properties, lower MIN_CONFIDENCE to 0.40
```

**Case 2: Account balance too low**
```
Free margin: $200
Min margin gate: $500
Result: BLOCKED
```
Fix:
```bash
# Add funds to account:
# MT5: Account menu → Deposit
# Or: Use demo account with higher balance

# Or lower margin gate in EA:
# Right-click chart → Properties
# Set MIN_MARGIN_DOLLARS = 100 (for testing only)
```

**Case 3: Too many open positions**
```
Open positions per symbol: 5
Max position limit: 5
Result: BLOCKED (cannot open another EURUSD)
```
Fix:
```bash
# Close some existing positions:
# Terminal → Trades → Right-click position → Close
# Keep only 2-3 open positions for testing

# Or increase position limit in EA:
# Right-click chart → Properties
# Set MAX_POSITIONS_PER_SYMBOL = 10
```

**Case 4: Daily loss limit exceeded**
```
Today's loss: $487
Max daily loss: $500
Result: BLOCKED (can't risk more today)
```
Fix:
```bash
# Wait until next trading day (when daily P&L resets)

# Or increase daily loss limit for testing:
# Right-click chart → Properties → GeoSignal EA
# Set MAX_DAILY_LOSS_DOLLARS = 5000

# Or close losing positions to reduce loss
```

**Case 5: Risk gates logging disabled**
```
No risk check messages at all
DEBUG_MODE = false
```
Fix:
```
Right-click chart → Properties → GeoSignal EA
Set DEBUG_MODE = true

Restart EA (remove/attach)
```

---

## Issue 7: heartbeat.json Not Created / Execution Not Logged

### Symptoms
```bash
# After trades execute, heartbeat.json doesn't update
ls -la signals/heartbeat.json
# File not found or very old

# Python logs show no heartbeat messages
tail -20 logs/engine.log | grep -i heartbeat
# (empty)
```

### Diagnosis

```bash
# Check if heartbeat file exists at all
ls -la signals/heartbeat.json

# Check last modification time
stat signals/heartbeat.json
# Should be within last 60 seconds

# Check if Python is reading it
tail -50 logs/engine.log | grep heartbeat
```

### Root Causes & Fixes

**Case 1: EA not writing heartbeat file**
```
EA executes trade but doesn't write heartbeat.json
```
Fix:
```bash
# Check if file write is enabled in EA code
# EA should have: FileOpen(..., FILE_WRITE)

# Check MT5 Files folder write permissions
# (See Issue 4 for fix)

# Check EA properties:
# Right-click chart → Properties → Expert Advisors
# Verify file write is allowed (no restrictions)

# Restart EA
```

**Case 2: heartbeat.json on Stratos not copied back to Mac**
```
heartbeat.json exists on Stratos but not on Mac
```
Fix:
```bash
# Manual copy back from Stratos to Mac:
cp "/Volumes/Stratos/.../heartbeat.json" ~/signal-engine/signals/

# Or setup reverse sync in Python:
# Modify sync script to copy heartbeat.json back
```

**Case 3: Python not reading heartbeat**
```
heartbeat.json exists but Python doesn't process it
```
Fix:
```bash
# Check Python heartbeat reading code in run.py
# Ensure heartbeat file path is correct:
# HEARTBEAT_FILE_PATH = "signals/heartbeat.json"

# Verify Python has permission to read:
ls -la signals/heartbeat.json
# Should be readable (644 or 755)

# Restart Python engine
```

**Case 4: File path mismatch between EA and Python**
```
EA writing to: C:\...\heartbeat.json
Python reading from: signals/heartbeat.json (different path)
```
Fix:
```bash
# Ensure both use same file path:
# EA: Right-click chart → Properties → HEARTBEAT_FILE_PATH
# Python: config/settings.json → "heartbeat_file": "signals/heartbeat.json"

# They must match (or both point to MT5 Files folder)
```

---

## Issue 8: High Latency (>5 minutes)

### Symptoms
```
Signal generated: 2026-04-07T14:23:56.123Z
Heartbeat received: 2026-04-07T14:28:45.000Z
Latency: 4m 49s (too long!)
```

### Diagnosis

```bash
# Check polling interval in Python
cat run.py | grep POLL_INTERVAL_SECONDS
# If 300, that's 5-minute polling (production)
# For testing, should be 10

# Check Python event fetch timing
tail -50 logs/engine.log | grep "Fetching events"
# Should be every 10 seconds, not every 300

# Check EA polling interval
# Right-click chart → Properties → GeoSignal EA
# Check POLL_INTERVAL_SECONDS (should be 60)
```

### Root Causes & Fixes

**Case 1: Python polling interval is 300 seconds (production)**
```
[14:23:55] Fetching events...
[14:28:55] Fetching events...  ← 5 minute gap!
```
Fix:
```python
# In run.py:
POLL_INTERVAL_SECONDS = 10  # For testing
# or
POLL_INTERVAL_SECONDS = 60  # For faster testing

# Restart Python engine
python run.py
```

**Case 2: EA polling interval is too long**
```
EA checks for signal.json every 300 seconds
Signal arrives but waits 5 minutes before EA reads it
```
Fix:
```
Right-click chart → Properties → GeoSignal EA
Set POLL_INTERVAL_SECONDS = 60 (or lower for testing)
Restart EA
```

**Case 3: File sync is slow**
```
signal.json on Mac updated at 14:23:56
Signal.json on Stratos updated at 14:24:45 (49 seconds!)
```
Fix:
```bash
# Check network latency
ping -c 10 stratos.example.com
# If > 50ms, network may be slow

# Check SMB performance
# May need to optimize network or use faster connection

# For testing, consider: direct file copy instead of network sync
```

---

## Issue 9: signal_id / event_id Mismatch

### Symptoms
```
Python signal.json:
  "event_id": "evt_abc123"

EA heartbeat.json:
  "signal_id": "evt_xyz789"  ← Different!

logs/signals.csv:
  event_id=evt_abc123, ticket=123456789
  # But heartbeat signal_id is different
```

### Diagnosis

```bash
# Extract event_ids from signal.json
jq '.signals[].event_id' signals/signal.json

# Extract signal_ids from heartbeat.json
jq '.signal_id' signals/heartbeat.json

# Check CSV entries
cut -d, -f2 logs/signals.csv | head -10
```

### Root Causes & Fixes

**Case 1: Event ID not passed through signal.json**
```
Python generates signal but doesn't include event_id
EA assigns its own ID or uses timestamp
```
Fix:
```python
# In Python signal generation:
signal = {
    "event_id": event["event_id"],  # MUST be included
    "symbol": "EURUSD",
    "action": "BUY",
    ...
}
```

**Case 2: EA reading wrong file**
```
EA reads old signal.json, loses track of event_id
```
Fix:
```bash
# Restart EA to pick up latest signal.json
# Right-click chart → Expert Advisors → GeoSignal EA (remove)
# Right-click chart → Expert Advisors → GeoSignal EA (attach)
```

**Case 3: Signal file corruption during transfer**
```
signal.json transferred with errors, event_id field missing
```
Fix:
```bash
# Verify signal.json on both systems
jq . signals/signal.json  # Mac
jq . "/Volumes/Stratos/.../signal.json"  # Windows via Mac

# If either errors, file is corrupted
# Restart Python engine to regenerate fresh signal.json
```

---

## General Troubleshooting Workflow

1. **Check Python Engine**
   ```bash
   ps aux | grep run.py
   tail -50 logs/engine.log
   cat signals/signal.json | jq .
   ```

2. **Check File Sync**
   ```bash
   ls -la signals/signal.json  # Mac
   stat "/Volumes/Stratos/.../signal.json"  # Windows via Mac
   # Timestamps should be similar
   ```

3. **Check EA Execution**
   ```
   Open MT5 Terminal → Journal
   Filter: "GeoSignal EA" "Expert Advisors"
   Watch for "Signal received", "PASSED", "EXECUTED", or "FAILED"
   ```

4. **Check Heartbeat**
   ```bash
   cat signals/heartbeat.json | jq .
   tail -10 logs/signals.csv
   tail -50 logs/engine.log | grep -i heartbeat
   ```

5. **Verify Consistency**
   ```bash
   # event_id from signal.json
   jq '.signals[0].event_id' signals/signal.json
   
   # signal_id from heartbeat.json
   jq '.signal_id' signals/heartbeat.json
   
   # event_id from CSV
   head -2 logs/signals.csv | tail -1 | cut -d, -f2
   
   # All three should match
   ```

6. **Document Issue & Fix**
   - Note timestamp of failure
   - Copy relevant logs to results/ folder
   - Update this TROUBLESHOOTING.md with new issues found

---

## Still Stuck?

If issue not listed here:

1. Check Python logs for stack traces:
   ```bash
   grep -i "exception\|traceback\|error" logs/engine.log
   ```

2. Check MT5 Journal for EA errors:
   ```
   View → Journal → Expert Advisors → GeoSignal EA
   Look for any ERROR messages
   ```

3. Verify basic connectivity:
   ```bash
   curl https://worldmonitor-api/events  # API alive?
   ping stratos.example.com  # Network OK?
   ls -la signals/  # File permissions OK?
   ```

4. Recreate test with minimal setup:
   - Run Python with single test event
   - Verify signal.json created
   - Manually copy to MT5
   - Watch EA execute single trade
   - Verify heartbeat returned

5. Contact: Add issue details to GitHub/Slack with:
   - Timestamp of issue
   - Complete error message(s)
   - Relevant log excerpts
   - Steps to reproduce
