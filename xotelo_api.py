"""
Xotelo API Client - Shared module for interacting with the Xotelo API.
Provides methods for searching hotels, getting rates, and listing hotels by location.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple, TypedDict

import requests

import config

logger = logging.getLogger(__name__)


class RateInfo(TypedDict):
    """Type definition for rate information."""
    rate: float
    provider: str
    code: str


class HotelInfo(TypedDict):
    """Type definition for hotel search result."""
    key: str
    name: str
    location: str


class HotelListItem(TypedDict, total=False):
    """Type definition for hotel list item."""
    name: str
    key: str
    url: str
    accommodation_type: str
    rating: Optional[float]
    review_count: Optional[int]


class XoteloAPI:
    """Client for interacting with the Xotelo API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        delay: Optional[float] = None,
        max_retries: Optional[int] = None
    ) -> None:
        """
        Initialize the Xotelo API client.

        Args:
            base_url: API base URL (defaults to config.BASE_URL)
            timeout: Request timeout in seconds (defaults to config.TIMEOUT)
            delay: Delay between requests in seconds (defaults to config.REQUEST_DELAY)
            max_retries: Maximum number of retries on failure (defaults to config.MAX_RETRIES)
        """
        self.base_url = base_url or config.BASE_URL
        self.timeout = timeout or config.TIMEOUT
        self.delay = delay or config.REQUEST_DELAY
        self.max_retries = max_retries or config.MAX_RETRIES
        self.session = requests.Session()

    def _request(
        self,
        endpoint: str,
        params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Make a request to the API with retry logic.

        Args:
            endpoint: API endpoint (e.g., '/rates', '/search', '/list')
            params: Query parameters

        Returns:
            API response data or None on failure
        """
        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()

                if data.get('error'):
                    logger.warning("API returned error: %s", data.get('error'))
                    return None

                return data

            except requests.exceptions.Timeout:
                logger.warning("Request timeout (attempt %d/%d)", attempt + 1, self.max_retries)
                if attempt < self.max_retries - 1:
                    time.sleep(config.RETRY_DELAY)
                    continue
                return None

            except requests.exceptions.RequestException as e:
                logger.error("Request failed: %s", e)
                if attempt < self.max_retries - 1:
                    time.sleep(config.RETRY_DELAY)
                    continue
                return None

        return None

    def get_rates(
        self,
        hotel_key: str,
        chk_in: str,
        chk_out: str,
        rooms: int = 1,
        adults: int = 2
    ) -> Optional[RateInfo]:
        """
        Get hotel rates for specific dates and occupancy.

        Args:
            hotel_key: Xotelo hotel key (e.g., 'g147319-d1234567')
            chk_in: Check-in date (YYYY-MM-DD)
            chk_out: Check-out date (YYYY-MM-DD)
            rooms: Number of rooms (default: 1)
            adults: Number of adults per room (default: 2)

        Returns:
            RateInfo with lowest rate, provider, and code, or None if no rates available
        """
        params = {
            "hotel_key": hotel_key,
            "chk_in": chk_in,
            "chk_out": chk_out,
            "rooms": rooms,
            "adults": adults
        }

        data = self._request("/rates", params)
        if not data:
            return None

        result = data.get('result', {})
        rates = result.get('rates', [])

        if not rates:
            return None

        valid_rates = []
        for rate in rates:
            raw_rate = rate.get('rate')
            try:
                numeric_rate = float(raw_rate)
            except (TypeError, ValueError):
                continue
            valid_rates.append((numeric_rate, rate))

        if not valid_rates:
            return None

        lowest_numeric_rate, lowest_rate = min(valid_rates, key=lambda item: item[0])

        return RateInfo(
            rate=lowest_numeric_rate,
            provider=lowest_rate.get('name', 'Unknown'),
            code=lowest_rate.get('code', '')
        )

    def search_hotel(
        self,
        query: str,
        location_type: str = "accommodation"
    ) -> Optional[HotelInfo]:
        """
        Search for a hotel by name.

        Args:
            query: Hotel name to search for
            location_type: Type of location (default: 'accommodation')

        Returns:
            HotelInfo with key, name, and location, or None if not found
        """
        params = {
            "query": query,
            "location_type": location_type
        }

        data = self._request("/search", params)
        if not data:
            return None

        result = data.get('result', {})
        hotels = result.get('list', [])

        if not hotels:
            return None

        hotel = hotels[0]
        return HotelInfo(
            key=hotel.get('hotel_key', ''),
            name=hotel.get('name', ''),
            location=hotel.get('short_place_name', '')
        )

    def list_hotels(
        self,
        location_key: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        sort: str = "best_value"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get list of hotels for a location.

        Args:
            location_key: Location key (defaults to Puerto Rico)
            limit: Maximum number of results (default: 100)
            offset: Starting offset for pagination (default: 0)
            sort: Sort order (default: 'best_value')

        Returns:
            Tuple of (list of hotels, total count)
        """
        params = {
            "location_key": location_key or config.LOCATION_KEY,
            "limit": limit,
            "offset": offset,
            "sort": sort
        }

        data = self._request("/list", params)
        if not data:
            return [], 0

        result = data.get('result', {})
        hotels = result.get('list', [])
        total_count = result.get('total_count', 0)

        return hotels, total_count

    def wait(self) -> None:
        """Wait for the configured delay between requests."""
        time.sleep(self.delay)


# Default client instance for convenience
_default_client: Optional[XoteloAPI] = None


def get_client() -> XoteloAPI:
    """Get or create the default API client instance."""
    global _default_client
    if _default_client is None:
        _default_client = XoteloAPI()
    return _default_client
