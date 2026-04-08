#!/usr/bin/env python3
"""
Trade Execution Verification Utility

Reads signals/signal.json and signals/heartbeat.json, verifies execution flow:
- signal event_id matches heartbeat signal_id
- Execution timestamp within expected latency
- Generates execution report with statistics

Usage:
    python verify_trade_execution.py [--csv logs/signals.csv] [--output EXECUTION_REPORT.txt]

Output:
    EXECUTION_REPORT.txt with summary table and statistics
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import argparse


class ExecutionVerifier:
    """Verifies signal-to-execution mapping"""

    def __init__(self, signals_csv="logs/signals.csv", output_file="EXECUTION_REPORT.txt"):
        self.signals_csv = Path(signals_csv)
        self.output_file = Path(output_file)
        self.signal_file = Path("signals/signal.json")
        self.heartbeat_file = Path("signals/heartbeat.json")

        self.signals = []
        self.heartbeats = []
        self.matched = []
        self.unmatched = []

    def load_signals_from_csv(self):
        """Load signals from logs/signals.csv"""
        if not self.signals_csv.exists():
            print(f"WARNING: {self.signals_csv} not found, skipping CSV load")
            return 0

        try:
            with open(self.signals_csv, "r") as f:
                lines = f.readlines()

            # Skip header
            for line in lines[1:]:
                parts = line.strip().split(",")
                if len(parts) >= 8:
                    self.signals.append({
                        "timestamp": parts[0],
                        "event_id": parts[1],
                        "symbol": parts[2],
                        "action": parts[3],
                        "confidence": float(parts[4]) if parts[4] else None,
                        "ticket": int(parts[5]) if parts[5] else None,
                        "status": parts[6],
                        "latency_sec": float(parts[7]) if parts[7] else None,
                    })

            return len(self.signals)
        except Exception as e:
            print(f"ERROR: Failed to load signals CSV: {e}")
            return 0

    def load_heartbeat(self):
        """Load latest heartbeat from signals/heartbeat.json"""
        if not self.heartbeat_file.exists():
            print(f"WARNING: {self.heartbeat_file} not found")
            return 0

        try:
            with open(self.heartbeat_file, "r") as f:
                heartbeat = json.load(f)

            self.heartbeats.append({
                "timestamp": heartbeat.get("timestamp"),
                "signal_id": heartbeat.get("signal_id"),
                "executed": heartbeat.get("executed"),
                "status": heartbeat.get("status"),
                "ticket": heartbeat.get("ticket"),
                "order_type": heartbeat.get("order_type"),
                "symbol": heartbeat.get("symbol"),
                "entry_price": heartbeat.get("entry_price"),
                "position_size": heartbeat.get("position_size"),
                "error_reason": heartbeat.get("error_reason", ""),
            })

            return 1
        except Exception as e:
            print(f"ERROR: Failed to load heartbeat: {e}")
            return 0

    def load_signal_file(self):
        """Load signals from signals/signal.json"""
        if not self.signal_file.exists():
            print(f"WARNING: {self.signal_file} not found")
            return 0

        try:
            with open(self.signal_file, "r") as f:
                data = json.load(f)

            signal_count = 0
            for signal in data.get("signals", []):
                self.signals.append({
                    "timestamp": data.get("timestamp"),
                    "event_id": signal.get("event_id"),
                    "symbol": signal.get("symbol"),
                    "action": signal.get("action"),
                    "confidence": signal.get("confidence"),
                    "ticket": None,
                    "status": "pending",
                    "latency_sec": None,
                })
                signal_count += 1

            return signal_count
        except Exception as e:
            print(f"ERROR: Failed to load signal file: {e}")
            return 0

    def match_signals_with_heartbeats(self):
        """Match signals with heartbeat responses"""
        for hb in self.heartbeats:
            signal_id = hb.get("signal_id")
            matched = False

            for signal in self.signals:
                if signal.get("event_id") == signal_id:
                    # Calculate latency
                    try:
                        from datetime import datetime
                        hb_time = datetime.fromisoformat(hb.get("timestamp").replace("Z", "+00:00"))
                        signal_time = datetime.fromisoformat(signal.get("timestamp").replace("Z", "+00:00"))
                        latency = (hb_time - signal_time).total_seconds()

                        self.matched.append({
                            "signal_id": signal_id,
                            "symbol": signal.get("symbol"),
                            "action": signal.get("action"),
                            "confidence": signal.get("confidence"),
                            "ticket": hb.get("ticket"),
                            "entry_price": hb.get("entry_price"),
                            "position_size": hb.get("position_size"),
                            "latency_sec": latency,
                            "status": hb.get("status"),
                        })
                        matched = True
                        break
                    except Exception as e:
                        print(f"WARNING: Failed to calculate latency for {signal_id}: {e}")

            if not matched:
                self.unmatched.append({
                    "signal_id": signal_id,
                    "status": hb.get("status"),
                })

    def generate_report(self):
        """Generate execution report"""
        report_lines = []

        report_lines.append("="*80)
        report_lines.append("EXECUTION REPORT - Signal → Heartbeat Verification")
        report_lines.append("="*80)
        report_lines.append("")

        # Summary statistics
        total_signals = len(self.signals)
        total_executed = len(self.matched)
        total_heartbeats = len(self.heartbeats)

        report_lines.append("SUMMARY STATISTICS")
        report_lines.append("-" * 80)
        report_lines.append(f"Total signals generated:          {total_signals}")
        report_lines.append(f"Total heartbeat responses:        {total_heartbeats}")
        report_lines.append(f"Signals matched with heartbeats:  {len(self.matched)}")
        report_lines.append(f"Unmatched heartbeats:             {len(self.unmatched)}")
        report_lines.append("")

        # Execution summary
        if total_executed > 0:
            success_count = sum(1 for m in self.matched if m.get("status") == "success")
            fail_count = total_executed - success_count

            report_lines.append("EXECUTION SUMMARY")
            report_lines.append("-" * 80)
            report_lines.append(f"Executed trades:                  {total_executed}")
            report_lines.append(f"  - Successful:                   {success_count} ({100*success_count/total_executed:.1f}%)")
            report_lines.append(f"  - Failed:                       {fail_count} ({100*fail_count/total_executed:.1f}%)")
            report_lines.append("")

        # Latency statistics
        if self.matched:
            latencies = [m.get("latency_sec") for m in self.matched if m.get("latency_sec") is not None]
            if latencies:
                report_lines.append("LATENCY STATISTICS")
                report_lines.append("-" * 80)
                report_lines.append(f"Min latency:                      {min(latencies):.1f} seconds")
                report_lines.append(f"Max latency:                      {max(latencies):.1f} seconds")
                report_lines.append(f"Avg latency:                      {sum(latencies)/len(latencies):.1f} seconds")
                report_lines.append(f"Median latency:                   {sorted(latencies)[len(latencies)//2]:.1f} seconds")
                report_lines.append("")

        # Detailed execution results
        if self.matched:
            report_lines.append("DETAILED EXECUTION RESULTS")
            report_lines.append("-" * 80)
            report_lines.append(f"{'Ticket':<12} {'Symbol':<10} {'Action':<6} {'Conf':<6} {'Price':<10} {'Size':<8} {'Latency':<10} {'Status'}")
            report_lines.append("-" * 80)

            for m in sorted(self.matched, key=lambda x: x.get("latency_sec", 0))[:20]:  # First 20
                ticket = str(m.get("ticket", "N/A"))[:11]
                symbol = str(m.get("symbol", ""))[:9]
                action = str(m.get("action", ""))[:5]
                conf = f"{m.get('confidence', 0):.2f}" if m.get("confidence") else "N/A"
                price = f"{m.get('entry_price', 0):.5f}" if m.get("entry_price") else "N/A"
                size = f"{m.get('position_size', 0):.2f}" if m.get("position_size") else "N/A"
                latency = f"{m.get('latency_sec', 0):.1f}s" if m.get("latency_sec") else "N/A"
                status = m.get("status", "unknown")

                report_lines.append(f"{ticket:<12} {symbol:<10} {action:<6} {conf:<6} {price:<10} {size:<8} {latency:<10} {status}")

            if len(self.matched) > 20:
                report_lines.append(f"... and {len(self.matched) - 20} more trades")

            report_lines.append("")

        # Validation checks
        report_lines.append("VALIDATION CHECKS")
        report_lines.append("-" * 80)

        all_valid = True

        # Check 1: All tickets valid
        tickets_valid = all(m.get("ticket") and m.get("ticket") > 0 for m in self.matched)
        check1 = "✓" if tickets_valid else "✗"
        report_lines.append(f"{check1} All executed trades have valid ticket numbers")
        all_valid = all_valid and tickets_valid

        # Check 2: Latency within SLA
        if self.matched:
            latencies = [m.get("latency_sec") for m in self.matched if m.get("latency_sec")]
            latency_ok = all(l < 300 for l in latencies)  # 5 minute SLA
            check2 = "✓" if latency_ok else "✗"
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            report_lines.append(f"{check2} Average latency within SLA (avg: {avg_latency:.1f}s, max: 300s)")
            all_valid = all_valid and latency_ok
        else:
            report_lines.append("✗ No executed trades to validate latency")
            all_valid = False

        # Check 3: signal_id matches
        ids_match = len(self.unmatched) == 0
        check3 = "✓" if ids_match else "✗"
        report_lines.append(f"{check3} All heartbeat signal_ids match original event_ids")
        all_valid = all_valid and ids_match

        # Check 4: Execution ratio
        if total_signals > 0:
            exec_ratio = total_executed / total_signals
            exec_ok = exec_ratio >= 0.20  # At least 20% should execute
            check4 = "✓" if exec_ok else "✗"
            report_lines.append(f"{check4} Execution ratio acceptable ({100*exec_ratio:.1f}% of signals executed)")
            all_valid = all_valid and exec_ok

        report_lines.append("")

        # Final verdict
        report_lines.append("="*80)
        if all_valid and total_executed > 0:
            report_lines.append("FINAL RESULT: PASS ✓")
            report_lines.append("All execution criteria met. Ready for production.")
        elif total_executed == 0:
            report_lines.append("FINAL RESULT: FAIL ✗")
            report_lines.append("No trades executed. Review risk gates and signal generation.")
        else:
            report_lines.append("FINAL RESULT: CONDITIONAL ⚠")
            report_lines.append("Some criteria failed. Review details above.")
        report_lines.append("="*80)

        return "\n".join(report_lines)

    def save_report(self, report_text):
        """Save report to file"""
        try:
            with open(self.output_file, "w") as f:
                f.write(report_text)
            print(f"\nReport saved to: {self.output_file}")
        except Exception as e:
            print(f"ERROR: Failed to save report: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Verify trade execution from signal.json and heartbeat.json"
    )
    parser.add_argument(
        "--csv",
        default="logs/signals.csv",
        help="Path to signals CSV log (default: logs/signals.csv)"
    )
    parser.add_argument(
        "--output",
        default="EXECUTION_REPORT.txt",
        help="Output report file (default: EXECUTION_REPORT.txt)"
    )

    args = parser.parse_args()

    # Create verifier
    verifier = ExecutionVerifier(signals_csv=args.csv, output_file=args.output)

    # Load data
    print("Loading signal execution data...")
    csv_count = verifier.load_signals_from_csv()
    file_count = verifier.load_signal_file() if csv_count == 0 else 0
    hb_count = verifier.load_heartbeat()

    if csv_count > 0:
        print(f"  Loaded {csv_count} signals from CSV")
    if file_count > 0:
        print(f"  Loaded {file_count} signals from signal.json")
    if hb_count > 0:
        print(f"  Loaded {hb_count} heartbeat response(s)")

    # Match and verify
    if verifier.signals and verifier.heartbeats:
        print("\nMatching signals with heartbeats...")
        verifier.match_signals_with_heartbeats()
        print(f"  Matched: {len(verifier.matched)}")
        print(f"  Unmatched: {len(verifier.unmatched)}")

    # Generate report
    print("\nGenerating execution report...")
    report = verifier.generate_report()

    # Display and save
    print("\n" + report)
    verifier.save_report(report)


if __name__ == "__main__":
    main()
