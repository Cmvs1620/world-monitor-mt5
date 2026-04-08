# Risk Gate Validation Checklist

Use this checklist to document manual testing and verification of all 5 risk gates. Fill out one section per test scenario.

---

## Test Session Information

**Test Date:** ________________  
**Tester Name:** ________________  
**EA Version:** ________________  
**Platform:** MetaTrader 5  
**Account Type:** ☐ Demo ☐ Micro ☐ Live (NOT RECOMMENDED)  
**Account Balance:** $________________  

---

## Test 1: Confidence Threshold Gate

**Risk Gate Tested:** Confidence < 0.5 → Rejection  
**Test File:** `test_low_confidence.json`  
**Start Time:** ________________  

### Signal 1: Confidence 0.30

- [ ] Signal copied to MT5 Files folder
- [ ] EA acknowledged signal in log
- [ ] **Expected Outcome:** REJECTED
- [ ] **Expected Log Message:** "SKIP: Confidence 0.30 below threshold (0.5)"

| Field | Value |
|-------|-------|
| Signal Event ID | test-conf-001 |
| Symbol | EURUSD |
| Confidence | 0.30 |
| Signal Sent At | ________________ |
| EA Processed At | ________________ |
| Expected Outcome | REJECT |
| Actual Outcome | ☐ REJECT ☐ EXECUTE ☐ ERROR |
| Log Message Found | ☐ YES ☐ NO ☐ PARTIAL |
| Notes | ________________ |

**Result:** ☐ PASS ☐ FAIL ☐ INCONCLUSIVE

### Signal 2: Confidence 0.45

- [ ] Signal copied to MT5 Files folder
- [ ] EA acknowledged signal in log
- [ ] **Expected Outcome:** REJECTED
- [ ] **Expected Log Message:** "SKIP: Confidence 0.45 below threshold (0.5)"

| Field | Value |
|-------|-------|
| Signal Event ID | test-conf-002 |
| Symbol | GBPUSD |
| Confidence | 0.45 |
| Signal Sent At | ________________ |
| EA Processed At | ________________ |
| Expected Outcome | REJECT |
| Actual Outcome | ☐ REJECT ☐ EXECUTE ☐ ERROR |
| Log Message Found | ☐ YES ☐ NO ☐ PARTIAL |
| Notes | ________________ |

**Result:** ☐ PASS ☐ FAIL ☐ INCONCLUSIVE

### Signal 3: Confidence 0.50 (Edge Case)

- [ ] Signal copied to MT5 Files folder
- [ ] EA acknowledged signal in log
- [ ] **Expected Outcome:** EXECUTED (boundary case, >= 0.5 should pass)
- [ ] **Expected Log Message:** "Signal executed successfully"

| Field | Value |
|-------|-------|
| Signal Event ID | test-conf-003 |
| Symbol | USDJPY |
| Confidence | 0.50 |
| Signal Sent At | ________________ |
| EA Processed At | ________________ |
| Expected Outcome | EXECUTE |
| Actual Outcome | ☐ REJECT ☐ EXECUTE ☐ ERROR |
| Position Opened | ☐ YES ☐ NO |
| Log Message Found | ☐ YES ☐ NO ☐ PARTIAL |
| Notes | ________________ |

**Result:** ☐ PASS ☐ FAIL ☐ INCONCLUSIVE

### Signal 4: Confidence 0.75

- [ ] Signal copied to MT5 Files folder
- [ ] EA acknowledged signal in log
- [ ] **Expected Outcome:** EXECUTED
- [ ] **Expected Log Message:** "Signal executed successfully"

| Field | Value |
|-------|-------|
| Signal Event ID | test-conf-004 |
| Symbol | AUDUSD |
| Confidence | 0.75 |
| Signal Sent At | ________________ |
| EA Processed At | ________________ |
| Expected Outcome | EXECUTE |
| Actual Outcome | ☐ REJECT ☐ EXECUTE ☐ ERROR |
| Position Opened | ☐ YES ☐ NO |
| Log Message Found | ☐ YES ☐ NO ☐ PARTIAL |
| Notes | ________________ |

**Result:** ☐ PASS ☐ FAIL ☐ INCONCLUSIVE

### Test 1 Summary

- [ ] Signals 1-2 correctly rejected (confidence < 0.5)
- [ ] Signal 3 correctly accepted (confidence = 0.5, edge case)
- [ ] Signal 4 correctly accepted (confidence > 0.5)
- [ ] All log messages match expected output
- [ ] No unexpected errors or rejections

**Overall Test 1 Result:** ☐ PASS ☐ FAIL ☐ REVIEW NEEDED

**Failure Analysis (if any):** ___________________________________

---

## Test 2: Max Concurrent Positions Gate

**Risk Gate Tested:** Concurrent Positions >= 3 → Rejection  
**Test File:** `test_max_positions.json`  
**EA Setting:** MAX_CONCURRENT_POSITIONS = 3 (for this test)  
**Start Time:** ________________  

### Signal 1: EURUSD (Position 1/3)

| Field | Value |
|-------|-------|
| Event ID | test-max-pos-001 |
| Symbol | EURUSD |
| Action | BUY |
| Confidence | 0.80 |
| Signal Sent At | ________________ |
| Expected Outcome | EXECUTE |
| Actual Outcome | ☐ EXECUTE ☐ REJECT ☐ ERROR |
| Position Opened | ☐ YES ☐ NO |
| Current Position Count | ____ / 3 |
| Notes | ________________ |

**Result:** ☐ PASS ☐ FAIL

### Signal 2: GBPUSD (Position 2/3)

| Field | Value |
|-------|-------|
| Event ID | test-max-pos-002 |
| Symbol | GBPUSD |
| Action | BUY |
| Confidence | 0.80 |
| Signal Sent At | ________________ |
| Expected Outcome | EXECUTE |
| Actual Outcome | ☐ EXECUTE ☐ REJECT ☐ ERROR |
| Position Opened | ☐ YES ☐ NO |
| Current Position Count | ____ / 3 |
| Notes | ________________ |

**Result:** ☐ PASS ☐ FAIL

### Signal 3: USDJPY (Position 3/3 - AT LIMIT)

| Field | Value |
|-------|-------|
| Event ID | test-max-pos-003 |
| Symbol | USDJPY |
| Action | BUY |
| Confidence | 0.80 |
| Signal Sent At | ________________ |
| Expected Outcome | EXECUTE (at max) |
| Actual Outcome | ☐ EXECUTE ☐ REJECT ☐ ERROR |
| Position Opened | ☐ YES ☐ NO |
| Current Position Count | ____ / 3 |
| Notes | ________________ |

**Result:** ☐ PASS ☐ FAIL

### Signal 4: AUDUSD (Would be 4/3 - REJECTION TEST)

- [ ] Signal copied to MT5 Files folder
- [ ] EA acknowledged signal in log
- [ ] **Expected Outcome:** REJECTED
- [ ] **Expected Log Message:** "SKIP: Already 3 positions open (max: 3)"

| Field | Value |
|-------|-------|
| Event ID | test-max-pos-004 |
| Symbol | AUDUSD |
| Action | BUY |
| Confidence | 0.80 |
| Signal Sent At | ________________ |
| Expected Outcome | REJECT |
| Actual Outcome | ☐ REJECT ☐ EXECUTE ☐ ERROR |
| Position Opened | ☐ YES ☐ NO |
| Final Position Count | ____ (should be 3) |
| Log Message Found | ☐ YES ☐ NO ☐ PARTIAL |
| Notes | ________________ |

**Result:** ☐ PASS ☐ FAIL ☐ INCONCLUSIVE

### Test 2 Summary

- [ ] First 3 signals executed successfully
- [ ] Exactly 3 positions open after 3rd signal
- [ ] 4th signal rejected with position limit message
- [ ] Log message mentions both current count and limit
- [ ] Position count never exceeded max

**Overall Test 2 Result:** ☐ PASS ☐ FAIL ☐ REVIEW NEEDED

**Failure Analysis (if any):** ___________________________________

---

## Test 3: Duplicate Symbol Gate

**Risk Gate Tested:** Duplicate Symbol → Rejection  
**Test File:** `test_duplicate_symbol.json`  
**Start Time:** ________________  

### Signal 1: EURUSD BUY (First Position)

| Field | Value |
|-------|-------|
| Event ID | test-dup-001 |
| Symbol | EURUSD |
| Action | BUY |
| Confidence | 0.75 |
| Signal Sent At | ________________ |
| Expected Outcome | EXECUTE |
| Actual Outcome | ☐ EXECUTE ☐ REJECT ☐ ERROR |
| Position Opened | ☐ YES ☐ NO |
| Notes | ________________ |

**Result:** ☐ PASS ☐ FAIL

### Signal 2: EURUSD BUY Again (REJECTION TEST)

- [ ] Signal copied to MT5 Files folder
- [ ] EA acknowledged signal in log
- [ ] **Expected Outcome:** REJECTED
- [ ] **Expected Log Message:** "SKIP: Position already open in EURUSD"

| Field | Value |
|-------|-------|
| Event ID | test-dup-002 |
| Symbol | EURUSD |
| Action | BUY |
| Confidence | 0.70 |
| Volume | 0.5 (different from first signal) |
| Signal Sent At | ________________ |
| Expected Outcome | REJECT |
| Actual Outcome | ☐ REJECT ☐ EXECUTE ☐ ERROR |
| New Position Opened | ☐ YES ☐ NO (should be NO) |
| Total EURUSD Positions | ____ (should be 1) |
| Log Message Found | ☐ YES ☐ NO ☐ PARTIAL |
| Notes | ________________ |

**Result:** ☐ PASS ☐ FAIL ☐ INCONCLUSIVE

### Additional Verification

- [ ] Original EURUSD position remains unchanged
- [ ] Original position parameters unchanged
- [ ] No execution errors recorded
- [ ] Verify with opposite action (try SELL EURUSD) - should also reject

**Opposite Action Test:** ☐ NOT TESTED ☐ TESTED - PASSED ☐ TESTED - FAILED

### Test 3 Summary

- [ ] First signal opens EURUSD position
- [ ] Second signal for same symbol rejected
- [ ] Duplicate rejection message is clear and accurate
- [ ] Original position unaffected by rejection attempt
- [ ] Works for multiple duplicate attempts

**Overall Test 3 Result:** ☐ PASS ☐ FAIL ☐ REVIEW NEEDED

**Failure Analysis (if any):** ___________________________________

---

## Test 4: Daily Loss Limit Gate

**Risk Gate Tested:** Daily Loss > -10% → Rejection  
**Test File:** `test_daily_loss.json`  
**Account Balance:** $________________  
**Max Daily Loss (10%):** $________________  
**Start Time:** ________________  

### Initial State

| Field | Value |
|-------|-------|
| Opening Balance | $________________ |
| Opening Equity | $________________ |
| Daily P&L | $0 (should be) |
| Drawdown | 0% (should be) |

### Signal 1: EURUSD BUY (Setup Position)

| Field | Value |
|-------|-------|
| Event ID | test-loss-001 |
| Symbol | EURUSD |
| Confidence | 0.80 |
| Signal Sent At | ________________ |
| Expected Outcome | EXECUTE |
| Actual Outcome | ☐ EXECUTE ☐ REJECT ☐ ERROR |
| Position Opened | ☐ YES ☐ NO |
| Notes | ________________ |

**Result:** ☐ PASS ☐ FAIL

### Manual Loss Creation

- [ ] Manually open/close position(s) to incur loss
- [ ] Target loss: > 10% of account ($__________)
- [ ] **Loss Incurred:** $__________
- [ ] **Loss Percent:** __________% (should be > 10%)

**Loss State:**
| Field | Value |
|-------|-------|
| Current Balance | $________________ |
| Current Equity | $________________ |
| Daily P&L | $________________ |
| Daily Loss % | __________% |
| Exceeds Limit (-10%)? | ☐ YES ☐ NO |

### Signal 2: GBPUSD BUY (REJECTION TEST)

- [ ] Signal copied to MT5 Files folder after loss state confirmed
- [ ] EA acknowledged signal in log
- [ ] **Expected Outcome:** REJECTED
- [ ] **Expected Log Message:** "SKIP: Daily loss exceeded limit"

| Field | Value |
|-------|-------|
| Event ID | test-loss-002 |
| Symbol | GBPUSD |
| Confidence | 0.80 |
| Signal Sent At | ________________ |
| Expected Outcome | REJECT |
| Actual Outcome | ☐ REJECT ☐ EXECUTE ☐ ERROR |
| Position Opened | ☐ YES ☐ NO |
| Log Message Found | ☐ YES ☐ NO ☐ PARTIAL |
| Notes | ________________ |

**Result:** ☐ PASS ☐ FAIL ☐ INCONCLUSIVE

### Recovery Test (Optional)

- [ ] Close losing positions to recover losses
- [ ] Verify Daily P&L returns to positive/zero
- [ ] Send another signal - should execute if loss recovered
- [ ] Recovery successful: ☐ YES ☐ NO

### Test 4 Summary

- [ ] Signal 1 executed successfully
- [ ] Loss state created (daily loss > 10%)
- [ ] Signal 2 rejected with daily loss message
- [ ] Message includes loss amount and limit
- [ ] Trading halted during loss state
- [ ] (Optional) Trading resumed after loss recovery

**Overall Test 4 Result:** ☐ PASS ☐ FAIL ☐ REVIEW NEEDED

**Failure Analysis (if any):** ___________________________________

---

## Test 5: Drawdown Limit Gate

**Risk Gate Tested:** Equity Drawdown > 15% → Rejection  
**Test File:** `test_drawdown_limit.json`  
**Account Balance:** $________________  
**Max Drawdown (15%):** $________________ (15% of balance)  
**Trigger Equity:** < $________________ (85% of balance)  
**Start Time:** ________________  

### Initial State

| Field | Value |
|-------|-------|
| Opening Balance | $________________ |
| Opening Equity | $________________ |
| Current Drawdown | 0% (should be) |

### Signal 1: EURUSD BUY (Setup Position)

| Field | Value |
|-------|-------|
| Event ID | test-dd-001 |
| Symbol | EURUSD |
| Confidence | 0.80 |
| Signal Sent At | ________________ |
| Expected Outcome | EXECUTE |
| Actual Outcome | ☐ EXECUTE ☐ REJECT ☐ ERROR |
| Position Opened | ☐ YES ☐ NO |
| Entry Price | ________________ |
| Position Size | ________________ |
| Notes | ________________ |

**Result:** ☐ PASS ☐ FAIL

### Induce Drawdown

**Method Used:** ☐ Adverse Price Movement ☐ Opposing Order ☐ Manual Drawdown

- [ ] Waited for or created price movement against position
- [ ] Equity decreased due to unrealized losses

**Drawdown State:**
| Field | Value |
|-------|-------|
| Current Balance | $________________ |
| Current Equity | $________________ |
| Drawdown Amount | $________________ |
| Drawdown % | __________% |
| Exceeds Limit (>15%)? | ☐ YES ☐ NO |
| Time of Max Drawdown | ________________ |

**Calculation Check:**
```
Drawdown = (Balance - Equity) / Balance * 100
         = ($__________ - $__________) / $__________ * 100
         = __________% 

Should be > 15% to trigger rejection
```

### Signal 2: GBPUSD BUY (REJECTION TEST)

- [ ] Signal copied to MT5 Files folder after drawdown confirmed
- [ ] Drawdown verified to exceed 15%
- [ ] EA acknowledged signal in log
- [ ] **Expected Outcome:** REJECTED
- [ ] **Expected Log Message:** "SKIP: Drawdown exceeded limit"

| Field | Value |
|-------|-------|
| Event ID | test-dd-002 |
| Symbol | GBPUSD |
| Confidence | 0.80 |
| Signal Sent At | ________________ |
| Expected Outcome | REJECT |
| Actual Outcome | ☐ REJECT ☐ EXECUTE ☐ ERROR |
| Position Opened | ☐ YES ☐ NO |
| Log Message Found | ☐ YES ☐ NO ☐ PARTIAL |
| Notes | ________________ |

**Result:** ☐ PASS ☐ FAIL ☐ INCONCLUSIVE

### Recovery Test

- [ ] Close EURUSD position (even at loss to speed recovery)
- [ ] Monitor equity recovery
- [ ] Once Equity > 85% of Balance (drawdown < 15%), send test signal
- [ ] Recovery signal outcome: ☐ EXECUTED ☐ REJECTED
- [ ] Recovery successful: ☐ YES ☐ NO

| Field | Value |
|-------|-------|
| Time to Recovery | ________________ |
| Equity at Recovery | $________________ |
| Recovery Drawdown % | __________% |
| Recovery Signal Result | ☐ EXECUTE ☐ REJECT |

### Test 5 Summary

- [ ] Signal 1 executed successfully
- [ ] Drawdown state created (> 15%)
- [ ] Signal 2 rejected with drawdown message
- [ ] Message includes actual drawdown percentage and limit
- [ ] Trading halted during excessive drawdown
- [ ] (Optional) Trading resumed after drawdown recovery
- [ ] Difference between daily loss and drawdown understood

**Overall Test 5 Result:** ☐ PASS ☐ FAIL ☐ REVIEW NEEDED

**Failure Analysis (if any):** ___________________________________

---

## Summary Results

### Risk Gate Summary Table

| Risk Gate | Test Result | Notes |
|-----------|------------|-------|
| 1. Confidence Threshold | ☐ PASS ☐ FAIL ☐ REVIEW | ________________ |
| 2. Max Positions | ☐ PASS ☐ FAIL ☐ REVIEW | ________________ |
| 3. Duplicate Symbol | ☐ PASS ☐ FAIL ☐ REVIEW | ________________ |
| 4. Daily Loss Limit | ☐ PASS ☐ FAIL ☐ REVIEW | ________________ |
| 5. Drawdown Limit | ☐ PASS ☐ FAIL ☐ REVIEW | ________________ |

### Overall Validation

**Total Tests:** 5  
**Passed:** ______ / 5  
**Failed:** ______ / 5  
**Requiring Review:** ______ / 5  

**Overall Result:** ☐ ALL PASS ☐ PARTIAL PASS ☐ NEEDS REVIEW ☐ FAILURES

### Key Findings

**What Worked Well:**
- ________________________________________________________________________
- ________________________________________________________________________

**Issues Encountered:**
- ________________________________________________________________________
- ________________________________________________________________________

**Recommendations:**
- ________________________________________________________________________
- ________________________________________________________________________

### Sign-Off

**Tester Name:** ________________  
**Date:** ________________  
**Time Completed:** ________________  
**EA Version Tested:** ________________  
**Next Steps:** ☐ Deploy to Live ☐ Fix Issues ☐ Further Testing

**Signature/Approval:** ________________

---

## Appendix: Detailed Log Excerpts

Paste relevant log excerpts from ea_execution.log below for documentation:

```
[From Test 1 - Confidence Gate]
[Timestamp] ___________________________________________________________________________
[Timestamp] ___________________________________________________________________________

[From Test 2 - Max Positions]
[Timestamp] ___________________________________________________________________________
[Timestamp] ___________________________________________________________________________

[From Test 3 - Duplicate Symbol]
[Timestamp] ___________________________________________________________________________
[Timestamp] ___________________________________________________________________________

[From Test 4 - Daily Loss]
[Timestamp] ___________________________________________________________________________
[Timestamp] ___________________________________________________________________________

[From Test 5 - Drawdown]
[Timestamp] ___________________________________________________________________________
[Timestamp] ___________________________________________________________________________
```

---

