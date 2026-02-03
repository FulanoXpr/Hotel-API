"""
Xotelo API Client - Shared module for interacting with the Xotelo API.
Provides methods for searching hotels, getting rates, and listing hotels by location.

Note: The /search endpoint now requires RapidAPI subscription.
This module implements a local cache workaround using the free /list endpoint.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypedDict

import requests

import config

# Cache file for hotel list (workaround for /search API restriction)
HOTEL_CACHE_FILE = os.getenv("XOTELO_HOTEL_CACHE", "xotelo_hotels_cache.json")

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

        First tries the API /search endpoint. If it fails (401 - RapidAPI required),
        falls back to local cache search using fuzzy matching.

        Args:
            query: Hotel name to search for
            location_type: Type of location (default: 'accommodation')

        Returns:
            HotelInfo with key, name, and location, or None if not found
        """
        # Try API search first
        params = {
            "query": query,
            "location_type": location_type
        }

        data = self._request("/search", params)
        if data:
            result = data.get('result', {})
            hotels = result.get('list', [])

            if hotels:
                hotel = hotels[0]
                return HotelInfo(
                    key=hotel.get('hotel_key', ''),
                    name=hotel.get('name', ''),
                    location=hotel.get('short_place_name', '')
                )

        # Fallback to local cache search
        logger.info("API /search unavailable, using local cache for: %s", query)
        return self.search_hotel_local(query)

    def search_hotel_local(self, query: str, threshold: float = 0.4) -> Optional[HotelInfo]:
        """
        Search for a hotel in the local cache using fuzzy matching.

        Args:
            query: Hotel name to search for
            threshold: Minimum similarity score (0.0-1.0) to consider a match

        Returns:
            HotelInfo with key and name, or None if not found
        """
        cache = self._load_hotel_cache()
        if not cache:
            logger.warning("Hotel cache is empty. Run refresh_hotel_cache() first.")
            return None

        query_normalized = self._normalize_name(query)
        best_match = None
        best_score = 0.0

        for hotel in cache:
            hotel_name = hotel.get('name', '')
            hotel_normalized = self._normalize_name(hotel_name)

            score = self._fuzzy_match_score(query_normalized, hotel_normalized)

            if score > best_score:
                best_score = score
                best_match = hotel

        if best_match and best_score >= threshold:
            logger.info("Local match: '%s' -> '%s' (score: %.2f)",
                       query, best_match.get('name'), best_score)
            return HotelInfo(
                key=best_match.get('key', ''),
                name=best_match.get('name', ''),
                location='Puerto Rico'
            )

        logger.info("No local match for '%s' (best score: %.2f)", query, best_score)
        return None

    def _normalize_name(self, name: str) -> str:
        """Normalize hotel name for comparison."""
        # Lowercase
        name = name.lower()
        # Remove common suffixes/prefixes
        remove_patterns = [
            r'\s*-\s*puerto rico$',
            r'\s*,\s*puerto rico$',
            r'\s*hotel$',
            r'\s*resort$',
            r'\s*&\s*spa$',
            r'\s*and\s*spa$',
            r'^the\s+',
            r'^hotel\s+',
        ]
        for pattern in remove_patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        # Remove special characters, keep alphanumeric and spaces
        name = re.sub(r'[^\w\s]', '', name)
        # Normalize whitespace
        name = ' '.join(name.split())
        return name

    def _fuzzy_match_score(self, query: str, target: str) -> float:
        """
        Calculate fuzzy match score between two strings.

        Uses a combination of:
        - Word overlap (Jaccard similarity)
        - Substring matching
        - Character-level similarity

        Returns:
            Score from 0.0 to 1.0
        """
        if not query or not target:
            return 0.0

        # Exact match
        if query == target:
            return 1.0

        # Word-based Jaccard similarity
        query_words = set(query.split())
        target_words = set(target.split())

        if query_words and target_words:
            intersection = len(query_words & target_words)
            union = len(query_words | target_words)
            jaccard = intersection / union if union > 0 else 0
        else:
            jaccard = 0

        # Substring bonus
        substring_bonus = 0.0
        if query in target or target in query:
            substring_bonus = 0.3

        # Character-level similarity (simple ratio)
        longer = max(len(query), len(target))
        if longer > 0:
            # Count matching characters in order
            matches = 0
            target_chars = list(target)
            for char in query:
                if char in target_chars:
                    target_chars.remove(char)
                    matches += 1
            char_ratio = matches / longer
        else:
            char_ratio = 0

        # Weighted combination
        score = (jaccard * 0.5) + (char_ratio * 0.3) + substring_bonus
        return min(score, 1.0)

    def _load_hotel_cache(self) -> List[Dict[str, Any]]:
        """Load hotel cache from file."""
        cache_path = Path(HOTEL_CACHE_FILE)
        if not cache_path.exists():
            return []

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('hotels', [])
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Error loading hotel cache: %s", e)
            return []

    def _save_hotel_cache(self, hotels: List[Dict[str, Any]]) -> None:
        """Save hotel cache to file."""
        cache_path = Path(HOTEL_CACHE_FILE)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'hotels': hotels,
                    'count': len(hotels),
                    'updated': time.strftime('%Y-%m-%d %H:%M:%S')
                }, f, ensure_ascii=False, indent=2)
            logger.info("Saved %d hotels to cache", len(hotels))
        except IOError as e:
            logger.error("Error saving hotel cache: %s", e)

    def refresh_hotel_cache(
        self,
        location_key: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> int:
        """
        Refresh the local hotel cache from the API.

        Fetches all hotels from the /list endpoint and saves to local cache.
        This is a workaround for the /search endpoint requiring RapidAPI.

        Args:
            location_key: Location key (defaults to Puerto Rico)
            progress_callback: Optional callback(current, total) for progress updates

        Returns:
            Number of hotels cached
        """
        location = location_key or config.LOCATION_KEY
        all_hotels = []
        offset = 0
        limit = 100  # API max per request

        # First request to get total count
        hotels, total_count = self.list_hotels(location_key=location, limit=limit, offset=0)
        if not hotels:
            logger.error("Failed to fetch hotels from API")
            return 0

        all_hotels.extend(hotels)
        if progress_callback:
            progress_callback(len(all_hotels), total_count)

        # Fetch remaining pages
        while len(all_hotels) < total_count:
            offset += limit
            self.wait()  # Rate limiting

            hotels, _ = self.list_hotels(location_key=location, limit=limit, offset=offset)
            if not hotels:
                break

            all_hotels.extend(hotels)
            if progress_callback:
                progress_callback(len(all_hotels), total_count)

        # Save to cache
        self._save_hotel_cache(all_hotels)
        return len(all_hotels)

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the hotel cache."""
        cache_path = Path(HOTEL_CACHE_FILE)
        if not cache_path.exists():
            return {'exists': False, 'count': 0, 'updated': None}

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    'exists': True,
                    'count': data.get('count', 0),
                    'updated': data.get('updated'),
                    'path': str(cache_path.absolute())
                }
        except (json.JSONDecodeError, IOError):
            return {'exists': False, 'count': 0, 'updated': None}

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
