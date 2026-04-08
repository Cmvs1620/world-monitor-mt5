#!/usr/bin/env python3
r"""
Risk Gate Test Runner

Automated test execution helper for validating all 5 EA risk gates.
- Generates test signals from JSON definitions
- Copies signals to MT5 Files folder
- Logs test execution and results
- Generates summary report

Usage:
    python run_risk_gate_tests.py --mt5-path "C:\Users\Username\AppData\Roaming\MetaQuotes\Terminal\[ID]\MQL5\Files"

Requirements:
    - Access to MT5 Files folder
    - Test signal JSON files in tests/ea_risk_gates/
    - Python 3.6+
"""

import json
import os
import sys
import shutil
import argparse
import time
from datetime import datetime
from pathlib import Path


class RiskGateTestRunner:
    """Manages test execution for all 5 risk gates."""

    # Test signal file names
    TEST_SCENARIOS = [
        "test_low_confidence.json",
        "test_max_positions.json",
        "test_duplicate_symbol.json",
        "test_daily_loss.json",
        "test_drawdown_limit.json"
    ]

    def __init__(self, mt5_files_path: str):
        """
        Initialize test runner.

        Args:
            mt5_files_path: Path to MT5 Files folder
        """
        self.mt5_files_path = Path(mt5_files_path)
        self.test_dir = Path(__file__).parent
        self.log_file = self.test_dir / "test_execution.log"
        self.results = {}
        self.test_start_time = None

        # Validate MT5 path exists
        if not self.mt5_files_path.exists():
            self._log_error(f"MT5 Files path does not exist: {mt5_files_path}")
            raise FileNotFoundError(f"MT5 path not found: {mt5_files_path}")

        self._log_header("Risk Gate Test Runner Initialized")
        self._log(f"MT5 Files Path: {self.mt5_files_path}")
        self._log(f"Test Directory: {self.test_dir}")

    def _log(self, message: str):
        """Log message to both console and file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        with open(self.log_file, "a") as f:
            f.write(log_message + "\n")

    def _log_error(self, message: str):
        """Log error message."""
        self._log(f"ERROR: {message}")

    def _log_header(self, header: str):
        """Log formatted header."""
        self._log("=" * 60)
        self._log(header)
        self._log("=" * 60)

    def load_test_scenario(self, filename: str) -> dict:
        """
        Load test scenario from JSON file.

        Args:
            filename: Name of test scenario file

        Returns:
            Test scenario dictionary
        """
        test_file = self.test_dir / filename
        if not test_file.exists():
            self._log_error(f"Test file not found: {filename}")
            return {}

        try:
            with open(test_file, "r") as f:
                scenario = json.load(f)
            self._log(f"Loaded test scenario: {scenario.get('test_name', filename)}")
            return scenario
        except json.JSONDecodeError as e:
            self._log_error(f"Invalid JSON in {filename}: {e}")
            return {}

    def generate_signal_json(self, signal: dict) -> str:
        """
        Generate signal.json content from signal dict.

        Args:
            signal: Signal dictionary from test scenario

        Returns:
            JSON string formatted for EA
        """
        # Extract only fields needed by EA
        ea_signal = {
            "timestamp": signal.get("timestamp", ""),
            "event_id": signal.get("event_id", ""),
            "event_title": signal.get("event_title", ""),
            "action": signal.get("action", "HOLD"),
            "symbol": signal.get("symbol", ""),
            "confidence": signal.get("confidence", 0.5),
            "volume": signal.get("volume", 1.0),
            "stop_loss": signal.get("stop_loss", 0.0),
            "take_profit": signal.get("take_profit", 0.0),
            "rationale": signal.get("rationale", "")
        }
        return json.dumps(ea_signal, indent=2)

    def copy_signal_to_mt5(self, signal: dict, sequence_num: int = None) -> bool:
        """
        Copy signal to MT5 signal.json file.

        Args:
            signal: Signal dictionary
            sequence_num: Optional sequence number for logging

        Returns:
            True if successful, False otherwise
        """
        try:
            signal_json = self.generate_signal_json(signal)
            signal_file = self.mt5_files_path / "signal.json"

            with open(signal_file, "w") as f:
                f.write(signal_json)

            seq_str = f"[{sequence_num}] " if sequence_num else ""
            self._log(f"{seq_str}Signal copied to MT5: {signal.get('event_id', 'unknown')}")
            return True
        except Exception as e:
            self._log_error(f"Failed to copy signal: {e}")
            return False

    def read_ea_log(self) -> list:
        """
        Read EA execution log from MT5 Files folder.

        Returns:
            List of recent log lines
        """
        log_file = self.mt5_files_path / "ea_execution.log"
        if not log_file.exists():
            return []

        try:
            with open(log_file, "r") as f:
                lines = f.readlines()
            # Return last 20 lines
            return lines[-20:] if lines else []
        except Exception as e:
            self._log_error(f"Failed to read EA log: {e}")
            return []

    def check_signal_execution(self, expected_log_keyword: str = None) -> bool:
        """
        Check if signal was processed by EA.

        Args:
            expected_log_keyword: Keyword to search for in log

        Returns:
            True if execution detected, False otherwise
        """
        log_lines = self.read_ea_log()
        if not log_lines:
            self._log("  ⚠ EA log not found - cannot verify execution")
            return False

        log_text = "".join(log_lines)

        if expected_log_keyword:
            found = expected_log_keyword.lower() in log_text.lower()
            if found:
                self._log(f"  ✓ Expected log message found: '{expected_log_keyword}'")
            else:
                self._log(f"  ✗ Expected log message NOT found: '{expected_log_keyword}'")
            return found
        else:
            return len(log_lines) > 0

    def run_test_scenario(self, filename: str) -> dict:
        """
        Execute complete test scenario.

        Args:
            filename: Test scenario file name

        Returns:
            Test result dictionary
        """
        self._log_header(f"Running Test Scenario: {filename}")

        scenario = self.load_test_scenario(filename)
        if not scenario:
            return {"passed": False, "reason": "Failed to load test scenario"}

        test_name = scenario.get("test_name", filename)
        risk_gate = scenario.get("risk_gate", "Unknown")
        signals = scenario.get("signals", [])

        self._log(f"Test Name: {test_name}")
        self._log(f"Risk Gate: {risk_gate}")
        self._log(f"Number of Signals: {len(signals)}")

        passed_count = 0
        failed_count = 0

        for i, signal in enumerate(signals, 1):
            sequence = signal.get("sequence", i)
            action = signal.get("action", "HOLD")
            symbol = signal.get("symbol", "??")
            expected = signal.get("expected_outcome", "")
            expected_log = signal.get("expected_log_message", "")

            self._log(f"\n  Signal {sequence}: {action} {symbol}")
            self._log(f"    Expected: {expected}")

            # Copy signal to MT5
            if not self.copy_signal_to_mt5(signal, sequence):
                self._log(f"    Result: FAILED (could not copy signal)")
                failed_count += 1
                continue

            # Wait for EA to process signal
            self._log(f"    Waiting for EA to process (10 seconds)...")
            time.sleep(10)

            # Check if signal was processed
            if self.check_signal_execution(expected_log):
                self._log(f"    Result: PASSED")
                passed_count += 1
            else:
                self._log(f"    Result: INCONCLUSIVE (check log manually)")
                failed_count += 1

            # Brief wait between signals
            if i < len(signals):
                time.sleep(5)

        # Summarize test scenario
        self._log(f"\n  Scenario Results: {passed_count} passed, {failed_count} inconclusive")

        return {
            "scenario": test_name,
            "risk_gate": risk_gate,
            "passed": passed_count,
            "inconclusive": failed_count,
            "total": len(signals)
        }

    def run_all_tests(self, skip_scenarios: list = None) -> dict:
        """
        Run all test scenarios.

        Args:
            skip_scenarios: List of scenario files to skip

        Returns:
            Summary of all test results
        """
        self.test_start_time = datetime.now()
        self._log_header("Starting All Risk Gate Tests")
        self._log(f"Start Time: {self.test_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self._log(f"MT5 Files Path: {self.mt5_files_path}")

        skip_scenarios = skip_scenarios or []
        all_results = []

        for scenario_file in self.TEST_SCENARIOS:
            if scenario_file in skip_scenarios:
                self._log(f"Skipping: {scenario_file}")
                continue

            result = self.run_test_scenario(scenario_file)
            all_results.append(result)
            time.sleep(2)  # Brief pause between scenarios

        # Generate final report
        self._generate_summary_report(all_results)
        return {"tests": all_results}

    def _generate_summary_report(self, results: list):
        """
        Generate summary report of all tests.

        Args:
            results: List of test results
        """
        self._log_header("TEST EXECUTION SUMMARY")

        total_scenarios = len(results)
        total_signals = sum(r.get("total", 0) for r in results)
        total_passed = sum(r.get("passed", 0) for r in results)
        total_inconclusive = sum(r.get("inconclusive", 0) for r in results)

        # Results table
        self._log("\nRisk Gate Test Results:")
        self._log("-" * 80)
        self._log(f"{'Risk Gate':<40} {'Passed':<10} {'Status':<15}")
        self._log("-" * 80)

        for result in results:
            gate = result.get("risk_gate", "Unknown")[:38]
            passed = result.get("passed", 0)
            total = result.get("total", 0)
            status = "PASS" if result.get("inconclusive", 0) == 0 and passed == total else "REVIEW"
            self._log(f"{gate:<40} {passed}/{total:<8} {status:<15}")

        self._log("-" * 80)

        # Overall summary
        self._log(f"\nTotal Scenarios: {total_scenarios}")
        self._log(f"Total Signals Tested: {total_signals}")
        self._log(f"Total Passed: {total_passed}")
        self._log(f"Total Inconclusive: {total_inconclusive}")

        end_time = datetime.now()
        duration = (end_time - self.test_start_time).total_seconds()

        self._log(f"\nEnd Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self._log(f"Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")

        # Next steps
        self._log("\nNext Steps:")
        self._log("1. Review test execution log above")
        self._log("2. Check ea_execution.log in MT5 Files folder for detailed results")
        self._log("3. Fill out VALIDATION_CHECKLIST.md with manual verification results")
        self._log("4. Cross-reference logs with EXPECTED_LOG_OUTPUTS.md")
        self._log(f"5. Log file saved to: {self.log_file}")

        self._log_header("Test Execution Complete")

    def interactive_mode(self):
        """
        Interactive test execution mode.

        Allows user to run tests one at a time with manual verification.
        """
        self._log_header("Interactive Test Mode")

        while True:
            self._log("\nAvailable Test Scenarios:")
            for i, scenario in enumerate(self.TEST_SCENARIOS, 1):
                self._log(f"  {i}. {scenario}")
            self._log("  0. Run all tests")
            self._log("  Q. Quit")

            choice = input("\nSelect scenario number: ").strip().upper()

            if choice == "Q":
                break
            elif choice == "0":
                self.run_all_tests()
            else:
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(self.TEST_SCENARIOS):
                        self.run_test_scenario(self.TEST_SCENARIOS[idx])
                    else:
                        self._log("Invalid selection")
                except ValueError:
                    self._log("Invalid input")

        self._log("Interactive mode ended")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Risk Gate Test Runner for GeoSignal EA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python run_risk_gate_tests.py --mt5-path "C:\\Users\\User\\AppData\\Roaming\\MetaQuotes\\Terminal\\[ID]\\MQL5\\Files"

  # Run specific scenario
  python run_risk_gate_tests.py --mt5-path "..." --scenario test_low_confidence.json

  # Interactive mode
  python run_risk_gate_tests.py --mt5-path "..." --interactive

  # Windows example with proper escaping
  python run_risk_gate_tests.py --mt5-path "C:\\Users\\YourName\\AppData\\Roaming\\MetaQuotes\\Terminal\\D0E8209F77C8CF37AD8BF550E51FF0B2\\MQL5\\Files"
        """
    )

    parser.add_argument(
        "--mt5-path",
        required=True,
        help="Path to MT5 Files folder"
    )
    parser.add_argument(
        "--scenario",
        help="Run specific scenario file"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode (select tests one at a time)"
    )
    parser.add_argument(
        "--skip",
        nargs="+",
        help="Skip specific scenario files"
    )

    args = parser.parse_args()

    try:
        runner = RiskGateTestRunner(args.mt5_path)

        if args.interactive:
            runner.interactive_mode()
        elif args.scenario:
            runner.run_test_scenario(args.scenario)
        else:
            runner.run_all_tests(skip_scenarios=args.skip)

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
