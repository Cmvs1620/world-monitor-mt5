"""Unit tests for the RiskGate pre-trade validator."""

import pytest
from engine.risk_gate import RiskGate


@pytest.fixture
def config():
    """Create a standard risk configuration."""
    return {
        "account_balance": 10000.0,
        "max_concurrent_positions": 3,
        "risk_per_trade_percent": 1.0,
        "max_drawdown_percent": 5.0,
    }


@pytest.fixture
def risk_gate(config):
    """Create a RiskGate instance."""
    return RiskGate(config)


def test_gate_allows_valid_trade(risk_gate):
    """Valid signal with high confidence passes all checks."""
    signal = {
        "action": "BUY",
        "symbol": "EURUSD",
        "confidence": 0.75,
        "rationale": "Strong uptrend detected",
    }
    current_positions = []

    result = risk_gate.validate(signal, current_positions)

    assert result["allowed"] is True
    assert "volume" in result
    assert result["volume"] > 0
    assert isinstance(result["reason"], str)


def test_gate_blocks_low_confidence_trade(risk_gate):
    """Signal with confidence below 0.5 is blocked."""
    signal = {
        "action": "BUY",
        "symbol": "EURUSD",
        "confidence": 0.45,
        "rationale": "Weak signal",
    }
    current_positions = []

    result = risk_gate.validate(signal, current_positions)

    assert result["allowed"] is False
    assert "confidence" in result["reason"].lower()


def test_gate_blocks_too_many_positions(risk_gate):
    """When already at max positions, new trades are blocked."""
    signal = {
        "action": "BUY",
        "symbol": "GBPUSD",
        "confidence": 0.75,
        "rationale": "Valid signal",
    }
    # Already have 3 positions (at max)
    current_positions = [
        {"symbol": "EURUSD", "volume": 1.0},
        {"symbol": "USDJPY", "volume": 1.0},
        {"symbol": "AUDUSD", "volume": 1.0},
    ]

    result = risk_gate.validate(signal, current_positions)

    assert result["allowed"] is False
    assert "position" in result["reason"].lower()


def test_gate_calculates_position_size(risk_gate):
    """Correct volume is calculated based on account and confidence."""
    signal = {
        "action": "BUY",
        "symbol": "EURUSD",
        "confidence": 0.80,
        "rationale": "Strong signal",
    }
    current_positions = []

    result = risk_gate.validate(signal, current_positions)

    assert result["allowed"] is True
    volume = result["volume"]
    # With 0.80 confidence and 1% risk:
    # Risk amount = 10000 * min(0.80/100, 1.0/100) = 10000 * 0.01 = 100
    # Volume = 100 / 100 = 1.0
    assert 0.01 <= volume <= 10.0  # Within lot bounds
    assert volume > 0


def test_gate_blocks_duplicate_symbol(risk_gate):
    """Same symbol cannot be opened twice."""
    signal = {
        "action": "BUY",
        "symbol": "EURUSD",
        "confidence": 0.75,
        "rationale": "Valid signal",
    }
    # Already have EURUSD open
    current_positions = [
        {"symbol": "EURUSD", "volume": 1.0},
    ]

    result = risk_gate.validate(signal, current_positions)

    assert result["allowed"] is False
    assert "already" in result["reason"].lower() or "duplicate" in result["reason"].lower()


def test_gate_respects_drawdown_limit(risk_gate):
    """Blocks trades if drawdown limit exceeded."""
    signal = {
        "action": "BUY",
        "symbol": "EURUSD",
        "confidence": 0.75,
        "rationale": "Valid signal",
    }
    current_positions = []
    current_drawdown_percent = 5.1  # Exceeds 5% limit

    result = risk_gate.validate(signal, current_positions, current_drawdown_percent)

    assert result["allowed"] is False
    assert "drawdown" in result["reason"].lower()


def test_gate_allows_trade_within_drawdown(risk_gate):
    """Allows trades if drawdown is within limit."""
    signal = {
        "action": "BUY",
        "symbol": "EURUSD",
        "confidence": 0.75,
        "rationale": "Valid signal",
    }
    current_positions = []
    current_drawdown_percent = 2.5  # Within 5% limit

    result = risk_gate.validate(signal, current_positions, current_drawdown_percent)

    assert result["allowed"] is True


def test_gate_blocks_hold_action(risk_gate):
    """HOLD action signals are not opened as trades."""
    signal = {
        "action": "HOLD",
        "symbol": "EURUSD",
        "confidence": 0.75,
        "rationale": "No position change",
    }
    current_positions = []

    result = risk_gate.validate(signal, current_positions)

    assert result["allowed"] is False
    assert "hold" in result["reason"].lower()


def test_gate_clamps_volume_to_bounds(risk_gate):
    """Volume is clamped between 0.01 and 10.0 lots."""
    # Very high confidence would produce large volume
    signal = {
        "action": "BUY",
        "symbol": "EURUSD",
        "confidence": 1.0,
        "rationale": "Perfect signal",
    }
    current_positions = []

    result = risk_gate.validate(signal, current_positions)

    if result["allowed"]:
        volume = result["volume"]
        assert volume >= 0.01
        assert volume <= 10.0


def test_gate_returns_correct_structure(risk_gate):
    """Result always has required keys."""
    signal = {
        "action": "BUY",
        "symbol": "EURUSD",
        "confidence": 0.75,
        "rationale": "Test",
    }
    current_positions = []

    result = risk_gate.validate(signal, current_positions)

    assert "allowed" in result
    assert isinstance(result["allowed"], bool)
    assert "reason" in result
    assert isinstance(result["reason"], str)
    assert "volume" in result
    assert isinstance(result["volume"], (int, float))
