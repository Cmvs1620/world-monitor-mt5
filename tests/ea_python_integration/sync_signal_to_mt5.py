#!/usr/bin/env python3
"""
Automated Signal File Sync Utility

Monitors signals/signal.json for changes and automatically syncs to MT5 Files folder
on Stratos Windows via SMB mount. Logs every operation with timestamp and event_ids.

Usage:
    python sync_signal_to_mt5.py --mt5-path "/Volumes/Stratos/.../MQL5/Files" --watch 300 --verbose

Arguments:
    --mt5-path      Path to MT5 Files folder (mounted SMB share)
    --watch         Polling interval in seconds (default: 10)
    --verbose       Enable verbose logging (default: False)
    --log-file      Output log file (default: logs/sync.log)
"""

import os
import sys
import json
import time
import argparse
import hashlib
from datetime import datetime
from pathlib import Path
import shutil


class SignalSyncManager:
    """Manages signal.json sync to MT5 Files folder"""

    def __init__(self, mt5_path, watch_interval=10, verbose=False, log_file="logs/sync.log"):
        self.mt5_path = Path(mt5_path)
        self.signal_file = Path("signals/signal.json")
        self.watch_interval = watch_interval
        self.verbose = verbose
        self.log_file = Path(log_file)
        self.last_sync_hash = None
        self.last_sync_time = 0
        self.sync_count = 0
        self.error_count = 0

        # Create log directory
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        self._log(f"Signal Sync Manager initialized")
        self._log(f"  Signal file: {self.signal_file}")
        self._log(f"  MT5 path: {self.mt5_path}")
        self._log(f"  Watch interval: {watch_interval} seconds")
        self._log(f"  Verbose: {verbose}")

    def _log(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"

        # Console output
        if self.verbose or "ERROR" in message or "Synced" in message:
            print(log_msg)

        # File output
        with open(self.log_file, "a") as f:
            f.write(log_msg + "\n")

    def _get_file_hash(self, filepath):
        """Calculate MD5 hash of file content"""
        try:
            if not filepath.exists():
                return None
            with open(filepath, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            self._log(f"ERROR: Failed to hash {filepath}: {e}")
            return None

    def _extract_event_ids(self, signal_data):
        """Extract event_ids from signal.json"""
        try:
            if isinstance(signal_data, dict) and "signals" in signal_data:
                return [s.get("event_id") for s in signal_data.get("signals", []) if s.get("event_id")]
            return []
        except Exception as e:
            self._log(f"ERROR: Failed to extract event_ids: {e}")
            return []

    def check_for_changes(self):
        """Check if signal.json has been modified"""
        if not self.signal_file.exists():
            self._log(f"WARNING: Signal file not found at {self.signal_file}")
            return False

        current_hash = self._get_file_hash(self.signal_file)

        if current_hash is None:
            return False

        if current_hash != self.last_sync_hash:
            if self.verbose:
                self._log(f"Change detected in signal.json (hash: {current_hash[:8]}...)")
            return True

        return False

    def sync_to_mt5(self):
        """Sync signal.json to MT5 Files folder"""
        try:
            # Verify signal file exists
            if not self.signal_file.exists():
                self._log(f"ERROR: Signal file not found: {self.signal_file}")
                self.error_count += 1
                return False

            # Verify MT5 path exists
            if not self.mt5_path.exists():
                self._log(f"ERROR: MT5 Files path not found: {self.mt5_path}")
                self.error_count += 1
                return False

            # Read signal data
            try:
                with open(self.signal_file, "r") as f:
                    signal_data = json.load(f)
            except json.JSONDecodeError as e:
                self._log(f"ERROR: Invalid JSON in signal file: {e}")
                self.error_count += 1
                return False

            # Extract event_ids
            event_ids = self._extract_event_ids(signal_data)

            # Destination path
            mt5_signal_file = self.mt5_path / "signal.json"

            # Copy file
            try:
                file_size = self.signal_file.stat().st_size
                shutil.copy2(self.signal_file, mt5_signal_file)

                # Verify copy
                if mt5_signal_file.exists():
                    dest_size = mt5_signal_file.stat().st_size
                    if dest_size == file_size:
                        self.sync_count += 1
                        event_ids_str = f" ({len(event_ids)} signal(s): {', '.join(event_ids[:3])})" if event_ids else ""
                        self._log(f"✓ Synced signal.json to MT5{event_ids_str} (size: {file_size} bytes)")

                        # Update hash
                        self.last_sync_hash = self._get_file_hash(self.signal_file)
                        self.last_sync_time = time.time()
                        return True
                    else:
                        self._log(f"ERROR: File size mismatch after copy ({dest_size} != {file_size})")
                        self.error_count += 1
                        return False
                else:
                    self._log(f"ERROR: Destination file not created: {mt5_signal_file}")
                    self.error_count += 1
                    return False

            except PermissionError:
                self._log(f"ERROR: Permission denied writing to {mt5_signal_file}")
                self._log(f"       Check MT5 Files folder permissions and SMB share access")
                self.error_count += 1
                return False
            except IOError as e:
                self._log(f"ERROR: I/O error during copy: {e}")
                self.error_count += 1
                return False

        except Exception as e:
            self._log(f"ERROR: Unexpected error during sync: {e}")
            self.error_count += 1
            return False

    def sync_heartbeat_from_mt5(self):
        """Optionally sync heartbeat.json back from MT5 (if it exists)"""
        try:
            mt5_heartbeat_file = self.mt5_path / "heartbeat.json"
            local_heartbeat_file = Path("signals/heartbeat.json")

            if not mt5_heartbeat_file.exists():
                return False

            # Check if heartbeat is newer than last sync
            if local_heartbeat_file.exists():
                mt5_mtime = mt5_heartbeat_file.stat().st_mtime
                local_mtime = local_heartbeat_file.stat().st_mtime

                if local_mtime >= mt5_mtime:
                    # Local is already up-to-date
                    return False

            # Copy heartbeat back from MT5
            file_size = mt5_heartbeat_file.stat().st_size
            shutil.copy2(mt5_heartbeat_file, local_heartbeat_file)

            if self.verbose:
                self._log(f"✓ Synced heartbeat.json from MT5 (size: {file_size} bytes)")

            return True

        except Exception as e:
            if self.verbose:
                self._log(f"WARNING: Could not sync heartbeat from MT5: {e}")
            return False

    def run_once(self):
        """Perform single sync cycle"""
        if self.check_for_changes():
            return self.sync_to_mt5()

        # Also check for heartbeat from MT5
        self.sync_heartbeat_from_mt5()

        return False

    def run_continuous(self):
        """Run continuous monitoring loop"""
        self._log("Starting continuous monitoring loop...")
        self._log(f"Press Ctrl+C to stop")

        try:
            while True:
                self.run_once()
                time.sleep(self.watch_interval)
        except KeyboardInterrupt:
            self._log("Sync manager stopped by user")
            self.print_summary()

    def print_summary(self):
        """Print sync statistics"""
        print("\n" + "="*60)
        print("SYNC SUMMARY")
        print("="*60)
        print(f"Total syncs performed: {self.sync_count}")
        print(f"Total errors: {self.error_count}")
        print(f"Sync success rate: {100 * self.sync_count / (self.sync_count + self.error_count) if (self.sync_count + self.error_count) > 0 else 0:.1f}%")
        print(f"Log file: {self.log_file}")
        print("="*60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Sync signal.json to MT5 Files folder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # One-time sync:
  python sync_signal_to_mt5.py --mt5-path "/Volumes/Stratos/.../MQL5/Files"

  # Continuous sync with 10-second interval:
  python sync_signal_to_mt5.py --mt5-path "/Volumes/Stratos/.../MQL5/Files" --watch 10 --verbose

  # Background sync (for testing):
  python sync_signal_to_mt5.py --mt5-path "/Volumes/Stratos/.../MQL5/Files" --watch 300 &
        """
    )

    parser.add_argument(
        "--mt5-path",
        required=True,
        help="Path to MT5 Files folder (mounted SMB share)"
    )
    parser.add_argument(
        "--watch",
        type=int,
        default=10,
        help="Polling interval in seconds (default: 10)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--log-file",
        default="logs/sync.log",
        help="Output log file (default: logs/sync.log)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (don't continuous)"
    )

    args = parser.parse_args()

    # Create sync manager
    sync_manager = SignalSyncManager(
        mt5_path=args.mt5_path,
        watch_interval=args.watch,
        verbose=args.verbose,
        log_file=args.log_file
    )

    # Run sync
    if args.once:
        print(f"Performing single sync...")
        sync_manager.run_once()
        sync_manager.print_summary()
    else:
        sync_manager.run_continuous()


if __name__ == "__main__":
    main()
