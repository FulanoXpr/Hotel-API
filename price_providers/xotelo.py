"""
Xotelo Price Provider - Wrapper for the existing XoteloAPI.

This is the primary price source, using the free Xotelo API
that aggregates prices from TripAdvisor.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from .base import PriceProvider, PriceResult

# Import from parent directory
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from xotelo_api import XoteloAPI, get_client

logger = logging.getLogger(__name__)


class XoteloProvider(PriceProvider):
    """
    Price provider using the Xotelo API (TripAdvisor-based).

    This is the primary price source. It requires a hotel_key to
    fetch prices, but offers the best coverage for hotels already
    mapped in hotel_keys_db.json.
    """

    def __init__(self, api: Optional[XoteloAPI] = None) -> None:
        """
        Initialize the Xotelo provider.

        Args:
            api: Optional XoteloAPI instance (uses default if not provided)
        """
        self.api = api or get_client()
        self._multi_date_ranges: Optional[List[dict]] = None

    def set_multi_date_ranges(self, date_ranges: List[dict]) -> None:
        """
        Set multiple date ranges to try for better coverage.

        Args:
            date_ranges: List of dicts with 'label', 'chk_in', 'chk_out' keys
        """
        self._multi_date_ranges = date_ranges

    def get_price(
        self,
        hotel_name: str,
        hotel_key: Optional[str],
        check_in: str,
        check_out: str,
        rooms: int = 1,
        adults: int = 2,
        **kwargs
    ) -> Optional[PriceResult]:
        """
        Get hotel price from Xotelo API.

        Requires a valid hotel_key. If multi_date_ranges is set,
        will try each date range until a price is found.

        Args:
            hotel_name: Hotel name (for logging)
            hotel_key: Xotelo hotel key (required)
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            rooms: Number of rooms
            adults: Adults per room

        Returns:
            PriceResult if found, None otherwise
        """
        if not hotel_key:
            logger.debug("Xotelo: No hotel key for %s, skipping", hotel_name)
            return None

        # If multi-date mode is enabled, try each date range
        if self._multi_date_ranges:
            return self._try_multiple_dates(hotel_key, rooms, adults)

        # Single date mode
        rate_data = self.api.get_rates(
            hotel_key, check_in, check_out, rooms, adults
        )

        if not rate_data:
            logger.debug("Xotelo: No price for %s", hotel_name)
            return None

        return PriceResult(
            price=rate_data['rate'],
            provider=rate_data['provider'],
            source="xotelo",
            cached=False
        )

    def _try_multiple_dates(
        self,
        hotel_key: str,
        rooms: int,
        adults: int
    ) -> Optional[PriceResult]:
        """
        Try multiple date ranges until a price is found.

        Args:
            hotel_key: Xotelo hotel key
            rooms: Number of rooms
            adults: Adults per room

        Returns:
            PriceResult if found, None otherwise
        """
        if not self._multi_date_ranges:
            return None

        for date_range in self._multi_date_ranges:
            rate_data = self.api.get_rates(
                hotel_key,
                date_range['chk_in'],
                date_range['chk_out'],
                rooms,
                adults
            )
            if rate_data:
                logger.debug(
                    "Xotelo: Found price via %s date range",
                    date_range['label']
                )
                return PriceResult(
                    price=rate_data['rate'],
                    provider=rate_data['provider'],
                    source=f"xotelo:{date_range['label']}",
                    cached=False
                )
            self.api.wait()

        return None

    def get_name(self) -> str:
        """Return provider name."""
        return "xotelo"

    def is_available(self) -> bool:
        """Xotelo is always available (no API key required)."""
        return True
