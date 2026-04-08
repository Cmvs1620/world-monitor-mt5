# Python-EA Integration Test Suite

Comprehensive end-to-end integration testing documentation and utilities for validating the signal flow from Python Signal Engine (Phase 1) to MQL5 Expert Advisor (Phase 3).

## Overview

This test suite validates the complete signal pipeline:
1. **Python Engine** - Fetches events, classifies with Claude, generates signals
2. **Signal File Transfer** - signal.json copied from Mac to Stratos MT5 Files folder
3. **EA Execution** - EA reads signal, validates risk rules, executes trade
4. **Heartbeat Response** - EA writes heartbeat.json with execution status
5. **Python Logging** - Python reads heartbeat and logs execution results

## Quick Start

1. Start here: [QUICK_START.txt](QUICK_START.txt) - 5 commands to run E2E test
2. Understand the flow: [DATA_FLOW.md](DATA_FLOW.md) - ASCII diagram with timestamps
3. Setup environment: [INTEGRATION_SETUP.md](INTEGRATION_SETUP.md) - Prerequisites and validation
4. Run full procedure: [E2E_TEST_PROCEDURE.md](E2E_TEST_PROCEDURE.md) - Step-by-step test execution
5. Verify results: [SUCCESS_CRITERIA.md](SUCCESS_CRITERIA.md) - 15+ checkboxes for go/no-go

## File Structure

```
tests/ea_python_integration/
├── README.md (this file)
├── QUICK_START.txt           - 1-page summary, 5 commands
├── DATA_FLOW.md              - ASCII flow diagram with timestamps
├── INTEGRATION_SETUP.md       - Prerequisites, env validation, file sync setup
├── E2E_TEST_PROCEDURE.md      - 6-part step-by-step procedure
├── SUCCESS_CRITERIA.md        - 15+ checkboxes with expected behavior
├── TROUBLESHOOTING.md         - Common failures, root causes, fixes
├── SIGNAL_PIPELINE_COMPARISON.md - Risk rules, format, logging comparison
├── TEST_RESULTS_TEMPLATE.md   - Fields for recording test results
├── sync_signal_to_mt5.py      - Auto-copy signal.json to MT5 Files folder
├── verify_trade_execution.py  - Verify signal→heartbeat mapping
└── run_integration_test.py    - Main orchestrator with --duration, --mt5-path args
```

## Key Files

| File | Purpose | Usage |
|------|---------|-------|
| `QUICK_START.txt` | 5 commands to run test | Start here for fast setup |
| `INTEGRATION_SETUP.md` | Environment validation | Run before E2E test |
| `E2E_TEST_PROCEDURE.md` | 6-part test procedure | Main test execution guide |
| `sync_signal_to_mt5.py` | Auto-copy signal.json | `python sync_signal_to_mt5.py --mt5-path "C:\path"` |
| `verify_trade_execution.py` | Verify execution flow | `python verify_trade_execution.py` |
| `run_integration_test.py` | Full E2E orchestrator | `python run_integration_test.py --duration 600 --mt5-path "C:\path"` |
| `SUCCESS_CRITERIA.md` | Go/no-go checkboxes | Verify test passed |
| `TROUBLESHOOTING.md` | Common issues & fixes | Debug failures |

## Test Components

### Part 1: Python Engine Setup
- Start Python engine with 10-second poll interval for testing
- Monitor engine logs for event fetching and classification
- Verify signal.json is being updated every 10 seconds

### Part 2: Signal File Monitoring
- Watch signals/signal.json for updates
- Verify timestamps and event_ids change
- Check confidence scores, symbols, actions

### Part 3: MT5 File Sync
- Manual copy or use sync_signal_to_mt5.py script
- Verify signal.json propagates within 60 seconds

### Part 4: EA Execution
- Watch MT5 Journal for "[EA] Executing" messages
- Verify orders appear in Trades panel

### Part 5: Heartbeat Monitoring
- Check signals/heartbeat.json for EA responses
- Verify execution status and ticket numbers

### Part 6: Log Correlation
- Cross-reference Python signals with EA execution
- Calculate end-to-end latency

## Test Duration & Signals

- **Recommended test duration:** 10-15 minutes
- **Expected signals:** 1-3 per minute (every 10 seconds with polling)
- **Expected trades:** 30-50% of signals (rest filtered by risk rules)
- **Total expected heartbeats:** Match number of executed trades

## Success Criteria

A test passes when:
- ✓ 15/15 checkboxes in SUCCESS_CRITERIA.md are checked
- ✓ Python signals match heartbeat signal_ids
- ✓ Average latency < 5 minutes (from Python signal to EA execution)
- ✓ All executed trades have valid order tickets
- ✓ No errors in logs/signals.csv or EA Journal

## Troubleshooting

Common issues:

| Issue | Diagnosis | Fix |
|-------|-----------|-----|
| signal.json not updating | Check Python logs | Restart Python engine, verify API connectivity |
| EA not reading signal | Check MT5 Files path | Verify EA DEBUG_MODE, file permissions |
| Trade not executing | Check risk rules | Review risk gate logs, account balance |
| Heartbeat not written | Check EA file access | Verify MT5 Files folder permissions |
| High latency (>5min) | Check polling interval | Reduce POLL_INTERVAL_SECONDS in run.py |

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for complete diagnosis guide.

## Environment Variables

Required for sync and execution scripts:
- `SIGNAL_DIR` - Path to signals/ folder (default: ./signals)
- `MT5_FILES_PATH` - Path to MT5 Files folder on Stratos (for sync)
- `POLL_INTERVAL_SECONDS` - Python polling interval (default: 10 for testing)

## Output Files

Test execution creates:
- `EXECUTION_REPORT.txt` - Summary of executed trades
- `logs/signals.csv` - Python signal log entries
- `logs/engine.log` - Python engine execution log
- MT5 Journal - EA execution messages

## Related Documentation

- **Phase 1 (Python Engine):** See config/settings.json, run.py, logs/
- **Phase 3 (EA):** See MQL5 source, EA properties, MT5 Journal
- **Risk Rules:** See risk_rules.json (Python) and EA_RISK_RULES (MQL5)

## Next Steps

1. Read QUICK_START.txt for immediate test setup
2. Review INTEGRATION_SETUP.md for environment validation
3. Follow E2E_TEST_PROCEDURE.md for step-by-step execution
4. Use verify_trade_execution.py to generate final report
5. Check SUCCESS_CRITERIA.md to confirm go/no-go status
