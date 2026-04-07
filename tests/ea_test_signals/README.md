# EA Signal Reading Test Suite

Comprehensive test signals and execution guides for validating the Expert Advisor's signal.json parsing and trade execution functionality.

## Test Files Overview

### Test Signal JSON Files

1. **test_signal_buy.json**
   - Action: BUY
   - Symbol: XAUUSD (Gold)
   - Volume: 0.5 lots
   - Confidence: 0.75
   - Expected: Order placed successfully
   - Purpose: Validate basic BUY order execution

2. **test_signal_sell.json**
   - Action: SELL
   - Symbol: EURUSD
   - Volume: 1.0 lots
   - Confidence: 0.65
   - Expected: Order placed successfully
   - Purpose: Validate SELL order execution

3. **test_signal_low_confidence.json**
   - Action: BUY (but confidence too low)
   - Symbol: GBPUSD
   - Confidence: 0.35 (below 0.5 threshold)
   - Expected: Signal REJECTED, no order
   - Purpose: Validate confidence threshold enforcement

4. **test_signal_hold.json**
   - Action: HOLD
   - Symbol: AUDUSD
   - Expected: Signal IGNORED, no order
   - Purpose: Validate that HOLD signals produce no trades

5. **test_signal_duplicate.json**
   - Event ID: test-buy-001 (duplicate of Test 1)
   - Action: BUY
   - Expected: Signal SKIPPED, duplicate detected
   - Purpose: Validate duplicate event_id detection

## Documentation Files

### TEST_EXECUTION_GUIDE.md
Complete manual testing guide with:
- Environment setup requirements
- Pre-test checklist
- Step-by-step procedures for each test
- Expected outcomes and troubleshooting
- Success criteria checklist
- Monitoring best practices

### TEST_RESULTS.md
Test results template with:
- Summary table for all 5 tests
- Detailed result recording sections
- Order ticket tracking fields
- Issue discovery template
- EA functionality assessment checklist
- Recommendation sections (APPROVED/INVESTIGATE/NOT APPROVED)
- Tester sign-off section

## Utility Scripts

### rotate_test_signals.py
Automated Python helper for signal rotation:

**Features:**
- Cycles through all test signals automatically
- Validates JSON format before copying
- Logs all actions to file and console
- Configurable polling interval (default: 60s)
- Test mode (run N cycles then exit)
- Error handling and reporting

**Usage:**
```bash
# Basic usage with default 60s interval
python rotate_test_signals.py --mt5-path "C:\Users\Admin\AppData\Roaming\MetaTrader 5\Files"

# Custom 90-second interval
python rotate_test_signals.py --mt5-path "C:\MT5Files" --interval 90

# Test mode: 5 cycles then exit
python rotate_test_signals.py --mt5-path "C:\MT5Files" --cycles 5

# With custom signals directory
python rotate_test_signals.py --mt5-path "C:\MT5Files" --signals-dir "C:\custom\path"
```

## Test Execution Flow

1. **Setup Phase**
   - Verify MT5 terminal is running
   - Attach EA to active chart
   - Confirm signal.json path accessibility
   - Review TEST_EXECUTION_GUIDE.md

2. **Manual Testing** (Step-by-step from guide)
   - Test 1: BUY signal
   - Test 2: SELL signal
   - Test 3: Low confidence (rejection)
   - Test 4: HOLD signal (ignore)
   - Test 5: Duplicate signal (skip)

3. **Automated Testing** (Optional, using rotate_test_signals.py)
   - Script copies signals in sequence
   - Each signal waits 60s for EA poll
   - Results logged for review

4. **Results Recording**
   - Fill in TEST_RESULTS.md
   - Record order tickets for successful trades
   - Document any deviations or issues
   - Provide recommendation

## Success Criteria

All 5 tests pass when:
- [ ] BUY order placed with correct parameters
- [ ] SELL order placed with correct parameters
- [ ] Low confidence signal correctly rejected
- [ ] HOLD signal properly ignored
- [ ] Duplicate signal properly detected and skipped
- [ ] All actions logged with event_id and timestamp
- [ ] No errors or exceptions in Journal
- [ ] Results reproducible on repeat testing

## Troubleshooting Guide

See TEST_EXECUTION_GUIDE.md "Troubleshooting" section for common issues:
- EA not executing after polling interval
- Wrong volume or parameters
- File access/locking issues
- Missing Journal messages
- Multiple executions from single signal

## File Structure

```
tests/ea_test_signals/
├── test_signal_buy.json              # Test 1: BUY order
├── test_signal_sell.json             # Test 2: SELL order
├── test_signal_low_confidence.json   # Test 3: Rejection test
├── test_signal_hold.json             # Test 4: Ignore test
├── test_signal_duplicate.json        # Test 5: Duplicate detection
├── TEST_EXECUTION_GUIDE.md           # Manual testing guide
├── TEST_RESULTS.md                   # Results template
├── rotate_test_signals.py            # Automated rotation script
└── README.md                         # This file
```

## Integration with EA

The EA expects signal.json in MT5 Files folder with this structure:
```json
{
  "timestamp": "2026-04-06T10:00:00Z",
  "event_id": "unique-identifier",
  "event_title": "Signal description",
  "action": "BUY|SELL|HOLD",
  "symbol": "XAUUSD",
  "confidence": 0.75,
  "volume": 0.5,
  "stop_loss": 2320.0,
  "take_profit": 2360.0,
  "rationale": "Brief explanation"
}
```

## Notes for Windows Stratos Testing

- All file paths in this suite use forward slashes (Python style)
- When running on Windows, adjust paths to use backslashes or raw strings
- MT5 Files folder typically located at: `C:\Users\[Username]\AppData\Roaming\MetaTrader 5\Files\`
- EA polling interval is configurable but default is 60 seconds
- Test signals should be copied via rotate_test_signals.py or manually moved to Files folder

## Version Information

- Test Suite Version: 1.0
- Created: 2026-04-06
- Target Platform: Windows Stratos MT5 Terminal
- Python Requirement: Python 3.7+
- EA Version Compatibility: [Specify EA version]

## Support

For issues or questions:
1. Review TEST_EXECUTION_GUIDE.md troubleshooting section
2. Check TEST_RESULTS.md for similar cases
3. Verify signal.json format and path
4. Consult EA developer documentation
5. Review MT5 Journal for detailed error messages
