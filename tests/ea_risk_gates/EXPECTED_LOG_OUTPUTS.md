# Expected Log Outputs Reference

This document lists the exact log messages that the GeoSignal EA produces for each risk gate rejection. Use this to verify that the EA is functioning correctly during testing.

## Log File Location

**File:** `ea_execution.log`  
**Path:** `C:\Users\[Username]\AppData\Roaming\MetaQuotes\Terminal\[ID]\MQL5\Files\`

The log file is created automatically when the EA starts and logs are written with each signal processing.

---

## Gate 1: Confidence Threshold

**Validation Code:** GeoSignalEA.mq5, lines 280-286  
**Condition:** `if(signal.confidence < 0.5)`

### Rejection Message

```
Signal validation failed: Confidence X.XX below 0.5 threshold
```

### Examples

```
[2026-04-07 10:00:15] Signal validation failed: Confidence 0.30 below 0.5 threshold
[2026-04-07 10:00:20] Signal validation failed: Confidence 0.45 below 0.5 threshold
[2026-04-07 10:00:25] Signal validation failed: Confidence 0.49 below 0.5 threshold
```

### Acceptance Messages (for reference)

```
[2026-04-07 10:00:30] Signal executed successfully: BUY USDJPY at confidence 0.50
[2026-04-07 10:00:35] Signal executed successfully: BUY AUDUSD at confidence 0.75
```

### Key Points

- Exact confidence value is logged (two decimals)
- Message uses "below 0.5 threshold" not "below threshold"
- Confidence of 0.5 exactly should be accepted, not rejected
- No position is opened when confidence is rejected

---

## Gate 2: Max Concurrent Positions

**Validation Code:** GeoSignalEA.mq5, lines 288-296  
**Condition:** `if(open_positions >= MAX_CONCURRENT_POSITIONS)`

### Rejection Message

```
Signal validation failed: Max positions [LIMIT] already open. Current: [COUNT]
```

### Examples

For MAX_CONCURRENT_POSITIONS = 3:

```
[2026-04-07 10:00:15] Signal validation failed: Max positions 3 already open. Current: 3
[2026-04-07 10:00:20] Signal validation failed: Max positions 3 already open. Current: 3
```

For MAX_CONCURRENT_POSITIONS = 5:

```
[2026-04-07 10:00:15] Signal validation failed: Max positions 5 already open. Current: 5
```

### Test-Specific Messages

When using `test_max_positions.json` with EA set to MAX_CONCURRENT_POSITIONS = 3:

```
[2026-04-07 10:00:15] Signal executed successfully: BUY EURUSD ... Confidence: 0.80
[2026-04-07 10:00:20] Signal executed successfully: BUY GBPUSD ... Confidence: 0.80
[2026-04-07 10:00:25] Signal executed successfully: BUY USDJPY ... Confidence: 0.80
[2026-04-07 10:00:30] Signal validation failed: Max positions 3 already open. Current: 3
```

### Key Points

- Both limit and current count are logged
- Message uses "Max positions X already open"
- Count is the current number of open positions
- Should trigger when current count == limit (not >)

---

## Gate 3: Duplicate Symbol

**Validation Code:** GeoSignalEA.mq5, lines 298-303  
**Condition:** `if(PositionSelect(signal.symbol))`

### Rejection Message

```
Signal validation failed: Position already open for [SYMBOL]
```

### Examples

```
[2026-04-07 10:00:15] Signal executed successfully: BUY EURUSD ... Confidence: 0.75
[2026-04-07 10:00:20] Signal validation failed: Position already open for EURUSD
[2026-04-07 10:00:25] Signal validation failed: Position already open for EURUSD
```

### Key Points

- Message includes the exact symbol (EURUSD, GBPUSD, etc.)
- Works for both BUY and SELL signals (rejects if position exists)
- No distinction between same action (BUY+BUY) or opposite action (BUY+SELL)
- Original position remains unaffected

---

## Gate 4: Daily Loss Limit

**Validation Code:** GeoSignalEA.mq5, lines 305-317  
**Condition:** `if(daily_profit < -max_loss_amount)`

**Formula:** 
```
daily_profit = equity - balance
max_loss_amount = (MAX_DAILY_LOSS_PERCENT / 100) * balance
Rejects if: daily_profit < -max_loss_amount
```

### Rejection Message

```
Signal validation failed: Daily loss [LOSS_AMOUNT] exceeds limit [LIMIT_AMOUNT]
```

### Examples

For account with $10,000 balance and MAX_DAILY_LOSS_PERCENT = 10.0:

```
[2026-04-07 10:30:00] Signal validation failed: Daily loss 1050.00 exceeds limit 1000.00
[2026-04-07 10:30:05] Signal validation failed: Daily loss 1100.00 exceeds limit 1000.00
```

For account with $5,000 balance and MAX_DAILY_LOSS_PERCENT = 5.0:

```
[2026-04-07 10:30:00] Signal validation failed: Daily loss 260.00 exceeds limit 250.00
```

### Before Rejection (Normal State)

```
[2026-04-07 10:00:00] Signal executed successfully: BUY EURUSD ... Confidence: 0.80
[2026-04-07 10:15:00] Daily loss: -500.00 (under limit of 1000.00) - trading continues
[2026-04-07 10:20:00] Signal executed successfully: BUY GBPUSD ... Confidence: 0.75
```

### Key Points

- Loss amounts are shown as positive numbers (not negative)
- Both actual loss and limit are included in message
- Loss is calculated as floating P&L from closed positions
- Different from drawdown (which includes unrealized losses)

---

## Gate 5: Drawdown Limit

**Validation Code:** GeoSignalEA.mq5, lines 319-327  
**Condition:** `if(equity_drawdown > MAX_DRAWDOWN_PERCENT)`

**Formula:**
```
equity_drawdown = (balance - equity) / balance * 100
Rejects if: equity_drawdown > MAX_DRAWDOWN_PERCENT
```

### Rejection Message

```
Signal validation failed: Drawdown X.XX% exceeds limit X.XX%
```

### Examples

For MAX_DRAWDOWN_PERCENT = 15.0:

```
[2026-04-07 10:30:00] Signal validation failed: Drawdown 15.20% exceeds limit 15.00%
[2026-04-07 10:30:05] Signal validation failed: Drawdown 16.50% exceeds limit 15.00%
```

For MAX_DRAWDOWN_PERCENT = 10.0:

```
[2026-04-07 10:30:00] Signal validation failed: Drawdown 10.10% exceeds limit 10.00%
```

### Before Rejection (Normal State)

```
[2026-04-07 10:00:00] Signal executed successfully: BUY EURUSD ... Confidence: 0.80
[2026-04-07 10:15:00] Current equity: 9500.00, Drawdown: 5.00% (under limit of 15.00%) - trading continues
[2026-04-07 10:20:00] Signal executed successfully: BUY GBPUSD ... Confidence: 0.75
```

### Key Points

- Drawdown percentage includes two decimal places
- Includes both actual drawdown and limit
- Drawdown measures unrealized losses in open positions
- Different from daily loss (which only counts closed losses)

---

## Overall Signal Execution Path

### Successful Signal Flow

```
[Timestamp] Signal read: BUY EURUSD at confidence 0.75
[Timestamp] Signal executed successfully: BUY EURUSD ... Confidence: 0.75
[Timestamp] Heartbeat written: execution=true status=success
```

### Rejected Signal Flow (Generic)

```
[Timestamp] Signal read: BUY EURUSD at confidence 0.30
[Timestamp] Signal validation failed: [GATE_SPECIFIC_MESSAGE]
[Timestamp] Signal execution aborted: Validation failed for EURUSD
[Timestamp] Heartbeat written: execution=false status=validation_failed
```

### Error Signal Flow

```
[Timestamp] Signal read: BUY EURUSD at confidence 0.75
[Timestamp] Error: Could not get price for symbol EURUSD
[Timestamp] Signal execution aborted: Price error for EURUSD
```

---

## Quick Reference: All 5 Rejection Messages

### Confidence (< 0.5)
```
Signal validation failed: Confidence 0.30 below 0.5 threshold
```

### Max Positions (>= limit)
```
Signal validation failed: Max positions 3 already open. Current: 3
```

### Duplicate Symbol (exists)
```
Signal validation failed: Position already open for EURUSD
```

### Daily Loss (exceeds %)
```
Signal validation failed: Daily loss 1050.00 exceeds limit 1000.00
```

### Drawdown (exceeds %)
```
Signal validation failed: Drawdown 15.20% exceeds limit 15.00%
```

---

## Searching Logs

### Using Windows Command Line

```batch
REM Find all rejections in log
findstr "validation failed" "ea_execution.log"

REM Find confidence rejections
findstr "Confidence" "ea_execution.log"

REM Find position limit rejections
findstr "Max positions" "ea_execution.log"

REM Find duplicate symbol rejections
findstr "already open" "ea_execution.log"

REM Find daily loss rejections
findstr "Daily loss" "ea_execution.log"

REM Find drawdown rejections
findstr "Drawdown" "ea_execution.log"

REM Find successful executions
findstr "executed successfully" "ea_execution.log"
```

### Using PowerShell

```powershell
# Find all validation failures
Select-String "validation failed" "ea_execution.log"

# Find specific gate rejections
Select-String "Confidence" "ea_execution.log"
Select-String "Max positions" "ea_execution.log"
Select-String "already open" "ea_execution.log"
Select-String "Daily loss" "ea_execution.log"
Select-String "Drawdown" "ea_execution.log"

# Get line count
(Select-String "Signal " "ea_execution.log").Count
```

---

## Testing Checklist

When validating each gate, ensure:

- [ ] Rejection message appears in log for invalid signals
- [ ] Exact values (confidence, counts, amounts, percentages) match expectations
- [ ] Successful signals show execution confirmation
- [ ] Timestamps are reasonable and sequential
- [ ] No duplicate messages for single signal
- [ ] No partial messages (complete log lines)

---

## Debugging Tips

1. **Message not appearing:** Check that DEBUG_MODE = true in EA parameters
2. **Unexpected message:** Verify signal.json is valid JSON
3. **Numbers don't match:** Check decimal precision in calculations
4. **No log file created:** Verify EA has write permissions to Files folder
5. **Timestamps missing:** Check system time is correct

---

## EA Code References

All rejection messages come from ValidateSignal() function in GeoSignalEA.mq5:

- **Line 281-286:** Confidence check
- **Line 289-296:** Max positions check  
- **Line 299-303:** Duplicate symbol check
- **Line 306-317:** Daily loss check
- **Line 320-327:** Drawdown check

Each gate outputs a unique message that can be searched in the log file.

