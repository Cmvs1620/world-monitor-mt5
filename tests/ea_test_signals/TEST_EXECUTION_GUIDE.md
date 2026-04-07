# EA Signal Reading Test Execution Guide

This guide provides step-by-step instructions for testing the Expert Advisor's signal reading functionality on Windows Stratos MT5 terminal.

## Overview

The EA polls a `signal.json` file in the MT5 Files folder every 60 seconds. This test suite validates that the EA correctly:
- Reads valid signals and executes trades
- Rejects low-confidence signals
- Ignores HOLD signals
- Prevents duplicate signal execution
- Properly logs all actions

## Test Environment Setup

### Prerequisites

1. **MT5 Installation**: MetaTrader 5 installed on Windows Stratos
2. **EA Deployment**: Trading EA compiled and attached to an active chart
3. **File Access**: MT5 Files folder accessible from Windows (typically `C:\Users\[Username]\AppData\Roaming\MetaTrader 5\Files\`)
4. **Test Signals**: All test_signal_*.json files present in this directory

### Pre-Test Checklist

- [ ] MT5 is running with internet connection active
- [ ] EA is deployed and attached to a chart (check Journal for "EA Initialized" message)
- [ ] MT5 Files folder path is confirmed accessible
- [ ] Signal.json is not locked by another process
- [ ] Journal window is open and visible for monitoring
- [ ] Account has sufficient margin for test trades
- [ ] Trading is enabled (Tools > Options > Expert Advisors > "Allow automated trading" is checked)

## Step-by-Step Test Procedure

### Test 1: Basic BUY Signal

**File**: `test_signal_buy.json`
**Expected Action**: Place a BUY order on XAUUSD

1. Copy `test_signal_buy.json` to MT5 Files folder
2. Rename it to `signal.json` (replace any existing file)
3. Note the time, then wait 60 seconds for EA polling cycle
4. **Watch Journal** for log message: `[EA] Executing: BUY XAUUSD (0.5 lots)`
5. **Check Trades panel** (Ctrl+T) for new open position on XAUUSD
6. **Verify position details**:
   - Symbol: XAUUSD
   - Volume: 0.5 lots
   - Type: BUY (entry price should be market price at execution time)
   - Stop Loss: ~2320.0
   - Take Profit: ~2360.0
7. **Manually close the position** to clean up before next test
8. **Record result** in TEST_RESULTS.md as PASSED/FAILED

### Test 2: SELL Signal

**File**: `test_signal_sell.json`
**Expected Action**: Place a SELL order on EURUSD

1. Copy `test_signal_sell.json` to MT5 Files folder
2. Rename it to `signal.json`
3. Wait 60 seconds for polling cycle
4. **Watch Journal** for log message: `[EA] Executing: SELL EURUSD (1.0 lots)`
5. **Check Trades panel** for new SELL position on EURUSD
6. **Verify position details**:
   - Symbol: EURUSD
   - Volume: 1.0 lots
   - Type: SELL
   - Stop Loss: ~1.1050
   - Take Profit: ~1.0950
7. **Manually close the position**
8. **Record result** in TEST_RESULTS.md

### Test 3: Low Confidence Signal (Should be REJECTED)

**File**: `test_signal_low_confidence.json`
**Expected Action**: Signal REJECTED - no trade placed (confidence 0.35 < 0.5 threshold)

1. Copy `test_signal_low_confidence.json` to MT5 Files folder
2. Rename it to `signal.json`
3. Wait 60 seconds
4. **Watch Journal** for rejection message similar to: `[EA] Signal rejected: confidence 0.35 below threshold 0.5`
5. **Check Trades panel** - there should be NO new position
6. **Verify Journal** shows the rejection reason clearly
7. **Record result** in TEST_RESULTS.md as SKIPPED (expected behavior)

### Test 4: HOLD Signal (Should be IGNORED)

**File**: `test_signal_hold.json`
**Expected Action**: No action taken - signal ignored

1. Copy `test_signal_hold.json` to MT5 Files folder
2. Rename it to `signal.json`
3. Wait 60 seconds
4. **Watch Journal** for informational message: `[EA] Signal action: HOLD - no trade executed`
5. **Check Trades panel** - no new positions should appear
6. **Verify no errors** in Journal related to this signal
7. **Record result** in TEST_RESULTS.md as IGNORED (expected behavior)

### Test 5: Duplicate Signal (Should be SKIPPED)

**File**: `test_signal_duplicate.json`
**Expected Action**: Duplicate detected and skipped (event_id already processed)

1. **First execute Test 1** to process the initial signal with event_id "test-buy-001"
2. After Test 1 position is closed, copy `test_signal_duplicate.json` to MT5 Files folder
3. Rename it to `signal.json`
4. Wait 60 seconds
5. **Watch Journal** for duplicate detection: `[EA] Signal skipped: duplicate event_id test-buy-001 already processed`
6. **Check Trades panel** - no new position should appear
7. **Verify Journal** confirms duplicate detection
8. **Record result** in TEST_RESULTS.md as SKIPPED (expected behavior)

## Expected Outcomes Summary

| Test | Signal File | Expected Result | Trades Created | Journal Message |
|------|-------------|-----------------|-----------------|-----------------|
| 1 | test_signal_buy.json | SUCCESS | 1 BUY order | "Executing: BUY XAUUSD" |
| 2 | test_signal_sell.json | SUCCESS | 1 SELL order | "Executing: SELL EURUSD" |
| 3 | test_signal_low_confidence.json | SKIPPED | None | "rejected: confidence...below threshold" |
| 4 | test_signal_hold.json | IGNORED | None | "action: HOLD - no trade" |
| 5 | test_signal_duplicate.json | SKIPPED | None | "duplicate event_id already processed" |

## Troubleshooting

### "EA didn't execute after 60 seconds"
- **Check**: Is EA still running? Look for "EA Running" in title bar
- **Check**: Is trading enabled in Tools > Options?
- **Check**: Is signal.json in the correct MT5 Files folder path?
- **Action**: Restart EA by detaching and re-attaching to chart
- **Action**: Check Journal for EA initialization errors

### "Position appeared but with wrong volume"
- **Cause**: Account lot size validation or insufficient margin
- **Action**: Adjust test signal volume to match account specifications
- **Action**: Verify account has sufficient free margin before test

### "Journal shows no messages from EA"
- **Check**: Is EA attached? Title bar should show "EA Running"
- **Check**: Journal filter - ensure you're not filtering out EA messages
- **Action**: Click on Journal tab and scroll to see latest messages
- **Action**: Check Tools > Options > Events tab for log settings

### "signal.json access denied error"
- **Cause**: File is locked by another process (MT5 still reading)
- **Solution**: Wait 60+ seconds after previous signal.json write
- **Solution**: Close any other file explorers accessing the folder
- **Action**: Manually delete signal.json from Files folder and retry

### "Multiple positions appeared from one signal"
- **Cause**: EA executed twice (polling cycle triggered multiple times)
- **Check**: Verify unique event_id is in signal.json
- **Action**: Check if this is the duplicate detection test
- **Action**: Close extra positions and review signal.json format

### "Position opened with different volume than requested"
- **Cause**: Account's max lot size is smaller than requested volume
- **Check**: Account specifications in Account info window
- **Action**: Adjust volume in test signals to match account limits
- **Action**: Check EA logs for volume adjustment warnings

## Additional Testing Notes

### Monitoring Best Practices

1. **Keep Journal visible**: Resize window to show both chart and Journal
2. **Monitor Account equity**: Watch free margin during test trades
3. **Use timestamps**: Note exact time you copy signal.json for correlation with Journal timestamps
4. **Screenshot results**: Take screenshots of successful trades and Journal entries for documentation
5. **Test one at a time**: Don't run multiple tests simultaneously

### Between Each Test

1. Manually close any open positions from the previous test
2. Wait at least 60 seconds before starting the next test
3. Delete or rename the signal.json file to prevent re-execution
4. Verify Journal shows no pending actions

### Test Environment Variables

- **Signal polling interval**: 60 seconds (EA scans for signal.json every 60 seconds)
- **Confidence threshold**: 0.5 (signals below this are rejected)
- **Duplicate detection**: Based on event_id field matching
- **File location**: `[MT5 Files folder]/signal.json`

## Success Criteria Checklist

All tests pass when:

- [ ] **Test 1 (BUY)**: Trade executed with correct symbol, volume, and stop/limit levels
- [ ] **Test 2 (SELL)**: Trade executed with correct symbol, volume, and stop/limit levels
- [ ] **Test 3 (Low Conf)**: Signal correctly rejected with appropriate Journal message
- [ ] **Test 4 (HOLD)**: No trade executed, clear Journal message confirming HOLD action
- [ ] **Test 5 (Duplicate)**: Duplicate correctly detected and skipped, event_id logged
- [ ] **All Journal entries**: Timestamped and include event_id and action details
- [ ] **No errors**: No exceptions or errors in Journal during any test
- [ ] **Reproducible**: All tests pass consistently when repeated

## Completion

Once all 5 tests pass:

1. Complete the TEST_RESULTS.md file with actual results
2. Screenshot the Journal entries for documentation
3. Note any deviations from expected behavior
4. If any test fails, use the Troubleshooting section to investigate
5. Document any issues discovered for EA developer review
6. Report ready for deployment to live trading (if all criteria met)

---

**Test Suite Version**: 1.0
**Created**: 2026-04-06
**For**: Windows Stratos MT5 Terminal
