# GeoSignal Expert Advisor (MT5)

**Automated trading EA that reads signals from Python WorldMonitor engine**

## Quick Facts

- **Language:** MQL5 5.0+
- **Platform:** MetaTrader 5 (v5.0+)
- **Magic Number:** 123456
- **Supported Instruments:** 17 (Forex pairs, commodities, indices)
- **Symbol-Agnostic:** Works on any chart timeframe

---

## Overview

The GeoSignal Expert Advisor is an automated trading system that bridges Python's geopolitical event analysis (Phase 1: WorldMonitor) with MetaTrader 5 execution. The EA continuously reads JSON signals from the Python engine, validates them against 5 independent risk gates, and executes trades with automatic position sizing, stop losses, and take profits.

**How it fits together:**
- **Phase 1 (Python Engine):** Fetches geopolitical events, classifies them with Claude AI, generates trading signals → writes `signal.json`
- **Phase 3 (MT5 EA):** Reads `signal.json`, validates risk gates, executes orders → writes `heartbeat.json` for confirmation

Result: Fully automated geopolitical event trading with human-level decision making and strict risk controls.

---

## Features

- **IPC Bridge:** Reads signals from `signal.json` (inter-process communication with Python)
- **5-Level Risk Validation:** Confidence threshold, position limit, duplicate prevention, daily loss limit, drawdown limit
- **Confidence-Scaled Position Sizing:** Automatically calculates lot size based on signal confidence
- **Instrument-Specific Configuration:** 17 pre-configured pairs with custom SL/TP distances (forex, commodities, indices)
- **Real-Time Execution Logging:** Writes to MT5 Journal and timestamped log files
- **Heartbeat Feedback:** Writes `heartbeat.json` to confirm execution status to Python engine
- **DEBUG_MODE:** Verbose logging for troubleshooting
- **Duplicate Prevention:** Tracks last executed event ID to prevent double-execution

---

## File Structure

```
ea/
├── GeoSignalEA.mq5              # Main EA source code (development)
├── GeoSignalEA.ex5              # Compiled binary (deployment ready)
├── includes/
│   ├── signal_struct.mqh         # TradeSignal & ExecutionResult structures
│   └── risk_config.mqh           # Risk parameters & instrument configuration
└── README.md                     # This file
```

---

## Quick Start (3 Steps)

### Step 1: Compile (on Windows with MT5 installed)

1. **Open MetaEditor**
   - Launch MT5
   - Press **F4** (or Tools → MetaEditor)

2. **Open EA Source**
   - File → Open
   - Navigate to: `GeoSignalEA.mq5`
   - Click Open

3. **Compile**
   - Press **F7** (or Compile button)
   - Watch for: **"Compile complete"** message
   - Result: `GeoSignalEA.ex5` file created in same folder

### Step 2: Deploy

**Automated (PowerShell on Windows):**
```powershell
powershell -ExecutionPolicy Bypass -File ..\deploy_ea.ps1 -RestartMT5
```

**Manual:**
1. Copy `GeoSignalEA.ex5` to MT5 Experts folder:
   - Typically: `C:\Users\[YourUser]\AppData\Roaming\MetaQuotes\Terminal\[TerminalID]\MQL5\Experts`
   - Or: File → Open Data Folder → MQL5 → Experts
2. Restart MT5 (or refresh: Tools → Options → Refresh)

### Step 3: Activate

1. **Open a Chart**
   - Pick any symbol (e.g., XAUUSD H1, EURUSD D1)
   - EA works on any timeframe and symbol

2. **Add EA to Chart**
   - Navigator (Ctrl+N)
   - Expert Advisors
   - Right-click **GeoSignalEA** → Add to Chart

3. **Verify Initialization**
   - **Green smiley ✓** appears in top-right corner = EA running
   - **Red sad face ✗** = Error (check Journal tab for details)
   - View Journal: Alt+T (see execution logs in real-time)

---

## Configuration

### Input Parameters

Edit parameters in MT5 after adding EA to chart:
1. Right-click EA on chart → **Modify**
2. Find input parameter
3. Change value and click **OK**
4. EA restarts with new settings (no recompile needed)

| Parameter | Default | Range | Purpose |
|-----------|---------|-------|---------|
| **EA_ENABLED** | `true` | bool | Master enable/disable switch |
| **EA_TRADING_ENABLED** | `false` | bool | When false, EA monitors only (no actual trades) |
| **POLL_INTERVAL_SECONDS** | `5` | 5–3600 | How often to check signal.json for new signals |
| **BRIDGE_TIMEOUT_SECONDS** | `30` | 5–300 | Timeout waiting for signal file response |
| **MAX_CONCURRENT_POSITIONS** | `5` | 1–10 | Maximum open trades allowed simultaneously |
| **RISK_PER_TRADE_PERCENT** | `2.0` | 0.1–10.0 | Risk % of account balance per trade |
| **MAX_DAILY_LOSS_PERCENT** | `10.0` | 1.0–50.0 | Stop trading if daily loss exceeds this % |
| **MAX_DRAWDOWN_PERCENT** | `15.0` | 5.0–50.0 | Stop trading if equity drawdown exceeds this % |
| **SIGNAL_FILE_PATH** | `signal.json` | string | Filename in MT5 Files folder (usually `signal.json`) |
| **DEBUG_MODE** | `false` | bool | Verbose logging to Journal (useful for testing) |

**Example: Safe Testing Setup**
```
EA_TRADING_ENABLED = false   (monitor only, no real trades)
DEBUG_MODE = true            (verbose logging)
POLL_INTERVAL_SECONDS = 5    (check frequently)
```

---

## Supported Instruments

EA includes pre-configured SL/TP distances for 17 instruments:

### Forex Pairs (20–25 pip SL, 40–50 pip TP)
- **Major Pairs:** EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, NZDUSD, USDCHF
- **Crosses:** EURGBP, EURJPY, GBPJPY

### Commodities (15 pip SL, 30 pip TP)
- **Energy:** WTIUSD (WTI Crude Oil), BRENTUSD (Brent Oil)
- **Metals:** XAUUSD (Gold)

### Indices (30 pip SL, 60 pip TP)
- **Global:** US30 (Dow), SPX500 (S&P 500), Germany40 (DAX), UK100 (FTSE 100)

**Add or Modify Instruments:**
1. Edit: `ea/includes/risk_config.mqh`
2. Find: `INSTRUMENT_CONFIGS[]` array (lines 42–61)
3. Add new entry: `{"SYMBOL", sl_pips, tp_pips}`
4. Recompile and redeploy

Example: Add Bitcoin (BTCUSD) with 50 pip SL, 100 pip TP:
```cpp
const InstrumentConfig INSTRUMENT_CONFIGS[] =
{
    // ... existing entries ...
    {"BTCUSD",   50, 100},      // Bitcoin: new
};
```

---

## Risk Gates Explained

Before executing any trade, EA validates 5 independent risk gates. All must pass.

### Gate 1: Confidence Threshold
- **Minimum:** 0.5 (50%)
- **Action:** Signals with confidence < 0.5 are **SKIPPED**
- **Example:** Signal arrives with confidence=0.3 → logged as "SKIP: Confidence below threshold" → no trade

### Gate 2: Position Limit
- **Maximum concurrent positions:** 5 (default, configurable)
- **Action:** New signal rejected if 5 trades already open
- **Example:** 5 EURUSD, GBPUSD, XAUUSD, WTIUSD, SPX500 open → new BUY NZDUSD signal → **REJECTED** (at limit)

### Gate 3: Duplicate Symbol Prevention
- **Rule:** Only 1 open trade per symbol allowed
- **Action:** Second signal for same symbol rejected if one already open
- **Example:** BUY EURUSD (ticket 123) already open → BUY EURUSD signal arrives → **REJECTED** (duplicate)

### Gate 4: Daily Loss Limit
- **Default:** -10% of account balance
- **Reset:** Daily at 00:00 UTC
- **Calculation:** Daily P&L = Account Balance - Current Equity
- **Action:** Trading halted if daily loss exceeds threshold
- **Example:** Account $10,000 → daily loss > $1,000 → all new trades blocked until next day

### Gate 5: Drawdown Limit
- **Default:** 15% equity drawdown
- **Action:** Trading halted if equity falls below (100% - 15%) = 85% of balance
- **Example:** Account $10,000 → equity drops to $8,500 ($1,500 loss) → trading halted

---

## Signal File Format

Python engine writes `signal.json` to MT5 Files folder. EA reads and parses this JSON:

```json
{
  "timestamp": "2026-04-08T10:00:00Z",
  "event_id": "evt-12345678",
  "event_title": "Federal Reserve Rate Decision",
  "action": "BUY",
  "symbol": "EURUSD",
  "confidence": 0.75,
  "volume": 1.0,
  "stop_loss": 1.0820,
  "take_profit": 1.0880,
  "rationale": "Fed policy shift expected to weaken USD"
}
```

**Required Fields:**
- `action` – "BUY", "SELL", or "HOLD" (only BUY/SELL execute trades)
- `symbol` – Trading symbol (must match MT5 symbol name)
- `confidence` – Float 0.0–1.0
- `volume` – Suggested lot size (EA may override based on position sizing rules)

**Optional Fields:**
- `stop_loss`, `take_profit` – Price levels. If missing, EA calculates from instrument config
- `event_id`, `event_title`, `rationale` – For logging and record-keeping
- `timestamp` – For tracking signal freshness

**HOLD Action:**
If `action` is "HOLD", EA skips execution (useful for signals that indicate "no trade now").

---

## Execution Flow

```
OnTick() called every tick
  │
  ├─ Is 60+ seconds (POLL_INTERVAL) elapsed?
  │  └─ No → skip, wait next tick
  │  └─ Yes → proceed
  │
  ├─ Read signal.json from MT5 Files folder
  │  ├─ File exists? No → log warning, skip
  │  ├─ Valid JSON? No → log parse error, skip
  │  └─ Valid JSON → parse to TradeSignal struct
  │
  ├─ Is action "HOLD"?
  │  └─ Yes → log "HOLD signal received", skip execution
  │
  ├─ Already executed this event_id?
  │  └─ Yes → log "Duplicate execution, skipping", skip
  │  └─ No → proceed
  │
  ├─ Validate 5 Risk Gates
  │  ├─ Gate 1: confidence ≥ 0.5?
  │  ├─ Gate 2: open positions < MAX_CONCURRENT?
  │  ├─ Gate 3: no trade already open on symbol?
  │  ├─ Gate 4: daily loss < limit?
  │  └─ Gate 5: drawdown < limit?
  │  └─ Any fail → log SKIP reason, abort
  │  └─ All pass → proceed
  │
  └─ ExecuteSignal()
     ├─ Get instrument config (SL/TP distances for symbol)
     ├─ Calculate position size (confidence × account × risk%)
     ├─ Calculate SL/TP from instrument config (if not provided)
     ├─ Place market order (BUY or SELL via CTrade)
     ├─ Update last_executed_signal_id (prevent duplicates)
     ├─ Log success/failure to Journal
     ├─ Write heartbeat.json response
     └─ Done
```

---

## Monitoring & Logging

### MT5 Journal (Real-Time Execution Log)

View execution logs live:
- **Keyboard:** Alt+T
- **Menu:** View → Toolbars → Journal Tab

**Example Output:**
```
[EA] Executing: BUY EURUSD (confidence: 0.75)
[EA] SUCCESS: BUY 1.0 EURUSD at 1.0850 | Ticket: 123456789
[EA] SKIP: Confidence 0.3 below threshold (0.5)
[EA] SKIP: Already 5 positions open (max: 5)
[EA] SKIP: Duplicate symbol EURUSD already open
[EA] HALT: Daily loss -10.5% exceeds limit -10.0%
[EA] HALT: Drawdown -15.2% exceeds limit -15.0%
```

### Heartbeat Response File

After execution, EA writes confirmation to `signals/heartbeat.json`:

```json
{
  "timestamp": "2026-04-08T10:00:15Z",
  "signal_id": "evt-12345678",
  "executed": true,
  "status": "success",
  "ticket": 123456789,
  "error_reason": ""
}
```

**Fields:**
- `executed` – true/false (was order placed?)
- `status` – "success", "skipped", or "error"
- `ticket` – MT5 order ticket number (0 if failed)
- `error_reason` – Description if status is "error"

Python engine reads this file to:
- Avoid sending duplicate signals
- Confirm execution for record-keeping
- Adjust future signal confidence if execution fails

### Log File

Timestamped file-based logging:
- **Location:** MT5 Files folder (usually `Files/ea_execution.log`)
- **Content:** All events logged with ISO timestamps
- **Use:** Backup logging (when Journal is unavailable or for historical review)

---

## Troubleshooting

### Issue: Red Sad Face ✗ in Corner

**Symptom:** EA shows error indicator instead of green checkmark.

**Diagnosis:**
1. Open Journal (Alt+T)
2. Look for EA error message
3. Check for common issues below

**Common Fixes:**

| Error | Fix |
|-------|-----|
| `Automated trading not allowed` | Tools → Options → Expert Advisors → Enable "Allow automated trading" |
| `signal.json not found` | Verify file exists in MT5 Files folder. Check SIGNAL_FILE_PATH parameter |
| `JSON parse error` | Ensure signal.json is valid JSON (Python engine might be stopped or crashed) |
| `Cannot open log file` | Check MT5 has write permission to Files folder |
| `Forbidden operation` | EA may be running on read-only chart or demo account restrictions |

---

### Issue: No Trades Executing

**Symptom:** EA is running (green checkmark) but not placing any trades.

**Checklist:**
- [ ] EA_TRADING_ENABLED = true (not false for "monitor only" mode)
- [ ] POLL_INTERVAL_SECONDS is reasonable (5–60 seconds typical)
- [ ] signal.json contains valid action "BUY" or "SELL" (not "HOLD")
- [ ] Confidence score ≥ 0.5 (check Journal for "SKIP: Confidence below threshold")
- [ ] Position limit not exceeded (check Journal for "SKIP: Already 5 positions open")
- [ ] No duplicate symbol (check Journal for "SKIP: Duplicate symbol X already open")
- [ ] Daily loss limit not breached (check Journal for "HALT: Daily loss exceeds limit")
- [ ] Python engine still running (check signal.json timestamp is recent, not stale)

**Quick Test:**
1. Set DEBUG_MODE = true
2. Right-click EA → Modify → OK
3. Watch Journal output in real-time
4. Manually check signal.json file (File → Open Data Folder → Files → signal.json)
5. Verify timestamp is within last minute

---

### Issue: Wrong Position Size

**Symptom:** Orders placed with unexpected lot sizes (too small or too large).

**How Position Size is Calculated:**
```
position_size_lots = (account_balance × confidence × RISK_PER_TRADE_PERCENT) 
                   / (stop_loss_pips × point_value × 100000)
```

**Clamped:** Min 0.01 lots, Max 10.0 lots

**Example:**
- Account: $10,000
- Signal confidence: 0.75
- RISK_PER_TRADE_PERCENT: 2.0
- Stop loss: 20 pips
- Expected: roughly 0.75 lots

**Fixes:**
1. **If too small:** Increase RISK_PER_TRADE_PERCENT (more risk per trade)
2. **If too large:** Decrease RISK_PER_TRADE_PERCENT (less risk per trade)
3. **Permanent changes:** Edit `CalculatePositionSize()` function in `ea/includes/risk_config.mqh`

---

### Issue: EA Reads Stale Signal

**Symptom:** EA executes very old signals or repeats same signal.

**Causes:**
1. Python engine crashed/stopped writing signal.json
2. signal.json file timestamp is old
3. Event ID filtering not working

**Fixes:**
1. Verify Python engine is running: `ps aux | grep "world_monitor\|python"`
2. Check signal.json file (File → Open Data Folder → Files → signal.json):
   - Timestamp should be recent (within last POLL_INTERVAL_SECONDS)
   - Action should be "BUY" or "SELL" (not "HOLD")
3. Check EA log for "Duplicate execution" messages
4. Increase POLL_INTERVAL_SECONDS if signal.json updates slowly

---

## Python Integration

The EA and Python engine communicate via two JSON files in the MT5 Files folder:

```
Python Engine (Phase 1)
  │
  ├─ Fetch geopolitical events (news APIs, databases)
  ├─ Classify with Claude AI
  ├─ Generate trading signal
  │
  └─ Write signal.json ──→ [MT5 Files folder]
                           │
                    ┌──────┴──────┐
                    │ EA reads    │
                    │ signal.json │
                    │             │
                    ├─ Validate  ├─ Execute trade
                    │ risk gates  │
                    │             │
                    └─────┬───────┘
                          │
                    Write heartbeat.json
                          │
                          └──→ Python reads confirmation
                             ├─ Verify execution
                             ├─ Update records
                             └─ Avoid duplicate signals
```

**Key Coordination:**
- **signal.json:** Python → MT5 (Python writes, EA reads)
- **heartbeat.json:** MT5 → Python (EA writes, Python reads)
- Both files in: MT5 Files folder (e.g., `C:\Users\...\AppData\Roaming\MetaQuotes\Terminal\...\MQL5\Files`)

---

## Safety Features

1. **Duplicate Prevention**
   - EA tracks `last_executed_signal_id`
   - Same event ID cannot execute twice
   - Prevents accidental double-trading if signal.json is read multiple times

2. **5-Level Risk Validation**
   - Confidence threshold (0.5 minimum)
   - Position limit (max 5 concurrent)
   - Duplicate symbol prevention
   - Daily loss limit (default -10%)
   - Drawdown limit (default -15%)

3. **Magic Number Identification**
   - All orders tagged with magic 123456
   - Allows EA to identify which orders it placed
   - Helps when running multiple EAs on same account

4. **Slippage Tolerance**
   - Default: 10 points maximum slippage
   - Prevents orders from filling at bad prices during gaps

5. **Position Sizing**
   - Always confidence-scaled (high confidence = larger position)
   - Limited by account % risk (never risks > 2% of account per trade)
   - Clamped minimum (0.01 lots) and maximum (10.0 lots)

---

## Advanced Configuration

### Modify Instrument Stop Loss / Take Profit

Edit pre-configured SL/TP for instruments:

1. **File:** `ea/includes/risk_config.mqh`
2. **Find:** `INSTRUMENT_CONFIGS[]` array (lines 42–61)
3. **Edit:** Change pip values for any symbol
4. **Recompile:** Press F7 in MetaEditor
5. **Redeploy:** Copy new .ex5 to Experts folder and restart MT5

**Example: Tighten Gold (XAUUSD) stops**
```cpp
// Before
{"XAUUSD",   15, 30},   // Gold: SL=15, TP=30

// After (tighter stops)
{"XAUUSD",   8, 16},    // Gold: SL=8, TP=16 (more sensitive)
```

### Modify Position Sizing Formula

Edit risk calculation logic:

1. **File:** `ea/includes/risk_config.mqh`
2. **Find:** `CalculatePositionSize()` function (lines 103–132)
3. **Modify:** Risk percentage, lot clamping, rounding logic
4. **Recompile & Redeploy**

**Example: Increase max lot size**
```cpp
// Before
if(position_size > 10.0)
    position_size = 10.0;

// After (allow up to 50 lots)
if(position_size > 50.0)
    position_size = 50.0;
```

### Change Risk Thresholds (No Recompile)

Most risk parameters are input parameters (adjustable in MT5 without recompile):

- **EA_ENABLED** – Master switch
- **MAX_CONCURRENT_POSITIONS** – Position limit
- **RISK_PER_TRADE_PERCENT** – Risk per trade
- **MAX_DAILY_LOSS_PERCENT** – Daily loss limit
- **MAX_DRAWDOWN_PERCENT** – Drawdown limit

Right-click EA on chart → Modify → Adjust values → OK

---

## Performance Notes

- **Signal Poll Interval:** Default 5 seconds (adjustable 5–3600)
- **Typical Execution Latency:** <5 seconds (signal read to order placement)
- **Logging Overhead:** Minimal (asynchronous file writes)
- **Chart Compatibility:** Works on any symbol, any timeframe (1M, 5M, H1, D1, W1, etc.)
- **EA Footprint:** ~100 KB compiled binary
- **Memory Usage:** <5 MB (very lightweight)

---

## Version & Support

- **Version:** 1.0.0
- **Built For:** Phase 3 (Python Integration)
- **MQL5 Version:** 5.0+
- **MT5 Version:** 5.0+
- **Last Updated:** 2026-04-08

### Getting Help

1. **Journal Tab** (Alt+T) – View execution logs and error messages
2. **Troubleshooting Section** (above) – Common issues and fixes
3. **DEBUG_MODE** – Enable for verbose logging
4. **Phase 3 Test Logs** – Review test execution history for similar issues

---

## File Locations Reference

| Item | Location |
|------|----------|
| **EA Source** | `ea/GeoSignalEA.mq5` |
| **EA Compiled** | `ea/GeoSignalEA.ex5` |
| **Includes** | `ea/includes/signal_struct.mqh`, `ea/includes/risk_config.mqh` |
| **MT5 Experts Folder** | `C:\Users\[User]\AppData\Roaming\MetaQuotes\Terminal\[ID]\MQL5\Experts` |
| **MT5 Files Folder** | `C:\Users\[User]\AppData\Roaming\MetaQuotes\Terminal\[ID]\MQL5\Files` |
| **signal.json** | MT5 Files folder (written by Python engine) |
| **heartbeat.json** | MT5 Files folder (written by EA after execution) |
| **ea_execution.log** | MT5 Files folder (timestamped execution log) |

---

## Quick Command Reference

| Task | Command |
|------|---------|
| **Compile EA** | F7 (in MetaEditor) |
| **Open Journal** | Alt+T (in MT5) |
| **Open Data Folder** | File → Open Data Folder (in MT5) |
| **Modify EA Parameters** | Right-click EA on chart → Modify |
| **Remove EA from Chart** | Right-click EA on chart → Remove |
| **View Experts Folder** | File → Open Data Folder → MQL5 → Experts |
| **Refresh EA List** | Tools → Options → Refresh |

---

## Checklist: First-Time Setup

- [ ] Compile GeoSignalEA.mq5 (F7) and verify GeoSignalEA.ex5 is created
- [ ] Copy GeoSignalEA.ex5 to MT5 Experts folder
- [ ] Restart MT5
- [ ] Open a chart (e.g., EURUSD H1)
- [ ] Add EA to chart (Ctrl+N → Expert Advisors → GeoSignalEA)
- [ ] Verify green checkmark appears
- [ ] Set EA_TRADING_ENABLED = false (monitor-only mode for testing)
- [ ] Set DEBUG_MODE = true (verbose logging)
- [ ] Open Journal (Alt+T)
- [ ] Verify Python engine is running and signal.json is being updated
- [ ] Watch for execution logs in Journal
- [ ] Once confident, set EA_TRADING_ENABLED = true for live trading

---

**Ready to trade!** For verification of a working end-to-end flow, ask to verify that signals are being read and executed correctly.
