# Integration Test Data Flow Diagram

## End-to-End Signal Pipeline: Python Engine → EA Execution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PHASE 1: PYTHON ENGINE (Mac)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐    │
│  │ WorldMonitor API │────▶│ Event Fetcher    │────▶│ Claude Classifier│    │
│  │ (every 10s)      │     │ (poll_interval)  │     │ (risk analysis)  │    │
│  └──────────────────┘     └──────────────────┘     └──────────────────┘    │
│         [T0]                    [T0+1s]                    [T0+2s]          │
│                                                                              │
│                                                              │               │
│                                                              ▼               │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │ signals/signal.json                                             │       │
│  ├─────────────────────────────────────────────────────────────────┤       │
│  │ {                                                               │       │
│  │   "timestamp": "2026-04-07T14:23:56.123Z",                     │       │
│  │   "signals": [                                                  │       │
│  │     {                                                           │       │
│  │       "event_id": "evt_abc123",                                │       │
│  │       "symbol": "EURUSD",                                      │       │
│  │       "action": "BUY",                                         │       │
│  │       "confidence": 0.92,                                      │       │
│  │       "reason": "Bullish momentum"                             │       │
│  │     }                                                           │       │
│  │   ]                                                             │       │
│  │ }                                                               │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│         [T0+3s]  ◀─── WRITTEN TO DISK                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
              [MANUAL COPY]  [SYNC SCRIPT]  [MONITORING]
                    │               │               │
        Copy to     │       Auto-copy every  Verify updates
        Stratos     │       10 seconds         every 10s
                    │               │               │
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PHASE 3: FILE TRANSFER (Network)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Mac (signal-engine)  ════════════════════════  Stratos MT5 Files Folder   │
│  signals/signal.json         [T0+5s]           signal.json                 │
│  (updated every 10s)     (via SMB share)       (readable by EA)            │
│                                                                              │
│  Network Latency: ~1-2 seconds typical                                      │
│  File Size: ~2-5 KB per signal batch                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 3: EXPERT ADVISOR (Stratos MT5)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  OnStart() ──▶ Initialize                                                   │
│  OnTick()  ──▶ Check for signal.json every 60 seconds                       │
│         [T0+5s] ◀─── FILE WRITTEN BY SYNC/COPY                             │
│                                                                              │
│  Signal Reader:                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │ Read signal.json                                            │           │
│  │ Parse JSON: event_id, symbol, action, confidence           │           │
│  │ Validate signature (if enabled)                             │           │
│  │ Check if already processed (via event_id)                   │           │
│  └─────────────────────────────────────────────────────────────┘           │
│         [T0+6s]                                                             │
│                  │                                                          │
│                  ▼                                                          │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │ Risk Gate Validation (MUST PASS ALL)                        │           │
│  ├─────────────────────────────────────────────────────────────┤           │
│  │ ✓ Confidence >= 0.50                                        │           │
│  │ ✓ Max open positions per symbol < 5                         │           │
│  │ ✓ Account free margin > MIN_MARGIN_DOLLARS                  │           │
│  │ ✓ Position size <= MAX_LOT_SIZE                             │           │
│  │ ✓ Daily loss not exceeded (if enabled)                      │           │
│  │ ✓ Market hours check (if enabled)                           │           │
│  └─────────────────────────────────────────────────────────────┘           │
│         [T0+7s]                                                             │
│                  │                                                          │
│      ┌───────────┼───────────┐                                             │
│      │           │           │                                             │
│   PASS       HOLD        FAIL                                              │
│      │           │           │                                             │
│      ▼           ▼           ▼                                             │
│  Execute    Do Nothing   Log & Continue                                    │
│    Trade                 (try next cycle)                                  │
│      │                                                                      │
│      ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │ Trade Execution                                             │           │
│  ├─────────────────────────────────────────────────────────────┤           │
│  │ Action: BUY → OrderSend(OP_BUY, ...)                        │           │
│  │ Action: SELL → OrderSend(OP_SELL, ...)                      │           │
│  │ Position Size: calculated from confidence + risk_percent    │           │
│  │ Stop Loss: symbol_pair.stop_loss_pips below entry           │           │
│  │ Take Profit: symbol_pair.take_profit_pips above entry       │           │
│  │ Result: ticket number (>0 = success, ≤0 = failure)          │           │
│  └─────────────────────────────────────────────────────────────┘           │
│         [T0+8s]                                                             │
│                  │                                                          │
│                  ▼                                                          │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │ Heartbeat Response (Write to File)                          │           │
│  ├─────────────────────────────────────────────────────────────┤           │
│  │ signals/heartbeat.json                                      │           │
│  │ {                                                           │           │
│  │   "timestamp": "2026-04-07T14:23:58.456Z",                 │           │
│  │   "signal_id": "evt_abc123",                               │           │
│  │   "executed": true,                                        │           │
│  │   "status": "success",                                     │           │
│  │   "ticket": 123456789,                                     │           │
│  │   "order_type": "BUY",                                     │           │
│  │   "entry_price": 1.0856,                                   │           │
│  │   "position_size": 0.1,                                    │           │
│  │   "error_reason": ""                                       │           │
│  │ }                                                           │           │
│  └─────────────────────────────────────────────────────────────┘           │
│         [T0+9s] ◀─── WRITTEN TO DISK                                       │
│                                                                              │
│  MT5 Journal Entry:                                                         │
│  "[14:23:58] GeoSignal EA: Executing BUY EURUSD @ 1.0856 (ticket: 123456789)"
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 1: HEARTBEAT RESPONSE (Mac)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  signals/heartbeat.json ◀───── READ BY PYTHON ENGINE                        │
│         [T0+10s]                                                            │
│            │                                                                │
│            ▼                                                                │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │ Heartbeat Validation & Logging                              │           │
│  ├─────────────────────────────────────────────────────────────┤           │
│  │ ✓ Parse heartbeat.json                                      │           │
│  │ ✓ Match signal_id with original event_id                    │           │
│  │ ✓ Log execution: ticket, entry_price, position_size        │           │
│  │ ✓ Calculate latency: (heartbeat_ts - signal_ts)             │           │
│  │ ✓ Write to logs/signals.csv and logs/engine.log             │           │
│  └─────────────────────────────────────────────────────────────┘           │
│         [T0+11s]                                                            │
│                                                                              │
│  logs/signals.csv:                                                          │
│  timestamp,event_id,symbol,action,confidence,ticket,status,latency_sec     │
│  2026-04-07T14:23:56.123Z,evt_abc123,EURUSD,BUY,0.92,123456789,success,5 │
│                                                                              │
│  logs/engine.log:                                                           │
│  [2026-04-07 14:23:56] Signal evt_abc123: BUY EURUSD (0.92 confidence)     │
│  [2026-04-07 14:23:58] Heartbeat received: ticket 123456789 executed      │
│  [2026-04-07 14:23:58] Latency: 2 seconds                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


## Timeline Summary

```
T0+0s   Python fetches events from WorldMonitor API
T0+1s   Claude classifier analyzes events
T0+2s   Classification complete
T0+3s   signal.json written to disk
T0+5s   signal.json copied to MT5 Files folder (network + file sync)
T0+6s   EA reads signal.json
T0+7s   Risk gate validation completes
T0+8s   Trade executed (OrderSend), order ticket returned
T0+9s   heartbeat.json written by EA
T0+10s  heartbeat.json copied back to Mac
T0+11s  Python engine reads heartbeat and logs execution
        
TOTAL LATENCY: ~11 seconds from event fetch to execution logging
(Max expected latency: 5 minutes if polling at 300s intervals)
```

## File Paths at Each Stage

| Stage | Mac Path | Windows Path | Notes |
|-------|----------|--------------|-------|
| 1 | N/A | N/A | Python fetches from API |
| 2 | N/A | N/A | Claude classification |
| 3 | ~/signal-engine/signals/signal.json | N/A | Initial write |
| 4 | ~/signal-engine/signals/signal.json | C:\Users\X\AppData\Roaming\MetaTrader 5\MQL5\Files\signal.json | Synced via SMB or manual copy |
| 5 | N/A | C:\Users\X\AppData\Roaming\MetaTrader 5\MQL5\Files\signal.json | EA reads from here |
| 6 | N/A | C:\Users\X\AppData\Roaming\MetaTrader 5\MQL5\Files\ | Heartbeat written by EA |
| 7 | ~/signal-engine/signals/heartbeat.json | C:\Users\X\AppData\Roaming\MetaTrader 5\MQL5\Files\heartbeat.json | Copied back or read directly |
| 8 | ~/signal-engine/logs/signals.csv | N/A | Python logs execution |

## Network Topology

```
┌──────────────────────┐              ┌──────────────────────┐
│   Python Engine      │              │   MT5 / Expert       │
│   (Mac)              │◀─── SMB ────▶│   Advisor             │
│                      │    Share     │   (Stratos Windows)  │
│ signals/             │              │                      │
│ - signal.json ◀──────┤ File Sync    │ MQL5/Files/          │
│ - heartbeat.json     │              │ - signal.json        │
│ - logs/              │              │ - heartbeat.json     │
└──────────────────────┘              └──────────────────────┘

Signal Flow:
Python → signal.json → (SMB) → EA → heartbeat.json → (SMB) → Python
```

## Latency Components

```
Total Latency = T_fetch + T_classify + T_write + T_sync + T_read + T_risk + T_execute + T_heartbeat

T_fetch:       1 sec   (WorldMonitor API request/response)
T_classify:    1 sec   (Claude API call)
T_write:       1 sec   (Write signal.json to disk)
T_sync:        2 sec   (Copy to MT5 via SMB)
T_read:        1 sec   (EA reads signal.json)
T_risk:        1 sec   (Risk gate validation)
T_execute:     1 sec   (OrderSend, ticket returned)
T_heartbeat:   1 sec   (Write heartbeat.json)
────────────────────
Total:        ~10 sec  (best case, polling at 10s intervals)

With 300s polling interval: +290 sec per cycle (until next poll)
Max latency: ~300+ seconds = 5+ minutes
```

## Data Structure Evolution

```
Stage 1: Raw Event (from WorldMonitor API)
{
  "event_id": "evt_abc123",
  "timestamp": "2026-04-07T14:23:45Z",
  "name": "Bullish momentum detected",
  "region": "EU",
  "impact": "high"
}

Stage 2: Classified Signal (Python engine output)
{
  "timestamp": "2026-04-07T14:23:56.123Z",
  "signals": [{
    "event_id": "evt_abc123",
    "symbol": "EURUSD",
    "action": "BUY",
    "confidence": 0.92,
    "reason": "Bullish momentum"
  }]
}

Stage 3: Heartbeat Response (EA output)
{
  "timestamp": "2026-04-07T14:23:58.456Z",
  "signal_id": "evt_abc123",
  "executed": true,
  "status": "success",
  "ticket": 123456789,
  "order_type": "BUY",
  "entry_price": 1.0856,
  "position_size": 0.1,
  "error_reason": ""
}

Stage 4: Python Log Entry
{
  "timestamp": "2026-04-07T14:23:58Z",
  "event_id": "evt_abc123",
  "symbol": "EURUSD",
  "action": "BUY",
  "confidence": 0.92,
  "ticket": 123456789,
  "status": "success",
  "latency_sec": 2
}
```

## Success Conditions

- Signal arrives at EA within POLL_INTERVAL_SECONDS (10s for testing, 300s production)
- All fields present and valid in each stage
- event_id/signal_id consistent across entire flow
- Risk gates either PASS (trade) or HOLD (logged but not executed)
- No file corruption or missing data at any stage
- heartbeat.json returned with matching signal_id and valid ticket
