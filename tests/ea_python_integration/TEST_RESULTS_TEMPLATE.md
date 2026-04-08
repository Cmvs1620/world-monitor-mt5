# Integration Test Results Template

**Test Date:** YYYY-MM-DD  
**Test Duration:** HH:MM - HH:MM (approximately XX minutes)  
**Tester:** [Your Name]  
**Environment:** [Mac/Stratos versions, Python version, MT5 version]  

---

## Summary

| Metric | Value | Notes |
|--------|-------|-------|
| Test Status | PASS / FAIL / CONDITIONAL | |
| Success Criteria Met | __/15 | |
| Total Signals Generated | __ | |
| Total Signals Executed | __ | __% of total |
| Failed Signals | __ | |
| Avg Latency | __ seconds | |
| Longest Latency | __ seconds | |

---

## Part 1: Python Engine Setup

- [ ] Python engine started without errors
- [ ] config/settings.json correctly configured
- [ ] WorldMonitor API accessible
- [ ] Claude API key valid
- [ ] signals/ and logs/ directories created
- [ ] POLL_INTERVAL_SECONDS set to 10 (testing) or __ (other)

**Notes:**
```
(Enter any issues or observations)
```

---

## Part 2: Signal File Monitoring

- [ ] signal.json created and updated
- [ ] Timestamp updates every 10 seconds
- [ ] event_ids are unique and sequential
- [ ] Confidence scores between 0.5-1.0
- [ ] Actions are valid (BUY/SELL/HOLD)
- [ ] Symbols are tradeable (EURUSD, GBPUSD, USDJPY, etc.)

**Signals Generated:** __ signals in __ minutes

**Sample Signals:**
| Timestamp | event_id | Symbol | Action | Confidence |
|-----------|----------|--------|--------|------------|
| | | | | |
| | | | | |
| | | | | |

**Notes:**
```
(Enter any unusual signal patterns or issues)
```

---

## Part 3: MT5 File Sync

**Sync Method Used:** Manual Copy / Automated Script

- [ ] signal.json successfully copied to MT5 Files folder
- [ ] File sync latency < 60 seconds
- [ ] File size matches (no corruption)
- [ ] File permissions allow EA to read

**First Sync Time:** __ seconds after Python signal write

**Sample Sync Operations:**
| Time | File Modified | Copied to MT5 | Latency |
|------|---------------|---------------|---------|
| | | | |
| | | | |
| | | | |

**Sync Script Output (if applicable):**
```
(Paste relevant log lines)
```

**Notes:**
```
(Enter any sync issues or observations)
```

---

## Part 4: EA Execution

- [ ] EA reads signal.json without errors
- [ ] Risk gate validation logs appear in MT5 Journal
- [ ] Trade execution messages logged
- [ ] Order tickets generated (numeric, > 0)
- [ ] Order entry prices reasonable
- [ ] SL/TP values correct

**Trades Executed:** __ trades from __ signals attempted

**Sample Trade Executions:**
| Time | Signal | Action | Symbol | Ticket | Entry Price | Status |
|------|--------|--------|--------|--------|-------------|--------|
| | | | | | | |
| | | | | | | |
| | | | | | | |

**Risk Gate Blocks (if applicable):**
| Time | Reason | Signal |
|------|--------|--------|
| | | |
| | | |

**MT5 Journal Excerpt:**
```
(Paste 10-15 relevant journal lines showing execution flow)
```

**Notes:**
```
(Enter any trading issues or risk gate triggers)
```

---

## Part 5: Heartbeat Monitoring

- [ ] heartbeat.json created by EA
- [ ] heartbeat.json readable by Python engine
- [ ] Heartbeat structure valid (all fields present)
- [ ] Heartbeat signal_id matches Python event_id
- [ ] executed flag is true for successful trades
- [ ] Ticket numbers in heartbeat match MT5

**Heartbeat Sample:**
```json
{
  "timestamp": "",
  "signal_id": "",
  "executed": true,
  "status": "success",
  "ticket": ,
  "order_type": "",
  "symbol": "",
  "entry_price": ,
  "position_size": ,
  "error_reason": ""
}
```

**Notes:**
```
(Enter any heartbeat-related issues)
```

---

## Part 6: Log Correlation

- [ ] logs/engine.log contains signal generation entries
- [ ] logs/signals.csv contains execution records
- [ ] event_id appears in both signal.json and signals.csv
- [ ] signal_id appears in heartbeat.json matching event_id
- [ ] Ticket numbers consistent across MT5 Journal, heartbeat, and CSV

**Sample Logs:**

**logs/engine.log:**
```
(Paste 5-10 relevant log lines)
```

**logs/signals.csv (first 5 rows):**
```
timestamp,event_id,symbol,action,confidence,ticket,status,latency_sec
(Paste sample rows)
```

**Notes:**
```
(Enter any logging inconsistencies)
```

---

## Latency Analysis

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Min Latency | __ seconds | < 5 min | ✓ / ✗ |
| Avg Latency | __ seconds | < 5 min | ✓ / ✗ |
| Max Latency | __ seconds | < 5 min | ✓ / ✗ |
| 95th Percentile | __ seconds | < 5 min | ✓ / ✗ |

**Latency Breakdown (sample signal):**
```
Signal generated:        HH:MM:SS.mmm
Signal synced to MT5:    HH:MM:SS.mmm  (+X seconds)
EA read signal:          HH:MM:SS.mmm  (+Y seconds)
Trade executed:          HH:MM:SS.mmm  (+Z seconds)
Heartbeat written:       HH:MM:SS.mmm  (+W seconds)
Total latency:           __ seconds
```

**Notes:**
```
(Enter any latency analysis or concerns)
```

---

## Success Criteria Validation

| # | Criterion | Status | Notes |
|---|-----------|--------|-------|
| 1 | Python engine initialization | ✓ / ✗ | |
| 2 | WorldMonitor event fetching | ✓ / ✗ | |
| 3 | Claude classification & signals | ✓ / ✗ | |
| 4 | signal.json file written | ✓ / ✗ | |
| 5 | signal.json updates every 10s | ✓ / ✗ | |
| 6 | signal.json copied to MT5 | ✓ / ✗ | |
| 7 | File sync latency < 60s | ✓ / ✗ | |
| 8 | EA reads signal file | ✓ / ✗ | |
| 9 | Risk gate validation | ✓ / ✗ | |
| 10 | Trade execution ≥30% | ✓ / ✗ | |
| 11 | Ticket numbers valid | ✓ / ✗ | |
| 12 | Trades in MT5 panel | ✓ / ✗ | |
| 13 | heartbeat.json created | ✓ / ✗ | |
| 14 | Heartbeat signal_id matches | ✓ / ✗ | |
| 15 | End-to-end latency < 5 min | ✓ / ✗ | |

**Total Passed:** __/15

---

## Issues Encountered

### Issue 1: [Brief Title]
**Severity:** Critical / High / Medium / Low  
**Description:** [What happened]  
**Root Cause:** [Why it happened]  
**Resolution:** [How it was fixed]  
**Time Impact:** __ minutes  

### Issue 2: [Brief Title]
...

---

## Environment Details

**Python Environment:**
- Python version: __
- anthropic version: __
- requests version: __
- OS: __
- Working directory: __

**MT5 Environment:**
- MetaTrader 5 version: __
- Account type: Demo / Real
- GeoSignal EA version: __
- Deployed symbols: EURUSD, GBPUSD, USDJPY, ...

**Network:**
- Mac ↔ Stratos latency: __ ms
- SMB mount status: Mounted / Not mounted
- File sync method: Manual / Automated

---

## Final Assessment

### Go/No-Go Decision

**Status:** GO ✓ / NO-GO ✗ / CONDITIONAL ⚠

**Reasoning:**
```
(Explain why you made this decision based on criteria above)
```

### Recommendations for Next Test

1. [Action item 1]
2. [Action item 2]
3. [Action item 3]

### Recommendations for Production

1. [Production consideration 1]
2. [Production consideration 2]
3. [Production consideration 3]

---

## Sign-Off

**Tester Signature:** ________________  
**Date:** YYYY-MM-DD  
**Approved By:** ________________  
**Approval Date:** YYYY-MM-DD  

---

## Appendix: Log Files

All logs archived in: `results/test_YYYY-MM-DD/`

- [ ] logs/engine.log
- [ ] logs/signals.csv
- [ ] logs/sync.log (if applicable)
- [ ] signals/signal.json (final state)
- [ ] signals/heartbeat.json (final state)
- [ ] EXECUTION_REPORT.txt
- [ ] SUCCESS_CRITERIA.md (completed)

Archive location: ________________
