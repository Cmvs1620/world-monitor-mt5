# EA Risk Gates Test Suite

## Overview

This directory contains comprehensive test scenarios and documentation for validating all five risk validation gates in the GeoSignal Expert Advisor (EA).

The test suite ensures that the EA correctly enforces risk management rules before executing any trade signals, protecting the account from excessive losses and position concentration risk.

## Risk Gates Tested

| # | Gate | Default Limit | Test File | Purpose |
|---|------|---------------|-----------|---------|
| 1 | **Confidence Threshold** | ≥ 0.5 | `test_low_confidence.json` | Reject signals with low confidence |
| 2 | **Max Concurrent Positions** | ≤ 5 | `test_max_positions.json` | Prevent excessive position concentration |
| 3 | **Duplicate Symbol** | 1 per symbol | `test_duplicate_symbol.json` | Block multiple positions in same pair |
| 4 | **Daily Loss Limit** | ≤ 10% | `test_daily_loss.json` | Stop trading after daily loss threshold |
| 5 | **Drawdown Limit** | ≤ 15% | `test_drawdown_limit.json` | Stop trading after equity drawdown |

## Directory Structure

```
tests/ea_risk_gates/
├── README.md                          # This file
├── RISK_GATES_TEST_GUIDE.md           # Comprehensive test execution guide
├── RISK_PARAMETERS_ADJUSTMENT.md      # How to modify EA parameters
├── EXPECTED_LOG_OUTPUTS.md            # EA log message reference
├── VALIDATION_CHECKLIST.md            # Test results tracking table
├── test_max_positions.json            # Test scenario 1: Max positions
├── test_duplicate_symbol.json         # Test scenario 2: Duplicate symbol
├── test_low_confidence.json           # Test scenario 3: Low confidence
├── test_daily_loss.json               # Test scenario 4: Daily loss
├── test_drawdown_limit.json           # Test scenario 5: Drawdown limit
└── run_risk_gate_tests.py             # Automated test runner utility
```

## Quick Start

### Prerequisites
- MetaTrader 5 terminal running
- GeoSignalEA deployed and attached to a chart
- Python 3.8+ (for automated test runner)
- Test signals ready to be sent

### Running Tests Manually

1. **Start with Confidence Threshold Test (simplest)**
   ```bash
   # Send the signal from test_low_confidence.json to MT5
   # Expected: Signal rejected with "Confidence 0.30 below 0.5 threshold"
   ```

2. **Test Duplicate Symbol Blocking**
   ```bash
   # Send first signal from test_duplicate_symbol.json
   # Expected: First EURUSD BUY executes
   
   # Send second signal (same symbol, different confidence)
   # Expected: Rejected with "Position already open in EURUSD"
   ```

3. **Test Max Positions Limit**
   - Set `MAX_CONCURRENT_POSITIONS = 3` in EA inputs
   - Send signals 1-3 sequentially (all should execute)
   - Send signal 4 (should be rejected)

4. **Test Daily Loss Limit**
   - Close existing positions
   - Manually create losing trades to hit 10% daily loss
   - Send new signal
   - Expected: Rejected with "Daily loss exceeded"

5. **Test Drawdown Limit**
   - Close existing positions
   - Create trades that result in 15%+ drawdown
   - Send new signal
   - Expected: Rejected with "Drawdown exceeded"

### Running Tests Automatically

```bash
# Navigate to test directory
cd tests/ea_risk_gates

# Run automated test runner
python run_risk_gate_tests.py --mt5-path "C:\path\to\mt5\files"

# Run specific test scenario
python run_risk_gate_tests.py --test max_positions --mt5-path "C:\path"

# Enable verbose logging
python run_risk_gate_tests.py --verbose --mt5-path "C:\path"
```

## Test Files Format

All JSON test files follow this structure:

```json
{
  "test_name": "Test Name",
  "test_description": "Description of what's being tested",
  "risk_gate": "Name of the risk gate being tested",
  "signals": [
    {
      "sequence": 1,
      "timestamp": "2026-04-07T10:00:00Z",
      "event_id": "test-gate-001",
      "event_title": "Signal Description",
      "action": "BUY" or "SELL",
      "symbol": "EURUSD",
      "confidence": 0.8,
      "volume": 1.0,
      "stop_loss": 0.0,
      "take_profit": 0.0,
      "rationale": "Why this signal is being sent",
      "expected_outcome": "What should happen"
    }
  ],
  "test_procedure": ["Step 1", "Step 2", ...],
  "success_criteria": ["Criterion 1", "Criterion 2", ...]
}
```

## Expected Log Outputs

Each risk gate rejection produces a specific log message. Reference guide:

| Gate | Rejection Message | Log File Location |
|------|------------------|------------------|
| Confidence | `"Confidence 0.30 below 0.5 threshold"` | MT5 Journal |
| Max Positions | `"Max positions 5 already open"` | ea_execution.log |
| Duplicate Symbol | `"Position already open in EURUSD"` | ea_execution.log |
| Daily Loss | `"Daily loss exceeds limit 10%"` | ea_execution.log |
| Drawdown | `"Drawdown exceeds limit 15%"` | ea_execution.log |

See `EXPECTED_LOG_OUTPUTS.md` for detailed reference with code line numbers.

## Test Configuration Reference

### Confidence Threshold Test
- **File:** `test_low_confidence.json`
- **Expected Behavior:** Single signal with confidence 0.3 rejected
- **Parameters:** Use defaults
- **Time Required:** 1 minute
- **Difficulty:** Easiest

### Duplicate Symbol Test
- **File:** `test_duplicate_symbol.json`
- **Expected Behavior:** First EURUSD buy succeeds, second buy rejected
- **Parameters:** Use defaults
- **Time Required:** 2 minutes
- **Difficulty:** Easy

### Max Positions Test
- **File:** `test_max_positions.json`
- **Expected Behavior:** First 3 signals execute, 4th rejected
- **Parameters:** Set `MAX_CONCURRENT_POSITIONS = 3`
- **Time Required:** 3 minutes
- **Difficulty:** Medium (requires parameter adjustment)

### Daily Loss Test
- **File:** `test_daily_loss.json`
- **Expected Behavior:** New signals rejected after 10% daily loss
- **Parameters:** Set `MAX_DAILY_LOSS_PERCENT = 5%` (for easier testing)
- **Time Required:** 5-10 minutes
- **Difficulty:** Hard (requires creating losing positions)

### Drawdown Test
- **File:** `test_drawdown_limit.json`
- **Expected Behavior:** New signals rejected after 15% equity drawdown
- **Parameters:** Set `MAX_DRAWDOWN_PERCENT = 10%` (for easier testing)
- **Time Required:** 5-10 minutes
- **Difficulty:** Hard (requires creating drawdown scenario)

## Validation Checklist

Use `VALIDATION_CHECKLIST.md` to track test results:

```markdown
| Risk Gate | Signal Sent | Expected Result | Actual Result | Pass/Fail | Notes |
|-----------|-------------|-----------------|---------------|-----------|-------|
| Confidence | Yes | REJECTED | REJECTED | PASS | Confidence 0.3 < 0.5 |
| Duplicate | Yes | REJECTED | REJECTED | PASS | EURUSD second buy blocked |
| ...       | ...  | ...      | ...       | ...  | ... |
```

## Pre-Test Checklist

Before running any test:

- [ ] MetaTrader 5 is running
- [ ] GeoSignalEA is deployed on a chart
- [ ] EA is set to `EA_ENABLED = true`
- [ ] EA is set to `EA_TRADING_ENABLED = false` (to prevent real trades)
- [ ] `DEBUG_MODE = true` (optional but recommended for testing)
- [ ] All open positions are closed
- [ ] Account balance is stable
- [ ] No other EAs or scripts running
- [ ] Signal file path is correct in EA configuration
- [ ] Journal and Logs folders are accessible

## Common Test Scenarios

### Scenario 1: Quick Risk Gate Validation (15 minutes)
1. Run confidence test
2. Run duplicate symbol test
3. Run 1 max positions test cycle
4. Review log outputs

### Scenario 2: Comprehensive Risk Testing (45 minutes)
1. Test all 5 gates in sequence
2. Modify parameters between tests
3. Verify gate triggers and log messages
4. Document results in checklist

### Scenario 3: Stress Testing (1-2 hours)
1. Set aggressive parameters
2. Send multiple signals rapidly
3. Create losing positions
4. Verify drawdown/loss limits trigger
5. Review comprehensive logs

## Troubleshooting

### Signal Not Being Read
- **Check:** Signal file path in EA inputs
- **Check:** Signal JSON format is valid
- **Check:** Event_id is unique
- **Solution:** See `RISK_GATES_TEST_GUIDE.md` Troubleshooting section

### EA Not Rejecting Expected Signal
- **Check:** Parameter value in EA inputs
- **Check:** Current position/account state
- **Check:** EA log for actual rejection reason
- **Solution:** Compare actual vs expected in log outputs

### Parameter Changes Not Taking Effect
- **Check:** EA recompiled after parameter change
- **Check:** EA reattached to chart
- **Check:** MT5 restarted if needed
- **Solution:** See `RISK_PARAMETERS_ADJUSTMENT.md`

### Conflicting Test Results
- **Check:** No overlapping tests running
- **Check:** All positions closed between tests
- **Check:** Account state stable
- **Solution:** Restart EA and try individual test in isolation

## Documentation Files Reference

| File | Purpose | When to Use |
|------|---------|------------|
| `README.md` | Overview and quick start | First time setup |
| `RISK_GATES_TEST_GUIDE.md` | Detailed execution procedures | Running actual tests |
| `RISK_PARAMETERS_ADJUSTMENT.md` | How to modify EA parameters | Adjusting test configuration |
| `EXPECTED_LOG_OUTPUTS.md` | EA log message reference | Interpreting results |
| `VALIDATION_CHECKLIST.md` | Test results tracking | Documenting findings |

## Test Automation

### Automated Test Runner

The `run_risk_gate_tests.py` utility provides automated testing:

```bash
# Show help
python run_risk_gate_tests.py --help

# Run all tests
python run_risk_gate_tests.py --mt5-path "C:\path"

# Run specific test
python run_risk_gate_tests.py --test low_confidence --mt5-path "C:\path"

# Verbose output
python run_risk_gate_tests.py --verbose --mt5-path "C:\path"

# Generate report
python run_risk_gate_tests.py --report test_results.txt --mt5-path "C:\path"
```

See `run_risk_gate_tests.py` for detailed options.

## Test Success Criteria

A test passes when:

1. **Expected outcome matches actual outcome**
   - If expecting rejection, signal is rejected
   - If expecting execution, position opens

2. **EA logs correct rejection reason**
   - Log message matches expected output format
   - Includes relevant parameter values

3. **No unexpected errors occur**
   - EA does not crash
   - No "critical error" messages in journal
   - EA remains operational

4. **State is correct after test**
   - Correct number of positions open
   - No orphaned orders
   - Account state is consistent

## Post-Test Cleanup

After each test:

1. Close all open positions manually in MT5
2. Reset all modified parameters to defaults
3. Remove signal.json file
4. Verify account is in clean state
5. Check EA logs for any errors

## Integration with CI/CD

These tests can be integrated into continuous integration:

```bash
# Run in CI pipeline
python run_risk_gate_tests.py \
  --mt5-path "/mt5/files" \
  --report "test_results.json" \
  --timeout 300
```

See `run_risk_gate_tests.py` for CI/CD integration options.

## Performance Baseline

Expected test execution times:

| Test | Manual | Automated |
|------|--------|-----------|
| Confidence | 1-2 min | 30 sec |
| Duplicate Symbol | 2-3 min | 45 sec |
| Max Positions | 3-5 min | 1.5 min |
| Daily Loss | 5-10 min | 2-3 min |
| Drawdown | 5-10 min | 2-3 min |
| **All tests** | **20-30 min** | **8-10 min** |

## Contributing Additional Tests

To add new risk gate tests:

1. Create new JSON file following test format
2. Add test scenario to this README
3. Update `VALIDATION_CHECKLIST.md`
4. Add log output reference to `EXPECTED_LOG_OUTPUTS.md`
5. Update `run_risk_gate_tests.py` to include new test
6. Document in `RISK_GATES_TEST_GUIDE.md`

## Maintenance

### Regular Review
- Review test suite monthly
- Update for EA version changes
- Validate log message formats
- Document any new findings

### EA Version Updates
- Verify tests still apply to new EA version
- Update expected log outputs if messages changed
- Recalibrate parameter values if defaults changed
- Document any compatibility issues

## Reference Links

- **EA Source Code:** `/ea/GeoSignalEA.mq5`
- **Risk Configuration:** `/ea/includes/risk_config.mqh`
- **Risk Gate Engine:** `/engine/risk_gate.py`
- **Integration Tests:** `/tests/test_risk_gate.py`

## Support and Questions

For questions about:
- **Test execution:** See `RISK_GATES_TEST_GUIDE.md`
- **Parameter modification:** See `RISK_PARAMETERS_ADJUSTMENT.md`
- **Log output interpretation:** See `EXPECTED_LOG_OUTPUTS.md`
- **Results tracking:** See `VALIDATION_CHECKLIST.md`

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-07 | Initial test suite creation with 5 risk gate scenarios |

---

**Last Updated:** 2026-04-07  
**EA Version Tested:** 1.00  
**Test Suite Version:** 1.0
