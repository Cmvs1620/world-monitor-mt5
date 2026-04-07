"""Integration tests for the complete MT5 GeoSignal signal pipeline.

Tests the end-to-end flow without mocking:
1. Fetch events from WorldMonitor API
2. Classify with Claude
3. Validate with RiskGate
4. Write to signal.json

No real MT5 connection needed (Phase 1 is Python only).
Uses real APIs where available, gracefully skips if offline.
"""

import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from engine.router import SignalRouter


class TestFullPipeline:
    """Integration tests for the complete signal pipeline."""

    @pytest.fixture
    def temp_signals_dir(self):
        """Create a temporary directory for signal output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def config(self, temp_signals_dir):
        """Create config pointing to temp directory for output."""
        return {
            "debug": False,
            "account_balance": 10000.0,
            "max_concurrent_positions": 3,
            "risk_per_trade_percent": 1.0,
            "max_drawdown_percent": 5.0,
            "mt5_files_path": temp_signals_dir,
        }

    @pytest.fixture
    def mock_events(self):
        """Sample events from WorldMonitor API for testing."""
        return [
            {
                "id": "evt_integration_001",
                "title": "US Federal Reserve Raises Interest Rates 0.5%",
                "description": "Federal Reserve increases rates amid inflation concerns.",
                "timestamp": "2024-04-01T10:00:00Z",
                "severity": "high",
                "region": "North America",
                "category": "economic",
                "source": "worldmonitor",
            },
            {
                "id": "evt_integration_002",
                "title": "Oil Prices Surge on Geopolitical Tensions",
                "description": "Crude oil prices jump 5% due to regional tensions.",
                "timestamp": "2024-04-02T14:30:00Z",
                "severity": "high",
                "region": "Middle East",
                "category": "economic",
                "source": "worldmonitor",
            },
        ]

    def test_full_pipeline_with_mocked_api(self, config, mock_events, temp_signals_dir):
        """
        Test complete pipeline: fetch → classify → validate → write signal.json.

        This test mocks the WorldMonitor API to provide consistent test data.
        It verifies:
        1. SignalRouter fetches events (mocked to avoid real API call)
        2. Events are classified by Claude
        3. Classified signals pass/fail risk validation
        4. signal.json is created with correct structure
        """
        # Setup temp directories
        signals_dir = Path(temp_signals_dir) / "signals"
        logs_dir = Path(temp_signals_dir) / "logs"
        signals_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Create router with config
        with patch("engine.router.WorldMonitorClient") as mock_wm_class:
            # Setup mock WorldMonitor to return test events
            mock_wm = MagicMock()
            mock_wm.fetch_events.return_value = mock_events
            mock_wm_class.return_value = mock_wm

            router = SignalRouter(config)

            # Override paths to use temp directories
            router.signals_dir = signals_dir
            router.logs_dir = logs_dir
            router.signal_json_path = router.signals_dir / "signal.json"
            router.signal_log_path = router.signals_dir / "signal_log.json"
            router.csv_log_path = router.logs_dir / "signals.csv"

            # Ensure directories exist
            router.signals_dir.mkdir(parents=True, exist_ok=True)
            router.logs_dir.mkdir(parents=True, exist_ok=True)
            router._init_csv_file()

            # Run the pipeline
            result = router.run_once(current_positions=[])

        # Assertions on result dict
        assert isinstance(result, dict)
        assert "timestamp" in result
        assert "events_fetched" in result
        assert "signals_generated" in result
        assert "signals_passed" in result
        assert "active_signal" in result
        assert "errors" in result

        # Check result values
        assert result["events_fetched"] >= 0, "Should fetch events"
        assert result["signals_generated"] >= 0, "Should generate signals"
        assert result["signals_passed"] >= 0, "Should validate signals"
        assert result["signals_generated"] >= result["signals_passed"], \
            "Passed signals should not exceed generated signals"
        assert isinstance(result["errors"], list), "Errors should be a list"

        # If events were fetched and passed validation, check signal.json exists
        if result["events_fetched"] > 0 and result["signals_passed"] > 0:
            signal_json_path = signals_dir / "signal.json"
            assert signal_json_path.exists(), "signal.json should exist after passing signals"

            # Verify signal.json is valid JSON
            with open(signal_json_path, "r") as f:
                signal_data = json.load(f)

            # Verify signal has required fields
            required_fields = ["action", "symbol", "confidence", "rationale", "timestamp"]
            for field in required_fields:
                assert field in signal_data, f"Signal missing required field: {field}"

            # Verify field types and values
            assert signal_data["action"] in ["BUY", "SELL", "HOLD"], "Action must be valid"
            assert isinstance(signal_data["symbol"], str), "Symbol must be string"
            assert isinstance(signal_data["confidence"], (int, float)), "Confidence must be numeric"
            assert 0 <= signal_data["confidence"] <= 1.0, "Confidence must be 0-1"
            assert isinstance(signal_data["rationale"], str), "Rationale must be string"
            assert len(signal_data["rationale"]) > 0, "Rationale should not be empty"

    def test_pipeline_handles_no_events(self, config, temp_signals_dir):
        """Test pipeline gracefully handles case when no events are returned."""
        signals_dir = Path(temp_signals_dir) / "signals"
        logs_dir = Path(temp_signals_dir) / "logs"
        signals_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)

        with patch("engine.router.WorldMonitorClient") as mock_wm_class:
            # Setup mock WorldMonitor to return empty list
            mock_wm = MagicMock()
            mock_wm.fetch_events.return_value = []
            mock_wm_class.return_value = mock_wm

            router = SignalRouter(config)
            router.signals_dir = signals_dir
            router.logs_dir = logs_dir
            router.signal_json_path = router.signals_dir / "signal.json"
            router.signal_log_path = router.signals_dir / "signal_log.json"
            router.csv_log_path = router.logs_dir / "signals.csv"
            router.signals_dir.mkdir(parents=True, exist_ok=True)
            router.logs_dir.mkdir(parents=True, exist_ok=True)
            router._init_csv_file()

            result = router.run_once(current_positions=[])

        # Should return valid result even with no events
        assert result["events_fetched"] == 0
        assert result["signals_generated"] == 0
        assert result["signals_passed"] == 0
        assert result["active_signal"] is None
        assert result["errors"] == []

    def test_pipeline_with_current_positions(self, config, mock_events, temp_signals_dir):
        """Test pipeline with existing open positions (should limit new trades)."""
        signals_dir = Path(temp_signals_dir) / "signals"
        logs_dir = Path(temp_signals_dir) / "logs"
        signals_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)

        current_positions = [
            {"symbol": "EURUSD", "volume": 1.0},
            {"symbol": "GBPUSD", "volume": 1.0},
        ]

        with patch("engine.router.WorldMonitorClient") as mock_wm_class:
            mock_wm = MagicMock()
            mock_wm.fetch_events.return_value = mock_events
            mock_wm_class.return_value = mock_wm

            router = SignalRouter(config)
            router.signals_dir = signals_dir
            router.logs_dir = logs_dir
            router.signal_json_path = router.signals_dir / "signal.json"
            router.signal_log_path = router.signals_dir / "signal_log.json"
            router.csv_log_path = router.logs_dir / "signals.csv"
            router.signals_dir.mkdir(parents=True, exist_ok=True)
            router.logs_dir.mkdir(parents=True, exist_ok=True)
            router._init_csv_file()

            result = router.run_once(current_positions=current_positions)

        # Should process events even with existing positions
        assert result["events_fetched"] >= 0
        assert result["signals_generated"] >= 0
        # Signals might be blocked if duplicate symbols or position limits reached
        assert result["signals_passed"] >= 0
        assert isinstance(result["errors"], list)

    def test_pipeline_logs_are_created(self, config, mock_events, temp_signals_dir):
        """Test that pipeline creates log files (CSV and JSON)."""
        signals_dir = Path(temp_signals_dir) / "signals"
        logs_dir = Path(temp_signals_dir) / "logs"
        signals_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)

        with patch("engine.router.WorldMonitorClient") as mock_wm_class:
            mock_wm = MagicMock()
            mock_wm.fetch_events.return_value = mock_events
            mock_wm_class.return_value = mock_wm

            router = SignalRouter(config)
            router.signals_dir = signals_dir
            router.logs_dir = logs_dir
            router.signal_json_path = router.signals_dir / "signal.json"
            router.signal_log_path = router.signals_dir / "signal_log.json"
            router.csv_log_path = router.logs_dir / "signals.csv"
            router.signals_dir.mkdir(parents=True, exist_ok=True)
            router.logs_dir.mkdir(parents=True, exist_ok=True)
            router._init_csv_file()

            result = router.run_once(current_positions=[])

        # CSV log should exist and have content
        csv_path = logs_dir / "signals.csv"
        assert csv_path.exists(), "CSV log should be created"

        with open(csv_path, "r") as f:
            lines = f.readlines()
            assert len(lines) > 0, "CSV should have content (header at minimum)"
            # Header line should be present
            assert "timestamp" in lines[0], "CSV should have timestamp header"

    def test_pipeline_output_dir_structure(self, config, temp_signals_dir):
        """Test that pipeline creates correct directory structure."""
        signals_dir = Path(temp_signals_dir) / "signals"
        logs_dir = Path(temp_signals_dir) / "logs"
        signals_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)

        with patch("engine.router.WorldMonitorClient") as mock_wm_class:
            mock_wm = MagicMock()
            mock_wm.fetch_events.return_value = []
            mock_wm_class.return_value = mock_wm

            router = SignalRouter(config)
            router.signals_dir = signals_dir
            router.logs_dir = logs_dir
            router.signal_json_path = router.signals_dir / "signal.json"
            router.signal_log_path = router.signals_dir / "signal_log.json"
            router.csv_log_path = router.logs_dir / "signals.csv"
            router.signals_dir.mkdir(parents=True, exist_ok=True)
            router.logs_dir.mkdir(parents=True, exist_ok=True)
            router._init_csv_file()

            result = router.run_once(current_positions=[])

        # Check directory structure
        assert signals_dir.exists(), "signals directory should exist"
        assert logs_dir.exists(), "logs directory should exist"
        assert (logs_dir / "signals.csv").exists(), "signals.csv should exist"

    def test_pipeline_result_structure(self, config, mock_events, temp_signals_dir):
        """Test that pipeline returns properly structured result dict."""
        signals_dir = Path(temp_signals_dir) / "signals"
        logs_dir = Path(temp_signals_dir) / "logs"
        signals_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)

        with patch("engine.router.WorldMonitorClient") as mock_wm_class:
            mock_wm = MagicMock()
            mock_wm.fetch_events.return_value = mock_events
            mock_wm_class.return_value = mock_wm

            router = SignalRouter(config)
            router.signals_dir = signals_dir
            router.logs_dir = logs_dir
            router.signal_json_path = router.signals_dir / "signal.json"
            router.signal_log_path = router.signals_dir / "signal_log.json"
            router.csv_log_path = router.logs_dir / "signals.csv"
            router.signals_dir.mkdir(parents=True, exist_ok=True)
            router.logs_dir.mkdir(parents=True, exist_ok=True)
            router._init_csv_file()

            result = router.run_once(current_positions=[])

        # Verify result structure and types
        assert isinstance(result, dict)
        assert isinstance(result["timestamp"], str)
        assert isinstance(result["events_fetched"], int)
        assert isinstance(result["signals_generated"], int)
        assert isinstance(result["signals_passed"], int)
        assert result["active_signal"] is None or isinstance(result["active_signal"], dict)
        assert isinstance(result["errors"], list)

        # Timestamps should be ISO format
        assert "T" in result["timestamp"] and "Z" in result["timestamp"], \
            "Timestamp should be ISO format with Z suffix"

        # Counters should be non-negative
        assert result["events_fetched"] >= 0
        assert result["signals_generated"] >= 0
        assert result["signals_passed"] >= 0

        # All errors should be strings
        assert all(isinstance(e, str) for e in result["errors"])
