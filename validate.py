#!/usr/bin/env python3
"""
MT5 GeoSignal Expert Advisor - Phase 0 Validation Script
Validates the entire environment setup after running setup.ps1
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from typing import Tuple, List


# ANSI Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def check_passed(message: str) -> None:
    """Print a passing check."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")


def check_failed(message: str) -> None:
    """Print a failing check."""
    print(f"{Colors.RED}✗{Colors.RESET} {message}")


def check_warning(message: str) -> None:
    """Print a warning."""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")


def section_header(title: str) -> None:
    """Print a section header."""
    print(f"\n{Colors.CYAN}[{title}]{Colors.RESET}")


def print_error_help(hint: str) -> None:
    """Print helpful error resolution message."""
    print(f"  {Colors.YELLOW}→ {hint}{Colors.RESET}")


# Check 1: Python Version
def check_python_version() -> bool:
    """Verify Python 3.11+ is being used."""
    section_header("Python")

    version_info = sys.version_info
    version_string = f"{version_info.major}.{version_info.minor}.{version_info.micro}"

    if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 11):
        check_failed(f"Python {version_string} (requires 3.11+)")
        print_error_help(f"Install Python 3.11+ from https://python.org")
        return False

    check_passed(f"Python {version_string}")
    return True


# Check 2: Project Structure
def check_project_structure(project_root: Path) -> bool:
    """Verify all required directories exist."""
    section_header("Project Structure")

    required_dirs = ["engine", "bridge", "signals", "logs", "config", "tests"]
    all_exist = True

    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.is_dir():
            check_passed(f"{dir_name}/")
        else:
            check_failed(f"{dir_name}/ (missing)")
            print_error_help(f"Run: mkdir -p {dir_name}")
            all_exist = False

    return all_exist


# Check 3: Configuration Files
def check_configuration_files(project_root: Path) -> bool:
    """Verify .env and config/settings.json exist and are properly configured."""
    section_header("Configuration Files")

    all_valid = True

    # Check .env
    env_file = project_root / ".env"
    if env_file.exists():
        check_passed(".env exists")

        # Verify ANTHROPIC_API_KEY is set (not placeholder)
        try:
            with open(env_file, 'r') as f:
                env_content = f.read()

            if 'ANTHROPIC_API_KEY=your_key_here' in env_content or \
               'ANTHROPIC_API_KEY=' not in env_content:
                check_warning(".env: ANTHROPIC_API_KEY not configured (placeholder or missing)")
                print_error_help("Edit .env and set ANTHROPIC_API_KEY to your actual key")
                all_valid = False
            else:
                check_passed(".env: ANTHROPIC_API_KEY configured")
        except Exception as e:
            check_failed(f".env: Could not read ({e})")
            all_valid = False
    else:
        check_failed(".env (missing)")
        print_error_help("Run setup.ps1 or create .env with API keys")
        all_valid = False

    # Check config/settings.json
    settings_file = project_root / "config" / "settings.json"
    if settings_file.exists():
        check_passed("config/settings.json exists")

        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)

            # Verify mt5_files_path is configured
            if 'mt5_files_path' not in settings or \
               settings['mt5_files_path'] == 'C:\\Users\\your_username\\AppData\\Roaming\\MetaQuotes\\Terminal\\your_terminal_id\\MQL5\\Files':
                check_warning("config/settings.json: mt5_files_path not configured (placeholder)")
                print_error_help("Edit config/settings.json and set mt5_files_path to your MT5 directory")
                all_valid = False
            else:
                check_passed("config/settings.json: mt5_files_path configured")

            # Verify JSON structure
            required_keys = ["debug", "log_level", "mt5_files_path", "worldmonitor_poll_interval_seconds"]
            missing_keys = [k for k in required_keys if k not in settings]
            if missing_keys:
                check_warning(f"config/settings.json: Missing keys: {', '.join(missing_keys)}")
                all_valid = False
            else:
                check_passed("config/settings.json: Structure valid")

        except json.JSONDecodeError as e:
            check_failed(f"config/settings.json: Invalid JSON ({e})")
            all_valid = False
        except Exception as e:
            check_failed(f"config/settings.json: Error reading file ({e})")
            all_valid = False
    else:
        check_failed("config/settings.json (missing)")
        print_error_help("Run setup.ps1 to create config/settings.json")
        all_valid = False

    return all_valid


# Check 4: Signal JSON Templates
def check_signal_templates(project_root: Path) -> bool:
    """Verify signal JSON template files exist and are valid JSON."""
    section_header("Signal JSON Templates")

    required_signals = {
        "signals/signal.json": ["timestamp", "event_id", "classification", "action"],
        "signals/signal_log.json": [],  # Should be a JSON array
        "signals/heartbeat.json": ["last_run", "status"]
    }

    all_valid = True

    for signal_path, required_keys in required_signals.items():
        file_path = project_root / signal_path
        if file_path.exists():
            check_passed(f"{signal_path} exists")

            try:
                with open(file_path, 'r') as f:
                    content = json.load(f)

                # For signal.json and heartbeat.json, check keys
                if required_keys and isinstance(content, dict):
                    missing = [k for k in required_keys if k not in content]
                    if missing:
                        check_warning(f"{signal_path}: Missing keys: {', '.join(missing)}")
                        all_valid = False
                    else:
                        check_passed(f"{signal_path}: Valid structure")
                elif signal_path == "signals/signal_log.json" and isinstance(content, list):
                    check_passed(f"{signal_path}: Valid array structure")
                else:
                    check_warning(f"{signal_path}: Structure may be incorrect")
                    all_valid = False

            except json.JSONDecodeError as e:
                check_failed(f"{signal_path}: Invalid JSON ({e})")
                all_valid = False
            except Exception as e:
                check_failed(f"{signal_path}: Error reading ({e})")
                all_valid = False
        else:
            check_failed(f"{signal_path} (missing)")
            print_error_help("Run setup.ps1 to create signal templates")
            all_valid = False

    return all_valid


# Check 5: Log CSV Files
def check_log_files(project_root: Path) -> bool:
    """Verify log CSV files exist with proper headers."""
    section_header("Log Files")

    required_logs = {
        "logs/trades.csv": "timestamp,symbol,action,volume,entry_price,stop_loss,take_profit,pnl,status,event_id",
        "logs/signals.csv": "timestamp,event_id,classification,confidence,symbol,action,volume,rationale,status",
        "logs/errors.log": None  # No specific header required
    }

    all_valid = True

    for log_path, expected_header in required_logs.items():
        file_path = project_root / log_path
        if file_path.exists():
            check_passed(f"{log_path} exists")

            if expected_header:
                try:
                    with open(file_path, 'r') as f:
                        first_line = f.readline().strip()

                    if first_line == expected_header:
                        check_passed(f"{log_path}: Headers valid")
                    else:
                        check_warning(f"{log_path}: Header mismatch or missing")
                        all_valid = False
                except Exception as e:
                    check_failed(f"{log_path}: Error reading ({e})")
                    all_valid = False
        else:
            check_failed(f"{log_path} (missing)")
            print_error_help("Run setup.ps1 to create log files")
            all_valid = False

    return all_valid


# Check 6: Python Packages
def check_python_packages() -> bool:
    """Verify required Python packages are installed."""
    section_header("Python Packages")

    required_packages = {
        "anthropic": "Claude API client",
        "MetaTrader5": "MT5 SDK",
        "requests": "HTTP library",
        "telegram": "Telegram Bot API",
        "python-dotenv": "Environment variables"
    }

    all_installed = True

    for package, description in required_packages.items():
        try:
            __import__(package.replace("-", "_"))
            check_passed(f"{package} ({description})")
        except ImportError:
            check_failed(f"{package} ({description}) - NOT INSTALLED")
            print_error_help(f"Run: pip install {package}")
            all_installed = False

    return all_installed


# Check 7: MT5 Connection (Optional)
def check_mt5_connection() -> bool:
    """Attempt to connect to MetaTrader 5 (fails gracefully on Mac/non-Windows)."""
    section_header("MetaTrader5 Connection (Optional)")

    try:
        import MetaTrader5 as mt5

        # Try to check if MT5 terminal is running
        if mt5.terminal_info() is not None:
            check_passed("MT5 Terminal is running")
            return True
        else:
            check_warning("MT5 Terminal not responding (may not be running)")
            print_error_help("Start MT5 Terminal to enable live trading features")
            return False
    except ImportError:
        check_warning("MetaTrader5 not available (normal on Mac/Linux)")
        return True  # Not a failure, just a limitation
    except Exception as e:
        check_warning(f"MT5 connection failed: {e}")
        print_error_help("Ensure MT5 Terminal is running on Windows")
        return True  # Not a hard failure


# Check 8: API Connectivity
def check_api_connectivity(project_root: Path) -> bool:
    """Test Claude API key and WorldMonitor API accessibility."""
    section_header("API Connectivity")

    all_valid = True

    # Test Claude API
    env_file = project_root / ".env"
    api_key = None

    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith("ANTHROPIC_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        break
        except Exception as e:
            check_warning(f"Could not read API key from .env ({e})")
            all_valid = False

    if api_key and api_key != "your_key_here":
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)
            # Make a minimal test request
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=10,
                messages=[
                    {"role": "user", "content": "OK"}
                ]
            )
            check_passed("Claude API: Key is valid and responsive")
        except Exception as e:
            check_failed(f"Claude API: Authentication or connection failed")
            print_error_help(f"Verify ANTHROPIC_API_KEY in .env is correct (Error: {str(e)[:50]})")
            all_valid = False
    else:
        check_warning("Claude API: Key not configured (skipping test)")
        print_error_help("Set ANTHROPIC_API_KEY in .env to enable API testing")

    # Test WorldMonitor API
    try:
        import requests

        response = requests.get(
            "https://api.worldmonitor.app/health",
            timeout=5
        )

        if response.status_code < 500:
            check_passed("WorldMonitor API: Accessible")
        else:
            check_warning(f"WorldMonitor API: Server error (HTTP {response.status_code})")
    except requests.exceptions.ConnectionError:
        check_warning("WorldMonitor API: Connection failed (network may be offline)")
    except requests.exceptions.Timeout:
        check_warning("WorldMonitor API: Request timeout")
    except Exception as e:
        check_warning(f"WorldMonitor API: Could not test ({type(e).__name__})")

    return all_valid


# Main validation function
def validate() -> int:
    """Run all validation checks."""
    print(f"{Colors.BOLD}{Colors.CYAN}=== MT5 GeoSignal Phase 0 Validation ==={Colors.RESET}\n")

    project_root = Path(__file__).parent

    results = {
        "Python Version": check_python_version(),
        "Project Structure": check_project_structure(project_root),
        "Configuration Files": check_configuration_files(project_root),
        "Signal JSON Templates": check_signal_templates(project_root),
        "Log Files": check_log_files(project_root),
        "Python Packages": check_python_packages(),
        "MetaTrader5 Connection": check_mt5_connection(),
        "API Connectivity": check_api_connectivity(project_root)
    }

    # Summary
    section_header("Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for check_name, result in results.items():
        status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if result else f"{Colors.RED}✗ FAIL{Colors.RESET}"
        print(f"{status} - {check_name}")

    print(f"\nResult: {passed}/{total} checks passed\n")

    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}Environment validation PASSED{Colors.RESET}")
        print(f"{Colors.CYAN}Next steps:{Colors.RESET}")
        print(f"  1. Edit .env with your actual API keys if not done")
        print(f"  2. Edit config/settings.json with your MT5 directory path")
        print(f"  3. Start development with: python -m engine.run")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}Environment validation FAILED{Colors.RESET}")
        print(f"{Colors.YELLOW}Fix the above issues before proceeding.{Colors.RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(validate())
