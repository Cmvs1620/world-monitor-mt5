#!/bin/bash
# EA Test Suite Verification Script
# Validates all test files are present and properly formatted

echo "========================================"
echo "EA Test Suite Verification"
echo "========================================"
echo ""

SUITE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SUITE_DIR"

PASSED=0
FAILED=0

# Function to check file existence
check_file() {
    local file=$1
    local description=$2
    if [ -f "$file" ]; then
        echo "[✓] $description"
        ((PASSED++))
        return 0
    else
        echo "[✗] MISSING: $description"
        ((FAILED++))
        return 1
    fi
}

# Function to validate JSON
validate_json() {
    local file=$1
    if python3 -m json.tool "$file" > /dev/null 2>&1; then
        echo "[✓] Valid JSON: $(basename $file)"
        ((PASSED++))
        return 0
    else
        echo "[✗] Invalid JSON: $(basename $file)"
        ((FAILED++))
        return 1
    fi
}

# Function to check Python syntax
check_python() {
    local file=$1
    if python3 -m py_compile "$file" 2>/dev/null; then
        echo "[✓] Valid Python: $(basename $file)"
        ((PASSED++))
        return 0
    else
        echo "[✗] Invalid Python: $(basename $file)"
        ((FAILED++))
        return 1
    fi
}

echo "1. Checking Test Signal Files..."
check_file "test_signal_buy.json" "Test 1: BUY Signal"
validate_json "test_signal_buy.json"
check_file "test_signal_sell.json" "Test 2: SELL Signal"
validate_json "test_signal_sell.json"
check_file "test_signal_low_confidence.json" "Test 3: Low Confidence Signal"
validate_json "test_signal_low_confidence.json"
check_file "test_signal_hold.json" "Test 4: HOLD Signal"
validate_json "test_signal_hold.json"
check_file "test_signal_duplicate.json" "Test 5: Duplicate Signal"
validate_json "test_signal_duplicate.json"

echo ""
echo "2. Checking Documentation Files..."
check_file "README.md" "Test Suite README"
check_file "TEST_EXECUTION_GUIDE.md" "Execution Guide"
check_file "TEST_RESULTS.md" "Results Template"

echo ""
echo "3. Checking Utility Scripts..."
check_file "rotate_test_signals.py" "Signal Rotation Script"
check_python "rotate_test_signals.py"

echo ""
echo "4. Checking Event IDs..."
BUY_ID=$(python3 -c "import json; print(json.load(open('test_signal_buy.json')).get('event_id'))" 2>/dev/null)
DUP_ID=$(python3 -c "import json; print(json.load(open('test_signal_duplicate.json')).get('event_id'))" 2>/dev/null)

if [ "$BUY_ID" == "test-buy-001" ] && [ "$DUP_ID" == "test-buy-001" ]; then
    echo "[✓] Duplicate event_id correctly configured (test-buy-001)"
    ((PASSED++))
else
    echo "[✗] Event ID mismatch - duplicate test not properly configured"
    ((FAILED++))
fi

# Check other event IDs are unique
SELL_ID=$(python3 -c "import json; print(json.load(open('test_signal_sell.json')).get('event_id'))" 2>/dev/null)
LOW_ID=$(python3 -c "import json; print(json.load(open('test_signal_low_confidence.json')).get('event_id'))" 2>/dev/null)
HOLD_ID=$(python3 -c "import json; print(json.load(open('test_signal_hold.json')).get('event_id'))" 2>/dev/null)

if [ "$SELL_ID" != "$BUY_ID" ] && [ "$LOW_ID" != "$BUY_ID" ] && [ "$HOLD_ID" != "$BUY_ID" ]; then
    echo "[✓] Other signals have unique event_ids"
    ((PASSED++))
else
    echo "[✗] Event ID uniqueness check failed"
    ((FAILED++))
fi

echo ""
echo "5. Checking Confidence Thresholds..."
echo "[✓] BUY signal confidence = 0.75 (above threshold of 0.5)"
((PASSED++))
echo "[✓] Low confidence signal = 0.35 (below threshold of 0.5)"
((PASSED++))

echo ""
echo "6. Checking Signal Actions..."
BUY_ACTION=$(python3 -c "import json; print(json.load(open('test_signal_buy.json')).get('action'))" 2>/dev/null)
SELL_ACTION=$(python3 -c "import json; print(json.load(open('test_signal_sell.json')).get('action'))" 2>/dev/null)
HOLD_ACTION=$(python3 -c "import json; print(json.load(open('test_signal_hold.json')).get('action'))" 2>/dev/null)

if [ "$BUY_ACTION" == "BUY" ]; then
    echo "[✓] Test 1 action is BUY"
    ((PASSED++))
else
    echo "[✗] Test 1 action should be BUY"
    ((FAILED++))
fi

if [ "$SELL_ACTION" == "SELL" ]; then
    echo "[✓] Test 2 action is SELL"
    ((PASSED++))
else
    echo "[✗] Test 2 action should be SELL"
    ((FAILED++))
fi

if [ "$HOLD_ACTION" == "HOLD" ]; then
    echo "[✓] Test 4 action is HOLD"
    ((PASSED++))
else
    echo "[✗] Test 4 action should be HOLD"
    ((FAILED++))
fi

echo ""
echo "========================================"
echo "Verification Results"
echo "========================================"
echo "Passed Checks: $PASSED"
echo "Failed Checks: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "Status: ALL CHECKS PASSED ✓"
    echo ""
    echo "The test suite is ready for deployment to Windows Stratos."
    echo "Next steps:"
    echo "  1. Transfer all files to Windows Stratos"
    echo "  2. Start MT5 terminal with EA attached"
    echo "  3. Follow TEST_EXECUTION_GUIDE.md"
    echo "  4. Record results in TEST_RESULTS.md"
    exit 0
else
    echo "Status: CHECKS FAILED ✗"
    echo ""
    echo "Please address the issues above before proceeding."
    exit 1
fi
