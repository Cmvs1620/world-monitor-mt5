#!/usr/bin/env python3
"""
Main Integration Test Orchestrator

Runs complete end-to-end integration test with monitoring and reporting.

Usage:
    python run_integration_test.py --duration 600 --mt5-path "C:\path\to\MT5\Files" --verbose

Arguments:
    --duration      Test duration in seconds (default: 900 = 15 minutes)
    --mt5-path      Path to MT5 Files folder for sync (required)
    --verbose       Enable verbose output
    --no-sync       Skip automated sync, assume manual copy
    --log-file      Output log file (default: logs/integration_test.log)
"""

import os
import sys
import time
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
import threading


class IntegrationTestOrchestrator:
    """Orchestrates end-to-end integration test"""

    def __init__(self, duration=900, mt5_path=None, verbose=False, enable_sync=True, log_file="logs/integration_test.log"):
        self.duration = duration
        self.mt5_path = mt5_path
        self.verbose = verbose
        self.enable_sync = enable_sync
        self.log_file = Path(log_file)
        self.start_time = None
        self.end_time = None

        self.signal_file = Path("signals/signal.json")
        self.heartbeat_file = Path("signals/heartbeat.json")

        self.signals_generated = 0
        self.signals_executed = 0
        self.errors = []

        # Create log directory
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        self._log("Integration Test Orchestrator initialized")
        self._log(f"  Duration: {duration} seconds ({duration/60:.1f} minutes)")
        self._log(f"  MT5 path: {mt5_path}")
        self._log(f"  Auto-sync: {enable_sync}")

    def _log(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"

        if self.verbose or "ERROR" in message:
            print(log_msg)

        with open(self.log_file, "a") as f:
            f.write(log_msg + "\n")

    def validate_environment(self):
        """Check prerequisites"""
        self._log("Validating environment...")

        checks = {
            "Python engine available": Path("run.py").exists(),
            "signal.json writable": Path("signals").exists(),
            "logs directory exists": Path("logs").exists(),
            "MT5 path provided": self.mt5_path is not None,
            "MT5 path accessible": Path(self.mt5_path).exists() if self.mt5_path else False,
        }

        passed = sum(1 for v in checks.values() if v)
        total = len(checks)

        for check, result in checks.items():
            status = "✓" if result else "✗"
            self._log(f"  {status} {check}")

        if passed == total:
            self._log(f"Environment validation: PASS ({passed}/{total})")
            return True
        else:
            self._log(f"Environment validation: FAIL ({passed}/{total})")
            return False

    def monitor_signal_updates(self):
        """Monitor signal.json for updates"""
        self._log("Starting signal update monitor...")
        last_hash = None

        while time.time() < self.end_time:
            try:
                if self.signal_file.exists():
                    with open(self.signal_file, "r") as f:
                        data = json.load(f)

                    current_hash = hash(json.dumps(data, sort_keys=True))
                    if current_hash != last_hash:
                        signal_count = len(data.get("signals", []))
                        self.signals_generated = signal_count
                        self._log(f"Signal update detected: {signal_count} signal(s)")
                        last_hash = current_hash

                time.sleep(5)
            except Exception as e:
                self._log(f"ERROR: Monitor failed: {e}")

    def monitor_heartbeat_updates(self):
        """Monitor heartbeat.json for updates"""
        self._log("Starting heartbeat monitor...")
        last_update = 0

        while time.time() < self.end_time:
            try:
                if self.heartbeat_file.exists():
                    mtime = self.heartbeat_file.stat().st_mtime
                    if mtime > last_update:
                        with open(self.heartbeat_file, "r") as f:
                            hb = json.load(f)

                        if hb.get("executed"):
                            self.signals_executed += 1
                            self._log(f"Heartbeat received: ticket={hb.get('ticket')}, status={hb.get('status')}")

                        last_update = mtime

                time.sleep(5)
            except Exception as e:
                if self.verbose:
                    self._log(f"WARNING: Heartbeat monitor error: {e}")

    def run_sync_script(self):
        """Run signal sync script in background"""
        if not self.enable_sync or not self.mt5_path:
            return

        self._log("Starting signal sync script...")

        try:
            cmd = [
                "python",
                "tests/ea_python_integration/sync_signal_to_mt5.py",
                "--mt5-path",
                str(self.mt5_path),
                "--watch",
                "10",
                "--verbose" if self.verbose else "",
            ]

            # Remove empty strings
            cmd = [c for c in cmd if c]

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self._log(f"Sync script started (PID: {process.pid})")

            # Let it run in background
            return process

        except Exception as e:
            self._log(f"ERROR: Failed to start sync script: {e}")
            self.errors.append(f"Sync script failed: {e}")
            return None

    def wait_for_python_engine(self):
        """Wait for Python engine to start"""
        self._log("Waiting for Python engine to become ready...")

        for i in range(30):  # Wait up to 30 seconds
            if self.signal_file.exists():
                try:
                    with open(self.signal_file, "r") as f:
                        json.load(f)
                    self._log("Python engine is ready (signal.json valid)")
                    return True
                except:
                    pass

            time.sleep(1)

        self._log("ERROR: Python engine did not start in time")
        self.errors.append("Python engine startup timeout")
        return False

    def run(self):
        """Run complete integration test"""
        self.start_time = time.time()
        self.end_time = self.start_time + self.duration

        print("\n" + "="*80)
        print("INTEGRATION TEST STARTING")
        print("="*80)
        self._log("Test started")

        # Validate environment
        if not self.validate_environment():
            self._log("Environment validation failed, aborting test")
            return False

        # Start sync script (background)
        sync_process = self.run_sync_script()

        # Wait for Python engine
        if not self.wait_for_python_engine():
            return False

        # Start monitoring threads
        monitor_signals = threading.Thread(target=self.monitor_signal_updates, daemon=True)
        monitor_heartbeat = threading.Thread(target=self.monitor_heartbeat_updates, daemon=True)

        monitor_signals.start()
        monitor_heartbeat.start()

        self._log(f"Test running for {self.duration} seconds...")
        print(f"\nTest running... Press Ctrl+C to stop early")

        # Run test loop
        try:
            while time.time() < self.end_time:
                elapsed = time.time() - self.start_time
                remaining = self.end_time - time.time()

                if int(elapsed) % 60 == 0 and elapsed > 0:  # Log every minute
                    self._log(f"Test progress: {elapsed:.0f}s elapsed, {remaining:.0f}s remaining")
                    self._log(f"  Signals generated: {self.signals_generated}")
                    self._log(f"  Signals executed: {self.signals_executed}")

                time.sleep(1)

        except KeyboardInterrupt:
            self._log("Test interrupted by user")

        finally:
            # Stop sync process
            if sync_process:
                sync_process.terminate()
                self._log("Sync script stopped")

            self.end_time = time.time()

        # Print summary
        self.print_summary()

        return len(self.errors) == 0

    def print_summary(self):
        """Print test summary"""
        duration = self.end_time - self.start_time
        minutes = duration / 60

        print("\n" + "="*80)
        print("INTEGRATION TEST SUMMARY")
        print("="*80)

        print(f"Duration:           {duration:.0f} seconds ({minutes:.1f} minutes)")
        print(f"Signals generated:  {self.signals_generated}")
        print(f"Signals executed:   {self.signals_executed}")
        if self.signals_generated > 0:
            exec_ratio = 100 * self.signals_executed / self.signals_generated
            print(f"Execution ratio:    {exec_ratio:.1f}%")

        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")
            print(f"\nStatus: FAIL ✗")
        else:
            print(f"\nStatus: PASS ✓")

        print(f"\nLog file: {self.log_file}")
        print("="*80 + "\n")

        self._log("Test completed")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run end-to-end integration test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run 10-minute test with auto-sync:
  python run_integration_test.py --duration 600 --mt5-path "/Volumes/Stratos/.../MQL5/Files" --verbose

  # Run 15-minute test without auto-sync:
  python run_integration_test.py --duration 900 --mt5-path "/Volumes/Stratos/.../MQL5/Files" --no-sync

  # Run quick 5-minute test:
  python run_integration_test.py --duration 300 --mt5-path "/Volumes/Stratos/.../MQL5/Files"
        """
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=900,
        help="Test duration in seconds (default: 900 = 15 minutes)"
    )
    parser.add_argument(
        "--mt5-path",
        required=True,
        help="Path to MT5 Files folder (required)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--no-sync",
        action="store_true",
        help="Skip automated sync (assume manual copy)"
    )
    parser.add_argument(
        "--log-file",
        default="logs/integration_test.log",
        help="Output log file"
    )

    args = parser.parse_args()

    # Create orchestrator
    orchestrator = IntegrationTestOrchestrator(
        duration=args.duration,
        mt5_path=args.mt5_path,
        verbose=args.verbose,
        enable_sync=not args.no_sync,
        log_file=args.log_file
    )

    # Run test
    success = orchestrator.run()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
