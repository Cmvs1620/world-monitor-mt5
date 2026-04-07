"""Telegram bot for sending real-time trade and error alerts."""

import asyncio
import logging
import os
from typing import Dict, Optional
from pathlib import Path

from telegram import Bot
from telegram.error import TelegramError

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass

logger = logging.getLogger(__name__)


class TelegramAlertBot:
    """Sends real-time trade signals and error alerts via Telegram."""

    def __init__(self, token: str, chat_id: str, enabled: bool = True):
        """
        Initialize TelegramAlertBot.

        Args:
            token (str): Telegram bot token
            chat_id (str): Target chat ID for alerts
            enabled (bool): Whether alerts are enabled (default: True)
        """
        self.token = token
        self.chat_id = chat_id
        self.enabled = enabled
        self.bot = Bot(token=token) if enabled else None
        logger.info(
            f"TelegramAlertBot initialized "
            f"(enabled={enabled}, chat_id={chat_id})"
        )

    async def send_signal_alert(self, signal: Dict, event_title: str) -> bool:
        """
        Send alert for new trade signal.

        Args:
            signal (dict): Signal dict with keys:
                - action: "BUY" | "SELL" | "HOLD"
                - symbol: Trading symbol (e.g., "EURUSD")
                - confidence: Confidence percentage (0.0-1.0)
                - rationale: Brief explanation
            event_title (str): Title of the event that triggered the signal

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Telegram alerts disabled, skipping send_signal_alert")
            return True

        try:
            action = signal.get("action", "HOLD")
            symbol = signal.get("symbol", "")
            confidence = signal.get("confidence", 0.0)
            rationale = signal.get("rationale", "")

            # Format message with Telegram markdown
            message = (
                "🔔 *NEW TRADE SIGNAL*\n\n"
                f"📰 *Event:* {event_title}\n"
                f"📊 *Action:* {action}\n"
                f"💱 *Symbol:* {symbol}\n"
                f"📈 *Confidence:* {confidence:.1%}\n"
                f"💬 *Rationale:* {rationale}"
            )

            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown"
            )

            logger.info(
                f"Sent signal alert: {symbol} {action} "
                f"(confidence: {confidence:.1%})"
            )
            return True

        except TelegramError as e:
            logger.error(f"Failed to send signal alert: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending signal alert: {e}")
            return False

    async def send_error_alert(self, error_msg: str) -> bool:
        """
        Send error alert.

        Args:
            error_msg (str): Error message text

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Telegram alerts disabled, skipping send_error_alert")
            return True

        try:
            message = f"⚠️ *ERROR*\n\n{error_msg}"

            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown"
            )

            logger.info(f"Sent error alert")
            return True

        except TelegramError as e:
            logger.error(f"Failed to send error alert: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending error alert: {e}")
            return False

    async def send_heartbeat(self, stats: Dict) -> bool:
        """
        Send periodic system status heartbeat.

        Args:
            stats (dict): System statistics with keys:
                - events_fetched (int): Number of events fetched
                - signals_generated (int): Number of signals generated
                - signals_passed (int): Number of signals that passed validation
                - errors (list): List of error messages

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Telegram alerts disabled, skipping send_heartbeat")
            return True

        try:
            events_fetched = stats.get("events_fetched", 0)
            signals_generated = stats.get("signals_generated", 0)
            signals_passed = stats.get("signals_passed", 0)
            errors = stats.get("errors", [])
            error_count = len(errors)

            message = (
                "💓 *System Heartbeat*\n\n"
                f"📥 *Events Fetched:* {events_fetched}\n"
                f"🔍 *Signals Generated:* {signals_generated}\n"
                f"✅ *Signals Passed:* {signals_passed}\n"
                f"❌ *Errors:* {error_count}"
            )

            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown"
            )

            logger.info(
                f"Sent heartbeat: "
                f"events={events_fetched}, "
                f"signals={signals_generated}, "
                f"passed={signals_passed}, "
                f"errors={error_count}"
            )
            return True

        except TelegramError as e:
            logger.error(f"Failed to send heartbeat: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending heartbeat: {e}")
            return False
