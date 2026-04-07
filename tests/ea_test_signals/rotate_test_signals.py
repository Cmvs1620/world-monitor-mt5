#!/usr/bin/env python3
"""
EA Test Signal Rotator

Automatically cycles through test signals and copies them to the MT5 Files folder.
This facilitates automated testing of the Expert Advisor's signal reading functionality.

Usage:
    python rotate_test_signals.py --mt5-path "C:\\Users\\Username\\AppData\\Roaming\\MetaTrader 5\\Files"
    python rotate_test_signals.py --mt5-path "C:\\path\\to\\MT5Files" --interval 90
    python rotate_test_signals.py --help

Requirements:
    - Python 3.7+
    - MT5 Files folder accessible and writable
    - All test_signal_*.json files in the same directory as this script
"""

import os
import sys
import json
import time
import shutil
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional


class TestSignalRotator:
    """Manages rotation of test signals to MT5 Files folder."""

    # Test signals in execution order
    TEST_SIGNALS = [
        "test_signal_buy.json",
        "test_signal_sell.json",
        "test_signal_low_confidence.json",
        "test_signal_hold.json",
        "test_signal_duplicate.json",
    ]

    OUTPUT_SIGNAL_NAME = "signal.json"

    def __init__(
        self,
        mt5_path: str,
        interval: int = 60,
        test_signals_dir: Optional[str] = None,
        log_file: Optional[str] = None,
    ):
        """
        Initialize the signal rotator.

        Args:
            mt5_path: Path to MT5 Files folder
            interval: Seconds between signal rotations (default: 60)
            test_signals_dir: Directory containing test signal files (default: current directory)
            log_file: Path to log file (default: rotate_test_signals.log in MT5 path)
        """
        self.mt5_path = Path(mt5_path)
        self.interval = interval
        self.test_signals_dir = (
            Path(test_signals_dir) if test_signals_dir else Path(__file__).parent
        )
        self.log_file = log_file or (self.mt5_path / "rotate_test_signals.log")

        # Setup logging
        self.logger = self._setup_logging()

        # Validate paths
        self._validate_paths()

        self.execution_count = 0
        self.errors = []

    def _setup_logging(self) -> logging.Logger:
        """Setup logging to file and console."""
        logger = logging.getLogger("TestSignalRotator")
        logger.setLevel(logging.DEBUG)

        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def _validate_paths(self) -> None:
        """Validate that required paths exist and are accessible."""
        if not self.mt5_path.exists():
            raise FileNotFoundError(f"MT5 Files path does not exist: {self.mt5_path}")

        if not self.mt5_path.is_dir():
            raise NotADirectoryError(f"MT5 Files path is not a directory: {self.mt5_path}")

        if not os.access(self.mt5_path, os.W_OK):
            raise PermissionError(
                f"MT5 Files path is not writable: {self.mt5_path}\n"
                "Ensure the path is correct and you have write permissions."
            )

        if not self.test_signals_dir.exists():
            raise FileNotFoundError(
                f"Test signals directory does not exist: {self.test_signals_dir}"
            )

        self.logger.info(f"MT5 Files path: {self.mt5_path}")
        self.logger.info(f"Test signals directory: {self.test_signals_dir}")

    def get_test_signals(self) -> List[Path]:
        """
        Get list of test signal files in order.

        Returns:
            List of Path objects for test signal files that exist
        """
        signals = []
        for signal_name in self.TEST_SIGNALS:
            signal_path = self.test_signals_dir / signal_name
            if signal_path.exists():
                signals.append(signal_path)
            else:
                self.logger.warning(f"Test signal file not found: {signal_path}")

        return signals

    def validate_signal_json(self, signal_path: Path) -> bool:
        """
        Validate that a signal file contains valid JSON with required fields.

        Args:
            signal_path: Path to signal file

        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            "timestamp",
            "event_id",
            "event_title",
            "action",
            "symbol",
        ]

        try:
            with open(signal_path, "r") as f:
                signal = json.load(f)

            missing_fields = [f for f in required_fields if f not in signal]
            if missing_fields:
                self.logger.error(
                    f"Signal missing required fields {missing_fields}: {signal_path}"
                )
                return False

            return True

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in signal file {signal_path}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error validating signal {signal_path}: {e}")
            return False

    def copy_signal_to_mt5(self, signal_path: Path) -> bool:
        """
        Copy a test signal to the MT5 Files folder as signal.json.

        Args:
            signal_path: Path to the test signal file

        Returns:
            True if successful, False otherwise
        """
        output_path = self.mt5_path / self.OUTPUT_SIGNAL_NAME

        try:
            # Validate signal before copying
            if not self.validate_signal_json(signal_path):
                self.logger.error(f"Signal validation failed: {signal_path}")
                return False

            # Remove old signal.json if it exists
            if output_path.exists():
                try:
                    output_path.unlink()
                    self.logger.debug(f"Removed previous signal.json")
                except Exception as e:
                    self.logger.warning(
                        f"Could not remove previous signal.json: {e}. Attempting overwrite."
                    )

            # Copy new signal
            shutil.copy2(signal_path, output_path)
            self.logger.info(
                f"Copied {signal_path.name} -> {output_path} "
                f"(next EA poll in ~{self.interval}s)"
            )

            return True

        except Exception as e:
            self.logger.error(f"Error copying signal {signal_path} to {output_path}: {e}")
            self.errors.append(str(e))
            return False

    def rotate_signals(self, num_cycles: Optional[int] = None) -> None:
        """
        Continuously rotate test signals.

        Args:
            num_cycles: Number of cycles to run (None = infinite)
        """
        signals = self.get_test_signals()

        if not signals:
            self.logger.error(
                "No test signals found. Check test_signals_dir and file names."
            )
            return

        self.logger.info(f"Found {len(signals)} test signals to rotate")
        self.logger.info(
            f"Starting rotation with {self.interval}s interval "
            f"({num_cycles} cycles)" if num_cycles else "(infinite cycles)"
        )

        cycle = 0
        signal_index = 0

        try:
            while num_cycles is None or cycle < num_cycles:
                cycle += 1
                self.execution_count += 1

                signal_path = signals[signal_index % len(signals)]

                self.logger.info(
                    f"[Cycle {cycle}] Deploying: {signal_path.name} "
                    f"({signal_index + 1}/{len(signals)})"
                )

                if self.copy_signal_to_mt5(signal_path):
                    signal_index += 1

                # Wait before next rotation (unless it's the last cycle)
                if num_cycles is None or cycle < num_cycles:
                    self.logger.debug(f"Waiting {self.interval}s before next signal...")
                    time.sleep(self.interval)

        except KeyboardInterrupt:
            self.logger.info("\nSignal rotation interrupted by user")
        except Exception as e:
            self.logger.error(f"Unexpected error during rotation: {e}")
            self.errors.append(str(e))
        finally:
            self.print_summary()

    def print_summary(self) -> None:
        """Print execution summary."""
        self.logger.info("=" * 60)
        self.logger.info("ROTATION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total signals deployed: {self.execution_count}")

        if self.errors:
            self.logger.error(f"Errors encountered: {len(self.errors)}")
            for error in self.errors:
                self.logger.error(f"  - {error}")
        else:
            self.logger.info("No errors encountered")

        self.logger.info(f"Log file: {self.log_file}")
        self.logger.info("=" * 60)

    @staticmethod
    def validate_mt5_path(path_str: str) -> Path:
        """Validate and return MT5 path."""
        path = Path(path_str)
        if not path.exists():
            raise argparse.ArgumentTypeError(f"Path does not exist: {path_str}")
        if not path.is_dir():
            raise argparse.ArgumentTypeError(f"Path is not a directory: {path_str}")
        return path


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Rotate test signals for EA integration testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with default 60s interval
  python rotate_test_signals.py --mt5-path "C:\\Users\\Admin\\AppData\\Roaming\\MetaTrader 5\\Files"

  # Custom interval (90 seconds between signals)
  python rotate_test_signals.py --mt5-path "C:\\MT5Files" --interval 90

  # Test mode: run only 5 cycles then exit
  python rotate_test_signals.py --mt5-path "C:\\MT5Files" --cycles 5

  # With custom test signals directory
  python rotate_test_signals.py --mt5-path "C:\\MT5Files" --signals-dir "C:\\custom\\path"
        """,
    )

    parser.add_argument(
        "--mt5-path",
        type=TestSignalRotator.validate_mt5_path,
        required=True,
        help="Path to MT5 Files folder",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Seconds between signal rotations (default: 60)",
    )

    parser.add_argument(
        "--cycles",
        type=int,
        default=None,
        help="Number of cycles to run (default: infinite until Ctrl+C)",
    )

    parser.add_argument(
        "--signals-dir",
        type=str,
        help="Directory containing test signal files (default: script directory)",
    )

    parser.add_argument(
        "--log-file",
        type=str,
        help="Path to log file (default: MT5 Files folder)",
    )

    args = parser.parse_args()

    try:
        rotator = TestSignalRotator(
            mt5_path=str(args.mt5_path),
            interval=args.interval,
            test_signals_dir=args.signals_dir,
            log_file=args.log_file,
        )

        rotator.rotate_signals(num_cycles=args.cycles)

    except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
