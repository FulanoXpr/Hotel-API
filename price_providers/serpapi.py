"""
SerpApi Price Provider - Google Hotels via SerpApi.

Uses SerpApi's Google Hotels engine to search for hotel prices.
Free tier: 250 searches/month.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from .base import PriceProvider, PriceResult

logger = logging.getLogger(__name__)

# Try to import serpapi, but don't fail if not installed
try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False
    GoogleSearch = None


class SerpApiProvider(PriceProvider):
    """
    Price provider using SerpApi's Google Hotels engine.

    This is the secondary price source, used when Xotelo doesn't
    have a price. Requires a SERPAPI_KEY environment variable.

    Free tier: 250 searches/month
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Initialize the SerpApi provider.

        Args:
            api_key: SerpApi API key (defaults to SERPAPI_KEY env var)
        """
        self.api_key = api_key or os.getenv("SERPAPI_KEY", "")

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
        Get hotel price from Google Hotels via SerpApi.

        Searches by hotel name + "Puerto Rico" and extracts the
        lowest available price.

        Args:
            hotel_name: Hotel name to search for
            hotel_key: Not used (Google Hotels searches by name)
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            rooms: Number of rooms
            adults: Adults per room

        Returns:
            PriceResult if found, None otherwise
        """
        if not self.is_available():
            logger.debug("SerpApi: Not available (missing API key or library)")
            return None

        try:
            params = {
                "engine": "google_hotels",
                "q": f"{hotel_name} Puerto Rico",
                "check_in_date": check_in,
                "check_out_date": check_out,
                "adults": adults,
                "currency": "USD",
                "api_key": self.api_key
            }

            search = GoogleSearch(params)
            results = search.get_dict()

            # Check for errors
            if "error" in results:
                logger.warning("SerpApi error: %s", results["error"])
                return None

            # Extract properties from results
            properties = results.get("properties", [])
            if not properties:
                logger.debug("SerpApi: No properties found for %s", hotel_name)
                return None

            # Find the best match by name similarity
            best_match = self._find_best_match(hotel_name, properties)
            if not best_match:
                logger.debug("SerpApi: No matching hotel found for %s", hotel_name)
                return None

            # Extract price
            price = self._extract_price(best_match)
            if price is None:
                logger.debug("SerpApi: No price in result for %s", hotel_name)
                return None

            # Get provider name from the result
            provider = best_match.get("rate", {}).get("source", "Google Hotels")

            return PriceResult(
                price=price,
                provider=provider,
                source="serpapi",
                cached=False
            )

        except Exception as e:
            logger.error("SerpApi error for %s: %s", hotel_name, e)
            return None

    def _find_best_match(
        self,
        hotel_name: str,
        properties: list
    ) -> Optional[dict]:
        """
        Find the best matching property by name similarity.

        Args:
            hotel_name: Target hotel name
            properties: List of properties from SerpApi

        Returns:
            Best matching property dict, or None
        """
        hotel_name_lower = hotel_name.lower()

        # First pass: exact or very close match
        for prop in properties:
            prop_name = prop.get("name", "").lower()
            if hotel_name_lower in prop_name or prop_name in hotel_name_lower:
                return prop

        # Second pass: word overlap
        hotel_words = set(hotel_name_lower.split())
        best_score = 0
        best_prop = None

        for prop in properties:
            prop_name = prop.get("name", "").lower()
            prop_words = set(prop_name.split())
            overlap = len(hotel_words & prop_words)

            if overlap > best_score:
                best_score = overlap
                best_prop = prop

        # Require at least 2 words in common for a match
        if best_score >= 2:
            return best_prop

        return None

    def _extract_price(self, property_data: dict) -> Optional[float]:
        """
        Extract the price from a property result.

        Args:
            property_data: Property dict from SerpApi

        Returns:
            Price as float, or None
        """
        # Try different price locations in the response
        rate = property_data.get("rate_per_night", {})
        if rate:
            lowest = rate.get("lowest")
            if lowest:
                # Remove currency symbol and convert
                price_str = str(lowest).replace("$", "").replace(",", "")
                try:
                    return float(price_str)
                except ValueError:
                    pass

        # Try total price
        total = property_data.get("total_rate", {}).get("lowest")
        if total:
            price_str = str(total).replace("$", "").replace(",", "")
            try:
                return float(price_str)
            except ValueError:
                pass

        # Try prices array
        prices = property_data.get("prices", [])
        if prices:
            for price_item in prices:
                rate_str = price_item.get("rate_per_night", "")
                if rate_str:
                    price_str = str(rate_str).replace("$", "").replace(",", "")
                    try:
                        return float(price_str)
                    except ValueError:
                        continue

        return None

    def get_name(self) -> str:
        """Return provider name."""
        return "serpapi"

    def is_available(self) -> bool:
        """Check if SerpApi is properly configured."""
        if not SERPAPI_AVAILABLE:
            return False
        if not self.api_key:
            return False
        return True
