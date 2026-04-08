# End-to-End Integration Test Procedure

## Overview

Complete step-by-step procedure for validating the signal pipeline from Python engine to MT5 trade execution.

**Duration:** 10-15 minutes  
**Signals Expected:** 1-3 per minute  
**Trades Expected:** 30-50% of signals (rest filtered by risk rules)

---

## PART 1: Python Engine Setup & Initialization

### Step 1.1: Open Terminal Session 1 (Python Engine)

```bash
cd /root/signal-engine
```

### Step 1.2: Edit run.py for Testing

Open `run.py` and set polling interval to 10 seconds (for faster signals during testing):

```python
# In run.py, find and modify:
POLL_INTERVAL_SECONDS = 10  # Changed from 300 for testing

# Also verify:
SIGNAL_FILE_PATH = "signals/signal.json"
HEARTBEAT_FILE_PATH = "signals/heartbeat.json"
LOG_FILE = "logs/engine.log"
SIGNALS_CSV = "logs/signals.csv"
```

### Step 1.3: Start Python Engine

```bash
python run.py
```

**Expected Output (first 10 lines):**
```
[2026-04-07 14:23:45.123] INFO - Engine initialized
[2026-04-07 14:23:45.124] INFO - Config loaded from config/settings.json
[2026-04-07 14:23:45.125] INFO - Polling interval: 10 seconds
[2026-04-07 14:23:45.126] INFO - WorldMonitor API: https://worldmonitor-api/events
[2026-04-07 14:23:45.127] INFO - Signal file: signals/signal.json
[2026-04-07 14:23:45.128] INFO - Heartbeat file: signals/heartbeat.json
[2026-04-07 14:23:45.129] INFO - Starting event polling loop...
[2026-04-07 14:23:45.130] INFO - Press Ctrl+C to stop
[2026-04-07 14:23:55.555] INFO - Fetching events from WorldMonitor API...
[2026-04-07 14:23:56.123] INFO - Fetched 2 new events (evt_abc123, evt_def456)
```

**Verification:**
- [ ] No errors in output
- [ ] "Press Ctrl+C to stop" message appears
- [ ] Polling starts immediately

**Keep this terminal open throughout test**

---

## PART 2: Signal File Monitoring

### Step 2.1: Open Terminal Session 2 (Signal Monitoring)

```bash
cd /root/signal-engine
```

### Step 2.2: Watch signal.json for Updates

```bash
# Option A: Continuous watch (recommended):
watch -n 2 'cat signals/signal.json | jq .'

# Option B: Tail for changes:
tail -f signals/signal.json

# Option C: Single check:
cat signals/signal.json | jq .
```

**Expected Output (after 10-20 seconds):**
```json
{
  "timestamp": "2026-04-07T14:23:56.123Z",
  "signals": [
    {
      "event_id": "evt_abc123",
      "symbol": "EURUSD",
      "action": "BUY",
      "confidence": 0.92,
      "reason": "Bullish momentum detected in EU region"
    }
  ]
}
```

### Step 2.3: Observe Signal Generation Pattern

Watch for at least 2-3 minutes (should see 12-18 signals):

- [ ] Timestamp updates every 10 seconds
- [ ] New event_ids appear regularly
- [ ] Confidence scores between 0.5-1.0
- [ ] Actions are BUY, SELL, or HOLD
- [ ] Symbols are valid (EURUSD, GBPUSD, USDJPY, etc.)

**Example 2-minute sequence:**
```
14:23:56 - 2 signals (evt_abc123, evt_def456)
14:24:06 - 1 signal  (evt_ghi789)
14:24:16 - 3 signals (evt_jkl012, evt_mno345, evt_pqr678)
14:24:26 - 2 signals (evt_stu901, evt_vwx234)
14:24:36 - 1 signal  (evt_yza567)
```

**Keep this terminal open throughout test**

---

## PART 3: MT5 File Sync Configuration

### Step 3.1: Open Terminal Session 3 (File Sync)

```bash
cd /root/signal-engine
```

### Step 3.2: Start Sync Script (Automated Option)

```bash
python tests/ea_python_integration/sync_signal_to_mt5.py \
  --mt5-path "/Volumes/Stratos/Users/<user>/AppData/Roaming/MetaTrader 5/MQL5/Files" \
  --watch 300 \
  --verbose
```

**Expected Output:**
```
[14:23:55] Sync script started
[14:23:55] Monitoring signals/signal.json for changes
[14:23:55] MT5 path: /Volumes/Stratos/Users/.../MQL5/Files
[14:23:56] Change detected (size: 1,234 bytes)
[14:23:56] Syncing signal.json...
[14:23:57] ✓ Synced 2 signals to MT5
[14:23:57] Last updated: 2026-04-07T14:23:56.123Z
[14:24:06] Change detected (size: 1,456 bytes)
[14:24:06] Syncing signal.json...
[14:24:07] ✓ Synced 1 signal to MT5
```

**Verification:**
- [ ] Script detects changes every 10 seconds
- [ ] Sync completes within 1-2 seconds
- [ ] No permission errors

**Alternative: Manual Copy (if not using sync script)**

If automated sync unavailable, manually copy every minute:
```bash
# Run in another terminal window every 60 seconds:
cp signals/signal.json "/Volumes/Stratos/Users/<user>/AppData/Roaming/MetaTrader 5/MQL5/Files/"
echo "[$(date)] Signal copied to MT5"
```

**Keep sync terminal open throughout test**

---

## PART 4: EA Execution Monitoring

### Step 4.1: Prepare MT5 for Monitoring

1. Open MetaTrader 5 on Stratos Windows machine
2. Verify GeoSignal EA is running (symbol shows expert icon)
3. Open Journal (View → Journal)
4. Filter for "Expert Advisors" and "GeoSignal EA"
5. Scroll to bottom (most recent messages)

### Step 4.2: Watch for Execution Messages

Over the next 5-10 minutes, watch MT5 Journal for messages like:

**Signal Received:**
```
[14:23:57] GeoSignal EA: Signal received - BUY EURUSD (confidence: 0.92)
```

**Risk Gate Validation:**
```
[14:23:57] GeoSignal EA: Risk check: confidence OK (0.92 >= 0.50)
[14:23:57] GeoSignal EA: Risk check: position limit OK (1 < 5 open)
[14:23:57] GeoSignal EA: Risk check: margin OK ($15,234 >= $500)
[14:23:57] GeoSignal EA: Risk check: position size OK (0.1 <= 0.5)
```

**Trade Execution:**
```
[14:23:58] GeoSignal EA: PASSED all risk gates - executing trade
[14:23:58] GeoSignal EA: OrderSend: BUY 0.1 EURUSD @ 1.0856
[14:23:58] GeoSignal EA: Trade executed - Ticket: 123456789
[14:23:58] GeoSignal EA: SL: 1.0836, TP: 1.0876
```

**Risk Gate Failure (signal held):**
```
[14:23:57] GeoSignal EA: Risk check FAILED: Daily loss exceeded ($487 > $500)
[14:23:57] GeoSignal EA: Signal held - will retry next cycle
```

### Step 4.3: Verification Checklist

Over 10 minutes, you should see:

- [ ] Signal received messages appear (1-3 per minute)
- [ ] Risk check messages for each signal
- [ ] Some signals pass (EXECUTED) and some hold (risk gates)
- [ ] Ticket numbers are numeric (> 0)
- [ ] Entry prices are reasonable (not extreme, not 0)

**Example 5-minute sequence (expecting ~10 signals):**
```
14:23:57 - RECEIVED, PASSED, EXECUTED, ticket: 123456789
14:24:07 - RECEIVED, FAILED (daily loss), HELD
14:24:17 - RECEIVED, PASSED, EXECUTED, ticket: 123456790
14:24:27 - RECEIVED, FAILED (confidence < 0.50), HELD
14:24:37 - RECEIVED, PASSED, EXECUTED, ticket: 123456791
...
```

---

## PART 5: Trade Execution Verification

### Step 5.1: Check MT5 Trades Panel

1. In MetaTrader 5, go to Terminal → Trades tab
2. Should see new open positions matching executed signals

**Expected output:**
```
Symbol    | Type | Volume | Open Price | Time         | Ticket
EURUSD    | BUY  | 0.1    | 1.0856     | 14:23:58     | 123456789
GBPUSD    | BUY  | 0.2    | 1.2734     | 14:24:18     | 123456790
USDJPY    | SELL | 0.1    | 150.32     | 14:24:38     | 123456791
```

**Verification:**
- [ ] At least 1-3 trades visible
- [ ] Volume matches risk parameters (0.1-0.5 lots)
- [ ] Open prices are reasonable (not 0, not extreme)
- [ ] Tickets match EA journal entries

### Step 5.2: Check Trade Details

Click on a trade in the Trades panel to see details:

```
Ticket:        123456789
Symbol:        EURUSD
Type:          BUY
Volume:        0.1 lots
Open Price:    1.0856
Open Time:     2026-04-07 14:23:58
Stop Loss:     1.0836 (20 pips)
Take Profit:   1.0876 (20 pips)
Profit/Loss:   +$50 (current)
Swap:          -$0.50
Commission:    -$1.00
```

**Verification:**
- [ ] SL is below entry for BUY (above for SELL)
- [ ] TP is above entry for BUY (below for SELL)
- [ ] SL/TP distances match symbol configuration

---

## PART 6: Heartbeat Monitoring & Log Correlation

### Step 6.1: Check Heartbeat File

On Mac (Terminal Session 2, or new terminal):

```bash
cat signals/heartbeat.json | jq .
```

**Expected Output:**
```json
{
  "timestamp": "2026-04-07T14:23:58.456Z",
  "signal_id": "evt_abc123",
  "executed": true,
  "status": "success",
  "ticket": 123456789,
  "order_type": "BUY",
  "symbol": "EURUSD",
  "entry_price": 1.0856,
  "position_size": 0.1,
  "error_reason": ""
}
```

**Verification:**
- [ ] heartbeat.json created after first trade
- [ ] signal_id matches Python event_id
- [ ] executed = true when trade successful
- [ ] ticket matches MT5 journal ticket
- [ ] entry_price matches MT5 Trades panel

### Step 6.2: Monitor Heartbeat Updates

```bash
# Watch for heartbeat updates every 60 seconds (or per EA poll cycle):
watch -n 2 'cat signals/heartbeat.json | jq .timestamp'
```

**Expected sequence:**
```
2026-04-07T14:23:58.456Z
2026-04-07T14:24:08.567Z
2026-04-07T14:24:18.678Z
...
```

### Step 6.3: Check Python Logs

View Python engine logs to see heartbeat responses:

```bash
# View last 20 log lines:
tail -20 logs/engine.log
```

**Expected Output:**
```
[2026-04-07 14:23:56] Signal evt_abc123: BUY EURUSD (confidence: 0.92)
[2026-04-07 14:23:58] Heartbeat received: signal_id=evt_abc123
[2026-04-07 14:23:58] Trade executed: ticket=123456789, price=1.0856
[2026-04-07 14:23:58] Latency: 2 seconds
[2026-04-07 14:24:06] Signal evt_def456: BUY GBPUSD (confidence: 0.87)
[2026-04-07 14:24:08] Heartbeat received: signal_id=evt_def456
[2026-04-07 14:24:08] Trade executed: ticket=123456790, price=1.2734
[2026-04-07 14:24:08] Latency: 2 seconds
```

### Step 6.4: Check Signals CSV Log

```bash
tail -10 logs/signals.csv
```

**Expected CSV Format:**
```csv
timestamp,event_id,symbol,action,confidence,ticket,status,latency_sec
2026-04-07T14:23:56.123Z,evt_abc123,EURUSD,BUY,0.92,123456789,success,2
2026-04-07T14:24:06.234Z,evt_def456,GBPUSD,BUY,0.87,123456790,success,2
2026-04-07T14:24:16.345Z,evt_ghi789,USDJPY,SELL,0.91,123456791,success,2
2026-04-07T14:24:26.456Z,evt_jkl012,EURUSD,HOLD,0.55,,,
```

**Verification:**
- [ ] One line per signal generated
- [ ] signal_id matches event_id
- [ ] ticket field populated for executed trades
- [ ] status = "success" for executed trades
- [ ] latency < 300 seconds (5 minutes)

---

## PART 7: End-to-End Latency Calculation

### Calculate Signal-to-Execution Latency

For each executed signal:

```
Latency = heartbeat_timestamp - signal_timestamp
```

**Example:**
```
Signal generated:     2026-04-07T14:23:56.123Z
Heartbeat received:   2026-04-07T14:23:58.456Z
Latency:              2.333 seconds ✓ (within expected range)
```

### View Latency Statistics

```bash
# Generate statistics from signals.csv:
python tests/ea_python_integration/verify_trade_execution.py
```

**Expected Output:**
```
=== EXECUTION REPORT ===

Signals Generated:    42
Signals Executed:     18 (42.9%)
Signals Held:         22 (52.4%)
Failed Signals:        2 (4.8%)

Latency Statistics:
  Min:               1.2 seconds
  Avg:               2.4 seconds
  Max:              14.3 seconds

Risk Gate Summary:
  Confidence gate:   22 blocked
  Margin gate:        0 blocked
  Position limit:     0 blocked
  Daily loss gate:    0 blocked

All Execution Results:
  ✓ ticket=123456789, symbol=EURUSD, latency=2.1s
  ✓ ticket=123456790, symbol=GBPUSD, latency=2.3s
  ✓ ticket=123456791, symbol=USDJPY, latency=1.8s
  ... (15 more)

FINAL STATUS: PASS ✓
All signals matched with heartbeats
All tickets valid and non-zero
Average latency within SLA (< 5 min)
```

---

## PART 8: Test Completion

### Step 8.1: Stop Python Engine

In Terminal Session 1:
```bash
# Press Ctrl+C to stop Python engine
^C
[2026-04-07 14:24:45] Stopping engine...
[2026-04-07 14:24:45] Final statistics logged
[2026-04-07 14:24:45] Engine stopped
```

### Step 8.2: Archive Results

```bash
mkdir -p results/test_2026-04-07
cp logs/engine.log results/test_2026-04-07/
cp logs/signals.csv results/test_2026-04-07/
cp EXECUTION_REPORT.txt results/test_2026-04-07/
cp signals/signal.json results/test_2026-04-07/
cp signals/heartbeat.json results/test_2026-04-07/
```

### Step 8.3: Verify Success Criteria

Open `SUCCESS_CRITERIA.md` and check all 15+ items:

```bash
cat SUCCESS_CRITERIA.md
```

Mark each checkbox:
- [ ] Python engine ran continuously
- [ ] signal.json updated every 10 seconds
- [ ] signal.json synced to MT5 within 60 seconds
- [ ] EA read signals and logged execution
- ... (12 more criteria)
```

**Go/No-Go Decision:**
- If ≥14/15 criteria pass → **PASS** ✓
- If <14/15 criteria pass → **FAIL** ✗ (see TROUBLESHOOTING.md)

---

## Expected Test Duration

| Phase | Time | Task |
|-------|------|------|
| 1 | 30s | Python engine startup |
| 2 | 2m | Signal generation observation |
| 3 | 1m | File sync setup |
| 4 | 5-7m | EA execution monitoring |
| 5 | 2m | Trade verification |
| 6 | 2m | Heartbeat & logs check |
| 7 | 1m | Latency calculation |
| 8 | 1m | Results archival |
| **Total** | **15m** | **Full test** |

---

## Next Steps

1. **Pass?** → Proceed to SUCCESS_CRITERIA.md, update TEST_RESULTS_TEMPLATE.md
2. **Fail?** → Check TROUBLESHOOTING.md for diagnosis
3. **Questions?** → Review DATA_FLOW.md for understanding signal pipeline
4. **Production?** → Change POLL_INTERVAL_SECONDS back to 300 in run.py
