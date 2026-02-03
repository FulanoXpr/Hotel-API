"""
Amadeus Price Provider - Hotel Search via Amadeus Self-Service API.

Uses Amadeus Hotel Search API to find hotel prices.
Free tier: 500 calls/month (separate from other providers).

Requires registration at: https://developers.amadeus.com/register
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from .base import PriceProvider, PriceResult

logger = logging.getLogger(__name__)

# Try to import amadeus SDK, but don't fail if not installed
try:
    from amadeus import Client, ResponseError
    AMADEUS_AVAILABLE = True
except ImportError:
    AMADEUS_AVAILABLE = False
    Client = None
    ResponseError = Exception


class AmadeusProvider(PriceProvider):
    """
    Price provider using Amadeus Self-Service Hotel Search API.

    This provider uses a two-step process:
    1. Search for hotels in Puerto Rico by city code
    2. Get offers for matching hotel

    Requires AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET environment variables.

    Free tier: 500 API calls/month
    Rate limit: 10 requests/second
    """

    # Puerto Rico city codes for hotel search
    PR_CITY_CODES = ["SJU", "PSE", "BQN", "MAZ", "ARE"]  # San Juan, Ponce, Aguadilla, Mayaguez, Arecibo

    # Puerto Rico bounding box for geocode search (fallback)
    PR_LATITUDE = 18.2208
    PR_LONGITUDE = -66.5901

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        use_production: bool = False
    ) -> None:
        """
        Initialize the Amadeus provider.

        Args:
            client_id: Amadeus API client ID (defaults to AMADEUS_CLIENT_ID env var)
            client_secret: Amadeus API client secret (defaults to AMADEUS_CLIENT_SECRET env var)
            use_production: Use production API instead of test (default: False)
        """
        self.client_id = client_id or os.getenv("AMADEUS_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("AMADEUS_CLIENT_SECRET", "")
        self.use_production = use_production
        self._client: Optional[Client] = None
        self._hotel_cache: dict[str, str] = {}  # hotel_name -> amadeus_hotel_id

    @property
    def client(self) -> Optional[Client]:
        """Lazy initialization of Amadeus client with OAuth2."""
        if self._client is None and self.is_available():
            hostname = "production" if self.use_production else "test"
            self._client = Client(
                client_id=self.client_id,
                client_secret=self.client_secret,
                hostname=hostname
            )
        return self._client

    def get_price(
        self,
        hotel_name: str,
        hotel_key: Optional[str],
        check_in: str,
        check_out: str,
        rooms: int = 1,
        adults: int = 2,
        amadeus_id: Optional[str] = None,
        **kwargs
    ) -> Optional[PriceResult]:
        """
        Get hotel price from Amadeus Hotel Search API.

        Two-step process:
        1. Find hotel ID by searching Puerto Rico hotels and matching name
        2. Get hotel offers for that specific hotel

        Args:
            hotel_name: Hotel name to search for
            hotel_key: Xotelo hotel key (not used by Amadeus)
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            rooms: Number of rooms
            adults: Adults per room
            amadeus_id: Pre-mapped Amadeus hotel ID (e.g., 'SISJU523')

        Returns:
            PriceResult if found, None otherwise
        """
        if not self.is_available():
            logger.debug("Amadeus: Not available (missing credentials or library)")
            return None

        try:
            # Priority 1: Use provided amadeus_id from hotel_keys_db.json
            hotel_id = amadeus_id

            # Priority 2: Search for hotel ID by name
            if not hotel_id:
                hotel_id = self._find_hotel_id(hotel_name)

            if not hotel_id:
                logger.debug("Amadeus: Could not find hotel ID for %s", hotel_name)
                return None

            # Get hotel offers
            return self._get_hotel_offers(
                hotel_name=hotel_name,
                hotel_id=hotel_id,
                check_in=check_in,
                check_out=check_out,
                rooms=rooms,
                adults=adults
            )

        except ResponseError as e:
            logger.error("Amadeus API error for %s: %s", hotel_name, e)
            return None
        except Exception as e:
            logger.error("Amadeus error for %s: %s", hotel_name, e)
            return None

    def _find_hotel_id(self, hotel_name: str) -> Optional[str]:
        """
        Find Amadeus hotel ID by searching Puerto Rico hotels.

        Searches by city code and matches hotel name.

        Args:
            hotel_name: Hotel name to find

        Returns:
            Amadeus hotel ID if found, None otherwise
        """
        # Check cache first
        cache_key = hotel_name.lower()
        if cache_key in self._hotel_cache:
            return self._hotel_cache[cache_key]

        client = self.client
        if not client:
            return None

        # Try each PR city code
        for city_code in self.PR_CITY_CODES:
            try:
                response = client.reference_data.locations.hotels.by_city.get(
                    cityCode=city_code
                )

                if not response.data:
                    continue

                # Find best match by name
                match = self._find_best_match(hotel_name, response.data)
                if match:
                    hotel_id = match.get("hotelId")
                    if hotel_id:
                        self._hotel_cache[cache_key] = hotel_id
                        logger.info("Amadeus: Found hotel ID %s for %s", hotel_id, hotel_name)
                        return hotel_id

            except ResponseError as e:
                logger.debug("Amadeus: Error searching city %s: %s", city_code, e)
                continue

        # Fallback: search by geocode (covers all PR)
        try:
            response = client.reference_data.locations.hotels.by_geocode.get(
                latitude=self.PR_LATITUDE,
                longitude=self.PR_LONGITUDE,
                radius=200,
                radiusUnit="KM"
            )

            if response.data:
                match = self._find_best_match(hotel_name, response.data)
                if match:
                    hotel_id = match.get("hotelId")
                    if hotel_id:
                        self._hotel_cache[cache_key] = hotel_id
                        logger.info("Amadeus: Found hotel ID %s via geocode for %s", hotel_id, hotel_name)
                        return hotel_id

        except ResponseError as e:
            logger.debug("Amadeus: Error in geocode search: %s", e)

        return None

    def _get_hotel_offers(
        self,
        hotel_name: str,
        hotel_id: str,
        check_in: str,
        check_out: str,
        rooms: int,
        adults: int
    ) -> Optional[PriceResult]:
        """
        Get hotel offers for a specific hotel ID.

        Args:
            hotel_name: Hotel name (for logging)
            hotel_id: Amadeus hotel ID
            check_in: Check-in date
            check_out: Check-out date
            rooms: Number of rooms
            adults: Number of adults

        Returns:
            PriceResult if offers found, None otherwise
        """
        client = self.client
        if not client:
            return None

        try:
            response = client.shopping.hotel_offers_search.get(
                hotelIds=hotel_id,
                checkInDate=check_in,
                checkOutDate=check_out,
                roomQuantity=rooms,
                adults=adults,
                currency="USD"
            )

            if not response.data:
                logger.debug("Amadeus: No offers for hotel %s", hotel_name)
                return None

            # Extract best price from offers
            price, provider = self._extract_best_price(response.data)
            if price is None:
                logger.debug("Amadeus: No valid price in offers for %s", hotel_name)
                return None

            return PriceResult(
                price=price,
                provider=provider,
                source="amadeus",
                cached=False
            )

        except ResponseError as e:
            # Common error: hotel not available for dates
            if "HOTEL NOT FOUND" in str(e) or "NO OFFER" in str(e).upper():
                logger.debug("Amadeus: No availability for %s on requested dates", hotel_name)
            else:
                logger.warning("Amadeus: Error getting offers for %s: %s", hotel_name, e)
            return None

    def _find_best_match(
        self,
        hotel_name: str,
        hotels: list
    ) -> Optional[dict]:
        """
        Find the best matching hotel by name similarity.

        Args:
            hotel_name: Target hotel name
            hotels: List of hotels from Amadeus

        Returns:
            Best matching hotel dict, or None
        """
        hotel_name_lower = hotel_name.lower()
        hotel_name_words = set(hotel_name_lower.split())

        best_match = None
        best_score = 0

        for hotel in hotels:
            # Get hotel name from response
            name = hotel.get("name", "")
            if not name:
                # Try nested structure
                name = hotel.get("hotel", {}).get("name", "")

            if not name:
                continue

            name_lower = name.lower()

            # Exact match
            if hotel_name_lower == name_lower:
                return hotel

            # Substring match
            if hotel_name_lower in name_lower or name_lower in hotel_name_lower:
                return hotel

            # Word overlap scoring
            name_words = set(name_lower.split())
            overlap = len(hotel_name_words & name_words)

            # Bonus for key words
            key_words = {"hotel", "resort", "inn", "suites", "hilton", "marriott", "hyatt", "sheraton"}
            meaningful_overlap = len((hotel_name_words & name_words) - key_words)

            score = overlap + meaningful_overlap
            if score > best_score:
                best_score = score
                best_match = hotel

        # Require minimum overlap
        if best_score >= 2:
            return best_match

        return None

    def _extract_best_price(self, offers_data: list) -> tuple[Optional[float], str]:
        """
        Extract the lowest price from hotel offers.

        Args:
            offers_data: List of hotel offers from Amadeus

        Returns:
            Tuple of (price, provider_name) or (None, "")
        """
        best_price = None
        provider = "Amadeus"

        for hotel_data in offers_data:
            offers = hotel_data.get("offers", [])
            hotel_info = hotel_data.get("hotel", {})

            for offer in offers:
                price_info = offer.get("price", {})
                total = price_info.get("total")

                if total:
                    try:
                        price = float(total)
                        if best_price is None or price < best_price:
                            best_price = price
                            # Try to get provider/chain name
                            chain = hotel_info.get("chainCode", "")
                            if chain:
                                provider = f"Amadeus ({chain})"
                    except (ValueError, TypeError):
                        continue

        return best_price, provider

    def get_name(self) -> str:
        """Return provider name."""
        return "amadeus"

    def is_available(self) -> bool:
        """Check if Amadeus is properly configured."""
        if not AMADEUS_AVAILABLE:
            return False
        if not self.client_id or not self.client_secret:
            return False
        return True
