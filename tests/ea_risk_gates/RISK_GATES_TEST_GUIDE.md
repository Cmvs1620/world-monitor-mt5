# Risk Gate Validation Test Guide

## Overview

This comprehensive guide validates all 5 risk validation rules in the GeoSignal Expert Advisor. Each risk gate protects the trading account from excessive losses and maintains disciplined position management.

### The 5 Risk Gates

1. **Confidence Threshold** — Rejects signals with confidence < 0.5
2. **Max Concurrent Positions** — Rejects signals if 3+ positions already open (default MAX_CONCURRENT_POSITIONS = 5)
3. **Duplicate Symbol** — Rejects if same symbol already has open position
4. **Daily Loss Limit** — Rejects if daily loss exceeds -10% (MAX_DAILY_LOSS_PERCENT = 10%)
5. **Drawdown Limit** — Rejects if equity drawdown exceeds 15% (MAX_DRAWDOWN_PERCENT = 15%)

---

## Pre-Test Checklist

Before executing any risk gate tests, ensure the following:

### System Requirements
- [ ] MetaTrader 5 is installed and running
- [ ] GeoSignalEA.mq5 is compiled and deployed to MT5
- [ ] EA is visible in MT5 "Experts" folder
- [ ] EA input parameters can be accessed and modified

### Trading Account Setup
- [ ] Test trading account is ready (demo or micro account)
- [ ] Account has sufficient balance ($10,000+ recommended for testing)
- [ ] Internet connection is stable
- [ ] No automatic backups running during tests

### File System Setup
- [ ] MT5 Files folder is accessible at: C:\Users\[username]\AppData\Roaming\MetaQuotes\Terminal\[terminal_id]\MQL5\Files\
- [ ] `signal.json` file is in the Files folder
- [ ] `ea_execution.log` is being created in Files folder
- [ ] Test signals directory is accessible

### EA Configuration
- [ ] EA_ENABLED = true (in EA input parameters)
- [ ] POLL_INTERVAL_SECONDS = 5 (or lower for faster testing)
- [ ] DEBUG_MODE = true (recommended for test execution)
- [ ] MAX_CONCURRENT_POSITIONS = 5 (or test-specific value)
- [ ] MAX_DAILY_LOSS_PERCENT = 10.0
- [ ] MAX_DRAWDOWN_PERCENT = 15.0

### Pre-Test Execution
- [ ] No open positions exist on test symbol(s)
- [ ] Account equity = account balance (no floating losses)
- [ ] Check terminal log for any compilation errors
- [ ] Verify signal.json is readable and has valid JSON format

---

## Test Scenario 1: Confidence Threshold Gate

**Risk Gate:** Confidence < 0.5 triggers rejection  
**Default Threshold:** 0.5  
**Test File:** `test_low_confidence.json`

### Objective
Validate that the EA rejects signals when confidence level is below the minimum threshold.

### Test Signals

| Signal | Symbol | Confidence | Expected Outcome | Log Message |
|--------|--------|-----------|------------------|-------------|
| 1 | EURUSD | 0.30 | REJECT | SKIP: Confidence 0.30 below threshold (0.5) |
| 2 | GBPUSD | 0.45 | REJECT | SKIP: Confidence 0.45 below threshold (0.5) |
| 3 | USDJPY | 0.50 | EXECUTE | Position opened (boundary case) |
| 4 | AUDUSD | 0.75 | EXECUTE | Position opened |

### Step-by-Step Procedure

1. **Prepare test environment**
   - Ensure no positions are open
   - Open MT5 Navigator and locate GeoSignalEA
   - Open EA Inputs dialog to verify parameters

2. **Send signal 1 (confidence 0.30)**
   ```
   Copy test_low_confidence.json signal 1 to signal.json
   Wait for EA to process (check log after 5-10 seconds)
   ```

3. **Verify rejection**
   - Check `ea_execution.log` for message: "Confidence 0.30 below threshold (0.5)"
   - Verify NO position is opened in EURUSD
   - Record: PASS/FAIL

4. **Send signal 2 (confidence 0.45)**
   ```
   Copy signal 2 to signal.json
   Wait 5 seconds
   ```

5. **Verify rejection**
   - Check log for: "Confidence 0.45 below threshold (0.5)"
   - Verify NO position in GBPUSD
   - Record: PASS/FAIL

6. **Send signal 3 (confidence 0.50 - boundary)**
   ```
   Copy signal 3 to signal.json
   Wait 5 seconds
   ```

7. **Verify execution**
   - Check log for: "Signal executed successfully" 
   - Verify USDJPY position IS opened
   - Record: PASS/FAIL

8. **Send signal 4 (confidence 0.75)**
   ```
   Copy signal 4 to signal.json
   Wait 5 seconds
   ```

9. **Verify execution**
   - Check log for: "Signal executed successfully"
   - Verify AUDUSD position IS opened
   - Record: PASS/FAIL

10. **Cleanup**
    - Close USDJPY and AUDUSD positions manually

### Success Criteria
- [ ] Signals with confidence < 0.5 are rejected
- [ ] Signal with confidence = 0.5 is accepted
- [ ] Signals with confidence > 0.5 are accepted
- [ ] Rejection messages are accurate and timestamped
- [ ] No errors in EA log

---

## Test Scenario 2: Max Positions Gate

**Risk Gate:** Rejects if concurrent positions >= MAX_CONCURRENT_POSITIONS  
**Test Limit:** Set to 3 for testing (normally 5)  
**Test File:** `test_max_positions.json`

### Objective
Validate that the EA prevents opening more positions than the maximum limit.

### Test Signals

| Seq | Symbol | Expected Positions | Expected Outcome |
|-----|--------|-------------------|------------------|
| 1 | EURUSD | 1 | EXECUTE |
| 2 | GBPUSD | 2 | EXECUTE |
| 3 | USDJPY | 3 (AT LIMIT) | EXECUTE |
| 4 | AUDUSD | Would be 4 | REJECT |

### Step-by-Step Procedure

1. **Configure EA for test**
   - Open EA Inputs dialog
   - Set MAX_CONCURRENT_POSITIONS = 3
   - Click OK to save

2. **Verify configuration**
   - Right-click EA in Navigator
   - Select Properties, check Inputs tab shows MAX_CONCURRENT_POSITIONS = 3

3. **Ensure clean start**
   - Close all positions (or verify none exist)
   - Check Account Summary shows 0 positions

4. **Send signal 1 (EURUSD)**
   ```
   Copy test_max_positions.json signal 1 to signal.json
   Wait 5 seconds
   ```

5. **Verify first execution**
   - Check log for: "Signal executed successfully" 
   - Verify EURUSD position open
   - Count in MT5 should be: 1 position
   - Record: Position 1/3

6. **Send signal 2 (GBPUSD)**
   ```
   Copy signal 2 to signal.json
   Wait 5 seconds
   ```

7. **Verify second execution**
   - Check log for: "Signal executed successfully"
   - Verify GBPUSD position open
   - Count in MT5 should be: 2 positions
   - Record: Position 2/3

8. **Send signal 3 (USDJPY)**
   ```
   Copy signal 3 to signal.json
   Wait 5 seconds
   ```

9. **Verify third execution (at limit)**
   - Check log for: "Signal executed successfully"
   - Verify USDJPY position open
   - Count in MT5 should be: 3 positions (AT MAX)
   - Record: Position 3/3 (AT LIMIT)

10. **Send signal 4 (AUDUSD) - REJECTION TEST**
    ```
    Copy signal 4 to signal.json
    Wait 5 seconds
    ```

11. **Verify rejection**
    - Check log for: "Already 3 positions open (max: 3)"
    - Verify NO AUDUSD position opened
    - Count in MT5 should still be: 3 positions
    - Record: PASS/FAIL

12. **Cleanup**
    - Close EURUSD, GBPUSD, USDJPY positions manually

### Success Criteria
- [ ] First 3 signals execute successfully
- [ ] 4th signal is rejected when at max limit
- [ ] Rejection message mentions current count and limit
- [ ] No position limit check error occurs
- [ ] Positions remain stable after rejection attempt

---

## Test Scenario 3: Duplicate Symbol Gate

**Risk Gate:** Rejects if same symbol already has open position  
**Test File:** `test_duplicate_symbol.json`

### Objective
Validate that the EA prevents opening multiple positions in the same symbol.

### Test Signals

| Seq | Action | Symbol | Expected Outcome |
|-----|--------|--------|------------------|
| 1 | BUY | EURUSD | EXECUTE |
| 2 | BUY | EURUSD | REJECT (duplicate) |

### Step-by-Step Procedure

1. **Ensure clean start**
   - No EURUSD position exists
   - No positions from previous tests

2. **Send signal 1 (EURUSD BUY)**
   ```
   Copy test_duplicate_symbol.json signal 1 to signal.json
   Wait 5 seconds
   ```

3. **Verify first execution**
   - Check log for: "Signal executed successfully"
   - Verify EURUSD position open in MT5
   - Record: Position opened

4. **Send signal 2 (EURUSD BUY again)**
   ```
   Copy signal 2 to signal.json
   Wait 5 seconds
   ```

5. **Verify rejection**
   - Check log for: "Position already open in EURUSD"
   - Verify EURUSD position count is still 1 (not 2)
   - Verify original position parameters unchanged
   - Record: PASS/FAIL

6. **Test variant: Different action**
   - Keep EURUSD BUY position open
   - Send SELL signal for EURUSD
   - Should also be rejected (position exists)
   - Record: PASS/FAIL

7. **Cleanup**
   - Close EURUSD position manually

### Success Criteria
- [ ] First signal opens EURUSD position
- [ ] Second signal for same symbol is rejected
- [ ] Rejection message is clear and accurate
- [ ] Original position remains unaffected
- [ ] Works for both BUY and SELL duplicate attempts

---

## Test Scenario 4: Daily Loss Limit Gate

**Risk Gate:** Rejects if daily loss exceeds -10%  
**Default Limit:** MAX_DAILY_LOSS_PERCENT = 10.0  
**Test File:** `test_daily_loss.json`

### Objective
Validate that the EA stops trading when daily losses exceed the configured limit.

### Test Setup

**Account Balance:** $10,000  
**Daily Loss Limit:** 10% = $1,000 maximum loss  
**Test Loss Trigger:** Close a position at -$1,050 loss (10.5%)  

### Step-by-Step Procedure

1. **Record baseline**
   - Note current Balance: ___________
   - Note current Equity: ___________
   - Verify Daily P&L = 0

2. **Send signal 1 (EURUSD BUY)**
   ```
   Copy test_daily_loss.json signal 1 to signal.json
   Wait 5 seconds
   ```

3. **Verify execution**
   - Check log for: "Signal executed successfully"
   - Note EURUSD position details (entry price, size)
   - Record: Executed

4. **Manually create loss**
   - Wait for EURUSD price to move against position OR
   - Open a losing position in another symbol to incur loss
   - Target: Daily P&L = -$1,050 (exceeds -$1,000 limit by 0.5%)

5. **Verify loss state**
   - Check Account Summary shows Equity < Balance
   - Calculate Daily Loss = Balance - Equity
   - Verify Daily Loss > $1,000 (10%)
   - Record Daily Loss Amount: ___________

6. **Send signal 2 (GBPUSD BUY) - REJECTION TEST**
   ```
   Copy signal 2 to signal.json
   Wait 5 seconds
   ```

7. **Verify rejection**
   - Check log for: "Daily loss exceeded limit"
   - Verify NO GBPUSD position opened
   - Verify EURUSD position still exists
   - Record: PASS/FAIL

8. **Cleanup**
   - Close all positions
   - Verify Daily P&L returns to 0
   - Record final balance

### Success Criteria
- [ ] Trading halts when daily loss exceeds limit
- [ ] Rejection message is clear
- [ ] Message includes loss amount and limit
- [ ] No new positions opened during loss state
- [ ] EA resumes trading after daily loss recovers

---

## Test Scenario 5: Drawdown Limit Gate

**Risk Gate:** Rejects if equity drawdown exceeds 15%  
**Default Limit:** MAX_DRAWDOWN_PERCENT = 15.0  
**Test File:** `test_drawdown_limit.json`

### Objective
Validate that the EA prevents new trades when account equity drawdown is excessive.

### Test Setup

**Account Balance:** $10,000  
**Drawdown Limit:** 15% = Equity must stay above $8,500  
**Trigger Condition:** (Balance - Equity) / Balance * 100 > 15%  

### Step-by-Step Procedure

1. **Record baseline**
   - Note Opening Balance: $__________
   - Note Opening Equity: $__________
   - Verify they are equal (no losses yet)

2. **Send signal 1 (EURUSD BUY)**
   ```
   Copy test_drawdown_limit.json signal 1 to signal.json
   Wait 5 seconds
   ```

3. **Verify execution**
   - Check log for: "Signal executed successfully"
   - Note entry price and position size
   - Record: Position opened

4. **Force price movement against position**
   - Option A: Wait for natural price movement
   - Option B: Send opposing SELL signal to force adverse move
   - Target: Equity drops to $8,400 or below
   - Current drawdown should exceed 15%

5. **Monitor equity deterioration**
   ```
   Equity needed to trigger rejection:
   Drawdown = (Balance - Equity) / Balance * 100 > 15%
   ($10,000 - X) / $10,000 * 100 > 15%
   $10,000 - X > $1,500
   X < $8,500
   
   So when Equity < $8,500, rejection should trigger
   ```

6. **Verify drawdown state**
   - Check Account Summary:
     - Balance: $__________
     - Equity: $__________ (should be < $8,500)
   - Calculate Drawdown = (Balance - Equity) / Balance * 100 = ____%
   - Verify Drawdown > 15%
   - Record: Drawdown ____%

7. **Send signal 2 (GBPUSD BUY) - REJECTION TEST**
   ```
   Copy signal 2 to signal.json
   Wait 5 seconds
   ```

8. **Verify rejection**
   - Check log for: "Drawdown exceeded limit"
   - Verify NO GBPUSD position opened
   - Verify EURUSD position still exists
   - Record: PASS/FAIL

9. **Test recovery**
   - Close EURUSD position (even at loss)
   - Wait for Equity to recover
   - Once Equity > $8,500 (drawdown < 15%), send new signal
   - Should execute successfully
   - Record: Recovery test PASS/FAIL

10. **Cleanup**
    - Close all positions
    - Return account to clean state

### Success Criteria
- [ ] Trading halts when drawdown exceeds limit
- [ ] Rejection message is clear
- [ ] Drawdown percentage in log is accurate
- [ ] Trading resumes after drawdown recovers
- [ ] Difference between daily loss and drawdown is clear

---

## Difference: Daily Loss vs Drawdown

**Daily Loss Gate:**
- Measures closed profit/loss only
- Formula: `daily_profit = equity - balance`
- Triggered by: Closed losing positions
- Resets: At end of trading day

**Drawdown Gate:**
- Measures total account deterioration
- Formula: `drawdown = (balance - equity) / balance * 100`
- Triggered by: Both closed and unrealized losses
- Does NOT reset daily

---

## Troubleshooting

### Issue: EA not responding to signals
- **Solution:** Check signal.json location in MT5 Files folder
- **Solution:** Verify JSON syntax with JSON validator
- **Solution:** Check POLL_INTERVAL_SECONDS is not too high

### Issue: Risk gate appears not triggered
- **Solution:** Verify gate parameter in EA Inputs (check current value)
- **Solution:** Check ea_execution.log for exact rejection message
- **Solution:** Verify account state matches test expectation

### Issue: Position counts don't match test expectation
- **Solution:** Close positions from previous tests first
- **Solution:** Verify MAX_CONCURRENT_POSITIONS setting
- **Solution:** Check for positions from other EAs (magic number mismatch)

### Issue: Confidence rejection not working
- **Solution:** Verify confidence value in signal.json is < 0.5 (not <= 0.5)
- **Solution:** Check signal.json decimal format (0.3 not 0,3)

### Issue: Daily loss/drawdown tests too complex
- **Solution:** Use EA's built-in simulator with pending orders
- **Solution:** Use small position sizes to trigger limits faster
- **Solution:** Create test scenarios that directly manipulate account state

### Issue: Log file not updating
- **Solution:** Verify DEBUG_MODE = true in EA parameters
- **Solution:** Check file path: Terminal\[ID]\MQL5\Files\ea_execution.log
- **Solution:** Restart EA and check log file handle error in alert

---

## Risk Gate Parameter Reference

### Confidence Threshold
- **Variable:** CONFIDENCE_THRESHOLD
- **Default:** 0.5 (50%)
- **Range:** 0.0 to 1.0
- **Location:** GeoSignalEA.mq5 line 281
- **Safe Range for Testing:** 0.4 to 0.6
- **Adjustment:** Lower = more aggressive; Higher = more selective

### Max Concurrent Positions
- **Variable:** MAX_CONCURRENT_POSITIONS
- **Default:** 5
- **Range:** 1 to 10
- **Location:** risk_config.mqh line 19
- **Safe Range for Testing:** 1 to 3
- **Adjustment:** For this test suite, use 3

### Daily Loss Limit
- **Variable:** MAX_DAILY_LOSS_PERCENT
- **Default:** 10.0 (10%)
- **Range:** 1.0 to 50.0
- **Location:** risk_config.mqh line 21
- **Safe Range for Testing:** 5% to 15%
- **Adjustment:** Lower = more conservative; Higher = more aggressive
- **Calculation:** `max_loss = balance * (max_daily_loss_percent / 100)`

### Drawdown Limit
- **Variable:** MAX_DRAWDOWN_PERCENT
- **Default:** 15.0 (15%)
- **Range:** 5.0 to 50.0
- **Location:** risk_config.mqh line 22
- **Safe Range for Testing:** 10% to 20%
- **Adjustment:** Lower = more conservative; Higher = more aggressive
- **Calculation:** `drawdown = (balance - equity) / balance * 100`

---

## Test Execution Summary

After completing all 5 test scenarios, fill out this summary:

| Risk Gate | Test Status | Notes |
|-----------|------------|-------|
| Confidence | PASS / FAIL | ________________ |
| Max Positions | PASS / FAIL | ________________ |
| Duplicate Symbol | PASS / FAIL | ________________ |
| Daily Loss Limit | PASS / FAIL | ________________ |
| Drawdown Limit | PASS / FAIL | ________________ |

**Overall Result:** ☐ ALL PASS ☐ PARTIAL PASS ☐ FAILURES

**Date Tested:** _______________  
**Tester Name:** _______________  
**EA Version:** _______________  
**Notes:** _______________________________________________

---

## Next Steps

- Review any FAIL results in detail
- Document findings in VALIDATION_CHECKLIST.md
- Cross-reference actual log output with EXPECTED_LOG_OUTPUTS.md
- Adjust parameters if needed using RISK_PARAMETERS_ADJUSTMENT.md
- Commit test results to repository

