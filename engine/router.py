"""Signal Router Orchestrator - Orchestrates the complete signal pipeline."""

import json
import logging
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from engine.worldmonitor import WorldMonitorClient
from engine.classifier import EventClassifier
from engine.risk_gate import RiskGate

logger = logging.getLogger(__name__)


class SignalRouter:
    """
    Orchestrates the complete signal pipeline: fetch → classify → validate → write outputs.

    Pipeline flow:
    1. Fetch new events from WorldMonitor
    2. For each event:
       a. Classify with Claude
       b. Validate against risk rules
       c. If passes: write to signal.json and logs
       d. If blocked: log to signal_log.json with status "blocked"
    3. Return results dict

    Outputs:
    - signals/signal.json: Current active trade signal (Python → EA reads)
    - signals/signal_log.json: Append-only archive of all signals
    - logs/signals.csv: CSV log of all signals (fired + skipped)
    """

    def __init__(self, config: Dict):
        """
        Initialize SignalRouter with config dict.

        Args:
            config (dict): Configuration dict with keys:
                - account_balance (float): Total account balance in USD
                - max_concurrent_positions (int): Maximum open trades
                - risk_per_trade_percent (float): Max risk per trade (e.g., 1.0 for 1%)
                - mt5_files_path (str): Path to MT5 Files folder
                - debug (bool): Debug mode enabled
                - max_drawdown_percent (float, optional): Max drawdown % (default: 5.0)
        """
        self.config = config
        self.debug = config.get("debug", False)

        # Initialize components
        self.worldmonitor = WorldMonitorClient()
        self.classifier = EventClassifier()

        # Add max_drawdown_percent to config if missing
        if "max_drawdown_percent" not in config:
            config["max_drawdown_percent"] = 5.0

        self.risk_gate = RiskGate(config)

        # Setup paths
        self.signals_dir = Path("signals")
        self.logs_dir = Path("logs")
        self.signal_json_path = self.signals_dir / "signal.json"
        self.signal_log_path = self.signals_dir / "signal_log.json"
        self.csv_log_path = self.logs_dir / "signals.csv"

        # Ensure directories exist
        self.signals_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Initialize CSV file if it doesn't exist
        self._init_csv_file()

        logger.info("SignalRouter initialized")

    def _init_csv_file(self) -> None:
        """Initialize CSV file with headers if it doesn't exist."""
        if not self.csv_log_path.exists():
            with open(self.csv_log_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "event_id",
                    "classification",
                    "confidence",
                    "symbol",
                    "action",
                    "volume",
                    "rationale",
                    "status",
                ])
            logger.debug(f"Created CSV file at {self.csv_log_path}")

    def run_once(self, current_positions: Optional[List[Dict]] = None) -> Dict:
        """
        Run one complete pipeline iteration.

        Flow:
        1. Fetch new events from WorldMonitor
        2. For each event:
           a. Classify with Claude
           b. Validate against risk rules
           c. If passes: write to signal.json and append to logs
           d. If blocked: log to signal_log.json with status "blocked"
        3. Return results dict

        Args:
            current_positions (list, optional): List of dicts with "symbol" and "volume" keys.
                If None, defaults to empty list.

        Returns:
            dict: Results with keys:
                - timestamp (str): ISO format timestamp
                - events_fetched (int): Number of events fetched
                - signals_generated (int): Number of signals generated (classified)
                - signals_passed (int): Number of signals that passed validation
                - active_signal (dict): First passed signal (or None if no passes)
                - errors (list): List of error strings
        """
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        current_positions = current_positions or []
        errors = []

        try:
            # Step 1: Fetch new events
            events = self.worldmonitor.fetch_events(limit=10, skip_cache=False)
            logger.info(f"Fetched {len(events)} new events")

            signals_generated = 0
            signals_passed = 0
            active_signal = None

            # Step 2: Process each event
            for event in events:
                try:
                    # 2a: Classify
                    signal = self.classifier.classify(event)
                    signals_generated += 1

                    # Enrich signal with event data
                    enriched_signal = {
                        "event_id": event.get("id", ""),
                        "event_title": event.get("title", ""),
                        **signal,
                    }

                    # 2b: Validate
                    validation = self.risk_gate.validate(
                        enriched_signal, current_positions
                    )

                    # 2c & 2d: Write outputs based on validation result
                    if validation["allowed"]:
                        # Signal passed validation
                        signals_passed += 1
                        enriched_signal["volume"] = validation["volume"]

                        # Set as active signal if it's the first one
                        if active_signal is None:
                            active_signal = enriched_signal

                        # Write to signal.json
                        self._write_signal(enriched_signal, timestamp)

                        # Log to signal_log.json and CSV with "passed" status
                        self._log_signal(
                            event, enriched_signal, "passed"
                        )

                        logger.info(
                            f"Signal passed: {enriched_signal.get('symbol')} "
                            f"{enriched_signal.get('action')} "
                            f"(confidence: {enriched_signal.get('confidence'):.2f})"
                        )
                    else:
                        # Signal blocked by risk gate
                        logger.info(
                            f"Signal blocked: {validation['reason']}"
                        )

                        # Log to signal_log.json and CSV with "blocked" status
                        self._log_signal(
                            event, enriched_signal, "blocked", validation["reason"]
                        )

                except Exception as e:
                    error_msg = f"Error processing event {event.get('id', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            return {
                "timestamp": timestamp,
                "events_fetched": len(events),
                "signals_generated": signals_generated,
                "signals_passed": signals_passed,
                "active_signal": active_signal,
                "errors": errors,
            }

        except Exception as e:
            error_msg = f"Fatal error in pipeline: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

            return {
                "timestamp": timestamp,
                "events_fetched": 0,
                "signals_generated": 0,
                "signals_passed": 0,
                "active_signal": None,
                "errors": errors,
            }

    def _write_signal(self, signal: Dict, timestamp: str) -> None:
        """
        Write current active signal to signal.json for IPC with EA.

        File format:
        {
            "timestamp": "2026-04-07T10:00:00Z",
            "event_id": "evt-123",
            "event_title": "...",
            "action": "BUY" | "SELL" | "HOLD",
            "symbol": "EURUSD",
            "confidence": 0.75,
            "volume": 1.0,
            "stop_loss": 1.0850,
            "take_profit": 1.1100,
            "rationale": "..."
        }

        Args:
            signal (dict): Signal dict with action, symbol, confidence, volume, rationale, etc.
            timestamp (str): ISO format timestamp
        """
        try:
            # Prepare output signal
            output = {
                "timestamp": timestamp,
                "event_id": signal.get("event_id", ""),
                "event_title": signal.get("event_title", ""),
                "action": signal.get("action", "HOLD"),
                "symbol": signal.get("symbol", ""),
                "confidence": signal.get("confidence", 0.0),
                "volume": signal.get("volume", 0.0),
                "stop_loss": 0.0,  # Placeholder for future TP/SL calculation
                "take_profit": 0.0,  # Placeholder for future TP/SL calculation
                "rationale": signal.get("rationale", ""),
            }

            # Write to signal.json with pretty formatting for readability
            with open(self.signal_json_path, "w") as f:
                json.dump(output, f, indent=2)

            logger.debug(f"Wrote signal to {self.signal_json_path}")

        except Exception as e:
            logger.error(f"Failed to write signal.json: {e}")
            raise

    def _log_signal(
        self,
        event: Dict,
        signal: Dict,
        status: str,
        block_reason: Optional[str] = None,
    ) -> None:
        """
        Log signal to JSON archive and CSV file.

        Appends to signal_log.json (JSON array) and logs row to signals.csv.

        Args:
            event (dict): Original event from WorldMonitor
            signal (dict): Classification signal from Claude
            status (str): "passed" or "blocked"
            block_reason (str, optional): Reason for blocking (if status="blocked")
        """
        try:
            timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

            # Prepare JSON log entry
            json_entry = {
                "timestamp": timestamp,
                "event_id": event.get("id", ""),
                "event_title": event.get("title", ""),
                "event_severity": event.get("severity", ""),
                "action": signal.get("action", ""),
                "symbol": signal.get("symbol", ""),
                "confidence": signal.get("confidence", 0.0),
                "volume": signal.get("volume", 0.0),
                "rationale": signal.get("rationale", ""),
                "status": status,
            }

            if block_reason:
                json_entry["block_reason"] = block_reason

            # Append to signal_log.json
            self._append_json_log(json_entry)

            # Append to CSV
            self._append_csv_log(
                timestamp,
                event.get("id", ""),
                "classified",
                signal.get("confidence", 0.0),
                signal.get("symbol", ""),
                signal.get("action", ""),
                signal.get("volume", 0.0),
                signal.get("rationale", ""),
                status,
            )

        except Exception as e:
            logger.error(f"Failed to log signal: {e}")
            raise

    def _append_json_log(self, entry: Dict) -> None:
        """
        Append entry to signal_log.json (JSON array).

        Args:
            entry (dict): Log entry to append
        """
        try:
            # Read existing log or start with empty list
            if self.signal_log_path.exists():
                with open(self.signal_log_path, "r") as f:
                    log = json.load(f)
            else:
                log = []

            # Append new entry
            log.append(entry)

            # Write back to file
            with open(self.signal_log_path, "w") as f:
                json.dump(log, f, indent=2)

            logger.debug(f"Appended signal to {self.signal_log_path}")

        except Exception as e:
            logger.error(f"Failed to append JSON log: {e}")
            raise

    def _append_csv_log(
        self,
        timestamp: str,
        event_id: str,
        classification: str,
        confidence: float,
        symbol: str,
        action: str,
        volume: float,
        rationale: str,
        status: str,
    ) -> None:
        """
        Append row to signals.csv.

        Args:
            timestamp (str): ISO format timestamp
            event_id (str): Event ID
            classification (str): Classification type (e.g., "classified")
            confidence (float): Signal confidence
            symbol (str): Trading symbol
            action (str): Action (BUY/SELL/HOLD)
            volume (float): Position volume
            rationale (str): Signal rationale
            status (str): "passed" or "blocked"
        """
        try:
            with open(self.csv_log_path, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp,
                    event_id,
                    classification,
                    f"{confidence:.4f}",
                    symbol,
                    action,
                    f"{volume:.4f}",
                    rationale,
                    status,
                ])

            logger.debug(f"Appended row to {self.csv_log_path}")

        except Exception as e:
            logger.error(f"Failed to append CSV log: {e}")
            raise
