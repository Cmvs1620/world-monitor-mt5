# Risk Parameters Adjustment Guide

## Overview

This guide explains how to adjust the risk parameters in the GeoSignal EA for testing different risk scenarios. All risk parameters are defined in `GeoSignalEA.mq5` input parameters and can be modified in MetaTrader 5.

## Risk Parameters Reference

### 1. **EA_ENABLED** (Boolean, Default: true)
- **Purpose:** Master on/off switch for the entire EA
- **Safe Values:** true = EA active, false = EA disabled
- **Testing Use:** Disable to pause EA during test setup

### 2. **EA_TRADING_ENABLED** (Boolean, Default: false)
- **Purpose:** Separate control for actual trade execution
- **Safe Values:** false = signals validated but not executed, true = signals executed
- **Testing Use:** Keep false to test validation without live trades

### 3. **MAX_CONCURRENT_POSITIONS** (Integer, Default: 5)
- **Purpose:** Maximum number of open positions allowed simultaneously
- **Current Value in risk_config.mqh:** 5
- **Safe Testing Ranges:**
  - Conservative: 1
  - Moderate: 3
  - Balanced: 5 (default)
  - Aggressive: 10
- **Test Scenarios:**
  - Set to 3 for max_positions gate test
  - Set to 1 for extreme position limit test
  - Set to 10 for high-volume testing

### 4. **RISK_PER_TRADE_PERCENT** (Double, Default: 2.0)
- **Purpose:** Maximum risk per trade as percentage of account balance
- **Current Value in risk_config.mqh:** 2.0%
- **Safe Testing Ranges:**
  - Conservative: 0.5%
  - Moderate: 1.0%
  - Balanced: 2.0% (default)
  - Aggressive: 5.0%
  - Extreme: 10.0%
- **Test Scenarios:**
  - Set to 0.5 for conservative risk testing
  - Set to 5.0 for aggressive position sizing

### 5. **MAX_DAILY_LOSS_PERCENT** (Double, Default: 10.0)
- **Purpose:** Maximum allowed daily loss as percentage of account balance
- **Current Value in risk_config.mqh:** 10.0%
- **Safe Testing Ranges:**
  - Conservative: 2.0%
  - Moderate: 5.0%
  - Balanced: 10.0% (default)
  - Aggressive: 15.0%
- **Test Scenarios:**
  - Set to 5.0 to trigger daily loss gate with fewer losing trades
  - Set to 1.0 for extreme sensitivity testing
  - Leave at 10.0 for standard testing

### 6. **MAX_DRAWDOWN_PERCENT** (Double, Default: 15.0)
- **Purpose:** Maximum allowed equity drawdown from opening balance
- **Current Value in risk_config.mqh:** 15.0%
- **Safe Testing Ranges:**
  - Conservative: 5.0%
  - Moderate: 10.0%
  - Balanced: 15.0% (default)
  - Aggressive: 20.0%
- **Test Scenarios:**
  - Set to 10.0 for standard drawdown testing
  - Set to 3.0 to trigger drawdown gate more easily
  - Leave at 15.0 for baseline testing

### 7. **POLL_INTERVAL_SECONDS** (Integer, Default: 5)
- **Purpose:** How frequently EA checks for new signals
- **Safe Values:** 1-30 seconds
- **Testing Use:** Set to 1 for rapid testing, 5+ for production

### 8. **BRIDGE_TIMEOUT_SECONDS** (Integer, Default: 30)
- **Purpose:** Maximum wait time for signal response from bridge
- **Safe Values:** 10-60 seconds
- **Testing Use:** Increase to 60 for testing over slow connections

### 9. **DEBUG_MODE** (Boolean, Default: false)
- **Purpose:** Enable verbose logging for troubleshooting
- **Safe Values:** true = verbose logs, false = minimal logs
- **Testing Use:** Set to true during test execution

## Test Configuration Presets

### Conservative Configuration
```
MAX_CONCURRENT_POSITIONS = 1
RISK_PER_TRADE_PERCENT = 0.5
MAX_DAILY_LOSS_PERCENT = 2.0
MAX_DRAWDOWN_PERCENT = 5.0
```
Use this for: Testing with minimal risk exposure, validating risk gates trigger correctly

### Balanced Configuration (DEFAULT)
```
MAX_CONCURRENT_POSITIONS = 5
RISK_PER_TRADE_PERCENT = 2.0
MAX_DAILY_LOSS_PERCENT = 10.0
MAX_DRAWDOWN_PERCENT = 15.0
```
Use this for: Standard testing, baseline validation

### Aggressive Configuration
```
MAX_CONCURRENT_POSITIONS = 10
RISK_PER_TRADE_PERCENT = 5.0
MAX_DAILY_LOSS_PERCENT = 15.0
MAX_DRAWDOWN_PERCENT = 20.0
```
Use this for: High-volume trading scenarios, stress testing

## How to Modify Parameters in MetaTrader 5

### Step 1: Open EA Properties
1. Open MetaTrader 5
2. Navigate to: View → Toolbox (if not visible)
3. Right-click on chart → Expert Advisors → GeoSignalEA
4. Select "GeoSignalEA" from Navigator (usually on left panel)
5. Right-click → Modify (or double-click)

### Step 2: Find Inputs Tab
1. In Expert Advisor dialog, click "Inputs" tab
2. Locate parameter you want to modify

### Step 3: Edit Parameter
1. Click on the Value column for target parameter
2. Enter new value
3. Press Enter to confirm
4. Click OK to apply

### Step 4: Recompile and Redeploy
1. Close EA dialog
2. Right-click on EA → Attach to Chart
3. EA will restart with new parameters

## Risk Gate Testing Parameters

### Test: Max Positions Limit
```
MAX_CONCURRENT_POSITIONS = 3
(Other parameters at default)
```
Expected: 4th signal rejected when 3 positions open

### Test: Daily Loss Limit
```
MAX_DAILY_LOSS_PERCENT = 5.0
(Other parameters at default)
```
Expected: New signals rejected when account loses 5%+

### Test: Drawdown Limit
```
MAX_DRAWDOWN_PERCENT = 10.0
(Other parameters at default)
```
Expected: New signals rejected when equity drawdown exceeds 10%

### Test: Low Confidence Rejection
```
(Use default parameters)
```
Expected: Signal with confidence < 0.5 automatically rejected
*Note: Confidence threshold is hardcoded in code (MIN_CONFIDENCE = 0.5), cannot be modified via UI*

### Test: Duplicate Symbol Blocking
```
(Use default parameters)
```
Expected: Second BUY signal for same symbol rejected
*Note: This check is in code logic, not a configurable parameter*

## Parameter Modification Checklist

When testing risk gates:

- [ ] Backup current EA configuration
- [ ] Note original parameter values before modification
- [ ] Modify ONE parameter at a time
- [ ] Test after each modification
- [ ] Verify EA recompiles successfully
- [ ] Check EA log for correct parameter values
- [ ] Document test results
- [ ] Restore original parameters after testing

## Verification Steps After Parameter Change

1. **Check EA Logs:**
   ```
   EA starts with new parameter value logged
   ```

2. **Check Journal Tab:**
   - Open MT5 Toolbox → Journal tab
   - Look for: "Risk threshold: MAX_CONCURRENT_POSITIONS = 3"

3. **Monitor Live Parameters:**
   - Right-click chart → Expert Advisors → GeoSignalEA
   - Select (do not modify)
   - Verify current values shown

## Common Issues and Fixes

### Parameter Won't Change
- **Issue:** Change doesn't take effect after editing
- **Solution:** 
  1. Remove EA from chart
  2. Close all MT5 windows
  3. Restart MetaTrader 5
  4. Reattach EA with new parameters

### EA Fails to Compile
- **Issue:** "Error compiling" after changing parameter
- **Solution:**
  1. Check parameter type matches definition
  2. Verify no invalid characters in value
  3. Check that numeric values are valid (no negative where invalid)
  4. Restart MT5

### Parameter Shows Old Value After Restart
- **Issue:** Parameter reverted to default
- **Solution:**
  1. Edit again in EA properties
  2. Remove EA from chart before closing MT5
  3. Save workspace (File → Save)
  4. Reattach EA after restarting

## Code References

### Risk Configuration Header
Location: `/ea/includes/risk_config.mqh`

All extern parameters are defined here:
```mql5
extern int MAX_CONCURRENT_POSITIONS = 5;
extern double RISK_PER_TRADE_PERCENT = 2.0;
extern double MAX_DAILY_LOSS_PERCENT = 10.0;
extern double MAX_DRAWDOWN_PERCENT = 15.0;
```

### Risk Validation Function
Location: `/ea/GeoSignalEA.mq5` (ValidateSignal function, lines 278-330)

Parameters are checked in order:
1. Confidence threshold (hardcoded, not configurable)
2. Max concurrent positions (MAX_CONCURRENT_POSITIONS)
3. Duplicate symbol (logic-based, not configurable)
4. Daily loss limit (MAX_DAILY_LOSS_PERCENT)
5. Drawdown limit (MAX_DRAWDOWN_PERCENT)

## Safe Testing Workflow

1. **Start with defaults**
   - Use balanced configuration
   - Run baseline tests

2. **Test conservative settings**
   - Reduce limits to trigger gates more easily
   - Verify gates activate correctly

3. **Test aggressive settings**
   - Increase limits to allow more positions
   - Verify EA handles high load

4. **Document findings**
   - Record parameter values used
   - Record expected vs actual results
   - Note any issues or unexpected behavior

5. **Restore defaults**
   - Return to balanced configuration
   - Verify EA operates normally

## Parameter Impact Summary

| Parameter | Risk Gate Affected | Impact on Testing |
|-----------|-------------------|------------------|
| MAX_CONCURRENT_POSITIONS | Position Limit | Direct - set to 3 for max positions test |
| RISK_PER_TRADE_PERCENT | Position Sizing | Indirect - affects volume per trade |
| MAX_DAILY_LOSS_PERCENT | Daily Loss Gate | Direct - set to 5% for easier testing |
| MAX_DRAWDOWN_PERCENT | Drawdown Gate | Direct - set to 10% for easier testing |
| POLL_INTERVAL_SECONDS | Signal Polling | Indirect - affects how fast signals processed |
| DEBUG_MODE | Logging | Indirect - more detailed logs during testing |

---

**Last Updated:** 2026-04-07
**EA Version:** 1.00
**Applicable Parameters File:** `/ea/includes/risk_config.mqh`
