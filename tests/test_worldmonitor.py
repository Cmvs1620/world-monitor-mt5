"""Unit tests for WorldMonitor API client."""

import pytest
import sqlite3
import os
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from engine.worldmonitor import WorldMonitorClient


@pytest.fixture
def temp_cache_db(tmp_path):
    """Create a temporary cache database for testing."""
    cache_path = str(tmp_path / "test_cache.db")
    yield cache_path
    # Cleanup
    if os.path.exists(cache_path):
        os.remove(cache_path)


@pytest.fixture
def client(temp_cache_db):
    """Create a WorldMonitorClient instance for testing."""
    return WorldMonitorClient(cache_db_path=temp_cache_db)


@pytest.fixture
def mock_events():
    """Sample events from WorldMonitor API."""
    return [
        {
            "id": "evt_001",
            "title": "Political Crisis in Region A",
            "description": "Ongoing political tensions",
            "timestamp": "2024-04-01T10:00:00Z",
            "severity": "high",
            "region": "Africa",
            "category": "political",
        },
        {
            "id": "evt_002",
            "title": "Economic Sanctions Announced",
            "description": "New trade restrictions",
            "timestamp": "2024-04-02T14:30:00Z",
            "severity": "critical",
            "region": "Asia",
            "category": "economic",
        },
        {
            "id": "evt_003",
            "title": "Natural Disaster Alert",
            "description": "Earthquake reported",
            "timestamp": "2024-04-03T08:15:00Z",
            "severity": "medium",
            "region": "Americas",
            "category": "natural",
        },
    ]


class TestWorldMonitorClientInitialization:
    """Test WorldMonitorClient initialization and cache setup."""

    def test_client_initialization(self, temp_cache_db):
        """Test that client initializes without error."""
        client = WorldMonitorClient(cache_db_path=temp_cache_db)
        assert client is not None
        assert client.cache_db_path == temp_cache_db

    def test_cache_db_created_on_init(self, temp_cache_db):
        """Test that SQLite cache database is created on initialization."""
        client = WorldMonitorClient(cache_db_path=temp_cache_db)
        assert os.path.exists(temp_cache_db)

    def test_cache_table_exists(self, temp_cache_db):
        """Test that the events cache table is created."""
        client = WorldMonitorClient(cache_db_path=temp_cache_db)
        conn = sqlite3.connect(temp_cache_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='events'"
        )
        assert cursor.fetchone() is not None
        conn.close()


class TestFetchEvents:
    """Test fetching events from WorldMonitor API."""

    @patch("engine.worldmonitor.requests.get")
    def test_fetch_events_returns_list(self, mock_get, client, mock_events):
        """Test that fetch_events returns a list of events."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_events
        mock_get.return_value = mock_response

        events = client.fetch_events(limit=10)

        assert isinstance(events, list)
        assert len(events) > 0
        mock_get.assert_called_once()

    @patch("engine.worldmonitor.requests.get")
    def test_events_have_required_fields(self, mock_get, client, mock_events):
        """Test that returned events have all required fields."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_events
        mock_get.return_value = mock_response

        events = client.fetch_events(limit=10)

        required_fields = [
            "id",
            "title",
            "description",
            "timestamp",
            "severity",
            "source",
            "region",
            "category",
        ]
        for event in events:
            for field in required_fields:
                assert field in event, f"Event missing field: {field}"

    @patch("engine.worldmonitor.requests.get")
    def test_events_normalized_with_source(self, mock_get, client, mock_events):
        """Test that events are normalized with 'source' field set to 'worldmonitor'."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_events
        mock_get.return_value = mock_response

        events = client.fetch_events(limit=10)

        for event in events:
            assert event.get("source") == "worldmonitor"

    @patch("engine.worldmonitor.requests.get")
    def test_fetch_with_limit_parameter(self, mock_get, client, mock_events):
        """Test that fetch_events respects the limit parameter."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_events
        mock_get.return_value = mock_response

        client.fetch_events(limit=5)

        # Verify the API was called with the correct limit
        call_args = mock_get.call_args
        assert "limit=5" in call_args[0][0]


class TestDeduplication:
    """Test event deduplication and caching."""

    @patch("engine.worldmonitor.requests.get")
    def test_deduplication_cache(self, mock_get, client, mock_events):
        """Test that the same events are not fetched twice (deduplication)."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_events
        mock_get.return_value = mock_response

        # First fetch
        events_first = client.fetch_events(limit=10)
        assert len(events_first) == 3

        # Second fetch with same data
        events_second = client.fetch_events(limit=10)
        assert len(events_second) == 0  # All events are cached, so no new events

    @patch("engine.worldmonitor.requests.get")
    def test_skip_cache_parameter(self, mock_get, client, mock_events):
        """Test that skip_cache=True bypasses the deduplication cache."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_events
        mock_get.return_value = mock_response

        # First fetch
        events_first = client.fetch_events(limit=10, skip_cache=False)
        assert len(events_first) == 3

        # Second fetch with skip_cache=True
        events_second = client.fetch_events(limit=10, skip_cache=True)
        assert len(events_second) == 3  # All events returned despite cache

    @patch("engine.worldmonitor.requests.get")
    def test_only_new_events_returned(self, mock_get, client, mock_events):
        """Test that only new (uncached) events are returned."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        # First request: all 3 events
        mock_response.json.return_value = mock_events
        mock_get.return_value = mock_response
        events_first = client.fetch_events(limit=10)
        assert len(events_first) == 3

        # Second request: mix of old (evt_001, evt_002) and new (evt_004)
        new_mock_events = mock_events[:2] + [
            {
                "id": "evt_004",
                "title": "New Event",
                "description": "A new event",
                "timestamp": "2024-04-04T12:00:00Z",
                "severity": "low",
                "region": "Europe",
                "category": "political",
            }
        ]
        mock_response.json.return_value = new_mock_events
        events_second = client.fetch_events(limit=10)
        assert len(events_second) == 1
        assert events_second[0]["id"] == "evt_004"


class TestCachePersistence:
    """Test SQLite cache persistence."""

    @patch("engine.worldmonitor.requests.get")
    def test_cache_persists_to_sqlite(self, mock_get, client, mock_events):
        """Test that events are persisted to SQLite cache."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_events
        mock_get.return_value = mock_response

        # Fetch events
        client.fetch_events(limit=10)

        # Check SQLite for cached events
        conn = sqlite3.connect(client.cache_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 3

    @patch("engine.worldmonitor.requests.get")
    def test_is_cached_returns_true_for_cached_event(
        self, mock_get, client, mock_events
    ):
        """Test that _is_cached returns True for cached events."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_events
        mock_get.return_value = mock_response

        # Fetch events to populate cache
        client.fetch_events(limit=10)

        # Check if events are cached
        assert client._is_cached("evt_001") is True
        assert client._is_cached("evt_002") is True
        assert client._is_cached("evt_999") is False

    @patch("engine.worldmonitor.requests.get")
    def test_get_cached_events_retrieves_recent_events(
        self, mock_get, client, mock_events
    ):
        """Test that get_cached_events retrieves events from cache."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_events
        mock_get.return_value = mock_response

        # Fetch and cache events
        client.fetch_events(limit=10)

        # Retrieve cached events
        cached_events = client.get_cached_events(days_back=7)

        assert len(cached_events) == 3
        assert all(event.get("source") == "worldmonitor" for event in cached_events)


class TestErrorHandling:
    """Test error handling in WorldMonitor client."""

    @patch("engine.worldmonitor.requests.get")
    def test_api_error_handling(self, mock_get, client):
        """Test that API errors are handled gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        # Should return empty list on API error
        events = client.fetch_events(limit=10)
        assert isinstance(events, list)

    @patch("engine.worldmonitor.requests.get")
    def test_connection_error_handling(self, mock_get, client):
        """Test that connection errors are handled gracefully."""
        import requests

        mock_get.side_effect = requests.ConnectionError("Connection failed")

        # Should return empty list on connection error
        events = client.fetch_events(limit=10)
        assert isinstance(events, list)
        assert len(events) == 0
