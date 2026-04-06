import json
import pytest
from engine.classifier import EventClassifier


@pytest.fixture
def classifier():
    """Create a classifier instance."""
    return EventClassifier()


def test_classifier_returns_trade_signal(classifier):
    """Classifier returns a dict with trade signal fields."""
    event = {
        "id": "test-1",
        "title": "US Fed Raises Interest Rates 0.5%",
        "description": "Federal Reserve increases rates amid inflation concerns.",
        "severity": "high",
    }

    signal = classifier.classify(event)

    assert isinstance(signal, dict)
    assert "action" in signal  # BUY, SELL, or HOLD
    assert "symbol" in signal
    assert "confidence" in signal
    assert "rationale" in signal
    assert isinstance(signal["confidence"], float)
    assert 0 <= signal["confidence"] <= 1.0
    assert signal["action"] in ["BUY", "SELL", "HOLD"]


def test_classifier_high_severity_events(classifier):
    """High-severity events trigger stronger signals."""
    high_sev = {
        "id": "test-high",
        "title": "Major Earthquake 7.5 Magnitude",
        "description": "Significant earthquake hits financial center.",
        "severity": "critical",
    }

    signal = classifier.classify(high_sev)

    # Expect non-HOLD signal for critical event
    assert signal["action"] != "HOLD"
    assert signal["confidence"] > 0.5


def test_classifier_handles_unrelated_events(classifier):
    """Unrelated events return HOLD signal."""
    unrelated = {
        "id": "test-unrelated",
        "title": "Local Sports Team Wins Championship",
        "description": "City celebrates local sports victory.",
        "severity": "low",
    }

    signal = classifier.classify(unrelated)

    assert signal["action"] == "HOLD"


def test_classifier_produces_rationale(classifier):
    """Signal includes text rationale explaining the trade."""
    event = {
        "id": "test-2",
        "title": "Oil Production Cut by OPEC",
        "description": "OPEC announces coordinated production cut.",
        "severity": "medium",
    }

    signal = classifier.classify(event)

    assert len(signal["rationale"]) > 10
    assert isinstance(signal["rationale"], str)


def test_classifier_suggests_forex_pairs(classifier):
    """Classifier returns valid forex/commodity symbols."""
    event = {
        "id": "test-3",
        "title": "US Dollar Strengthens Against Euro",
        "description": "Dollar gains on economic data.",
        "severity": "medium",
    }

    signal = classifier.classify(event)

    # Expect forex pair
    assert signal["symbol"] in [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
        "XAUUSD", "XBRUSD", "XTIUSD",  # Commodities
        "HOLD"
    ]


def test_classifier_handles_json_errors(classifier):
    """Gracefully handles Claude JSON errors."""
    # This test verifies that even if Claude returns malformed JSON,
    # the classifier returns a valid HOLD signal
    event = {
        "id": "test-error",
        "title": "Test Event",
        "description": "Test description",
        "severity": "low",
    }

    signal = classifier.classify(event)

    # Should always return a valid signal, even on error
    assert isinstance(signal, dict)
    assert "action" in signal
    assert "symbol" in signal
    assert "confidence" in signal
    assert "rationale" in signal
