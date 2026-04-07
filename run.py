#!/usr/bin/env python3
"""
MT5 GeoSignal Expert Advisor - Main Entry Point
Starts the signal engine loop that continuously polls WorldMonitor for events and generates signals.

Usage:
    python run.py

This is the command users run to start the entire system. The engine will:
1. Load configuration from config/settings.json
2. Initialize the signal pipeline (WorldMonitor → Classifier → RiskGate → SignalRouter)
3. Poll WorldMonitor every N seconds (configurable)
4. Generate trading signals and write them to signals/signal.json for MT5 EA consumption
5. Log all activities to console and files

Exit with Ctrl+C (graceful KeyboardInterrupt handling)
"""

import json
import logging
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

from engine.router import SignalRouter


# ============================================================================
# Logging Setup
# ============================================================================

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Setup logging with both console and file handlers.

    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        logging.Logger: Configured logger instance
    """
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level))

    # Format string: timestamp - logger name - level - message
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (logs/engine.log)
    file_handler = logging.FileHandler(logs_dir / "engine.log")
    file_handler.setLevel(getattr(logging, log_level))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# ============================================================================
# Configuration Loading
# ============================================================================

def load_config() -> Dict:
    """
    Load configuration from config/settings.json.

    Returns:
        dict: Configuration dictionary with keys like:
            - debug (bool): Debug mode enabled
            - worldmonitor_poll_interval_seconds (int): Poll interval in seconds
            - account_balance (float): Total account balance in USD
            - max_concurrent_positions (int): Maximum open trades
            - risk_per_trade_percent (float): Max risk per trade (e.g., 1.0 for 1%)
            - mt5_files_path (str): Path to MT5 Files folder
            - log_level (str): Logging level (default: "INFO")
            - telegram_enabled (bool): Whether Telegram alerts are enabled
            - signal_expiry_seconds (int): How long signals stay active

    Raises:
        FileNotFoundError: If config/settings.json doesn't exist
        json.JSONDecodeError: If config file has invalid JSON
    """
    config_path = Path("config/settings.json")

    if not config_path.exists():
        print(f"ERROR: Configuration file not found: {config_path}")
        print(f"Expected path: {config_path.resolve()}")
        sys.exit(1)

    try:
        with open(config_path, "r") as f:
            config = json.load(f)

        # Validate required fields
        required_fields = [
            "debug",
            "worldmonitor_poll_interval_seconds",
            "risk_per_trade_percent",
            "max_concurrent_positions",
            "mt5_files_path",
        ]

        missing_fields = [field for field in required_fields if field not in config]
        if missing_fields:
            print(f"ERROR: Missing required config fields: {', '.join(missing_fields)}")
            sys.exit(1)

        # Set default account_balance if not provided
        if "account_balance" not in config:
            config["account_balance"] = 10000.0

        # Set default log_level if not provided
        if "log_level" not in config:
            config["log_level"] = "INFO"

        return config

    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in config file: {e}")
        sys.exit(1)


# ============================================================================
# Current Positions Placeholder
# ============================================================================

def get_current_positions() -> List[Dict]:
    """
    Get current open positions from MT5.

    Phase 1 placeholder: Returns empty list.
    Phase 2 will integrate with MT5 via the MetaTrader5 Python library.

    Returns:
        list: List of dicts with keys: symbol (str), volume (float)
              Example: [{"symbol": "EURUSD", "volume": 1.0}, ...]
              Empty list in Phase 1.
    """
    # Phase 1: No MT5 integration yet
    # Phase 2 will implement: MT5Manager.get_open_positions()
    return []


# ============================================================================
# Main Loop
# ============================================================================

def main() -> None:
    """
    Main entry point for the signal engine.

    Flow:
    1. Load .env file (API keys, credentials)
    2. Setup logging (console + file)
    3. Load configuration from config/settings.json
    4. Initialize SignalRouter
    5. Start main polling loop:
       a. Poll WorldMonitor every poll_interval seconds
       b. Classify events and validate signals
       c. Log results to console and files
       d. Write active signal to signals/signal.json for MT5 EA
       e. Handle errors gracefully
    6. On KeyboardInterrupt (Ctrl+C): Gracefully shutdown
    """

    # Step 1: Load .env file
    load_dotenv()

    # Step 2: Setup logging
    logger = setup_logging("INFO")
    logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("MT5 GeoSignal Engine Started")
    logger.info("=" * 80)

    # Step 3: Load configuration
    logger.info("Loading configuration from config/settings.json...")
    try:
        config = load_config()
        logger.info(f"Configuration loaded successfully")
        logger.debug(f"Config: {json.dumps(config, indent=2)}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Step 4: Initialize SignalRouter
    logger.info("Initializing SignalRouter...")
    try:
        router = SignalRouter(config)
        logger.info("SignalRouter initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize SignalRouter: {e}")
        sys.exit(1)

    # Extract configuration
    poll_interval = config.get("worldmonitor_poll_interval_seconds", 300)
    debug = config.get("debug", False)

    logger.info(f"Starting signal loop (poll interval: {poll_interval}s, debug: {debug})")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 80)

    # Step 5: Main polling loop
    iteration = 0
    consecutive_errors = 0
    max_consecutive_errors = 3

    try:
        while True:
            iteration += 1
            loop_start_time = time.time()

            try:
                logger.info(f"\n[Iteration {iteration}] Starting signal pipeline...")

                # Get current positions (Phase 1: empty, Phase 2: from MT5)
                current_positions = get_current_positions()

                # Run one complete pipeline iteration
                result = router.run_once(current_positions)

                # Extract results
                timestamp = result.get("timestamp", "")
                events_fetched = result.get("events_fetched", 0)
                signals_generated = result.get("signals_generated", 0)
                signals_passed = result.get("signals_passed", 0)
                active_signal = result.get("active_signal")
                errors = result.get("errors", [])

                # Log pipeline results
                logger.info(
                    f"Pipeline: {events_fetched} events, "
                    f"{signals_generated} signals, "
                    f"{signals_passed} passed"
                )

                # Log active signal if one was generated
                if active_signal:
                    symbol = active_signal.get("symbol", "???")
                    action = active_signal.get("action", "HOLD")
                    confidence = active_signal.get("confidence", 0.0)
                    logger.info(
                        f"✓ ACTIVE SIGNAL: {action} {symbol} (confidence: {confidence:.2f})"
                    )
                else:
                    logger.info("No signals passed validation in this iteration")

                # Log any errors
                if errors:
                    logger.warning(f"Pipeline encountered {len(errors)} error(s):")
                    for error in errors:
                        logger.warning(f"  - {error}")

                # Reset error counter on successful iteration
                consecutive_errors = 0

            except Exception as e:
                consecutive_errors += 1
                error_msg = f"Error in pipeline iteration {iteration}: {str(e)}"
                logger.error(error_msg)

                if consecutive_errors >= max_consecutive_errors:
                    logger.critical(
                        f"Too many consecutive errors ({consecutive_errors}). "
                        f"Stopping engine."
                    )
                    sys.exit(1)

                # Wait before retrying (min of poll_interval and 60 seconds)
                retry_wait = min(poll_interval, 60)
                logger.info(f"Retrying in {retry_wait}s...")
                time.sleep(retry_wait)
                continue

            # Calculate sleep time
            elapsed = time.time() - loop_start_time
            sleep_time = max(0, poll_interval - elapsed)

            if sleep_time > 0:
                logger.info(f"Sleeping {sleep_time:.1f}s until next poll...")
                time.sleep(sleep_time)
            else:
                logger.warning(
                    f"Pipeline iteration took {elapsed:.1f}s, longer than poll interval "
                    f"{poll_interval}s. Starting next iteration immediately."
                )

    except KeyboardInterrupt:
        logger.info("\n" + "=" * 80)
        logger.info("Interrupted by user (Ctrl+C)")
        logger.info("=" * 80)
        logger.info("Signal engine stopped gracefully")
        sys.exit(0)

    except Exception as e:
        logger.critical(f"Unexpected error in main loop: {e}")
        logger.exception(e)
        sys.exit(1)


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    main()
