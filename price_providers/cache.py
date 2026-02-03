"""
Price Cache - JSON-based caching for hotel prices.

Implements a simple file-based cache with TTL (Time To Live)
to reduce API calls on subsequent runs.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from .base import PriceResult

logger = logging.getLogger(__name__)


class PriceCache:
    """
    File-based cache for hotel prices with TTL support.

    Stores prices in a JSON file with timestamps, automatically
    expiring entries after the configured TTL.

    Cache structure:
    {
        "Hotel Name": {
            "2026-03-01": {
                "price": 150.0,
                "provider": "Booking.com",
                "source": "serpapi",
                "timestamp": "2026-02-03T10:30:00"
            }
        }
    }
    """

    def __init__(
        self,
        cache_file: str = "cache/prices_cache.json",
        ttl_hours: int = 24
    ) -> None:
        """
        Initialize the price cache.

        Args:
            cache_file: Path to the cache JSON file
            ttl_hours: Time To Live in hours (default: 24h)
        """
        self.cache_file = cache_file
        self.ttl = timedelta(hours=ttl_hours)
        self._cache: dict = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cache from file if it exists."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
                logger.debug("Loaded %d hotels from cache", len(self._cache))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load cache: %s", e)
                self._cache = {}
        else:
            self._cache = {}

    def _save_cache(self) -> None:
        """Save cache to file."""
        # Ensure directory exists
        cache_dir = os.path.dirname(self.cache_file)
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)

        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except OSError as e:
            logger.error("Failed to save cache: %s", e)

    def _is_expired(self, timestamp_str: str) -> bool:
        """
        Check if a timestamp is expired based on TTL.

        Args:
            timestamp_str: ISO format timestamp

        Returns:
            True if expired, False otherwise
        """
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            age = datetime.now() - timestamp
            return age > self.ttl
        except (ValueError, TypeError):
            return True

    def get(
        self,
        hotel_name: str,
        check_in: str
    ) -> Optional[PriceResult]:
        """
        Get cached price for a hotel and date.

        Args:
            hotel_name: Hotel name
            check_in: Check-in date (YYYY-MM-DD)

        Returns:
            PriceResult with cached=True if found and not expired, None otherwise
        """
        hotel_cache = self._cache.get(hotel_name)
        if not hotel_cache:
            return None

        date_cache = hotel_cache.get(check_in)
        if not date_cache:
            return None

        # Check expiration
        timestamp = date_cache.get("timestamp")
        if self._is_expired(timestamp):
            logger.debug("Cache expired for %s on %s", hotel_name, check_in)
            return None

        return PriceResult(
            price=date_cache["price"],
            provider=date_cache["provider"],
            source=date_cache["source"],
            cached=True
        )

    def set(
        self,
        hotel_name: str,
        check_in: str,
        result: PriceResult
    ) -> None:
        """
        Cache a price result.

        Args:
            hotel_name: Hotel name
            check_in: Check-in date (YYYY-MM-DD)
            result: PriceResult to cache
        """
        if hotel_name not in self._cache:
            self._cache[hotel_name] = {}

        self._cache[hotel_name][check_in] = {
            "price": result["price"],
            "provider": result["provider"],
            "source": result["source"],
            "timestamp": datetime.now().isoformat()
        }

        self._save_cache()

    def clear_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        removed = 0
        hotels_to_remove = []

        for hotel_name, hotel_cache in self._cache.items():
            dates_to_remove = []
            for check_in, data in hotel_cache.items():
                if self._is_expired(data.get("timestamp", "")):
                    dates_to_remove.append(check_in)
                    removed += 1

            for date in dates_to_remove:
                del hotel_cache[date]

            if not hotel_cache:
                hotels_to_remove.append(hotel_name)

        for hotel in hotels_to_remove:
            del self._cache[hotel]

        if removed > 0:
            self._save_cache()
            logger.info("Cleared %d expired cache entries", removed)

        return removed

    def clear_all(self) -> None:
        """Clear entire cache."""
        self._cache = {}
        self._save_cache()
        logger.info("Cache cleared")

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with total_hotels, total_entries, expired_entries
        """
        total_entries = 0
        expired_entries = 0

        for hotel_cache in self._cache.values():
            for data in hotel_cache.values():
                total_entries += 1
                if self._is_expired(data.get("timestamp", "")):
                    expired_entries += 1

        return {
            "total_hotels": len(self._cache),
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "valid_entries": total_entries - expired_entries
        }
