"""
Base classes for price providers.

Defines the abstract interface that all price providers must implement.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, TypedDict


class PriceResult(TypedDict):
    """
    Standard result format for all price providers.

    Attributes:
        price: The hotel price in USD
        provider: Name of the booking provider (e.g., "Booking.com", "Hotels.com")
        source: Which price provider found this (e.g., "xotelo", "serpapi", "apify")
        cached: Whether this result came from cache
    """
    price: float
    provider: str
    source: str
    cached: bool


class PriceProvider(ABC):
    """
    Abstract base class for price providers.

    All price providers must implement get_price() and get_name() methods.
    """

    @abstractmethod
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
        Get hotel price for the specified dates and occupancy.

        Args:
            hotel_name: Display name of the hotel
            hotel_key: Provider-specific hotel key (may be None)
            check_in: Check-in date in YYYY-MM-DD format
            check_out: Check-out date in YYYY-MM-DD format
            rooms: Number of rooms (default: 1)
            adults: Adults per room (default: 2)
            **kwargs: Additional provider-specific parameters
                - booking_url: Direct Booking.com URL (for ApifyProvider)

        Returns:
            PriceResult if price found, None otherwise
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Get the provider name for logging and stats.

        Returns:
            Provider name (e.g., "xotelo", "serpapi", "apify")
        """
        pass

    def is_available(self) -> bool:
        """
        Check if this provider is properly configured and available.

        Override this method to check for required API keys, etc.

        Returns:
            True if provider is available, False otherwise
        """
        return True
