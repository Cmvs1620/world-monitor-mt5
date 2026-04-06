"""WorldMonitor API client for fetching geopolitical events with caching and deduplication."""

import sqlite3
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class WorldMonitorClient:
    """
    Client for fetching geopolitical events from WorldMonitor public API.

    Features:
    - Fetches events from WorldMonitor public API
    - Caches events in SQLite database
    - Deduplicates events (returns only new, uncached events)
    - Retrieves historical cached events
    """

    BASE_URL = "https://api.worldmonitor.app"
    EVENTS_ENDPOINT = "/events"

    def __init__(self, cache_db_path: str = "signals/.worldmonitor_cache.db"):
        """
        Initialize WorldMonitorClient with cache database path.

        Args:
            cache_db_path: Path to SQLite cache database. Defaults to signals/.worldmonitor_cache.db
        """
        self.cache_db_path = cache_db_path
        self._init_cache_db()

    def _init_cache_db(self) -> None:
        """Create SQLite cache table if it doesn't exist."""
        # Ensure parent directory exists
        Path(self.cache_db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()

        # Create events table if it doesn't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                timestamp TEXT NOT NULL,
                severity TEXT,
                source TEXT,
                region TEXT,
                category TEXT,
                cached_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()
        logger.debug(f"Cache database initialized at {self.cache_db_path}")

    def _is_cached(self, event_id: str) -> bool:
        """
        Check if an event is already in the cache.

        Args:
            event_id: The event ID to check

        Returns:
            True if event is cached, False otherwise
        """
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM events WHERE id = ?", (event_id,))
        result = cursor.fetchone() is not None
        conn.close()
        return result

    def _cache_event(self, event: dict) -> None:
        """
        Store an event in SQLite cache.

        Args:
            event: Event dictionary with keys: id, title, description, timestamp, severity, source, region, category
        """
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR IGNORE INTO events
            (id, title, description, timestamp, severity, source, region, category, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.get("id"),
                event.get("title"),
                event.get("description"),
                event.get("timestamp"),
                event.get("severity"),
                event.get("source"),
                event.get("region"),
                event.get("category"),
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        conn.close()

    def _normalize_event(self, event: dict) -> dict:
        """
        Normalize event from API response to standard format.

        Args:
            event: Raw event from API

        Returns:
            Normalized event dictionary
        """
        return {
            "id": event.get("id"),
            "title": event.get("title"),
            "description": event.get("description"),
            "timestamp": event.get("timestamp"),
            "severity": event.get("severity"),
            "source": "worldmonitor",
            "region": event.get("region"),
            "category": event.get("category"),
        }

    def fetch_events(self, limit: int = 10, skip_cache: bool = False) -> list:
        """
        Fetch events from WorldMonitor API and filter out cached events.

        Returns only NEW (previously unseen) events, unless skip_cache is True.

        Args:
            limit: Maximum number of events to fetch from API. Defaults to 10
            skip_cache: If True, bypass deduplication and return all events from API. Defaults to False

        Returns:
            List of NEW event dictionaries (only uncached events)
            Returns empty list if API error or no new events
        """
        try:
            # Fetch events from API
            url = f"{self.BASE_URL}{self.EVENTS_ENDPOINT}?limit={limit}"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                logger.error(f"WorldMonitor API error: {response.status_code}")
                return []

            api_events = response.json()
            if not isinstance(api_events, list):
                logger.error("API response is not a list")
                return []

            # Normalize all events
            normalized_events = [self._normalize_event(event) for event in api_events]

            # Filter out cached events (deduplication)
            new_events = []
            for event in normalized_events:
                if skip_cache:
                    # Skip deduplication, include all events
                    new_events.append(event)
                    self._cache_event(event)
                elif not self._is_cached(event.get("id")):
                    # Only include new (uncached) events
                    new_events.append(event)
                    self._cache_event(event)
                # else: event is already cached, skip it

            logger.info(
                f"Fetched {len(api_events)} events, {len(new_events)} are new"
            )
            return new_events

        except requests.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return []
        except requests.Timeout as e:
            logger.error(f"Request timeout: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching events: {e}")
            return []

    def get_cached_events(self, days_back: int = 7) -> list:
        """
        Retrieve cached events from the last N days.

        Args:
            days_back: Number of days to look back. Defaults to 7

        Returns:
            List of cached event dictionaries
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        cutoff_iso = cutoff_date.isoformat()

        conn = sqlite3.connect(self.cache_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, title, description, timestamp, severity, source, region, category
            FROM events
            WHERE cached_at >= ?
            ORDER BY timestamp DESC
            """,
            (cutoff_iso,),
        )

        rows = cursor.fetchall()
        conn.close()

        # Convert sqlite3.Row objects to dictionaries
        events = [dict(row) for row in rows]
        logger.info(f"Retrieved {len(events)} cached events from last {days_back} days")
        return events
