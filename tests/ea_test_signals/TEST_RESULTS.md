# EA Signal Reading Test Results

**Test Date**: [YYYY-MM-DD]
**Tester**: [Name]
**MT5 Account**: [Account Number/Name]
**EA Version**: [Version]
**Test Environment**: Windows Stratos MT5 Terminal

---

## Test Execution Summary

| Test # | Signal File | Expected Result | Actual Result | Status | Notes |
|--------|-------------|-----------------|---------------|--------|-------|
| 1 | test_signal_buy.json | BUY order placed (XAUUSD, 0.5 lots) | | | |
| 2 | test_signal_sell.json | SELL order placed (EURUSD, 1.0 lots) | | | |
| 3 | test_signal_low_confidence.json | Signal rejected (confidence < 0.5) | | | |
| 4 | test_signal_hold.json | Signal ignored (no trade) | | | |
| 5 | test_signal_duplicate.json | Signal skipped (duplicate event_id) | | | |

### Status Legend
- **PASS**: Signal processed exactly as expected
- **FAIL**: Unexpected behavior or error occurred
- **PARTIAL**: Some aspects correct, others incorrect
- **SKIP**: Test could not be executed

---

## Detailed Test Results

### Test 1: Basic BUY Signal

**Signal File**: `test_signal_buy.json`
**Action**: BUY
**Symbol**: XAUUSD
**Volume**: 0.5 lots
**Stop Loss**: 2320.0
**Take Profit**: 2360.0
**Confidence**: 0.75

**Expected Outcome**:
- Order placed successfully on XAUUSD
- Volume: 0.5 lots
- Journal shows: "[EA] Executing: BUY XAUUSD (0.5 lots)"
- Position visible in Trades panel

**Actual Outcome**:
```
[Paste actual results here from MT5 Journal and Trades panel]
```

**Order Details** (if executed):
- Ticket Number: ___________
- Entry Price: ___________
- Entry Time: ___________
- Current P/L: ___________

**Result**: [ ] PASS  [ ] FAIL  [ ] PARTIAL  [ ] SKIP

**Notes**:
```
[Record any observations or deviations]
```

---

### Test 2: SELL Signal

**Signal File**: `test_signal_sell.json`
**Action**: SELL
**Symbol**: EURUSD
**Volume**: 1.0 lots
**Stop Loss**: 1.1050
**Take Profit**: 1.0950
**Confidence**: 0.65

**Expected Outcome**:
- Order placed successfully on EURUSD
- Volume: 1.0 lots
- Journal shows: "[EA] Executing: SELL EURUSD (1.0 lots)"
- Position visible in Trades panel

**Actual Outcome**:
```
[Paste actual results here from MT5 Journal and Trades panel]
```

**Order Details** (if executed):
- Ticket Number: ___________
- Entry Price: ___________
- Entry Time: ___________
- Current P/L: ___________

**Result**: [ ] PASS  [ ] FAIL  [ ] PARTIAL  [ ] SKIP

**Notes**:
```
[Record any observations or deviations]
```

---

### Test 3: Low Confidence Signal (Should be Rejected)

**Signal File**: `test_signal_low_confidence.json`
**Action**: BUY (but should be rejected)
**Symbol**: GBPUSD
**Confidence**: 0.35 (below 0.5 threshold)
**Threshold**: 0.5

**Expected Outcome**:
- Signal rejected
- NO order placed
- Journal shows: "[EA] Signal rejected: confidence 0.35 below threshold 0.5"
- No position appears in Trades panel

**Actual Outcome**:
```
[Paste actual results here from MT5 Journal]
```

**Result**: [ ] PASS  [ ] FAIL  [ ] PARTIAL  [ ] SKIP

**Notes**:
```
[Record any observations or deviations]
```

---

### Test 4: HOLD Signal (Should be Ignored)

**Signal File**: `test_signal_hold.json`
**Action**: HOLD (no trading action)
**Symbol**: AUDUSD
**Confidence**: 0.0

**Expected Outcome**:
- Signal processed but no action taken
- NO order placed
- Journal shows: "[EA] Signal action: HOLD - no trade executed"
- No position appears in Trades panel

**Actual Outcome**:
```
[Paste actual results here from MT5 Journal]
```

**Result**: [ ] PASS  [ ] FAIL  [ ] PARTIAL  [ ] SKIP

**Notes**:
```
[Record any observations or deviations]
```

---

### Test 5: Duplicate Signal (Should be Skipped)

**Signal File**: `test_signal_duplicate.json`
**Event ID**: test-buy-001 (same as Test 1)
**Action**: BUY (but should be skipped due to duplicate)
**Symbol**: XAUUSD

**Expected Outcome**:
- Duplicate detected and signal skipped
- NO new order placed
- Journal shows: "[EA] Signal skipped: duplicate event_id test-buy-001 already processed"
- No additional position in Trades panel

**Prerequisite**: Test 1 must be executed first to establish the initial event_id in EA's memory

**Actual Outcome**:
```
[Paste actual results here from MT5 Journal]
```

**Result**: [ ] PASS  [ ] FAIL  [ ] PARTIAL  [ ] SKIP

**Notes**:
```
[Record any observations or deviations]
```

---

## Overall Results

### Summary Statistics

| Category | Count |
|----------|-------|
| Tests Passed | |
| Tests Failed | |
| Tests Partial | |
| Tests Skipped | |
| **Total** | **5** |

### Pass Rate
```
[Passed Tests] / [Total Tests] = ____%
```

### Issues Discovered

| Issue # | Severity | Description | Impact | Status |
|---------|----------|-------------|--------|--------|
| | HIGH/MED/LOW | | | |
| | | | | |

---

## EA Functionality Assessment

### Signal Reading
- [ ] EA correctly reads signal.json file
- [ ] EA parses JSON format correctly
- [ ] EA detects all required fields
- [ ] EA handles missing fields gracefully

### Signal Validation
- [ ] Confidence threshold (0.5) properly enforced
- [ ] Low-confidence signals rejected with clear logging
- [ ] Action type validation works (BUY/SELL/HOLD)
- [ ] Symbol validation works

### Trade Execution
- [ ] BUY orders placed with correct parameters
- [ ] SELL orders placed with correct parameters
- [ ] Volume applied correctly
- [ ] Stop loss set correctly
- [ ] Take profit set correctly

### Duplicate Detection
- [ ] Event IDs tracked in EA memory
- [ ] Duplicates properly identified
- [ ] Duplicates logged and skipped
- [ ] Event ID tracking persists across polling cycles

### Logging & Monitoring
- [ ] All signals logged to Journal with timestamp
- [ ] Event IDs included in Journal messages
- [ ] Rejection reasons clearly logged
- [ ] Error messages helpful for troubleshooting

---

## Action Items

### Critical Issues (Block deployment)
```
1. [If any]
```

### High Priority Issues (Should fix before live trading)
```
1. [If any]
```

### Low Priority Issues (Can address in future versions)
```
1. [If any]
```

---

## Recommendation

Based on test results:

- [ ] **APPROVED FOR DEPLOYMENT** - All tests passed, EA ready for live trading
- [ ] **APPROVED WITH CONDITIONS** - Some tests passed, known issues documented and acceptable
- [ ] **REQUIRES INVESTIGATION** - Some failures need developer review before deployment
- [ ] **NOT APPROVED** - Critical failures discovered, do not deploy to live trading

**Rationale**:
```
[Explain reasoning for recommendation]
```

---

## Tester Sign-Off

**Tester Name**: ___________________

**Signature**: _____________________

**Date**: ___________________

---

## Developer Notes

[For EA developer to review and respond to test results]

```
[Developer response space]
```

---

**Test Suite Version**: 1.0
**Created**: 2026-04-06
**Last Updated**: [Date]
