"""
Tests for the PriceCache.

Tests caching logic, TTL expiration, and persistence.
"""
import pytest
from unittest.mock import patch, mock_open
import os
import sys
import json
import tempfile
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from price_providers.cache import PriceCache
from price_providers.base import PriceResult


class TestPriceCache:
    """Tests for PriceCache."""

    def test_init_creates_empty_cache(self):
        """Test that init creates empty cache when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "cache.json")
            cache = PriceCache(cache_file=cache_file, ttl_hours=24)

            assert cache._cache == {}

    def test_set_and_get(self):
        """Test basic set and get operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "cache.json")
            cache = PriceCache(cache_file=cache_file, ttl_hours=24)

            result: PriceResult = {
                "price": 150.0,
                "provider": "Booking.com",
                "source": "serpapi",
                "cached": False
            }

            cache.set("Test Hotel", "2026-03-01", result)
            retrieved = cache.get("Test Hotel", "2026-03-01")

            assert retrieved is not None
            assert retrieved["price"] == 150.0
            assert retrieved["provider"] == "Booking.com"
            assert retrieved["source"] == "serpapi"
            assert retrieved["cached"] is True  # Should be marked as cached

    def test_get_nonexistent_hotel(self):
        """Test get returns None for non-existent hotel."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "cache.json")
            cache = PriceCache(cache_file=cache_file, ttl_hours=24)

            result = cache.get("Nonexistent Hotel", "2026-03-01")
            assert result is None

    def test_get_nonexistent_date(self):
        """Test get returns None for non-existent date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "cache.json")
            cache = PriceCache(cache_file=cache_file, ttl_hours=24)

            result: PriceResult = {
                "price": 150.0,
                "provider": "Test",
                "source": "test",
                "cached": False
            }
            cache.set("Test Hotel", "2026-03-01", result)

            # Different date should return None
            result = cache.get("Test Hotel", "2026-03-02")
            assert result is None

    def test_ttl_expiration(self):
        """Test that expired entries are not returned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "cache.json")
            cache = PriceCache(cache_file=cache_file, ttl_hours=1)

            # Manually set an expired entry
            expired_time = (datetime.now() - timedelta(hours=2)).isoformat()
            cache._cache = {
                "Test Hotel": {
                    "2026-03-01": {
                        "price": 150.0,
                        "provider": "Test",
                        "source": "test",
                        "timestamp": expired_time
                    }
                }
            }

            result = cache.get("Test Hotel", "2026-03-01")
            assert result is None

    def test_persistence(self):
        """Test that cache persists to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "cache.json")

            # Create cache and add entry
            cache1 = PriceCache(cache_file=cache_file, ttl_hours=24)
            result: PriceResult = {
                "price": 200.0,
                "provider": "Persistent",
                "source": "test",
                "cached": False
            }
            cache1.set("Persistent Hotel", "2026-03-01", result)

            # Create new cache instance and verify data
            cache2 = PriceCache(cache_file=cache_file, ttl_hours=24)
            retrieved = cache2.get("Persistent Hotel", "2026-03-01")

            assert retrieved is not None
            assert retrieved["price"] == 200.0

    def test_clear_expired(self):
        """Test clearing expired entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "cache.json")
            cache = PriceCache(cache_file=cache_file, ttl_hours=1)

            # Set up cache with mixed entries
            expired_time = (datetime.now() - timedelta(hours=2)).isoformat()
            valid_time = datetime.now().isoformat()

            cache._cache = {
                "Expired Hotel": {
                    "2026-03-01": {
                        "price": 100.0,
                        "provider": "Test",
                        "source": "test",
                        "timestamp": expired_time
                    }
                },
                "Valid Hotel": {
                    "2026-03-01": {
                        "price": 200.0,
                        "provider": "Test",
                        "source": "test",
                        "timestamp": valid_time
                    }
                }
            }

            removed = cache.clear_expired()

            assert removed == 1
            assert "Expired Hotel" not in cache._cache
            assert "Valid Hotel" in cache._cache

    def test_clear_all(self):
        """Test clearing entire cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "cache.json")
            cache = PriceCache(cache_file=cache_file, ttl_hours=24)

            result: PriceResult = {
                "price": 100.0,
                "provider": "Test",
                "source": "test",
                "cached": False
            }
            cache.set("Hotel A", "2026-03-01", result)
            cache.set("Hotel B", "2026-03-01", result)

            cache.clear_all()

            assert cache._cache == {}
            assert cache.get("Hotel A", "2026-03-01") is None

    def test_get_stats(self):
        """Test statistics calculation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "cache.json")
            cache = PriceCache(cache_file=cache_file, ttl_hours=1)

            expired_time = (datetime.now() - timedelta(hours=2)).isoformat()
            valid_time = datetime.now().isoformat()

            cache._cache = {
                "Hotel A": {
                    "2026-03-01": {
                        "price": 100.0,
                        "provider": "Test",
                        "source": "test",
                        "timestamp": valid_time
                    },
                    "2026-03-02": {
                        "price": 110.0,
                        "provider": "Test",
                        "source": "test",
                        "timestamp": expired_time
                    }
                },
                "Hotel B": {
                    "2026-03-01": {
                        "price": 200.0,
                        "provider": "Test",
                        "source": "test",
                        "timestamp": valid_time
                    }
                }
            }

            stats = cache.get_stats()

            assert stats["total_hotels"] == 2
            assert stats["total_entries"] == 3
            assert stats["expired_entries"] == 1
            assert stats["valid_entries"] == 2

    def test_creates_cache_directory(self):
        """Test that cache creates parent directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "subdir", "cache.json")
            cache = PriceCache(cache_file=cache_file, ttl_hours=24)

            result: PriceResult = {
                "price": 100.0,
                "provider": "Test",
                "source": "test",
                "cached": False
            }
            cache.set("Test Hotel", "2026-03-01", result)

            assert os.path.exists(cache_file)

    def test_handles_corrupt_cache_file(self):
        """Test that corrupt cache file is handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "cache.json")

            # Write corrupt JSON
            with open(cache_file, 'w') as f:
                f.write("not valid json {{{")

            # Should not raise, just start with empty cache
            cache = PriceCache(cache_file=cache_file, ttl_hours=24)
            assert cache._cache == {}

    def test_multiple_dates_same_hotel(self):
        """Test storing multiple dates for same hotel."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_file = os.path.join(tmpdir, "cache.json")
            cache = PriceCache(cache_file=cache_file, ttl_hours=24)

            result1: PriceResult = {
                "price": 100.0,
                "provider": "Test",
                "source": "test",
                "cached": False
            }
            result2: PriceResult = {
                "price": 150.0,
                "provider": "Test",
                "source": "test",
                "cached": False
            }

            cache.set("Test Hotel", "2026-03-01", result1)
            cache.set("Test Hotel", "2026-03-02", result2)

            retrieved1 = cache.get("Test Hotel", "2026-03-01")
            retrieved2 = cache.get("Test Hotel", "2026-03-02")

            assert retrieved1["price"] == 100.0
            assert retrieved2["price"] == 150.0
