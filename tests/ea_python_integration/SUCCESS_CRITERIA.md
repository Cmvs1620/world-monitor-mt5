# Integration Test Success Criteria

## Go/No-Go Decision Framework

A test is **PASS** (go to production) if **≥14 of 15** criteria are met.

A test is **FAIL** (no-go) if **<14 of 15** criteria are met.

---

## Core Signal Pipeline Criteria

### Criterion 1: Python Engine Initialization
**Description:** Python engine starts without errors and logs initialization

**Expected Behavior:**
```
[2026-04-07 14:23:45.123] INFO - Engine initialized
[2026-04-07 14:23:45.125] INFO - Polling interval: 10 seconds
[2026-04-07 14:23:45.129] INFO - Starting event polling loop...
```

**Test Method:**
- Run `python run.py` in Terminal 1
- Check logs/engine.log for initialization messages
- No fatal errors in first 10 lines

**Pass Condition:** ✓ Engine starts, no initialization errors
**Fail Condition:** ✗ Engine exits with error, missing config file, API key invalid

### Criterion 2: WorldMonitor Event Fetching
**Description:** Python engine successfully fetches events from WorldMonitor API

**Expected Behavior:**
```
[2026-04-07 14:23:55] INFO - Fetching events from WorldMonitor API...
[2026-04-07 14:23:56] INFO - Fetched 2 new events (evt_abc123, evt_def456)
```

**Test Method:**
- Monitor logs/engine.log for fetch messages
- Check for event_id format: evt_XXXXXXX
- Should see 1-3 events per 10-second cycle
- Duration: 2-3 minutes (6-9 cycles)

**Pass Condition:** ✓ Events fetched every 10 seconds, event_ids present
**Fail Condition:** ✗ API timeout, 0 events fetched, API error 403/401

### Criterion 3: Claude Classification & Signal Generation
**Description:** Python engine calls Claude API and generates BUY/SELL/HOLD signals

**Expected Behavior:**
```
[2026-04-07 14:23:56] INFO - Classifying 2 events with Claude...
[2026-04-07 14:23:57] INFO - Classification complete: confidence=0.92
[2026-04-07 14:23:57] INFO - Signal generated: BUY EURUSD
```

**Test Method:**
- Monitor logs/engine.log for classification messages
- Check for confidence scores (0.5 to 1.0)
- Check for action: BUY, SELL, or HOLD

**Pass Condition:** ✓ Claude called, signals generated with valid confidence
**Fail Condition:** ✗ Claude API fails, confidence outside range, no signal output

### Criterion 4: signal.json File Written
**Description:** Python engine writes signal.json with correct structure

**Expected Behavior:**
```json
{
  "timestamp": "2026-04-07T14:23:56.123Z",
  "signals": [
    {
      "event_id": "evt_abc123",
      "symbol": "EURUSD",
      "action": "BUY",
      "confidence": 0.92,
      "reason": "Bullish momentum"
    }
  ]
}
```

**Test Method:**
- `cat signals/signal.json | jq .`
- Verify all fields present
- Check timestamp is ISO 8601 format
- Check symbol is valid (EURUSD, GBPUSD, USDJPY, etc.)

**Pass Condition:** ✓ signal.json valid JSON, all fields present
**Fail Condition:** ✗ File missing, corrupted JSON, missing fields

### Criterion 5: signal.json Updates Every 10 Seconds
**Description:** signal.json timestamp and content change every polling cycle

**Expected Behavior:**
```
14:23:56 - timestamp: 2026-04-07T14:23:56.123Z
14:24:06 - timestamp: 2026-04-07T14:24:06.234Z
14:24:16 - timestamp: 2026-04-07T14:24:16.345Z
```

**Test Method:**
- Monitor signals/signal.json for 3+ minutes
- Check timestamp changes every 10 seconds
- Verify new event_ids appear in each cycle

**Pass Condition:** ✓ Timestamp updates every 10±2 seconds, new signals appear
**Fail Condition:** ✗ No updates, stale data, timestamps unchanged

---

## File Transfer & Synchronization Criteria

### Criterion 6: signal.json Copied to MT5 Files Folder
**Description:** signal.json successfully transferred from Mac to Stratos MT5 Files

**Expected Behavior:**
- signal.json appears in: C:\Users\X\AppData\Roaming\MetaTrader 5\MQL5\Files\
- File size: 500-5000 bytes
- File is readable by MT5 process

**Test Method:**
- Use sync_signal_to_mt5.py OR manual copy
- Verify file appears on Stratos within 60 seconds
- Check `stat` or Properties to confirm modification time

**Pass Condition:** ✓ File copied, size reasonable, readable by MT5
**Fail Condition:** ✗ File missing, permission denied, size=0

### Criterion 7: File Sync Latency < 60 Seconds
**Description:** signal.json transferred to MT5 within 60 seconds of Python write

**Expected Behavior:**
```
Mac:     14:23:56 - signal.json written (timestamp: 2026-04-07T14:23:56.123Z)
Stratos: 14:23:57 - signal.json appears (1 second latency)
```

**Test Method:**
- Note timestamp in signal.json (Mac)
- Check arrival time on Stratos (clock synchronized)
- Latency = (arrival_time - write_time)
- Expected: 1-10 seconds, max 60 seconds

**Pass Condition:** ✓ Latency < 60 seconds for all syncs
**Fail Condition:** ✗ Latency > 60 seconds, file doesn't arrive

---

## EA Execution & Trading Criteria

### Criterion 8: EA Reads Signal File
**Description:** Expert Advisor successfully reads signal.json from MT5 Files folder

**Expected Behavior (MT5 Journal):**
```
[14:23:57] GeoSignal EA: Looking for signal at C:\...signal.json
[14:23:57] GeoSignal EA: Signal file found, size: 1,234 bytes
[14:23:57] GeoSignal EA: Signal received - BUY EURUSD
[14:23:57] GeoSignal EA: Parsing JSON...
```

**Test Method:**
- Open MT5 Journal
- Filter for "GeoSignal EA" and "Expert Advisors"
- Watch for "Signal received" messages
- Count: expect 1-3 messages per 10 seconds

**Pass Condition:** ✓ EA reads signals, "received" messages appear every 10s
**Fail Condition:** ✗ File not found, parse errors, no messages

### Criterion 9: Risk Gate Validation
**Description:** EA validates all risk gates before executing trade

**Expected Behavior (MT5 Journal):**
```
[14:23:57] GeoSignal EA: Risk check: confidence OK (0.92 >= 0.50)
[14:23:57] GeoSignal EA: Risk check: margin OK ($15,234 >= $500)
[14:23:57] GeoSignal EA: Risk check: position limit OK (1 < 5)
[14:23:57] GeoSignal EA: All risk gates PASSED
```

**Test Method:**
- Monitor MT5 Journal for risk check messages
- Verify each gate is evaluated
- Check for PASSED or FAILED outcome
- If FAILED: "Risk check FAILED: <reason>"

**Pass Condition:** ✓ Risk gates evaluated, PASS/FAIL logged for each signal
**Fail Condition:** ✗ Risk checks skipped, no PASS/FAIL messages

### Criterion 10: Trade Execution (≥30% Signal-to-Trade Ratio)
**Description:** At least 30% of signals result in executed trades

**Expected Behavior:**
```
Signals Generated: 30
Signals Executed:  10 (33%)  ✓
Signals Held:      18 (60%)  (risk gates blocked)
Failed Signals:     2 (7%)
```

**Test Method:**
- Run `verify_trade_execution.py` after test
- Check "Execution Summary" section
- Calculate: executed_trades / total_signals
- Expected: 20-60% (30-50% typical)

**Pass Condition:** ✓ ≥30% of signals executed as trades (rest blocked by risk rules)
**Fail Condition:** ✗ <30% executed, majority should pass risk gates

### Criterion 11: Trade Ticket Numbers Valid
**Description:** All executed trades have valid ticket numbers

**Expected Behavior (MT5 Journal):**
```
[14:23:58] GeoSignal EA: Trade executed - Ticket: 123456789
[14:24:08] GeoSignal EA: Trade executed - Ticket: 123456790
```

**Test Method:**
- Monitor MT5 Journal for "Ticket: XXXXXXXXX" messages
- Check MT5 Trades panel for order tickets
- Verify tickets are numeric and > 0
- Verify each ticket unique

**Pass Condition:** ✓ All tickets numeric, positive, unique, in both journal and Trades
**Fail Condition:** ✗ Ticket = 0, negative, non-numeric, or mismatches

### Criterion 12: Trades Appear in MT5 Trades Panel
**Description:** Executed trades visible in MT5 Terminal → Trades tab

**Expected Behavior:**
```
Symbol   | Type | Volume | Open Price | Time         | Ticket
EURUSD   | BUY  | 0.1    | 1.0856     | 14:23:58     | 123456789
GBPUSD   | BUY  | 0.2    | 1.2734     | 14:24:08     | 123456790
USDJPY   | SELL | 0.1    | 150.32     | 14:24:18     | 123456791
```

**Test Method:**
- Open MT5 Terminal on Stratos
- Go to Trades tab
- Count open positions
- Verify symbols, volumes, entry prices, tickets

**Pass Condition:** ✓ ≥1 trade visible, correct symbols, prices, volumes
**Fail Condition:** ✗ No trades, mismatched prices, zero volume

---

## Heartbeat & Response Criteria

### Criterion 13: heartbeat.json Created by EA
**Description:** EA writes heartbeat.json response after trade execution

**Expected Behavior:**
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

**Test Method:**
- On Mac, check: `cat signals/heartbeat.json | jq .`
- Verify all fields present
- Check signal_id matches an event_id from signal.json
- Verify executed = true, status = "success"

**Pass Condition:** ✓ heartbeat.json exists, all fields valid, proper JSON
**Fail Condition:** ✗ File missing, corrupted, signal_id mismatch, empty fields

### Criterion 14: Heartbeat signal_id Matches Python event_id
**Description:** heartbeat.json signal_id matches Python engine's original event_id

**Expected Behavior:**
```
Python signal.json:
  "event_id": "evt_abc123"

EA heartbeat.json:
  "signal_id": "evt_abc123"  ✓ Match

logs/signals.csv:
  event_id=evt_abc123, ticket=123456789  ✓ Consistent
```

**Test Method:**
- Extract event_id from signals/signal.json
- Extract signal_id from signals/heartbeat.json
- Extract event_id from logs/signals.csv
- Compare all three: should be identical

**Pass Condition:** ✓ All three IDs match (signal.json, heartbeat.json, signals.csv)
**Fail Condition:** ✗ IDs mismatch, inconsistent tracking across pipeline

### Criterion 15: End-to-End Latency < 5 Minutes
**Description:** Signal generated by Python engine → trade executed by EA in < 5 minutes

**Expected Behavior:**
```
Signal generated: 2026-04-07T14:23:56.123Z
Heartbeat received: 2026-04-07T14:23:58.456Z
Latency: 2.333 seconds ✓ (well within SLA)

Average latency: 2.4 seconds (min: 1.2, max: 14.3)
All trades: < 5 minutes ✓
```

**Test Method:**
- Run `verify_trade_execution.py`
- Check "Latency Statistics" section
- Average should be: 1-5 seconds (testing), 10-300 seconds (production with 300s polls)
- Max should be: < 5 minutes for testing scenario

**Pass Condition:** ✓ Average latency < 5 min, all individual trades < 5 min
**Fail Condition:** ✗ Average > 5 min, or any trade > 5 min (signal never executed)

---

## Summary Checklist

```
CRITERION                                    PASS/FAIL   NOTES
────────────────────────────────────────────────────────────────
1. Python engine initialization             ☐ / ☐
2. WorldMonitor event fetching              ☐ / ☐
3. Claude classification & signals          ☐ / ☐
4. signal.json file written                 ☐ / ☐
5. signal.json updates every 10s            ☐ / ☐
6. signal.json copied to MT5                ☐ / ☐
7. File sync latency < 60s                  ☐ / ☐
8. EA reads signal file                     ☐ / ☐
9. Risk gate validation                     ☐ / ☐
10. Trade execution ≥30%                    ☐ / ☐
11. Ticket numbers valid                    ☐ / ☐
12. Trades in MT5 panel                     ☐ / ☐
13. heartbeat.json created                  ☐ / ☐
14. Heartbeat signal_id matches event_id    ☐ / ☐
15. End-to-end latency < 5 min              ☐ / ☐
────────────────────────────────────────────────────────────────
PASSED:  __ / 15
FAILED:  __ / 15

DECISION: ☐ PASS (14-15 criteria met) → Ready for production
          ☐ FAIL (<14 criteria met)    → Fix issues, re-test
```

---

## How to Record Results

1. After completing E2E_TEST_PROCEDURE.md
2. Run: `python verify_trade_execution.py`
3. Check each criterion above
4. Fill in checklist above
5. Copy SUCCESS_CRITERIA.md to results directory
6. If FAIL: consult TROUBLESHOOTING.md before re-test

---

## Go/No-Go Decision

**PASS** (Go to Production):
- 14-15 criteria met
- All core trading pipeline working
- Signal → Heartbeat latency acceptable
- Risk gates functioning
- Trades executing with valid tickets

**FAIL** (No-Go):
- <14 criteria met
- Critical failures in event fetch, classification, file sync, or EA execution
- Cannot proceed to production until all criteria pass
- See TROUBLESHOOTING.md for diagnosis and fixes

**Marginal** (Conditional):
- 13/15 criteria met (1 failure)
- If failure is non-critical (e.g., one signal failed), may proceed with caution
- Document failure in TEST_RESULTS_TEMPLATE.md
- Plan to fix before next production deployment
