"""
Amadeus ID Finder - Maps hotels to valid Amadeus hotel IDs.

Searches the Amadeus hotel database and validates that IDs return offers.
Saves validated IDs to hotel_keys_db.json for use in the cascade pipeline.

Usage:
    python amadeus_id_finder.py                     # Find IDs for all hotels
    python amadeus_id_finder.py --hotel "Hotel"    # Find ID for specific hotel
    python amadeus_id_finder.py --limit 10          # Limit to first N hotels
    python amadeus_id_finder.py --validate-only     # Only validate existing IDs
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import config

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

HOTEL_KEYS_DB = config.HOTEL_KEYS_DB

# Try to import Amadeus SDK
try:
    from amadeus import Client, ResponseError
    AMADEUS_AVAILABLE = True
except ImportError:
    AMADEUS_AVAILABLE = False
    logger.error("Amadeus SDK not installed. Run: pip install amadeus")


def normalize_name(name: str) -> set:
    """Normalize hotel name to set of keywords for matching."""
    name = re.sub(r'[^a-zA-Z0-9\s]', '', name.lower())
    words = set(name.split())
    stop_words = {'the', 'a', 'an', 'hotel', 'resort', 'and', 'by', 'at', 'de', 'la', 'el', 'puerto', 'rico', 'pr'}
    return words - stop_words


def calculate_match_score(name1: str, name2: str) -> float:
    """Calculate similarity score between two hotel names."""
    words1 = normalize_name(name1)
    words2 = normalize_name(name2)

    if not words1 or not words2:
        return 0.0

    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0


class AmadeusIdFinder:
    """Finds and validates Amadeus hotel IDs for PRTC hotels."""

    # Puerto Rico city codes
    PR_CITY_CODES = ["SJU", "PSE", "BQN", "MAZ", "ARE", "VQS", "CPX"]

    def __init__(self) -> None:
        """Initialize the finder with Amadeus client."""
        self.client_id = os.getenv("AMADEUS_CLIENT_ID", "")
        self.client_secret = os.getenv("AMADEUS_CLIENT_SECRET", "")
        self._client: Optional[Client] = None
        self._amadeus_hotels: List[Dict] = []

    @property
    def client(self) -> Optional[Client]:
        """Lazy initialization of Amadeus client."""
        if self._client is None and self.is_available():
            self._client = Client(
                client_id=self.client_id,
                client_secret=self.client_secret,
                hostname='test'  # Use test environment
            )
        return self._client

    def is_available(self) -> bool:
        """Check if Amadeus is properly configured."""
        if not AMADEUS_AVAILABLE:
            return False
        return bool(self.client_id and self.client_secret)

    def load_amadeus_hotels(self) -> List[Dict]:
        """Load all hotels from Amadeus for Puerto Rico."""
        if self._amadeus_hotels:
            return self._amadeus_hotels

        client = self.client
        if not client:
            return []

        all_hotels = []

        for city_code in self.PR_CITY_CODES:
            try:
                response = client.reference_data.locations.hotels.by_city.get(
                    cityCode=city_code
                )
                if response.data:
                    for hotel in response.data:
                        hotel['_city_code'] = city_code
                    all_hotels.extend(response.data)
                    logger.info("Loaded %d hotels from %s", len(response.data), city_code)
            except ResponseError as e:
                logger.warning("Error loading hotels from %s: %s", city_code, e)

        # Remove duplicates by hotelId
        seen = set()
        unique_hotels = []
        for hotel in all_hotels:
            hid = hotel.get('hotelId')
            if hid and hid not in seen:
                seen.add(hid)
                unique_hotels.append(hotel)

        self._amadeus_hotels = unique_hotels
        logger.info("Total unique Amadeus hotels loaded: %d", len(unique_hotels))
        return self._amadeus_hotels

    def find_matching_hotel(self, hotel_name: str) -> Optional[Tuple[str, str, float]]:
        """
        Find best matching Amadeus hotel for a given hotel name.

        Returns:
            Tuple of (hotel_id, amadeus_name, score) or None
        """
        hotels = self.load_amadeus_hotels()
        if not hotels:
            return None

        best_match = None
        best_score = 0.0

        for hotel in hotels:
            amadeus_name = hotel.get('name', '')
            if not amadeus_name:
                continue

            score = calculate_match_score(hotel_name, amadeus_name)

            if score > best_score:
                best_score = score
                best_match = (hotel.get('hotelId'), amadeus_name, score)

        # Require minimum 40% match
        if best_score >= 0.4:
            return best_match

        return None

    def validate_hotel_id(self, hotel_id: str, hotel_name: str) -> bool:
        """
        Validate that a hotel ID returns offers.

        Args:
            hotel_id: Amadeus hotel ID
            hotel_name: Hotel name (for logging)

        Returns:
            True if ID returns valid offers
        """
        client = self.client
        if not client:
            return False

        # Use date 45 days in future
        check_in = (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d')
        check_out = (datetime.now() + timedelta(days=46)).strftime('%Y-%m-%d')

        try:
            response = client.shopping.hotel_offers_search.get(
                hotelIds=hotel_id,
                checkInDate=check_in,
                checkOutDate=check_out,
                adults=2,
                currency='USD'
            )

            if response.data:
                # Check if there are actual offers
                for hotel_data in response.data:
                    offers = hotel_data.get('offers', [])
                    if offers:
                        price = offers[0].get('price', {}).get('total', 'N/A')
                        logger.info("  VALID: %s -> %s (price: $%s)", hotel_name, hotel_id, price)
                        return True

            logger.warning("  NO OFFERS: %s -> %s", hotel_name, hotel_id)
            return False

        except ResponseError as e:
            error_msg = str(e)
            if "INVALID PROPERTY CODE" in error_msg:
                logger.warning("  INVALID ID: %s -> %s", hotel_name, hotel_id)
            elif "NO ROOMS AVAILABLE" in error_msg:
                # ID is valid but no rooms - still save it
                logger.info("  VALID (no rooms): %s -> %s", hotel_name, hotel_id)
                return True
            else:
                logger.warning("  ERROR: %s -> %s: %s", hotel_name, hotel_id, error_msg[:50])
            return False

    def find_and_validate(self, hotel_name: str) -> Optional[str]:
        """
        Find and validate Amadeus ID for a hotel.

        Args:
            hotel_name: Hotel name to search for

        Returns:
            Valid Amadeus ID or None
        """
        match = self.find_matching_hotel(hotel_name)
        if not match:
            logger.info("  No match found for: %s", hotel_name)
            return None

        hotel_id, amadeus_name, score = match
        logger.info("  Match: %s -> %s (%.0f%% match)", hotel_name, amadeus_name, score * 100)

        if self.validate_hotel_id(hotel_id, hotel_name):
            return hotel_id

        return None


def load_hotel_keys() -> Dict[str, Any]:
    """Load hotel keys database."""
    if not os.path.exists(HOTEL_KEYS_DB):
        return {}

    with open(HOTEL_KEYS_DB, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_hotel_keys(data: Dict[str, Any]) -> None:
    """Save hotel keys database."""
    with open(HOTEL_KEYS_DB, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("Saved hotel keys to %s", HOTEL_KEYS_DB)


def main():
    parser = argparse.ArgumentParser(description='Find Amadeus hotel IDs')
    parser.add_argument('--hotel', type=str, help='Specific hotel name to search')
    parser.add_argument('--limit', type=int, default=0, help='Limit number of hotels to process')
    parser.add_argument('--validate-only', action='store_true', help='Only validate existing IDs')
    parser.add_argument('--force', action='store_true', help='Re-find IDs even if already set')
    args = parser.parse_args()

    finder = AmadeusIdFinder()
    if not finder.is_available():
        logger.error("Amadeus not available. Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET")
        sys.exit(1)

    hotel_keys = load_hotel_keys()

    if args.hotel:
        # Search for specific hotel
        hotels_to_process = {args.hotel: hotel_keys.get(args.hotel, {})}
    else:
        hotels_to_process = hotel_keys

    print("=" * 70)
    print("Amadeus ID Finder")
    print("=" * 70)

    # Load Amadeus hotels first
    print("\nLoading Amadeus hotel database...")
    amadeus_hotels = finder.load_amadeus_hotels()
    print(f"Found {len(amadeus_hotels)} hotels in Amadeus (test environment)")
    print("=" * 70)

    processed = 0
    found = 0
    validated = 0
    skipped = 0

    for hotel_name, hotel_data in hotels_to_process.items():
        if args.limit > 0 and processed >= args.limit:
            break

        processed += 1

        # Convert string format to dict
        if isinstance(hotel_data, str):
            hotel_data = {"xotelo": hotel_data}
            hotel_keys[hotel_name] = hotel_data

        existing_id = hotel_data.get('amadeus')

        print(f"\n[{processed}] {hotel_name}")

        if args.validate_only:
            if existing_id:
                if finder.validate_hotel_id(existing_id, hotel_name):
                    validated += 1
                else:
                    # Remove invalid ID
                    del hotel_data['amadeus']
                    logger.info("  Removed invalid ID")
            else:
                print("  No Amadeus ID to validate")
            continue

        if existing_id and not args.force:
            print(f"  Already has Amadeus ID: {existing_id}")
            skipped += 1
            continue

        # Find and validate new ID
        new_id = finder.find_and_validate(hotel_name)

        if new_id:
            hotel_data['amadeus'] = new_id
            found += 1
            print(f"  Saved: {new_id}")
        else:
            print("  No valid Amadeus ID found")

    # Save updated database
    save_hotel_keys(hotel_keys)

    print("\n" + "=" * 70)
    print("Summary:")
    print(f"  Processed: {processed}")
    if args.validate_only:
        print(f"  Validated: {validated}")
    else:
        print(f"  Found: {found}")
        print(f"  Skipped (already had ID): {skipped}")
    print("=" * 70)


if __name__ == '__main__':
    main()
