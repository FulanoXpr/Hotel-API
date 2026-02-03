"""
Apify Price Provider - Booking.com Scraper via Apify.

Uses two Apify actors:
- Fast Booking Scraper: For searches by hotel name (faster, cheaper)
- Full Booking Scraper: For direct hotel URLs (more accurate)

Free tier: $5/month in credits (~1,700 results).
"""
from __future__ import annotations

import logging
import os
import time
from typing import Optional

from .base import PriceProvider, PriceResult

logger = logging.getLogger(__name__)

# Try to import apify_client, but don't fail if not installed
try:
    from apify_client import ApifyClient
    APIFY_AVAILABLE = True
except ImportError:
    APIFY_AVAILABLE = False
    ApifyClient = None


class ApifyProvider(PriceProvider):
    """
    Price provider using Apify's Booking.com scrapers.

    Uses two different scrapers:
    - Fast Booking Scraper (voyager/fast-booking-scraper): For name searches
    - Full Booking Scraper (dtrungtin/booking-scraper): For direct hotel URLs

    The full scraper is more accurate when we have a booking_url, as the
    fast scraper cannot handle individual hotel URLs.

    This is the tertiary price source, used as a last resort when
    both Xotelo and SerpApi don't have prices. Requires an APIFY_TOKEN
    environment variable.

    Free tier: $5/month (~1,700 results)
    Note: Searches can take 30-60 seconds to complete.
    """

    # Apify actor IDs
    FAST_ACTOR_ID = "voyager/fast-booking-scraper"  # For name searches
    FULL_ACTOR_ID = "dtrungtin/booking-scraper"     # For direct URLs

    def __init__(
        self,
        api_token: Optional[str] = None,
        timeout_seconds: int = 120
    ) -> None:
        """
        Initialize the Apify provider.

        Args:
            api_token: Apify API token (defaults to APIFY_TOKEN env var)
            timeout_seconds: Maximum wait time for scraper (default: 120s)
        """
        self.api_token = api_token or os.getenv("APIFY_TOKEN", "")
        self.timeout_seconds = timeout_seconds
        self._client: Optional[ApifyClient] = None

    @property
    def client(self) -> Optional[ApifyClient]:
        """Lazy initialization of Apify client."""
        if self._client is None and self.is_available():
            self._client = ApifyClient(self.api_token)
        return self._client

    def get_price(
        self,
        hotel_name: str,
        hotel_key: Optional[str],
        check_in: str,
        check_out: str,
        rooms: int = 1,
        adults: int = 2,
        booking_url: Optional[str] = None
    ) -> Optional[PriceResult]:
        """
        Get hotel price from Booking.com via Apify scraper.

        If booking_url is provided, fetches that specific hotel directly.
        Otherwise, searches by hotel name + "Puerto Rico".

        Note: This method can take 30-60 seconds to complete.

        Args:
            hotel_name: Hotel name to search for
            hotel_key: Not used (Booking.com searches by name)
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            rooms: Number of rooms
            adults: Adults per room (total, not per room)
            booking_url: Direct Booking.com hotel URL (preferred)

        Returns:
            PriceResult if found, None otherwise
        """
        if not self.is_available():
            logger.debug("Apify: Not available (missing token or library)")
            return None

        try:
            # Choose actor and configure input based on whether we have a URL
            if booking_url:
                # Use FULL scraper for direct URLs - more accurate
                actor_id = self.FULL_ACTOR_ID
                run_input = {
                    "startUrls": [{"url": booking_url}],
                    "checkIn": check_in,
                    "checkOut": check_out,
                    "rooms": rooms,
                    "adults": adults,
                    "currency": "USD",
                    "language": "en-us",
                    "minScore": 0,
                    "maxPages": 1
                }
                logger.info("Apify: Using FULL scraper for direct URL: %s", hotel_name)
            else:
                # Use FAST scraper for name searches - cheaper
                actor_id = self.FAST_ACTOR_ID
                run_input = {
                    "search": f"{hotel_name}, Puerto Rico",
                    "checkIn": check_in,
                    "checkOut": check_out,
                    "rooms": rooms,
                    "adults": adults,
                    "currency": "USD",
                    "maxResults": 5,
                    "language": "en-us"
                }
                logger.info("Apify: Using FAST scraper for name search: %s", hotel_name)

            # Run the actor and wait for completion
            client = self.client
            if not client:
                return None

            run = client.actor(actor_id).call(
                run_input=run_input,
                timeout_secs=self.timeout_seconds,
                memory_mbytes=256  # Minimum memory to save credits
            )

            # Check if run succeeded
            if not run:
                logger.warning("Apify: Run failed for %s", hotel_name)
                return None

            # Get results from the dataset
            dataset_id = run.get("defaultDatasetId")
            if not dataset_id:
                logger.warning("Apify: No dataset returned for %s", hotel_name)
                return None

            items = list(client.dataset(dataset_id).iterate_items())
            if not items:
                logger.debug("Apify: No results for %s", hotel_name)
                return None

            # Find best matching result
            best_match = self._find_best_match(hotel_name, items)
            if not best_match:
                logger.debug("Apify: No matching hotel for %s", hotel_name)
                return None

            # Extract price
            price = self._extract_price(best_match)
            if price is None:
                logger.debug("Apify: No price in result for %s", hotel_name)
                return None

            return PriceResult(
                price=price,
                provider="Booking.com",
                source="apify",
                cached=False
            )

        except Exception as e:
            logger.error("Apify error for %s: %s", hotel_name, e)
            return None

    def _find_best_match(
        self,
        hotel_name: str,
        items: list
    ) -> Optional[dict]:
        """
        Find the best matching hotel by name similarity.

        Args:
            hotel_name: Target hotel name
            items: List of results from Apify

        Returns:
            Best matching item dict, or None
        """
        hotel_name_lower = hotel_name.lower()

        # First pass: exact or very close match
        for item in items:
            item_name = item.get("name", "").lower()
            if hotel_name_lower in item_name or item_name in hotel_name_lower:
                return item

        # Second pass: word overlap
        hotel_words = set(hotel_name_lower.split())
        best_score = 0
        best_item = None

        for item in items:
            item_name = item.get("name", "").lower()
            item_words = set(item_name.split())
            overlap = len(hotel_words & item_words)

            if overlap > best_score:
                best_score = overlap
                best_item = item

        # Require at least 2 words in common
        if best_score >= 2:
            return best_item

        return None

    def _extract_price(self, item: dict) -> Optional[float]:
        """
        Extract the price from a Booking.com result.

        Args:
            item: Result item from Apify

        Returns:
            Price as float, or None
        """
        # Try different price fields
        price_fields = [
            "price",
            "priceForDisplay",
            "rawPrice",
            "originalPrice",
            "priceNumeric"
        ]

        for field in price_fields:
            price_val = item.get(field)
            if price_val is not None:
                try:
                    # Handle string prices with currency symbols
                    if isinstance(price_val, str):
                        price_str = price_val.replace("$", "").replace(",", "")
                        price_str = price_str.replace("USD", "").strip()
                        return float(price_str)
                    return float(price_val)
                except (ValueError, TypeError):
                    continue

        # Try nested price object
        price_obj = item.get("priceBreakdown", {})
        if price_obj:
            total = price_obj.get("grossPrice", {}).get("value")
            if total:
                try:
                    return float(total)
                except (ValueError, TypeError):
                    pass

        return None

    def get_name(self) -> str:
        """Return provider name."""
        return "apify"

    def is_available(self) -> bool:
        """Check if Apify is properly configured."""
        if not APIFY_AVAILABLE:
            return False
        if not self.api_token:
            return False
        return True
